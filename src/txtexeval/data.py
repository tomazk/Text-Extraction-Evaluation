import os
import urlparse
import codecs

import yaml

import settings
from .evaluation import CleanEvalFormat

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
    
    def __init__(self, dataset_name):
        self.dataset_name = dataset_name
        
        # load meta data
        meta_filepath = os.path.join(settings.PATH_LOCAL_DATA, 'datasets', dataset_name, 'meta.yaml')
        with open(meta_filepath, 'r') as f:
            self.meta_yaml = yaml.load(f.read())
    
    def __iter__(self):
        '''DataInstance generator'''
        for dict in self.meta_yaml:
            yield LocalDocument(self.dataset_name, **dict)
    

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
        
        
    def get_raw_html(self):
        file_path = os.path.join(settings.PATH_LOCAL_DATA,
                                 'datasets',
                                 self.dataset,
                                 'raw',
                                 self.raw_filename
                                 )
        with codecs.open(file_path,'r', encoding = self.raw_encoding, errors = 'ignore') as f:
            return f.read()
    
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
             
        
        