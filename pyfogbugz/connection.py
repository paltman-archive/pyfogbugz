# Copyright (c) 2009 Patrick Altman http://paltman.com
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

"""
Provides connectivity to FogBugz
"""
import urllib2
import urlparse
import socket
import errno
import xml.sax

from pyfogbugz import config, UserAgent, XmlHandler
from pyfogbugz.exceptions import FogBugzClientError, FogBugzServerError
from pyfogbugz.filter import FilterList


class Connection(object):
    def __init__(self, url=None, username=None, password=None):
        if url:
            self.url = url
        elif config.has_option('Connection', 'url'):
            self.url = config.get('Connection', 'url')
        
        if username:
            self.username = username
        elif config.has_option('Connection', 'username'):
            self.username = config.get('Connection', 'username')
        
        if password:
            self.password = password
        elif config.has_option('Connection', 'password'):
            self.password = config.get('Connection', 'password')
        
    def make_request(self, path, data=None):
        response = None
        headers = {'User-Agent':UserAgent}
        if data:
            headers['Content-Length'] = len(data)
        try:
            url = "%s/%s" % (self.url, path)
            request = urllib2.Request(url=url, headers=headers)
            response = urllib2.urlopen(request)
            if response.code < 300:
                return response
        except KeyboardInterrupt:
            sys.exit("Keyboard Interrupt")
        except Exception, e:
            pass
        
        if response:
            raise FogBugzServerError(response.code, response.msg, response.read())
        elif e:
            raise e
        else:
            raise FogBugzClientError("Please report this exception as an issue with pyfogbugz.")
            
        
        
class ApiCheckHandler(XmlHandler):
    def __init__(self):
        super(ApiCheckHandler, self).__init__()
        self.version = ''
        self.minversion = ''
        self.url = ''
        
    def endElement(self, name):
        if name == 'version':
            self.version = self.current_value
        elif name == 'minversion':
            self.minversion = self.current_value
        elif name == 'url':
            self.url = self.current_value
        super(ApiCheckHandler, self).endElement(name)
        

class LogonHandler(XmlHandler):
    def __init__(self):
        super(LogonHandler, self).__init__()
        self.token = None
        self.people = None
    
    def startElement(self, name, attrs):
        super(LogonHandler, self).startElement(name, attrs)
        if name == 'people':
            self.people = []
    
    def endElement(self, name):
        if name == 'token':
            self.token = self.current_value
        elif name == 'person':
            self.people.append(self.current_value)
        super(LogonHandler, self).endElement(name)
    
        
    
class FogBugzConnection(Connection):
    def __init__(self, url=None, username=None, password=None):
        """
        @type url: string
        @param url: The url to the FogBugz server to connect to
        
        @type username: string
        @param username: The username for the connection
        
        @type password: string
        @param password: The password for the connection
        """
        self.token = None
        self.base_path = None
        super(FogBugzConnection, self).__init__(url, username, password)
        self._check_api()
        self._logon()
        
        
    def make_request(self, path, data=None):
        computed_path = path
        if self.base_path:
            computed_path = "%s%s" % (self.base_path, path)
            if self.token:
                computed_path += "&token=%s" % self.token
        return super(FogBugzConnection, self).make_request(computed_path, data)
    
    def _check_api(self):
        response = self.make_request('api.xml')
        if response:
            data = response.read()
            handler = ApiCheckHandler()
            xml.sax.parseString(data, handler)
            self.base_path = handler.url
        else:
            raise FogBugzClientError("Could not validate API.")
    
    def _logon(self):
        response = self.make_request('cmd=logon&email=%s&password=%s' % (self.username, self.password))
        if response:
            data = response.read()
            handler = LogonHandler()
            xml.sax.parseString(data, handler)
            if handler.has_error:
                raise FogBugzClientError("Invalid login: %s" % handler.error_message)
            else:
                self.token = handler.token
                
    def list_filters(self):
        response = self.make_request('cmd=listFilters')
        if response:
            data = response.read()
            filter_list = FilterList(connection=self)
            xml.sax.parseString(data, filter_list)
            if filter_list.has_error:
                raise FogBugzClientError("Invalid filter request: %s" % filter_list.error_message)
            else:
                return filter_list.filters
    
    