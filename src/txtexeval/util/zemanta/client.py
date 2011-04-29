from collections import namedtuple

from thrift import Thrift
from thrift.transport import TSocket, TTransport
from thrift.protocol import TBinaryProtocol

# this is the code thrift generates for us 
# gen-py directory was renamed to thriftgen
from .thriftgen.ceservice import ExtractorService
from .thriftgen.ceservice import ttypes

import settings
from ..common import execute_only_once
credentials = dict(settings.ZEMANTA_THRIFT) 

Response = namedtuple('Response', 'text error')

class ClientManager(object):
    
    __internal_state = {} # Borg design pattern (singleton)
    
    def __init__(self, extractor = None):
        self.__dict__ = self.__internal_state
        self.set_client()
        
    @execute_only_once    
    def set_client(self):
        self._transport = TTransport.TBufferedTransport(
            TSocket.TSocket(credentials['host'], credentials['port'])
        )
        self._protocol = TBinaryProtocol.TBinaryProtocol(self._transport)
        self._client = ExtractorService.Client(self._protocol)
        self._transport.open()
        
    def extract(self, encoded_htmldata, encoding):
        error = None
        text = ''
        try:
            response = self._client.extract('', '', encoded_htmldata, encoding)
        except ttypes.TAppException as e:
            error = '%r' % e
        except Thrift.TException as e:
            error = '%r' % e
        except Exception as e:
            error = '%r' % e
        else:
            if response.success:
                text = response.body.encode('utf8')
            else:
                error = 'ExtractorService.extract returned a response but the success flag was set to False'
        return Response(text, error)