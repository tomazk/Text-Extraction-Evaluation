import os
import urllib
import urllib2

from BeautifulSoup import BeautifulSoup

import settings

# urllib wrappers

class _Response(object):
    
    def __init__(self, status_code = None, headers = None, 
                 content = None, err_msg = None):
        self.status_code = status_code
        self.headers = headers
        self.content = content
        self._err_msg = err_msg
        
    def success(self):
        if self._err_msg: 
            return False
        elif self.status_code and str(self.status_code).startswith('2'):# see RFC 2616
            return True
        else: 
            return False 
    
    @property
    def err_msg(self):
        if self._err_msg: 
            return self._err_msg
        elif self.status_code and str(self.status_code).startswith('2'):
            return 'Status code: %i' % self.status_code
        else: 
            return '' 
            

class Request(object):
    
    def __init__(self, url, data, **kwargs):
        self.url = url   
        self.kwargs = kwargs     
        if isinstance(data, dict):
            self.data = urllib.urlencode(data)
        else:
            self.data = data
        
    def post(self):
        request = urllib2.Request(self.url, self.data, **self.kwargs)
        try: 
            r = urllib2.urlopen(request)
        except urllib2.URLError as e:
            return _Response(err_msg = str(e))
        else:
            return _Response(r.code, r.headers, r.read())
            
    def get(self):
        request = urllib2.Request('%s?%s' % (self.url, self.data), **self.kwargs)
        try: 
            r = urllib2.urlopen(request)
        except urllib2.URLError as e:
            return _Response(err_msg = str(e))
        else:
            return _Response(r.code, r.headers, r.read())
        
# dataset helpers

def check_local_path(*args):
    return os.path.exists( 
            os.path.join(settings.PATH_LOCAL_DATA, 'datasets', *args)
    )
    
def get_local_path(*args):
    return os.path.join(settings.PATH_LOCAL_DATA, 'datasets', *args)

# others

def execute_only_once(method):
    '''A decorator that runs a method only once.'''
    attrname = "_%s_once_result" % id(method)
    def wrap(self, *args, **kwargs):
        try:
            return getattr(self, attrname)
        except AttributeError:
            setattr(self, attrname, method(self, *args, **kwargs))
            return getattr(self, attrname)
    return wrap

def html_to_text(html, encoding):
    '''Get all the text from a given html string'''
    soup = BeautifulSoup(html, fromEncoding = encoding)
    tags = soup.findAll(text = True)
    useful = lambda e: e.parent.name not in ('style', 'script', 'head', 'title')
    tags = filter(useful, tags)
    return ' '.join(map(lambda e: e.encode(encoding), tags))