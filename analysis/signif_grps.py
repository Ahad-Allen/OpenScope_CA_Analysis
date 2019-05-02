"""
signif_grps.py

This module contains functions to run analyses of ROI groups showing
significant differences between surprise and regular sequences in the data 
generated by the AIBS experiments for the Credit Assignment Project

Authors: Colleen Gillon

Date: October, 2018

Note: this code uses python 2.7.

"""

import numpy as np

from sess_util import sess_ntuple_util
from util import gen_util, math_util



#############################################
def sep_grps(sign_rois, nrois, grps='all', tails='2', add_reg=False):
    """
    sep_grps(sign_rois, nrois)

    Separate ROIs into groups based on whether their first/last quintile was
    significant in a specific tail.

    Required args:
        - sign_rois (nested list): list of significant ROIs, structured as:
                                       quintile (x tail) 
        - nrois (int)            : total number of ROIs in data (signif or not)
    Optional args:
        - grps (str or list): set of groups or list of sets of groups to 
                              return, e.g., 'all', 'change', 'no_change', 
                              'reduc', 'incr'
                              default: 'all'
        - tails (str)       : tail(s) used in analysis: 'up', 'lo' or 2
                              default: 2
        - add_reg (bool)    : if True, group of ROIs showing no significance in 
                              either is included in the groups returned
                              default: False 
    Returns:
        - roi_grps (list)   : lists structured as follows:
                              if grp parameter includes only one set, 
                                  ROIs per roi group
                              otherwise: sets x roi grps
                              numbers included in the group
        - grp_names (list)  : if grp parameter includes only one set, list of 
                              names of roi grps (order preserved)
                              otherwise: list of sublists per set, each 
                              containing names of roi grps per set
    """

    grps = gen_util.list_if_not(grps)
    # get ROI numbers for each group
    if tails in ['up', 'lo']:
        # sign_rois[first/last]
        all_rois  = range(nrois)
        surp_surp = list(set(sign_rois[0]) & set(sign_rois[1]))
        surp_reg  = list(set(sign_rois[0]) - set(sign_rois[1]))
        reg_surp  = list(set(sign_rois[1]) - set(sign_rois[0]))
        reg_reg   = list(set(all_rois) - set(surp_surp) - 
                         set(surp_reg) - set(reg_surp))
        # to store stats
        roi_grps  = [surp_surp, surp_reg, reg_surp, reg_reg]
        grp_names = ['surp_surp', 'surp_reg', 'reg_surp', 'reg_reg']
        reg_ind = 3
        grp_inds = []
        for i, g in enumerate(grps):
            if g == 'all':
                grp_ind = range(len(roi_grps))
            elif g == 'change':
                grp_ind = [1, 2]
            elif g == 'no_change':
                grp_ind = [0, 3]
            elif g == 'reduc':
                grp_ind = [1]
            elif g == 'incr':
                grp_ind = [2]
            else:
                gen_util.accepted_values_error('grps', g, ['all', 'change', 
                                               'no_change', 'reduc', 'incr'])
            if add_reg and reg_ind not in grp_ind:
                grp_ind.extend([reg_ind])
            grp_inds.append(sorted(grp_ind))

    elif str(tails) == '2':
        # sign_rois[first/last][lo/up]
        all_rois = range(nrois)         
        surp_up_surp_up = list(set(sign_rois[0][1]) & set(sign_rois[1][1]))
        surp_up_surp_lo = list(set(sign_rois[0][1]) & set(sign_rois[1][0]))
        surp_lo_surp_up = list(set(sign_rois[0][0]) & set(sign_rois[1][1]))
        surp_lo_surp_lo = list(set(sign_rois[0][0]) & set(sign_rois[1][0]))

        surp_up_reg = list((set(sign_rois[0][1]) - set(sign_rois[1][1]) - 
                                set(sign_rois[1][0])))
        surp_lo_reg = list((set(sign_rois[0][0]) - set(sign_rois[1][1]) -
                                set(sign_rois[1][0])))
        
        reg_surp_up = list((set(sign_rois[1][1]) - set(sign_rois[0][1]) - 
                                set(sign_rois[0][0])))
        reg_surp_lo = list((set(sign_rois[1][0]) - set(sign_rois[0][1]) -
                                set(sign_rois[0][0])))
        
        reg_reg = list((set(all_rois) - set(sign_rois[0][1]) -
                                set(sign_rois[1][1]) - set(sign_rois[0][0]) -
                                set(sign_rois[1][0])))
        # to store stats
        roi_grps = [surp_up_surp_up, surp_up_surp_lo, surp_lo_surp_up, 
                    surp_lo_surp_lo, surp_up_reg, surp_lo_reg, 
                    reg_surp_up, reg_surp_lo, reg_reg]
        reg_ind = 8 # index of reg_reg
        # group names 
        grp_names = ['surpup_surpup', 'surpup_surplo', 'surplo_surpup', 
                     'surplo_surplo', 'surpup_reg', 'surplo_reg', 
                     'reg_surpup', 'reg_surplo', 'reg_reg']
        reg_ind = 8
        grp_inds = []
        for i, g in enumerate(grps):
            if g == 'all':
                grp_ind = range(len(roi_grps))
            elif g == 'change':
                grp_ind = [1, 2, 4, 5, 6, 7]
            elif g == 'no_change':
                grp_ind = [0, 3, 8]
            elif g == 'reduc':
                grp_ind = [1, 4, 7]
            elif g == 'incr':
                grp_ind = [2, 5, 6]
            else:
                gen_util.accepted_values_error('grps', grps, ['all', 'change', 
                                               'no_change', 'reduc', 'incr'])
            if add_reg and reg_ind not in grp_ind:
                    grp_ind.extend([reg_ind])
            grp_inds.append(sorted(grp_ind))

    all_roi_grps = [[roi_grps[i] for i in grp_ind] for grp_ind in grp_inds]
    all_grp_names = [[grp_names[i] for i in grp_ind] for grp_ind in grp_inds]
    if len(grps) == 1:
        all_roi_grps = all_roi_grps[0]
        all_grp_names = all_grp_names[0] 

    return all_roi_grps, all_grp_names


