"""
sess_plot_util.py

This module contains basic functions for plotting with pyplot data generated by 
the AIBS experiments for the Credit Assignment Project.

Authors: Colleen Gillon

Date: October, 2018

Note: this code uses python 3.7.

"""

import copy
import os

import itertools
from matplotlib import colors as mplcol
from matplotlib import pyplot as plt
import numpy as np

from util import gen_util, plot_util
from sess_util import sess_str_util


#############################################
def init_figpar(ncols=4, sharex=False, sharey=True, subplot_hei=7, 
                subplot_wid=7, datetime=True, use_dt=None, fig_ext='svg', 
                overwrite=False, runtype='prod', output='', plt_bkend=None, 
                linclab=True, fontdir=None):
    
    """
    Returns a dictionary containing figure parameter dictionaries for 
    initializing a figure, saving a figure, and extra save directory 
    parameters.

    Optional args: 
        - ncols (int)      : number of columns in the figure
                             default: 4 
        - sharex (bool)    : if True, x axis lims are shared across subplots
                             default: False 
        - sharey (bool)    : if True, y axis lims are shared across subplots
                             default: True
        - subplot_hei (num): height of each subplot (inches)
                             default: 7
        - subplot_wid (num): width of each subplot (inches)
                             default: 7
        - datetime (bool)  : if True, figures are saved in a subfolder named 
                             based on the date and time.
        - use_dt (str)     : datetime folder to use
                             default: None
        - fig_ext (str)    : figure extension
                             default: 'svg'
        - overwrite (bool) : if False, overwriting existing figures is 
                             prevented by adding suffix numbers.
                             default: False
        - runtype (str)    : runtype ('pilot', 'prod')
                             default: 'prod'
        - output (str)     : general directory in which to save output
                             default: ''
        - plt_bkend (str)  : mpl backend to use for plotting (e.g., 'agg')
                             default: None
        - linclab (bool)   : linclab style setting 
                             default: None
        - fontdir (str)    : path to directory where additional fonts are stored
                             default: None

    Returns:
        - figpar (dict): dictionary containing figure parameters:
            ['init'] : dictionary containing the following inputs as
                       attributes:
                           ncols, sharex, sharey, subplot_hei, subplot_wid
            ['save'] : dictionary containing the following inputs as
                       attributes:
                           datetime, use_dt, fig_ext, overwrite
            ['dirs']: dictionary containing the following attributes:
                ['figdir'] (str)   : main folder in which to save figures
                ['roi'] (str)      : subdirectory name for ROI analyses
                ['run'] (str)      : subdirectory name for running analyses
                ['acr_sess'] (str) : subdirectory name for analyses across 
                                     sessions
                ['autocorr'] (str) : subdirectory name for autocorrelation 
                                     analyses
                ['full'] (str)     : subdirectory name for full trace plots
                ['glm'] (str)      : subdirectory name for glm plots
                ['grped'] (str)    : subdirectory name for ROI grps data
                ['lat'] (str)      : subdirectory name for latency analyses
                ['locori'] (str)   : subdirectory name for location and 
                                     orientation responses
                ['mags'] (str)     : subdirectory name for magnitude analyses
                ['posori'] (str)   : subdirectory name for position and 
                                     orientation plots
                ['prop'] (str)     : subdirectory name for proportion 
                                     responsive ROI analyses
                ['pupil'] (str)    : subdirectory for pupil analyses
                ['oridir'] (str)   : subdirectory name for 
                                     orientation/direction analyses
                ['surp_qu'] (str)  : subdirectory name for surprise, quintile 
                                     analyses
                ['tune_curv'] (str): subdirectory name for tuning curves
                
            ['mng']: dictionary containing the following attributes:
                ['plt_bkend'] (str): mpl backend to use
                ['linclab'] (bool) : if True, Linclab mpl defaults are used
                ['fontdir'] (str)  : path to directory containing additional 
                                     fonts
    """

    fig_init = {'ncols'      : ncols,
                'sharex'     : sharex,
                'sharey'     : sharey, 
                'subplot_hei': subplot_hei,
                'subplot_wid': subplot_wid
                }

    fig_save = {'datetime' : datetime,
                'use_dt'   : use_dt,
                'fig_ext'  : fig_ext,
                'overwrite': overwrite
                }
    
    fig_mng = {'linclab'  : linclab,
               'plt_bkend': plt_bkend,
               'fontdir'  : fontdir,
                }

    figdir = os.path.join(output, 'results', 'figures')

    fig_dirs = {'figdir'   : figdir,
                'roi'      : os.path.join(figdir, f'{runtype}_roi'),
                'run'      : os.path.join(figdir, f'{runtype}_run'),
                'acr_sess' : 'acr_sess',
                'autocorr' : 'autocorr',
                'full'     : 'full',
                'glm'      : 'glm',
                'grped'    : 'grped',
                'lat'      : 'latencies',
                'mags'     : 'mags',
                'posori'   : 'posori',
                'prop'     : 'prop_resp',
                'pupil'    : 'pupil',
                'oridir'   : 'oridir',
                'surp_qu'  : 'surp_qu',
                'tune_curv': 'tune_curves',
               }

    figpar = {'init' : fig_init,
              'save' : fig_save,
              'dirs' : fig_dirs,
              'mng'  : fig_mng
              }
    
    return figpar


