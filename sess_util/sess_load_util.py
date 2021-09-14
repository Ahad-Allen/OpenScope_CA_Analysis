"""
sess_load_util.py

This module contains functions for loading data from files generated by the 
Allen Institute OpenScope experiments for the Credit Assignment Project.

Authors: Colleen Gillon

Date: August, 2018

Note: this code uses python 3.7.

"""

import copy
import logging
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from util import file_util, gen_util, logger_util
from sess_util import sess_gen_util, sess_sync_util

logger = logging.getLogger(__name__)

TAB = "    "


######################################
def get_sessid_from_mouse_df(mouse_n=1, sess_n=1, runtype="prod", 
                             mouse_df="mouse_df.csv"):
    """
    get_sessid_from_mouse_df(sessid)

    Returns session ID, based on the mouse number, session number, and runtype,
    based on the mouse dataframe.

    Optional args:
        - mouse_n (int)  : mouse number
                           default: 1
        - sess_n (int)   : session number
                           default: 1
        - runtype (str)  : type of data
                           default: 1
        - mouse_df (Path): path name of dataframe containing information on each 
                           session. Dataframe should have the following columns:
                               mouse_n, sess_n, runtype
                           default: "mouse_df.csv"

    Returns:
        - sessid (int): session ID
    """

    if isinstance(mouse_df, (str, Path)):
        mouse_df = file_util.loadfile(mouse_df)

    df_line = gen_util.get_df_vals(
        mouse_df, ["mouse_n", "sess_n", "runtype"], 
        [int(mouse_n), int(sess_n), runtype],
        single=True
        )

    sessid = int(df_line["sessid"].tolist()[0])

    return sessid


######################################
def load_info_from_mouse_df(sessid, mouse_df="mouse_df.csv"):
    """
    load_info_from_mouse_df(sessid)

    Returns dictionary containing information from the mouse dataframe.

    Required args:
        - sessid (int): session ID

    Optional args:
        - mouse_df (Path): path name of dataframe containing information on each 
                           session. Dataframe should have the following columns:
                               sessid, mouse_n, depth, plane, line, sess_gen, 
                               sess_within, sess_n, pass_fail, all_files, 
                               any_files, notes
                           default: "mouse_df.csv"

    Returns:
        - df_dict (dict): dictionary with following keys:
            - all_files (bool) : if True, all files have been acquired for
                                 the session
            - any_files (bool) : if True, some files have been acquired for
                                 the session
            - depth (int)      : recording depth 
            - plane (str)      : recording plane ("soma" or "dend")
            - line (str)       : mouse line (e.g., "L5-Rbp4")
            - mouse_n (int)    : mouse number (e.g., 1)
            - notes (str)      : notes from the dataframe on the session
            - pass_fail (str)  : whether session passed "P" or failed "F" 
                                 quality control

            - sess_n (int)     : overall session number (e.g., 1)
    """

    if isinstance(mouse_df, (str, Path)):
        mouse_df = file_util.loadfile(mouse_df)

    df_line = gen_util.get_df_vals(mouse_df, "sessid", sessid, single=True)

    df_dict = {
        "mouse_n"      : int(df_line["mouse_n"].tolist()[0]),
        "depth"        : df_line["depth"].tolist()[0],
        "plane"        : df_line["plane"].tolist()[0],
        "line"         : df_line["line"].tolist()[0],
        "sess_n"       : int(df_line["sess_n"].tolist()[0]),
        "pass_fail"    : df_line["pass_fail"].tolist()[0],
        "all_files"    : bool(int(df_line["all_files"].tolist()[0])),
        "any_files"    : bool(int(df_line["any_files"].tolist()[0])),
        "notes"        : df_line["notes"].tolist()[0],
    }

    return df_dict


