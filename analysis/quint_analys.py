"""
quint_analys.py

This module contains functions to run quintile analyses on data
generated by the AIBS experiments for the Credit Assignment Project

Authors: Colleen Gillon

Date: October, 2018

Note: this code uses python 3.7.

"""

import copy
import numpy as np

from util import gen_util, math_util
from sess_util import sess_gen_util, sess_ntuple_util


#############################################
def quint_segs(stim, stimpar, n_quints=4, qu_idx='all', surp='any', 
               empty_ok=False, remconsec=False, by_surp_len=False):
    """
    quint_segs(stim, stimpar)

    Returns segments split into quintiles.
    
    Required args:
        - stim (Stim)      : stim object
        - stimpar (StimPar): named tuple containing stimulus parameters

    Optional args:
        - n_quints (int)      : number of quintiles to split data into
                                default: 4
        - qu_idx (str or list): indices of quintiles to retain
                                default: 'all'
        - surp (int or list)  : surprise values to include (e.g., 0 or 1)
                                default: 'any'
        - empty_ok (bool)     : if True, catches error if no segments respond 
                                to criteria and returns empty qu_segs and 
                                qu_counts = 0.
                                default: False 
        - remconsec (bool)    : if True, consecutive segments are removed
                                default: False
        - by_surp_len (bool)  : if True, consecutive segments are removed and
                                the number of consecutive segments 
                                corresponding to each retained segment is also 
                                returned
                                default: False

    Returns:
        - qu_segs (list)  : list of sublists for each quintile, each containing 
                            segment numbers for that quintile
        - qu_counts (list): list of number of segments in each quintile
        if by_surp_len:
            - qu_n_consec (list): list of sublists for each quintile, each
                                  containing the number of consecutive segments
                                  corresponding to the values in qu_segs
    """

    if qu_idx == 'all':
        qu_idx = list(range(n_quints))
    else:
        qu_idx = gen_util.pos_idx(qu_idx, n_quints)

    # get all seg values (for all gabor frames and orientations)
    try:
        all_segs = stim.get_segs_by_criteria(gabk=stimpar.gabk, 
                                           bri_dir=stimpar.bri_dir,
                                           bri_size=stimpar.bri_size, by='seg')
    except ValueError as err:
        if empty_ok:
            all_segs = []
        else:
            raise err

    # get seg ranges for each quintile [[start, end], [start, end], etc.] 
    qu_segs = []
    qu_counts = []

    # get the min and max seg numbers for stimulus
    if len(all_segs) != 0:
        seg_min = np.min(all_segs)
        seg_max = np.max(all_segs)+1
    else:
        seg_min = 0
        seg_max = 0
    
    # calculate number of segments in each quintile (ok if not round number)
    qu_len = (seg_max - seg_min)/float(n_quints)

    # get all seg values
    try:
        all_segs = stim.get_segs_by_criteria(gabfr=stimpar.gabfr,
                                              gabk=stimpar.gabk, 
                                              gab_ori=stimpar.gab_ori,
                                              bri_dir=stimpar.bri_dir,
                                              bri_size=stimpar.bri_size,
                                              surp=surp, by='seg', 
                                              remconsec=remconsec)
    except ValueError as err:
        if empty_ok:
            all_segs = []
        else:
            raise err                                         
    
    if by_surp_len:
        all_segs, n_consec = gen_util.consec(all_segs)
        qu_n_consec = []

    for q in qu_idx:
        qu_segs.append([seg for seg in all_segs 
                            if (seg >= q * qu_len + seg_min and 
                                seg < (q + 1) * qu_len + seg_min)])
        qu_counts.extend([len(qu_segs[-1])])
        if by_surp_len: # also include lengths
            qu_n_consec.append([n for i, n in enumerate(n_consec) 
                                  if (all_segs[i] >= q * qu_len + seg_min and 
                                    all_segs[i] < (q + 1) * qu_len + seg_min)])

    if by_surp_len:
        return qu_segs, qu_counts, qu_n_consec
    else:
        return qu_segs, qu_counts


