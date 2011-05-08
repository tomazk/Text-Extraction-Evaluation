import os

import numpy as np
import matplotlib.pyplot as plt

import settings
from txtexeval.evaluation import TextBasedResults
from txtexeval.extractor import extractor_list

#helper
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        plt.text(rect.get_x()+rect.get_width()/2.25,rect.get_height() + 0.01 ,
                 '%1.2f'%height, ha='center', va='bottom', size = 'x-small')

# get results
txt_results = TextBasedResults()
txt_results.load('google-news')
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
    
    rects_avg = plt.bar(ind, avg, width,color=bar_color[i], ecolor ='g' ,yerr = stddev)
    
    # lables and titles
    plt.title(pdata[0])
    
    plt.xticks(ind+width/2., extractor_names, size = 'xx-small', rotation = 'vertical')
    
    plt.legend( (rects_avg[0],),
                 ('avg',),
                 fancybox = True,
                 prop = dict(size='x-small')
    )
    
    autolabel(rects_avg)
    
    
#subplots adjusting
plt.subplots_adjust( wspace=0.5, hspace=0.9)

#adjust figure height
fig = plt.gcf()
w,h = fig.get_size_inches()
fig.set_size_inches( w , h*1.6)

# output 
out_path = os.path.join(settings.PATH_LOCAL_DATA, 'plot-output',  'img.png')
plt.savefig( out_path )
print 'done'