#############################################
def fig_init_linpla(figpar=None, traces=False):
    """
    fig_init_linpla()

    Returns figpar dictionary with initialization parameters modified for
    graphs across sessions divided by line/plane combinations.

    Optional args:
        - figpar (dict)       : dictionary containing figure parameters 
                                (initialized if None):
            ['init'] : dictionary containing the following inputs as
                       attributes:
                           ncols, sharex, sharey, subplot_hei, subplot_wid
                                default: None
        - traces (bool or int): if not False, provides number of traces per 
                                line/plane combination to use in dividing 
                                subplot height
                                default: False

    Returns:
        - figpar (dict): dictionary containing figure parameters:
            ['init'] : dictionary containing the following inputs modified:
                           ncols, sharex, sharey, subplot_hei, subplot_wid
    """

    figpar = copy.deepcopy(figpar)

    if figpar is None:
        figpar = init_figpar()

    if 'init' not in figpar.keys():
        raise ValueError('figpar should have `init` subdictionary.')

    if traces:
        wid = 4.5
        hei = np.max([wid/traces, 1.0])
    else:
        wid = 3.2
        hei = wid * 1.8
        figpar['init']['gs'] = {'hspace': 0.2, 'wspace': 0.4}


    figpar['init']['ncols'] = 2
    figpar['init']['subplot_hei'] = hei
    figpar['init']['subplot_wid'] = wid
    figpar['init']['sharex'] = True
    figpar['init']['sharey'] = True

    return figpar


#############################################
def fig_linpla_pars(traces=False, n_grps=None):
    """
    fig_linpla_pars()

    Returns parameters for a line/plane combination graph.

    Optional args:
        - traces (bool or int): if not False, provides number of traces per 
                                line/plane combination to use in multiplying
                                number of plots
                                default: False
        - n_grps (int or None): if not None, the number of groups in the data 
                                is verified against the expected number of 
                                groups
                                default: None

    Returns:
        - lines (list)      : ordered list of lines
        - planes (list)     : ordered list of planes
        - linpla_iter (list): ordered list of lines and planes, structured as 
                              grp x [lin, pla]
        - pla_cols (list)   : colors for each plane
        - pla_cols (list)   : color names for each plane
        - n_plots (int)     : total number of plots
    """

    lines, planes = ['L2/3', 'L5'], ['dendrites', 'soma']
    linpla_iter = [[lin, pla] for lin in lines for pla in planes]
    pla_col_names = ['green', 'blue']
    pla_cols = [plot_util.get_color(c, ret='single') for c in pla_col_names]
    
    if traces:
        mult = traces
    else:
        mult = 1
    n_plots = len(lines) * len(planes) * mult

    if n_grps is not None and n_grps > n_plots/mult:
        raise ValueError(f'Expected up to {n_plots} line x plane '
                         f'combinations, not {n_grps}.')

    return lines, planes, linpla_iter, pla_cols, pla_col_names, n_plots


