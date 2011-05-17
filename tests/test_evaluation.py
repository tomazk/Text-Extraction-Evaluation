# -*- coding: utf-8 -*-
import re
import math

import unittest2

from txtexeval.util import html_to_text
from txtexeval.evaluation import _tokenize_text, _bow
from txtexeval.evaluation import TextOnlyEvaluator
from txtexeval.evaluation import TextBasedResults, Result
from txtexeval.evaluation import BaseResultFormat, TextResultFormat, \
                                 CleanEvalFormat,GoogleNewsFormat
                                 
                                 
class TestHelpers(unittest2.TestCase):        
                                 
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

class TestFormats(unittest2.TestCase):
        
    def test_textresultformat(self):
        s = '''
        This is (some text). AAAA!!"#.{}
        special charčć€šđž char.
        '''
        t = TextResultFormat(s)
        self.assertEqual(t.get_word_seq(), ['this','is','some','text','aaaa','special','char','char'])
        self.assertEqual(t.get_bow(), {'this':1,'is':1,'some':1,'text':1,'aaaa':1,'special':1,'char':2})
        
    def test_textresultformat_empty(self):
        t = TextResultFormat('''
        
        
            ''')
        self.assertEqual(t.get_word_seq(), [])
        self.assertEqual(t.get_bow(), {})
    
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
        s = '''URL: http://childparenting.about.com/b/archives.htm
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
                content
            </span>
        </span> 
        Not content
        </p>
        '''
        gn = GoogleNewsFormat(s, 'utf8')
        self.assertEqual(gn.get_word_seq(), ['headline','here','double','content','text','content','here','content',])
        self.assertEqual(gn.get_bow(), {'headline':1,'here':2,'double':1,'content':3,'text':1})
        
    def test_googlenewsformat_empty1(self):
        s = '''
        <p>
        <span class="x-nc-sel5"> 
            Headline here (not content)
        </span>
        <span class="bodysmall">
            <span class="x-nc-sel5"> 
                not content 
                <span class="x-nc-sel5"> 
                    no content here€
                </span>
                not content
            </span>
        </span> 
        Not content
        </p>
        '''
        gn = GoogleNewsFormat(s, 'utf8')
        self.assertEqual(gn.get_word_seq(), [])
        self.assertEqual(gn.get_bow(), {})
    
    def test_googlenewsformat_empty2(self):
        gn = GoogleNewsFormat('','ascii')
        self.assertEqual(gn.get_word_seq(), [])
        self.assertEqual(gn.get_bow(), {})
        
def dummy_format_factory(word_seq):
    class DummyFormat(BaseResultFormat):
        def get_bow(self):
            return _bow(word_seq) 
    
        def get_word_seq(self):
            return word_seq
    return DummyFormat()
        
class TestTextEvaluator(unittest2.TestCase):
    
    def test_empty_relevant(self):
        ret = dummy_format_factory(['one','two'])
        rel = dummy_format_factory([])
        # args: TextOnlyEvaluator(retrieved, relevant)
        e = TextOnlyEvaluator(ret, rel)
        r = e.get_eval_results()
        self.assertEqual(r.precision, 0)
        self.assertTrue(math.isinf(r.recall))
        self.assertTrue(math.isnan(r.f1_score))
        
    def test_empty_retrieved(self):
        ret = dummy_format_factory([])
        rel = dummy_format_factory(['one','two'])
        # args: TextOnlyEvaluator(retrieved, relevant)
        e = TextOnlyEvaluator(ret, rel)
        r = e.get_eval_results()
        self.assertEqual(r.recall, 0)
        self.assertTrue(math.isinf(r.precision))
        self.assertTrue(math.isnan(r.f1_score))
        
    def test_both_empty(self):
        ret = dummy_format_factory([])
        rel = dummy_format_factory([])
        # args: TextOnlyEvaluator(retrieved, relevant)
        e = TextOnlyEvaluator(ret, rel)
        r = e.get_eval_results()
        self.assertTrue(math.isinf(r.precision))
        self.assertTrue(math.isinf(r.recall))
        self.assertTrue(math.isnan(r.f1_score))
        
    def test_missmatch(self):
        ret = dummy_format_factory(['one','four'])
        rel = dummy_format_factory(['two','three'])
        # args: TextOnlyEvaluator(retrieved, relevant)
        e = TextOnlyEvaluator(ret, rel)
        r = e.get_eval_results()
        self.assertEqual(r.precision, 0)
        self.assertEqual(r.recall, 0)
        self.assertTrue(math.isinf(r.f1_score))
        
    def test_match(self):
        ret = dummy_format_factory(['zero','one','two','four'])
        rel = dummy_format_factory(['one','two','three'])
        # args: TextOnlyEvaluator(retrieved, relevant)
        e = TextOnlyEvaluator(ret, rel)
        r = e.get_eval_results()
        self.assertAlmostEqual(r.precision, 0.5)
        self.assertAlmostEqual(r.recall, 0.6666, delta = 0.0001)
        self.assertAlmostEqual(r.f1_score, 0.5714, delta = 0.001)
        
    def test_perfect_match(self):
        ret = dummy_format_factory(['zero'])
        rel = dummy_format_factory(['zero'])
        # args: TextOnlyEvaluator(retrieved, relevant)
        e = TextOnlyEvaluator(ret, rel)
        r = e.get_eval_results()
        self.assertAlmostEqual(r.precision, 1)
        self.assertAlmostEqual(r.recall, 1)
        self.assertAlmostEqual(r.f1_score, 1)
        