#############################################
def grp_stats(integ_stats, grps, plot_vals='both', op='diff', stats='mean', 
              error='std', scale=False):
    """
    grp_stats(integ_stats, grps)

    Calculate statistics (e.g. mean + sem) across quintiles for each group 
    and session.

    Required args:
        - integ_stats (list): list of 3D arrays of mean/medians of integrated
                              sequences, for each session structured as:
                                 surp if bysurp x
                                 quintiles x
                                 ROIs if byroi
        - grps (list)       : list of sublists per session, each containing
                              sublists per roi grp with ROI numbers included in 
                              the group: session x roi_grp
    Optional args:
        - plot_vals (str): which values to return ('surp', 'reg' or 'both')
                           default: 'both'
        - op (str)       : operation to use to compare groups, if plot_vals
                           is 'both'
                           i.e. 'diff': grp1-grp2, or 'ratio': grp1/grp2
                           default: 'diff'
        - stats (str)    : statistic parameter, i.e. 'mean' or 'median'
                           default: 'mean'
        - error (str)    : error statistic parameter, i.e. 'std' or 'sem'
                           default: 'std'
        - scale (bool)   : if True, data is scaled using first quintile
    Returns:
        - all_grp_st (4D array): array of group stats (mean/median, error) 
                                 structured as:
                                  session x quintile x grp x stat 
        - all_ns (2D array)    : array of group ns, structured as:
                                  session x grp
    """

    n_sesses = len(integ_stats)
    n_quints = integ_stats[0].shape[1]
    n_stats  = 2 + (stats == 'median' and error == 'std')
    n_grps   = len(grps[0])

    all_grp_st = np.empty([n_sesses, n_quints, n_grps, n_stats])
    all_ns = np.empty([n_sesses, n_grps], dtype=int)

    for i, [sess_data, sess_grps] in enumerate(zip(integ_stats, grps)):
        # calculate diff/ratio or retrieve reg/surp 
        if plot_vals in ['reg', 'surp']:
            op = ['reg', 'surp'].index(plot_vals)
        sess_data = math_util.calc_op(sess_data, op, dim=0)
        for g, grp in enumerate(sess_grps):
            all_ns[i, g] = len(grp)
            all_grp_st[i, :, g, :] = np.nan
            if len(grp) != 0:
                grp_data = sess_data[:, grp]
                if scale:
                    grp_data, _ = math_util.scale_data(grp_data, axis=0, pos=0, 
                                                       sc_type='unit')
                all_grp_st[i, :, g] = math_util.get_stats(grp_data, stats, 
                                                          error, axes=1).T

    return all_grp_st, all_ns


