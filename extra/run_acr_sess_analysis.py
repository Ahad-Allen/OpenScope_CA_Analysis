"""
run_acr_sess_analysis.py

This script runs across session analyses using a Session object with data 
generated by the Allen Institute OpenScope experiments for the Credit 
Assignment Project.

Authors: Colleen Gillon

Date: October, 2019

Note: this code uses python 3.7.

"""

import argparse
import copy
import inspect
import logging
from pathlib import Path

from matplotlib import pyplot as plt

# try to set cache/config as early as possible (for clusters)
from util import gen_util 
gen_util.CC_config_cache()

gen_util.extend_sys_path(__file__, parents=2)
from util import gen_util, logger_util, plot_util, rand_util
from sess_util import sess_gen_util, sess_ntuple_util, sess_plot_util
from extra_analysis import acr_sess_analys
from extra_plot_fcts import plot_from_dicts_tool as plot_dicts


DEFAULT_DATADIR = Path("..", "data", "OSCA")
DEFAULT_MOUSE_DF_PATH = Path("mouse_df.csv")
DEFAULT_FONTDIR = Path("..", "tools", "fonts")

logger = logging.getLogger(__name__)


ANALYSIS_DESCR = {
    "s": "difference between unexpected and expected sequences",
    "l": "difference between unexpected and expected sequences, locked to unexpected and v.v.",
    "a": "difference between stimulus and grayscreen, locked to onset and v.v.",
    "t": "traces for unexpected and expected sequences",
    "r": "traces locked to unexpected and to expected sequence onset",
    "b": "traces locked to stimulus onset and to stimulus offset",
    "i": "unexpected event selectivity indices",
    "m": "unexpected event selectivity indices with common orientations",
    "d": "direction selectivity indices",
    "c": "unexpected event seletivity index colormaps across stimulus parameters",
    "g": "progression of unexpected and expected responses",
    "o": "unexpected and expected responses for each position (1st, 2nd, etc.)",
    "u": "unexpected reponse latency",
    "p": "proportion of responsive ROIs for each stimulus type",
}


