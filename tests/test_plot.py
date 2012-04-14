import unittest2

from plot_manage import equidistant_count
                                 
class TestEvaluation(unittest2.TestCase):
    
    def test_equidistant_count(self):
        r = equidistant_count(0, 1, 0.2, [0.11,0.22,0.32])
        self.assertEqual(r, (1,2,0,0,0))
        
        r = equidistant_count(0, 1, 0.5, [0.,0.22,0.32,0.5])
        self.assertEqual(r, (3,1))
    
def main():
    unittest2.main(exit = False, verbosity = 2)
    
if __name__ == '__main__':
    main()