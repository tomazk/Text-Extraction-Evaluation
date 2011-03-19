import json

import readability
from BeautifulSoup import BeautifulSoup

import settings
from .util import Request

class ExtractorError(Exception):
    pass

class BaseExtractor(object):
    '''Extractor base class
    
    Using a base class to ensure a common representation. 
    If an extractor returns only e.g. text based results it 
    should raise a NotImpelemntedError for the respective
    method'''
    
    NAME = ''# unique name 
    
    def __init__(self, data_instance):
        self.data_instance = data_instance
        
    def extract_text(self):
        pass
    
    def extract_html(self):
        pass
    
class PythonReadabilityExtractor(BaseExtractor):
    '''Extractor based on python-readability 
    (https://github.com/gfxmonk/python-readability)'''
    
    NAME = 'Python Readability'
    
    def _get_summary(self):
        html = self.data_instance.get_raw_html()
        
        doc = readability.Document(html)
        return doc.summary()
        
    def extract_text(self):
        soup = BeautifulSoup(self._get_summary())
        return ' '.join([tag.text for tag in soup.findAll(recursive=True)])
    
    def extract_html(self):
        return self._get_summary()

class AlchemyExtractor(BaseExtractor):
    '''Alchemy API extractor'''
    
    NAME = 'Alchemy API'
    
    def extract_text(self):
        html = self.data_instance.get_raw_html()
        
        req = Request(
            'http://access.alchemyapi.com/calls/html/HTMLGetText',
            data = {'apikey':settings.ALCHEMY_API_KEY,
                    'html': html.encode(self.data_instance.raw_encoding),
                    'outputMode':'json'
            } 
            
        )
        res = req.post()
        
        if not res.success():
            raise ExtractorError(res.err_msg)
        
        # dump all meta-data in the response and return the extracted text
        # Alchemy API ensures utf-8 encoding for every response 
        return json.loads(res.content, encoding = 'utf8')['text']
    
    def extract_html(self):
        raise NotImplementedError
        
    
    