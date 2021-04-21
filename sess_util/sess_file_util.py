"""
sess_file_util.py

This module contains functions for dealing with reading and writing of data 
files generated by the Allen Institute OpenScope experiments for the Credit 
Assignment Project.

Authors: Blake Richards

Date: August, 2018

Note: this code uses python 3.7.

"""

import glob
import os

from util import file_util, gen_util, logger_util


#############################################
def get_sess_dirs(maindir, sessid, expid, segid, mouseid, runtype="prod",
                  mouse_dir=True, check=True):
    """
    get_sess_dirs(maindir, sessid, expid, segid, mouseid)

    Returns the full path names of the session directory and subdirectories for 
    the specified session and experiment on the given date that can be used for 
    the Credit Assignment analysis.

    Also checks existence of expected directories.
 
    Required arguments:
        - maindir (str): name of the main data directory
        - sessid (int) : session ID (9 digits)
        - expid (str)  : experiment ID (9 digits)
        - segid (str)  : segmentation ID (9 digits)
        - mouseid (str): mouse 6-digit ID string used for session files
                         e.g. "389778" 

    Optional arguments
        - runtype (str)   : "prod" (production) or "pilot" data
                            default: "prod"
        - mouse_dir (bool): if True, session information is in a "mouse_*"
                            subdirectory
                            default: True
        - check (bool)    : if True, checks whether the directories in the 
                            output dictionary exist
                            default: True

    Returns:
        - sessdir (str) : full path name of the session directory
        - expdir (str)  : full path name of the experiment directory
        - procdir (str) : full path name of the processed 
                          data directory
        - demixdir (str): full path name of the demixing data directory
        - segdir (str)  : full path name of the segmentation directory
    """
    
    # get the name of the session and experiment data directories
    if mouse_dir:
        sessdir = os.path.join(maindir, runtype, f"mouse_{mouseid}", 
            f"ophys_session_{sessid}")
    else:
        sessdir = os.path.join(maindir, runtype, f"ophys_session_{sessid}")

    expdir   = os.path.join(sessdir, f"ophys_experiment_{expid}")
    procdir  = os.path.join(expdir, "processed")
    demixdir = os.path.join(expdir, "demix")
    segdir   = os.path.join(procdir, f"ophys_cell_segmentation_run_{segid}")

    # check that directory exists
    if check:
        try:
            file_util.checkdir(sessdir)
        except OSError:
            raise OSError(
                f"{sessdir} does not conform to expected OpenScope structure.")

    return sessdir, expdir, procdir, demixdir, segdir


