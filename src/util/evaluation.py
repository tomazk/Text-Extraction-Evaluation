import os
import re
import pickle
import string
import difflib
from collections import namedtuple
import settings

# module utils

def _remove_punctuation(s):
    exclude = set(string.punctuation)
    return ''.join( ch for ch in s if ch not in exclude )

# classes

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
            
    def appendResult(self, result):
        '''Append the result instance to the given extractor'''
        pass
    
    def printResults(self):
        '''Print results to stdout'''
        pass
    
    def plotResults(self):
        '''Plot results with matplotlib'''
        pass
            
class TextBasedResults(BaseEvalResults):
            
    def appendResult(self, result):
        if self._extractor:
            self.text_eval_results[self._extractor].append(result)
        
    def printResults(self):
        print 'results based on text based evaluation'
        for extractor_name, results_list in self.text_eval_results.iteritems():
            avg_precision = sum([r.precision for r in results_list]) / float(len(results_list)) 
            avg_recall = sum([r.recall for r in results_list]) / float(len(results_list))
            avg_f1 = sum([r.f1_score for r in results_list]) / float(len(results_list))
            print '----------------'
            print 'Ex. name: %s' % extractor_name
            print 'avg. precision: %f' % avg_precision 
            print 'avg. racall: %f' % avg_recall
            print 'avg. F1 score: %f' % avg_f1
    
    def plotResults(self):
        #TODO
        pass
    

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
        
        
    
        
    