#############################################
def load_small_stim_pkl(stim_pkl, runtype="prod"):
    """
    load_small_stim_pkl(stim_pkl)

    Loads a smaller stimulus dictionary from the stimulus pickle file in which 
    "posbyframe" for bricks stimuli is not included. 
    
    If it does not exist, small stimulus dictionary is created and saved as a
    pickle with "_small" appended to name.
    
    Reduces the pickle size about 10 fold.

    Required args:
        - stim_pkl (Path): full path name for the full stimulus pickle file
    
    Optional args:
        - runtype (str): runtype ("prod" or "pilot")
    """

    stim_pkl = Path(stim_pkl)
    stim_pkl_no_ext = Path(stim_pkl.parent, stim_pkl.stem)
    small_stim_pkl_name = Path(f"{stim_pkl_no_ext}_small.pkl")
    
    if small_stim_pkl_name.exists():
        return file_util.loadfile(small_stim_pkl_name)
    else:
        logger.info("Creating smaller stimulus pickle.", extra={"spacing": TAB})

        stim_dict = file_util.loadfile(stim_pkl)

        if runtype == "pilot":
            stim_par_key = "stimParams"
        elif runtype == "prod":
            stim_par_key = "stim_params"
        else:
            gen_util.accepted_values_error(
                "runtype", runtype, ["prod", "pilot"])

        for i in range(len(stim_dict["stimuli"])):
            stim_keys = stim_dict["stimuli"][i][stim_par_key].keys()
            stim_par = stim_dict["stimuli"][i][stim_par_key]
            if runtype == "pilot" and "posByFrame" in stim_keys:
                _ = stim_par.pop("posByFrame")
            elif runtype == "prod" and "square_params" in stim_keys:
                _ = stim_par["session_params"].pop("posbyframe")
                
        file_util.saveinfo(stim_dict, small_stim_pkl_name)

        return stim_dict


#############################################
def load_stim_df_info(stim_pkl, stim_sync_h5, time_sync_h5, align_pkl, sessid, 
                      runtype="prod"):
    """
    load_stim_df_info(stim_pkl, stim_sync_h5, time_sync_h5, align_pkl, sessid)

    Creates the alignment dataframe (stim_df) and saves it as a pickle
    in the session directory, if it does not already exist. Returns dataframe, 
    alignment arrays, and frame rate.
    
    Required args:
        - stim_pkl (Path)    : full path name of the experiment stim pickle 
                               file
        - stim_sync_h5 (Path): full path name of the experiment sync hdf5 file
        - time_sync_h5 (Path): full path name of the time synchronization hdf5 
                               file
        - align_pkl (Path)   : full path name of the output pickle file to 
                               create
        - sessid (int)       : session ID, needed the check whether this 
                               session needs to be treated differently 
                               (e.g., for alignment bugs)

    Optional args:
        - runtype (str): runtype ("prod" or "pilot")
                         default: "prod"

    Returns:
        - stim_df (pd DataFrame): stimlus alignment dataframe with columns:
                                    "stimType", "stimPar1", "stimPar2", 
                                    "surp", "stimSeg", "gabfr", 
                                    "start2pfr", "end2pfr", "num2pfr"
        - stimtype_order (list) : stimulus type order
        - stim2twopfr (1D array): 2p frame numbers for each stimulus frame, 
                                  as well as the flanking
                                  blank screen frames 
        - twop_fps (num)        : mean 2p frames per second
        - twop_fr_stim (int)    : number of 2p frames recorded while stim
                                  was playing
    """

    align_pkl = Path(align_pkl)
    sessdir = align_pkl.parent

    # create stim_df if doesn't exist
    if not align_pkl.exists():
        logger.info(f"Stimulus alignment pickle not found in {sessdir}, and "
            "will be created.", extra={"spacing": TAB})
        sess_sync_util.get_stim_frames(
            stim_pkl, stim_sync_h5, time_sync_h5, align_pkl, sessid, runtype, 
            )
        
    align = file_util.loadfile(align_pkl)

    stim_df = align["stim_df"]
    stim_df = stim_df.rename(
        columns={"GABORFRAME": "gabfr", 
                 "start_frame": "start2pfr", 
                 "end_frame": "end2pfr", 
                 "num_frames": "num2pfr"})

    stim_df = modify_bri_segs(stim_df, runtype)
    stim_df = stim_df.sort_values("start2pfr").reset_index(drop=True)

    # note: STIMULI ARE NOT ORDERED IN THE PICKLE
    stimtype_map = {
        "g": "gabors", 
        "b": "bricks"
        }
    stimtype_order = stim_df["stimType"].map(stimtype_map).unique()
    stimtype_order = list(
        filter(lambda s: s in stimtype_map.values(), stimtype_order))

    # expand on direction info
    for direc in ["right", "left"]:
        stim_df.loc[(stim_df["stimPar2"] == direc), "stimPar2"] = \
            sess_gen_util.get_bri_screen_mouse_direc(direc)

    stim2twopfr  = align["stim_align"].astype("int")
    twop_fps     = sess_sync_util.get_frame_rate(stim_sync_h5)[0] 
    twop_fr_stim = int(max(align["stim_align"]))

    return stim_df, stimtype_order, stim2twopfr, twop_fps, twop_fr_stim


