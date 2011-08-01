import urllib
import json

import readability
import justext
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

import settings
from .util import Request, html_to_text
from .util.zemanta.client import ClientManager
from .evaluation import TextResultFormat, CleanEvalFormat

class ExtractorError(Exception):
    '''Extractor failed on the network layer'''
    pass

class ContentExtractorError(ExtractorError):
    '''
    Raised when the error is included in the content (e.g. json formatted 
    response has a status field) fetched by the extractor
    '''
    pass

def return_content(extract):
    '''
    DRY decorator that wraps the extract method. We check for response
    success and raise the appropriate error or return the content.
    '''
    def wrapper(self):
        # fetch the response
        response = extract(self)
        # check for any network related errors
        if not response.success():
            raise ExtractorError(response.err_msg) 
        return response.content
    return wrapper

def check_content_status(extract):
    '''
    DRY decorator that mitigates the trouble of inserting boilerplate code 
    inside the extract method for invoking the private method _content_status.
    WhateverExtractor._content_status is used to check for errors returned in
    the response content itself.
    '''
    def wrapper(self):
        self._content = extract(self)
        self._content_status()
        return self._content
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
    
    @classmethod
    def formatted_result(cls, result_string):
        pass
    
    
class _ContentCheckMin(object):
    
    def _content_status(self):
        js = json.loads(self._content)
        if js['status'] == "ERROR":
            raise ContentExtractorError(js['errorMsg'].encode('utf-8','ignore'))
        
class _FormattedResultMin(object):
    
    @classmethod
    def formatted_result(cls, result_string):
        js = json.loads(result_string, encoding = 'utf8')
        return TextResultFormat(js['result'].encode('utf8','ignore'))
        
class BoilerpipeDefaultExtractor(_FormattedResultMin,_ContentCheckMin,BaseExtractor):
    '''Boilerpipe default extractor '''
    
    NAME = 'Boilerpipe DEF'
    SLUG = 'boilerpipe_def'
    FORMAT = 'json'
    
    _extractor_type = 'default'
    
    @return_content
    def extract(self):
        html = self.data_instance.get_raw_html()
        req = Request(
            settings.BOILERPIPE_API_ENDPOINT,
            data = {
                "extractorType":self._extractor_type,
                "rawHtml": html.encode(self.data_instance.raw_encoding,'ignore') 
            },
            headers = {'Content-Type':'application/x-www-form-urlencoded'}
        )
        return req.post()
        
    
class BoilerpipeArticleExtractor(BoilerpipeDefaultExtractor):
    '''Boilerpipe article extractor'''
    
    NAME = 'Boilerpipe ART'
    SLUG = 'boilerpipe_art'
    FORMAT = 'json'
    
    _extractor_type = 'article'
    
class BoilerpipeArticleSentencesExtractor(BoilerpipeDefaultExtractor):
    '''Boilerpipe extractor tuned for extracting article sentences'''
    
    NAME = 'Boilerpipe SENT'
    SLUG = 'boilerpipe_sent'
    FORMAT = 'json'
    
    _extractor_type = 'sentence'
    
class GooseExtractor(_FormattedResultMin,_ContentCheckMin,BaseExtractor):
    '''Goose project extractor'''
    
    NAME = 'Goose'
    SLUG = 'goose'
    FORMAT = 'json'
    
    @return_content
    def extract(self):
        html = self.data_instance.get_raw_html()
        req = Request(
            settings.GOOSE_API_ENDPOINT,
            data = dict(rawHtml = html.encode(self.data_instance.raw_encoding,'ignore')),
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
            data = html.encode('utf-8','ignore'),
            headers= {'Content-Type': 'text/plain;charset=UTF-8'}
        )
        return req.post()
    
    @classmethod
    def formatted_result(cls, result_string):
        return TextResultFormat(html_to_text(result_string, 'utf8'))
        
    
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
    
    @classmethod
    def formatted_result(cls, result_string):
        return TextResultFormat(html_to_text(result_string, 'utf8'))
    
class NodeReadabilityExtractor(_FormattedResultMin,BaseExtractor):
    '''Extractor based on node-readability'''
    
    NAME = 'Node Readability'
    SLUG = 'node_read'
    FORMAT = 'json'
    
    @check_content_status
    @return_content
    def extract(self):
        html = self.data_instance.get_raw_html()
        
        req = Request(
            settings.READABILITY_ENDPOINT,
            #this implementation requires utf-8 encoded input
            data = html.encode('utf-8','ignore'),
            headers= {'Content-Type': 'text/plain;charset=UTF-8'}
        )
        return req.post() 
    
    def _content_status(self):
        js = json.loads(self._content, encoding = 'utf8')
        if js['status'] == 'ERROR':
            raise ContentExtractorError('failed')
        
