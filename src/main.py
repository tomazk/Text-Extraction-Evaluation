import unittest2
from util import data, evaluation as ev, extractor as ex

# debugging utility
DEBUG = False 


class Results(object):
    '''Results container'''
    
    __internal_state = {} # Borg design pattern
    
    def __init__(self, extractor = None):
        self.__dict__ = self.__internal_state
        if not 'results' in self.__dict__: 
            self.results = {}
        
        if extractor and (not (extractor in self.results)):
            self.results[extractor] = []
            
        self.extractor = extractor
        
            
    def appendResult(self, result):
        if self.extractor:
            self.results[self.extractor].append(result)
        
    def printResults(self):
        for extractor_name, results_list in self.results.iteritems():
            avg_precision = sum([r.precision for r in results_list]) / float(len(results_list))
            avg_recall = sum([r.recall for r in results_list]) / float(len(results_list))
            avg_f1 = sum([r.f1_score for r in results_list]) / float(len(results_list))
            print '----------------'
            print 'Ex. name: %s' % extractor_name
            print 'avg. precision: %f' % avg_precision 
            print 'avg. racall: %f' % avg_recall
            print 'avg. F1 score: %f' % avg_f1
    
    def plotResults(self):
        #TODO
        pass
        

# skipIf wrapper
def skip(test_fun):
    return unittest2.skipIf(DEBUG, 'debug option is on')(test_fun)

# main loops are using the unittest framework
class TestDatasetEvaluation(unittest2.TestCase):
    
    @skip
    def test_alchemy(self):
        evalResults = Results(ex.AlchemyExtractor.NAME)
        
        loader = data.LocalDatasetLoader()
        for dat in loader.get_dataset('testdataset'):
            ext = ex.AlchemyExtractor(dat)
            
            ret = ev.AlchemyFormat(ext.extract_text())
            rel = dat.get_result()
            
            evaluator = ev.TextOnlyEvaluator(ret, rel)
            result = evaluator.get_results()
            evalResults.appendResult(result)

    
    @skip
    def test_python_readability(self):
        evalResults = Results(ex.PythonReadabilityExtractor.NAME)
        
        loader = data.LocalDatasetLoader()
        for dat in loader.get_dataset('testdataset'):
            ext = ex.PythonReadabilityExtractor(dat)
            
            ret = ev.PythonRedabilityFormat(ext.extract_text())
            rel = dat.get_result()#CleanEval format
            
            evaluator = ev.TextOnlyEvaluator(ret, rel)
            result = evaluator.get_results()
            evalResults.appendResult(result)


def main():
    unittest2.main(exit = False, verbosity = 2)
    
    evalRes = Results()
    evalRes.printResults()
    

if __name__ == '__main__':
    main()
    