#############################################
def _warn_nans_diff_thr(run, min_consec=5, n_pre_existing=None, sessid=None):
    """
    _warn_nans_diff_thr(run)

    Checks for NaNs in running velocity, and logs a warning about the total 
    number of NaNs, and the consecutive NaNs. Optionally indicates the number 
    of pre-existing NaNs, versus number of NaNs resulting from the difference 
    threshold. 

    Required args:
        - run (1D array): array of running velocities in cm/s

    Optional args:
        - min_consec (num)    : minimum number of consecutive NaN running 
                                values to warn aboout
                                default: 5
        - n_pre_existing (num): number of pre-existing NaNs (before difference 
                                thresholding was used)
                                default: None
        - sessid (int)        : session ID to include in the log or error
                                default: None 
    """

    n_nans = np.sum(np.isnan(run))

    if n_nans == 0:
        return

    split_str = ""
    if n_pre_existing is not None:
        if n_pre_existing == n_nans:
            split_str = " (in pre-processing)"
        elif n_pre_existing == 0:
            split_str = " (using diff thresh)"
        else:
            split_str = (f" ({n_pre_existing} in pre-processing, "
                f"{n_nans - n_pre_existing} more using diff thresh)")

    mask = np.concatenate(([False], np.isnan(run), [False]))
    idx = np.nonzero(mask[1 : ] != mask[ : -1])[0]
    n_consec = np.sort(idx[1 :: 2] - idx[ :: 2])[::-1]

    n_consec_above_min_idx = np.where(n_consec > min_consec)[0]
    
    n_consec_str = ""
    if len(n_consec_above_min_idx) > 0:
        n_consec_str = ", ".join(
            [str(n) for n in n_consec[n_consec_above_min_idx]])
        n_consec_str = (f"\n{TAB}This includes {n_consec_str} consecutive "
            "dropped running values.")

    prop = n_nans / len(run)
    sessstr = "" if sessid is None else f"Session {sessid}: "
    logger.warning(f"{sessstr}{n_nans} dropped running frames "
        f"(~{prop * 100:.1f}%){split_str}.{n_consec_str}", 
        extra={"spacing": TAB})

    return


#############################################
def nan_large_run_differences(run, diff_thr=50, warn_nans=True, 
                              drop_tol=0.0003, sessid=None):
    """
    nan_large_run_differences(run)

    Returns running velocity with outliers replaced with NaNs.

    Required args:
        - run (1D array): array of running velocities in cm/s

    Optional args:
        - diff_thr (int)    : threshold of difference in running velocity to 
                              identify outliers
                              default: 50
        - warn_nans (bool)  : if True, a warning is logged 
                              default: True
        - drop_tol (num)    : the tolerance for proportion running frames 
                              dropped. A warning is produced only if this 
                              condition is not met. 
                              default: 0.0003 
        - sessid (int)      : session ID to include in the log or error
                              default: None 

    Returns:
        - run (1D array): updated array of running velocities in cm/s
    """

    # temorarily remove preexisting NaNs (to be reinserted after)
    original_length = len(run)
    not_nans_idx = np.where(~np.isnan(run))[0]
    run = run[not_nans_idx]
    n_pre_existing = original_length - len(run)

    run_diff = np.diff(run)
    out_idx = np.where((run_diff < -diff_thr) | (run_diff > diff_thr))[0]
    at_idx = -1
    for idx in out_idx:
        if idx > at_idx:
            if idx == 0:
                # in case the first value is completely off
                comp_val = 0
                if np.absolute(run[0]) > diff_thr:
                    run[0] = np.nan
            else:
                comp_val = run[idx]
            while np.absolute(run[idx + 1] - comp_val) > diff_thr:
                run[idx + 1] = np.nan
                idx += 1
            at_idx = idx

    # reinsert pre-existing NaNs
    prev_run = copy.deepcopy(run)
    run = np.empty(original_length) * np.nan
    run[not_nans_idx] = prev_run

    prop_nans = np.sum(np.isnan(run)) / len(run)
    if warn_nans and prop_nans > drop_tol:
        _warn_nans_diff_thr(
            run, min_consec=5, n_pre_existing=n_pre_existing, sessid=sessid
            )

    return run