#############################################
def reformat_args(args):
    """
    reformat_args(args)

    Returns reformatted args for analyses, specifically 
        - Sets stimulus parameters to "none" if they are irrelevant to the 
          stimtype
        - Changes stimulus parameters from "both" to actual values
        - Modifies the session number parameter
        - Sets seed, though doesn't seed
        - Modifies analyses (if "all" or "all_" in parameter)
        - Sets latency parameters based on lat_method

    Adds the following args:
        - dend (str)     : type of dendrites to use ("allen" or "extr")
        - omit_sess (str): sess to omit
        - omit_mice (str): mice to omit

    Required args:
        - args (Argument parser): parser with the following attributes: 
            visflow_dir (str)        : visual flow direction values to include
                                   (e.g., "right", "left" or "both")
            visflow_size (int or str): visual flow size values to include
                                   (e.g., 128, 256, "both")
            gabfr (int)          : gabor frame value to start sequences at
                                   (e.g., 0, 1, 2, 3)
            gabk (int or str)    : gabor kappa values to include 
                                   (e.g., 4, 16 or "both")
            gab_ori (int or str) : gabor orientation values to include
                                   (e.g., 0, 45, 90, 135, 180, 225 or "all")
            mouse_ns (str)       : mouse numbers or range 
                                   (e.g., 1, "1,3", "1-3", "all")
            runtype (str)        : runtype ("pilot" or "prod")
            sess_n (str)         : session number range (e.g., "1-1", "all")
            stimtype (str)       : stimulus to analyse (visflow or gabors)
    
    Returns:
        - args (Argument parser): input parser, with the following attributes
                                  modified: 
                                      visflow_dir, visflow_size, gabfr, gabk, 
                                      gab_ori, sess_n, mouse_ns, analyses, seed, 
                                      lat_p_val_thr, lat_rel_std
                                  and the following attributes added:
                                      omit_sess, omit_mice, dend
    """

    args = copy.deepcopy(args)

    if args.plane == "soma":
        args.dend = "allen"

    [args.visflow_dir, args.visflow_size, args.gabfr, 
        args.gabk, args.gab_ori] = sess_gen_util.get_params(
            args.stimtype, args.visflow_dir, args.visflow_size, args.gabfr, 
            args.gabk, args.gab_ori)

    if args.datatype == "run":
        args.fluor = "n/a"
    if args.plane == "soma":
        args.dend = "allen"

    args.omit_sess, args.omit_mice = sess_gen_util.all_omit(
        args.stimtype, args.runtype, args.visflow_dir, args.visflow_size, 
        args.gabk)
    
    if "-" in str(args.sess_n):
        vals = str(args.sess_n).split("-")
        if len(vals) != 2:
            raise ValueError("If args.sess_n is a range, must have format 1-3.")
        st = int(vals[0])
        end = int(vals[1]) + 1
        args.sess_n = list(range(st, end))

    if args.lat_method == "ratio":
        args.lat_p_val_thr = None
    elif args.lat_method == "ttest":
        args.lat_rel_std = None

    # choose a seed if none is provided (i.e., args.seed=-1), but seed later
    args.seed = rand_util.seed_all(
        args.seed, "cpu", log_seed=False, seed_now=False)

    # collect mouse numbers from args.mouse_ns
    if "," in args.mouse_ns:
        args.mouse_ns = [int(n) for n in args.mouse_ns.split(",")]
    elif "-" in args.mouse_ns:
        vals = str(args.mouse_ns).split("-")
        if len(vals) != 2:
            raise ValueError(
                "If args.mouse_ns is a range, must have format 1-3.")
        st = int(vals[0])
        end = int(vals[1]) + 1
        args.mouse_ns = list(range(st, end))
    elif args.mouse_ns not in ["all", "any"]:
        args.mouse_ns = int(args.mouse_ns)

    # collect analysis letters
    all_analyses = "".join(get_analysis_fcts().keys())
    if "all" in args.analyses:
        if "_" in args.analyses:
            excl = args.analyses.split("_")[1]
            args.analyses, _ = gen_util.remove_lett(all_analyses, excl)
        else:
            args.analyses = all_analyses
    elif "_" in args.analyses:
        raise ValueError("Use '_' in args.analyses only with 'all'.")

    return args


