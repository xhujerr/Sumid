"""Unit test for sumid.py"""
# http://bayes.colorado.edu/PythonGuidelines.html#unit_tests

__version__="0.26"

import unittest
import sumid
from comptree import NodeProxy
from miscutil import Debug, Settings, Shared, CounterManager
import inspect
import logging
from mock import Mock
#import tempfile #026
import os
import os.path
import time

#moduleSetUp=False

def setUpModule():
    if not hasattr(Shared,"settings") or not hasattr(Shared,"debug"): #not moduleSetUp: # 026 The condition doesn't work in pyDev coz global vars aren't loaded. 
        print "Setting up the module."
        settings=Settings()
        settings.pathStorage=UnixPathStorageMock()
        # settings.mainINIFilePath="/media/KINGSTON/Sumid/src/testing.ini" # 026 For future - testing could have other settings.
        # settings.loadAdaptive("all") # 026 Conflicts with args loaded by unittest.
        settings.loadAdaptive("INI","sumid")
        settings.workDir="/home/sumid.results/unittests/"
        settings.logDir="/home/sumid.results/unittests/"
        Shared.settings=settings
        debug=Debug(settings)
        Shared.debug=debug
    #moduleSetUp=True  # 026
 
class HydraDummy(sumid.Hydra):
    _shallContinue=False
    def shallContinue(self,strategyName):
        return self._shallContinue
    def rejuvernateThreads(self):
        pass

class HydraMock(Mock):
    def __init__(self):
        self.filesAdaptorInstance=FilesAdaptorMock()
        self.shallContinue=sumid.Hydra.shallContinue

class DebugDummy(Debug):
    def __init__(self): pass
    def printHeader(self): pass

class ProducerDummy(sumid.AbstractProducer):
    """ This is to test abstract producer which can't be instantiated."""
    def customInitialization(self):
        self.shallContinue=False
        return True
    
    def produce(self,semiProduct):
        while self.shallContinue:
            time.sleep(1)

class ProducerCausingException(sumid.AbstractProducer):
    """ This is to test abstract producer which can't be instantiated."""
    # 026 Shall act as a ComptreeProcessor. Esp connected to termination.

    def customInitialization(self):
        self.errorsThrownInConsume=1
        self.errorsThrownInProduce=1
        if hasattr(self.hydra,"_shallContinue"):
            self.hydra._shallContinue=True
        else:
            sumid.CompTreeProducer.running=1
        
    def setToTermination(self):
        if hasattr(self.hydra,"_shallContinue"):
            self.hydra._shallContinue=False
        else:
            #self.linksQueue.queue.clear() 
            #self.nodeQueue.queue.clear() 
            self.inputQueue.queue.clear()
            self.outputQueue.queue.clear()
            sumid.CompTreeProducer.running=0   
            #self.hydra.linksQueue.queue.clear()        
            #self.hydra.nodeQueue.queue.clear()
            self.hydra.allThreadsStarted=True         
    
    def consume(self):            
        while self.errorsThrownInConsume:
            self.errorsThrownInConsume-=1
            raise ValueError("Caused deliberately for testing purpose")
        return object()
            
    def produce(self,semiProduct):
        while self.errorsThrownInProduce:
            self.errorsThrownInProduce-=1
            raise AttributeError("Caused deliberately for testing purpose")  
        self.setToTermination()   

class FilesAdaptorMock(Mock):

    def __init__(self,numberOfLinesInFile=0):
        #self.pseudofile=tempfile.NamedTemporaryFile() # 026
        self.pseudofile=[]
        self.addLinesToFile(numberOfLinesInFile)
        #self.__class__.__name__=sumid.FilesAdaptor.__class__.__name__
        self.fileProcessedAnswer=True # 026 True/False/Real
        self.linklist=None
    
    def addLinesToFile(self,howMany,counter=0):
        #self.pseudofile.seek(os.SEEK_END) #026
        for i in range(howMany):
            #self.pseudofile+="http://www.example.com/file%03d.html\n"%(i) #026
            #self.pseudofile.write("http://www.example.com/file%03d.html\n"%(i)) #026
            self.pseudofile.append("http://www.example.com/file%03d.html\n"%(i))
            
    def loadPartOfLinkList(self,numberOfLines=None):
        """ In this mock input file is ignored. Always is used pseudofile. """
        if not numberOfLines: numberOfLines=3
        result=[]
        cx=0
        for line in self.pseudofile: #026
            cx+=1
            result.append(line)
            if cx>=numberOfLines: break
        #self.pseudofile.seek(0) #026 # There's some bug which makes first field empty.
        #for line in range(numberOfLines):
        #    result.append(self.pseudofile.readline())
        return result

    def loadPartOfLinkListSplitted(self,numberOfLines=None):
        """ In this mock input file is ignored. Always is used pseudofile. """
        if not numberOfLines: numberOfLines=3
        result=[]
        cx=0
        for line in self.pseudofile: #026
            cx+=1
            result.append(line.split('/'))
            if cx>=numberOfLines: break
        #self.pseudofile.seek(0) #026 # There's some bug which makes first field empty.
        #for line in range(numberOfLines):
        #    result.append(self.pseudofile.readline())
        return result
    
    def fileProcessed(self,file):
        if self.fileProcessedAnswer=="Real": return sumid.FilesAdaptor.fileProcessed(self,file) 
        elif not self.fileProcessedAnswer: return False
        else: return True

    def writeFile(self,fileLink,fileBuffer,testChars=''):
        return True
            
class LinklistMock(Mock):
    def parse2Queue(self,linklist=None):
        result=sumid.Queue()
        howMany=5
        for i in range(howMany):
            result.put(["http:","","www.example.com","link%03d.html"%(i)])
        return result
    
class UnixPathStorageMock(Mock):
    def workDir(self):
        return "/home/sumid.results/unittests"
    
    def composeURL(self,splitedURL):
        return "/".join(splitedURL)

