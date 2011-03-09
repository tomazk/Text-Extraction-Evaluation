import json
import requests
import settings
import readability
from BeautifulSoup import BeautifulSoup


class BaseExtractor(object):
    '''Extractor base class
    
    Using a base class to ensure a common representation. 
    If an extractor returns only e.g. text based results it 
    should raise a NotImpelemntedError for the respective
    method'''
    
    
    def __init__(self, data_instance):
        self.data_instance = data_instance
        
    def extract_text(self):
        pass
    
    def extract_html(self):
        pass
    
class PythonReadabilityExtractor(BaseExtractor):
    '''Extractor based on python-readability 
    (https://github.com/gfxmonk/python-readability)'''
    
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
    
    def extract_text(self):
        
        html = self.data_instance.get_raw_html()
        
        request = requests.post(
            'http://access.alchemyapi.com/calls/html/HTMLGetText',
             data = {'apikey':settings.ALCHEMY_API_KEY,
                     'html': html,
                     'outputMode':'json'
                     }
             )
        if request.status_code != 200:
            raise RuntimeError('Something went wrong when accessing Alchemy API')
        
        #dump all meta-data in the response and return the extracted text
        return json.loads(request.content)['text']
    
    def extract_html(self):
        raise NotImplementedError('Alchemy API doesn\'t support html based extraction' )
        
    
    