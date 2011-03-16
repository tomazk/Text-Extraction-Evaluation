import os

import numpy as np
import matplotlib.pyplot as plt

import settings
from txtexeval.evaluation import TextBasedResults

#helper
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        plt.text(rect.get_x()+rect.get_width()/2., 0.01 , '%1.2f'%height,ha='center', va='bottom')

# get results
txt_results = TextBasedResults()
txt_results.load()
txt_results.print_results()

#package results
extractor_names = tuple( [name for name in txt_results.get_results().iterkeys()] )
packaged_data = (
    ('Precision', [ txt_results.precision_statistics(en) for en in extractor_names ]),
    ('Recall', [ txt_results.recall_statistics(en) for en in extractor_names ]),
    ('F1 score', [ txt_results.f1score_statistics(en) for en in extractor_names ]),             
)

for i,pdata in enumerate(packaged_data):

    # package plotting values 
    num_of_extractors = len(extractor_names)
    ind = np.arange(num_of_extractors)  # the x locations for the groups
    width = 0.25      # the width of the bars
    
    avg = [ x[0] for x in pdata[1]]
    stddev = [ x[1] for x in pdata[1]]
    
    # plot
    plt.subplot(3,1,i+1)
    rects_avg = plt.bar(ind, avg, width,color='b')
    rects_stddev = plt.bar(ind+width, stddev, width,color='c')
    
    # lables and titles
    plt.title(pdata[0])
    
    plt.xticks(ind+width, extractor_names, size = 'small' )
    
    plt.legend( (rects_avg[0], rects_stddev[0]),
                 ('avg', 'stddev'),
                 fancybox = True,
                 prop = dict(size='x-small')
    )
    
    autolabel(rects_avg)
    autolabel(rects_stddev)
    
    
#subplots adjusting
plt.subplots_adjust( wspace=0.5, hspace=0.5)

#adjust figure height
fig = plt.gcf()
w,h = fig.get_size_inches()
fig.set_size_inches( w*0.75 , h*1.30)

# output 
out_path = os.path.join(settings.PATH_LOCAL_DATA, 'plot-output',  'img.png')
plt.savefig( out_path )
print 'done'