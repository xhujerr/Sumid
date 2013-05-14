"""Unit test for bow.py"""
# http://bayes.colorado.edu/PythonGuidelines.html#unit_tests

__version__="0.27"


# Set path for thirdparty imports
import sys
sys.path.append('../thirdparty/')
sys.path.append('../src/')

import unittest
import mocklegacy
from mock import Mock
from Queue import Queue
from threading import Condition
from bow import BOWBuilderSimple, BOWUpdaterSimple, BOWBuilderComplex
from linklist import SmartURL
from miscutil import CounterManager


class TextLinklistParserMock(Mock):
    _linklistEOF=False
    cx=0
    
    def __init__(self):
        super(TextLinklistParserMock, self).__init__()
        #self._linklistEOF=False # 026 It's expected that this variable will be accessed as public within module.
        #self.cx=0
        
    
    @ property
    def linklistEOF(self):
        return self._linklistEOF
    
    def next(self):
        self.cx+=1 # 026 If not outside, infinite cycle.
        if not self.linklistEOF:
            url=SmartURL("http://www.example.com/page%i.html"%(self.cx))
            return url
        else: return None

class TextLinklistParserMockForComplex(TextLinklistParserMock):

    def next(self):
        self.cx+=1 # 026 If not outside, infinite cycle.
        if not self.linklistEOF:
            url=SmartURL("http://www.server%i-example.com/directory/page%i.html?p1=static&p2=dyn%i"%(self.cx,self.cx,self.cx))
            return url
        else: return None
        
class SettingsDummy(object):
    linkListSpcSymbols=['@','#']
    urlWordsSeparators=[',',' ','.','/','-','_','?','&','=']   
    commonWords=["","http:","www","html","com","php","net","org","co","uk","htm","aspx","cfm","asp","au","cgi"]
    bowTempSize=100     
    bowWaitTime=0
    linklistURLParts=["scheme", "netloc", "path", "params", "query", "fragment"]

    
class DebugMock(Mock):
    #Mock 0.8.0 documentation
    #http://www.voidspace.org.uk/python/mock/mock.html
    # mockLegacy used because in mock 0.8 is required "spec" which breaks this class.
    mainLogger=None
    ThreadAwareLogger=None
    
    def __init__(self):
        #super(self.__class__, self).__init__()
        super(DebugMock, self).__init__()
        self.mainLogger=LoggerMock()
        self.ThreadAwareLogger=LoggerMock()
        
        
    def printHeader(self):
        # 027 Printing header output suppressed.
        pass

class LoggerMock(Mock):
            
    def debug(self,argument):
        super(LoggerMock, self).__init__()
        # 027 Printing debug messages disabled. 
        #print argument
    
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
            # 027 The formula 73+1 means 73 dynamicly changed counters plus one static of value 73.
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
        self.assertEqual(item.title, "word")
    
    def test_BOWBuilderSimple_initializeCounters(self):
        """ initializeCounters just add attribute counters into BOWBuilderSimple (which is of type CounterManager). """
        # 027 The problem to test this is, that is already added BOWBuilderSimple in init().
        self.bOWBuilderSimple.counters=None
        self.bOWBuilderSimple.initializeCounters()
        self.assertIsInstance(self.bOWBuilderSimple.counters, CounterManager)
        
    def test_BOWBuilderSimple_finalize(self):
        """ Finalize just puts actual counters into output queue without respect how many has accumulated. """
        outputQueueSizeInitial=self.outputQueue.qsize()
        self.bOWBuilderSimple.finalize()
        self.assertEqual(outputQueueSizeInitial+1, self.outputQueue.qsize())
        

class BOWBuilderComplexWithDummySettings(BOWBuilderComplex):
    # 027 self setting is used in init, resp in initializeCounters so it's not possible to add them later.
    def customInitialization(self):
        self.parser=self.kwargs['parserInstance']
        self.settings=SettingsDummy()
        self.debug=DebugMock()
        self.initializeCounters()