#############################################
def get_quint_cols(n_quints=4):
    """
    get_quint_cols()

    Returns regular and surprise colors for quintiles, as well as label colors
    for regular and surprise.

    Required args:
        - n_quints (int): number of quintiles

    Returns:
        - cols (list)    : nested list of colors, 
                           structured as [regular, surprise]
        - lab_cols (list): label colors for regular and surprise data
    """

    col_reg  = plot_util.get_color_range(n_quints, 'blue')
    col_surp = plot_util.get_color_range(n_quints, 'red')

    lab_reg = plot_util.get_color_range(1, 'blue')[0]
    lab_surp = plot_util.get_color_range(1, 'red')[0]

    cols = [col_reg, col_surp]
    lab_cols = [lab_reg, lab_surp]

    return cols, lab_cols


#############################################
def add_axislabels(sub_ax, fluor='dff', area=False, scale=False, datatype='roi', 
                   x_ax=None, y_ax=None, first_col=True, last_row=True):
    """
    add_axislabels(sub_ax)

    Adds the appropriate labels to the subplot x and y axes. 
    
    If y_ax is None, y axis is assumed to be fluorescence, and label is 
    inferred from fluor and dff parameters. If x_ax is None, x axis is assumed
    to be time in seconds.

    Required args:
        - sub_ax (plt Axis subplot): subplot

    Optional args:
        - fluor (str)     : if y_ax is None, whether 'raw' or processed 
                            fluorescence traces 'dff' are plotted. 
                            default: 'dff'
        - area (bool)     : if True, 'area' is added after the y_ax label
                            default: False
        - scale (bool)    : if True, '(scaled)' is added after the y_ax label
                            default: False
        - datatype (str)  : type of data, either 'run' or 'roi'
                            default: 'roi'
        - x_ax (str)      : label to use for x axis.
                            default: None
        - y_ax (str)      : label to use for y axis.
                            default: None
        - first_col (bool): if True, only add an y axis label to subplots in 
                            first column
                            default: True
        - last_row (bool) : if True, only add an x axis label to subplots in 
                            last row
                            default: True
    """

    area_str = ''
    if area:
        area_str = ' area'

    scale_str = ''
    if scale:
        scale_str = ' (scaled)'

    if x_ax is None:
        x_str = 'Time (s)'
    else:
        x_str = x_ax

    if not(last_row) or sub_ax.is_last_row():
        sub_ax.set_xlabel(x_str)

    if y_ax is None:
        if datatype == 'roi':
            y_str = sess_str_util.fluor_par_str(fluor, str_type='print')
        elif datatype == 'run':
            y_str = 'Running velocity (cm/s)'
        else:
            gen_util.accepted_values_error('datatype', datatype, ['roi', 'run'])
    else:
        y_str = y_ax
    
    if not(first_col) or sub_ax.is_first_col():
        sub_ax.set_ylabel(u'{}{}{}'.format(y_str, area_str, scale_str))


#############################################
def get_fr_lab(plot_vals='both', op='diff', start_fr=-1):
    """
    get_fr_lab()

    Returns a list of labels for gabor frames based on values that are plotted,
    and operation on surprise v no surprise, starting with gray.

    Optional args:
        - plot_vals (str): values plotted ('surp', 'reg', 'both')
                           default: 'both'
        - op (str)       : operation on the values, if both ('ratio' or 'diff')
                           default: 'diff'
        - start_fr (int) : starting gabor frame 
                           (-1: gray, 0: A, 1: B, 2:C, 3:D/E)
                           default: -1
    
    Returns:
        - labels (list)  : list of labels for gabor frames
    """

    labels = ['gray', 'A', 'B', 'C']

    if plot_vals == 'surp':
        labels.extend(['E'])
    elif plot_vals == 'reg':
        labels.extend(['D'])
    elif plot_vals == 'both':
        if op == 'diff':
            labels.extend(['E-D'])      
        elif op == 'ratio':
            labels.extend(['E/D'])
        else:
            gen_util.accepted_values_error('op', op, ['diff', 'ratio'])
    else:
        gen_util.accepted_values_error('plot_vals', plot_vals, 
                                       ['both', 'reg', 'surp'])

    if start_fr != -1:
        labels = list(np.roll(labels, -(start_fr+1)))

    return labels