#############################################
def init_param_cont(args):
    """
    init_param_cont(args)

    Initializes parameter containers.

    Returns args:
        - in the following nametuples: analyspar, sesspar, stimpar, permpar, 
                                       basepar, idxpar, latpar
        - in the following dictionary: figpar 

    Required args:
        - args (Argument parser): parser with the following attributes:

            base (float)             : baseline value to use
            visflow_dir (str or list): visual flow direction values to include
                                       ("right", "left", ["right", "left"])
            visflow_size (int or list): visual flow size values to include
                                       (128, 256 or [128, 256])
            dend (str)               : type of dendrites to use 
                                       ("allen" or "dend")
            error (str)              : error statistic parameter 
                                       ("std" or "sem")
            fluor (str)              : if "raw", raw ROI traces are used. If 
                                       "dff", dF/F ROI traces are used.
            fontdir (str)            : path to directory containing additional 
                                       fonts
            gabfr (int)              : gabor frame at which sequences start 
                                       (0, 1, 2, 3)
            gabk (int or list)       : gabor kappa values to include 
                                       (4, 16 or [4, 16])
            gab_ori (int or list)    : gabor orientation values to include
                                       ([0, 45, 90, 135, 180, 225])
            idx_feature (str)        : feature used to calculate index
                                       ("by_exp", "unexp_lock", "prog_unexp")
            idx_op (str)             : type of index to use 
                                       ("d-prime", "rel_diff", "diff")
            idx_position (int)       : position to use if using a "prog" feature 
                                       to calculate index (e.g., 0)
            incl (str)               : sessions to include ("yes", "no", "all") 
            keepnans (str)           : if True, ROIs with NaN/Inf values are 
                                       kept in the analyses.
            lag_s (num)              : lag for autocorrelation (in sec)
            lat_method (str)         : latency calculation method 
                                       (ratio or ttest)
            lat_not_unexp_resp (bool): if False, only unexpected event 
                                       responsive ROIs are used for latency 
                                       analysis
            lat_p_val_thr (float)    : p-value threshold for ttest latency 
                                       method
            lat_std (float)          : standard deviation threshold for ratio 
                                       latency method
            line (str)               : "L23", "L5", "any"
            min_rois (int)           : min number of ROIs
            n_perms (int)            : nbr of permutations to run
            ncols (int)              : number of columns
            no_datetime (bool)       : if True, figures are not saved in a 
                                       subfolder named based on the date and 
                                       time.
            no_scale (bool)          : if True, data is not scaled
            not_save_fig (bool)      : if True, figures are not saved
            output (str)             : general directory in which to save output
            overwrite (bool)         : if False, overwriting existing figures 
                                       is prevented by adding suffix numbers.
            pass_fail (str or list)  : pass/fail values of interest ("P", "F")
            p_val (float)            : p-value threshold for significane tests
            plane (str)              : plane ("soma", "dend", "any")
            plt_bkend (str)          : mpl backend to use
            post (num)               : range of frames to include after each 
                                        reference frame (in s)
            pre (num)                : range of frames to include before each 
                                       reference frame (in s)
            rel_std (float)          : relative st. dev. threshold for ratio 
                                       latency method
            runtype (str or list)    : runtype ("pilot" or "prod")
            sess_n (int)             : session number
            stats (str)              : statistic parameter ("mean" or "median")
            stimtype (str)           : stimulus to analyse 
                                       ("visflow" or "gabors")
            tails (str or int)       : which tail(s) to test ("hi", "lo", 2)

    Returns:
        - analysis_dict (dict): dictionary of analysis parameters
            ["analyspar"] (AnalysPar): named tuple of analysis parameters
            ["sesspar"] (SessPar)    : named tuple of session parameters
            ["stimpar"] (StimPar)    : named tuple of stimulus parameters
            ["permpar"] (PermPar)    : named tuple of permutation parameters
            ["basepar"] (BasePar)    : named tuple of baseline parameters
            ["idxpar"] (IdxPar)      : named tuple of unexpected index parameters
            ["latpar"] (LatPar)      : named tuple of latency parameters
            ["figpar"] (dict)        : dictionary containing following 
                                       subdictionaries:
                ["init"]: dict with following inputs as attributes:
                    ["ncols"] (int)      : number of columns in the figures
                    ["sharex"] (bool)    : if True, x axis lims are shared 
                                           across subplots
                    ["sharey"] (bool)    : if True, y axis lims are shared 
                                           across subplots
                    ["subplot_hei"] (num): height of each subplot (inches)
                    ["subplot_wid"] (num): width of each subplot (inches)

                ["save"]: dict with the following inputs as attributes:
                    ["datetime"] (bool) : if True, figures are saved in a  
                                          subfolder named based on the date and 
                                          time.
                    ["fig_ext"] (str)   : figure extension
                    ["overwrite"] (bool): if True, existing figures can be 
                                          overwritten
                    ["save_fig"] (bool) : if True, figures are saved
                    ["use_dt"] (str)    : datetime folder to use
                    
                ["dirs"]: dict with the following attributes:
                    ["figdir"] (str)   : main folder in which to save figures
                    ["roi"] (str)      : subdirectory name for ROI analyses
                    ["run"] (str)      : subdirectory name for running analyses
                    ["autocorr"] (str) : subdirectory name for autocorrelation 
                                         analyses
                    ["locori"] (str)   : subdirectory name for location and 
                                         orientation responses
                    ["oridir"] (str)   : subdirectory name for 
                                         orientation/direction analyses
                    ["unexp_qu"] (str) : subdirectory name for unexpected, 
                                         quantile analyses
                    ["tune_curv"] (str): subdirectory name for tuning curves
                    ["grped"] (str)    : subdirectory name for ROI grps data
                    ["mags"] (str)     : subdirectory name for magnitude 
                                         analyses
                
                ["mng"]: dict with the following attributes:
                    ["plt_bkend"] (str): mpl backend to use
                    ["linclab"] (bool) : if True, Linclab mpl defaults are used
                    ["fontdir"] (str)  : path to directory containing 
                                         additional fonts
    """

    args = copy.deepcopy(args)

    analysis_dict = dict()

    # analysis parameters
    analysis_dict["analyspar"] = sess_ntuple_util.init_analyspar(
        args.fluor, not(args.keepnans), args.stats, args.error, 
        scale=not(args.no_scale), dend=args.dend)

    # session parameters
    analysis_dict["sesspar"] = sess_ntuple_util.init_sesspar(
        args.sess_n, False, args.plane, args.line, args.min_rois, 
        args.pass_fail, args.incl, args.runtype, args.mouse_ns)
    
    # stimulus parameters
    analysis_dict["stimpar"] = sess_ntuple_util.init_stimpar(
        args.stimtype, args.visflow_dir, args.visflow_size, args.gabfr, 
        args.gabk, args.gab_ori, args.pre, args.post)

    # SPECIFIC ANALYSES
    analysis_dict["permpar"] = sess_ntuple_util.init_permpar(
        args.n_perms, args.p_val, args.tails, False)

    analysis_dict["basepar"] = sess_ntuple_util.init_basepar(args.base)

    analysis_dict["idxpar"] = sess_ntuple_util.init_idxpar(args.idx_op, 
        args.idx_feature, args.idx_position)

    analysis_dict["latpar"] = sess_ntuple_util.init_latpar(
        args.lat_method, args.lat_p_val_thr, args.lat_rel_std, 
        not(args.lat_not_unexp_resp))

    # figure parameters
    analysis_dict["figpar"] = sess_plot_util.init_figpar(
        ncols=int(args.ncols), datetime=not(args.no_datetime), 
        overwrite=args.overwrite, save_fig=not(args.not_save_fig), 
        runtype=args.runtype, output=args.output, plt_bkend=args.plt_bkend, 
        fontdir=args.fontdir)

    return analysis_dict


