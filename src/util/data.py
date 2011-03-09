import urlparse
import os
import yaml

import settings
from util.evaluation import CleanEvalFormat

class BaseDatasetLoader(object):
    # if you want a loader with a different backend 
    # (e.g. database)just extend this class and implement
    # get_dataset method which returns a some sort of
    # BaseDocumentInstance  generator
    
    def get_dataset(self):
        pass

class LocalDatasetLoader(BaseDatasetLoader):
    '''Data instance loading utility using local filesystem'''
    
    def __init__(self):
        meta_filepath = os.path.join(settings.PATH_LOCAL_DATA, 'meta.yaml')
        self.meta_yaml = yaml.load(open(meta_filepath,'r').read())
    
    def get_dataset(self, dataset_name):
        '''DataInstance generator'''
        for dict in self.meta_yaml[dataset_name]:
            yield LocalDocumentInstance(dataset_name, **dict)
    

class BaseDocumentInstance(object):
    # same goes for document instances
    
    def get_raw_html(self):
        pass
    
    def get_url(self):
        pass
    
    def get_result(self):
        # must return an instance of BaseResultFormat
        pass
    

class LocalDocumentInstance(BaseDocumentInstance):
    '''Evaluation data representation using local filesystem'''
    
    def __init__(self, dataset, **kwargs):
        self.dataset = dataset
        self.raw_filename = kwargs.pop('raw')
        self.clean_filename = kwargs.pop('clean')
        self.url = kwargs.pop('url')
        
        
    def get_raw_html(self):
        file_path = os.path.join(settings.PATH_LOCAL_DATA,
                                 self.dataset,
                                 'raw',
                                 self.raw_filename
                                 )
        return open(file_path,'r').read()
    
    def get_url(self):
        if self.url: return self.url
        else:
            tail = self.dataset + '/raw/' + self.raw_filename
            return urlparse.urljoin(settings.PATH_REMOTE_DATA, tail)
        
    def get_result(self):
        file_path = os.path.join(settings.PATH_LOCAL_DATA,
                                 self.dataset,
                                 'clean',
                                 self.clean_filename
                                 )
        s = open(file_path, 'r').read()
        return CleanEvalFormat(s)
             
        
        