#############################################
def load_run_data(stim_dict, stim_sync_h5, filter_ks=5, diff_thr=50, 
                  drop_tol=0.0003, sessid=None):
    """
    load_run_data(stim_dict, stim_sync_h5)

    Returns running velocity with outliers replaced with NaNs, and median 
    filters the data.

    Required args:
        - stim_dict (Path or dict): stimulus dictionary or path to dictionary,
                                   containing stimulus information
        - stim_sync_h5 (Path)     : stimulus synchronization file. 

    Optional args:
        - filter_ks (int)   : kernel size to use in median filtering the 
                              running velocity (0 to skip filtering).
                              default: 5
        - diff_thr (int)    : threshold of difference in running velocity to 
                              identify outliers
                              default: 50
        - drop_tol (num)    : the tolerance for proportion running frames 
                              dropped. A warning is produced only if this 
                              condition is not met. 
                              default: 0.0003 
        - sessid (int)      : session ID to include in the log or error
                              default: None 

    Returns:
        - run_velocity (1D array): array of running velocities in cm/s for each 
                                   recorded stimulus frames

    """

    run_kwargs = {
        "stim_sync_h5": stim_sync_h5,
        "filter_ks"   : filter_ks,
    }

    if isinstance(stim_dict, dict):
        run_kwargs["stim_dict"] = stim_dict        
    elif isinstance(stim_dict, (str, Path)):
        run_kwargs["pkl_file_name"] = stim_dict
    else:
        raise TypeError(
            "'stim_dict' must be a dictionary or a path to a pickle."
            )

    run_velocity = sess_sync_util.get_run_velocity(**run_kwargs)

    run_velocity = nan_large_run_differences(
        run_velocity, diff_thr, warn_nans=True, drop_tol=drop_tol, 
        sessid=sessid
        )

    return run_velocity


#############################################
def load_pup_data(pup_data_h5):
    """
    load_pup_data(pup_data_h5)

    If it exists, loads the pupil tracking data. Extracts pupil diameter
    and position information in pixels.

    If it doesn't exist or several are found, raises an error.

    Required args:
        - pup_data_h5 (Path or list): path to the pupil data h5 file

    Returns:
        - pup_data (pd DataFrame): pupil data dataframe with columns:
            - frames (int)        : frame number
            - pup_diam (float)    : median pupil diameter in pixels
            - pup_center_x (float): pupil center position for x at 
                                    each pupil frame in pixels
            - pup_center_y (flat) : pupil center position for y at 
                                    each pupil frame in pixels
    """

    if pup_data_h5 == "none":
        raise OSError("No pupil data file found.")
    elif isinstance(pup_data_h5, list):
        raise OSError("Many pupil data files found.")

    columns = ["nan_diam", "nan_center_x", "nan_center_y"]
    pup_data = pd.read_hdf(pup_data_h5).filter(items=columns).astype(float)
    nan_pup = (lambda name : name.replace("nan_", "pup_") 
        if "nan" in name else name)
    pup_data = pup_data.rename(columns=nan_pup)
    pup_data.insert(0, "frames", value=range(len(pup_data)))

    return pup_data  


#############################################
def load_pup_sync_h5_data(pup_video_h5):
    """
    load_pup_sync_h5_data(pup_video_h5)

    Returns pupil synchronization information.

    Required args:
        - pup_video_h5 (Path): path to the pupil video h5 file

    Returns:
        - pup_fr_interv (1D array): interval in sec between each pupil 
                                    frame
    """

    with h5py.File(pup_video_h5, "r") as f:
        pup_fr_interv = f["frame_intervals"][()].astype("float64")

    return pup_fr_interv


#############################################
def load_beh_sync_h5_data(time_sync_h5):
    """
    load_beh_sync_h5_data(time_sync_h5)

    Returns behaviour synchronization information.

    Required args:
        - time_sync_h5 (Path): path to the time synchronization hdf5 file

    Returns:
        - twop2bodyfr (1D array)  : body-tracking video (video-0) frame 
                                    numbers for each 2p frame
        - twop2pupfr (1D array)   : eye-tracking video (video-1) frame 
                                    numbers for each 2p frame
        - stim2twopfr2 (1D array) : 2p frame numbers for each stimulus 
                                    frame, as well as the flanking
                                    blank screen frames (second 
                                    version, very similar to stim2twopfr 
                                    with a few differences)
    """

    with h5py.File(time_sync_h5, "r") as f:
        twop2bodyfr  = f["body_camera_alignment"][()].astype("int")
        twop2pupfr   = f["eye_tracking_alignment"][()].astype("int")
        stim2twopfr2 = f["stimulus_alignment"][()].astype("int")

    return twop2bodyfr, twop2pupfr, stim2twopfr2