#############################################
def init_mouse_sess(mouse_n, all_sess_ns, sesspar, mouse_df, datadir, 
                    omit_sess=[], fluor="dff", dend="extr", roi=True, 
                    run=False, pupil=False):

    """
    init_mouse_sess(mouse_n, all_sess_ns, sesspar, mouse_df, datadir)

    Initializes the sessions for the specified mouse.

    Required args:
        - mouse_n (int)       : mouse number
        - all_sess_ns (list)  : list of all sessions to include
        - sesspar (SessPar)   : named tuple containing session parameters
        - mouse_df (pandas df): path name of dataframe containing information 
                                  on each session
        - datadir (str)       : path to data directory
    
    Optional args:
        - omit_sess (list): list of sessions to omit
        - dend (str)      : type of dendrites to use ("allen" or "dend")
        - fluor (str)     : if "raw", raw ROI traces are used. If 
                            "dff", dF/F ROI traces are used.
        - dend (str)      : type of dendrites to use ("allen" or "dend")
        - roi (bool)      : if True, ROI data is loaded
                            default: True
        - run (bool)      : if True, running data is loaded
                            default: False
        - pupil (bool)    : if True, pupil data is loaded
                            default: False

    Returns:
        - mouse_sesses (list): list of Session objects for the specified mouse, 
                               with None in the position of missing sessions 
    """

    sesspar_dict = sesspar._asdict()
    sesspar_dict.pop("closest")

    mouse_sesses = []
    for sess_n in all_sess_ns:
        sesspar_dict["sess_n"] = sess_n
        sesspar_dict["mouse_n"] = mouse_n
        sessid = sess_gen_util.get_sess_vals(
            mouse_df, "sessid", omit_sess=omit_sess, **sesspar_dict)
        if len(sessid) == 0:
            sess = [None]
        elif len(sessid) > 1:
            raise RuntimeError(
                "Expected no more than 1 session per mouse/session number."
                )
        else:
            sess = sess_gen_util.init_sessions(
                sessid[0], datadir, mouse_df, sesspar.runtype, full_table=False, 
                fluor=fluor, dend=dend, omit=roi, roi=roi, run=run, 
                pupil=pupil, temp_log="warning")
            if len(sess) == 0:
                sess = [None]
        mouse_sesses.append(sess[0])

    return mouse_sesses


