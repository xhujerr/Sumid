"""Unit test for sumid.py"""
# http://bayes.colorado.edu/PythonGuidelines.html#unit_tests

__version__="0.26"

import unittest
from mock import Mock
from Queue import Queue
from threading import Condition
from bow import BOWBuilderSimple, BOWUpdaterSimple
from linklist import SmartURL
from miscutil import CounterManager

class TextLinklistParserMock(Mock):
    
    def __init__(self):
        self._linklistEOF=False # 026 It's expected that this variable will be accessed as public within module.
        self.cx=0
    
    @ property
    def linklistEOF(self):
        return self._linklistEOF
    
    def next(self):
        self.cx+=1 # 026 If not outside, infinite cycle.
        if not self.linklistEOF:
            url=SmartURL("http://www.example.com/page%i.html"%(self.cx))
            return url
        else: return None
        
class SettingsDummy(object):
    linkListSpcSymbols=['@','#']
    urlWordsSeparators=[',',' ','.','/','-','_','?']   
    commonWords=["","http:","www","html","com","php","net","org","co","uk","htm","aspx","cfm","asp","au","cgi"]
    bowTempSize=100     
    bowWaitTime=0
    
class DebugMock(Mock):
    
    def __init__(self):
        self.mainLogger=LoggerMock()
        self.ThreadAwareLogger=LoggerMock()

class LoggerMock(Mock):
            
    def debug(self,argument):
        #print argument
        pass
    
class FilesAdaptorDummy():
    """ This is not to test FilesAdaptor - out of scope."""
    def __init__(self):
        self._updateDBcounter=0
    
    def updateBOW(self,counters):
        self._updateDBcounter+=1
        return 88

class BOWBuilderTest(unittest.TestCase): 
    
    def setUp(self):
        self.parserInstance=TextLinklistParserMock()
        self.outputQueue=Queue()
        outputCondition=Condition()
        self.bOWBuilderSimple=BOWBuilderSimple(None,self.outputQueue,None,outputCondition,parserInstance=self.parserInstance)
        self.bOWBuilderSimple.settings=SettingsDummy()
        self.bOWBuilderSimple.debug=DebugMock()
    
    def tearDown(self):
        del self.bOWBuilderSimple
        del self.parserInstance

    def test_BOWBuilderSimple_consume(self):
        """ BOWBuilderSimple.consume() returns an instance of a SmartURL. """
        result=self.bOWBuilderSimple.consume()
        self.assertTrue(isinstance(result,SmartURL))

    def test_BOWBuilderSimple_verify_incorrect_input(self):
        """ BOWBuilderSimple.verifySemiProduct() doesn't accept simple string or another wrong input. """
        self.assertFalse(self.bOWBuilderSimple.verifySemiProduct("http://www.example.com/page88.html"))
        self.assertFalse(self.bOWBuilderSimple.verifySemiProduct(None))
        self.assertFalse(self.bOWBuilderSimple.verifySemiProduct('c'))
        self.assertFalse(self.bOWBuilderSimple.verifySemiProduct(88))
        
    def test_BOWBuilderSimple_verify_correct_input(self):
        """ BOWBuilderSimple.verifySemiProduct() returns true if called with a SmartURL instance."""
        url=SmartURL("http://www.example.com/page88.html")
        self.assertTrue(self.bOWBuilderSimple.verifySemiProduct(url))
    
    def test_BOWBuilderSimple_produce_data(self):
        """ Into counters goes the result of parser.words() """
        url=SmartURL("http://www.kosek.cz/clanky/kosek/swn-xml/ar02s17.html")
        expectation={"kosek":2,"cz":1,"clanky":1,"swn":1,"xml":1,"ar02s17":1}
        # 026 Tests also that "http:","","www","html" are left out.
        # 026 Tests also that kosek is count twice.
        self.bOWBuilderSimple.produce(url)
        result=self.bOWBuilderSimple.counters.counters
        self.assertDictEqual(result,expectation)
        
        
    def test_BOWBuilderSimple_produce_incremental(self):
        """ BOWBuilderSimple.produce() is incrementally stuffed with data, while at some places are performed asserts. """
        while self.parserInstance.cx<205:
            semiProduct = self.bOWBuilderSimple.consume()
            if self.parserInstance.cx >= 204: self.parserInstance._linklistEOF=True
            if self.bOWBuilderSimple.verifySemiProduct(semiProduct):
                # 026 Verification requires due to async in incrementing.) 
                self.bOWBuilderSimple.produce(semiProduct)
            if self.parserInstance.cx == 73: self.assertEqual(self.bOWBuilderSimple.counters.NumberOfCounters, 73+1)
            if self.parserInstance.cx == 99: self.assertTrue(self.outputQueue.empty())
            if self.parserInstance.cx == 101: self.assertFalse(self.outputQueue.empty())
            if self.parserInstance.cx == 101: self.assertEqual(self.bOWBuilderSimple.counters.NumberOfCounters, 1+1)
            if self.parserInstance.cx == 173: self.assertEqual(self.bOWBuilderSimple.counters.NumberOfCounters, 73+1)
            if self.parserInstance.cx == 199: self.assertEqual(self.outputQueue.qsize(),1)
            if self.parserInstance.cx == 201: self.assertEqual(self.outputQueue.qsize(),2)
            if self.parserInstance.cx == 201: self.assertEqual(self.bOWBuilderSimple.counters.NumberOfCounters, 1+1)
            if self.parserInstance.cx == 204: self.assertEqual(self.outputQueue.qsize(),3)
        # Test if item in queue is correct:
        item=self.outputQueue.get()
        self.assertTrue(isinstance(item,CounterManager))
        self.assertEqual(item.title, "words")
 
