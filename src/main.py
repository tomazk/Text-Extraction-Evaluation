import unittest
from util import data, eval, extractor

# main loops are using the unittest framework
class TestDatasetEvaluation(unittest.TestCase):
    
    def test_alchemy(self):
        loader = data.LocalDatasetLoader()
        for dat in loader.get_dataset('testdataset'):
            ext = extractor.AlchemyExtractor(dat)
            
            ret = eval.AlchemyFormat(ext.extract_text())
            rel = dat.get_result()
            
            evaluator = eval.TextOnlyEvaluator(ret, rel)
            result = evaluator.get_results()
            print '----------'
            print 'data %s' % dat.raw_filename
            print 'precision %f' % result.precision
            print 'recall %f' % result.recall
            print 'f1_score %f' % result.f1_score

if __name__ == '__main__':
    unittest.main()