#############################################
def get_file_names(maindir, sessid, expid, segid, date, mouseid, 
                   runtype="prod", mouse_dir=True, check=True):
    """
    get_file_names(maindir, sessionid, expid, date, mouseid)

    Returns the full path names of all of the expected data files in the 
    main directory for the specified session and experiment on the given date 
    that can be used for the Credit Assignment analysis.
 
    Required args:
        - maindir (str): name of the main data directory
        - sessid (int) : session ID (9 digits)
        - expid (str)  : experiment ID (9 digits)
        - segid (str)  : segmentation ID (9 digits)
        - date (str)   : date for the session in YYYYMMDD, e.g. "20160802"
        - mouseid (str): mouse 6-digit ID string used for session files

    Optional args:
        - runtype (str)   : "prod" (production) or "pilot" data
                            default: "prod"
        - mouse_dir (bool): if True, session information is in a "mouse_*"
                            subdirectory
                            default: True
        - check (bool)    : if True, checks whether the files and directories 
                            in the output dictionaries exist (with a few 
                            exceptions)
                            default: True

    Returns:
        - dirpaths (dict): dictionary of directory paths
            ["expdir"] (str)  : full path name of the experiment directory
            ["procdir"] (str) : full path name of the processed directory
            ["demixdir"] (str): full path name of the demixed directory
            ["segdir"] (str)  : full path name of the segmentation directory
        - filepaths (dict): dictionary of file paths
            ["behav_video_h5"] (str)    : full path name of the behavioral hdf5
                                          video file
            ["pupil_video_h5"] (str)    : full path name of the pupil hdf5 
                                          video file
            ["roi_extract_json"] (str)  : full path name of the ROI extraction 
                                          json
            ["roi_objectlist_txt"] (str): full path to ROI object list txt
            ["stim_pkl"]  (str)         : full path name of the stimulus
                                          pickle file
            ["stim_sync_h5"] (str)      : full path name of the stimulus
                                          synchronization hdf5 file
            ["time_sync_h5"] (str)      : full path name of the time 
                                          synchronization hdf5 file
            
            Existence not checked:
            ["align_pkl"] (str)         : full path name of the stimulus
                                          alignment pickle file
            ["corrected_data_h5"] (str) : full path name of the motion
                                          corrected 2p data hdf5 file
            ["roi_trace_h5"] (str)      : full path name of the ROI raw 
                                          processed fluorescence trace hdf5 
                                          file (allen version)
            ["roi_trace_dff_h5"] (str)  : full path name of the ROI dF/F trace 
                                          hdf5 file (allen version)
            ["zstack_h5"] (str)         : full path name of the zstack 2p hdf5 
                                          file
    """
    
    sessdir, expdir, procdir, demixdir, segdir = get_sess_dirs(
        maindir, sessid, expid, segid, mouseid, runtype, mouse_dir, check)

    roi_trace_paths = get_roi_trace_paths(
        maindir, sessid, expid, segid, mouseid, runtype, mouse_dir, 
        dendritic=False, check=False) # will check below, if required

    # set the file names
    sess_m_d = f"{sessid}_{mouseid}_{date}"

    dirpaths = {"expdir"  : expdir,
                "procdir" : procdir,
                "segdir"  : segdir,
                "demixdir": demixdir
                }

    filepaths = {"align_pkl"         : os.path.join(sessdir, 
                                       f"{sess_m_d}_df.pkl"),
                 "behav_video_h5"    : os.path.join(sessdir, 
                                       f"{sess_m_d}_video-0.h5"),
                 "correct_data_h5"   : os.path.join(procdir, 
                                       "concat_31Hz_0.h5"),
                 "pupil_video_h5"    : os.path.join(sessdir, 
                                       f"{sess_m_d}_video-1.h5"),
                 "roi_extract_json"  : os.path.join(procdir, 
                                       f"{expid}_input_extract_traces.json"),
                 "roi_trace_h5"      : roi_trace_paths["roi_trace_h5"],
                 "roi_trace_dff_h5"  : roi_trace_paths["roi_trace_dff_h5"],
                 "roi_objectlist_txt": os.path.join(segdir, "objectlist.txt"),
                 "stim_pkl"          : os.path.join(sessdir, 
                                       f"{sess_m_d}_stim.pkl"),
                 "stim_sync_h5"      : os.path.join(sessdir, 
                                       f"{sess_m_d}_sync.h5"),
                 
                 "time_sync_h5"      : os.path.join(expdir, 
                                       f"{expid}_time_synchronization.h5"),
                 "zstack_h5"         : os.path.join(sessdir, 
                                       f"{sessid}_zstack_column.h5"),
                }
    
    if check:
        # files not to check for (are created if needed or should be checked 
        # when needed, due to size)
        no_check = ["align_pkl", "correct_data_h5", "zstack_h5", 
            "roi_trace_h5", "roi_trace_dff_h5"]

        for key in filepaths.keys():
            if key not in no_check:
                file_util.checkfile(filepaths[key])

    return dirpaths, filepaths


#############################################
def get_file_names_from_sessid(maindir, sessid, runtype="prod", check=True):
    """
    get_file_names_from_sessid(maindir, sessid)

    Returns the full path names of all of the expected data files in the 
    main directory for the specified session.
 
    Required args:
        - maindir (str): name of the main data directory
        - sessid (int) : session ID (9 digits)

    Optional args:
        - runtype (str)   : "prod" (production) or "pilot" data
                            default: "prod"
        - check (bool)    : if True, checks whether the files and directories 
                            in the output dictionaries exist (with a few 
                            exceptions)
                            default: True

    Returns:
        - dirpaths (dict): dictionary of directory paths (see get_file_names)
        - filepaths (dict): dictionary of file paths (see get_file_names)
    """

    sessdir, mouse_dir = get_sess_dir_path(maindir, sessid, runtype)

    mouseid, date = get_mouseid_date(sessdir, sessid)

    expid = get_expid(sessdir)
    segid = get_segid(sessdir)

    dirpaths, filepaths = get_file_names(
        maindir, sessid, expid, segid, date, mouseid, runtype, mouse_dir, 
        check)

    return dirpaths, filepaths