class Hydra_ShallContinue(unittest.TestCase): 
    """ Hydra does decide if a thread shall continue, or terminate. """ 
    # There are four kinds of threads: LinklistSupplier, CompTreeProducer, CompTreeProcessor and CounterSupervisor
    # Decision making gonna be applied as a strategy pattern.
    
    # LinklistSupplier shall continue if:
    # - there still are some unprocessed links in linklist.  
    
    # CompTreeProducer shall continue if:
    # - the linksQueue is not empty
    # - LinklistSupplier thread is running.
    # - LinklistSupplier didn't started yet.
    
    # CompTreeProcessor shall continue if:
    # - the linksQueue or nodeQueue is not empty
    # - LinklistSupplier or CompTreeProducer thread is running.
    # - LinklistSupplier or CompTreeProducer didn't started yet.

    # CounterSupervisor shall continue if:    
    # - the linksQueue or nodeQueue or counterManagerQueue is not empty
    # - LinklistSupplier or CompTreeProducer or CompTreeProcessor thread is running.
    # - LinklistSupplier or CompTreeProducer or CompTreeProcessor didn't started yet.
    
    def setUp(self):
        sumid.LinklistSupplier.running=0
        sumid.CompTreeProducer.running=0
        sumid.CompTreeProcessor.running=0
        sumid.CounterSupervisor.running=0
 
        self.hydra=sumid.Hydra()
        self.hydra.allThreadsStarted=True
        #self.hydraMock=HydraMock()
        self.hydra.filesAdaptorInstance=FilesAdaptorMock()
        
        self.linksQueue=sumid.Queue(14)
        self.nodeQueue=sumid.Queue(7)
        self.comptreeResults=sumid.Queue()
        self.hydra.connectProductQueues(self.linksQueue,self.nodeQueue,self.comptreeResults)
 
    # If wrong strategy applied raise AttributeError
    def test_shallContinue_wrongStrategy(self):
        self.assertRaises(AttributeError,self.hydra.shallContinue,"WrongStrategy")

    # LinklistSupplier shall continue if:
    # - there still are some unprocessed links in linklist.  
    def test_LinklistSupplier_shallContinue_linklistProcessed(self):
        #self.hydra.filesAdaptorInstance.pseudofile=[]
        self.hydra.filesAdaptorInstance.fileProcessedAnswer=True
        self.assertFalse(self.hydra.shallContinue("LinklistSupplierStrategy"))
    
    def test_LinklistSupplier_shallContinue_linklistNotProcessed(self):
        self.hydra.filesAdaptorInstance.fileProcessedAnswer=False
        self.assertTrue(self.hydra.shallContinue("LinklistSupplierStrategy"))

    # CompTreeProducer shall continue if:
    # - the linksQueue is not empty
    # - LinklistSupplier thread is running.
    # - LinklistSupplier didn't started yet. # Hydra.allThreadsStarted
    
    def test_CompTreeProducer_linksQueue_notEmpty(self):
        self.linksQueue.put(object())
        # Clear others
        self.nodeQueue.queue.clear() 
        self.comptreeResults.queue.clear()
        # All threads down:
        sumid.LinklistSupplier.running=0
        sumid.CompTreeProducer.running=0
        sumid.CompTreeProcessor.running=0
        self.assertTrue(self.hydra.shallContinue("CompTreeProducerStrategy"))
 
    def test_CompTreeProducer_LinklistSupplier_running(self):
        # Clear all queues
        self.linksQueue.queue.clear()
        self.nodeQueue.queue.clear() 
        self.comptreeResults.queue.clear()
        # LinklistSupplier running
        sumid.LinklistSupplier.running=1
        # Other threads down:
        sumid.CompTreeProducer.running=0
        sumid.CompTreeProcessor.running=0        
        self.assertTrue(self.hydra.shallContinue("CompTreeProducerStrategy"))
        
    def test_CompTreeProducer_shallEnd(self):
        # Clear all queues
        self.linksQueue.queue.clear()
        self.nodeQueue.queue.clear() 
        self.comptreeResults.queue.clear()  
        # All threads down:
        sumid.LinklistSupplier.running=0
        sumid.CompTreeProducer.running=0
        sumid.CompTreeProcessor.running=0
        self.assertFalse(self.hydra.shallContinue("CompTreeProducerStrategy"))

    def test_CompTreeProducer_notAllThreadsStarted(self):
        # Clear all queues
        self.linksQueue.queue.clear()
        self.nodeQueue.queue.clear() 
        self.comptreeResults.queue.clear()  
        # All threads down:
        sumid.LinklistSupplier.running=0
        sumid.CompTreeProducer.running=0
        sumid.CompTreeProcessor.running=0
        self.hydra.allThreadsStarted=False
        self.assertTrue(self.hydra.shallContinue("CompTreeProducerStrategy"))

    # CompTreeProcessor shall continue if:
    # - the linksQueue or nodeQueue is not empty
    # - LinklistSupplier or CompTreeProducer thread is running.
    # - LinklistSupplier or CompTreeProducer didn't started yet.

    def test_CompTreeProcessor_linksQueue_notEmpty(self):
        self.linksQueue.put(object())
        # Clear others
        self.nodeQueue.queue.clear() 
        self.comptreeResults.queue.clear()
        # All threads down:
        sumid.LinklistSupplier.running=0
        sumid.CompTreeProducer.running=0
        sumid.CompTreeProcessor.running=0
        self.assertTrue(self.hydra.shallContinue("CompTreeProcessorStrategy"))

    def test_CompTreeProcessor_nodeQueue_notEmpty(self):
        self.nodeQueue.put(object())
        # Clear others
        self.linksQueue.queue.clear()
        self.comptreeResults.queue.clear()
        # All threads down:
        sumid.LinklistSupplier.running=0
        sumid.CompTreeProducer.running=0
        sumid.CompTreeProcessor.running=0
        self.assertTrue(self.hydra.shallContinue("CompTreeProcessorStrategy"))            

    def test_CompTreeProcessor_CompTreeProducer_running(self):
        # Clear others
        self.linksQueue.queue.clear()
        self.nodeQueue.queue.clear()
        self.comptreeResults.queue.clear()
        # All threads down:
        sumid.LinklistSupplier.running=0
        sumid.CompTreeProducer.running=1
        sumid.CompTreeProcessor.running=0
        self.assertTrue(self.hydra.shallContinue("CompTreeProcessorStrategy"))  

    def test_CompTreeProcessor_shallEnd(self):
        # Clear all queues
        self.linksQueue.queue.clear()
        self.nodeQueue.queue.clear() 
        self.comptreeResults.put(object())
        # All threads down:
        sumid.LinklistSupplier.running=1
        sumid.CompTreeProducer.running=0
        sumid.CompTreeProcessor.running=5
        self.assertTrue(self.hydra.shallContinue("CompTreeProducerStrategy"))

    def test_CompTreeProcessor_notAllThreadsStarted(self):
        # Clear all queues
        self.linksQueue.queue.clear()
        self.nodeQueue.queue.clear() 
        self.comptreeResults.queue.clear()  
        # All threads down:
        sumid.LinklistSupplier.running=0
        sumid.CompTreeProducer.running=0
        sumid.CompTreeProcessor.running=0
        self.hydra.allThreadsStarted=False
        self.assertTrue(self.hydra.shallContinue("CompTreeProducerStrategy"))
 
    # CounterSupervisor shall continue if:    
    # - the linksQueue or nodeQueue or counterManagerQueue is not empty
    def test_shallContinue_linksQueue_NotEmpty(self):
        self.linksQueue.put(object())
        # Clear others
        self.nodeQueue.queue.clear() 
        self.comptreeResults.queue.clear()
        # All threads down:
        sumid.LinklistSupplier.running=0
        sumid.CompTreeProducer.running=0
        sumid.CompTreeProcessor.running=0
                
        self.assertEqual(self.hydra.shallContinue("CounterSupervisorStrategy"),True)
    
    def test_shallContinue_nodeQueue_NotEmpty(self):
        self.nodeQueue.put(object())
        # Clear others
        self.linksQueue.queue.clear() 
        self.comptreeResults.queue.clear()
        # All threads down:
        sumid.LinklistSupplier.running=0
        sumid.CompTreeProducer.running=0
        sumid.CompTreeProcessor.running=0
                
        self.assertEqual(self.hydra.shallContinue("CounterSupervisorStrategy"),True)
        
    def test_shallContinue_comptreeResults_NotEmpty(self):
        self.comptreeResults.put(object())
        # Clear others
        self.linksQueue.queue.clear() 
        self.nodeQueue.queue.clear() 
        # All threads down:
        sumid.LinklistSupplier.running=0
        sumid.CompTreeProducer.running=0
        sumid.CompTreeProcessor.running=0
                
        self.assertEqual(self.hydra.shallContinue("CounterSupervisorStrategy"),True)
    
    # - LinklistSupplier or CompTreeProducer or CompTreeProcessor thread is running.

    def test_shallContinue_LinklistSupplier_Running(self):
        # All threads already started:
        self.hydra.allThreadsStarted=True
        # Empty all queues   
        self.linksQueue.queue.clear() 
        self.nodeQueue.queue.clear() 
        self.comptreeResults.queue.clear() 
        
        sumid.LinklistSupplier.running=1
        sumid.CompTreeProducer.running=0
        sumid.CompTreeProcessor.running=0
                
        # Do the test - shall return True.
        self.assertEqual(self.hydra.shallContinue("CounterSupervisorStrategy"),True)
    
    def test_shallContinue_CompTreeProducer_Running(self):
        # All threads already started:
        self.hydra.allThreadsStarted=True
        # Empty all queues   
        self.linksQueue.queue.clear() 
        self.nodeQueue.queue.clear() 
        self.comptreeResults.queue.clear() 
        
        sumid.LinklistSupplier.running=0
        sumid.CompTreeProducer.running=1
        sumid.CompTreeProcessor.running=0
                
        # Do the test - shall return False.
        self.assertEqual(self.hydra.shallContinue("CounterSupervisorStrategy"),True)
                
    def test_shallContinue_CompTreeProcessor_Running(self):
        # All threads already started:
        self.hydra.allThreadsStarted=True
        # Empty all queues   
        self.linksQueue.queue.clear() 
        self.nodeQueue.queue.clear() 
        self.comptreeResults.queue.clear() 
        
        sumid.LinklistSupplier.running=0
        sumid.CompTreeProducer.running=0
        sumid.CompTreeProcessor.running=1
                
        # Do the test - shall return False.
        self.assertEqual(self.hydra.shallContinue("CounterSupervisorStrategy"),True)        
            
    # - LinklistSupplier or CompTreeProducer or CompTreeProcessor didn't started yet.
    def test_shallContinue_NotAllStarted(self):
        self.hydra.allThreadsStarted=False
        self.assertEqual(self.hydra.shallContinue("CounterSupervisorStrategy"),True)
        
    def test_shallContinue_shallTerminate(self):
        # All threads already started:
        self.hydra.allThreadsStarted=True
        sumid.LinklistSupplier.running=0
        sumid.CompTreeProducer.running=0
        sumid.CompTreeProcessor.running=0
        # Empty all queues   
        self.linksQueue.queue.clear() 
        self.nodeQueue.queue.clear() 
        self.comptreeResults.queue.clear() 
        # Do the test - shall return False.
        self.assertEqual(self.hydra.shallContinue("CounterSupervisorStrategy"),False)
    
    def tearDown(self):
        sumid.LinklistSupplier.running=0
        sumid.CompTreeProducer.running=0
        sumid.CompTreeProcessor.running=0
        sumid.CounterSupervisor.running=0

