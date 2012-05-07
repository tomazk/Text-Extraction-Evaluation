'''
Script for plotting evaluation results.
'''
import os
import math

import argparse
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

import settings
from txtexeval.evaluation import TextBasedResults
from txtexeval.extractor import extractor_list, get_extractor_cls

def extractor_list_filter(extractor_slugs):
    '''
    Produce a filtered extractor_list based on a list that contains slugs of
    desired extractors. We need this because the global extractor_list 
    dictates the correct order.
    '''
    return [e for e in extractor_list if e.SLUG in extractor_slugs]


def dataset_stat_latex_print(dataset_name):
    '''
    Print the avg precision, recall and F1 score in latex format
    to console. 
    '''
    # get results
    txt_results = TextBasedResults()
    txt_results.load(dataset_name)
    txt_results.print_results()
    
    #package results
    elist = extractor_list_filter(txt_results.text_eval_results.keys())
    extractor_slugs = tuple([e.SLUG for e in elist])
    
    result_list = []
    for e in extractor_slugs:
    	result_tuple = (
    		get_extractor_cls(e).NAME,
    		txt_results.precision_statistics(e)[0],
    		txt_results.recall_statistics(e)[0],
    		txt_results.f1score_statistics(e)[0],
    	)
    	result_list.append(result_tuple)
    result_list.sort(key = lambda i: i[3])
    result_list.reverse()
    
    print '---------------- B< ------------------------'
    for r in result_list:
    	print '\\texttt{%s} & %.4f & %.4f & %.4f \\\\ \\hline' % r
    print '---------------- B< ------------------------'
    
    

def dataset_stat_plot(dataset_name, img_name):
    '''
    Plot the avg precision, recall and F1 score bar chart for the given dataset
    name.
    '''
    # get results
    txt_results = TextBasedResults()
    txt_results.load(dataset_name)
    txt_results.print_results()
    
    #package results
    elist = extractor_list_filter(txt_results.text_eval_results.keys())
    extractor_slugs = tuple([e.SLUG for e in elist])
    packaged_data = (
        ('Precision', [ (txt_results.precision_statistics(e), e) for e in extractor_slugs ] ),
        ('Recall', [ (txt_results.recall_statistics(e), e) for e in extractor_slugs ] ),
        ('F1 score', [ (txt_results.f1score_statistics(e), e) for e in extractor_slugs ] ),
    )
    
    bar_color = ('b','c','m')
    for i,pdata in enumerate(packaged_data):
    
        # package plotting values 
        num_of_extractors = len(extractor_slugs)
        ind = np.arange(num_of_extractors)  # the x locations for the groups
        width = 0.6      # the width of the bars
        
        result_list = pdata[1]
        result_list.sort(key=lambda i: i[0][0])
        result_list.reverse()
        
        avg = [ x[0][0] for x in result_list]
        stddev = [ x[0][1] for x in result_list]
        
        # plot
        plt.subplot(3,1,i+1)
        plt.grid(True, alpha = 0.5)
        
        rects_avg = plt.bar(ind, avg, width,color=bar_color[i], ecolor ='g' ,
            yerr = stddev, linewidth = 0.5, alpha = 0.8)
        
        # lables and titles
        extractor_names = [ get_extractor_cls(r[1]).NAME for r in result_list]
        plt.title(pdata[0])
        plt.xticks(ind+width/2., extractor_names, size = 'xx-small', rotation = 'vertical')
        plt.legend(  (rects_avg[0],),
                     ('avg',),
                     fancybox = True,
                     prop = dict(size='x-small'),
                     loc = 4 # lower right 
        )
        for rect in rects_avg:
            height = rect.get_height()
            plt.text(rect.get_x()+rect.get_width()/2.25,rect.get_height() + 0.01 ,
                 '%1.2f'%height, ha='center', va='bottom', size = 'x-small')
        
        
    #subplots adjusting
    plt.subplots_adjust( wspace=0.5, hspace=0.9)
    
    #adjust figure height
    fig = plt.gcf()
    w,h = fig.get_size_inches()
    fig.set_size_inches( w , h*1.6)
    
    # output 
    out_path = os.path.join(settings.PATH_LOCAL_DATA, 'plot-output', img_name)
    plt.savefig(out_path)
    
