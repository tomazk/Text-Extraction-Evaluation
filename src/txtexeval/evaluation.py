import os
import re
import pickle
import string
import difflib
import math
from collections import namedtuple

import settings

# module utils

def _remove_punctuation(s):
    exclude = set(string.punctuation)
    return ''.join( ch for ch in s if ch not in exclude )

# results

Result = namedtuple('Result', 'precision recall f1_score')# result instance

class BaseEvalResults(object):
    '''Base results container'''
    
    __pickle_filepath = os.path.join(settings.PATH_LOCAL_DATA, 'results.pickle')
    
    __internal_state = {} # Borg design pattern
    
    def __init__(self, extractor = None):
        self.__dict__ = self.__internal_state
        
        # ensure the presence of attributes
        if not 'text_eval_results' in self.__dict__: 
            self.text_eval_results = {}
        
        # optional
        if extractor and (not (extractor in self.text_eval_results)):
            self.text_eval_results[extractor] = []
        self._extractor = extractor

    def save(self):
        '''Pickle the internal state'''
        with open( self.__pickle_filepath ,'wb') as f:
            pickle.dump( self.__internal_state ,f)
    
    def load(self):
        '''Unpickle the internal state'''
        with open( self.__pickle_filepath ,'rb') as f:
            self.__internal_state = pickle.load(f)
            self.__dict__ = self.__internal_state
            
    def append_result(self, result):
        '''Append the result instance to the given extractor'''
        pass
    
    def print_results(self):
        '''Print results to stdout'''
        pass
    
            
class TextBasedResults(BaseEvalResults):
            
    def get_results(self):
        '''Getter'''
        return self.text_eval_results
    
    def append_result(self, result):
        if self._extractor:
            self.text_eval_results[self._extractor].append(result)
    
    def _statistics(self, extractor, stat_typ): # DRY helper
        if stat_typ == 'precision':  selector = 0
        elif stat_typ == 'recall':   selector = 1
        elif stat_typ == 'f1_score': selector = 2
        
        results_list = self.text_eval_results[extractor]
        avg = sum([r[selector] for r in results_list]) / float(len(results_list))
        
        stddev =  sum([(r[selector] - avg)**2. for r in results_list]) / float(len(results_list))
        stddev = math.sqrt(stddev)
        
        return avg, stddev
      
    def precision_statistics(self, extractor):
        '''Return a tuple containing (avg, stddev)'''
        return self._statistics(extractor, 'precision')
    
    def recall_statistics(self, extractor):
        '''Return a tuple containing (avg, stddev)'''
        return self._statistics(extractor, 'recall')
    
    def f1score_statistics(self, extractor):
        '''Return a tuple containing (avg, stddev)'''
        return self._statistics(extractor, 'f1_score')
        
    def print_results(self):
        print 'results based on text based evaluation'
        for extractor_name in self.text_eval_results.iterkeys():
            
            print '----------------'
            print 'Ex. name: %s' % extractor_name
            print 'avg. precision: %f   stddev: %f' % self.precision_statistics(extractor_name) 
            print 'avg. recall: %f   stddev: %f' % self.recall_statistics(extractor_name) 
            print 'avg. F1 score: %f   stddev: %f' % self.f1score_statistics(extractor_name) 
    
# evaluators    

class BaseEvaluator():
    '''Outline for evaluators'''
    
    def __init__(self, retrieved, relevant):
        self.retrieved = retrieved
        self.relevant = relevant
    
    
    def get_results(self):
        # return instance of Result
        pass
    
class TextOnlyEvaluator(BaseEvaluator):
    
    def get_results(self):
        
        s = difflib.SequenceMatcher()
        rel = self.relevant.get_word_seq()
        ret = self.retrieved.get_word_seq()
        
        s.set_seqs(rel, ret)
        matches = s.get_matching_blocks()[:-1]
        
        rel_union_ret = sum(i.size for i in matches) if len(matches) > 0 else 0
        
        precision = float(rel_union_ret) / float(len(ret)) if len(ret) > 0 else 0.
        recall = float(rel_union_ret) / float(len(rel)) if len(rel) > 0 else 0.
        f1_score = (2. * precision * recall)/(precision + recall) if precision + recall > 0 else 0
        
        return Result(precision, recall, f1_score)
        
#formats
    
class BaseTextResultFormat(object):
    
    def get_bow(self):# bag of words
        pass
    
    def get_word_seq(self):# sequence of words
        pass
    
class AlchemyFormat(BaseTextResultFormat):
    
    def __init__(self, result_string):
        self._strip = _remove_punctuation(result_string)

    def get_word_seq(self):
        split = re.split(r'[\s]+', self._strip)
        return [i for i in split if i != '' ]
    
    def get_bow(self):
        raise NotImplementedError
    
class PythonRedabilityFormat(AlchemyFormat):
    # basically the same as AlchemyFormat
    pass 
    
class CleanEvalFormat(BaseTextResultFormat):
    
    def __init__(self, cleaneval_string):
        # remove URL meta data
        self._strip = re.sub(r'URL:(.*)\n', '', cleaneval_string)
        # remove tag guidelines
        self._strip = re.sub(r'<(p|h|l)>', '', self._strip)
    
        self._strip = _remove_punctuation(self._strip)
        
    def get_word_seq(self):
        split = re.split(r'[\s]+', self._strip)
        return [i for i in split if i != '' ]
        
    def get_bow(self):
        bow = {}
        seq = self.get_word_seq()
        
        for i in seq:
            if i not in bow:
                bow[i] = 1
            else:
                bow[i] += 1
        
        return bow
        
        
    
        
    