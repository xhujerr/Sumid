#!/bin/env python

#    BOW - Bag of words analyzer
#    Copyright (C) 2011-2012  Roman Hujer <sumid at gmx dot com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/ .

__program__="SUMID"
__programLongName__="Bag of words analyzer"
__version__="0.02"
__sumidVersion__="0.27"
__authors__="Roman Hujer <sumid at gmx dot com>"
__year__="2011-2012"

greetingPrompt="""
    %s %s - %s 
    Copyright (C) %s  %s
    This program comes with ABSOLUTELY NO WARRANTY.
    This is free software, and you are welcome to redistribute it
    under certain conditions; view http://www.gnu.org/licenses/gpl.txt for details.
"""%(__program__,__version__ , __programLongName__, __year__, __authors__)

todoList=""" Todo list:
"""
notes="""
"""
# Settings begin
mainINIFilePath='/media/KINGSTON/Sumid/src/sumid.ini'
# Settings end
import threading
import time
#import miscutil # 027 expanded to ease regrTest
from miscutil import CounterManager, Settings, Shared, Debug, FactoryMethod, FilesAdaptor, UnixPathStorage, FilesAdaptorComplex
from linklist import LinklistAdaptor, TextLinklistParser, SmartURL
from Queue import Queue 

class AbstractProducer(threading.Thread, Shared):
    """
    This class is in theory the same as the AbstractProducer in sumid module and shall be eventually merged. Nonetheless there are minor differences:
    -- reference to Hydra in __init__()
    -- reference to parser in __init__(
    --- both to terminate run() 
    --- there could be BOW definition of hydra with it's own shallContinue()
    """
    def __init__(self,inputQueue,outputQueue,inputCondition,outputCondition,**kwargs):
        threading.Thread.__init__(self)
        if not hasattr(self.__class__,"cx"): self.__class__.cx=0
        self.__class__.cx+=1
        self.name="%s_%s"%(self.__class__.__name__,self.__class__.cx)
        # Load from params
        self.kwargs=kwargs
        # 026 kwargs are:
        #     For BOWBuilderSimple "parserInstance" (mandatory)
        #     For BOWUpdaterSimple "filesAdaptor" (mandatory)
        self.inputCondition=inputCondition
        self.inputQueue=inputQueue
        self.outputCondition=outputCondition
        self.outputQueue=outputQueue
        # Set-up processed url counter.
        self.cx=0
        self.customInitialization()
        
    def run(self):
        while not self.parser.linklistEOF or not self.inputQueue.empty():
            semiProduct=self.consume()
            if self.verifySemiProduct(semiProduct):
                self.produce(semiProduct)
        self.finalize()
        self.logger.info("%s %s has nothing to do. Ending."%(self.__class__.__name__,self.getName()))
    
    # 026 Those three have to be always redefined.            
    def consume(self): raise NotImplementedError
    def verifySemiProduct(self,semiProduct): raise NotImplementedError
    def produce(self,semiProduct): raise NotImplementedError
    
    def customInitialization(self): pass # 026 Doesn't have to be defined.
    def finalize(self): pass # 026 BOWBuilderSimple needs to finalize operation bebore is terminated. 
    

