'''
str_util.py

This module contains basic math functions for getting strings to print or save
files for AIBS experiments for the Credit Assignment Project.

Authors: Colleen Gillon

Date: October, 2018

Note: this code uses python 2.7.

'''
import datetime

import gen_util


#############################################
def shuff_par_str(shuffle=True, type_str='print'):
    """
    shuff_par_str()

    Creates a string from shuffle parameter to print or for a filename.

    Optional arguments:
        - shuffle (bool): default: True
        - type (str)    : 'print' for a printable string and 'file' for a
                           string usable in a filename.
                           default: 'print'
    
    Returns:
        - shuff_str (str): shuffle parameter string
    """

    if shuffle:
        if type_str == 'print':
            shuff_str = ', shuffled'
        elif type_str == 'file':
            shuff_str = '_shuffled'
        elif type_str == 'labels':
            shuff_str = ' (shuffled labels)'
        else:
            gen_util.accepted_values_error('type_str', type_str, ['print', 'file'])
    else:
        shuff_str = ''

    return shuff_str
    
    
#############################################
def norm_par_str(norm=True, type_str='print'):
    """
    norm_par_str()

    Creates a string from norm parameter to print or for a filename.

    Optional arguments:
        - norm (bool or str): default: True
        - type (str)        : 'print' for a printable string and 'file' for a
                              string usable in a filename.
                              default: 'print'
    
    Returns:
        - norm_str (str): norm parameter string
    """
    
    if norm != 'none' and norm:
        if type_str == 'print':
            norm_str = ', norm'
        elif type_str == 'file':
            norm_str = '_norm'
        else:
            gen_util.accepted_values_error('type_str', type_str, ['print', 'file'])
    else:
        norm_str = ''

    return norm_str
    

#############################################
def fluor_par_str(fluor='dff', type_str='print', dff=None):
    """
    fluor_par_str()

    Creates a string from the fluorescence parameter to print or for a 
    filename.

    Optional arguments:
        - fluor (str): whether 'raw' or processed fluorescence traces 'dff' are 
                       used  
                       default: 'dff'
        - type (str) : 'print' for a printable string and 'file' for a
                       string usable in a filename.
                       default: 'print'
        - dff (bool) : can be used instead of fluor, and if so
                       (not None), will supercede fluor. 
                       if True, fluor is set to 'dff', if False, 
                       fluor is set to 'raw'. If None, no effect.
                       default: None  
    
    Returns:
        - fluor_str (str): fluorescence parameter string
    """

    if dff is not None:
        if dff:
            fluor = 'dff'
        else:
            fluor = 'raw'

    if fluor == 'raw':
        if type_str == 'print':
            fluor_str = 'raw fluorescence intensity'
        elif type_str == 'file':
            fluor_str = 'raw'
        else:
            gen_util.accepted_values_error('type_str', type_str, ['print', 'file'])
    elif fluor == 'dff':
        if type_str == 'print':
            delta = u'\u0394'
            fluor_str = u'{}F/F'.format(delta)
        elif type_str == 'file':
            fluor_str = 'dff'
        else:
            gen_util.accepted_values_error('type_str', type_str, ['print', 'file'])
    else:
        gen_util.accepted_values_error('fluor', fluor, ['raw', 'dff'])

    return fluor_str
    

#############################################
def stat_par_str(stats='mean', error='std', str_type='print'):
    """
    stat_par_str()

    Creates a string from statistical analysis parameters to print or for a 
    title.

    Optional arguments:
        - stats (str)   : 'mean' or 'median'
                          default: 'mean'
        - error (str)   : 'std' (for std or quartiles) or 'sem' (for SEM or MAD)
                          default: 'std'
        - str_type (str): use of output str, i.e., for a filename ('file') or
                          to print the info to console or for title ('print')
                          default = 'print'
    
    Returns:
        - stat_str (str): statistics combo string
    """
    if str_type == 'print':
        sep = u'\u00B1' # +- symbol
    elif str_type == 'file':
        sep = '_'
    else:
        gen_util.accepted_values_error('str_type', str_type, ['print', 'file'])

    if stats == 'mean':
        stat_str = u'{}{}{}'.format(stats, sep, error)
    elif stats == 'median':
        if error == 'std':
            stat_str = u'{}{}qu'.format(stats, sep)
        elif error == 'sem':
            stat_str = u'{}{}mad'.format(stats, sep)
        else:
            gen_util.accepted_values_error('error', error, ['std', 'sem'])
    else:
        gen_util.accepted_values_error('stats', stats, ['mean', 'median'])
    return stat_str


