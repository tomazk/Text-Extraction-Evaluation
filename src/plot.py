import os
import math

import argparse
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

import settings
from txtexeval.evaluation import TextBasedResults
from txtexeval.extractor import extractor_list

def precision_recall_plot(dataset_name, img_name):

    # get results
    txt_results = TextBasedResults()
    txt_results.load(dataset_name)
    txt_results.print_results()
    
    #package results
    extractor_names = tuple( [e.NAME for e in extractor_list] )
    packaged_data = (
        ('Precision', [ txt_results.precision_statistics(en) for en in extractor_names ]),
        ('Recall', [ txt_results.recall_statistics(en) for en in extractor_names ]),
        ('F1 score', [ txt_results.f1score_statistics(en) for en in extractor_names ]),             
    )
    
    bar_color = ('b','c','m')
    
    for i,pdata in enumerate(packaged_data):
    
        # package plotting values 
        num_of_extractors = len(extractor_names)
        ind = np.arange(num_of_extractors)  # the x locations for the groups
        width = 0.6      # the width of the bars
        
        avg = [ x[0] for x in pdata[1]]
        stddev = [ x[1] for x in pdata[1]]
        
        # plot
        plt.subplot(3,1,i+1)
        plt.grid(True, alpha = 0.5)
        
        rects_avg = plt.bar(ind, avg, width,color=bar_color[i], ecolor ='g' ,
            yerr = stddev, linewidth = 0.5, alpha = 0.8)
        
        # lables and titles
        plt.title(pdata[0])
        plt.xticks(ind+width/2., extractor_names, size = 'xx-small', rotation = 'vertical')
        plt.legend( (rects_avg[0],),
                     ('avg',),
                     fancybox = True,
                     prop = dict(size='x-small')
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
    limit_list = np.arange(start,stop, step)
    count = []
    for low in limit_list:
        up = low + step
        bmap = map(lambda x: 1 if low <= x < up else 0 , list)
        count.append(sum(bmap))
    return tuple(count)

def resize_axis_tick_labels(axis, size = 'xx-small'):
    for label in axis.get_ticklabels():
        label.set_size(size)
        
def extractor_stat_plot(dataset_name, output_img_name):
    fig = plt.figure()
    
    # get results and repackage the data
    txt_results = TextBasedResults()
    txt_results.load(dataset_name)
    txt_results.print_results()
    
    for ex_index,extractor_cls in enumerate(extractor_list):
    
        # repackage results
        extractor_results = txt_results.filtered_results(extractor_cls.NAME)
        results_list_prec = [r.precision for r in extractor_results] 
        results_list_rec = [r.recall for r in extractor_results]
        results_list_f1 = [r.f1_score for r in extractor_results ]
        
        width = 0.05  # the width of the bars
        ind = np.arange(0,1,width)
        n = len(ind)
        eq_count_prec = equidistant_count(0, 1, width, results_list_prec)
        eq_count_rec = equidistant_count(0, 1, width, results_list_rec)
        eq_count_f1 = equidistant_count(0, 1, width, results_list_f1)
        
        # plotting
        ax = fig.add_subplot(5,3,ex_index+1,projection = '3d')
        
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
        ax.set_xlabel('\nlimits',size = 'x-small', linespacing=2)
        ax.set_zlabel('\nno. of instances',size = 'x-small', linespacing=2)
        ax.yaxis.set_ticks([])
        resize_axis_tick_labels(ax.xaxis)
        resize_axis_tick_labels(ax.zaxis)
        ax.grid(True, alpha = 0.7)
        
    # with 3d plotting we need to use proxy artist because legends
    # are not supported
    blue = plt.Rectangle((0, 0), 1, 1, fc="b") # proxys
    cyan = plt.Rectangle((0, 0), 1, 1, fc="c")
    mag = plt.Rectangle((0, 0), 1, 1, fc="m")
    fig.legend(      (blue,cyan,mag),
                     ('precision','recall','f1 score'),
                     fancybox = True,
                     prop = dict(size='x-small')
    )
    w,h = fig.get_size_inches()
    fig.set_size_inches( w *1.5, h*2.5)
    fig.subplots_adjust( wspace=0.025, hspace=0.15)
    
    # save plot
    out_path = os.path.join(settings.PATH_LOCAL_DATA, 'plot-output', output_img_name)
    fig.savefig(out_path)
    
    
 
def parse_args():
    parser = argparse.ArgumentParser(description = 'Plotting tool')
    parser.add_argument('action', choices = ('dataset_stat', 'extr_stat'))
    parser.add_argument('dataset_name', help = 'name of the dataset')
    parser.add_argument('-o','--output_img_name', type=str, help = 'name of the output image')
    return parser.parse_args()
    
def main():
    args = parse_args()
    
    output_img_name = args.output_img_name or '%s.png' % args.dataset_name
    if args.action == 'dataset_stat':
        precision_recall_plot(args.dataset_name, output_img_name)
    elif args.action == 'extr_stat':
        extractor_stat_plot(args.dataset_name, output_img_name)
    
    print '[DONE]'

if __name__ == '__main__':
    main()