class HydraTests(unittest.TestCase):
    """ Testing facility for Hydra thread manager. """
    """
    Hydra keeps following queues: linksQueue[2*fileSipSize], nodeQueue[fileSipSize], comptreeResults. (Creates. right type, right size)
    Hydra manages instances of following classes (which are threads): LinklistSupplier, CompTreeProducer, CompTreeProcessor, CounterSupervisor
    Hydra creates instances (and destroys them) of these threads. (Because there could be more instances of a producer, producers are kept in lists, even where is no chance for multiple instances.)
    Hydra could ask FilesAdaptor if all links in linklist were processed.
    If not all links from linklist were processed Hydra must have (at least) one instance of LinklistSupplier. If no LinklistSupplier is running, Hydra starts a new instance.
    Hydra has a strategy to decide if a producer is allowed to terminate.
    In the beginning Hydra creates all instances of producers defined by settings.
    Hydra is capable to restart a producer if it dies (which also means to check).
    -- Recheck terminate clause for each strategy.
    -- Check if the number of working threads is lower then max in settings. 
    -- Start new threads where termination constrains are not fulfilled and more threads could be created.
    Each thread has its own logger and logs into a separate file. 
    (026) 
    """ 
    
    def setUp(self):
        #self.__class__.running
        self.hydra=sumid.Hydra()
        self.hydraDummy=HydraDummy()
        self.hydraDummy.settings.loadAdaptive("INI") # Shouldn't be necessary.
        self.previousRangeBackup=self.hydraDummy.settings.previousRange
        self.hydraDummy.settings.previousRange=0
        sumid.LinklistSupplier.running=2
        sumid.CompTreeProducer.running=3
        sumid.CompTreeProcessor.running=14
        sumid.CounterSupervisor.running=1  
        self.hydra.filesAdaptorInstance=FilesAdaptorMock() 
        self.hydra.linkListInstance=LinklistMock() 

    def tearDown(self):
        sumid.LinklistSupplier.running=0
        sumid.CompTreeProducer.running=0
        sumid.CompTreeProcessor.running=0
        sumid.CounterSupervisor.running=0
        self.hydraDummy.settings.previousRange=self.previousRangeBackup  

    # countThreads returns a CounterManager instance with count of each running thread of: 
    # LinklistSupplier, CompTreeProducer, CompTreeProcessor and CounterSupervisor
    def test_countRunningThreads_resultTypeCorrect(self):
        """ countThreads: Verify if method does return a CounterManager instance and contains correct counters. """
        hydraDummy=HydraDummy()
        hydraDummy.debug = DebugDummy()
        counters=hydraDummy.countRunningThreads()
        self.assertEqual(isinstance(counters,sumid.CounterManager),True)
        self.assertEqual(counters.hasCounter("LinklistSupplier"),True)
        self.assertEqual(counters.hasCounter("CompTreeProducer"),True)
        self.assertEqual(counters.hasCounter("CompTreeProcessor"),True)
        self.assertEqual(counters.hasCounter("CounterSupervisor"),True)
    
    def test_countRunningThreads_countCorrect(self):
        """ countThreads: Verify if the count is correct. """
        #Run the test
        hydraDummy=HydraDummy()
        hydraDummy.debug = DebugDummy()
        counters=hydraDummy.countRunningThreads()
        self.assertEqual(counters.value("LinklistSupplier"),2)
        self.assertEqual(counters.value("CompTreeProducer"),3)
        self.assertEqual(counters.value("CompTreeProcessor"),14)
        self.assertEqual(counters.value("CounterSupervisor"),1)
    
    def test_HydraCreatesConditions(self):
        """ Hydra creates conditions: linksAvailable, comptreeAvailable, comptreeResultsAvailable."""
        result=self.hydraDummy.createConditions()
        self.assertTrue(isinstance(result,list)) 
        
        self.assertTrue(hasattr(self.hydraDummy,"linksAvailable"))
        self.assertTrue(isinstance(self.hydraDummy.linksAvailable,sumid.EnhancedCondition))
        self.assertTrue(hasattr(self.hydraDummy,"comptreeAvailable"))
        self.assertTrue(isinstance(self.hydraDummy.comptreeAvailable,sumid.EnhancedCondition))
        self.assertTrue(hasattr(self.hydraDummy,"comptreeResultsAvailable"))
        self.assertTrue(isinstance(self.hydraDummy.comptreeResultsAvailable,sumid.threading._Condition))
    
    def test_HydraCreatesQueues(self):
        """Hydra creates linksQueue, nodeQueue and comptreeResults queues correctly. And returns product queues as a list in order: linksQueue, nodeQueue, comptreeResults"""
        # 026 obsoleted # hydra = sumid.Hydra()
        # 026 obsoleted # fileSipSize=7 # Copy paste from settings.
        # (026) Hydra could use factory method to create the queues, which are specified as input parameters. 
        # (026) The problem is how to save the results. 
        result=self.hydraDummy.createQueues()
        
        self.assertTrue(isinstance(result,list))
        
        self.assertTrue(hasattr(self.hydraDummy,"linksQueue"))
        self.assertEqual(self.hydraDummy.linksQueue.__class__,sumid.Queue)
        self.assertEqual(self.hydraDummy.linksQueue.maxsize,8)
        
        self.assertTrue(hasattr(self.hydraDummy,"nodeQueue"))
        self.assertEqual(self.hydraDummy.nodeQueue.__class__,sumid.Queue)
        self.assertEqual(self.hydraDummy.nodeQueue.maxsize,8)

        self.assertTrue(hasattr(self.hydraDummy,"comptreeResults"))
        self.assertEqual(self.hydraDummy.comptreeResults.__class__,sumid.Queue)
        self.assertEqual(self.hydraDummy.comptreeResults.maxsize,0)

    def test_HydraCreatesProducers(self):
        """ Test if Hydra creates LinklistSupplier, CompTreeProducer, CompTreeProcessor and CounterSupervisor producers correctly."""
        # (026) Hydra could use factory method to create the producers, which are specified as input parameters. 
        # (026) The problem is how to save the results. 
        # 026 So apparently the producer variables (such as hydra.linklistSupplier) are meant as lists of the instances.
        # 026 There shall be also list of lists as in queue example.
        
        # First conditions and queues have to be created
        self.hydra.createConditions()
        self.hydra.createQueues()
        self.hydra.createProducers()
            
        self.assertEqual(hasattr(self.hydra,"linklistSupplier"),True)
        self.assertEqual(len(self.hydra.linklistSupplier),1)
        for producer in self.hydra.linklistSupplier:
            self.assertEqual(isinstance(producer,sumid.LinklistSupplier),True)
            self.assertEqual(isinstance(producer,sumid.threading.Thread),True)
            self.assertTrue(hasattr(producer,"logger"))
            self.assertTrue(isinstance(producer.logger,logging.Logger))
            
        self.assertEqual(hasattr(self.hydra,"compTreeProducer"),True)
        self.assertEqual(len(self.hydra.compTreeProducer),1)
        for producer in self.hydra.compTreeProducer:
            self.assertEqual(isinstance(producer,sumid.CompTreeProducer),True)
            self.assertEqual(isinstance(producer,sumid.threading.Thread),True)
            self.assertTrue(hasattr(producer,"logger"))
            self.assertTrue(isinstance(producer.logger,logging.Logger))
            
        self.assertEqual(hasattr(self.hydra,"compTreeProcessor"),True)
        self.assertEqual(len(self.hydra.compTreeProcessor),8)
        for producer in self.hydra.compTreeProcessor:
            self.assertEqual(isinstance(producer,sumid.CompTreeProcessor),True)
            self.assertEqual(isinstance(producer,sumid.threading.Thread),True)
            self.assertTrue(hasattr(producer,"logger"))
            self.assertTrue(isinstance(producer.logger,logging.Logger))

        self.assertEqual(hasattr(self.hydra,"counterSupervisor"),True)
        self.assertEqual(len(self.hydra.counterSupervisor),1)
        for producer in self.hydra.counterSupervisor:
            self.assertEqual(isinstance(producer,sumid.CounterSupervisor),True)
            self.assertEqual(isinstance(producer,sumid.threading.Thread),True)
            self.assertTrue(hasattr(producer,"logger"))
            self.assertTrue(isinstance(producer.logger,logging.Logger))  
        
        # 026 Threads are not started here.    
        #for producerKind in self.hydra.producers:
        #    for producer in producerKind:
        #        producer.join()          

    def test_LinklistEmpty_Querry(self):
        """ Could Hydra find out if all links from linklist were processed? """
        # 026 Test should be split in two by result True/False
        hydra = sumid.Hydra()
        filesAdaptorMock=FilesAdaptorMock()
        
        filesAdaptorMock.linklist=None
        filesAdaptorMock.fileProcessedAnswer=True # 026 If used fileProcessedAnswer="Real" returns TypeError: unbound method fileProcessed() must be called with FilesAdaptor instance as first argument (got FilesAdaptorMock instance instead)
        hydra.connectFilesAdaptor(filesAdaptorMock)
        self.assertEqual(hasattr(hydra,"filesAdaptorInstance"),True)
        
        # 026 This is testing of FilesAdaptor. Shouldn't be performed in hydra test set.
        # 026 Of course nonsense to test it with FilesAdaptorMock
        self.assertTrue(hydra.filesAdaptorInstance.fileProcessed(hydra.filesAdaptorInstance.linklist)) # 026 Call should include parameter hydra.filesAdaptorInstance.linklist - but it causes error. 
    
    #def test_MinimalThreadsRunning(self):
    #    """ If not all links from linklist were processed Hydra must have (at least) one instance of LinklistSupplier. If no LinklistSupplier is running, Hydra starts a new instance. """
    #    testWritten=False
    #    self.assertTrue(testWritten)
        
        
    def test_HasStrategyToThreadTermination(self):
        """ Hydra has a strategy to decide if a producer is allowed to terminate. """
        hydra = sumid.Hydra
        #self.assertTrue(hasattr(hydra,"AbstractProducerStrategy")) # 026 Added for test_AbstractProducer_runExcept, but doesn't work anyway.
        self.assertTrue(hasattr(hydra,"LinklistSupplierStrategy"))
        self.assertTrue(hasattr(hydra,"CompTreeProducerStrategy"))
        self.assertTrue(hasattr(hydra,"CompTreeProcessorStrategy"))
        self.assertTrue(hasattr(hydra,"CounterSupervisorStrategy"))

    def s_test_HydraStartProducers(self): #026 Gets stuck - probably in joining.
        """In the beginning Hydra creates and starts all instances of producers defined by settings."""
        # 026 I changed my mind. Hydra is not going to create produces on startup.
        # Means in Hydra.__init__()
        # 026 Test remade to start test. 
        
        # 026 Test suspended because LinklistSupplier ran infinitely. Dunno why.
        
        hydra=HydraDummy()
        hydra.filesAdaptorInstance=FilesAdaptorMock() 
        hydra.linkListInstance=LinklistMock() 
        hydra._shallContinue=True
        # First conditions and queues have to be created
        hydra.createConditions()
        hydra.createQueues()
        hydra.createProducers()
        hydra.startProducers()
        
        self.assertEqual(sumid.threading.activeCount(),12) # Expected to be 12 (1+1+8+1+main). Maybe main doesn't count. 
        self.assertTrue(hydra.allThreadsStarted)
        hydra._shallContinue=False
        
        #for producerKind in self.hydra.producers:
        #    for producer in producerKind:
        #        producer.join()
        
        hydra.joinProducers()  
        
        self.assertEqual(sumid.threading.activeCount(),1)
                
    def s_test_HydraCheckThreads(self): # 026 Gets stuck.
        """Hydra is capable to restart a producer if it dies (which also means to check)."""
        """
        -- Recheck terminate clause for each strategy.
        -- Check if the number of working threads is lower then max in settings. 
        -- Start new threads where termination constrains are not fulfilled and more threads could be created.
        
        -- Doesn't create producer, if shallContinue condition is not fullfilled.
        -- Doesn't touch the existing producers.
        -- Not only create missing thread but it also starts it.
        
        It is far more complex: 
        - If the thread ends, it still remains in the hydra's list of producers.
        -- This can be useful. It is not necessary to recreate the thread. Just re-start.
        -- Threads cannot be restarted. You must re-create the Thread in order to start it again.
        -- So hydra.rejuvernateThreads has to purge all inactive threads from the list.
        So rejuvernateThreads dels the inactive threads first.
        """ 
        hydra = sumid.Hydra()
        hydra.filesAdaptorInstance=FilesAdaptorMock() 
        hydra.linkListInstance=LinklistMock() 
        if not hasattr(hydra,"linksQueue"):
            hydra.createConditions()
            hydra.createQueues()
        if not hasattr(hydra,"producers"):
            hydra.linklistSupplier=[]
            hydra.compTreeProducer=[]
            hydra.compTreeProcessor=[]
            hydra.counterSupervisor=[]
            hydra.producers=[hydra.linklistSupplier,hydra.compTreeProducer,hydra.compTreeProcessor,hydra.counterSupervisor]
        hydra.rejuvernateThreads()
        activeThreadCount=sumid.threading.activeCount()
        activeThreadsNames=hydra.getActiveThreadNames()
        self.assertEqual(activeThreadCount,12,"%i!=12\nActive Threads: %s"%(activeThreadCount,activeThreadsNames))
        
        for producerKind in hydra.producers:
            for producer in producerKind:
                producer.join()    
  
    def s_test_Hydra_rejuvernateThreads_shallNotContinue(self):
        """ If hydra.shallContinue() returns False, no new thread shall be created."""
        if not hasattr(self.hydra,"linksQueue"): self.hydra.createQueues()
        if not hasattr(self.hydra,"producers"): self.hydra.createProducers()
        self.hydra.filesAdaptorInstance.fileProcessedAnswer=True
        # All threads already started:
        self.hydra.allThreadsStarted=True
        # Empty all queues   
        self.hydra.linksQueue.queue.clear() 
        self.hydra.nodeQueue.queue.clear() 
        self.hydra.comptreeResults.queue.clear() 
        
        sumid.LinklistSupplier.running=0
        sumid.CompTreeProducer.running=0
        sumid.CompTreeProcessor.running=0
        sumid.CounterSupervisor.running=0
        
        countBefore=self.hydra.countRunningThreads().sumAllValues()
        self.hydra.rejuvernateThreads()
        countAfter=self.hydra.countRunningThreads().sumAllValues()
        self.assertEqual(countBefore,countAfter)
        
    def suspended_test_Hydra_rejuvernateThreads_shallRejuvernate(self):
        if not hasattr(self.hydra,"linksQueue"): self.hydra.createQueues()
        self.hydra.filesAdaptorInstance.fileProcessedAnswer=True
        # All threads already started:
        self.hydra.allThreadsStarted=True # shallContinue does rely on this. 
        # Fill all queues.   
        self.hydra.linksQueue.put(object()) 
        self.hydra.nodeQueue.put(object())
        self.hydra.comptreeResults.put(object())
        self.hydra.rejuvernateThreads()
        
        # Check if they're started, before they stop.
        allThreadsStarted=True
        for producersList in self.hydra.producers:
            for producer in producersList:
                if not producer.is_alive(): allThreadsStarted=False
        self.assertTrue(allThreadsStarted)
        
        self.assertEqual(len(self.hydra.linklistSupplier),1)
        self.assertEqual(len(self.hydra.compTreeProducer),1)
        self.assertEqual(len(self.hydra.compTreeProcessor),8)
        self.assertEqual(len(self.hydra.counterSupervisor),1)
        

  
    def test_Hydra_measureQueues(self):
        # Make sure that queues are empty.
        #self.hydraDummy.linksQueue.queue.clear()
        #self.hydraDummy.nodeQueue.queue.clear()
        #self.hydraDummy.comptreeResults.queue.clear()
        self.hydraDummy.createQueues()
        #The test.
        for index in range(6): self.hydraDummy.linksQueue.put(index)
        for index in range(3): self.hydraDummy.nodeQueue.put(index)
        for index in range(11): self.hydraDummy.comptreeResults.put(index)
        self.assertEqual(self.hydraDummy.measureQueues(),[6,3,11])
        #Clear the queues afterwards.
        self.hydraDummy.linksQueue.queue.clear()
        self.hydraDummy.nodeQueue.queue.clear()
        self.hydraDummy.comptreeResults.queue.clear()

    def test_adjustThreadWaitingTime_negativeAdjustment(self):
        """ Hydra adjustThreadWaitingTime shall return negative (just) adjustment when occupancy is more than 60%."""
        # 026 queueOcupancy=float(resultQueueLength)/float(resultQueueSize)
        timeAdjustment=self.hydra.adjustThreadWaitingTime(9, 10, 77)
        self.assertTrue(timeAdjustment<0)
    
    def test_adjustThreadWaitingTime_positiveAdjustment(self):
        """ Hydra adjustThreadWaitingTime shall return positive (just) adjustment when occupancy is less 40%."""
        timeAdjustment=self.hydra.adjustThreadWaitingTime(3, 10, 77)
        self.assertTrue(timeAdjustment>0)
    
    def test_adjustThreadWaitingTime_noAdjustment(self):
        """ Hydra adjustThreadWaitingTime shall return (just) adjustment==0 when occupancy is between 40% and 60%."""
        timeAdjustment=self.hydra.adjustThreadWaitingTime(5, 10, 77)
        self.assertTrue(timeAdjustment==0)

    def test_adjustThreadWaitingTime_tooShort(self):
        """ Hydra adjustThreadWaitingTime shall reject to adjust  time when the resulting time is under 2 seconds."""
        timeAdjustment=self.hydra.adjustThreadWaitingTime(9, 10, 3)
        self.assertTrue(timeAdjustment==0)
        timeAdjustment=self.hydra.adjustThreadWaitingTime(1, 10, 599)
        self.assertTrue(timeAdjustment==0)
              
    
