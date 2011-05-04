# -*- coding: utf-8 -*-
import re

import unittest2

from txtexeval.util import html_to_text
from txtexeval.evaluation import _tokenize_text
from txtexeval.evaluation import TextResultFormat, \
                                 CleanEvalFormat,GoogleNewsFormat
                                 
                                 

class TestEvaluation(unittest2.TestCase):
    
    def test_tokenize_text(self):
        s = '''
        This is (some text). AAAA!!"#.{}
        special charčć€šđž.
        '''
        r = _tokenize_text(s)
        self.assertEqual(r, ['this','is','some','text','aaaa','special','char'])
        
    def test_tokenize_text_empty(self):
        s = ''
        r = _tokenize_text(s)
        self.assertEqual(r, [])
    
    def test_html_to_text(self):
        s = '''
        <html>
            <head>
                <title>Title</title>
                <style>
                p
                {
                font-family:"Times New Roman";
                font-size:20px;
                }
                </style>
            </head>
            
            <body>
                <script type="text/javascript">
                 $.document()
                </script>

                Body
                <p>Paragraph <strong>here</strong></p>
                More text
            </body>
        </html>
        '''
        t = html_to_text(s, encoding = 'ascii')
        t = t.strip()
        self.assertTrue(t.startswith('Body'))
        self.assertTrue(t.endswith('text'))
        
    def test_html_to_text_empty(self):
        s = ''
        t = html_to_text(s, encoding = 'ascii')
        self.assertTrue(re.match('\s*', t))
        
    def test_textresultformat(self):
        s = '''
        This is (some text). AAAA!!"#.{}
        special charčć€šđž char.
        '''
        t = TextResultFormat(s)
        self.assertEqual(t.get_word_seq(), ['this','is','some','text','aaaa','special','char','char'])
        self.assertEqual(t.get_bow(), {'this':1,'is':1,'some':1,'text':1,'aaaa':1,'special':1,'char':2})
        
    
    def test_cleanevalformat(self):
        s = '''
        URL: http://childparenting.about.com/b/archives.htm
        <p> this is
        <h> cleaneval
        <l> format
        
        <P> this is
        <H> cleaneval
        <L> format
        '''
        ce = CleanEvalFormat(s)
        self.assertEqual(ce.get_word_seq(), ['this','is','cleaneval','format','this','is','cleaneval','format'])
        self.assertEqual(ce.get_bow(), {'this':2,'is':2,'cleaneval':2,'format':2})

    def test_cleanevalformat_empty(self):
        s = '''
        URL: http://childparenting.about.com/b/archives.htm
        '''
        ce = CleanEvalFormat(s)
        self.assertEqual(ce.get_word_seq(), [])
        self.assertEqual(ce.get_bow(), {})
        
    def test_googlenewsformat(self):
        s = '''
        <p>
        <span class="x-nc-sel1"> 
            Headline here
        </span>
        <span class="bodysmall">
            <span class="x-nc-sel2"> 
                Double content 
                <span class="x-nc-sel2"> 
                    Text content here€
                </span>
            </span>
        </span> 
        </p>
        '''
        gn = GoogleNewsFormat(s, 'utf8')
        self.assertEqual(gn.get_word_seq(), ['headline','here','double','content','text','content','here'])
        self.assertEqual(gn.get_bow(), {'headline':1,'here':2,'double':1,'content':2,'text':1})
        
    def test_googlenewsformat_empty(self):
        s = ''
        gn = GoogleNewsFormat(s,'ascii')
        self.assertEqual(gn.get_word_seq(), [])
        self.assertEqual(gn.get_bow(), {})
    
def main():
    unittest2.main(exit = False, verbosity = 2)
    
if __name__ == '__main__':
    main()
    