#############################################
def get_sess_dir_path(maindir, sessid, runtype="prod"):
    """
    get_sess_dir_path(maindir, sessid)

    Returns the path to the session directory, and whether a mouse directory 
    is included in the path.

    Required args:
        - maindir (str): main directory
        - sessid (int) : session ID

    Optional args:
        - runtype (str): "prod" (production) or "pilot" data
                          default: "prod"

    Returns:
        - sess_dir (str)  : path to the session directory
        - mouse_dir (bool): if True, session information is in a "mouse_*"
                            subdirectory
                            default: True 
    """

    if runtype not in ["pilot", "prod"]:
        gen_util.accepted_values_error("runtype", runtype, ["prod", "pilot"])

    # set the session directory (full path)
    wild_dir  = os.path.join(
        maindir, runtype, "mouse_*", f"ophys_session_{sessid}")
    name_dir  = glob.glob(wild_dir)
    
    # pilot data may not be in a "mouse_" folder
    if len(name_dir) == 0:
        wild_dir  = os.path.join(
            maindir, runtype,  f"ophys_session_{sessid}")
        name_dir  = glob.glob(wild_dir)
        mouse_dir = False
    else:
        mouse_dir = True

    if len(name_dir) == 0:
        raise OSError(f"Could not find directory for session {sessid} "
            f"(runtype {runtype}) in {maindir} subfolders.")
    elif len(name_dir) > 1:
        raise OSError(f"Found {len(name_dir)} matching session folders in "
            f"{maindir} instead of 1.")

    sess_dir = name_dir[0]

    return sess_dir, mouse_dir


#############################################
def get_mouseid(sessdir, mouse_dir=True):
    """
    get_mouseid(sessdir)

    Returns the mouse ID.

    Required args:
        - sessdir (str): session directory

    Optional args:
        - mouse_dir (bool): if True, session information is in a "mouse_*"
                            subdirectory
                            default: True
        - sessid (int)    : session ID. If None, it is retrieved from the 
                            session directory.
                            default: None

    Returns:
        - mouseid (int): mouse ID (6 digits)
        - date (str)   : session date (i.e., yyyymmdd)
    """

    if mouse_dir:
        mstr = "mouse_"
        start = sessdir.find(mstr) + len(mstr)
        mouseid = sessdir[start:start + 6]

        return mouseid
    
    else:
        mouseid, _ = get_mouseid_date(sessdir)


#############################################
def get_mouseid_date(sessdir, sessid=None):
    """
    get_mouseid_date(sessdir)

    Returns the mouse ID and optionally the date associated with a session, by
    finding the associated stimulus pickle.

    Required args:
        - sessdir (str): session directory

    Optional args:
        - sessid (int) : session ID. If None, it is retrieved from the session
                         directory.
                         default: None

    Returns:
        - mouseid (int): mouse ID (6 digits)
        - date (str)   : session date (i.e., yyyymmdd)
    """

    if sessid is None:
        sessid = get_sessid(sessdir)

    pklglob = glob.glob(os.path.join(sessdir, f"{sessid}*stim.pkl"))
    
    if len(pklglob) == 0:
        raise OSError(f"Could not find stim pkl file in {sessdir}")
    else:
        pklinfo = os.path.basename(pklglob[0]).split("_")
    
    mouseid = int(pklinfo[1]) # mouse 6 digit nbr
    date    = pklinfo[2]

    return mouseid, date


##############################################
def get_sessid(sessdir):
    """
    get_sessid(sessdir)

    Returns the session ID associated with a session.

    Required args:
        - sessdir (str): session directory

    Returns:
        - sessid (int): session ID (9 digits)

    """

    sesspart = "ophys_session_"
    start = sessdir.find(sesspart) + len(sesspart)
    sessid = sessdir[start:start + 9]

    return sessid


############################################
def get_expid(sessdir):
    """
    get_expid(sessdir)

    Returns the experiment ID associated with a session.

    Required args:
        - sessdir (str): session directory

    Returns:
        - expid (int): experiment ID (9 digits)

    """

    expglob = glob.glob(os.path.join(sessdir,"ophys_experiment*"))
    if len(expglob) == 0:
        raise OSError(f"Could not find experiment directory in {sessdir}.")
    else:
        expinfo = os.path.basename(expglob[0]).split("_")
    expid = int(expinfo[2])

    return expid


#############################################
def get_segid(sessdir):
    """
    get_segid(sessdir)

    Returns the segmentation ID associated with a session.

    Required args:
        - sessdir (str): session directory

    Returns:
        - segid (int): experiment ID (8 digits)

    """

    segglob = glob.glob(os.path.join(
        sessdir, "*", "processed", "ophys_cell_segmentation_run_*"))
    if len(segglob) == 0:
        raise OSError(f"Could not find segmentation directory in {sessdir}")
    else:
        seginfo = os.path.basename(segglob[0]).split("_")
    segid = int(seginfo[-1])

    return segid