#############################################
def samp_quint_segs(qu_segs, seg_pre=0, seg_post=0):
    """
    samp_quint_segs(qu_segs, seg_pre, seg_post)

    Returns segments sampled from each series of consecutive segments, still 
    split into quintiles.

    Required args:
        - qu_segs (list)  : list of sublists for each quintile, each containing 
                            segment numbers for that quintile

    Optional args:
        - seg_pre (int) : minimum difference between the sampled segment number 
                          and the lowest segment number in each consecutive 
                          series  
                          default: 0
        - seg_post (int): minimum difference between the sampled segment number 
                          and the highest segment number in each consecutive 
                          series  
                          default: 0

    Returns:
        - qu_segs (list)  : list of sublists for each quintile, each containing 
                            the sampled segment numbers for that quintile
        - qu_counts (list): list of number of segments in each quintile

    """
    seg_pre = int(np.around(seg_pre))
    seg_post = int(np.around(seg_post))

    qu_segs_flat = [seg for segs in qu_segs for seg in segs]

    if min(np.diff(qu_segs_flat)) not in [1, 4]:
        raise ValueError(('No consecutive segments (1 or 4 interval) found in '
                          ' qu_segs.'))

    all_segs, n_consec = gen_util.consec(qu_segs_flat, smallest=True)


    samp_segs = []
    i = 0
    for seg, n in zip(all_segs, n_consec):
        qu_sub = qu_segs_flat[i : i + n]
        min_seg = min(qu_sub) + seg_pre
        max_seg = max(qu_sub) - seg_post
        if min_seg < max_seg:
            qu_samp = [seg for seg in qu_sub if seg in range(min_seg, max_seg)]
            samp_seg = np.random.choice(qu_samp)
            samp_segs.append(samp_seg)
        i += n
    
    qu_samp_segs = []
    qu_counts = []
    for sub_segs in qu_segs:
        min_seg = min(sub_segs)
        max_seg = max(sub_segs)
        qu_samps = [seg for seg in samp_segs if seg in range(min_seg, max_seg)]
        qu_samp_segs.append(qu_samps)
        qu_counts.append(len(qu_samps))

    return qu_samp_segs, qu_counts


#############################################
def trace_stats_by_qu(stim, qu_segs, pre, post, analyspar, byroi=True, 
                      integ=False, ret_arr=False, nan_empty=False, 
                      baseline=None, datatype='roi'):
    """
    trace_stats_by_qu(stim, qu_seg, pre, post, analyspar)

    Returns trace statistics for the quintiles of interest. If ret_arr, also
    returns trace data arrays.

    Required args:
        - stim (Stim object)   : stim object
        - qu_segs (dict)       : list of sublists for each quintile, each 
                                 containing segment numbers for that quintile
        - pre (num)            : range of frames to include before each frame 
                                 reference (in s)
        - post (num)           : range of frames to include after each frame 
                                 reference (in s)
        - analyspar (AnalysPar): named tuple containing analysis parameters
    
    Optional args:
        - byroi (bool)    : If datatype is 'roi', if True, returns statistics 
                            for each ROI. If False, returns statistics 
                            across ROIs.
                            default: True
        - integ (bool)    : if True, dF/F is integrated over sequences
                            default: False
        - ret_arr (bool)  : if True, data arrays are returned also
                            default: False
        - nan_empty (bool): if a quintile is empty, returns NaN arrays instead
                            of an error (1 sequence, for qu_array) 
                            default: False
        - baseline (num)  : number of seconds to use as baseline. If None,
                            data is not baselined.
                            default: None
        - datatype (str)  : datatype, i.e. ROIs or running
                            default: 'roi'

    Returns:
        - xran (1D array)          : time values for the 2p frames
        - qu_stats (2 to 4D array) : trace data statistics, structured as:
                                         quintiles x
                                         stats (me, err) x
                                         (ROIs if byroi x)
                                         (frames if not integ)
        if ret_arr, also:
        - qu_array (list)          : list per quintile of 1-3D arrays of trace 
                                     data structured as:
                                        (ROIs x) sequences 
                                        (x frames if not integ)
    """
  
    qu_stats, qu_array = [], []
    for segs in qu_segs:
        rep_nan = False
        for _ in range(2): # allows retrying if nan_empty is True
            try:
                if datatype == 'roi':
                    twop_fr = stim.get_twop_fr_by_seg(segs, first=True)
                    trace_info = stim.get_roi_trace_stats(twop_fr, pre, post, 
                                        byroi=byroi, fluor=analyspar.fluor, 
                                        remnans=analyspar.remnans, 
                                        stats=analyspar.stats, 
                                        error=analyspar.error,
                                        integ=integ, ret_arr=ret_arr, 
                                        baseline=baseline)
                elif datatype == 'run':
                    stim_fr = stim.get_stim_fr_by_seg(segs, first=True)
                    trace_info = stim.get_run_array_stats(stim_fr, pre, post, 
                                        remnans=analyspar.remnans,
                                        stats=analyspar.stats, 
                                        error=analyspar.error,
                                        integ=integ, ret_arr=ret_arr, 
                                        baseline=baseline)
                else:
                    gen_util.accepted_values_error('datatype', datatype, 
                                                    ['roi', 'run'])
                break # break out of for loop if successful
            except ValueError as err:
                if nan_empty and 'No frames' in str(err):
                    segs = [10]     # dummy segment to use
                    rep_nan = True # later, replace values with NaNs
                else:
                    raise err

        xran = trace_info[0]
        # array: stats [me, err] (x ROI) (x frames)
        trace_stats = trace_info[1]
        if rep_nan: # replace dummy values with NaNs
            trace_stats = np.full_like(trace_stats, np.nan)
        qu_stats.append(trace_stats)
        if ret_arr:
            trace_array = trace_info[2]
            if rep_nan: # replace dummy values with NaNs
                trace_array = np.full_like(trace_array, np.nan)
            qu_array.append(trace_array)

    qu_stats = np.asarray(qu_stats)

    if ret_arr:
        return xran, qu_stats, qu_array
    else:
        return xran, qu_stats


