import os
import re
import pickle
import string
import difflib
import math

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
    
# results

class Result(object):
    
    def __init__(self, precision, recall, f1_score, id = None):
        # validate result 
        if math.isinf(precision) and not math.isinf(recall):
            assert recall == 0
            assert math.isnan(f1_score)
        elif not math.isinf(precision) and math.isinf(recall):
            assert precision == 0
            assert math.isnan(f1_score)
        elif math.isinf(precision) and math.isinf(recall):
            assert math.isnan(f1_score)
        elif precision == recall == 0:
            assert math.isinf(f1_score)
        elif not math.isinf(precision) and not math.isinf(recall):
            assert 0 < precision <= 1
            assert 0 < recall <= 1
            assert 0 < f1_score <= 1
        
        self.precision = precision
        self.recall = recall
        self.f1_score = f1_score
        self.id = id
    
    @property
    def retrieved_empty(self):
        return math.isinf(self.precision) and self.recall == 0
    
    @property
    def relevant_empty(self):
        return math.isinf(self.recall) and self.precision == 0
    
    @property
    def relevant_retrieved_empty(self):
        return math.isinf(self.precision) and math.isinf(self.recall)
    
    @property
    def missmatch(self):
        return self.precision == self.recall == 0
    
    @property
    def succ(self):
        return 0 < self.f1_score <= 1
        
class ResultsContents(object):
    
    def __init__(self,succ,rel_empty,rel_ret_empty,ret_empty,missmatch,dataset_len):
        assert dataset_len >= succ+rel_empty+rel_ret_empty+ret_empty+missmatch
        
        self.succ = succ
        self.rel_empty = rel_empty
        self.rel_ret_empty = rel_ret_empty
        self.ret_empty = ret_empty
        self.missmatch = missmatch
         
        self.fail =  dataset_len-(succ+rel_empty+rel_ret_empty+ret_empty+missmatch)
        
class TextBasedResults(object):
            
    __pickle_path = os.path.join(settings.PATH_LOCAL_DATA,'results-cache')
    __internal_state = {} # Borg design pattern
    
    def __init__(self, extractor = None):
        self.__dict__ = self.__internal_state
        
        # ensure the presence of attributes
        if not 'text_eval_results' in self.__dict__: 
            self.text_eval_results = {}
        if not 'dataset_len' in self.__dict__:
            self.dataset_len = 0
        
        # optional
        if extractor and (not (extractor in self.text_eval_results)):
            self.text_eval_results[extractor] = []
        self._extractor = extractor

    def save(self, dataset_name):
        '''Pickle the internal state'''
        with open(os.path.join(self.__pickle_path,'%s.pickle' % dataset_name),'wb') as f:
            pickle.dump( self.__internal_state ,f)
    
    def load(self, dataset_name):
        '''Unpickle the internal state'''
        with open(os.path.join(self.__pickle_path,'%s.pickle' % dataset_name),'rb') as f:
            self.__internal_state = pickle.load(f)
            self.__dict__ = self.__internal_state
    
    def add_result(self, result):        
        self.text_eval_results[self._extractor].append(result)
        
    def filtered_results(self, extractor):
        result_filter = lambda r: r.succ
        return filter(result_filter, self.text_eval_results[extractor])
    
    def results_contents(self, extractor):
        results = self.text_eval_results[extractor]
        
        succ = len(self.filtered_results(extractor))
        rel_empty     = len(filter(lambda r: r.relevant_empty, results))
        ret_empty     = len(filter(lambda r: r.retrieved_empty, results))
        rel_ret_empty = len(filter(lambda r: r.relevant_retrieved_empty, results))
        missmatch     = len(filter(lambda r: r.missmatch, results))
    
        return ResultsContents(succ, rel_empty, rel_ret_empty, ret_empty,
                                missmatch, self.dataset_len)
    
    def _statistics(self, extractor, stat_typ): # DRY helper
        results_list = [getattr(r, stat_typ) for r in  self.filtered_results(extractor)]
        # average
        avg = sum(results_list) / float(len(results_list))
        # std deviation
        stddev =  sum([(r - avg)**2. for r in results_list]) / float(len(results_list))
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
        for extractor in self.text_eval_results.iterkeys():
            print '----------------'
            print 'Ex. name:       %s' % extractor
            print 'avg. precision: %f   stddev: %f' \
             % self.precision_statistics(extractor) 
            print 'avg. recall:    %f   stddev: %f' \
             % self.recall_statistics(extractor) 
            print 'avg. F1 score:  %f   stddev: %f' \
             % self.f1score_statistics(extractor) 
             
            rcontents = self.results_contents(extractor) 
            print 'relevant  empty:   %d' % rcontents.rel_empty
            print 'retrieved empty:   %d' % rcontents.ret_empty
            print 'rel intersect ret: %d' % rcontents.rel_ret_empty
            print 'success:           %d' % rcontents.succ
            print 'missmatch:         %d' % rcontents.missmatch
            print 'fail:              %d' % rcontents.fail
            print 'dataset_len=%d' % self.dataset_len
                                             