class BOWBuilderComplexTest(unittest.TestCase): 
    
    def setUp(self):
        self.parserInstance=TextLinklistParserMockForComplex()
        self.outputQueue=Queue()
        outputCondition=Condition()
        self.bOWBuilderComplex=BOWBuilderComplexWithDummySettings(None,self.outputQueue,None,outputCondition,parserInstance=self.parserInstance)        
    
    def tearDown(self):
        del self.bOWBuilderComplex
        del self.parserInstance

    def test_BOWBuilderComplex_produce_data(self):
        """ Into counters goes the result of parser.words() """
        # Just counts the words restricted on group ["scheme", "netloc", "path", "params", "query", "fragment"]. 
        url=SmartURL("http://www.kosek.cz/clanky/kosek/kosek-swn-xml/ar02s17.html?bla=blabla&gla=blabla")
        expectedNetloc={"kosek":1,"cz":1}
        expectedPath={"clanky":1,"kosek":2,"swn":1,"xml":1,"ar02s17":1}
        expectedQuery={"bla":1,"blabla":2,"gla":1}
        # 026 Tests also that "http:","","www","html" are left out.
        # 026 Tests also that kosek is count twice.
        self.bOWBuilderComplex.produce(url)        
        # 027 bOWBuilderComplex.counters is a dictionary with keys "netloc", "path", "params", "query", "fragment"
        result=self.bOWBuilderComplex.counters
        self.assertDictEqual(result["netloc"].counters,expectedNetloc)
        self.assertDictEqual(result["path"].counters,expectedPath)
        self.assertDictEqual(result["query"].counters,expectedQuery)

    def _showWhatIsInQueue(self,queue):
        while not queue.empty():
            item=queue.get()
            print "\n"
            print "%s %i"%(item.title,item.NumberOfCounters)
    
    def test_BOWBuilderComplex_produce_incremental(self):
        """ BOWBuilderComplex.produce() is incrementally stuffed with data, while at some places are performed asserts. """
        while self.parserInstance.cx<205:
            semiProduct = self.bOWBuilderComplex.consume()
            if self.parserInstance.cx >= 204: self.parserInstance._linklistEOF=True
            if self.bOWBuilderComplex.verifySemiProduct(semiProduct):
                # 026 Verification requires due to async in incrementing. 
                self.bOWBuilderComplex.produce(semiProduct)
            if self.parserInstance.cx == 73: 
                self.assertEqual(self.bOWBuilderComplex.counters["netloc"].NumberOfCounters, 73+1)
                self.assertEqual(self.bOWBuilderComplex.counters["netloc"].value("example"),73)
                self.assertEqual(self.bOWBuilderComplex.counters["path"].NumberOfCounters, 73+1)
                self.assertEqual(self.bOWBuilderComplex.counters["path"].value("directory"),73)  
                self.assertEqual(self.bOWBuilderComplex.counters["query"].NumberOfCounters, 73+3) # 027 static + p1 + p2 = 3
                self.assertEqual(self.bOWBuilderComplex.counters["query"].value("static"),73)                                
            # 027 Must be on 97, coz query has +3 counters. Which means that on cx=97 the NumberOfCounter is already 100.
            if self.parserInstance.cx == 96: self.assertTrue(self.outputQueue.empty())
            if self.parserInstance.cx == 97: self.assertEqual(self.outputQueue.qsize(),1)
            if self.parserInstance.cx == 98: self.assertEqual(self.outputQueue.qsize(),1)
            if self.parserInstance.cx == 99: self.assertEqual(self.outputQueue.qsize(),3)
            if self.parserInstance.cx == 100: self.assertEqual(self.outputQueue.qsize(),3)
            if self.parserInstance.cx == 101:
                # self._showWhatIsInQueue(self.outputQueue) # 027 This method is destructive. 
                # 027 Counting new netloc and path starts at cx==99.
                self.assertEqual(self.bOWBuilderComplex.counters["netloc"].NumberOfCounters, 1+1+1)
                self.assertEqual(self.bOWBuilderComplex.counters["netloc"].value("example"),2)
                self.assertEqual(self.bOWBuilderComplex.counters["path"].NumberOfCounters, 1+1+1)
                self.assertEqual(self.bOWBuilderComplex.counters["path"].value("directory"),2)  
                # 027 +3 Because the counters get emptied earlier and accumulate words since cx==97 already.
                self.assertEqual(self.bOWBuilderComplex.counters["query"].NumberOfCounters, 1+3+3) 
                # 027 Also static is count from 97 already.
                self.assertEqual(self.bOWBuilderComplex.counters["query"].value("static"),1+3)            
            if self.parserInstance.cx == 173: 
                self.assertEqual(self.bOWBuilderComplex.counters["netloc"].NumberOfCounters, 73+1+1)
                self.assertEqual(self.bOWBuilderComplex.counters["netloc"].value("example"),73+1)
                self.assertEqual(self.bOWBuilderComplex.counters["path"].NumberOfCounters, 73+1+1)
                self.assertEqual(self.bOWBuilderComplex.counters["path"].value("directory"),73+1)  
                # 027 +3 Because the counters get emptied earlier and accumulate words since cx==97 already.
                self.assertEqual(self.bOWBuilderComplex.counters["query"].NumberOfCounters, 73+3+3)
                # 027 Also static is count from 97 already.
                self.assertEqual(self.bOWBuilderComplex.counters["query"].value("static"),73+3)    
            # 027 After two hundreds the items are enqueued even earlier (coz of the +3 feature).   
            if self.parserInstance.cx == 193:
                # 027 Three items: CounterManager.title="querry", CounterManager.title="netloc", CounterManager.title="path"
                #self._showWhatIsInQueue(self.outputQueue)
                self.assertEqual(self.outputQueue.qsize(),3) 
            # 027 The fourth item (CounterManager.title="querry") arrives on 196
            if self.parserInstance.cx == 194: self.assertEqual(self.outputQueue.qsize(),4)
            if self.parserInstance.cx == 197: self.assertEqual(self.outputQueue.qsize(),4)
            if self.parserInstance.cx == 198: self.assertEqual(self.outputQueue.qsize(),6)
            if self.parserInstance.cx == 201: self.assertEqual(self.outputQueue.qsize(),6)
            if self.parserInstance.cx == 201: 
                # 027 Netloc and path starts to count from 198, which means three already at 201.
                self.assertEqual(self.bOWBuilderComplex.counters["netloc"].NumberOfCounters, 1+3)
                self.assertEqual(self.bOWBuilderComplex.counters["netloc"].value("example"),3)
                self.assertEqual(self.bOWBuilderComplex.counters["path"].NumberOfCounters, 1+3)
                self.assertEqual(self.bOWBuilderComplex.counters["path"].value("directory"),3)  
                # 027 Starts accumulate earlier.
                self.assertEqual(self.bOWBuilderComplex.counters["query"].NumberOfCounters, 1+3+6)
                self.assertEqual(self.bOWBuilderComplex.counters["query"].value("static"),1+6)             
            if self.parserInstance.cx == 204:
                #self._showWhatIsInQueue(self.outputQueue) 
                self.assertEqual(self.outputQueue.qsize(),11)
        # Test if item in queue is correct:
        item=self.outputQueue.get()
        self.assertTrue(isinstance(item,CounterManager))

    def test_BOWBuilderComplex_initializeCounters(self):
        """ initializeCounters just add attribute counters into bOWBuilderComplex (which is dict of CounterManager). """
        # 027 The problem to test this is, that counters are already added bOWBuilderComplex in init().
        self.bOWBuilderComplex.counters=None
        self.bOWBuilderComplex.initializeCounters()
        self.assertIsInstance(self.bOWBuilderComplex.counters, dict)
        allowedCounterNames=["netloc", "path", "params", "query", "fragment"]
        for counterName in self.bOWBuilderComplex.counters.keys():
            self.assertIsInstance(self.bOWBuilderComplex.counters[counterName], CounterManager)
            self.assertIn(counterName, allowedCounterNames)
        
    def test_BOWBuilderComplex_finalize(self):
        """ Finalize just puts actual counters into output queue without respect how many has accumulated. """
        outputQueueSizeInitial=self.outputQueue.qsize()
        self.bOWBuilderComplex.finalize()
        self.assertEqual(outputQueueSizeInitial+5, self.outputQueue.qsize())
        allowedCounterNames=["netloc", "path", "params", "query", "fragment"]
        while not self.outputQueue.empty():
            item=self.outputQueue.get()
            self.assertIsInstance(item, CounterManager)
            self.assertIn(item.title, allowedCounterNames)
 
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