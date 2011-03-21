import unittest2

from txtexeval import data, evaluation as ev, extractor as ex

# debugging constant
DEBUG = False 

# skipIf wrapper
def skip_when_debugging(test_fun):
    return unittest2.skipIf(DEBUG, 'debug option is on')(test_fun)

# main loops are using the unittest framework
class TestDatasetEvaluation(unittest2.TestCase):
    

    @skip_when_debugging
    def test_alclchemy(self):
        evalResults = ev.TextBasedResults(ex.AlchemyExtractor.NAME)
        
        loader = data.LocalDatasetLoader('testdataset2')
        for dat in loader:
            print 'working on %s' % dat.raw_filename
            ext = ex.AlchemyExtractor(dat)
            try:
                ret = ev.TextResultFormat(ext.extract_text())
            except ex.ExtractorError as e:
                print 'skipped %s: %s' % dat.raw_filename, str(e)
            else:
                rel = dat.get_result()
                evaluator = ev.TextOnlyEvaluator(ret, rel)
                result = evaluator.get_results()
                evalResults.append_result(result)
            
    @skip_when_debugging
    def test_python_readability(self):
        evalResults = ev.TextBasedResults(ex.PythonReadabilityExtractor.NAME)
        
        loader = data.LocalDatasetLoader('testdataset2')
        for dat in loader:
            print 'working on %s' % dat.raw_filename
            ext = ex.PythonReadabilityExtractor(dat)
            
            ret = ev.TextResultFormat(ext.extract_text())
            rel = dat.get_result()
            
            evaluator = ev.TextOnlyEvaluator(ret, rel)
            result = evaluator.get_results()
            evalResults.append_result(result)
            
    @skip_when_debugging
    def test_MSS(self):
        evalResults = ev.TextBasedResults(ex.MSSExtractor.NAME)
        
        loader = data.LocalDatasetLoader('testdataset2')
        for dat in loader:
            print 'working on %s' % dat.raw_filename
            ext = ex.MSSExtractor(dat)
            try:
                ret = ev.TextResultFormat(ext.extract_text())
            except ex.ExtractorError as e:
                print 'skipped %s: %s' % dat.raw_filename, str(e)
            else:
                rel = dat.get_result()
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
    