class AbstractProducerTests(unittest.TestCase): 
    """ Testing facility for abstract producer/consumer. """
    """
    [TIP] Testing multi-threaded applications
    http://lists.idyll.org/pipermail/testing-in-python/2007-May/000278.html
    
    + Each producer can do both consume and produce but doesn't have to. 
    - It is expected that concrete producers override consume and produce behavior. Default implementation is empty.  
    + Each producer has access to two queues. Input queue and output queue.
    + Each producer is implemented as a thread.
    - Each concrete producer is instanciated and started by hydra. (Tested in Hydra. It is not required to forbid to create a producer by someone else.)
    - Each concrete producer has to ask hydra if he is allowed to terminate.
    + Each producer does catch all exceptions, because they don't continue into main program.
    + Each exception is logged via main logger on Error level.
    - Concrete producers are forbidden to override run method. This method is fully defined in Abstract producer. (Afaik Python has no way how to seal a method from overriding thus this is just a convention.)
    - Following concrete producers are projected: LinklistSupplier, CompTreeProducer, CompTreeProcessor, CounterSupervisor
    - Each producer sends a notification when it produce an output.
    + Each producer has a condition (notification channel) bound with both, input and output queue.
    - Each producer pauses production when the output queue is full.
    - Each producer resumes production when notified that new item was added to input queue.
    - Each producer resumes production after certain period of time.
    + Each concrete producer has a static counter in its class. 
    + Counter is increased in constructor and decreased on exception caught of if termination allowed by Hydra.
    - Result of consume method is always semiProduct.
    - Each producer has a method which does verify if semiProduct is correct. If not, produce is skipped and warning is logged via main logger. 
    - Produce method takes semiProduct as an input argument.
    - Before calling produce Producer checks if output queue is full and if it is sends notify to output condition.
    
    (026)
    
    What do you test on thread?
    - Thread doesn't finish while there still some work it has to do.
    - Thread does finish, when there is nothing to do.
    - Threads do inteact with each other.
    """
    
    def setUp(self):
        setUpModule()
        # Create parameters for a producer.
        inputQueue=sumid.Queue()
        outputQueue=sumid.Queue()
        inputCondition=sumid.EnhancedCondition()
        outputCondition=sumid.EnhancedCondition()
        # Create hydra and the producer
        self.hydra=HydraDummy()
        self.hydra.linksQueue=sumid.Queue()
        self.hydra.nodeQueue=sumid.Queue()
        self.producer=ProducerDummy(self.hydra,inputQueue,outputQueue,inputCondition,outputCondition)
        self.producerCausingException=ProducerCausingException(self.hydra,self.hydra.nodeQueue,outputQueue,inputCondition,outputCondition)        
    
    
    def test_AbstractProducer_isThread(self):
        """ Is Abstract Producer a thread? (Yes) """
        self.assertTrue(issubclass(sumid.AbstractProducer,sumid.threading.Thread))
    
    def neverWorked_test_AbstractProducer_counterIncremented(self):
        hydra=HydraDummy()
        localProducer=ProducerDummy(hydra,sumid.Queue(),sumid.Queue(),sumid.EnhancedCondition(),sumid.EnhancedCondition())
        localProducer.__class__.__name__="CompTreeProducer"
        localProducer.shallContinue=True
        self.assertEqual(localProducer.__class__.running,0)
        localProducer.start()
        hydra.allThreadsStarted=True
        self.assertEqual(localProducer.__class__.running,1)
        localProducer.shallContinue=False
        
        self.assertEqual(localProducer.__class__.running,0)
        
        localProducer.join()
    
    def test_AbstractProducer_consumeProduce(self):
        """ Each producer can do both consume and produce but doesn't have to. """
        self.assertTrue(hasattr(self.producer,"produce"))
        self.assertTrue(inspect.ismethod(self.producer.produce))
        self.assertTrue(hasattr(self.producer,"consume"))
        self.assertTrue(inspect.ismethod(self.producer.consume))

    #def test_consumeProduce_empty(self):
    #    """ Abstract producer defines consume and produce with empty default implementation."""
    #    testWritten=False
    #    self.assertTrue(testWritten)

    #def test_AbstractProducer_canTerminate(self):
    #    """ Each concrete producer has to ask hydra if he is allowed to terminate. """
    #    testWritten=False
    #    self.assertTrue(testWritten)

    def test_AbstractProducer_init(self):
        """ Constructor of each producer has input/output queue, input/output condition and increments counter."""
        # Each producer has access to two queues. Input queue and output queue.
        self.assertTrue(hasattr(self.producer,"inputQueue"))
        self.assertTrue(isinstance(self.producer.inputQueue,sumid.Queue))
        self.assertTrue(hasattr(self.producer,"outputQueue"))
        self.assertTrue(isinstance(self.producer.outputQueue,sumid.Queue))
        # Each producer has a condition (notification channel) bound with both, input and output queue.
        self.assertTrue(hasattr(self.producer,"inputQueue"))
        self.assertTrue(isinstance(self.producer.inputQueue,sumid.Queue))

    def test_AbstractProducer_runExcept(self):
        # Each producer does catch all exceptions, because they don't continue into main program.
        self.producerCausingException.__class__.__name__="CompTreeProcessor"
        self.producerCausingException.inputQueue.put(object)
        self.producerCausingException.run()
        """
        There is a few problems with this test:
        1) This create new thread and the exception takes down the thread. No effect in main thread.
        2) The loop inside Producer.Thread could be infinite.
        3) If there is nothing in the queues, consume/produce methods don't have to be called at all.
        """
        # 026 The would repeatedly throw the exceptions until hydra.shallContinue("CompTreeProcessor") returns False.
        # Setup conditions for CompTreeProcessor termination:
        # 026 Fuck that wont help !! (Doesn't run in separate thread.)
 
        
        # The result of the test is that no exception is caused. 
        self.assertTrue(True)
        # Each exception is logged via main logger on Error level. Will see in log.

        #Each producer sends a notification when it produce an output.

    def test_checkOutputQueue_notFull(self):
        # Before calling produce Producer checks if output queue is full and if it is sends notify to output condition.
        while self.producer.outputQueue.full():
            self.producer.outputQueue.get()
        self.producer.checkOutputQueue()
        # The positive result is that run doesn't stuck here.
    
    def tearDown(self):pass
    
    
