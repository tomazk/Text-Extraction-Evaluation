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
    SLUG = ''# unique slug name ([a-z_]+)
    
    def __init__(self, data_instance):
        self.data_instance = data_instance
        
    def extract(self):
        '''Returns unformatted extractor resposne'''
        pass
        
    def extract_text(self):
        '''Returns the cleaned text'''
        pass
    
    def extract_html(self):
        '''Returns the cleaned html'''
        pass
    
class BoilerpipeDefaultExtractor(BaseExtractor):
    '''Boilerpipe default extractor '''
    
    NAME = 'Boilerpipe DEF'
    SLUG = 'boilerpipe_def'
    
    __extractor_type = 'default'
    
    def extract(self):
        html = self.data_instance.get_raw_html()
        req = Request(
            settings.BOILERPIPE_API_ENDPOINT,
            data = {
                "extractorType":self.__extractor_type,
                "rawHtml": html.encode(self.data_instance.raw_encoding) 
            },
            headers = {'Content-Type':'application/x-www-form-urlencoded'}
        )
        res = req.post()

        if not res.success():
            raise ExtractorError(res.err_msg)        
        return res.content
        
    
    def extract_text(self):
        response_content = json.loads(self.extract())
        if response_content['status'] == "ERROR":
            raise ExtractorError(response_content['errorMsg'].encode('utf-8'))
        
        return response_content['result']
    
    def extract_html(self):
        raise NotImplementedError
    
class BoilerpipeArticleExtractor(BoilerpipeDefaultExtractor):
    '''Boilerpipe article extractor'''
    
    NAME = 'Boilerpipe ART'
    SLUG = 'boilerpipe_art'
    
    __extractor_type = 'article'
    
    
class GooseExtractor(BaseExtractor):
    '''Goose project extractor'''
    
    NAME = 'Goose'
    SLUG = 'goose'
    
    def extract(self):
        html = self.data_instance.get_raw_html()
        req = Request(
            settings.GOOSE_API_ENDPOINT,
            data = dict(rawHtml = html),
            headers = {'Content-Type':'application/x-www-form-urlencoded'}
        )
        res = req.post()

        if not res.success():
            raise ExtractorError(res.err_msg)
        return res.content
    
    def extract_text(self):
        
        response_content = json.loads(self.extract())
        if response_content['status'] == "ERROR":
            raise ExtractorError(response_content['errorMsg'].encode('utf-8'))
        
        return response_content['result']
    
    def extract_html(self):
        raise NotImplementedError
    
class MSSExtractor(BaseExtractor):
    '''MSS implementation by Jeffrey Pasternack'''
    
    NAME = 'MSS'
    SLUG = 'mss'
    
    def extract(self):
        html = self.data_instance.get_raw_html()
        req = Request(
            dict(settings.MSS_URL)['text'],
            #this implementation requires utf-8 encoded input
            data = html.encode('utf-8'),
            headers= {'Content-Type': 'text/plain;charset=UTF-8'}
        )
        res = req.post()
        
        if not res.success():
            raise ExtractorError(res.err_msg)
        return res.content
        
    def extract_text(self):
        soup = BeautifulSoup(self.extract_html().encode('utf-8'), fromEncoding = 'utf-8')
        return ' '.join([tag.text for tag in soup.findAll(recursive=True)])
    
    def extract_html(self):
        return unicode(self.extract(), encoding = 'utf-8')
    
class PythonReadabilityExtractor(BaseExtractor):
    '''Extractor based on python-readability 
    (https://github.com/gfxmonk/python-readability)'''
    
    NAME = 'Python Readability'
    SLUG = 'python_read'
    
    def extract(self):
        html = self.data_instance.get_raw_html()
        doc = readability.Document(html)
        return doc.summary()
        
    def extract_text(self):
        soup = BeautifulSoup(self.extract())
        return ' '.join([tag.text for tag in soup.findAll(recursive=True)])
    
    def extract_html(self):
        return self.extract()

class AlchemyExtractor(BaseExtractor):
    '''Alchemy API extractor'''
    
    NAME = 'Alchemy API'
    NAME = 'alchemy'
    
    def extract(self):
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
        
        self._response_content = json.loads(res.content, encoding = 'utf8')
        if self._response_content['status'] == 'ERROR':
            raise ExtractorError(self._response_content['statusInfo'].encode('utf8'))
        return res.content
        
    def extract_text(self):
        self.extract()
        # dump all meta-data in the response and return the extracted text
        # Alchemy API ensures utf-8 encoding for every response 
        return self._response_content['text']
    
    def extract_html(self):
        raise NotImplementedError
        
    
    