#############################################
def prep_analyses(sess_n, args, mouse_df, parallel=False):
    """
    prep_analyses(sess_n, args, mouse_df)

    Prepares named tuples and sessions for which to run analyses, based on the 
    arguments passed.

    Required args:
        - sess_n (int)          : session number to run analyses on, or 
                                  combination of session numbers to compare, 
                                  e.g. "1v2"
        - args (Argument parser): parser containing all parameters
        - mouse_df (pandas df)  : path name of dataframe containing information 
                                  on each session

    Optional args:
        - parallel (bool): if True, sessions are initialized in parallel 
                           across CPU cores 
                           default: False

    Returns:
        - sessions (list)      : list of sessions, or nested list per mouse 
                                 if sess_n is a combination
        - analysis_dict (dict): dictionary of analysis parameters 
                                (see init_param_cont())
    """

    args = copy.deepcopy(args)

    args.sess_n = sess_n

    analysis_dict = init_param_cont(args)
    analyspar, sesspar, stimpar = [analysis_dict[key] for key in 
        ["analyspar", "sesspar", "stimpar"]]

    roi = (args.datatype == "roi")
    run = (args.datatype == "run")

    sesspar_dict = sesspar._asdict()
    _ = sesspar_dict.pop("closest")

    [all_mouse_ns, all_sess_ns] = sess_gen_util.get_sess_vals(
        mouse_df, ["mouse_n", "sess_n"], omit_sess=args.omit_sess, 
        omit_mice=args.omit_mice, unique=False, **sesspar_dict)

    if args.sess_n in ["any", "all"]:
        all_sess_ns = [n + 1 for n in range(max(all_sess_ns))]
    else:
        all_sess_ns = args.sess_n

    # get session IDs and create Sessions
    all_mouse_ns = sorted(set(all_mouse_ns))

    logger.info(
        f"Loading sessions for {len(all_mouse_ns)} mice...", 
        extra={"spacing": "\n"}
        )
    args_list = [all_sess_ns, sesspar, mouse_df, args.datadir, args.omit_sess, 
        analyspar.fluor, analyspar.dend, roi, run]
    sessions = gen_util.parallel_wrap(
        init_mouse_sess, all_mouse_ns, args_list=args_list, parallel=parallel, 
        use_tqdm=True
        )

    check_all = set([sess for m_sess in sessions for sess in m_sess])
    if len(sessions) == 0 or check_all == {None}:
        raise RuntimeError("No sessions meet the criteria.")

    runtype_str = ""
    if sesspar.runtype != "prod":
        runtype_str = f" ({sesspar.runtype} data)"

    stim_str = stimpar.stimtype
    if stimpar.stimtype == "gabors":
        stim_str = "gabor"
    elif stimpar.stimtype == "visflow":
        stim_str = "visual flow"

    logger.info(
        f"Analysis of {sesspar.plane} responses to {stim_str} "
        f"stimuli{runtype_str}.\nSession {sesspar.sess_n}", 
        extra={"spacing": "\n"})

    return sessions, analysis_dict