# evaluators    

class BaseEvaluator():
    '''Outline for evaluators'''
    
    def __init__(self, retrieved, relevant, id = None):
        self.retrieved = retrieved
        self.relevant = relevant
        self.id = id
    
    def get_eval_results(self):
        # return instance of Result
        pass
    
class TextOnlyEvaluator(BaseEvaluator):
    
    def get_eval_results(self):
        
        s = difflib.SequenceMatcher()
        rel = self.relevant.get_word_seq()
        ret = self.retrieved.get_word_seq()
        
        s.set_seqs(rel, ret)
        matches = s.get_matching_blocks()[:-1]
        
        rel_union_ret = sum(i.size for i in matches) if len(matches) > 0 else 0
        
        precision = float(rel_union_ret) / float(len(ret)) \
                    if len(ret) > 0 else float('inf')
        recall = float(rel_union_ret) / float(len(rel)) \
                    if len(rel) > 0 else float('inf')
                    
        # nan when prec or recall are inf 
        f1_score = (2. * precision * recall)/(precision + recall) \
                    if precision + recall > 0 else float('inf')
        
        return Result(precision, recall, f1_score, self.id)
        
#formats
    
class BaseResultFormat(object):
    
    def get_word_seq(self):# sequence of words
        pass
    
    def get_bow(self):# bag of words
        pass
    
class TextResultFormat(BaseResultFormat):
    '''Basic format for dirty text'''
    
    def __init__(self, dirty_text):
        self._text = dirty_text

    def get_word_seq(self):
        return _tokenize_text(self._text)
    
    def get_bow(self):
        return _bow(_tokenize_text(self._text))
    
class CleanEvalFormat(BaseResultFormat):
    '''Format specific for cleaneval dataset'''
    
    re_URL = re.compile(r'^(\s*)URL:(.*)$', re.IGNORECASE | re.MULTILINE)
    re_TAG = re.compile(r'^(\s*)<(p|h|l)>', re.IGNORECASE | re.MULTILINE)
    
    @staticmethod
    def from_document(document):
        return CleanEvalFormat(document.get_clean())
    
    def __init__(self, cleaneval_string):
        # remove URL meta data
        self._text = self.re_URL.sub('', cleaneval_string)
        # remove tag guidelines
        self._text = self.re_TAG.sub('', self._text)
        
    def get_word_seq(self):
        return _tokenize_text(self._text)
        
    def get_bow(self):
        return _bow(_tokenize_text(self._text))
        
class GoogleNewsFormat(BaseResultFormat):
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
    
    @staticmethod
    def from_document(document):
        return GoogleNewsFormat(document.get_clean(), document.clean_encoding)
    
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
        self._content_string = ' '.join(map(lambda e: e.encode(encoding,'ignore'), content_strings))
        
    def get_word_seq(self):
        return _tokenize_text(self._content_string)
        
    def get_bow(self):
        return _bow(_tokenize_text(self._content_string))
    
# formats in this mapping should have a from_document static method implemented
dataset_format_map = (
    ('cleaneval', CleanEvalFormat),
    ('gnews', GoogleNewsFormat),
)

def from_document_factory(document, slug):
    '''
    Factory function that returns an instance of a format class listed in the
    dataset format map.
    '''
    map = dict(dataset_format_map)
    cls = map[slug]
    return cls.from_document(document)