class LinklistSupplierTests(unittest.TestCase):
     
    """
    LinklistSupplier:
    - Is a pure producer.
    - It gets inputs from linklist file on disk. Indirectly trough files adaptor.
    - Input queue is None, output queue contains processed and splitted links.
    - Linklist is read in sips (bursts).
    + Linklist obtains from Hydra reference to FilesAdaptor instance.
    + LinklistSupplier could request a sip(certain amount) of links from Files adaptor. (Empty and non-empty linklist.)
    - Consume returns a whole queue with processed links. # Which should be changed in future.
    - When the input file was fully processed the result if consume is empty queue.
    """
    
    def setUp(self):
        #settings = sumid.comptree.miscutil.Settings()
        
        # Create parameters for a producer.
        inputQueue=sumid.Queue()
        outputQueue=sumid.Queue(8) # 026 If the queue is infinite, adjustThreadWaitingTime raises div by zero.
        inputCondition=sumid.EnhancedCondition()
        outputCondition=sumid.EnhancedCondition()
        # Create hydra and the producers
        self.hydra=HydraDummy()   
        self.hydra.settings.loadAdaptive("INI", "sumid")
        linklistMock=LinklistMock()
        filesAdaptorMock=FilesAdaptorMock()
        filesAdaptorMock.linklist=linklistMock
        self.hydra.connectFilesAdaptor(filesAdaptorMock)  
        self.hydra.connectLinkListInstance(linklistMock)   
        self.linklistSupplier=sumid.LinklistSupplier(self.hydra,inputQueue,outputQueue,inputCondition,outputCondition)
        # 026 #self.compTreeProducer=sumid.CompTreeProducer(self.hydra,inputQueue,outputQueue,inputCondition,outputCondition)

    def isSplittedLink(self,item):
        """ This is not a unit test, but a subroutine.
        Tries if item is splitted link. """
        self.assertTrue(isinstance(item,list))
        cx=0
        for subitem in item:
            if not cx==1: self.assertTrue(isinstance(subitem,str))
            else: self.assertFalse(subitem)
            cx+=1        