#############################################
def get_analysis_fcts():
    """
    get_analysis_fcts()

    Returns dictionary of analysis functions.

    Returns:
        - fct_dict (dict): dictionary where each key is an analysis letter, and
                           records the corresponding function and list of
                           acceptable 'datatype' values
    """

    fct_dict = dict()

    # 0. Plots the difference between unexpected and expected traces across sessions
    fct_dict["s"] = [acr_sess_analys.run_unexp_area_diff, ["roi", "run"]]

    # 1. Plots the difference between unexpected and expected locked to unexpected
    # onset and v.v. across sessions
    fct_dict["l"] = [acr_sess_analys.run_lock_area_diff, ["roi", "run"]]

    # 2. Plots the difference between stimulus and grayscreen, locked to onset 
    # and v.v., across sessions
    fct_dict["a"] = [acr_sess_analys.run_stim_grayscr_diff, ["roi", "run"]]

    # 3. Plots the unexpected and expected traces across sessions
    fct_dict["t"] = [acr_sess_analys.run_unexp_traces, ["roi", "run"]]

    # 4. Plots the unexpected and expected traces locked to unexpected across 
    # sessions
    fct_dict["r"] = [acr_sess_analys.run_lock_traces, ["roi", "run"]]

    # 5. Plots the stimulus onset traces across sessions
    fct_dict["b"] = [acr_sess_analys.run_stim_grayscr, ["roi", "run"]]

    # 6. Plots unexpected event indices across sessions
    fct_dict["i"] = [acr_sess_analys.run_unexp_idx, ["roi", "run"]]

    # 7. Plots unexpected event indices across sessions with common orientations
    fct_dict["m"] = [acr_sess_analys.run_unexp_idx_common_oris, ["roi", "run"]]

    # 8. Plots direction indices across sessions
    fct_dict["d"] = [acr_sess_analys.run_direction_idx, ["roi", "run"]]

    # 9. Plot unexpected event index colormaps across stimulus parameters
    fct_dict["c"] = [acr_sess_analys.run_unexp_idx_cm, ["roi", "run"]]

    # 10. Plots progression of unexpected or expected responses within and 
    # across sessions
    fct_dict["g"] = [acr_sess_analys.run_prog, ["roi", "run"]]

    # 11. Plots unexpected or expected position responses across sessions
    fct_dict["o"] = [acr_sess_analys.run_position, ["roi", "run"]]

    # 12. Plots the unexpected response latencies across sessions
    fct_dict["u"] = [acr_sess_analys.run_unexp_latency, ["roi", "run"]]

    # 13. Plots proportion of ROIs responses to both unexpected response types
    fct_dict["p"] = [acr_sess_analys.run_resp_prop, ["roi"]]

    return fct_dict


#############################################
def run_analyses(sessions, analysis_dict, analyses, datatype="roi", seed=None, 
                 parallel=False):
    """
    run_analyses(sessions, analysis_dict, analyses)

    Runs requested analyses on sessions using the parameters passed.

    Required args:
        - sessions (list)     : list of sessions, possibly nested
        - analysis_dict (dict): analysis parameter dictionary 
                                (see init_param_cont())
        - analyses (str)      : analyses to run
    
    Optional args:
        - datatype (str) : datatype ("run", "roi")
                           default: "roi"
        - seed (int)     : seed to use
                           default: None
        - parallel (bool): if True, some analyses are parallelized 
                           across CPU cores 
                           default: False
    """

    if len(sessions) == 0:
        logger.warning("No sessions meet these criteria.")
        return

    # changes backend and defaults
    plot_util.manage_mpl(cmap=False, **analysis_dict["figpar"]["mng"])
    sess_plot_util.update_plt_linpla()

    fct_dict = get_analysis_fcts()

    args_dict = copy.deepcopy(analysis_dict)
    for key, item in zip(["seed", "parallel", "datatype"], 
        [seed, parallel, datatype]):
        args_dict[key] = item

    # run through analyses
    for analysis in analyses:
        if analysis not in fct_dict.keys():
            raise ValueError(f"{analysis} analysis not found.")
        fct, datatype_req = fct_dict[analysis]
        if datatype not in datatype_req:
            continue
        args_dict_use = gen_util.keep_dict_keys(
            args_dict, inspect.getfullargspec(fct).args)
        fct(sessions=sessions, analysis=analysis, **args_dict_use)
        
        plt.close("all")


