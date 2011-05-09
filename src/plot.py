import os
import math

import argparse
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

import settings
from txtexeval.evaluation import TextBasedResults
from txtexeval.extractor import extractor_list, get_extractor_cls

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
        
    
def extractor_stat_plot(dataset_name, extractor_slug):
    plt.clf() # clear current figure
    extractor_cls = get_extractor_cls(extractor_slug)
    
    # get results and repackage the data
    txt_results = TextBasedResults()
    txt_results.load(dataset_name)
    txt_results.print_results()
    extractor_results = txt_results.get_results()[extractor_cls.NAME]
    
    non_inf_nan = lambda r: (not math.isinf(r)) and (not math.isnan(r))
    results_list_prec = filter(non_inf_nan, [r[0] for r in extractor_results]) 
    results_list_rec = filter(non_inf_nan,[r[1] for r in extractor_results])
    results_list_f1 = filter(non_inf_nan,[r[0] for r in extractor_results ])
    
    width = 0.1  # the width of the bars
    ind = np.arange(0,1,width)
    n = len(ind)
    eq_count_prec = equidistant_count(0, 1, width, results_list_prec)
    eq_count_rec = equidistant_count(0, 1, width, results_list_rec)
    eq_count_f1 = equidistant_count(0, 1, width, results_list_f1)
    
    # plotting
    fig = plt.figure()
    ax = fig.add_subplot(111, projection = '3d')
    
    ax.bar3d(ind,np.array([0]*n), np.array([0]*n) ,
             dx = width, dy = width*2,dz=eq_count_prec,
             color ='b', linewidth = 0.3, alpha = 0.4)
    ax.bar3d(ind,np.array([1]*n), np.array([0]*n) ,
             dx = width, dy = width*2,dz=eq_count_rec,
             color ='m', linewidth = 0.3,alpha = 0.5)
    ax.bar3d(ind,np.array([2]*n), np.array([0]*n) ,
             dx = width, dy = width*2,dz=eq_count_f1,
             color ='c', linewidth = 0.3,alpha = 0.8)

    
    plt.title(extractor_cls.NAME)
    ax.set_xlabel('limits')
    ax.set_zlabel('no. of instances')
    ax.yaxis.set_ticks([])
    ax.grid(True, alpha = 0.7)
    
    # with 3d plotting we need to use proxy artist because legends
    # are not supported
    blue = plt.Rectangle((0, 0), 1, 1, fc="b") # proxys
    cyan = plt.Rectangle((0, 0), 1, 1, fc="c")
    mag = plt.Rectangle((0, 0), 1, 1, fc="m")
    plt.legend(      (blue,mag,cyan),
                     ('precision','recall','f1 score'),
                     fancybox = True,
                     prop = dict(size='x-small')
    )
    
    # save plot
    out_path = os.path.join(settings.PATH_LOCAL_DATA, 'plot-output', 
                            '%s.png' % extractor_slug)
    plt.savefig(out_path)
    
    
 
def parse_args():
    parser = argparse.ArgumentParser(description = 'Plotting tool')
    parser.add_argument('action', choices = ('dataset_stat', 'extr_stat'))
    parser.add_argument('dataset_name', help = 'name of the dataset')
    parser.add_argument('-o','--output_img_name', type=str, help = 'name of the output image')
    return parser.parse_args()
    
def main():
    args = parse_args()
    
    if args.action == 'dataset_stat':
        output_img_name = args.output_img_name or '%s.png' % args.dataset_name
        precision_recall_plot(args.dataset_name, output_img_name)
    elif args.action == 'extr_stat':
        # TODO: loop over all extractors
        extractor_stat_plot(args.dataset_name, 'alchemy')
    
    print '[DONE]'

if __name__ == '__main__':
    main()