def equidistant_count(start, stop, step , list):
    '''Return a tuple containing equidistant distribution baskets.'''
    limit_list = np.arange(start,stop, step)
    count = [0] * len(limit_list) 
    
    for value in list:
        value = float(value)
        assert start <= value <= stop
        mark = False
        for i, low in enumerate(limit_list):
            up = low + step
            #print 'low %s up %s' % (str(low), str(up))
            if i < (len(limit_list)-1) and low <= value < up:
                count[i] += 1
                mark =True
                break
            elif i == (len(limit_list)-1) and low <= value <=up:
                count[i] += 1
                mark  =True
                break
        '''
        if not mark:
            print len(limit_list)
            print j
            print value
            print type(value)
            print 0.3 <= value < 0.35
            raise Exception('something very weird is going on - %s' % str(value))
        '''
    return tuple(count)

def resize_axis_tick_labels(axis, size = 'xx-small'):
    for label in axis.get_ticklabels():
        label.set_size(size)
        
def extractor_stat_plot(dataset_name, img_name):
    '''Plot the distributions of per-document precision, recall & F1 score '''
    #np.seterr(all='raise')
    fig = plt.figure()
    
    # get results and repackage the data
    txt_results = TextBasedResults()
    txt_results.load(dataset_name)
    txt_results.print_results()
    
    elist = extractor_list_filter(txt_results.text_eval_results.keys())
    for ex_index,extractor_cls in enumerate(elist):
    
        # repackage results
        extractor_results = txt_results.filtered_results(extractor_cls.SLUG)
        results_list_prec = [r.precision for r in extractor_results] 
        results_list_rec = [r.recall for r in extractor_results]
        results_list_f1 = [r.f1_score for r in extractor_results ]
        
        width = 0.05  # the width of the bars
        ind = np.arange(0,1,width)
        n = len(ind)

        print extractor_cls.NAME
        eq_count_prec = equidistant_count(0, 1, width, results_list_prec)
        print len(results_list_prec)
        print sum(eq_count_prec)
        eq_count_rec = equidistant_count(0, 1, width, results_list_rec)
        print len(results_list_rec)
        print sum(eq_count_rec)
        eq_count_f1 = equidistant_count(0, 1, width, results_list_f1)
        print len(results_list_f1)
        print sum(eq_count_f1)
        
        # plotting
        ax = fig.add_subplot(6,3,ex_index+1,projection = '3d')
        
        ax.bar3d(ind,np.array([0]*n), np.array([0]*n) ,
                 dx = width, dy = width*2,dz=eq_count_prec,
                 color ='b', linewidth = 0.3, alpha = 0.4)
        ax.bar3d(ind,np.array([1]*n), np.array([0]*n) ,
                 dx = width, dy = width*2,dz=eq_count_rec,
                 color ='c', linewidth = 0.3,alpha = 0.5)
        ax.bar3d(ind,np.array([2]*n), np.array([0]*n) ,
                 dx = width, dy = width*2,dz=eq_count_f1,
                 color ='m', linewidth = 0.3,alpha = 0.8)
    
        
        ax.set_title(extractor_cls.NAME, size = 'small')
        #ax.set_xlabel('\nlimits',size = 'x-small', linespacing=2)
        ax.set_zlabel('\nnum. of instances',size = 'x-small', linespacing=1)
        ax.yaxis.set_ticks([])
        resize_axis_tick_labels(ax.xaxis)
        resize_axis_tick_labels(ax.zaxis)
        ax.grid(True, alpha = 0.7)
        
    # with 3d plotting we need to use proxy artist because legends
    # are not supported
    blue = plt.Rectangle((0, 0), 1, 1, fc='b') # proxys
    cyan = plt.Rectangle((0, 0), 1, 1, fc='c')
    mag = plt.Rectangle((0, 0), 1, 1, fc='m')
    fig.legend(      (blue,cyan,mag),
                     ('precision','recall','f1 score'),
                     fancybox = True,
                     prop = dict(size='x-small')
    )
    w,h = fig.get_size_inches()
    fig.set_size_inches( w *1.5, h*2.5)
    fig.subplots_adjust( wspace=0.025, hspace=0.15)
    
    # save plot
    out_path = os.path.join(settings.PATH_LOCAL_DATA, 'plot-output', img_name)
    fig.savefig(out_path,bbox_inches='tight')

    
