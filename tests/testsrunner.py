'''
Run all test cases residing in all modules that follow the test_[name].py
naming template.

We could also use nose test autodiscovery tool instead.
'''
import os
import unittest2

def test_modules():
    '''Get all test modules'''
    modlist = []
    for mod in os.listdir('.'):
        if mod.startswith('test_') and mod.endswith(".py"):
            modlist.append(mod[0:-3])
    return modlist

if __name__ == "__main__":    
    suite = unittest2.TestSuite()
    for mod in test_modules():
        suite.addTests(unittest2.TestLoader().loadTestsFromName(mod))    
    unittest2.TextTestRunner(verbosity=2).run(suite)