#############################################
def main(args):
    """
    main(args)

    Runs analyses with parser arguments.

    Required args:
        - args (dict): parser argument dictionary
    """

    logger_util.set_level(level=args.log_level)

    args.fontdir = DEFAULT_FONTDIR

    if args.dict_path is not None:
        source = "acr_sess"
        if args.modif:
            source = "modif"
        plot_dicts.plot_from_dicts(
            Path(args.dict_path), source=source, plt_bkend=args.plt_bkend, 
            fontdir=args.fontdir, parallel=args.parallel, 
            datetime=not(args.no_datetime), overwrite=args.overwrite)

    else:
        if args.datadir is None: 
            args.datadir = DEFAULT_DATADIR
        else:
            args.datadir = Path(args.datadir)

        mouse_df = DEFAULT_MOUSE_DF_PATH

        args = reformat_args(args)

        analys_pars = prep_analyses(args.sess_n, args, mouse_df, args.parallel)
        
        args.parallel = bool(args.parallel  * (not args.debug))
        run_analyses(*analys_pars, analyses=args.analyses, seed=args.seed,
            parallel=args.parallel, datatype=args.datatype)


#############################################
def parse_args():
    """
    parse_args()

    Returns parser arguments.

    Returns:
        - args (dict): parser argument dictionary
    """

    parser = argparse.ArgumentParser()

    ANALYSIS_STR = " || ".join(
        [f"{key}: {item}" for key, item in ANALYSIS_DESCR.items()])

        # general parameters
    parser.add_argument("--datadir", default=None, 
        help="data directory (if None, uses a directory defined below)")
    parser.add_argument("--output", default=".", type=Path, 
        help="where to store output")
    parser.add_argument("--analyses", default="all", 
        help=("analyses to run, e.g. 'sla', 'all' or 'all_s' (all, save 's'). "
            f"ANALYSES: {ANALYSIS_STR}"))
    parser.add_argument("--datatype", default="roi", 
        help="datatype to use (roi or run)")  
    parser.add_argument("--sess_n", default="1-3",
        help="session range to include, where last value is included, "
            "e.g. 1-3, all")
    parser.add_argument("--mouse_ns", default="all", help="mice to include")
    parser.add_argument("--dict_path", default=None, 
        help=("path to info dictionary or directory of dictionaries from "
            "which to plot data."))

        # technical parameters
    parser.add_argument("--plt_bkend", default=None, 
        help="switch mpl backend when running on server")
    parser.add_argument("--parallel", action="store_true", 
        help="do runs in parallel.")
    parser.add_argument("--debug", action="store_true", 
        help="only enable session loading in parallel")
    parser.add_argument("--seed", default=-1, type=int, 
        help="random seed (-1 for None)")
    parser.add_argument("--log_level", default="info", 
        help="logging level (does not work with --parallel)")

        # session parameters
    parser.add_argument("--runtype", default="prod", help="prod or pilot")
    parser.add_argument("--plane", default="any", help="soma, dend, any")
    parser.add_argument("--min_rois", default=5, type=int, 
        help="min rois criterion")
        # stimulus parameters
    parser.add_argument("--visflow_dir", default="both", 
        help="visual flow dir (right, left, or both)") 
    parser.add_argument("--gabfr", default=3, type=int, 
        help="gabor frame at which to start sequences")  
    parser.add_argument("--post", default=0.45, type=float, 
        help="sec after reference frames")
    parser.add_argument("--stimtype", default="gabors", 
        help="stimulus to analyse")   
        # roi group parameters
    parser.add_argument("--plot_vals", default="unexp", 
        help="plot both (with op applied), unexp or exp")
    
    # generally fixed 
        # analysis parameters
    parser.add_argument("--keepnans", action="store_true", 
        help="keep ROIs containing NaNs or Infs in session.")
    parser.add_argument("--fluor", default="dff", help="raw or dff")
    parser.add_argument("--stats", default="mean", help="plot mean or median")
    parser.add_argument("--error", default="sem", 
        help="sem for SEM/MAD, std for std/qu")    
    parser.add_argument("--dend", default="extr", help="allen, extr")
    parser.add_argument("--no_scale", action="store_true", help="scale ROIs")
        # session parameters
    parser.add_argument("--line", default="any", help="L23, L5")
    parser.add_argument("--closest", action="store_true", 
        help=("if True, the closest session number is used. "
            "Otherwise, only exact."))
    parser.add_argument("--pass_fail", default="P", 
        help="P to take only passed sessions")
    parser.add_argument("--incl", default="any",
        help="include only 'yes', 'no' or 'any'")
        # stimulus parameters
    parser.add_argument("--visflow_size", default=128, 
        help="visual flow size (128, 256, or both)")
    parser.add_argument("--gabk", default=16,
        help="kappa value (4, 16, or both)")    
    parser.add_argument("--gab_ori", default="all",
        help="gabor orientation values (0, 45, 90, 135, 180, 225, all)")    
    parser.add_argument("--pre", default=0, type=float, 
    help="sec before frame")
        # permutation parameters
    parser.add_argument("--n_perms", default=10000, type=int, 
        help="nbr of permutations")
    parser.add_argument("--tails", default="2", 
        help="tails for perm analysis (2, lo, up)")
    parser.add_argument("--p_val", default=0.05, type=float,
        help="p-value for significance tests")

        # baseline parameter
    parser.add_argument("--base", default=0, type=float,
        help="baseline for unexpected difference calculations.")

         # index parameters 
    parser.add_argument("--idx_feature", default="by_exp",
        help="type of feature to use as index ('by_exp' or 'unexp_lock' "
            "for either stimulus or 'prog_unexp'.")
    parser.add_argument("--idx_op", default="d-prime",
        help="type of index to use ('d-prime', 'diff', 'rel_diff'.")
    parser.add_argument("--idx_position", default=0,
        help="if using a prog feature, position of unexp/exp to use in "
            "index.")

        # latency parameters
    parser.add_argument("--lat_method", default="ttest", 
        help="latency calculation method ('ratio' or 'ttest')")
    parser.add_argument("--lat_p_val_thr", default="0.005", type=float,
        help="p-value threshold for ttest method")
    parser.add_argument("--lat_rel_std", default="0.5", type=float,
        help="relative st. dev. threshold for ratio method")
    parser.add_argument("--lat_not_unexp_resp", action="store_true", 
         help="don't use only unexpected responsive ROIs")

        # figure parameters
    parser.add_argument("--ncols", default=4, help="number of columns")
    parser.add_argument("--no_datetime", action="store_true",
        help="create a datetime folder")
    parser.add_argument("--overwrite", action="store_true", 
        help="allow overwriting")
    parser.add_argument("--not_save_fig", action="store_true", 
        help="don't save figures")
        # plot using modif_analys_plots (only if plotting from dictionary)
    parser.add_argument("--modif", action="store_true", 
        help=("plot from dictionary using modified plot functions"))

    args = parser.parse_args()

    return args


#############################################
if __name__ == "__main__":

    args = parse_args()
    main(args)

