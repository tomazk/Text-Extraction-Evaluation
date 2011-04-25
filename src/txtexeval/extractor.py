import readability

import settings
from .util import Request

class ExtractorError(Exception):
    pass

def return_content(extract):
    '''
    DRY decorator that wraps the extract method. We check for response
    success and raise the appropriate error or return the content.
    '''
    def wrapper(self):
        response = extract(self)
        if not response.success():
            raise ExtractorError(response.err_msg)        
        return response.content
    return wrapper

class BaseExtractor(object):
    '''Extractor base class
    
    Using a base class to ensure a common representation. 
    If an extractor returns only e.g. text based results it 
    should raise a NotImpelemntedError for the respective
    method'''
    
    NAME = ''# unique name
    SLUG = ''# unique slug name ([a-z_]+)
    FORMAT = ''# txt|html|json|xml
    
    def __init__(self, data_instance):
        self.data_instance = data_instance
        
    def extract(self):
        '''Returns unformatted extractor resposne'''
        pass
    
class BoilerpipeDefaultExtractor(BaseExtractor):
    '''Boilerpipe default extractor '''
    
    NAME = 'Boilerpipe DEF'
    SLUG = 'boilerpipe_def'
    FORMAT = 'json'
    
    __extractor_type = 'default'
    
    @return_content
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
        return req.post()
        
    
class BoilerpipeArticleExtractor(BoilerpipeDefaultExtractor):
    '''Boilerpipe article extractor'''
    
    NAME = 'Boilerpipe ART'
    SLUG = 'boilerpipe_art'
    FORMAT = 'json'
    
    __extractor_type = 'article'
    
    
class GooseExtractor(BaseExtractor):
    '''Goose project extractor'''
    
    NAME = 'Goose'
    SLUG = 'goose'
    FORMAT = 'json'
    
    @return_content
    def extract(self):
        html = self.data_instance.get_raw_html()
        req = Request(
            settings.GOOSE_API_ENDPOINT,
            data = dict(rawHtml = html.encode(self.data_instance.raw_encoding)),
            headers = {'Content-Type':'application/x-www-form-urlencoded'}
        )
        return req.post()

    
class MSSExtractor(BaseExtractor):
    '''MSS implementation by Jeffrey Pasternack'''
    
    NAME = 'MSS'
    SLUG = 'mss'
    FORMAT = 'html'
    
    @return_content
    def extract(self):
        html = self.data_instance.get_raw_html()
        req = Request(
            dict(settings.MSS_URL)['text'],
            #this implementation requires utf-8 encoded input
            data = html.encode('utf-8'),
            headers= {'Content-Type': 'text/plain;charset=UTF-8'}
        )
        return req.post()
    
class PythonReadabilityExtractor(BaseExtractor):
    '''Extractor based on python-readability 
    (https://github.com/gfxmonk/python-readability)'''
    
    NAME = 'Python Readability'
    SLUG = 'python_read'
    FORMAT = 'html'
    
    def extract(self):
        html = self.data_instance.get_raw_html()
        doc = readability.Document(html)
        # FIXME
        return doc.summary().encode('ascii','ignore')

class AlchemyExtractor(BaseExtractor):
    '''Alchemy API extractor'''
    
    NAME = 'Alchemy API'
    SLUG = 'alchemy'
    FORMAT = 'json'
    
    @return_content
    def extract(self):
        html = self.data_instance.get_raw_html()
        req = Request(
            'http://access.alchemyapi.com/calls/html/HTMLGetText',
            data = {'apikey':settings.ALCHEMY_API_KEY,
                    'html': html.encode(self.data_instance.raw_encoding),
                    'outputMode':'json'
            } 
            
        )
        return req.post()
        
# list of all extractor classes         
extractor_list = (
    BoilerpipeArticleExtractor,
    BoilerpipeDefaultExtractor,
    GooseExtractor,
    MSSExtractor,
    PythonReadabilityExtractor,
    AlchemyExtractor,
)

def get_extractor_cls(extractor_slug):
    '''Return the extractor class given a slug'''
    for e in extractor_list:
        if e.SLUG == extractor_slug: 
            return e
    