#############################################
def trace_stats_by_qu_sess(sessions, analyspar, stimpar, n_quints=4, 
                           qu_idx='all', byroi=True, bysurp=False, integ=False, 
                           ret_arr=False, nan_empty=False, lock='no', 
                           baseline=None, sample_reg=False, datatype='roi'):
    """
    trace_stats_by_qu_sess(sessions, analyspar, stimpar)

    Returns trace statistics for the quintiles of interest for each
    session and surprise value, for the datatype of interest.

    Required args:
        - sessions (list)      : list of Session objects
        - analyspar (AnalysPar): named tuple containing analysis parameters
        - stimpar (StimPar)    : named tuple containing stimulus parameters
        
    Optional args:
        - n_quints (int)      : number of quintiles to divide sessions into
                                default: 4
        - qu_idx (str or list): indices of quintiles to retain
                                default: 'all'
        - byroi (bool)        : If datatype is 'roi', if True, returns 
                                statistics for each ROI. If False, returns 
                                statistics across ROIs.
                                default: True
        - bysurp (bool)       : if True, quintiles are separated into surprise 
                                and no surprise groups.
                                default: False
        - integ (bool)        : if True, dF/F is integrated over sequences
                                default: False
        - ret_arr (bool)      : if True, data arrays are returned also
                                default: False
        - nan_empty (bool)    : if a quintile is empty, return NaN arrays 
                                (avoids an error)
                                default: False
        - lock (bool)         : if 'surp', 'reg', 'regsamp', only the first 
                                surprise or regular segments are retained.
                                If 'both'
                                (bysurp is ignore). 
                                default: False
        - baseline (num)      : number of seconds to use as baseline. If None,
                                data is not baselined.
                                default: None
        - datatype (str)      : datatype, i.e. ROIs or running
                                default: 'roi'

    Returns:
        - xran (1D array)          : time values for the 2p frames
        - all_stats (list)         : list of 2 to 5D arrays of trace data 
                                     statistics for each session, structured as:
                                         (surp if bysurp x)
                                         quintiles x
                                         stats (me, err) x
                                         (ROIs if byroi x)
                                         (frames if not integ)
        - all_counts (nested list) : list of number of sequences, 
                                     structured as:
                                        sess 
                                        x (surp if bysurp or lock is 'both') 
                                        x quintiles
        if ret_arr:
        - all_arrays (nested lists): list of data trace arrays, structured as:
                                        session (x surp if bysurp) x quintile 
                                        of 1 to 3D arrays: 
                                            (ROI x) sequences 
                                            (x frames if not integ)
    """

    remconsec, sample = False, False
    surp_vals = ['any']
    if lock in ['surp', 'reg', 'both']:
        remconsec = True
        surp_vals = [1, 0]
        if lock == 'reg':
            surp_vals = [0]
        elif lock == 'surp':
            surp_vals = [1]
        if stimpar.stimtype == 'gabors' and stimpar.gabfr != 'any':
            stimpar = stimpar._asdict()
            stimpar['gabfr'] = 'any'
            stimpar = sess_ntuple_util.init_stimpar(**stimpar)
            print(('If locking to surprise, regular onset or both, '
                   'stimpar.gabfr is set to `any`.'))
    elif lock == 'regsamp':
        remconsec, sample = False, True
        surp_vals = [0]
    elif bysurp:
        surp_vals = [0, 1]    

    all_counts, all_stats, all_arrays = [], [], []
    for sess in sessions:
        stim = sess.get_stim(stimpar.stimtype)
        sess_counts, sess_stats, sess_arrays = [], [], []
        for surp in surp_vals:
            qu_segs, qu_counts = quint_segs(stim, stimpar, n_quints, qu_idx, 
                                            surp, empty_ok=nan_empty, 
                                            remconsec=remconsec)
            if sample:
                pre_seg = stimpar.pre/stim.seg_len_s
                post_seg = stimpar.post/stim.seg_len_s
                qu_segs, qu_counts = samp_quint_segs(qu_segs, pre_seg, post_seg)
            sess_counts.append(qu_counts)
            trace_info = trace_stats_by_qu(stim, qu_segs, stimpar.pre,
                                           stimpar.post, analyspar, 
                                           byroi=byroi, integ=integ, 
                                           ret_arr=ret_arr, 
                                           nan_empty=nan_empty, 
                                           baseline=baseline, datatype=datatype)
            xran = trace_info[0]
            sess_stats.append(trace_info[1])
            if ret_arr:
                sess_arrays.append(trace_info[2])
        if len(surp_vals) > 1:
            sess_stats = np.asarray(sess_stats)
        else:
            sess_stats = np.asarray(sess_stats[0]) # list of length 1
            sess_counts = sess_counts[0]
            if ret_arr:
                sess_arrays = sess_arrays[0] # list of length 1
        all_counts.append(sess_counts)
        all_stats.append(sess_stats)
        if ret_arr:
            all_arrays.append(sess_arrays)

    if ret_arr:
        return xran, all_stats, all_counts, all_arrays
    else:
        return xran, all_stats, all_counts


