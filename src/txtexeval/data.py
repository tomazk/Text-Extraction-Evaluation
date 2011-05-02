import os
import urlparse
import codecs
import logging

import yaml

import settings
from .evaluation import CleanEvalFormat
from .util import check_local_path, get_local_path
from .extractor import extractor_list, ExtractorError, ContentExtractorError

logger = logging.getLogger(__name__)

class DataError(Exception):
    pass

def verify_local_dataset(init):
    def wrapper(self, dataset, *args, **kwargs):
        if not check_local_path(dataset):
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
        meta_filepath = get_local_path( dataset_name, 'meta.yaml')
        with open(meta_filepath, 'r') as f:
            self.meta_yaml = yaml.load(f.read())
            self._len = len(self.meta_yaml)
    
    def __iter__(self):
        '''DataInstance generator'''
        for dict in self.meta_yaml:
            yield LocalDocument(self.dataset, **dict)
            
    def __len__(self):
        self._len
    

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
        file_path = get_local_path(
                                 self.dataset,
                                 'raw',
                                 self.raw_filename
                                 )
        with codecs.open(file_path,'r', encoding = self.raw_encoding, errors = 'ignore') as f:
            return f.read()
    
    def get_url(self):
        if self.url: 
            return self.url
        else:
            tail = self.dataset + '/' + self.raw_filename
            return urlparse.urljoin(settings.PATH_REMOTE_DATA, tail)
        
    def get_result(self):
        file_path = get_local_path(
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
    
    
class ExtractionSummary(object):
    
    @verify_local_dataset
    def __init__(self, dataset_name, extractor_slug = None):
        self._summary_path = get_local_path(dataset_name,'result', 'summary.yaml')
        
        if os.path.exists(self._summary_path):
            with open(self._summary_path,'r') as f:
                self._summary_structure = yaml.load(f.read())
        else:
            self._summary_structure = {} 
            for e in extractor_list:
                self._summary_structure[e.SLUG] = []
                
        if extractor_slug:
            self.set_extractor(extractor_slug)
        
    def set_extractor(self, extractor_slug):
        self.extractor_slug = extractor_slug
        self._summary_structure[self.extractor_slug] = []
        
    def add_fail(self, id, reason = None):
        if self.extractor_slug == None:
            raise DataError('extractor not set')
        
        self._summary_structure[self.extractor_slug].append({
            'id': id,
            'reason': reason
        })
        
    def serialize(self):
        with open(self._summary_path, 'w') as out:
            out.write(yaml.dump(self._summary_structure, default_flow_style=False ))
    
    def short_summary(self, extractor_slug = None):
        if extractor_slug:
            return 'extraction summary: %i failed' \
               % len(self._summary_structure[extractor_slug])
        elif self.extractor_slug: 
            return 'extraction summary: %i failed' \
               % len(self._summary_structure[self.extractor_slug])
        else:
            raise DataError('extractor not set')
        
class LocalResultStorage(BaseResultStorage):
    
    @verify_local_dataset
    def __init__(self, dataset_name, extractor_class):
        super(LocalResultStorage, self).__init__(dataset_name, extractor_class)
        
        # with dataset name out of the way, we must now check the existance of
        # the result folder for the given extractor
        self._result_dir = get_local_path( self.dataset,'result')
        
        self._extractor_result_dir = os.path.join(
            self._result_dir,
            self.extractor_cls.SLUG)
        
        if not os.path.exists( self._extractor_result_dir ):
            os.mkdir(self._extractor_result_dir)
            
        # create an object to be serialized into a .yaml file
        # we need this to store a summary of the extraction process for the 
        # whole dataset
        self._summary = ExtractionSummary(self.dataset, self.extractor_cls.SLUG)
        
    def push_result(self, document):
        extractor = self.extractor_cls(document)
        try:
            result = extractor.extract()
        except DataError as e:
            err_msg = 'Data related error: %r' % e
            logger.warning(err_msg)
            self._summary.add_fail(document.raw_filename, err_msg)
        except ContentExtractorError as e:
            err_msg = 'Content extractor related error: %r' % e
            logger.warning(err_msg)
            self._summary.add_fail(document.raw_filename, err_msg)
        except ExtractorError as e:
            err_msg = 'Extractor related error: %r' % e
            logger.warning(err_msg)
            self._summary.add_fail(document.raw_filename, err_msg)
        except Exception as e:
            err_msg = 'Unknown error: %r' % e
            logger.warning(err_msg)
            self._summary.add_fail(document.raw_filename, err_msg)
        else:
            output_file = '%s.%s' % (document.raw_filename,self.extractor_cls.FORMAT)
            with open(os.path.join(self._extractor_result_dir, output_file), 'w') as out:
                out.write(result)
            
    @property        
    def log_path(self):
        return os.path.join(
            self._result_dir,
            '%s.log' % self.extractor_cls.SLUG
        )
        
    def dump_summary(self):
        logger.info(self._summary.short_summary())
        self._summary.serialize()