class BOWBuilderSimple(AbstractProducer): 
    """ Creates bow for each class. """    
    
    def customInitialization(self):
        self.parser=self.kwargs['parserInstance']
        self.initializeCounters()

    def initializeCounters(self):
        """ Initialization for BOWBuilderSimple is trivial (unlike BOWBuilderComplex)."""
        self.counters = CounterManager()
        self.counters.title="word" # 026 Title is used by FilesAdaptor to determine column.
                
    def consume(self): 
        """ Consume just asks parser for next url. """
        url=self.parser.next()
        # 026 Just non-mandatory logging:
        self.cx+=1
        if url and self.cx % 10 == 0:
            self.logger.debug("Processing url number: %i. Last processed url: %s"%(self.cx,url.Composed))
        return url
    
    def verifySemiProduct(self,semiProduct):
        """ SemiProduct must be an SmartURL instance. """
        if isinstance(semiProduct,SmartURL):
            return True
        else: return False 

    def produce(self,semiProduct):
        """ 
        Doesn't create product every iteration. 
        Just acumulates words until counters reaches number of settings.bowTempSize. 
        Then put old counters into output queue and starts counting from 0.
        """
        words=semiProduct.Words(self.settings.urlWordsSeparators)

        for word in words:
            if word not in self.settings.commonWords:
                self.counters.increment(word)
        if self.counters.NumberOfCounters>self.settings.bowTempSize or self.parser.linklistEOF:
            # 026 Put full counters to output queue.
            self.outputCondition.acquire()
            self.outputQueue.put(self.counters)
            self.outputCondition.release()
            # 026 Create new empty counters:
            self.counters = CounterManager()
            self.counters.title="word"
            return True
        else: return False
        # 026 The meaning of the return value is, if a counter was added to the queue.
        
    def finalize(self):
        self.outputCondition.acquire()
        self.outputQueue.put(self.counters)
        self.outputCondition.release()


class BOWBuilderComplex(BOWBuilderSimple):
    """
    Creates bow from parsed url.
    Methods customInitialization, consume, verifySemiProduct and finalize are the same as in BOWBuilderSimple.
    Main difference is in produce.
    Minor difference is also in initializeCounters.
    """
            
    def initializeCounters(self):
        """ This method covers the difference in counters initialization."""
        # 027 Just initialize the structure for the counters.
        self.counters={}
        for keyWord in self.settings.linklistURLParts:
            if keyWord == "scheme": continue
            self.counters[keyWord]=CounterManager()
            # 026 Title is used by FilesAdaptor to determine column.
            self.counters[keyWord].title=keyWord 
                  
    def produce(self,semiProduct):    
        """ Just counts the words restricted on group ["scheme", "netloc", "path", "params", "query", "fragment"]. """  
        self.debug.printHeader()   
        words=semiProduct.WordsPerPartes(self.settings.urlWordsSeparators)
        # 026 The meaning of the return value is, if a counter was added to the queue.
        result = False
        cx=-1 # 027 just a trick how to have the iteration in the beginning of the cycle. Cannot be in the end, coz is skipped by continue.
        # 027 Cycle thru all url parts.
        for keyWord in self.settings.linklistURLParts:
            # 027 linklistURLParts are in settings coz I try to hide the linklist implementation from BOWBuilder.
            cx += 1
            if keyWord == "scheme": continue
            
            # 027 Count the words for specific part into specific counter.
            for word in words[cx]:
                if word and word not in self.settings.commonWords:
                    self.counters[keyWord].increment(word)
            
            # 027 Check if the counters shall be updated in database.
            if self.counters[keyWord].NumberOfCounters>=self.settings.bowTempSize or self.parser.linklistEOF:
                # 026 Put full counters to output queue.
                self.outputCondition.acquire()
                self.outputQueue.put(self.counters[keyWord])
                self.outputCondition.release()
                # 026 Create new empty counters:
                self.counters[keyWord] = CounterManager()
                # 027 The title is important, coz FileAdaptor identifies the right DB column by the title.
                self.counters[keyWord].title=keyWord
                result = True
        return result

    def finalize(self):
        self.outputCondition.acquire()
        # 027 For bow complex the counters are list of CounterManager, while BOWUpdaterSimple expects simple CounterManager. 
        for counterKey in self.counters.keys():
            self.outputQueue.put(self.counters[counterKey])
        self.outputCondition.release()
    

