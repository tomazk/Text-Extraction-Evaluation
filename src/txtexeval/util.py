import urllib
import urllib2

class Response(object):
    
    def __init__(self, status_code = None, headers = None, content = None, err_msg = None):
        self.status_code = status_code
        self.headers = headers
        self.content = content
        self.err_msg = err_msg
        
    def success(self):
        if self.err_msg: 
            return False
        elif self.status_code and str(self.status_code).startswith('2'):# see RFC 2616
            return True
        else: 
            return False 

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
            return Response(err_msg = str(e.reason))
        else:
            return Response(r.code, r.headers, r.read())
            
    def get(self):
        request = urllib2.Request('%s?%s' % (self.url, self.data), **self.kwargs)
        try: 
            r = urllib2.urlopen(request)
        except urllib2.URLError as e:
            return Response(err_msg = str(e.reason))
        else:
            return Response(r.code, r.headers, r.read())