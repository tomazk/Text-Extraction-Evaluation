import unittest2
from util import data, evaluation as ev, extractor as ex

DEBUG = False 

# skipIf wrapper
def skip(test_fun):
    return unittest2.skipIf(DEBUG, 'debug option is on')(test_fun)

# main loops are using the unittest framework
class TestDatasetEvaluation(unittest2.TestCase):
    
    
    @skip
    def test_alchemy(self):
        loader = data.LocalDatasetLoader()
        for dat in loader.get_dataset('testdataset'):
            ext = ex.AlchemyExtractor(dat)
            
            ret = ev.AlchemyFormat(ext.extract_text())
            rel = dat.get_result()
            
            evaluator = ev.TextOnlyEvaluator(ret, rel)
            result = evaluator.get_results()
            print '----------'
            print 'data %s' % dat.raw_filename
            print 'precision %f' % result.precision
            print 'recall %f' % result.recall
            print 'f1_score %f' % result.f1_score
    
    @skip
    def test_python_readability(self):
        loader = data.LocalDatasetLoader()
        for dat in loader.get_dataset('testdataset'):
            ext = ex.PythonReadabilityExtractor(dat)
            
            ret = ev.PythonRedabilityFormat(ext.extract_text())
            rel = dat.get_result()#CleanEval format
            
            evaluator = ev.TextOnlyEvaluator(ret, rel)
            result = evaluator.get_results()
            print '----------'
            print 'data %s' % dat.raw_filename
            print 'precision %f' % result.precision
            print 'recall %f' % result.recall
            print 'f1_score %f' % result.f1_score

if __name__ == '__main__':
    unittest2.main()