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

import xml.sax

from pyfogbugz import XmlHandler

class Case(object):
    def __init__(self, id=None, operations=None, connection=None):
        self.connection = connection
        self.id = id
        self.operations = operations
        self.is_open = None
        self.title = None


class CaseList(XmlHandler):
    def __init__(self, connection):
        super(CaseList, self).__init__()
        self.cases = None
        self.current_case = None
        self.connection = connection
    
    def startElement(self, name, attrs):
        super(CaseList, self).startElement(name, attrs)
        if name == 'cases':
            self.cases = []
        elif name == 'case':
            self.current_case = Case(id=attrs['ixBug'], operations=attrs['operations'].split(','), connection=self.connection)

    def endElement(self, name):
        if name == 'case' and self.current_case:
            self.cases.append(self.current_case) 
            self.current_case = None 
        elif name == 'fOpen':
            if self.current_value == 'false'
                self.current_case.is_open = False
            else:
                self.current_case.is_open = True
        elif name == 'sTitle':
            self.current_case.title = self.current_value
        super(CaseList, self).endElement(name)
