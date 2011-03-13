import unittest2
from util import data, evaluation as ev, extractor as ex

# debugging utility
DEBUG = False 

# skipIf wrapper
def skip(test_fun):
    return unittest2.skipIf(DEBUG, 'debug option is on')(test_fun)

# main loops are using the unittest framework
class TestDatasetEvaluation(unittest2.TestCase):
    
    @skip
    def test_alchemy(self):
        evalResults = ev.TextBasedResults(ex.AlchemyExtractor.NAME)
        
        loader = data.LocalDatasetLoader()
        for i,dat in enumerate (loader.get_dataset('testdataset')):
            print i
            ext = ex.AlchemyExtractor(dat)
            
            ret = ev.AlchemyFormat(ext.extract_text())
            rel = dat.get_result()
            
            evaluator = ev.TextOnlyEvaluator(ret, rel)
            result = evaluator.get_results()
            evalResults.append_result(result)

    
    @skip
    def test_python_readability(self):
        evalResults = ev.TextBasedResults(ex.PythonReadabilityExtractor.NAME)
        
        loader = data.LocalDatasetLoader()
        for i,dat in enumerate(loader.get_dataset('testdataset')):
            print i
            ext = ex.PythonReadabilityExtractor(dat)
            
            ret = ev.PythonRedabilityFormat(ext.extract_text())
            rel = dat.get_result()#CleanEval format
            
            evaluator = ev.TextOnlyEvaluator(ret, rel)
            result = evaluator.get_results()
            evalResults.append_result(result)


def main():
    unittest2.main(exit = False, verbosity = 2)
    
    evalRes = ev.TextBasedResults()
    evalRes.print_results()
    evalRes.save()
    

if __name__ == '__main__':
    main()
    