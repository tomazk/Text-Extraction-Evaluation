'''
Script for extracting article text from dataset instances
'''
import time
import logging

import argparse

from txtexeval.extractor import get_extractor_cls, extractor_list
from txtexeval.data import LocalDatasetLoader, LocalResultStorage
from txtexeval.util import get_local_path

logger = logging.getLogger()

def local_extract(dataset_name, extractor_slug, timeout, retry_failed):
    # init storage and loader
    ex = get_extractor_cls(extractor_slug)
    
    if retry_failed:
        loader = LocalDatasetLoader(dataset_name, load_failed = extractor_slug)
    else:
        loader = LocalDatasetLoader(dataset_name)
    storage = LocalResultStorage(dataset_name, ex)
    
    logger.info('started extracting content from %s dataset using %s', dataset_name, ex.NAME)
    for doc in loader:
        storage.push_result(doc)
        logger.debug('extracted content from %s', doc.raw_filename)
        if timeout:
            time.sleep(timeout)
        
    storage.dump_summary()
    logger.info('finished with %s dataset', dataset_name)
    
def parse_args():
    '''Sys argument parsing trough argparse'''
    ex_list = [e.SLUG for e in extractor_list]
    ex_list.append('all')
    
    parser = argparse.ArgumentParser(description = 'Tool for extracting article text from dataset instances')
    parser.add_argument('extractor', choices = ex_list, help = 'extractor slug or [all] for iterating over all extractors')
    parser.add_argument('dataset_name', help = 'name of the dataset')
    parser.add_argument('-v','--verbose', action = 'store_true', help = 'print log to console')
    parser.add_argument('-t','--timeout', type=int, default=0, help='wait x seconds between extraction operations')
    parser.add_argument('-rf','--retry_failed', action = 'store_true', help = 'retry to extract text from instances that failed')
    args = parser.parse_args()
    
    # printing arguments
    print 'extractor: %s' % args.extractor
    print 'dataset name: %s' % args.dataset_name
    
    return args
    
def logging_setup(verbose, output_path):
    '''Set verbose to True if you want the log to appear on stderr'''
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    file = logging.FileHandler(filename = output_path)
    file.setLevel(logging.INFO)
    file.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
    logger.addHandler(file)
    
    if verbose:
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
        logger.addHandler(console)

def main():
    args = parse_args()
    
    # setup logging
    logging_setup(args.verbose, get_local_path(args.dataset_name,'result','result.log'))
    
    print '[STARTED]'
    if args.extractor == 'all': # special case
        for ex in extractor_list:
            local_extract(args.dataset_name, ex.SLUG, args.timeout, args.retry_failed)
    else:
        local_extract(args.dataset_name, args.extractor, args.timeout, args.retry_failed)
    print '[DONE]'
    
if __name__ == '__main__':
    main()