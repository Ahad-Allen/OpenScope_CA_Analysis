"""
run_logreg.py

This script runs and analyses logistic regressions on data generated by the 
AIBS experiments for the Credit Assignment Project

Authors: Colleen Gillon

Date: October, 2018

Note: this code uses python 3.7.

"""

import os
import copy
import argparse

from analysis import logreg
from util import gen_util
from sess_util import sess_gen_util, sess_ntuple_util, sess_str_util
from plot_fcts import logreg_plots


#############################################
def run_regr(args):
    """
    run_regr(args)

    Does runs of a logistic regressions on the specified comparison and range
    of sessions.
    
    Required args:
        - args (Argument parser): parser with analysis parameters as attributes:
            bal (bool)            : if True, classes are balanced
            batchsize (int)       : nbr of samples dataloader will load per 
                                    batch
            bri_dir (str)         : brick direction to analyse
            bri_size (int or list): brick sizes to include
            comp (str)            : type of comparison
            datadir (str)         : data directory
            device (str)          : device name (i.e., 'cuda' or 'cpu')
            ep_freq (int)         : frequency at which to print loss to 
                                    console
            error (str)           : error to take, i.e., 'std' (for std 
                                    or quintiles) or 'sem' (for SEM or MAD)
            fluor (str)           : fluorescence trace type
            fontdir (str)         : directory in which additional fonts are 
                                    located
            gabfr (int)           : gabor frame of reference if comparison 
                                    is 'surp'
            gabk (int or list)    : gabor kappas to include
            lr (num)              : model learning rate
            mouse_n (int)         : mouse number
            n_epochs (int)        : number of epochs
            n_reg (int)           : number of regular runs
            n_shuff (int)         : number of shuffled runs
            scale (str)           : type of scaling
            output (str)          : general directory in which to save 
                                    output
            parallel (bool)       : if True, runs are done in parallel
            plt_bkend (str)       : pyplot backend to use
            q1v4 (bool)           : if True, analysis is separated across 
                                    first and last quintiles
            reg (str)             : regularization to use
            runtype (str)         : type of run ('prod' or 'pilot')
            seed (int)            : seed to seed random processes with
            sess_n (int)          : session number
            stats (str)           : stats to take, i.e., 'mean' or 'median'
            stimtype (str)        : stim to analyse ('gabors' or 'bricks')
            train_p (list)        : proportion of dataset to allocate to 
                                    training
            uniqueid (str or int) : unique ID for analysis
    """

    args = copy.deepcopy(args)

    if args.datadir is None:
        args.datadir = os.path.join('..', 'data', 'AIBS') 

    if args.uniqueid == 'datetime':
        args.uniqueid = gen_util.create_time_str()
    elif args.uniqueid in ['None', 'none']:
        args.uniqueid = None

    reseed = False
    if args.seed in [None, 'None']:
        reseed = True

    # deal with parameters
    extrapar = {'uniqueid' : args.uniqueid,
                'seed'     : args.seed
               }
    
    techpar = {'reseed'   : reseed,
               'device'   : args.device,
               'parallel' : args.parallel,
               'plt_bkend': args.plt_bkend,
               'fontdir'  : args.fontdir,
               'output'   : args.output,
               'ep_freq'  : args.ep_freq,
               'n_reg'    : args.n_reg,
               'n_shuff'  : args.n_shuff,
               }

    mouse_df = 'mouse_df.csv'

    stimpar = logreg.get_stimpar(args.comp, args.stimtype, args.bri_dir, 
                                 args.bri_size, args.gabfr, args.gabk)
    analyspar = sess_ntuple_util.init_analyspar(args.fluor, stats=args.stats, 
                                            error=args.error, scale=args.scale)  
    if args.q1v4:
        quintpar = sess_ntuple_util.init_quintpar(4, [0, -1])
    else:
        quintpar = sess_ntuple_util.init_quintpar(1)
    logregpar = sess_ntuple_util.init_logregpar(args.comp, args.q1v4, 
                                        args.n_epochs, args.batchsize, args.lr, 
                                        args.train_p, args.wd, args.bal)
    omit_sess, omit_mice = sess_gen_util.all_omit(args.stimtype, args.runtype, 
                                            stimpar.bri_dir, stimpar.bri_size, 
                                            stimpar.gabk)

    sessids = sess_gen_util.get_sess_vals(mouse_df, 'sessid', args.mouse_n, 
                                          args.sess_n, args.runtype, 
                                          omit_sess=omit_sess, 
                                          omit_mice=omit_mice)

    if len(sessids) == 0:
        print(('No sessions found (mouse: {}, sess: {}, '
               'runtype: {})').format(args.mouse_n, args.sess_n, args.runtype))

    for sessid in sessids:
        sess = sess_gen_util.init_sessions(sessid, args.datadir, mouse_df, 
                                           args.runtype, fulldict=False)[0]
        logreg.run_regr(sess, analyspar, stimpar, logregpar, quintpar, 
                        extrapar, techpar)



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--output', 
                        default=os.path.join('results', 'logreg_models'),
                        help='where to store output')
    parser.add_argument('--datadir', default=None, 
                        help=('data directory (if None, uses a directory '
                              'defined below'))
    parser.add_argument('--task', default='run_regr', 
                        help='run_regr, analyse or plot')

        # technical parameters
    parser.add_argument('--plt_bkend', default=None, 
                        help='switch mpl backend when running on server')
    parser.add_argument('--parallel', action='store_true', 
                        help='do runs in parallel.')
    parser.add_argument('--cuda', action='store_true', 
                        help='run on cuda.')
    parser.add_argument('--ep_freq', default=50, type=int,  
                        help='epoch frequency at which to print loss')
    parser.add_argument('--n_reg', default=50, type=int, help='n regular runs')
    parser.add_argument('--n_shuff', default=50, type=int, 
                        help='n shuffled runs')

        # logregpar
    parser.add_argument('--comp', default='surp', 
                        help='surp, AvB, AvC, BvC, DvE, all')
    parser.add_argument('--n_epochs', default=1000, type=int)
    parser.add_argument('--batchsize', default=200, type=int)
    parser.add_argument('--lr', default=0.0001, type=float, 
                        help='learning rate')
    parser.add_argument('--train_p', default=0.75, type=float, 
                        help='proportion of dataset used in training set')
    parser.add_argument('--wd', default=0, type=float, 
                        help='weight decay to use')
    parser.add_argument('--q1v4', action='store_true', 
                        help='run on 1st quintile and test on last')
    parser.add_argument('--bal', action='store_true', 
                        help='if True, classes are balanced')

        # sesspar
    parser.add_argument('--mouse_n', default=1, type=int)
    parser.add_argument('--runtype', default='prod', help='prod or pilot')
    parser.add_argument('--sess_n', default='all')
    
        # stimpar
    parser.add_argument('--stimtype', default='gabors', help='gabors or bricks')
    parser.add_argument('--gabk', default=16, type=int, 
                        help='gabor kappa parameter')
    parser.add_argument('--gabfr', default=0, type=int, 
                        help='starting gab frame if comp is surp')
    parser.add_argument('--bri_dir', default='both', help='brick direction')
    parser.add_argument('--bri_size', default=128, help='brick size')

        # analyspar
    parser.add_argument('--scale', default='roi', 
                        help='scaling data: none, all or roi (by roi)')
    parser.add_argument('--fluor', default='dff', help='raw or dff')
    parser.add_argument('--stats', default='mean', help='mean or median')
    parser.add_argument('--error', default='sem', help='std or sem')

        # extra parameters
    parser.add_argument('--seed', default=-1, type=int, 
                        help='manual seed (-1 for None)')
    parser.add_argument('--uniqueid', default='datetime', 
                        help=('passed string, \'datetime\' for date and time '
                              'or \'none\' for no uniqueid'))

        # CI parameter for analyse and plot tasks
    parser.add_argument('--CI', default=0.95, type=float, help='shuffled CI')

        # from dict
    parser.add_argument('--dict_path', default=None, 
                        help='path of directory to plot from')


    args = parser.parse_args()

    args.device = gen_util.get_device(args.cuda)
    args.fontdir = os.path.join('..', 'tools', 'fonts')

    if args.runtype == 'pilot':
       args.output = '{}_pilot'.format(args.output)

    if args.q1v4:
        args.output = '{}_q1v4'.format(args.output)
    if args.bal:
        args.output = '{}_bal'.format(args.output)

    if args.comp == 'all':
        comps = ['surp', 'AvB', 'AvC', 'BvC', 'DvE']
    else:
        comps = gen_util.list_if_not(args.comp)

    if args.dict_path is not None:
        logreg_plots.plot_from_dict(args.dict_path, args.plt_bkend, 
                                    args.fontdir)

    else:
        for comp in comps:
            args.comp = comp
            print(('\nTask: {}\nStim: {} \nComparison: {}\n').format(args.task, 
                                                    args.stimtype, args.comp))

            if args.task == 'run_regr':
                run_regr(args)

            # collates regression runs and analyses accuracy
            elif args.task == 'analyse':
                logreg.run_analysis(args.output, args.stimtype, args.comp, 
                                    args.bri_dir, args.CI, args.parallel)

            elif args.task == 'plot':
                logreg.run_plot(args.output, args.stimtype, args.comp, 
                                args.bri_dir, args.fluor, args.scale, args.CI, 
                                args.plt_bkend, args.fontdir)

            else:
                gen_util.accepted_values_error('args.task', args.task, 
                                            ['run_regr', 'analyse', 'plot'])