class SeleniumReadabilityExtractor(BaseExtractor):
    '''
    Using selenium webdriver API to harvest the results of the original
    readability bookmarklet
    '''
    
    NAME = 'Readability'
    SLUG = 'orig_read'
    FORMAT = 'txt'
    
    _driver = webdriver.Firefox()
    #TODO: share the modified code
    _bookmarklet_source = "(function(){readConvertLinksToFootnotes=false;readStyle='style-newspaper';readSize='size-medium';readMargin='margin-wide';_bookm=document.createElement('script');_bookm.type='text/javascript';_bookm.src='" + \
    settings.READABILITY_BOOKMARKLET + "?x='+Math.random();document.getElementsByTagName('head')[0].appendChild(_bookm);})();"
    
    def _check_content_presence(self):
        try:
            # this was a modification to readability.js script
            # if it failed to extract any meaningful content
            # we renamed the id of the content block to
            # explicitly indicate this special case
            self._driver.find_element_by_id('readability-content-failed')
        except NoSuchElementException:
            pass
        else:
            raise ContentExtractorError('readability failed to extract any content')
    
    def extract(self):
        url = self.data_instance.get_url()
        self._driver.get(url)
        self._driver.execute_script(self._bookmarklet_source)
        
        try:
            element = self._driver.find_element_by_id('readInner')
        except NoSuchElementException:
            raise ContentExtractorError('readability failed to produce the #readInner DOM node')
        else:
            return element.text.encode(self.data_instance.raw_encoding, 'ignore')
        
    @classmethod
    def formatted_result(cls, result_string):
        #TODO: 
        pass

class AlchemyExtractor(BaseExtractor):
    '''Alchemy API extractor'''
    
    NAME = 'Alchemy API'
    SLUG = 'alchemy'
    FORMAT = 'json'
    
    @check_content_status
    @return_content
    def extract(self):
        html = self.data_instance.get_raw_html()
        req = Request(
            'http://access.alchemyapi.com/calls/html/HTMLGetText',
            data = {'apikey':settings.ALCHEMY_API_KEY,
                    'html': html.encode(self.data_instance.raw_encoding,'ignore'),
                    'outputMode':'json'
            } 
            
        )
        return req.post()
    
    def _content_status(self):
        js = json.loads(self._content, encoding = 'utf8')
        if js['status'] == 'ERROR':
            raise ContentExtractorError(js['statusInfo'].encode('utf8','ignore'))
        
    @classmethod
    def formatted_result(cls, result_string):
        js = json.loads(result_string, encoding = 'utf8')
        return TextResultFormat(js['text'].encode('utf8','ignore'))
        
class DiffbotExtractor(BaseExtractor):
    '''Diffbot extractor'''
    
    NAME = 'Diffbot'
    SLUG = 'diffbot'
    FORMAT = 'json'
    
    @return_content
    def extract(self):        
        data = urllib.urlencode(dict(
            token = settings.DIFFBOT_API_KEY,
            url = self.data_instance.get_url(),
            format = 'json'
        ))
        data += '&stats' # use '&html' for html formatted result
        req = Request(
            'http://www.diffbot.com/api/article',
            data = data
        )
        return req.get()
    
    @classmethod
    def formatted_result(cls, result_string):
        js = json.loads(result_string, encoding = 'utf8')
        return TextResultFormat(
            js.get('title','').encode('utf8','ignore') + ' ' +\
            js['text'].encode('utf8','ignore')
        )
    
class ExtractivExtractor(BaseExtractor):
    '''Extractiv extractor'''
    
    NAME = 'Extractiv'
    SLUG = 'extractiv'
    FORMAT = 'json'
    
    @return_content
    def extract(self):
        html = self.data_instance.get_raw_html()
        req = Request(
            'http://rest.extractiv.com/extractiv/',
            data = {'api_key':settings.EXTRACTIV_API_KEY,
                    'content': html.encode(self.data_instance.raw_encoding,'ignore'),
                    'output_format':'json'
            } 
            
        )
        return req.post()
    
    @classmethod
    def formatted_result(cls, result_string):
        js = json.loads(result_string, encoding = 'utf8')
        
        text = js['Document']['text']
        content_sentences = []
        for se in js['sentences']:
            zone = se.get('zone','regular')
            if zone == 'regular':
                content_sentences.append(text[se['offset']:se['offset']+se['len']] ) 
        
        return TextResultFormat(
            js['Document'].get('title','').encode('utf8','ignore') + ' ' +\
            (' '.join(content_sentences)).encode('utf8','ignore')
        )
        