#############################################
def trace_stats_by_surp_len_sess(sessions, analyspar, stimpar, n_quints=4, 
                                 qu_idx='all', byroi=True, integ=False, 
                                 ret_arr=False, nan_empty=False, 
                                 baseline=None, datatype='roi'):
    """
    trace_stats_by_surp_len_sess(sessions, analyspar, stimpar)

    Returns trace statistics for the quintiles of interest for each
    session and surprise length value, for the datatype of interest.

    Required args:
        - sessions (list)      : list of Session objects
        - analyspar (AnalysPar): named tuple containing analysis parameters
        - stimpar (StimPar)    : named tuple containing stimulus parameters
        
    Optional args:
        - n_quints (int)      : number of quintiles to divide sessions into
                                default: 4
        - qu_idx (str or list): indices of quintiles to retain
                                default: 'all'
        - byroi (bool)        : If datatype is 'roi', if True, returns 
                                statistics for each ROI. If False, returns 
                                statistics across ROIs.
                                default: True
        - integ (bool)        : if True, dF/F is integrated over sequences
                                default: False
        - ret_arr (bool)      : if True, data arrays are returned also
                                default: False
        - nan_empty (bool)    : if a quintile is empty, return NaN arrays 
                                (avoids an error)
                                default: False
        - baseline (num)      : number of seconds to use as baseline. If None,
                                data is not baselined.
                                default: None
        - datatype (str)      : datatype, i.e. ROIs or running
                                default: 'roi'

    Returns:
        - xran (1D array)         : time values for the 2p frames
        - all_stats (list)        : list of 2 to 5D arrays of trace data 
                                    statistics for each session, structured as:
                                        surp_len x
                                        quintiles x
                                        stats (me, err) x
                                        (ROIs if byroi x)
                                        (frames if not integ)
        - all_counts (nested list) : list of number of sequences, 
                                     structured as:
                                        sess x surp_len x quintiles
        - all_n_consec (list)      : unique values of number of consecutive 
                                     segments, by session  
        if ret_arr:
        - all_arrays (nested lists): list of data trace arrays, structured as:
                                        session x surp_len x quintile 
                                        of 1 to 3D arrays: 
                                            (ROI x) sequences 
                                            (x frames if not integ)
    """

    if stimpar.stimtype == 'gabors' and stimpar.gabfr != 'any':
        stimpar = stimpar._asdict()
        stimpar['gabfr'] = 'any'
        stimpar = sess_ntuple_util.init_stimpar(**stimpar)
        print(('If locking to surprise onset, stimpar.gabfr is set to '
               '`any`.'))

    all_counts, all_stats, all_arrays, all_n_consec = [], [], [], []
    for sess in sessions:
        stim = sess.get_stim(stimpar.stimtype)
        sess_counts, sess_stats, sess_arrays = [], [], []
        qu_segs, _, qu_n_consec = quint_segs(stim, stimpar, n_quints, qu_idx, 
                                             1, empty_ok=nan_empty, 
                                             by_surp_len=True)
        n_consec_flat   = [n for sub_ns in qu_n_consec for n in sub_ns]
        all_n_consec.append(sorted(set(n_consec_flat)))

        for n_consec in all_n_consec[-1]:
            sub_segs, sub_counts = [], []
            # retain segments with correct number of consecutive values
            for segs, ns in zip(qu_segs, qu_n_consec): 
                idx = np.where(np.asarray(ns) == n_consec)[0]
                sub_segs.append([segs[i] for i in idx])
                sub_counts.append(len(idx))
            sess_counts.append(sub_counts)
            trace_info = trace_stats_by_qu(stim, sub_segs, stimpar.pre,
                                           stimpar.post, analyspar, 
                                           byroi=byroi, integ=integ, 
                                           ret_arr=ret_arr, 
                                           nan_empty=nan_empty, 
                                           baseline=baseline, datatype=datatype)
            xran = trace_info[0]
            sess_stats.append(trace_info[1])
            if ret_arr:
                sess_arrays.append(trace_info[2])
        all_counts.append(sess_counts)
        all_stats.append(np.asarray(sess_stats))
        if ret_arr:
            all_arrays.append(sess_arrays)

    if ret_arr:
        return xran, all_stats, all_counts, all_n_consec, all_arrays
    else:
        return xran, all_stats, all_counts, all_n_consec


