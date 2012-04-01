import os
import urlparse
import codecs
import logging

import yaml

import settings
from .util import check_local_path, get_local_path
from .extractor import extractor_list, get_extractor_cls
from .extractor import  ExtractorError, ContentExtractorError

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
    def __init__(self, dataset_name, load_failed = None, skip_existing = None):     
        self.dataset = dataset_name   
        self._skip_existing = skip_existing
        
        # load meta data
        meta_filepath = get_local_path( dataset_name, 'meta.yaml')
        with open(meta_filepath, 'r') as f:
            self.meta_yaml = yaml.load(f.read())
            self._len = len(self.meta_yaml)
            
        if load_failed:
            self._failed_list = ExtractionSummary(self.dataset) \
                                .get_failed_ids(load_failed) 
        else:
            self._failed_list = None
            
    def __iter__(self):
        '''DataInstance generator'''
        for dict in self.meta_yaml:
            document = LocalDocument(self.dataset, **dict)
            
            # check if all conditions for yielding a document are set
            yield_ = False
            if self._skip_existing != None and \
            document.check_existing_clean(self._skip_existing):
                yield_ = False
            elif self._failed_list != None and \
            dict['id'] in self._failed_list:
                yield_ = True
                
            if yield_:
                yield document
            else: 
                logger.debug('skipping document %s', document.id)
                continue
            
    def __len__(self):
        return self._len
    

class BaseDocument(object):
    # same goes for document instances
    
    def get_raw_html(self):
        pass
    
    def get_url(self):
        pass

    def get_url_local(self):
        pass
    
    def get_clean(self):
        pass
    
class LocalDocument(BaseDocument):
    '''Evaluation data representation using local filesystem'''
    
    def __init__(self, dataset, **kwargs):
        self.dataset = dataset
        
        # instance attributes
        self.id = kwargs.pop('id')
        self.raw_filename = kwargs.pop('raw')
        self.clean_filename = kwargs.pop('clean')
        self.url = kwargs.pop('url')
        self.raw_encoding = kwargs.pop('raw_encoding')
        self.clean_encoding = kwargs.pop('clean_encoding')
        
    def get_raw_html(self):
        file_path = get_local_path(self.dataset,'raw',self.raw_filename)
        with codecs.open(file_path,'r', encoding = self.raw_encoding, errors = 'ignore') as f:
            return f.read()
    
    def get_url(self):
        if self.url: 
            return self.url
        else:
            tail = self.dataset + '/' + self.raw_filename
            return urlparse.urljoin(settings.PATH_REMOTE_DATA, tail)
        
    def get_url_local(self):
        # file:///home/tomaz/workspace/diploma/txt-ex-eval-data/datasets/cleaneval-final/raw/100.html
        return 'file://' + settings.PATH_LOCAL_DATA + '/datasets/' \
             + self.dataset + '/raw/' + self.raw_filename
        
    def get_clean(self):
        file_path = get_local_path(self.dataset,'clean',self.clean_filename)
        with open(file_path, 'r') as f:
            return f.read()
        
    def check_existing_clean(self, extractor_slug):
        ex_cls = get_extractor_cls(extractor_slug)
        return check_local_path(self.dataset,'result',extractor_slug,
                                '%s.%s' %(self.id, ex_cls.FORMAT))
        
        
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
                
        self.set_extractor(extractor_slug)
        
    def set_extractor(self, extractor_slug):
        if extractor_slug:
            self.extractor_slug = extractor_slug
            self._summary_structure[self.extractor_slug] = []
        else:
            self.extractor_slug = None
        
    def get_failed_ids(self, extractor_slug):
        if self.extractor_slug:
            raise DataError('extractor_slug set - list of fails was reinitialized')
        return [f['id'] for f in self._summary_structure[extractor_slug]]
        
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
        
class BaseResultStorage(object):
    
    def __init__(self, dataset_name, extractor_class):
        self.dataset =  dataset_name
        self.extractor_cls = extractor_class
        
    def push_result(self, document):
        pass
    
    def fetch_result(self, document): 
        pass
    
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
            self._summary.add_fail(document.id, err_msg)
        except ContentExtractorError as e:
            err_msg = 'Content extractor related error: %r' % e
            logger.warning(err_msg)
            self._summary.add_fail(document.id, err_msg)
        except ExtractorError as e:
            err_msg = 'Extractor related error: %r' % e
            logger.warning(err_msg)
            self._summary.add_fail(document.id, err_msg)
        except NotImplementedError:
            logger.debug('extraction method is not implemented - do nothing')
            pass
        except Exception as e:
            err_msg = 'Unknown error: %r' % e
            logger.warning(err_msg)
            self._summary.add_fail(document.id, err_msg)
        else:
            logger.debug('extracted content from %s', document.id)
            output_file = '%s.%s' % (document.id,self.extractor_cls.FORMAT)
            with open(os.path.join(self._extractor_result_dir, output_file), 'w') as out:
                out.write(result)
                
    def fetch_result(self, document):
        result_file = '%s.%s' % (document.id,self.extractor_cls.FORMAT)
        result_file_path = os.path.join(self._extractor_result_dir, result_file)
        if not os.path.exists(result_file_path):
            raise DataError('result file %s does not exist' % result_file)
        with open(result_file_path,'r') as f:
            return f.read()
        
    def dump_summary(self):
        logger.info(self._summary.short_summary())
        self._summary.serialize()