class RepustateExtractor(BaseExtractor):
    '''Repustate extractor'''
    
    NAME = 'Repustate'
    SLUG = 'repustate'
    FORMAT = 'json'
    
    @check_content_status
    @return_content
    def extract(self):
        req  = Request(
            'http://api.repustate.com/v1/%s/clean-html.json' \
             % settings.REPUSTATE_API_KEY,
            data = 'url=%s' % self.data_instance.get_url()
        )
        return req.get()
    
    def _content_status(self):
        js = json.loads(self._content, encoding = 'utf8')
        if js['status'] != 'OK':
            raise ContentExtractorError(js['status'].encode('utf8','ignore'))
        
    @classmethod
    def formatted_result(cls, result_string):
        js = json.loads(result_string, encoding = 'utf8')
        return TextResultFormat(js['text'].encode('utf8','ignore'))
    
class ZemantaExtractor(BaseExtractor):
    '''Extractor used internally by Zemanta Ltd'''
    
    NAME = 'Zextractor'
    SLUG = 'zemanta'
    FORMAT = 'txt'
    
    def extract(self):
        html = self.data_instance.get_raw_html()
        html = html.encode(self.data_instance.raw_encoding,'ignore')
        cm = ClientManager()
        
        response = cm.extract(html, self.data_instance.raw_encoding)
        if response.error:
            raise ExtractorError(response.error)
        return response.text
    
    @classmethod
    def formatted_result(cls, result_string):
        return TextResultFormat(result_string)
    
class NCleanerStdEnExtractor(BaseExtractor):
    '''NCleaner extractor using the standard english n-gram model'''
    
    NAME = 'NCleaner En'
    SLUG = 'ncleaner_en'
    FORMAT = 'txt'
    
    def extract(self):
        '''
        This method is not implemented (for now), because ncleaner
        comes with a handy command line tool that trivially executes  
        the extraction task for us.
        '''
        raise NotImplementedError
    
    @classmethod
    def formatted_result(cls, result_string):
        # ncleaner uses the cleaneval style format for its output
        return CleanEvalFormat(result_string)
    
class NCleanerNonLexExtractor(NCleanerStdEnExtractor):
    '''NCleaner extractor using the non lexical n-gram model'''
    
    NAME = 'NCleaner NonLex'
    SLUG = 'ncleaner_nonlex'
    FORMAT = 'txt'
    
class TrendictionExtractor(BaseExtractor):
    '''Trendiction API'''
    
    NAME = 'Trendiction'
    SLUG = 'trendiction'
    FORMAT = 'json'
    
    @check_content_status
    @return_content
    def extract(self):
        req  = Request(
            settings.TRENDICTION_ENDPOINT,
            data = {
                'ckey':'',
                'url':self.data_instance.get_url(),
                'onlycontent':'false',
                'outf':'json',
            }
        )
        return req.get()
    
    def _content_status(self):
        js = json.loads(self._content, encoding = 'utf8')
        try:
            js['result_content']['data'][0]['content']['content_text']
            js['result_content']['data'][0]['content']['title_text']
        except (IndexError, KeyError) as e:
            raise ContentExtractorError('content not present in the response' + repr(e))
        
    @classmethod
    def formatted_result(cls, result_string):
        js = json.loads(result_string, encoding = 'utf8')
        content = js['result_content']['data'][0]['content']['content_text']
        title = js['result_content']['data'][0]['content']['title_text']
        return TextResultFormat((title +' '+ content).encode('utf8','ignore'))
    
class JustextExtractor(BaseExtractor):
    '''Justext extractor'''
    
    NAME = 'JusText'
    SLUG = 'justext'
    FORMAT = 'txt'
    
    def extract(self):
        html = self.data_instance.get_raw_html()
        html = html.encode(self.data_instance.raw_encoding,'ignore')
        paragraphs = justext.justext(html, justext.get_stoplist('English'),
                             encoding = self.data_instance.raw_encoding)    
        good_paragraphs = []
        for para in paragraphs:
            if para['class'] == 'good':
                paragraph_text = para['text']
                # this asseration makes sure we catch string and unicode only
                assert isinstance(paragraph_text, basestring)
                if type(paragraph_text) == unicode:
                    good_paragraphs.append(paragraph_text.encode('utf8', 'ignore'))
                else:
                    good_paragraphs.append(paragraph_text)
            
        return '\n\n'.join(good_paragraphs)
        
    @classmethod
    def formatted_result(cls, result_string):
        return TextResultFormat(result_string)
    
# list of all extractor classes         
extractor_list = (
    BoilerpipeDefaultExtractor,
    BoilerpipeArticleExtractor,
    BoilerpipeArticleSentencesExtractor,
    GooseExtractor,
    MSSExtractor,
    PythonReadabilityExtractor,
    NodeReadabilityExtractor,
    AlchemyExtractor,
    DiffbotExtractor,
    ExtractivExtractor,
    RepustateExtractor,
    ZemantaExtractor,
    NCleanerStdEnExtractor,
    NCleanerNonLexExtractor,
    TrendictionExtractor,
    JustextExtractor,
)

def get_extractor_cls(extractor_slug):
    '''Return the extractor class given a slug'''
    for e in extractor_list:
        if e.SLUG == extractor_slug: 
            return e
    