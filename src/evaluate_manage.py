'''
Script for generating evaluation results
'''
import os
import logging

import argparse

import settings
from txtexeval.extractor import extractor_list
from txtexeval.data import LocalDatasetLoader, LocalResultStorage
from txtexeval.data import DataError
from txtexeval.evaluation import TextBasedResults, TextOnlyEvaluator
from txtexeval.evaluation import from_document_factory, dataset_format_map

logger = logging.getLogger()

def local_evaluate(dataset_type, dataset_name):    
    for extractor_cls in extractor_list:
        logger.info('started evaluating extractor %s', extractor_cls.NAME)
        results = TextBasedResults(extractor_cls.NAME)
        storage = LocalResultStorage(dataset_name, extractor_cls)
        
        loader = LocalDatasetLoader(dataset_name)
        for doc in loader:
            logger.debug('doc: %s', doc.raw_filename)
            format_clean = from_document_factory(doc, slug = dataset_type)
            
            try:
                result_string = storage.fetch_result(doc)
            except DataError:
                logger.info('skipped %s no result for %s extractor',
                             doc.raw_filename, extractor_cls.NAME)
                continue
            else:
                format_result = extractor_cls.formatted_result(result_string)
                evaluator = TextOnlyEvaluator(retrieved = format_result, relevant = format_clean)
                results.append_result(evaluator.get_eval_results())
            
    results = TextBasedResults()
    results.print_results()
    results.save(dataset_name)     
    
def parse_args():
    '''Sys argument parsing trough argparse'''
    parser = argparse.ArgumentParser(description = 'Tool for for generating evaluation results')
    parser.add_argument('dataset_type', choices = [i[0] for i in dataset_format_map], help = 'dataset type e.g. cleaneval' )
    parser.add_argument('dataset_name', help = 'name of the dataset')
    parser.add_argument('-v','--verbose', action = 'store_true', help = 'print log to console')
    args = parser.parse_args()
    # printing arguments
    print 'dataset type: %s' % args.dataset_type
    print 'dataset name: %s' % args.dataset_name
    return args
    
def logging_setup(verbose):
    '''Set verbose to True if you want the log to appear on stderr'''
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logd = os.path.join(settings.PATH_LOCAL_DATA,'results-cache','results.log')
    file = logging.FileHandler(filename = logd)
    file.setLevel(logging.INFO)
    file.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
    logger.addHandler(file)
    if verbose:
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
        logger.addHandler(console)
    print 'log: %s' % logd

def main():
    args = parse_args()
    logging_setup(args.verbose)
    print '[STARTED]'
    local_evaluate(args.dataset_type,args.dataset_name)
    print '[DONE]'
    
if __name__ == '__main__':
    main()