# 026 Not needed Files adaptor already has the linklist.    
#    def test_LinklistSupplier_gainLinklistInstance(self):
#        linklistInstance = self.linklistSupplier.gainLinklistInstance()
#        self.assertTrue(isinstance(linklistInstance,sumid.LinklistAdaptor))
    
    def test_LinklistSupplier_gainFilesAdaptorInstance(self):
        realFilesAdaptor=sumid.FilesAdaptor(UnixPathStorageMock())
        self.linklistSupplier.connectFilesAdaptor(realFilesAdaptor) #026 self.hydra.filesAdaptorInstance)
        self.assertTrue(isinstance(self.linklistSupplier.filesAdaptorInstance,sumid.FilesAdaptor))
        
    def test_LinklistSupplier_filesAdaptorSip(self):
        # 026 This is not a test of FilesAdaptor, so mock used instead. Mock needs initialization.
        self.hydra.filesAdaptorInstance.addLinesToFile(13)
        partOfLinkList = self.hydra.filesAdaptorInstance.loadPartOfLinkListSplitted(7)
        self.assertEqual(len(partOfLinkList),7)
        for item in partOfLinkList:
            self.isSplittedLink(item)
            
    def test_LinklistSupplier_produceNonEmpty(self):
        result = self.linklistSupplier.consume()
        self.assertTrue(isinstance(result,sumid.Queue))
        self.assertTrue(result.qsize())
        part=result.get()
        subpartCounter=0
        for subpart in part:
            if not subpartCounter==1: self.assertTrue(subpart)
            else: self.assertEqual(subpart,"")
            subpartCounter+=1
 
    def test_LinklistSupplier_verifySemiproduct_isNotQueue(self):
        """ Linklist supplier semiproduct must be a queue instance."""
        semiProduct=object()
        result=self.linklistSupplier.verifySemiProduct(semiProduct)
        self.assertFalse(result)

    def test_LinklistSupplier_verifySemiproduct_isEmpty(self):
        """ Linklist supplier produce must not return empty queue. """
        semiProduct=sumid.Queue()
        result=self.linklistSupplier.verifySemiProduct(semiProduct)
        self.assertFalse(result)    

    def test_LinklistSupplier_verifySemiproduct_inproperContent(self):
        """ Linklist supplier semiproduct must not contain single string or number or a list of numbers."""
        semiProduct=sumid.Queue()
        semiProduct.put("singleString")
        self.assertFalse(self.linklistSupplier.verifySemiProduct(semiProduct))
        semiProduct.get()
        semiProduct.put(32)
        self.assertFalse(self.linklistSupplier.verifySemiProduct(semiProduct))
        semiProduct.get()
        semiProduct.put([1,2,3,4,5])
        self.assertFalse(self.linklistSupplier.verifySemiProduct(semiProduct))
        semiProduct.get()

    def test_LinklistSupplier_verifySemiproduct_properContent(self):
        """ Each field in Linklist supplier Semiproduct is a list of strings (splitted url)."""
        filesAdaptorMock=FilesAdaptorMock()
        filesAdaptorMock.addLinesToFile(13)
        partOfLinkList=filesAdaptorMock.loadPartOfLinkListSplitted(7)
        semiProduct=sumid.Queue()
        for splittedURL in partOfLinkList:
            semiProduct.put(splittedURL)
        result=self.linklistSupplier.verifySemiProduct(semiProduct)
        self.assertTrue(result) 
        
    def test_LinklistSupplier_consume(self):
        """ Result of LinklistSupplier.consume() must be queue containing some splitted urls"""
        self.hydra.filesAdaptorInstance.addLinesToFile(13)
        result = self.linklistSupplier.consume()
        self.assertTrue(isinstance(result,sumid.Queue))
        self.assertTrue(result.qsize())
        # Test if each item in queue is splitted link. 
        for index in range(result.qsize()):
            item=result.get()
            result.put(item)
            self.isSplittedLink(item)
                
    def test_LinklistSupplier_produce(self):
        """ LinklistSupplier.produce extends the output queue with splitted links by length of semiproduct.qsize() """
        # Prepare semiproduct.
        filesAdaptorMock=FilesAdaptorMock()
        filesAdaptorMock.addLinesToFile(13)
        partOfLinkList=filesAdaptorMock.loadPartOfLinkListSplitted(7)
        semiProduct=sumid.Queue()
        for splittedURL in partOfLinkList:
            semiProduct.put(splittedURL)
        # The test:
        queueLenghtBefore=self.linklistSupplier.outputQueue.qsize()
        queueLengthDifference=semiProduct.qsize()
        self.linklistSupplier.produce(semiProduct)     
        queueLenghtAfter=self.linklistSupplier.outputQueue.qsize()
        self.assertEqual(queueLengthDifference,queueLenghtAfter-queueLenghtBefore) 
        if queueLenghtBefore:
            for index in range(queueLenghtBefore): # 026 Skip item which were in queue before.
                item = self.linklistSupplier.outputQueue.get()
                self.linklistSupplier.outputQueue.put(item)
        for index in range(queueLenghtAfter-queueLenghtBefore):
            item = self.linklistSupplier.outputQueue.get()
            self.linklistSupplier.outputQueue.put(item) # 026 We already have the item, so it can be put back in queue.
            self.isSplittedLink(item) 
        return index # 026 Just to surpress warning.


class CompTreeProducerTests(unittest.TestCase):       
    """
    CompTreeProducer:
    Input is a processed url.
    Semiproduct is also processed url
    Consume only takes it from the input queue.
    Output is an object structure, a tree, which represents this url.
    """ 

    def setUp(self):
        # 026 # settings = sumid.comptree.miscutil.Settings()
        
        # Create parameters for a producer.
        self.inputQueue=sumid.Queue()
        self.outputQueue=sumid.Queue(8) # 026 If the queue is infinite, adjustThreadWaitingTime raises div by zero.
        inputCondition=sumid.EnhancedCondition()
        outputCondition=sumid.EnhancedCondition()
        # Create hydra and the producers
        self.hydra=HydraDummy()   
        self.hydra.settings.loadAdaptive("INI", "sumid")
        linklistMock=LinklistMock()
        filesAdaptorMock=FilesAdaptorMock()
        filesAdaptorMock.linklist=linklistMock
        self.hydra.connectFilesAdaptor(filesAdaptorMock)     
        self.compTreeProducer=sumid.CompTreeProducer(self.hydra,self.inputQueue,self.outputQueue,inputCondition,outputCondition)

    def isSplittedLink(self,item):
        """ This is not a unit test, but a subroutine.
        Tries if item is splitted link. """
        self.assertTrue(isinstance(item,list))
        cx=0
        for subitem in item:
            if not cx==1: self.assertTrue(isinstance(subitem,str))
            else: self.assertFalse(subitem)
            cx+=1
        # 026 If the result should be false, the asserts will stop the method sooner with negative result.
        return True  
    
    def test_CompTreeProducer_consume(self):
        """ CompTreeProducer.consume should return single splitted url. Input queue should be 1 item shorter.""" 
        # Prepare input queue.
        filesAdaptorMock=FilesAdaptorMock()
        filesAdaptorMock.addLinesToFile(11)
        partOfLinkList=filesAdaptorMock.loadPartOfLinkListSplitted(5)
        for splittedURL in partOfLinkList:
            self.inputQueue.put(splittedURL) 
        # The test
        queueSizeBefore=self.inputQueue.qsize()
        semiProduct=self.compTreeProducer.consume()
        queueSizeAfter=self.inputQueue.qsize()
        self.assertTrue(self.isSplittedLink(semiProduct))
        self.assertEqual(queueSizeBefore-1,queueSizeAfter)                 

    def test_CompTreeProducer_verifySemiproduct_isNotList(self):
        """ CompTreeProducer semiproduct must be a list instance."""
        semiProduct=object()
        result=self.compTreeProducer.verifySemiProduct(semiProduct)
        self.assertFalse(result)

    def test_CompTreeProducer_verifySemiproduct_isEmpty(self):
        """ CompTreeProducer produce must not return empty list. """
        semiProduct=[]
        result=self.compTreeProducer.verifySemiProduct(semiProduct)
        self.assertFalse(result)    

    def test_CompTreeProducer_verifySemiproduct_inproperContent(self):
        """ CompTreeProducer semiproduct must not contain single string or number or a list of numbers."""
        semiProduct="singleString"
        self.assertFalse(self.compTreeProducer.verifySemiProduct(semiProduct))
        semiProduct=32
        self.assertFalse(self.compTreeProducer.verifySemiProduct(semiProduct))
        semiProduct=[1,2,3,4,5]
        self.assertFalse(self.compTreeProducer.verifySemiProduct(semiProduct))
        
    def test_CompTreeProducer_verifySemiproduct_properContent(self):
        """ Each field in Linklist supplier Semiproduct is a list of strings (splitted url)."""
        filesAdaptorMock=FilesAdaptorMock()
        filesAdaptorMock.addLinesToFile(13)
        partOfLinkList=filesAdaptorMock.loadPartOfLinkListSplitted(7)
        semiProduct="http://www.example.com/file03.html".split('/')
        result=self.compTreeProducer.verifySemiProduct(semiProduct)
        self.assertTrue(result)     
    
    def test_CompTreeProducer_produce(self): 
        """ CompTreeProducer.produce tree object structure and saves it into outputQueue. """
        semiProduct="http://www.example.com/file03.html".split('/')  
        queueLengthBefore=self.outputQueue.qsize()
        self.compTreeProducer.produce(semiProduct)
        queueLengthAtfer=self.outputQueue.qsize()
        self.assertEqual(queueLengthBefore+1,queueLengthAtfer)
        if queueLengthBefore:
            for index in range(queueLengthBefore): # 026 Skip item which were in queue before.
                item = self.compTreeProducer.outputQueue.get()
                self.compTreeProducer.outputQueue.put(item)    
        item = self.compTreeProducer.outputQueue.get()
        self.assertTrue(isinstance(item,NodeProxy)) 
        self.compTreeProducer.outputQueue.put(item)
        # 026 This in not a test of comptree - so just the root Node is tested for type.   
     
