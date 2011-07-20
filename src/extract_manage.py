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
        if timeout:
            time.sleep(timeout)
        
    storage.dump_summary()
    logger.info('finished with %s dataset', dataset_name)
    
def parse_args(args):
    '''Sys argument parsing trough argparse'''
    ex_list = [e.SLUG for e in extractor_list]    
    parser = argparse.ArgumentParser(description = 'Tool for extracting article text from dataset instances')
    parser.add_argument('extractor', choices = ex_list, help = 'extractor slug or [all] for iterating over all extractors')
    parser.add_argument('dataset_name', help = 'name of the dataset')
    parser.add_argument('-v','--verbose', action = 'store_true', help = 'print log to console')
    parser.add_argument('-t','--timeout', type=int, default=0, help='wait x seconds between extraction operations')
    parser.add_argument('-rf','--retry_failed', action = 'store_true', help = 'retry to extract text from instances that failed')
    return parser.parse_args(args)
    
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

def main(args):
    pargs = parse_args(args)
    logging_setup(pargs.verbose, get_local_path(pargs.dataset_name,'result','result.log'))
    
    print '[STARTED]'
    local_extract(pargs.dataset_name, pargs.extractor, pargs.timeout, pargs.retry_failed)
    print '[DONE]'
    
if __name__ == '__main__':
    import sys
    main(sys.argv[1:])