class BOWUpdaterSimple(AbstractProducer):
        
    def customInitialization(self):
        self.files=self.kwargs["filesAdaptor"]
        self.parser=self.kwargs["parserInstance"] # 026 parser is in AbstractProducer used to terminate run() (while not parser.EOF). To be removed. 
    
    def consume(self):
        """ Takes the bow counters from queue with the locking magic. """ 
        if not self.inputQueue.empty():
            self.logger.debug("Going to take an item from inputQueue, which is %i items long."%(self.inputQueue.qsize()))
            self.inputCondition.acquire()
            item = self.inputQueue.get()
            self.inputCondition.release()
        else:
            time.sleep(self.settings.bowWaitTime)
            item=None
        return item
        
    def verifySemiProduct(self,semiProduct): 
        """ SemiProduct must be a counters instance."""
        if isinstance(semiProduct, CounterManager):
            self.logger.debug("Got correct counterManager with title %s."%(semiProduct.title)) 
            return True
        else:
            if semiProduct: self.logger.warning("Got incorrect input of type: %s."%(type(semiProduct)))
            return False
        
    def produce(self,semiProduct): 
        """ Produce calls filesAdaptor to update DB."""
        BOWLenghth=self.files.updateBOW(semiProduct)
        self.logger.debug("BOW table length is now %i. And the countersQueue is %i long."%(BOWLenghth,self.inputQueue.qsize()))
        return BOWLenghth

    def finalize(self):
        """ All the remaining items in output queue have to be processed. """
        # 027 This code duplicates self.run() only the condition from run is already false.
        while not self.inputQueue.empty():
            debug.ThreadAwareLogger.debug("There are still %i counters which are not in db yet. Fixing it."%(self.inputQueue.qsize()))
            semiProduct = self.consume()
            if self.verifySemiProduct(semiProduct):
                self.produce(semiProduct)

class AbstractFilter(Shared):
    _nonMatchRegexp=None
    _matchRegexp=None
        
# body begin
if __name__ == "__main__":
    settings = Settings()
    Shared.settings=settings
    settings.mainINIFilePath=mainINIFilePath
    settings.loadAdaptive("all")
    settings.loadFromINI(mainINIFilePath)
    debug=Debug(settings)
    Shared.debug=debug
    
    factory=FactoryMethod()
    settings.pathStorage=factory.create(eval(settings.platform+'PathStorage'))
    factory.sharedRef.pathStorage=settings.pathStorage 
    
    files=FilesAdaptorComplex()
    settings.connectFilesAdaptor(files)
    linklistAdaptor=LinklistAdaptor()
    linklistAdaptor.connectLinklistFile(files.linklist)
    
    textLinklistParser=TextLinklistParser()
    textLinklistParser.connectLinklistAdaptor(linklistAdaptor)
    
    debug.ThreadAwareLogger.info("Basic initialization complete.")
    
    counters = CounterManager()
    files.connectDB()

    dummyQueue=Queue() # 026 This is to bypass non-existence of hydra. Fast & ugly.
    countersQueue=Queue()
    countersQueueCondition=threading.Condition()
    
    #AbstractProducer(inputQueue,outputQueue,inputCondition,outputCondition,**kwargs):
    #bowBuilderSimple=BOWBuilderSimple(dummyQueue,countersQueue,None,countersQueueCondition,parserInstance=textLinklistParser)
    bowBuilderComplex=BOWBuilderComplex(dummyQueue,countersQueue,None,countersQueueCondition,parserInstance=textLinklistParser)
    bowUpdaterSimple=BOWUpdaterSimple(countersQueue,None,countersQueueCondition,None,filesAdaptor=files, parserInstance=textLinklistParser)

    #bowBuilderSimple.start()
    bowBuilderComplex.start()
    bowUpdaterSimple.start()
    
    debug.ThreadAwareLogger.debug("Waiting for threads to finish their work")
    
    #bowBuilderSimple.join()
    bowBuilderComplex.join()
    bowUpdaterSimple.join()
    
    while not countersQueue.empty():
        debug.ThreadAwareLogger.debug("There are still some counters which are not in db yet. Fixing it.")
        files.updateBOW(countersQueue.get())
        
    files.applyStemFilter()
    
    files.disconnectDB()
    
    debug.ThreadAwareLogger.info("BOW finished without critical errors.")
    
# body end    
