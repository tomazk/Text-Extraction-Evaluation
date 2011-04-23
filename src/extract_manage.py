'''
Script for extracting article text from dataset instances
'''
import sys
import logging

import argparse

from txtexeval.extractor import get_extractor_cls, extractor_list
from txtexeval.extractor import ExtractorError
from txtexeval.data import LocalDatasetLoader, LocalResultStorage
from txtexeval.data import DataError

logger = logging.getLogger()

def local_extract(dataset_name, extractor_slug, verbose = False):
    # init storage and loader
    ex = get_extractor_cls(extractor_slug)
    storage = LocalResultStorage(dataset_name, ex)
    loader = LocalDatasetLoader(dataset_name)
    
    # setup logging
    logging_setup(verbose, storage.log_path)
    
    logger.info('started extracting content from %s dataset', dataset_name)
    for doc in loader:
        storage.push_result(doc)
        logger.debug('extracted content from %s', doc.raw_filename)
    logger.info('finished with %s dataset', dataset_name)
    
def parse_args():
    '''Sys argument parsing trough argparse'''
    parser = argparse.ArgumentParser(description = 'Tool for extracting article text from dataset instances')
    parser.add_argument('extractor', choices = [e.SLUG for e in extractor_list])
    parser.add_argument('dataset_name', help = 'name of the dataset')
    parser.add_argument('-v','--verbose', action = 'store_true', help = 'print log to console')
    #TODO: parser.add_argument('-m','--missing_only', action = 'store_true')
    args = parser.parse_args()
    
    # printing arguments
    print 'extractor: %s' % args.extractor
    print 'dataset name: %s' % args.dataset_name
    
    return args
    
def logging_setup(verbose, output_path):
    '''Set verbose to True if you want the log to appear on stderr'''
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.FileHandler(filename = output_path))
    if verbose:
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
        logger.addHandler(console)

def main():
    args = parse_args()
    
    try:
        local_extract(args.dataset_name, args.extractor, args.verbose)
    except DataError as e:
        print 'Data related error: %s' % e
        sys.exit(-1)
    except ExtractorError as e:
        print 'Extractor related error: %s' % e
        sys.exit(-1)
    except Exception as e:
        print 'Unknown error: %s' % e
        raise
    print '[DONE]'
    
if __name__ == '__main__':
    main()