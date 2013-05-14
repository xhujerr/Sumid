#!/bin/env python

#    BOW - Bag of words analyzer
#    Copyright (C) 2011  Roman Hujer <sumid at gmx dot com>
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
__version__="0.01"
__sumidVersion__="0.26"
__authors__="Roman Hujer <sumid at gmx dot com>"
__year__="2011"

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
import miscutil
from sumid import FilesAdaptor, UnixPathStorage
from linklist import LinklistAdaptor, TextLinklistParser, SmartURL
from Queue import Queue 

class AbstractProducer(threading.Thread, miscutil.Shared):
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
    
    # 026 Those three have to be always redefined.            
    def consume(self): raise NotImplementedError
    def verifySemiproduct(self,semiProduct): raise NotImplementedError
    def produce(self,semiProduct): raise NotImplementedError
    
    def customInitialization(self): pass # 026 Doesn't have to be defined.
    def finalize(self): pass # 026 BOWBuilderSimple needs to finalize operation bebore is terminated. 
    

class BOWBuilderSimple(AbstractProducer): 
    """ Creates bow for each class. """    
    
    def customInitialization(self):
        self.parser=self.kwargs['parserInstance']
                
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
        if not hasattr(self,"counters"):
            # 026 The idea here is to always overwrite the old instance of counters with a new one.
            self.counters = miscutil.CounterManager()
            self.counters.title="words" # 026 Title is used by FilesAdaptor to determine column.
        for word in words:
            if word not in self.settings.commonWords:
                self.counters.increment(word)
        if self.counters.NumberOfCounters>self.settings.bowTempSize or self.parser.linklistEOF:
            # 026 Put full counters to output queue.
            self.outputCondition.acquire()
            self.outputQueue.put(self.counters)
            self.outputCondition.release()
            # 026 Create new empty counters:
            self.counters = miscutil.CounterManager()
            self.counters.title="words"
            return True
        else: return False
        # 026 The meaning of the return value is, if a counter was added to the queue.
        
    def finalize(self):
        self.outputCondition.acquire()
        self.outputQueue.put(self.counters)
        self.outputCondition.release()
        
                
class BOWUpdaterSimple(AbstractProducer):
        
    def customInitialization(self):
        self.files=self.kwargs["filesAdaptor"]
        self.parser=self.kwargs["parserInstance"] # 026 parser is in AbstractProducer used to terminate run() (while not parser.EOF). To be removed. 
    
    def consume(self):
        """ Takes the bow counters from queue with the locking magic. """ 
        if not self.inputQueue.empty():
            self.inputCondition.acquire()
            item = self.inputQueue.get()
            self.inputCondition.release()
        else:
            time.sleep(self.settings.bowWaitTime)
            item=None
        return item
        
    def verifySemiProduct(self,semiProduct): 
        """ SemiProduct must be a counters instance."""
        if isinstance(semiProduct, miscutil.CounterManager): return True
        else: return False
        
    def produce(self,semiProduct): 
        """ Produce calls filesAdaptor to update DB."""
        BOWLenghth=self.files.updateBOW(semiProduct)
        self.logger.debug("BOW table length is now %i."%(BOWLenghth))
        return BOWLenghth
        
# body begin
if __name__ == "__main__":
    settings = miscutil.Settings()
    miscutil.Shared.settings=settings
    settings.mainINIFilePath=mainINIFilePath
    settings.loadAdaptive("all")
    settings.loadFromINI(mainINIFilePath)
    debug=miscutil.Debug(settings)
    miscutil.Shared.debug=debug
    
    factory=miscutil.FactoryMethod()
    settings.pathStorage=factory.create(eval(settings.platform+'PathStorage'))
    factory.sharedRef.pathStorage=settings.pathStorage 
    
    files=FilesAdaptor()
    settings.connectFilesAdaptor(files)
    linklistAdaptor=LinklistAdaptor()
    linklistAdaptor.connectLinklistFile(files.linklist)
    
    textLinklistParser=TextLinklistParser()
    textLinklistParser.connectLinklistAdaptor(linklistAdaptor)
    
    debug.ThreadAwareLogger.info("Basic initialization complete.")
    
    counters = miscutil.CounterManager()
    files.connectDB()
    """
    cx=0
    while not textLinklistParser.linklistEOF:
        url=textLinklistParser.next()
        cx+=1
        if cx % 10 == 0:
            debug.mainLogger.debug("Processing url number: %i."%(cx))
        if url: 
            debug.mainLogger.debug("Working with url: %s."%(url.Composed))
            words=url.Words(settings.urlWordsSeparators)
        else: continue

        for word in words:
            if word not in settings.commonWords:
                counters.increment(word)
        if counters.NumberOfCounters>settings.bowTempSize:
            BOWLenghth=files.updateBOW(counters)
            counters.clear()
            debug.mainLogger.debug("BOW table length is now %i."%(BOWLenghth))
        
    files.updateBOW(counters)"""

    dummyQueue=Queue() # 026 This is to bypass non-existence of hydra. Fast & ugly.
    countersQueue=Queue()
    countersQueueCondition=threading.Condition()
    
    bowBuilderSimple=BOWBuilderSimple(dummyQueue,countersQueue,None,countersQueueCondition,parserInstance=textLinklistParser)
    bowUpdaterSimple=BOWUpdaterSimple(countersQueue,None,countersQueueCondition,None,filesAdaptor=files, parserInstance=textLinklistParser)

    bowBuilderSimple.start()
    bowUpdaterSimple.start()
    
    debug.ThreadAwareLogger.debug("Waiting for threads to finish their work")
    
    bowBuilderSimple.join()
    bowUpdaterSimple.join()
    
    if countersQueue.qsize():
        debug.ThreadAwareLogger.debug("There are still some counters which are not in db yet. Fixing it.")
        files.updateBOW(countersQueue.get())
        
    files.disconnectDB()
    
    debug.ThreadAwareLogger.info("BOW finished without critical errors.")
    
# body end    