#############################################
def grp_traces_by_qu_surp_sess(trace_data, analyspar, roigrppar, all_roi_grps):

    """
    grp_traces_by_qu_surp_sess(trace_data, analyspar, roigrppar, all_roi_grps)
                               
    Required args:
        - trace_data (list)    : list of 4D array of mean/medians traces 
                                 for each session, structured as:
                                    surp x quintiles x ROIs x frames
        - analyspar (AnalysPar): named tuple containing analysis parameters
        - roigrppar (RoiGrpPar): named tuple containing roi grouping parameters
        - all_roi_grps (list)  : list of sublists per session, each containing
                                 sublists per roi grp with ROI numbers included 
                                 in the group: session x roi_grp

    Returns:
        - grp_stats (5D array): statistics for ROI groups structured as:
                                    sess x qu x ROI grp x stats x frame
    """

    # calculate diff/ratio or retrieve reg/surp 
    op = roigrppar.op
    if roigrppar.plot_vals in ['reg', 'surp']:
        op = ['reg', 'surp'].index(roigrppar.plot_vals)
    data_me = [math_util.calc_op(sess_me, op, dim=0) for sess_me in trace_data]
    
    n_sesses = len(data_me)
    n_quints = data_me[0].shape[0]
    n_frames = data_me[0].shape[2]

    n_grps   = len(all_roi_grps[0])
    n_stats  = 2 + (analyspar.stats == 'median' and analyspar.error == 'std')

    # sess x quintile (first/last) x ROI grp x stats
    grp_stats = np.full([n_sesses, n_quints, n_grps, n_stats, n_frames], 
                        np.nan)

    for i, sess in enumerate(data_me):
        for q, quint in enumerate(sess): 
            for g, grp_rois in enumerate(all_roi_grps[i]):
                # leave NaNs if no ROIs in group
                if len(grp_rois) == 0:
                    continue
                grp_st = math_util.get_stats(quint[grp_rois], analyspar.stats, 
                                             analyspar.error, axes=0)
                grp_stats[i, q, g] = grp_st

    return grp_stats


