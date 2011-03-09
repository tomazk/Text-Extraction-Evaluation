import re
import string
import difflib
from collections import namedtuple

# module utils

def _remove_punctuation(s):
    exclude = set(string.punctuation)
    return ''.join( ch for ch in s if ch not in exclude )

# classes

Result = namedtuple('Result', 'precision recall f1_score')

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
        
        precision = float(rel_union_ret) / float(len(ret)) if len(ret) > 0 else -1.
        recall = float(rel_union_ret) / float(len(rel)) if len(rel) > 0 else -1.
        f1_score = (2. * precision * recall)/(precision + recall) if precision != -1. and recall != -1. else -1
        
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
        
        
    
        
    