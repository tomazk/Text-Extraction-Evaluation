import os
import re
import pickle
import string
import difflib
import math
from collections import namedtuple

from BeautifulSoup import BeautifulSoup

import settings

# module utils

re_CONTROL = re.compile("[\x00-\x1F]+")
re_WS = re.compile("\s+")
re_NONASCII = re.compile("[\x80-\xFF]+")

def _tokenize_text(dirty_text):
    '''Tokenize dirty text into a normalized list of words'''
    # remove punctuation and replace with whitespace
    table = string.maketrans(string.punctuation, ' '*len(string.punctuation))
    dirty_text =  dirty_text.translate(table)
    # remove any control char
    dirty_text = re_CONTROL.sub(' ', dirty_text)
    # remove any non ascii char to mitigate the troubles of broken encodings
    dirty_text = re_NONASCII.sub('', dirty_text)
    # normalize to lowercase
    dirty_text = dirty_text.lower()
    # remove empty tokens
    return filter(lambda w: w != '', re_WS.split(dirty_text))

def _bow(word_tokens):
    '''Returns bag of words dictionary from a list of word tokens'''
    bow = {}
    for i in word_tokens:
        if i not in bow:
            bow[i] = 1
        else:
            bow[i] += 1
    return bow
    
def _html_to_text(html, encoding):
    '''Get all the text from a given html string'''
    soup = BeautifulSoup(html, fromEncoding = encoding)
    tags = soup.findAll(text = True)
    useful = lambda e: e.parent.name not in ('style', 'script', 'head', 'title')
    tags = filter(useful, tags)
    return ' '.join(map(lambda e: e.encode(encoding), tags))
    
# results

Result = namedtuple('Result', 'precision recall f1_score')# result instance

class BaseEvalResults(object):
    '''Base results container'''
    
    __pickle_filepath = os.path.join(settings.PATH_LOCAL_DATA,'results-cache','results.pickle')
    
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
    
class ResultFormat(object):
    
    def get_bow(self):# bag of words
        pass
    
    def get_word_seq(self):# sequence of words
        pass
    
class TextResultFormat(ResultFormat):
    '''Basic format for dirty text'''
    
    def __init__(self, dirty_text):
        self._text = dirty_text

    def get_word_seq(self):
        return _tokenize_text(self._text)
    
    def get_bow(self):
        return _bow(_tokenize_text(self._text))
    
class CleanEvalFormat(ResultFormat):
    '''Format specific for cleaneval dataset'''
    
    re_URL = re.compile(r'^(\s+)URL:(.*)\n')
    re_TAG = re.compile(r'^(\s+)<(p|h|l)>', re.IGNORECASE | re.MULTILINE)
    
    def __init__(self, cleaneval_string):
        # remove URL meta data
        self._text = self.re_URL.sub( '', cleaneval_string)
        # remove tag guidelines
        self._text = self.re_TAG.sub('', self._text)
        
    def get_word_seq(self):
        return _tokenize_text(self._text)
        
    def get_bow(self):
        return _bow(_tokenize_text(self._text))
        
class GoogleNewsFormat(ResultFormat):
    '''
    Format specific for google news dataset
    
    From README.txt distributed with google news dataset:
    The human-assessed documents contain annotations in the form of <SPAN> tags
    with specific CSS classes that indicate the type of content:
    x-nc-sel0    Not content
    x-nc-sel1    Headline
    x-nc-sel2    Full text
    x-nc-sel3    Supplemental
    x-nc-sel4    Related content
    x-nc-sel5    Comments
    '''
    
    re_CLASS = re.compile('x-nc-sel[1|2]')
    
    def __init__(self, gnews_string, encoding):
        soup = BeautifulSoup(gnews_string, fromEncoding = encoding)
        
        # The trouble of google news dataset is that it sometimes nests 
        # the annotated span tags. That's why we first have to find any 
        # annotated children and remove them from the content_tags list.
        redundant_tags = []
        content_tags = soup.findAll('span',attrs = {'class' : self.re_CLASS })
        for ct in content_tags:
            red = ct.findAll('span',attrs = {'class' : self.re_CLASS })
            redundant_tags.extend(red)
        self._content_tags = filter(lambda tag: tag not in redundant_tags, content_tags)
        # Next we find all the text and concatenate it into one single string
        content_strings = []
        for ct in self._content_tags:
            content_strings.extend(ct.findAll(text=True))
        self._content_string = ' '.join(map(lambda e: e.encode(encoding), content_strings))
        
    def get_word_seq(self):
        return _tokenize_text(self._content_string)
        
    def get_bow(self):
        return _bow(_tokenize_text(self._content_string))
        
    