def dataset_contents_plot(dataset_name, img_name):
    '''Plot the error case analysis.'''
    # get results
    txt_results = TextBasedResults()
    txt_results.load(dataset_name)
    txt_results.print_results()
    
    # package data
    elist = extractor_list_filter(txt_results.text_eval_results.keys())
    extractor_slugs = tuple( [e.SLUG for e in elist] )
    package = [
        ('|rel| = 0','#9DFADE', [ txt_results.result_contents(ex).rel_empty for ex in extractor_slugs] ),
        ('|rel intersect ret| = 0','#3C70A3', [ txt_results.result_contents(ex).rel_ret_empty for ex in extractor_slugs] ),
        ('|ret| = 0','#5CCBED', [ txt_results.result_contents(ex).ret_empty for ex in extractor_slugs] ),
        ('missmatch','#A76CF5', [ txt_results.result_contents(ex).missmatch for ex in extractor_slugs] ),
        ('failed','#C43156', [ txt_results.result_contents(ex).fail for ex in extractor_slugs] ),
        ('successful','#31C460', [ txt_results.result_contents(ex).succ for ex in extractor_slugs] ),
    ]
    num_of_extractors = len(extractor_slugs)
    ind = np.arange(num_of_extractors)  # the x locations for the groups
    width = 0.6
    
    fig = plt.gcf()
    fig.legend(      [plt.Rectangle((0, 0), 1, 1, fc=p[1]) for p in package],
                     [p[0] for p in package],
                     fancybox = True,
                     prop = dict(size='x-small'),                     
    )
    
    # with successful instances
    ax1 = plt.subplot(121)
    bottom_y = np.zeros(num_of_extractors)
    for pdata in package:
        ax1.bar(ind, pdata[2],width,bottom = bottom_y,color=pdata[1], 
                ecolor ='g', linewidth = 0.2, alpha = 0.95)
        bottom_y += pdata[2]

    ax2 = plt.subplot(122)
    bottom_y = np.zeros(num_of_extractors)
    del package[-1]
    for pdata in package:
        ax2.bar(ind, pdata[2],width,bottom = bottom_y,color=pdata[1], 
                ecolor ='g', linewidth = 0.2, alpha = 0.95)
        bottom_y += pdata[2]
    
    # xticks labels
    extractor_names = [ get_extractor_cls(e).NAME for e in extractor_slugs]
    ax1.set_xticks(ind+width/2.)
    ax1.set_xticklabels(extractor_names, size = 'xx-small', rotation = 'vertical')
    ax2.set_xticks(ind+width/2.)
    ax2.set_xticklabels(extractor_names, size = 'xx-small', rotation = 'vertical')
    
    # grid settings
    fig.suptitle('Border cases')
    ax1.grid(True, alpha = 0.5)
    ax2.grid(True, alpha = 0.5)
    
    # adjustment
    w,h = fig.get_size_inches()
    fig.set_size_inches( w*1.5, h*1.5)
    fig.subplots_adjust( bottom = 0.2)
    
    # output 
    out_path = os.path.join(settings.PATH_LOCAL_DATA, 'plot-output', img_name)
    fig.savefig(out_path)
    
def parse_args(args):
    parser = argparse.ArgumentParser(description = 'Plotting tool')
    parser.add_argument('action', choices = ('dataset_stat', 'extr_stat','contents','dataset_latex'))
    parser.add_argument('dataset_name', help = 'name of the dataset')
    parser.add_argument('-f','--format', type=str, help = 'format: png, pdf, ps, eps or svg')
    return parser.parse_args(args)
    
def main(args):
    pargs = parse_args(args)
    output_img_name = '%s-%s' % (pargs.dataset_name, pargs.action)
    if pargs.format:
        output_img_name = '%s.%s'  % (output_img_name, pargs.format) 
    else:
        output_img_name = '%s.%s'  % (output_img_name, 'png') 
        
    if pargs.action == 'dataset_stat':
        dataset_stat_plot(pargs.dataset_name, output_img_name)
    elif pargs.action == 'dataset_latex':
        dataset_stat_latex_print(pargs.dataset_name)        
    elif pargs.action == 'extr_stat':
        extractor_stat_plot(pargs.dataset_name, output_img_name)
    elif pargs.action == 'contents':
        dataset_contents_plot(pargs.dataset_name, output_img_name)
    
    print '[DONE]'

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