#############################################
def load_sync_h5_data(pup_video_h5, time_sync_h5):
    """
    load_sync_h5_data(pup_video_h5, time_sync_h5)

    Returns pupil and behaviour synchronization information.

    Required args:
        - pup_video_h5 (Path): path to the pupil video h5 file
        - time_sync_h5 (Path): path to the time synchronization hdf5 file

    Returns:
        - pup_fr_interv (1D array): interval in sec between each pupil 
                                    frame
        - twop2bodyfr (1D array)  : body-tracking video (video-0) frame 
                                    numbers for each 2p frame
        - twop2pupfr (1D array)   : eye-tracking video (video-1) frame 
                                    numbers for each 2p frame
        - stim2twopfr2 (1D array) : 2p frame numbers for each stimulus 
                                    frame, as well as the flanking
                                    blank screen frames (second 
                                    version, very similar to stim2twopfr 
                                    with a few differences)
    """

    pup_fr_interv = load_pup_sync_h5_data(pup_video_h5)

    twop2bodyfr, twop2pupfr, stim2twopfr2 = load_beh_sync_h5_data(time_sync_h5)

    return pup_fr_interv, twop2bodyfr, twop2pupfr, stim2twopfr2


#############################################
def modify_bri_segs(stim_df, runtype="prod"):
    """
    modify_bri_segs(stim_df)

    Returns stim_df with brick segment numbers modified to ensure that
    they are different for the two brick stimuli in the production data.

    Required args:
        - stim_df (pd DataFrame): stimlus alignment dataframe with columns:
                                    "stimType", "stimPar1", "stimPar2", 
                                    "surp", "stimSeg", "gabfr", 
                                    "start2pfr", "end2pfr", "num2pfr"

    Optional args:
        - runtype (str): runtype
                         default: "prod"

    Returns:
        - stim_df (pd DataFrame): modified dataframe
    """

    if runtype != "prod":
        return stim_df

    stim_df = copy.deepcopy(stim_df)

    bri_st_fr = gen_util.get_df_vals(
        stim_df, "stimType", "b", "start2pfr", unique=False)
    bri_num_fr = np.diff(bri_st_fr)
    num_fr = gen_util.get_df_vals(
        stim_df, "stimType", "b", "num2pfr", unique=False)[:-1]
    break_idx = np.where(num_fr != bri_num_fr)[0]
    n_br = len(break_idx)
    if n_br != 1:
        raise RuntimeError("Expected only one break in the bricks "
            f"stimulus, but found {n_br}.")
    
    # last start frame and seg for the first brick stim
    last_fr1 = bri_st_fr[break_idx[0]] 
    last_seg1 = gen_util.get_df_vals(
        stim_df, ["stimType", "start2pfr"], ["b", last_fr1], "stimSeg")[0]
    
    seg_idx = ((stim_df["stimType"] == "b") & (stim_df["start2pfr"] > last_fr1))

    new_idx = stim_df.loc[seg_idx]["stimSeg"] + last_seg1 + 1
    stim_df = gen_util.set_df_vals(stim_df, seg_idx, "stimSeg", new_idx)

    return stim_df


#############################################
def load_sess_stim_seed(stim_dict, runtype="prod"):
    """
    load_sess_stim_seed(stim_df)

    Returns session's stimulus seed for this session. Expects all stimuli 
    stored in the session's stimulus dictionary to share the same seed.

    Required args:
        - stim_dict (dict): stimlus dictionary

    Optional args:
        - runtype (str): runtype
                         default: "prod"

    Returns:
        - seed (int): session's stimulus seed
    """

    if runtype == "pilot":
        stim_param_key = "stimParams"
        sess_param_key = "subj_params"
    elif runtype == "prod":
        stim_param_key = "stim_params"
        sess_param_key = "session_params"
    else:
        gen_util.accepted_values_error("runtype", runtype, ["pilot", "prod"])

    seeds = []
    for stimulus in stim_dict["stimuli"]:
        seeds.append(stimulus[stim_param_key][sess_param_key]["seed"])
    
    if np.max(seeds) != np.min(seeds):
        raise RuntimeError("Unexpectedly found different seeds for different "
        "stimuli for this session.")
    
    seed = seeds[0]

    return seed

    