class CompTreeProcessorTests(unittest.TestCase): 
       
    """        
    CompTreeProcessor
    Input is an url tree.
    CompTreeProcessor calls the operation.
    Output queue: CounterManager instance
    Other outputs (in competence of comptree):
    comptree logs: CSV log, hits log, miss log.
    """
    def setUp(self):        
        # Create parameters for a producer.
        self.inputQueue=sumid.Queue()
        self.outputQueue=sumid.Queue(8) # 026 If the queue is infinite, adjustThreadWaitingTime raises div by zero.
        self.nodeQueue=sumid.Queue(8)        
        inputCondition=sumid.EnhancedCondition()
        nodeCondition=sumid.EnhancedCondition()
        outputCondition=sumid.EnhancedCondition()
        
        # Create hydra and the producers
        self.hydra=HydraDummy()   
        self.hydra.settings.loadAdaptive("INI", "sumid")
        self.hydra.settings.previousRange=0 # 026 To make the test faster.
        self.hydra.settings.maxLevels=1
        self.hydra.settings.pathStorage=UnixPathStorageMock()
        #linklistMock=LinklistMock()
        filesAdaptorMock=FilesAdaptorMock()
        #filesAdaptorMock.linklist=linklistMock
        self.hydra.settings.connectFilesAdaptor(filesAdaptorMock) # Files adaptor needed by LeafProxy.operate() to write distant file.     
        self.compTreeProducer=sumid.CompTreeProducer(self.hydra,self.inputQueue,self.nodeQueue,inputCondition,nodeCondition)
        self.compTreeProcessor=sumid.CompTreeProcessor(self.hydra,self.nodeQueue,self.outputQueue,nodeCondition,outputCondition) 
        
    def tearDown(self):
        # 026 cannot join thread before it is started
        #self.compTreeProducer.join()
        #self.compTreeProcessor.join()
        pass

    def test_CompTreeProcessor_consume(self):
        """ CompTreeProcessor.consume() should return a URL tree as a result. Input queue should be 1 item shorter. """
        # CompTreeProducer is needed to produce input data for CompTreeProcessor.
        semiProduct="http://www.example.com/file03.html".split('/')
        self.compTreeProducer.produce(semiProduct)
        inputQueueLenghtBefore=self.nodeQueue.qsize()
        semiProduct=self.compTreeProcessor.consume() # This is different semiProduct: URL Tree
        inputQueueLenghtAfter=self.nodeQueue.qsize()
        self.assertEqual(inputQueueLenghtBefore-1,inputQueueLenghtAfter)
        self.assertTrue(isinstance(semiProduct,NodeProxy)) 
        # 026 This in not a test of comptree - so just the root Node is tested for type.  
        
    def test_CompTreeProducer_verifySemiproduct_Empty(self): 
        """CompTreeProducer.verifySemiproduct will return false if the tree is empty."""
        self.assertFalse(self.compTreeProcessor.verifySemiProduct(None))
              
    def test_CompTreeProducer_verifySemiproduct_properContent(self):
        """CompTreeProducer.verifySemiproduct will return true if it receives URL Tree"""
        semiProduct="http://www.example.com/file03.html".split('/')
        self.compTreeProducer.produce(semiProduct)
        semiProduct=self.compTreeProcessor.consume()
        self.assertTrue(self.compTreeProcessor.verifySemiProduct(semiProduct))

        
    def test_CompTreeProcessor_produce_NonExistingURL(self):
        """ CompTreeProcessor.produce() adds one empty counter manager instance to output queue. Output queue is 1 item longer."""
        # This test takes long to timeout.
        semiProduct="http://www.example.com/file03.html".split('/')
        self.compTreeProducer.produce(semiProduct)
        semiProduct=self.compTreeProcessor.consume()
        outputQueueLenghtBefore=self.outputQueue.qsize()
        self.compTreeProcessor.produce(semiProduct)
        outputQueueLenghtAfter=self.outputQueue.qsize()
        self.assertEqual(outputQueueLenghtBefore+1,outputQueueLenghtAfter)
        item=self.outputQueue.get()
        self.assertTrue(isinstance(item,sumid.CounterManager))
        self.outputQueue.put(item)

    def test_CompTreeProcessor_produce_existingURL(self):
        """ CompTreeProcessor.produce() adds one counter manager instance to output queue. Output queue is 1 item longer."""
        semiProduct="http://ocw.mit.edu/ans7870/18/18.013a/textbook/HTML/tools/tools08.html".split('/')
        self.compTreeProducer.produce(semiProduct)
        semiProduct=self.compTreeProcessor.consume()
        outputQueueLenghtBefore=self.outputQueue.qsize()
        self.compTreeProcessor.produce(semiProduct)
        outputQueueLenghtAfter=self.outputQueue.qsize()
        self.assertEqual(outputQueueLenghtBefore+1,outputQueueLenghtAfter)
        item=self.outputQueue.get()
        self.assertTrue(isinstance(item,sumid.CounterManager))
        self.outputQueue.put(item)