#############################################
def get_seg_comp(gabfr=0, plot_vals='both', op='diff', pre=0, post=1.5):
    """
    get_seg_comp()

    Returns lists with different components needed when plotting segments, 
    namely positions of labels, ordered labels, positions of heavy bars and 
    position of regular bars.

    Optional args:
        - gabfr (int)    : gabor frame of reference
                           default: 0
        - plot_vals (str): values plotted ('surp', 'reg', 'both')
                           default: 'both'
        - op (str)       : operation on the values, if both ('ratio' or 'diff')
                           default: 'diff'
        - pre (num)      : range of frames to include before reference frame 
                           (in s)
                           default: 0 (only value implemented)
        - post (num)     : range of frames to include after reference frame
                           (in s)
                           default: 1.5 (only value implemented)
    
    Returns:
        - xpos (list)          : list of x coordinates at which to add labels
                                 (same length as labels)
        - labels (list)         : ordered list of labels for gabor frames
        - hbars (list or float): list of x coordinates at which to add 
                                 heavy dashed vertical bars
        - bars (list or float) : list of x coordinates at which to add 
                                 dashed vertical bars
    """

    if gabfr not in list(range(0, 4)):
        raise ValueError('Gabor frame must be 0, 1, 2 or 3.')

    seg_len = 0.3

    pre_segs = int(np.floor(pre/seg_len)) # number of segs pre
    n_segs = int(np.floor((pre + post)/seg_len)) # number of segs
    xpos = [(x + 0.5 - pre_segs) * seg_len for x in range(n_segs)]
    bars = [(x - pre_segs) * seg_len for x in range(n_segs)]
    
    labels = get_fr_lab(plot_vals, op, gabfr - pre_segs)
    if len(labels) < len(xpos):
        labels = labels * (len(xpos)//len(labels) + 1)
    if len(labels) > len(xpos):
        labels = labels[:len(xpos)]

    hbars = [bars[x] for x in range(1, len(bars)) if labels[x-1] == 'C']
    bars = gen_util.remove_if(bars, [-pre] + hbars)
    hbars = gen_util.remove_if(hbars, -pre)

    return xpos, labels, hbars, bars


#############################################
def plot_labels(ax, gabfr=0, plot_vals='both', op='none', pre=0, post=1.5, 
                cols=None, sharey=True, t_heis=[0.85, 0.75], incr=True, 
                omit_empty=True):
    """
    plot_labels(ax)

    Plots lines and labels for gabors segments.
   
    Required args:
        - ax (plt Axis): axis

    Optional args:
        - gabfr (int)      : gabor frame of reference
                             default: 0
        - plot_vals (str)  : values plotted ('surp', 'reg', 'comb', 'both')
                             default: 'both'
        - op (str)         : operation on the values, if both ('ratio' or 'diff')
                             default: 'none'
        - pre (num)        : range of frames to include before reference frame 
                             (in s)
                             default: 0 (only value implemented)
        - post (num)       : range of frames to include after reference frame
                             (in s)
                             default: 1.5 (only value implemented)
        - cols (str)       : colors to use for labels
                             default: None
        - sharey (bool)    : if True, y axes are shared
                             default: True
        - t_heis (list)    : height(s) at which to place labels. If t_hei 
                             includes negative values, the ylims are not 
                             modified.
                             default: [0.85, 0.75]
        - incr (bool)      : if True, y axis limits are increased to accomodate
                             labels
                             default: True
        - omit_empty (bool): if True, no labels are added to subplots with no 
                             lines plotted
                             default: True 
    """

    t_heis = gen_util.list_if_not(t_heis)
    if cols is None:
        cols = ['k', 'k']

    min_t_hei = min(t_heis)
    if min_t_hei > 0:
        plot_util.incr_ymax(ax, incr=1.05/min_t_hei, sharey=sharey)

    if plot_vals == 'both':
        if op == 'none':
            plot_vals = ['reg', 'surp']

    plot_vals = gen_util.list_if_not(plot_vals)

    n_ax = np.product(ax.shape)
    for i in range(n_ax):
        sub_ax = plot_util.get_subax(ax, i)
        if omit_empty and len(sub_ax.lines) == 0:
            continue
        for i, pv in enumerate(plot_vals):
            [xpos, lab, h_bars, seg_bars] = get_seg_comp(
                gabfr, pv, op, pre, post)
            plot_util.add_labels(sub_ax, lab, xpos, t_heis[i], cols[i])
        plot_util.add_bars(sub_ax, hbars=h_bars, bars=seg_bars)


#############################################
def plot_gabfr_pattern(sub_ax, x_ran, alpha=0.1, offset=0, bars_omit=[]):
    """
    plot_gabfr_pattern(sub_ax, x_ran)

    Plots light dashed lines at the edges of each gabor sequence (end of 
    grayscreen) and shades D/E segments.

    Required args:
        - sub_ax (plt Axis subplot): subplot
        - x_ran (array-like)       : range of x axis values

    Optional args:
        - alpha (num)     : plt alpha variable controlling shading 
                            transparency (from 0 to 1)
                            default: 0.1
        - offset (num)    : offset of sequence start from 0 in segs 
                            (start gabor frame number)
                            default: 0
        - bars_omit (list): positions at which to omit bars (e.g., in case they 
                            would be redundant)
                            default: []
    """

    offset_s = np.round(0.3 * offset, 10) # avoid periodic values

    bars = plot_util.get_repeated_bars(np.min(x_ran), np.max(x_ran), 1.5, 
        offset=-offset_s) # sequence start/end
    shade_st = plot_util.get_repeated_bars(np.min(x_ran), np.max(x_ran), 1.5, 
        offset=-offset_s - 0.6) # surprise start
    bars = gen_util.remove_if(bars, bars_omit)
    plot_util.add_bars(sub_ax, bars=bars)
    plot_util.add_vshade(sub_ax, shade_st, width=0.3, alpha=0.1)


#############################################
def format_linpla_subaxes(ax, fluor='dff', area=False, datatype='roi', 
                          lines=None, planes=None, xlab=None, 
                          xticks=None, sess_ns=None, y_ax=None):
    """
    format_linpla_subaxes(ax)

    Formats axis labels and grids for a square of subplots, structured as 
    planes (2 or more rows) x lines (2 columns). 
    
    Specifically:
    - Removes bottom lines and ticks for top plots
    - Adds line names to top plots
    - Adds y labels on left plots (midde of top and bottom half)
    - Adds plane information on right plots (midde of top and bottom half)
    - Adds x labels to bottom plots
    - Adds session numbers if provided

    Required args:
        - ax (plt Axis): plt axis

    Optional args:
        - fluor (str)   : if y_ax is None, whether 'raw' or processed 
                            fluorescence traces 'dff' are plotted. 
                            default: 'dff'
        - area (bool)   : if True, 'area' is added after the y_ax label
                            default: False
        - datatype (str): type of data, either 'run' or 'roi'
                            default: 'roi'
        - lines (list)  : ordered lines (2)
                            default: None
        - planes (list) : ordered planes (2)
                            default: None
        - xlab (str)    : x label
                          default: None
        - xticks (list) : x tick labels (if None, none are added)
                          default: None
        - sess_ns (list): list of session numbers (inferred if None)
                          default: None 
        - y_ax (str)    : y axis label (overrides automatic one)
                          default: None
    """

    if ax.shape[1] != 2:
        raise ValueError('Expected 2 columns.')
    
    n_rows = ax.shape[0]
    if n_rows%2 != 0:
        raise ValueError('Expected even number of rows')
    rs_mid = [n_rows//4, n_rows - n_rows//4 - 1]

    if sess_ns is not None: # extra rows are seconds
        xlab = 'Time (s)'

    if lines is None:
        lines = ['L2/3', 'L5']
    if planes is None:
        planes = ['dendrites', 'soma']
    
    for l, name in zip([lines, planes], ['lines', 'planes']):
        if len(l) != 2:
            raise ValueError(f'2 {name} expected.')


    for r in range(ax.shape[0]):
        for c in range(ax.shape[1]):
            if xticks is not None:
                ax[r, c].set_xticks(xticks)
            if c == 0 and r in rs_mid: # LEFT MID plane
                add_axislabels(ax[r, c], fluor=fluor, area=area, 
                                datatype=datatype, x_ax='', y_ax=y_ax)
            if c != 0: # RIGHT
                right_lab = ''
                if sess_ns is not None:
                    sess_n = sess_ns[r%len(sess_ns)]
                    right_lab = f'{sess_n}\n'
                    if sess_n == sess_ns[-1]:
                        right_lab = f'sess {right_lab}'
                if r in rs_mid: # RIGHT MID plane
                    r_idx = rs_mid.index(r)
                    right_lab = f'{right_lab}{planes[r_idx]}\n'
                ax[r, c].set_ylabel(right_lab[:-1])
                ax[r, c].yaxis.set_label_position('right')
            if r == 0: # TOP
                ax[r, c].set_title(f'{lines[c]} neurons')            
            if r != n_rows-1: # NOT BOTTOM
                ax[r, c].tick_params(axis='x', which='both', bottom=False) 
                ax[r, c].spines['bottom'].set_visible(False)
            elif xlab is not None: # BOTTOM
                ax[r, c].set_xlabel(xlab)
                

#############################################
def plot_ROIs(sub_ax, masks, valid_mask=None, border=None, savename=None):
    """
    plot_ROIs(sub_ax, masks)

    Plots whole ROIs contours from a boolean mask, and optionally non valid
    ROIs in red.

    Required args:
        - sub_ax (plt Axis subplot): subplot
        - masks (3D array)         : boolean ROI masks, structured as
                                     ROIs x hei x wid
    
    Optional args:
        - valid_mask (int): mask of valid ROIs (length of mask_bool). If None,
                            all ROIs plotted in white.
                            default: None
        - border (list)   : border values to plot in red [right, left, down, up]
                            default: None
        - savename (bool) : if provided, saves mask contours to file 
                            (exact pixel size). '.png' best to avoid 
                            anti-aliasing.
                            default: False

    Returns:
        - masks_plot_proj (2D array): ROI image array: hei x wid
    """

    if len(masks.shape) == 2:
        masks = np.expand_dims(masks, 0)
    if valid_mask is None:
        valid_mask = np.ones(len(masks))

    color_list = ['black', 'white', 'red']
    if valid_mask.all() and border is None:
        color_list = ['black', 'white']
    cm = mplcol.LinearSegmentedColormap.from_list(
        'roi_mask_cm', color_list, N=len(color_list))
    
    masks = masks.astype(bool).astype(int)
    masks[~valid_mask.astype(bool)] *= 2
    masks_plot_proj = np.max(masks, axis=0)
    
    if border is not None:
        hei, wid = masks_plot_proj.shape
        right, left, down, up = [
            np.ceil(border[i]).astype(int) for i in [0, 1, 2, 3]]

        # create dash patterns
        dash_len = 3
        hei_dash, wid_dash = [np.concatenate([np.arange(i, v, 
            dash_len * 2) for i in range(dash_len)]) for v in [hei, wid]]

        masks_plot_proj[hei_dash, right] = 2
        masks_plot_proj[hei_dash, wid-left] = 2
        masks_plot_proj[hei-down, wid_dash] = 2
        masks_plot_proj[up, wid_dash] = 2

    sub_ax.imshow(masks_plot_proj, cmap=cm, interpolation='none')

    if savename:
        plt.imsave(savename, masks_plot_proj, cmap=cm)

    return masks_plot_proj


#############################################
def plot_ROI_contours(sub_ax, masks, outlier=None, tight=False, 
                      restrict=False, cw=1, savename=False):
    """
    plot_ROI_contours(sub_ax, mask_bool)

    Plots and returns ROI contours from a boolean mask, and optionally an 
    outlier in red. Optionally saves ROI contours to file.

    Required args:
        - sub_ax (plt Axis subplot): subplot
        - masks (3D array)         : boolean ROI masks, structured as
                                     ROIs x hei x wid
    Optional args:
        - outlier (int)  : index of ROI, if any, for which to plot contour 
                           in a red.
                           default: None
        - tight (bool)   : if True, plot is restricted to the ROIs in the mask,
                           allowing for a 15% border, where possible
                           default: False
        - restrict (bool): if True, plot is restricted to the outlier ROI,
                           allowing for a 150% border, where possible. Overrides
                           right.
                           default: True
        - cw (int)       : contour width (in pixels) (always within the ROI)
                           default: 1
        - savename (bool): if provided, saves mask contours to file 
                           (exact pixel size). '.png' best to avoid 
                           anti-aliasing.
                           default: False

    Returns:
        - contour_mask (2D array): ROI contour image array: hei x wid
    """

    color_list = ['black', 'white', 'red']
    if outlier is None:
        color_list = ['black', 'white']
    cm = mplcol.LinearSegmentedColormap.from_list(
        'roi_mask_cm', color_list, N=len(color_list))

    if len(masks.shape) == 2:
        masks = np.expand_dims(masks, 0)
    masks = np.ceil(masks).astype(int)
    _, h_orig, w_orig = masks.shape

    if outlier is None and restrict:
        raise ValueError('`restrict` requires providing an outlier.')

    if tight or restrict:
        dims     = h_orig, w_orig
        if restrict:
            border_p = 1.5
            dim_vals = np.where(masks[outlier])
            r_val = 1
        else:
            border_p = 0.15
            dim_vals = np.where(masks.sum(axis=0))
            r_val = 0
        dim_mins = [val.min() for val in dim_vals]
        dim_maxs = [val.max() for val in dim_vals]
        borders    = [int(np.ceil(border_p*(dmax - dmin))) 
            for dmin, dmax in zip(dim_mins, dim_maxs)]
        h_min, w_min = [np.max([0, val - bord - r_val]) 
            for val, bord in zip(dim_mins, borders)]
        h_max, w_max = [np.min([d, val + bord + r_val]) 
            for val, bord, d in zip(dim_maxs, borders, dims)]
        masks = masks[:, h_min:h_max, w_min:w_max]

    pad_zhw = [0, 0], [cw, cw], [cw, cw]
    contour_mask = np.pad(masks, pad_zhw, 'constant', constant_values=0)
    shifts = range(-cw, cw + 1)
    _, h, w = masks.shape
    for h_sh, w_sh in itertools.product(shifts, repeat=2):
        if h_sh == 0 and w_sh == 0:
            continue
        contour_mask[:, cw+h_sh: h+cw+h_sh, cw+w_sh: w+cw+w_sh] += masks
    
    contour_mask = contour_mask[:, cw:h+cw, cw:w+cw] != len(shifts)**2
    contour_mask = contour_mask * masks
    del masks

    if restrict:
        dim_vals = [h_min, h_max, w_min, w_max]
        comps = [0, h_orig, 0, w_orig]
        shifts = [0, 0, 0, 0]
        for i, (val, comp) in enumerate(zip(dim_vals, comps)):
            if val != comp:
                shifts[i] = r_val
        contour_mask = contour_mask[
            :, shifts[0]:comps[1]-shifts[1], shifts[2]:comps[3]-shifts[3]]
    
    mult_mask = np.ones([len(contour_mask), 1, 1])
    if outlier is not None:
        mult_mask[outlier] = 2
    contour_mask = np.max(contour_mask * mult_mask, axis=0)

    sub_ax.imshow(contour_mask, cmap=cm, interpolation='none')

    if savename:
        plt.imsave(savename, contour_mask, cmap=cm)

    return contour_mask