#############################################
def run_mag_permute(all_data_perm, act_mag_me_rel, act_L2_rel, n_regs, permpar, 
                    op_qu='diff', op_grp='diff', stats='mean', nanpol=None):
    """
    run_mag_permute(all_data_perm, act_mag_rel, act_L2_rel, n_reg, permpar)

    Returns the results of a permutation analysis of difference or ratio 
    between 2 quintiles of the magnitude change or L2 norm between regular and 
    surprise activity.

    Required args:
        - all_data_perm (2D array): Data from both groups for permutation, 
                                    structured as:
                                        ROI x seqs
        - act_mag_rel (num)       : Real mean/median magnitude difference
                                    between quintiles
        - act_L2_rel (num)        : Real L2 difference between quintiles
        - n_regs (list)           : List of number of regular sequences in
                                    each quintile
        - permpar (PermPar)       : named tuple containing permutation 
                                    parameters
    
    Optional args:
        - op_qu (str) : Operation to use in comparing the last vs first 
                        quintile ('diff' or 'ratio')
                        default: 'diff'       
        - op_grp (str): Operation to use in comparing groups 
                        (e.g., surprise vs regular data) ('diff' or 'ratio')
                        default: 'diff' 
        - stats (str) : Statistic to take across group sequences, and then 
                        across magnitude differences ('mean' or 'median')
                        default: 'mean'
        - nanpol (str): Policy for NaNs, 'omit' or None when taking statistics
                        default: None
    
    Returns:
        - signif (list) : list of significance results ('up', 'lo' or 'no') for 
                          magnitude, L2
        - threshs (list): list of thresholds (1 if 1-tailed analysis, 
                          2 if 2-tailed) for magnitude, L2
    """

    if len(all_data_perm) != 2 or len(n_regs) !=2:
        raise ValueError('all_data_perm and n_regs must have length of 2.')

    all_rand_vals = [] # qu x grp x ROI x perms
    # for each quintile
    for q, perm_data in enumerate(all_data_perm):
        qu_vals = math_util.permute_diff_ratio(perm_data, n_regs[q], 
                                             permpar.n_perms, stats, 
                                             nanpol=nanpol, op='none')
        all_rand_vals.append(qu_vals)

    all_rand_vals = np.asarray(all_rand_vals)
    # get absolute change stats and retain mean/median only
    rand_mag_me = math_util.calc_mag_change(all_rand_vals, 0, 2, order='stats', 
                                            op=op_qu, stats=stats)[0]
    rand_L2 = math_util.calc_mag_change(all_rand_vals, 0, 2, order=2, op=op_qu)

    # take diff/ratio between grps
    rand_mag_rel = math_util.calc_op(rand_mag_me, op_grp, dim=0)
    rand_L2_rel  = math_util.calc_op(rand_L2, op_grp, dim=0)

    # check significance (returns list although only one result tested)
    mag_sign, mag_th = math_util.id_elem(rand_mag_rel, act_mag_me_rel, 
                                    permpar.tails, permpar.p_val, ret_th=True)
    L2_sign, L2_th   = math_util.id_elem(rand_L2_rel, act_L2_rel, permpar.tails, 
                                    permpar.p_val, ret_th=True)
    
    mag_signif, L2_signif = ['no', 'no']
    if str(permpar.tails) == '2':
        if len(mag_sign[0]) == 1:
            mag_signif = 'lo'
        elif len(mag_sign[1]) == 1:
            mag_signif = 'up'
        if len(L2_sign[0]) == 1:
            L2_signif = 'lo'
        elif len(L2_sign[1]) == 1:
            L2_signif = 'up'
    elif permpar.tails in ['lo', 'up']:
        if len(mag_sign) == 1:
            mag_signif = permpar.tails
        if len(L2_sign) == 1:
            L2_signif = permpar.tails

    signif  = [mag_signif, L2_signif]
    threshs = [mag_th[0], L2_th[0]]

    return signif, threshs