#############################################
def op_par_str(plot_vals='diff', op='diff', area=False, str_type='file'):
    """
    op_par_str()

    Creates a string from operation parameter (e.g., surprise, non surprise 
    or the difference/ratio between the two) to print or for a title.

    Optional arguments:
        - plot_vals (str): 'surp', 'nosurp' or 'diff'
                           default: 'diff'
        - op (str)       : 'diff' or 'ratio'
                           default: 'diff'
        - str_type (str) : use of output str, i.e., for a filename ('file') or
                           to print the info to console ('print')
                           default = 'file'
    
    Returns:
        - area (bool) : if True, print string indicates that 'area' is plotted,
                        not trace
                        default: False 
        - op_str (str): operation type string
    """
    if area:
        area_str = ' area'
    else:
        area_str = ''
    if plot_vals == 'diff':
        if str_type == 'print':
            op_str = '{} in dF/F{} for surp v nosurp'.format(area_str, op)
        elif str_type == 'file':
            op_str = plot_vals
    elif plot_vals in ['surp', 'nosurp']:
        if str_type == 'print':
            op_str = 'dF/F{} for {}'.format(area_str, plot_vals)
        elif str_type == 'file':
            op_str = plot_vals
    else:
        gen_util.accepted_values_error('plot_vals', plot_vals, ['diff', 'surp', 'nosurp'])
    return op_str


#############################################
def create_time_str():
    """
    create_time_str()

    Creates a string in a format appropriate for a directory or filename
    containing date and time information based on time at which the function is
    called.

    Return:
        dir_name (str): string containing date and time formatted as 
                        YYMMDD_HHMMSS
    """

    now = datetime.datetime.now()
    dir_name = ('{:02d}{:02d}{:02d}_'
                '{:02d}{:02d}{:02d}').format(now.year, now.month, now.day, 
                                             now.hour, now.minute, now.second)
    return dir_name


#############################################
def gab_k_par_str(gab_k):
    """
    gab_k_par_str(gab_k)

    Creates a string from gabor kappa parameter (e.g., 4 or 16). Returns
    an empty string if both gabor kappa parameters are passed.

    Required arguments:
        - gab_k (int or list): gabor kappa parameter

    Return:
        (list): string containing gabor kappa parameter value or empty string
                if both parameters are passed.
    """

    gab_k = gen_util.list_if_not(gab_k)
    if len(gab_k) > 1:
        return ''
    else:
        return str(gab_k[0])


#############################################
def size_par_str(size):
    """
    size_par_str(size)

    Creates a string from brick size parameter (e.g., 128 or 256). 
    Returns an empty string if both brick size parameters are passed.

    Required arguments:
        - size (int or list): brick size parameter

    Return:
        (list): string containing brick size parameter value or empty string
                if both parameters are passed.
    """

    size = gen_util.list_if_not(size)
    if len(size) > 1:
        return ''
    else:
        return str(size[0])


#############################################
def dir_par_str(dir):
    """
    dir_par_str(dir)

    Creates a string from brick direction parameter (e.g., 'right' or 'left'). 
    Returns an empty string if both brick direction parameters are passed.

    Required arguments:
        - dir (str or list): brick direction parameter

    Return:
        (list): string containing brick direction parameter value or empty string
                if both parameters are passed.
    """

    dir = gen_util.list_if_not(dir)
    if len(dir) > 1:
        return ''
    else:
        return str(dir[0])