#############################################
def get_dendritic_mask_path(maindir, sessid, expid, mouseid, runtype="prod", 
                            mouse_dir=True, check=True):
    """
    get_dendritic_mask_path(maindir, sessid, expid, mouseid)

    Returns path to dendritic mask file.

    Required args:
        - maindir (str): name of the main data directory
        - sessid (int) : session ID (9 digits), e.g. "712483302"
        - expid (str)  : experiment ID (9 digits), e.g. "715925563"
        - date (str)   : date for the session in YYYYMMDD
                         e.g. "20160802"
        - mouseid (str): mouse 6-digit ID string used for session files
                         e.g. "389778" 

    Optional args:
        - runtype (str)   : "prod" (production) or "pilot" data
                            default: "prod"
        - mouse_dir (bool): if True, session information is in a "mouse_*"
                            subdirectory
                            default: True
        - check (bool)    : if True, checks whether the mask file exists
                            default: True

    Returns:
        - maskfile (str): full path name of the extract masks hdf5 file
    """

    procdir = get_sess_dirs(
        maindir, sessid, expid, None, mouseid, runtype, mouse_dir, 
        check=check)[2]


    maskfile = os.path.join(procdir, f"{sessid}_dendritic_masks.h5")

    if check:
        file_util.checkfile(maskfile)
    
    return maskfile


#############################################
def get_dendritic_mask_path_from_sessid(maindir, sessid, runtype="prod", 
                                        check=True):
    """
    get_dendritic_mask_path_from_sessid(maindir, sessid)

    Returns path to dendritic mask file for the specified session.

    Required args:
        - maindir (str): main directory
        - sessid (int) : session ID

    Optional args:
        - runtype (str)   : "prod" (production) or "pilot" data
                            default: "prod"
        - check (bool)    : if True, checks whether the files in the output 
                            dictionary exist
                            default: True

    Returns:
        - maskfile (str): full path name of the extract masks hdf5 file
    """

    sessdir, mouse_dir = get_sess_dir_path(maindir, sessid, runtype)

    mouseid = get_mouseid(sessdir, mouse_dir)

    expid = get_expid(sessdir)

    maskfile = get_dendritic_mask_path(
        maindir, sessid, expid, mouseid, runtype, mouse_dir, check)

    return maskfile


#############################################
def get_dendritic_trace_path(orig_file, check=True):
    """
    get_dendritic_trace_path(orig_file)

    Returns path to traces for EXTRACT dendritic trace data.

    Required args:
        - orig_file (str): path to allen ROI traces

    Optional args:
        - check (bool): if True, the existence of the dendritic file is checked
                        default: True

    Returns:
        - dend_file (str): path to corresponding EXTRACT dendritic ROI traces
    """

    filepath, ext = os.path.splitext(orig_file)
    
    dend_part = "_dendritic"

    dend_file = f"{filepath}{dend_part}{ext}"

    if check:
        file_util.checkfile(dend_file)

    return dend_file