#############################################
def qu_mags(all_data, permpar, mouse_ns, lines, stats='mean', error='sem', 
            nanpol=None, op_qu='diff', op_surp='diff', print_vals=True):
    """
    qu_mags(all_data, permpar, mouse_ns, lines)

    Returns a dictionary containing the results of the magnitudes and L2 
    analysis, as well as the results of the permutation test.

    Specifically, magnitude and L2 norm are calculated as follows: 
        - Magnitude: for surp and regular segments: 
                         mean/median across ROIs of
                             diff/ratio in average activity between 2 quintiles
        - L2 norm:   for surp and regular segments: 
                         L2 norm across ROIs of
                             diff/ratio in average activity between 2 quintiles
    
    Significance is assessed based on the diff/ratio between surprise and 
    regular magnitude/L2 norm results.

    Optionally, the magnitudes and L2 norms are printed for each session, with
    significance indicated.

    Required args:
        - all_data (list)  : nested list of data, structured as:
                                 session x surp x qu x array[(ROI x) seqs]
        - permpar (PermPar): named tuple containing permutation parameters
        - mouse_ns (list)  : list of mouse numbers (1 per session)
        - lines (list)     : list of mouse lines (1 per session)

    Optional args:
        - stats (str)      : statistic to take across segments, (then ROIs) 
                             ('mean' or 'median')
                             default: 'mean'
        - error (str)      : statistic to take across segments, (then ROIs) 
                             ('std' or 'sem')
                             default: 'sem'
        - nanpol (str)     : policy for NaNs, 'omit' or None when taking 
                             statistics
                             default: None
        - op_qu (str)      : Operation to use in comparing the last vs first 
                             quintile ('diff' or 'ratio')
                             default: 'diff'       
        - op_surp (str)    : Operation to use in comparing the surprise vs 
                             regular, data ('diff' or 'ratio')
                             default: 'diff' 
        - print_vals (bool): If True, the magnitudes and L2 norms are printed
                             for each session, with significance indicated.

    Returns:
        - mags (dict): dictionary containing magnitude and L2 data to plot.
            ['L2'] (3D array)        : L2 norms, structured as: 
                                           sess x scaled x surp
            ['mag_st'] (4D array)    : magnitude stats, structured as: 
                                           sess x scaled x surp x stats
            ['L2_rel_th'] (2D array) : L2 thresholds calculated from 
                                       permutation analysis, structured as:
                                           sess x tail(s)
            ['mag_rel_th'] (2D array): magnitude thresholds calculated from
                                       permutation analysis, structured as:
                                           sess x tail(s)
            ['L2_sig'] (list)        : L2 significance results for each session 
                                       ('hi', 'lo' or 'no')
            ['mag_sig'] (list)       : magnitude significance results for each 
                                       session 
                                           ('hi', 'lo' or 'no')
    """


    n_sess = len(all_data)
    n_qu   = len(all_data[0][0])
    scales = [False, True]
    surps    = ['reg', 'surp']
    stat_len = 2 + (stats == 'median' and error == 'std')
    tail_len = 1 + (str(permpar.tails) == '2')

    if n_qu != 2:
        raise ValueError('Expected 2 quintiles, but found {}.'.format(n_qu))
    if len(surps) != 2:
        raise ValueError(('Expected a length 2 surprise dim, '
                          'but found length {}.').format(len(surps)))
    
    mags = {'mag_st': np.empty([n_sess, len(scales), 
                                len(surps), stat_len]),
            'L2'    : np.empty([n_sess, len(scales), len(surps)])
           }
    
    for lab in ['mag_sig', 'L2_sig']:
        mags[lab] = []
    for lab in ['mag_rel_th', 'L2_rel_th']:
        mags[lab] = np.empty([n_sess, tail_len])

    all_data = copy.deepcopy(all_data)
    for i in range(n_sess):
        print('\nMouse {}, {}:'.format(mouse_ns[i], lines[i]))
        sess_data_me = []
        # number of regular sequences
        n_regs = [all_data[i][0][q].shape[-1] for q in range(n_qu)]
        for s in range(len(surps)):
            # take the mean for each quintile
            data_me = np.asarray([math_util.mean_med(all_data[i][s][q], stats, 
                                                     axis=-1, nanpol=nanpol) 
                                                     for q in range(n_qu)])
            if len(data_me.shape) == 1:
                # add dummy ROI-like axis, e.g. for run data
                data_me = data_me[:, np.newaxis]
                all_data[i][s] = [qu_data[np.newaxis, :] 
                                  for qu_data in all_data[i][s]]
            mags['mag_st'][i, 0, s] = math_util.calc_mag_change(data_me, 0, 1, 
                                                    order='stats', op=op_qu, 
                                                    stats=stats, error=error)
            mags['L2'][i, 0, s] = math_util.calc_mag_change(data_me, 0, 1, 
                                                            order=2, op=op_qu)
            sess_data_me.append(data_me)
        # scale
        sess_data_me = np.asarray(sess_data_me)
        mags['mag_st'][i, 1] = math_util.calc_mag_change(sess_data_me, 1, 2, 
                                        order='stats', op=op_qu, stats=stats, 
                                        error=error, scale=True, axis=0, pos=0, 
                                        sc_type='unit').T
        mags['L2'][i, 1] = math_util.calc_mag_change(sess_data_me, 1, 2, 
                                    order=2, op=op_qu, stats=stats, scale=True, 
                                    axis=0, pos=0, sc_type='unit').T
        
        # diff/ratio for permutation test
        act_mag_rel = math_util.calc_op(mags['mag_st'][i, 0, :, 0], op=op_surp)
        act_L2_rel  = math_util.calc_op(mags['L2'][i, 0, :], op=op_surp)

        # concatenate regular and surprise sequences for each quintile
        all_data_perm = [np.concatenate([all_data[i][0][q], all_data[i][1][q]], 
                                        axis=1) for q in range(n_qu)]
        
        signif, ths = run_mag_permute(all_data_perm, act_mag_rel, act_L2_rel, 
                                      n_regs, permpar, op_qu, op_surp, stats, 
                                      nanpol)
        
        mags['mag_sig'].append(signif[0])
        mags['L2_sig'].append(signif[1])
        mags['mag_rel_th'][i] = np.asarray(ths[0])
        mags['L2_rel_th'][i] = np.asarray(ths[1])

        # prints results 
        if print_vals:
            sig_symb = ['', '']
            for si, sig in enumerate(signif):
                if sig != 'no':
                    sig_symb[si] = '*'

            vals = [mags['mag_st'][i, 0, :, 0], mags['L2'][i, 0, :]]
            names = ['{} mag'.format(stats).capitalize(), 'L2']
            for v, (val, name) in enumerate(zip(vals, names)):
                for s, surp in zip([0, 1], ['(reg) ', '(surp)']):
                    print('    {} {}: {:.4f}{}'.format(name, surp, val[s], 
                                                       sig_symb[v]))
        
    return mags