class CounterSupervisorTests(unittest.TestCase):       
    """
    CounterSupervisor
    Is a pure consumer. 026 Well not really :-)
    Process and sums the counters.
    Writes the counters to disk.
    Measures performance.
    """

    def setUp(self):
        # Create parameters for a producer.
        inputCondition=sumid.EnhancedCondition()
        # Create hydra and the producers
        self.hydra=HydraDummy()   
        self.hydra.createQueues()
        self.counterSupervisor=sumid.CounterSupervisor(self.hydra,self.hydra.comptreeResults,None,inputCondition,None)

    def test_counterSupervisor_consume(self):
        """ counterSupervisor.consume Returns a counter supervisor. The input queue is 1 item shorter. """
        counterManager=sumid.CounterManager()
        counterManager.addCounters(self.hydra.settings.defaultCounters)
        self.hydra.comptreeResults.put(counterManager)
        inputQueueLenghtBefore=self.hydra.comptreeResults.qsize()
        semiProduct=self.counterSupervisor.consume() # This is different semiProduct: URL Tree
        inputQueueLenghtAfter=self.hydra.comptreeResults.qsize()
        self.assertEqual(inputQueueLenghtBefore-1,inputQueueLenghtAfter)
        self.assertTrue(isinstance(semiProduct,sumid.CounterManager))

    def test_counterSupervisor_verifySemiproduct_Empty(self): 
        """counterSupervisor.verifySemiproduct will return false if the semiProduct is empty."""
        self.assertFalse(self.counterSupervisor.verifySemiProduct(None))
              
    def test_counterSupervisor_verifySemiproduct_properContent(self):
        """ counterSupervisor.verifySemiproduct will return true if semiProduct is CounterManager instance."""
        counterManager=sumid.CounterManager()
        counterManager.addCounters(self.hydra.settings.defaultCounters)
        self.counterSupervisor.verifySemiProduct(counterManager)
        
    def test_counterSupervisor_refreshCounters(self):
        """
        Incorporates individual counterManagers into global counters.
        Returns refreshed global counters.
        Should log (on debug or info level?) change in global counters after adding each individual counter?
        Otherwise it's not possible to log counters after each tree. 
        """ 
        individualCounterManager=sumid.CounterManager()
        self.counterSupervisor.allFilesCount=sumid.CounterManager()
        
        individualCounterManager.increment("hits", 4)
        individualCounterManager.increment("contentLength", 2048)
        individualCounterManager.increment("patternFound", 11)
        individualCounterManager.increment("errorResponseMiss", 5)
        individualCounterManager.increment("differentURLMiss", 2)
        
        # 026 From some reason it has to have title, otherwise the counters aren't added.
        individualCounterManager.title="http://www.example.com/file03.html"
        
        self.counterSupervisor.allFilesCount.reset()
        
        self.counterSupervisor.allFilesCount.increment("hits", 13)
        self.counterSupervisor.allFilesCount.increment("contentLength", 16384)
        self.counterSupervisor.allFilesCount.increment("patternFound", 95)
        self.counterSupervisor.allFilesCount.increment("errorResponseMiss", 53)
        self.counterSupervisor.allFilesCount.increment("differentURLMiss", 16)
        
        self.counterSupervisor.allFilesCount.increment("statusResponseMiss", 2)
        self.counterSupervisor.allFilesCount.increment("zeroLengthMiss", 11)
        self.counterSupervisor.allFilesCount.increment("urlopenTime", 71)
        self.counterSupervisor.allFilesCount.increment("treeOperateTime", 117)
        self.counterSupervisor.allFilesCount.increment("linearPatternTrees", 2)
        
        # Counter allTrees gets always incremented by 1
        self.counterSupervisor.allFilesCount.increment("allTrees", 17)
        #  026 which counters shall be created by refreshCounters?
        
        # The test:
        self.counterSupervisor.refreshCounters(individualCounterManager)
        
        self.assertEqual(self.counterSupervisor.allFilesCount.value("hits"),17)
        self.assertEqual(self.counterSupervisor.allFilesCount.value("contentLength"),18432)
        self.assertEqual(self.counterSupervisor.allFilesCount.value("patternFound"),106)
        self.assertEqual(self.counterSupervisor.allFilesCount.value("errorResponseMiss"),58)
        self.assertEqual(self.counterSupervisor.allFilesCount.value("differentURLMiss"),18)
        
        self.assertEqual(self.counterSupervisor.allFilesCount.value("statusResponseMiss"),2)
        self.assertEqual(self.counterSupervisor.allFilesCount.value("zeroLengthMiss"),11)
        self.assertEqual(self.counterSupervisor.allFilesCount.value("urlopenTime"),71)
        self.assertEqual(self.counterSupervisor.allFilesCount.value("treeOperateTime"),117)
        self.assertEqual(self.counterSupervisor.allFilesCount.value("linearPatternTrees"),2)
        
        self.assertEqual(self.counterSupervisor.allFilesCount.value("allTrees"),18)
        

    def test_counterSupervisor_refreshCounters_spcCounters(self):
        """ counterSupervisor.refreshCounters increment following counters in spc conditions: linearPatternTrees, linearHitsTrees"""
        # Setup for "linearPatternTrees"
        individualCounterManager=sumid.CounterManager()
        self.counterSupervisor.allFilesCount=sumid.CounterManager()
        self.counterSupervisor.allFilesCount.reset()
        
        individualCounterManager.increment("hits", 1)
        individualCounterManager.increment("patternFound", 1)
        self.counterSupervisor.allFilesCount.increment("linearPatternTrees",55)
        self.counterSupervisor.allFilesCount.increment("linearHitsTrees",14)
        
        # 026 From some reason it has to have title, otherwise the counters aren't added.
        individualCounterManager.title="http://www.example.com/file03.html"

        # The test "linearPatternTrees":
        self.counterSupervisor.refreshCounters(individualCounterManager)
        self.assertEqual(self.counterSupervisor.allFilesCount.value("linearPatternTrees"),56)
        self.assertEqual(self.counterSupervisor.allFilesCount.value("linearHitsTrees"),14)
        # Setup for linearHitsTrees
        individualCounterManager.increment("patternFound", 1)
        # The test "linearPatternTrees":
        self.counterSupervisor.refreshCounters(individualCounterManager)
        self.assertEqual(self.counterSupervisor.allFilesCount.value("linearPatternTrees"),56)
        self.assertEqual(self.counterSupervisor.allFilesCount.value("linearHitsTrees"),15)  

class DBTest(unittest.TestCase):
    
    def setUp(self):
        self.filesAdaptor=sumid.FilesAdaptor()       
        self.filesAdaptor.settings.workDir="/home/sumid.results/unittests/"
        self.filesAdaptor.settings.logDir="/home/sumid.results/unittests/"
    
    def test_connectAndDisconnectDB(self):
        """ Files adaptor creates db connection and ensures that BOW table exists."""
        # 026 Shall be also checked for following situations:
        # 1) Neither file nor BOW table exists.
        # 2) File exists, but not BOW table.
        # 3) Both, file and BOW table, exist.
        self.filesAdaptor.connectDB()
        self.assertTrue(isinstance(self.filesAdaptor.DBconnection,sumid.sqlite3.Connection))
        tableList=[]
        self.filesAdaptor.DBcursor.execute("select * from sqlite_master;")
        for row in self.filesAdaptor.DBcursor:
            tableList.append(row[2])
        #print tableList
        self.assertTrue("BOW" in tableList)
        self.filesAdaptor.disconnectDB()
        self.assertRaises(sumid.sqlite3.dbapi2.ProgrammingError,self.filesAdaptor.DBcursor.execute,"select * from sqlite_master;")
        
    def test_updateBOW(self):
        """ When specific counter is sent to update first time, counter gets INSERTed to db. Second time is just updated """
        if os.path.exists("/home/sumid.results/unittests/sumid.log.sqlite"):
            os.remove("/home/sumid.results/unittests/sumid.log.sqlite")
        #if os.path.exists("/home/sumid.results/prelinklist25sumid.log.sqlite"):
        #    os.remove("/home/sumid.results/prelinklist25sumid.log.sqlite")
        self.filesAdaptor.connectDB()
        counters=CounterManager()
        testWords=[["word1", 1],["word2", 2],["word3", 3]]
        counters.increment(testWords[0][0], testWords[0][1])
        counters.increment(testWords[1][0], testWords[1][1])
        counters.increment(testWords[2][0], testWords[2][1])
        # First update and check of the counters.
        result=self.filesAdaptor.updateBOW(counters)    
        self.filesAdaptor.DBcursor.execute("select * from BOW order by word asc;")
        rowIndex=0
        for row in self.filesAdaptor.DBcursor:
            self.assertEqual(row[1],testWords[rowIndex][0])
            self.assertEqual(row[2],testWords[rowIndex][1])
            rowIndex+=1
        self.assertEqual(rowIndex,len(testWords))
        self.assertEqual(result,len(testWords))
        # Second update. The counters shall be doubled, while the count of them shall stay same.
        self.filesAdaptor.updateBOW(counters)    
        self.filesAdaptor.DBcursor.execute("select * from BOW order by word asc;")
        rowIndex=0
        for row in self.filesAdaptor.DBcursor:
            self.assertEqual(row[1],testWords[rowIndex][0])
            self.assertEqual(row[2],testWords[rowIndex][1]*2)
            rowIndex+=1
        self.assertEqual(rowIndex,len(testWords))
        self.assertEqual(result,len(testWords))
        
if __name__ == "__main__":
    
    #whole=False
    whole=True
    if not hasattr(Shared,"settings") or not hasattr(Shared,"debug"): setUpModule()
    
    if whole:
        unittest.main()   
    else:
        hydraSuite1 = unittest.TestLoader().loadTestsFromTestCase(HydraTests)
        unittest.TextTestRunner(verbosity=2).run(hydraSuite1) # ValueError: year out of range
        hydraSuite2 = unittest.TestLoader().loadTestsFromTestCase(Hydra_ShallContinue)
        unittest.TextTestRunner(verbosity=2).run(hydraSuite2)
        abstractProducerTestsSuite = unittest.TestLoader().loadTestsFromTestCase(AbstractProducerTests)
        unittest.TextTestRunner(verbosity=2).run(abstractProducerTestsSuite) # ValueError: year out of range
        linklistSupplierTests = unittest.TestLoader().loadTestsFromTestCase(LinklistSupplierTests)
        unittest.TextTestRunner(verbosity=2).run(linklistSupplierTests) # ValueError: year out of range
        compTreeProducerTests = unittest.TestLoader().loadTestsFromTestCase(CompTreeProducerTests)
        unittest.TextTestRunner(verbosity=2).run(compTreeProducerTests)  # ValueError: year out of range
        dbTests = unittest.TestLoader().loadTestsFromTestCase(DBTest)
        unittest.TextTestRunner(verbosity=2).run(dbTests)