class TestTextBasedResults(unittest2.TestCase):
    
    def setUp(self):
        self.results = TextBasedResults('e1')
        # Result(precision, recall, f1_score, id)
        self.results.add_result(Result(0,0,float('inf'),None))
        
        self.results.add_result(Result(float('inf'),0,float('nan'),None))
        self.results.add_result(Result(float('inf'),0,float('nan'),None))
        
        self.results.add_result(Result(0,float('inf'),float('nan'),None))
        self.results.add_result(Result(0,float('inf'),float('nan'),None))
        
        self.results.add_result(Result(float('inf'),float('inf'),float('nan'),None))
        
        self.results.add_result(Result(0.2,0.2,0.2,None))
        self.results.add_result(Result(0.2,0.2,0.2,None))
        self.results.add_result(Result(0.2,0.2,0.2,None))
        self.results.add_result(Result(0.2,0.2,0.2,None))
        
        self.results.dataset_len = 12
        
    def tearDown(self):
        self.results.text_eval_results['e1'] = []
        
    def test_results_contents(self):
        contents = self.results.results_contents('e1')
        self.assertEqual(contents.fail, 2)
        self.assertEqual(contents.succ, 4)
        self.assertEqual(contents.rel_empty, 2)
        self.assertEqual(contents.ret_empty, 2)
        self.assertEqual(contents.rel_ret_empty, 1)
        self.assertEqual(contents.missmatch, 1)
        
    def test_result_filter(self):
        fr = self.results.filtered_results('e1')
        self.assertEqual(len(fr), 4)
        
    def test_precision_statistics(self):
        avg, std = self.results.precision_statistics('e1')
        self.assertEqual(avg, 0.2)
        self.assertEqual(std, 0.)
        
    def test_recall_statistics(self):
        avg, std = self.results.recall_statistics('e1')
        self.assertEqual(avg, 0.2)
        self.assertEqual(std, 0.)
        
    def test_f1score_statistics(self):
        avg, std = self.results.f1score_statistics('e1')
        self.assertEqual(avg, 0.2)
        self.assertEqual(std, 0.)
        
    def test_add_bad_result(self):
        r = TextBasedResults('e2')
        with self.assertRaises(AssertionError):
            r.add_result(Result(2,1,1,None))
        with self.assertRaises(AssertionError):
            r.add_result(Result(float('inf'),float('inf'),1,None))
        with self.assertRaises(AssertionError):
            r.add_result(Result(float('inf'),0,1,None))
        with self.assertRaises(AssertionError):
            r.add_result(Result(0,0,1,None))
            
    def test_add_good_result(self):
        r = TextBasedResults('e3')
        try:
            r.add_result(Result(0.2,0.2,0.2,None))
        except AssertionError:
            self.fail()

def main():
    unittest2.main(exit = False, verbosity = 2)
    
if __name__ == '__main__':
    main()
    