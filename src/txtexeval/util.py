import os
import urllib
import urllib2

import settings

# urllib wrappers

class _Response(object):
    
    def __init__(self, status_code = None, headers = None, content = None, err_msg = None):
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
            return _Response(err_msg = str(e.reason))
        else:
            return _Response(r.code, r.headers, r.read())
            
    def get(self):
        request = urllib2.Request('%s?%s' % (self.url, self.data), **self.kwargs)
        try: 
            r = urllib2.urlopen(request)
        except urllib2.URLError as e:
            return _Response(err_msg = str(e.reason))
        else:
            return _Response(r.code, r.headers, r.read())
        
# dataset helpers

def check_local_dataset(dataset_name):
    return os.path.exists( 
            os.path.join(settings.PATH_LOCAL_DATA, 'datasets', dataset_name)
    )