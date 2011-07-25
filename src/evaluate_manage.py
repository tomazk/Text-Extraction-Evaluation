'''
Script for generating evaluation results
'''
import os
import logging

import argparse

import settings
from txtexeval.extractor import extractor_list, get_extractor_cls
from txtexeval.data import LocalDatasetLoader, LocalResultStorage
from txtexeval.data import DataError
from txtexeval.evaluation import TextBasedResults, TextOnlyEvaluator
from txtexeval.evaluation import from_document_factory, dataset_format_map

logger = logging.getLogger()

def single_evaluation(extractor_cls, results, dataset_type, dataset_name):
    logger.info('started evaluating extractor %s', extractor_cls.NAME)
    results.set_extractor(extractor_cls.SLUG)
    storage = LocalResultStorage(dataset_name, extractor_cls)
    
    loader = LocalDatasetLoader(dataset_name)
    for doc in loader:
        logger.debug('doc: %s', doc.id)
        format_clean = from_document_factory(doc, slug = dataset_type)
        try:
            result_string = storage.fetch_result(doc)
        except DataError:
            logger.info('no stored result for %s at %s extractor',
                        doc.id, extractor_cls.NAME)
            continue
        else:
            format_result = extractor_cls.formatted_result(result_string)
            evaluator = TextOnlyEvaluator(
                        retrieved = format_result,
                        relevant = format_clean,
                        id = doc.id)
            results.add_result(evaluator.get_eval_results())

def local_evaluate(dataset_type, dataset_name, update_ext_slug = None):
    results = TextBasedResults()
    
    if update_ext_slug:
        results.load(dataset_name)
        ex_cls = get_extractor_cls(update_ext_slug)
        single_evaluation(ex_cls, results, dataset_type, dataset_name)
    else:
        for extractor_cls in extractor_list:
            single_evaluation(extractor_cls, results, dataset_type, dataset_name)

    results.dataset_len = len(LocalDatasetLoader(dataset_name))
    results.save(dataset_name)     
    results.print_results()
    
def parse_args(args):
    '''Sys argument parsing trough argparse'''
    parser = argparse.ArgumentParser(description = 'Tool for for generating evaluation results')
    parser.add_argument('dataset_type', choices = [i[0] for i in dataset_format_map], help = 'dataset type e.g. cleaneval' )
    parser.add_argument('dataset_name', help = 'name of the dataset')
    parser.add_argument('-v','--verbose', action = 'store_true', help = 'print log to console')
    parser.add_argument('-u','--update', choices = [e.SLUG for e in extractor_list], help = 'update the results for a single extractor')
    return parser.parse_args(args)
    
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

def main(args):
    pargs = parse_args(args)
    logging_setup(pargs.verbose)
    print '[STARTED]'
    local_evaluate(pargs.dataset_type, pargs.dataset_name, pargs.update)
    print '[DONE]'
    
if __name__ == '__main__':
    import sys
    main(sys.argv[1:])