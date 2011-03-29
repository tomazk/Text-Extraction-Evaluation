import os
import re
import urlparse
import codecs

import yaml

import settings
from .evaluation import CleanEvalFormat

# dataset loaders

class BaseDatasetLoader(object):
    '''
    If you want a loader with a different backend (e.g. database)just extend 
    this class and implement __iter__ method which returns an iterator over 
    document instances
    '''
    
    def __iter__(self):
        raise NotImplementedError

class LocalDatasetLoader(BaseDatasetLoader):
    '''Dataset loader using local filesystem'''
    
    def __init__(self, dataset_name, raw_filter = None):
        self.dataset_name = dataset_name
        self.raw_filter = raw_filter # raw filter function
        
        # load meta data
        meta_filepath = os.path.join(settings.PATH_LOCAL_DATA, 'datasets', dataset_name, 'meta.yaml')
        with open(meta_filepath, 'r') as f:
            self.meta_yaml = yaml.load(f.read())
    
    def __iter__(self):
        '''DataInstance generator'''
        for dict in self.meta_yaml:
            yield LocalDocument(self.dataset_name, raw_filter = self.raw_filter, **dict)

# documents

class BaseDocument(object):
    # same goes for document instances
    
    def get_raw_html(self):
        pass
    
    def get_url(self):
        pass
    
    def get_result(self):
        # must return an instance of BaseResultFormat
        pass
    

class LocalDocument(BaseDocument):
    '''Evaluation data representation using local filesystem'''
    
    def __init__(self, dataset, **kwargs):
        self.dataset = dataset
        
        # instance attributes
        self.raw_filename = kwargs.pop('raw')
        self.clean_filename = kwargs.pop('clean')
        self.url = kwargs.pop('url')
        
        # choosing utf-8 if no encoding is provided is based on the observation 
        # that only ascii chars are used in such files e.g. CleanEval 
        self.raw_encoding = kwargs.pop('raw_encoding') or 'utf-8'
        self.clean_encoding = kwargs.pop('clean_encoding') or 'utf-8'
        
        # optional raw html filter function
        try:
            self._raw_filter = kwargs.pop('raw_filter')
        except KeyError:
            self._raw_filter = None
        
    
    
    def get_raw_html(self):
        file_path = os.path.join(settings.PATH_LOCAL_DATA,
                                 'datasets',
                                 self.dataset,
                                 'raw',
                                 self.raw_filename
                                 )
        with codecs.open(file_path,'r', encoding = self.raw_encoding, errors = 'ignore') as f:
            # if we provide a raw filter we return the filtered content of the file
            return self._raw_filter(f.read()) if self._raw_filter else f.read()
    
    def get_url(self):
        if self.url: return self.url
        else:
            tail = self.dataset + '/raw/' + self.raw_filename
            return urlparse.urljoin(settings.PATH_REMOTE_DATA, tail)
        
    def get_result(self):
        file_path = os.path.join(settings.PATH_LOCAL_DATA,
                                 'datasets',
                                 self.dataset,
                                 'clean',
                                 self.clean_filename
                                 )
        with codecs.open(file_path, 'r', encoding =  self.clean_encoding, errors = 'ignore') as f:
            return CleanEvalFormat(f.read())

# dataset specific filters

def cleaneval_raw_html_filter(raw_html):
    '''
    Cleaneval has a <text> tag that wraps the whole html structure. This 
    function removes it with a pessimistic regular expression because we don't 
    want to mess everything up with a parser.
    '''
    # remove <text> at the beginning
    regex_beg = re.compile(r'^(\s*)<(\s*)text((\s*)(id|title|encoding)(\s*)=(\s*)"(.*)")*>', re.UNICODE)
    notext = regex_beg.sub('', raw_html)
    # remove the closing part of the tag
    regex_end = re.compile(r'<(\s*)/(\s*)text(\s*)>$', re.UNICODE)
    notext = regex_end.sub('',notext)
    
    return notext