class BOWUpdaterTest(unittest.TestCase): 

    def setUp(self):
        self.parserInstance=TextLinklistParserMock()
        self.intputQueue=Queue()
        inputCondition=Condition()
        self.files=FilesAdaptorDummy()
        self.bOWUpdaterSimple=BOWUpdaterSimple(self.intputQueue,None,inputCondition,None,filesAdaptor=self.files, parserInstance=self.parserInstance)
        self.bOWUpdaterSimple.settings=SettingsDummy()
        self.bOWUpdaterSimple.debug=DebugMock()
    
    def tearDown(self):
        del self.bOWUpdaterSimple
        #del self.files        
        
    def test_BOWUpdaterSimple_consume(self): 
        """ BOWUpdaterSimple.consume() returns an instance of a CounterManager. And shorten input queue."""
        # 026 First with empty queue.
        self.assertEqual(self.intputQueue.qsize(), 0)
        item = self.bOWUpdaterSimple.consume()
        self.assertEqual(self.intputQueue.qsize(), 0)
        self.assertIsNone(item)
        # 026 Then with some items in input queue.
        self.intputQueue.put(CounterManager())
        self.intputQueue.put(CounterManager())
        self.assertEqual(self.intputQueue.qsize(), 2)
        item = self.bOWUpdaterSimple.consume()
        self.assertEqual(self.intputQueue.qsize(), 1)
        self.assertTrue(isinstance(item,CounterManager))
        
    def test_BOWUpdaterSimple_verify_incorrect_input(self): 
        """ BOWUpdaterSimple.verifySemiProduct() doesn't accept simple string, SmartURL or another wrong input. """
        self.assertFalse(self.bOWUpdaterSimple.verifySemiProduct("http://www.example.com/page88.html"))
        self.assertFalse(self.bOWUpdaterSimple.verifySemiProduct(None))
        self.assertFalse(self.bOWUpdaterSimple.verifySemiProduct(SmartURL("http://www.example.com/page88.html")))
        # 026 Shall be empty CounterManager correct input?
            
    def test_BOWUpdaterSimple_verify_correct_input(self):  
        """ BOWUpdaterSimple.verifySemiProduct() returns true if called with a CounterManager instance."""
        self.assertTrue(self.bOWUpdaterSimple.verifySemiProduct(CounterManager()))
    
    def test_BOWUpdaterSimple_produce(self): 
        """ BOWUpdaterSimple.produce() """
        # 026 check how many times was called FilesAdaptor.updateBOW()
        cnt=self.files._updateDBcounter
        self.bOWUpdaterSimple.produce(CounterManager())
        cnt2=self.files._updateDBcounter
        self.assertEqual(cnt2-cnt, 1)
        
if __name__ == "__main__":
    
    #whole=False
    whole=True
    
    if whole:
        unittest.main()   