#############################################
def stim_par_str(gab_k=None, bri_dir=None, bri_size=None, stim_type='gabors', 
                 str_type='print'):
    """
    stim_par_str(par)

    Creates a string from gabor kappa or brick size and direction parameters. 
    Returns an empty string if both possible parameters values are passed.

    Optional arguments:
        - gab_k (int or list)   : gabor kappa parameter
                                  default = None
        - bri_dir (str or list) : brick direction parameter
                                  default = None
        - bri_size (int or list): brick size parameter
                                  default = None
        - stim_type (str)       : type of stimulus
                                  default = 'gabors'
        - str_type (str)        : use of output str, i.e., for a filename 
                                  ('file') or to print the info to console 
                                  ('print')
                                  default = 'print'

    Return:
        - pars (str): string containing parameter value or empty string
                      if both parameters are passed.
    """
    if gab_k is None and (bri_size is None or bri_dir is None):
        raise IOError('Must pass value for gabor k parameter or brick size and direction.')

    if stim_type == 'gabors':
        pars = gab_k_par_str(gab_k)
    elif stim_type == 'bricks':
        size_par = size_par_str(bri_size)
        dir_par = dir_par_str(bri_dir)
        if str_type == 'print':
            if len(dir_par) != 0:
                if len(size_par) != 0:
                    sep = ', '
                elif len(size_par) == 0:
                    sep = ' '
            else:
                sep = ''
        elif str_type == 'file':
            if len(dir_par) != 0:
                sep = '_'
            else:
                sep = ''
        else:
            gen_util.accepted_values_error('str_type', str_type, ['print', 'file'])
        
        pars = '{}{}{}'.format(size_par, sep, dir_par)    
    else:
        gen_util.accepted_values_error('stim_type', stim_type, ['gabors', 'bricks'])

    return pars


#############################################
def sess_par_str(sess_par, gab_k=None, bri_dir=None, bri_size=None, 
                 stim_type='gabors', str_type='print'):
    """
    sess_par_str(sess_par, stim_par)

    Creates a string from session and stimulus parameters for a filename, 
    or to print or use in a title.

    Required arguments:
        - sess_par (dict)       : dictionary containing session parameters: 
                                e.g. 'layer', 'overall_sess_n'
                ['layer'] (str)         : layer ('soma', 'dend', 'L23_soma',  
                                                'L5_soma', 'L23_dend', 'L5_dend', 
                                                'L23_all', 'L5_all')
                ['overall_sess_n'] (int): overall session number aimed for

    Optional arguments:
        - gab_k (int or list)   : gabor kappa parameter
                                  default = None
        - bri_dir (str or list) : brick direction parameter
                                  default = None
        - bri_size (int or list): brick size parameter
                                  default = None
        - stim_type (str)       : type of stimulus
                                  default = 'gabors'
        - str_type (str)        : use of output str, i.e., for a filename 
                                  ('file') or to print the info to console 
                                  ('print')
                                  default = 'print'
    Return:
        - sess_str (list): string containing info on session and gabor kappa 
                           parameters
    """
    if gab_k is None and (bri_size is None or bri_dir is None):
        raise IOError('Must pass value for gabor k parameter or brick size and direction.')
    elif gab_k is None:
        stim_type = 'bricks'
    elif bri_size is None:
        stim_type = 'gabors'
    
    stim_str = stim_par_str(gab_k, bri_dir, bri_size, stim_type, str_type)

    if str_type == 'file':
        sess_str = 'sess{}_{}{}_{}'.format(sess_par['overall_sess_n'], stim_type[0:3],
                                           stim_str, sess_par['layer'])
    elif str_type == 'print':
        if len(stim_str) == 0:
            sess_str = '{}, '.format(stim_type)
        else:
            if stim_str[0] == ' ':
                stim_str = stim_str[1:]
            sess_str = '{}: {}, '.format(stim_type, stim_str)
        sess_str += 'session: {}, layer: {}'.format(sess_par['overall_sess_n'], 
                                                     sess_par['layer'])
    else:
        gen_util.accepted_values_error('str_type', str_type, ['file', 'print'])
    
    return sess_str
    
