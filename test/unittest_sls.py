"""Unit test for sls.py"""
# http://bayes.colorado.edu/PythonGuidelines.html#unit_tests

__version__="0.27"

import unittest


class Class_Test(unittest.TestCase): 
    
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
        
    def test_awesome(self):
        """ BOWBuilderSimple.consume() returns an instance of a SmartURL. """
        pass

if __name__ == "__main__":
    
    #whole=False
    whole=True
    
    if whole:
        unittest.main()   