#############################################
def get_roi_trace_paths(maindir, sessid, expid, segid, mouseid, 
                        runtype="prod", mouse_dir=True, dendritic=False, 
                        check=True):
    """
    get_roi_trace_paths(maindir, sessid, expid, segid, mouseid)

    Returns the full path names of all of the expected ROI trace files in the 
    main directory.

    Required arguments:
        - maindir (str): name of the main data directory
        - sessid (int) : session ID (9 digits)
        - expid (str)  : experiment ID (9 digits)
        - segid (str)  : segmentation ID (9 digits)
        - mouseid (str): mouse 6-digit ID string used for session files
                         e.g. "389778" 

    Optional arguments
        - runtype (str)   : "prod" (production) or "pilot" data
                            default: "prod"
        - mouse_dir (bool): if True, session information is in a "mouse_*"
                            subdirectory
                            default: True
        - dendritic (bool): if True, paths are changed to EXTRACT dendritic 
                            version
                            default: False
        - check (bool)    : if True, checks whether the files in the output 
                            dictionary exist
                            default: True
    
    Returns:
        - roi_trace_paths (dict): ROI trace paths dictionary
            ["demixed_trace_h5"] (str)   : full path to demixed trace hdf5 file
            ["neuropil_trace_h5"] (str)  : full path to neuropil trace hdf5 file
            ["roi_trace_h5"] (str)       : full path name of the ROI raw 
                                           processed fluorescence trace hdf5 
                                           file
            ["roi_trace_dff_h5"] (str)   : full path name of the ROI dF/F trace 
                                           hdf5 file
            ["unproc_roi_trace_h5"] (str): full path to unprocessed ROI trace 
                                           hdf5 file (data stored under "FC")
    """

    _, expdir, procdir, demixdir, _ = get_sess_dirs(
        maindir, sessid, expid, segid, mouseid, runtype, mouse_dir, check)

    roi_trace_paths = {
        "unproc_roi_trace_h5": os.path.join(procdir, "roi_traces.h5"),
        "neuropil_trace_h5"  : os.path.join(procdir, "neuropil_traces.h5"),
        "demixed_trace_h5"   : os.path.join(demixdir, 
                               f"{expid}_demixed_traces.h5"),
        "roi_trace_h5"       : os.path.join(expdir, "neuropil_correction.h5"),
        "roi_trace_dff_h5"   : os.path.join(expdir, f"{expid}_dff.h5"),
    }

    if dendritic:
        for key, val in roi_trace_paths.items():
            roi_trace_paths[key] = get_dendritic_trace_path(val, check=check)
    elif check:
        for _, val in roi_trace_paths.items():
            file_util.checkfile(val)

    return roi_trace_paths


#############################################
def get_roi_trace_paths_from_sessid(maindir, sessid, runtype="prod", 
                                    dendritic=False, check=True):
    """
    get_roi_trace_paths_from_sessid(maindir, sessid)

    Returns the full path names of all of the expected ROI trace files in the 
    main directory for the specified session.

    Required args:
        - maindir (str): main directory
        - sessid (int) : session ID

    Optional args:
        - runtype (str)   : "prod" (production) or "pilot" data
                            default: "prod"
        - dendritic (bool): if True, paths are changed to EXTRACT dendritic 
                            version
                            default: False
        - check (bool)    : if True, checks whether the files in the output 
                            dictionary exist
                            default: True

    Returns:
        - roi_trace_paths (dict): ROI trace paths dictionary 
                                  (see get_roi_trace_paths)
    """

    sessdir, mouse_dir = get_sess_dir_path(maindir, sessid, runtype)

    mouseid = get_mouseid(sessdir, mouse_dir)

    expid = get_expid(sessdir)
    segid = get_segid(sessdir)

    roi_trace_paths = get_roi_trace_paths(
        maindir, sessid, expid, segid, mouseid, runtype, mouse_dir, 
        dendritic, check)

    return roi_trace_paths


#############################################
def get_pupil_data_h5_path(maindir):
    """
    get_pupil_data_h5_path(maindir)

    Returns path to pupil data h5 file.

    Required args:
        - maindir (str): name of the main data directory

    Returns:
        - pup_data_h5 (str): if full path name of the pupil h5 file
    """

    name_part = "*pupil_data_df.h5"
    pupil_data_files = glob.glob(os.path.join(maindir, name_part))

    if len(pupil_data_files) == 1:
        pup_data_h5 = pupil_data_files[0]
    elif len(pupil_data_files) > 1:
        pup_data_h5 = pupil_data_files
    else:
        pup_data_h5 = "none"

    return pup_data_h5


#############################################
def get_nway_match_path_from_sessid(maindir, sessid, runtype="prod", 
                                    check=True):
    """
    get_nway_match_path_from_sessid(maindir, sessid)

    Returns the full path name for the nway match file in the main directory 
    for the specified session.

    Required args:
        - maindir (str): main directory
        - sessid (int) : session ID

    Optional args:
        - runtype (str)   : "prod" (production) or "pilot" data
                            default: "prod"
        - check (bool)    : if True, checks whether the files in the output 
                            dictionary exist
                            default: True

    Returns:
        - nway_match_path (str): n-way match path
    """

    sessdir, mouse_dir = get_sess_dir_path(maindir, sessid, runtype)

    mouseid = get_mouseid(sessdir, mouse_dir)

    expid = get_expid(sessdir)
    segid = get_segid(sessdir)

    _, _, procdir, _, _ = get_sess_dirs(
        maindir, sessid, expid, segid, mouseid, runtype, mouse_dir, check)

    nway_match_path = os.path.join(
        procdir, f"mouse_{mouseid}__session_{sessid}__nway_matched_rois.json"
        )

    if check:
        file_util.checkfile(nway_match_path)

    return nway_match_path