#############################################
def signif_rois_by_grp_sess(sessids, integ_data, permpar, roigrppar,  
                            qu_labs=['first quint', 'last quint'], 
                            stats='mean', nanpol=None):
    """
    signif_rois_by_grp_sess(sessids, integ_data, permpar, quintpar, roigrppar)

    Identifies ROIs showing significant surprise in specified quintiles,
    groups accordingly and retrieves statistics for each group.

    Required args:
        - sessids (list)       : list of Session IDs
        - integ_data (list)    : list of 2D array of ROI activity integrated 
                                 across frames. Should only include quintiles
                                 retained for analysis:
                                    sess x surp x quintiles x 
                                    array[ROI x sequences]
        - permpar (PermPar)    : named tuple containing permutation parameters
        - roigrppar (RoiGrpPar): named tuple containing roi grouping parameters

    Optional args:
        - qu_labs (list): quintiles being compared
                          default: ['first Q', 'last Q']
        - stats (str)   : statistic parameter, i.e. 'mean' or 'median'
                          default: 'mean'
        - nanpol (str)  : policy for NaNs, 'omit' or None when taking statistics
                          default: None

    Returns: 
        - all_roi_grps (list)   : list of sublists per session, containing ROI 
                                  numbers included in each group, structured as 
                                  follows:
                                      if sets of groups are passed: 
                                          session x set x roi_grp
                                      if one group is passed: 
                                          session x roi_grp
        - grp_names (list)      : list of names of the ROI groups in roi grp 
                                  lists (order preserved)
        - permpar_mult (PermPar): named tuple containing new p-values and 
                                  number of permutations for each session, 
                                  recalculated to compensate for multiple 
                                  comparisons
    """

    if len(qu_labs) != 2:
        raise ValueError(('Identifying significant ROIs is only implemented '
                          'for 2 quintiles.'))

    print(('\nIdentifying ROIs showing significant surprise in {} and/or '
           '{}.'.format(qu_labs[0].capitalize(), qu_labs[1].capitalize())))

    all_roi_grps = []

    pvals_mult = []
    nperms_mult = []

    for sessid, sess_data in zip(sessids, integ_data):
        print('\nSession {}'.format(sessid))
        
        sess_rois = []
        # adjust p-value to number of comparisons
        nrois   = sess_data[0][0].shape[0]
        n_comps = nrois * float(len(qu_labs)) # number of comp
        pval_mult, nperm_mult = math_util.calc_mult_comp(n_comps, permpar.p_val, 
                                                         permpar.n_perms)
        for q, q_lab in enumerate(qu_labs):
            print('    {}'.format(q_lab.capitalize()))
            n_reg = sess_data[0][q].shape[1]
            # calculate real values (average across seqs)
            data = [math_util.mean_med(sess_data[0][q], stats, axis=1, 
                                       nanpol=nanpol), 
                    math_util.mean_med(sess_data[1][q], stats, axis=1,
                                       nanpol=nanpol)]
            # ROI x seq
            qu_data_res = math_util.calc_op(np.asarray(data), roigrppar.op, 
                                            dim=0)
            # concatenate surp and reg from quintile
            qu_data_all = np.concatenate([sess_data[0][q], 
                                          sess_data[1][q]], axis=1)
            # run permutation to identify significant ROIs
            all_rand_res = math_util.permute_diff_ratio(qu_data_all, n_reg, 
                                                        nperm_mult, stats, 
                                                        nanpol, roigrppar.op)
            sign_rois = math_util.id_elem(all_rand_res, qu_data_res, 
                                          permpar.tails, pval_mult, 
                                          print_elems=True)
            sess_rois.append(sign_rois)

        pvals_mult.append(pval_mult)
        nperms_mult.append(nperm_mult)
            
        grps = gen_util.list_if_not(roigrppar.grps)

        if len(grps) == 1:
            roi_grps, grp_names = sep_grps(sess_rois, nrois=nrois, 
                                      grps=roigrppar.grps, tails=permpar.tails,
                                      add_reg=roigrppar.add_reg)
        else:
            roi_grps = []
            for grp_set in roigrppar.grps:
                roi_grps_set, _ = sep_grps(sess_rois, nrois=nrois, grps=grp_set, 
                                           tails=permpar.tails, add_reg=False)
                
                # flat, without duplicates
                flat_grp = sorted(list(set([roi for grp in roi_grps_set 
                                                for roi in grp])))
                roi_grps.append(flat_grp)
                
            grp_names = roigrppar.grps
        
        all_roi_grps.append(roi_grps)
        permpar_mult = sess_ntuple_util.init_permpar(nperms_mult, pvals_mult, 
                                                     permpar.tails)

    return all_roi_grps, grp_names, permpar_mult

