import os
import re
import urlparse
import codecs

import yaml

import settings
from .evaluation import CleanEvalFormat
from .util import check_local_dataset

class DataError(Exception):
    pass

def verify_local_dataset(init):
    def wrapper(self, dataset, *args, **kwargs):
        if not check_local_dataset(dataset):
            raise DataError('local dataset %s does not exist' % dataset)
        init(self, dataset, *args, **kwargs)
    return wrapper

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
    
    @verify_local_dataset
    def __init__(self, dataset_name):     
        self.dataset = dataset_name   
        # load meta data
        meta_filepath = os.path.join(settings.PATH_LOCAL_DATA, 'datasets', dataset_name, 'meta.yaml')
        with open(meta_filepath, 'r') as f:
            self.meta_yaml = yaml.load(f.read())
    
    def __iter__(self):
        '''DataInstance generator'''
        for dict in self.meta_yaml:
            yield LocalDocument(self.dataset, **dict)
    

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
        self.raw_encoding = kwargs.pop('raw_encoding')
        self.clean_encoding = kwargs.pop('clean_encoding')
        
        
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
        
class BaseResultStorage(object):
    
    def __init__(self, dataset_name, extractor_class):
        self.dataset =  dataset_name
        self.extractor_cls = extractor_class
        
    def push_result(self, document):
        pass
    
class LocalResultStorage(BaseResultStorage):
    
    @verify_local_dataset
    def __init__(self, dataset_name, extractor_class):
        super(LocalResultStorage, self).__init__(dataset_name, extractor_class)
        
        # with dataset name out of the way, we must now check the existance of
        # the result folder for the given extractor
        self._result_dir = os.path.join(
            settings.PATH_LOCAL_DATA,
            'datasets',
            self.dataset,
            'result')
        
        self._extractor_result_dir = os.path.join(
            self._result_dir,
            self.extractor_cls.SLUG)
        
        if not os.path.exists( self._extractor_result_dir ):
            os.mkdir(self._extractor_result_dir)
    
    def push_result(self, document):
        extractor = self.extractor_cls(document)
        result = extractor.extract()
        
        output_file = '%s.%s' % (document.raw_filename,self.extractor_cls.FORMAT)
        with open(os.path.join(self._extractor_result_dir, output_file), 'w') as out:
            out.write(result)
            
    @property        
    def log_path(self):
        return os.path.join(
            self._result_dir,
            '%s.log' % self.extractor_cls.SLUG
        )