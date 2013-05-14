#!/bin/env python

#    SUMID - Script used for mass items downloading
#    Copyright (C) 2004-2012  Roman Hujer <sumid at gmx dot com>
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
__programLongName__="Script used for mass items downloading"
__version__="0.27"
__authors__="Roman Hujer <sumid [at] gmx [dot] com>"
__year__="2004-2012"

greetingPrompt="""
    %s %s - %s 
    Copyright (C) %s  %s
    This program comes with ABSOLUTELY NO WARRANTY.
    This is free software, and you are welcome to redistribute it
    under certain conditions; view http://www.gnu.org/licenses/gpl.txt for details.
"""%(__program__,__version__ , __programLongName__, __year__, __authors__)

todoList=""" Todo list:
032: find how create debug instance in settings class (before Debug class is defined) - what about to store logged stuff in buffer until Debug instance is created? 
034: auto correction Settings.platform()
039: move loadFromInterface to Shared class
043: implement switching loglevels (keep only Settins.restricted)
044: implement switching loglevels for whole class
046: port it to win32 - esp imlpement Win32PathStorage
047: Remove all "raise NotImplementedYetError". (This means write appropriate code instead of it.) 
048: Rewrite regexp for local filename. Every number has to be at least 3 digits.
055: Improve code to be in accordance with "Style guide for Python code" ( http://www.python.org/dev/peps/pep-0008/ )
055a:I'll resist to rename from mixedCase to lower_case_with_underscores
055b:Non-public attribute MUST start with underscore.
055c:Properties only work on new-style classes. ( http://www.python.org/download/releases/2.2.3/descrintro/#property or http://adam.gomaa.us/blog/the-python-property-builtin/ )
059: Find what is purpose of miscutil.Shared.loadFromInterface and make it work. (Since Shared is static, I doubt I can solve this.) Solves also 039.
063: GPL terms clashes with docstring.
065: Try to make miscutil.Debug and miscutil.Settings static. This could reduce the mess caused by Singleton and Shared.
     -- simple static method (aka classmethod): http://www.ibm.com/developerworks/linux/library/l-cpdecor.html
     -- http://pyref.infogami.com/staticmethod
068: Printing of method headers should be also controlled by debug level. Needed because of comptree...download operation.
070: Rework FilesAdaptor to manage collection of file objects.
075: If Node.content contains more than one group of numbers only one(each direction - so two) sib-node is created incrementing all groups at once.
     This is wrong. Usually only the last group of digits needs to be incremented.
076: Files adaptor shouldn't care about desired file name. Shouldn't call pattern analyzer. It should obtain desired file name as input parameter. 
078: Automatic detection required for step from 10 to 9 vs from 10 to 09.
079: GUI
080: Regular expression for something different than numbers.
081: Remove hand over of the debug variable via inheritance. It is highway to hell! 
     I tried to enhance the debug class and I wasn't able to get the right instance. I will either:
     -- Create instance of Shared and hand it over to every class via input parameter.
     -- Find out howto work with static classes and rework Debug and Settings to static.
     -- Solves also 065 and 073

     Enhancements planned for version 0.24
084: Write successful hits into a file. (partially solved)
     -- Also sqlite could be used
     -- Aside successful hits unsuccessful shall be written due to statistics. (solved in 140)
     -- Write other information related to hit? E.g. seed, # hole overlaps, sibling, links discovered per seed?
085: Implement decision about result just based on http reply. (Instead of filetype detection.) (partially rejected)
     -- Shall be configurable!
     -- HTTPResponse NOT returned by urllib2.open().info()!!!
     -- I'm afraid that RFC2616 doesn't define numeric code in HTTPResponse. http://www.cs.tut.fi/~jkorpela/http.html
     -- Works in 2.6 only: self.returnCode=self.content.getcode() 
     -- Sometimes server does return 200 even if the response does no match the result.
086: Implement more kinds of operation (partially solved)
     -- download, log hits, index ...
     -- Abstract factory? Simple inheritance?
     -- This is bit more complicated. I need to create the class with operation in LeafProxy. 
     -- So I cannot initialize it from body because I need a large number of their instances.
     -- Inside of DistantFile.__init__() I would need if for each operation type, which is wrong.
     -- Probably I have to create an Abstract factory in body and ask it for creation of concrete instance from LeafProxy.
     -- There is also mess among competition of LeafProxy and DistantFile.
     -- Also decorator should be taken into account. So far there are two operations: download and log. But all combinations are possible.
     -- Solves also 066
     -- Replace all occurrences of word download by operation (not only in comptree). (SUMID - Script used for mass items downloading)

     Bugs found during coding of version 0.24
089: Low priority: Merge XMLDebug with debug.
090: Settings should be a factory. Each kind of loading should be a class. INILoader should be inherited from FileLoader.
102: Implement class selective logging - more in miscutil.Debug.__init__().
103: Have a look at DistantFile.writeToLocalFile() - it is necessary to call filesAdaptor?
105: Create module shared for classes Settings Debug and Shared?
110: Create Debug.LoadAdaptive(*args) - purpose is to create Debug instance without having settings instance.
     -- Redefine everything - with or without settings. 
     -- If instance tries to call something where Settings instance is needed Debug should try to recreate the instance with setting and if it's not possible then raise exception.
111: Bug: If proxy server required in Internet connection miscutil.LeafProxy.download() doesn't raise any exception.
     => when catching an exception, write it into log file.
121: TypeError: unsupported operand type(s) for +=: 'CounterManager' and 'CounterManager'
123: miscutil.Singleton.__new__() is a classmethod. Use decorated syntax @classmethod .
     -- simple static method (aka classmethod): http://www.ibm.com/developerworks/linux/library/l-cpdecor.html 
124: SLS: Reanalysis of 082. Create class AbstractFetcher - develops alternative connector to external link database. Access via webservice. Will be base for concrete fetcher classes implemented in 124 -132 Probably factory pattern.
125: SLS: concrete fetcher: Google connector - GoogleSearch SOAP webservice no longer available.
126: SLS: concrete fetcher: Nutch connector 
128: SLS: concrete fetcher: Delicious connector - http://delicious.com/
129: SLS: concrete fetcher: Twitter connector - This is it: http://stackoverflow.com/questions/2204856/write-timestamp-to-file-every-hour-in-python
130: SLS: concrete fetcher: Reddit connector - reddit.com - http://code.reddit.com/wiki/API 
131: SLS: concrete fetcher: Flickr connector
132: SLS: concrete fetcher: Yahoo connector - http://developer.yahoo.com/, + http://www.stumbleupon.com/technology/
134: MD5 check of settings.py, if it was changed. It is not supposed to change.
135: Google for lazy initialization. Great for settings. Will load the settings.param when it is called the first time. (Params with get/set methods.)
     Python lazy property decorator
     http://stackoverflow.com/questions/3012421/python-lazy-property-decorator
145: RegrTst: Bug: For following link was the hole tolerance infinite while it should have been 3; For other links from linklist the hole tolerance did work.
146: D2T: miscutil.Settings.loadFromINI() cannot use a variable created in settings.py as a constant. D2T doesn't use settings. (It is used twice. First as a global var, second as a Setting property.)

     Enhancements planned for version 0.25
141: Grouping links in linklist
     -- 4 groups according to Cun-He, Li; Ke-qiang, Lv: Hyperlink classification
         -- This wouldn't be possible because the grouping was done in relation to current resource.
     
     Issues found during coding of version 0.25
151: Decision about incompatibilities among D2T and Sumid based on __program__ .
152: Log hits which are not in linklist into a separate file. (Or exclude seeds from hits.)
159: CounterManager.value(nonExistingCounter) returns zero.
160: A slash at the end of the link can cause error 516.
165: Remove all calls of debug.printHeader. (This covers half of Todo: 083,068)
170: Log trees with more than one hit.
171: 1M: Debug.printHeader() causes KeyError since threading included into Sumid. 
     I suspect that call stack was changed coz threads. When not logging.level!=debug method bypassed (which should be anyway).
     -- Original problem bypassed by enclosing into protected block.
175: Consider moving thread managers to appropriate files. (Problems: Import threading 3x. Handover of Conditions, Queues, Threads ) 
180: Trace log level needed.
185: Bug: DistantFile.SafeOpen could overwrite returned status with 200.
188: 1M: URL could start with https.
189: 1M: For several urls are in counters more than 100 misses with just 0/1 hits => Limitation for sibsExtendDecision() creating sibs probably doesn't work. 
193: The config parser wrapped in EnhancedConfigParser is still used by Debug.initializeLoggers()
        -- eh what's wrong about it?
195: Change Hydra to Mediator: http://cs.wikipedia.org/wiki/Prost%C5%99edn%C3%ADk_%28n%C3%A1vrhov%C3%BD_vzor%29


     Enhancements planned for version 0.26
166: Loggers shall have own config file: http://docs.python.org/library/logging.html     
179: Develop some verification of sumid results. Eg SQL query to patterns, or comparing and counting logs.
184: Implement verification if the hit is indexed by google.

     Bugs found during coding of version 0.26
197: Divide the links to easy and difficult and handle them separately.
        -- For each pattern found is by default generated 8 sibs.
        -- With more patterns in a link this number grows exponentially.
        -- Which means to split links queue in two and create an manager which decides from which queue links are taken.
        -- But this have an influence to resulting stats. (= configurable)
198: Previous range can be changed dynamically based on tree success ratio.
        -- previousRange=previousRange*(hits/patternsFound)
199: Try to identify a subpattern (Eg: date)
201: For modification of a pattern consider operations from genetic algorithms (such as mutation). 
203: 1M: 2010-12-16 04:24:12,003 | comptree | 222 | compTree | sibsExtendDecision | WARNING | 
         Forcefully limiting adding of more siblings. TrialsPerTree: 0; SibsCount 51; 
         url: http://readersupportednews.org/off-site-news-section/28-28/2169-congress-blames-bp-cost-cutting-for-gulf-oil-leak-disaster
208: Replace FilesAdaptor.loadPartOfAFile() with EnhancedURLopener(URLopener).readlines(number) 
209: Remove method FilesAdaptor.loadPartOfLinkList() in favor of LinklistAdaptor.
     - Won't be loaded in batches but one by one.
210: Hydra.adjustThreadWaitingTime how should be computed occupancy in infinite queue (Err div by zero).
214: Create check for robots.txt (soft and hard policy in settings - None/Permisive/Enforcing). 
     http://en.wikipedia.org/wiki/Robots.txt
     Will consume a lot of extra time (opening robots.txt for each seed).
215: Create check of counters. patternFound=hits+sum(allMisses)
216: AnyProducer.Consume() could be unified. 
     The only problem is LinklistSupplier 
     => class AbstractConsumer(AbstractProducer): with unified method consume()
218: NodeProxy class shall be handed to ComptreeProducer explicitly. To be able mock it in tests.
219: Do not write into the cll URLs, where 0 hits was reached.
     -- If so, Sumid can clean old linklist file from links which are completelly defunct.
     -- New functionality based just on configuration change (previousRange=0, maxLevels=1).
     => Cleaning the linklist.
220: qSize logger: Later it should be possible to set-up filename or turn it off.
221: 1M: RejuvernateThreads is not able to rejuvernate a thread after an exception occurred. Line 463 sumid.py.
223: Settings.maxLevels doesn't work.
224: URL class design => beginning, content and tail are out of competence of SmartURL. They have to be managed by NodeProxy.
     (default behavior is: everything is in the beginning, content and tail are empty)
     - need a method to move content from beginning to tail (self.content=self.splittedLink.pop(0))
227: DistantFile shall match URL against robots.txt before opening.
     (http://docs.python.org/library/robotparser.html)
     - Probably one robot matching instance can be shared per tree.
     - Solves also 214
230: Try to save distantfile even thou status was an error.
233: In sumid module create function BasicInitialization() - from the lines of body till message "Threading hell begin. Creating all queues."
     This function could be shared by sumid, sls and bow.
     -- reconsider: sls and bow shouldn't import sumid. 
237: Enhance all prosumers with **kwargs as demonstrated in bow.AbstractProducer.__init__() and bow.BOWBuilderSimple.custominit()
238: Merge AbstractProducer from bow into AP in sumid. (requires 237)
239: Remove parser from BOWUpdaterSimple kwargs. (requires 238)
240: Consider waitingTime property for every prosumer in odrer to replace: timeWaitLinklistSupplier, timeWaitCounterSupervisor, timeWaitCompTreeProcessor, timeWaitDefaultThread
     -- Controversy: It's driven by practical means and don't have logical justification.
     -- Why should be thread by default destined to wait?
241: Option to ommit search in hostname. Allow  to search only in path.
242: Sumid configurator. GUI, Radioboxes with preselected values with comments. RegrTst/Small scale/1M/Heawy load/Load running/Profiling.
     
     Enhancements planned for version 0.27
200: Engineer changes needed in Sumid in order to work with other pattern than numeric.
    -- Pattern analyser.
    -- Carrier of logic how could be pattern changed.
    -- Solves also 080
232: Create new module Prosumers and move there all producers and Hydra.
     - Should also include 175.
038: write documentation
    -- (026)at least create separate issues to figure out what means documentation (Release notes, User manual, Configuration manual, Class and methods description).
    -- (026)research automated documentation generation from comments.
236: cll (counters.csv) will change to sqlite. Each link is in fact seed. Table colums: url, hits, misses, patterns, ?isPaternLinear?, ?isHitLinear?

     Bugs found during coding of version 0.27
244: Distinct commonWords for a netlock and path.
246: sls: Create posibility to do weekly / monthly linklists. Configurable. 
248: printHeader could be a method of logger (ThreadAwareLogger):
     - printing the name of the function is not neccesary anymore
     - name of function: how they do it in formatter?
     - params could be refered as self.dict .. or whatever
     - the old implementation and the new is not in conflict, coz is attr of another Class.
249: For bow develop class Filters (& Filter)
     - Filters can be used from BOW builder to filter certain words from adding to sqlite.
     - Shall be possible to turn on/off each filter.
     - Filter 1: commonWords=["","http:","www","html","com","php","net","org","co","uk","htm","aspx","cfm","asp","au","cgi"]
     - Filter 2: plural vs. singular of words.
         - Stemming library by Porter http://tartarus.org/~martin/PorterStemmer/ also package python-stemmer
     - Filter 3: national domains (low importance - is in netlock).
251: Rewrite SmartURL to be using furl: https://github.com/gruns/furl/     
253: --next bug --
"""

import os
import urllib2 # 027 Remove with FA.
# import comptree # 026 in order to make regrtest easier (renaming units).
from miscutil import Settings, Debug, Shared, FactoryMethod, CounterManager, SchedulerManager, FilesAdaptor, UnixPathStorage # 027 UnixPathStorage needed in an eval
from linklist import LinklistAdaptor
from comptree import NodeProxy
import threading
from Queue import Queue 
import time
#import sched #026
from logging import INFO, DEBUG
#import traceback # 026
#import sys #026

class EnhancedCondition(threading._Condition,Shared):
    "This class enhances the Condition class in order to find out which thread owns the lock."
    #It is also dirty hack. I shouldn't access private class. But the I think it is also hack in threading module.
    
    def __init__(self):
        self.owner= None
        return super(EnhancedCondition, self).__init__()
    
    def acquire(self,*args):
        self.owner=threading.currentThread().getName()
        result=super(EnhancedCondition, self).acquire(args)
        self.logger.debug("Lock acquired by %s"%(threading.currentThread().getName()))
        return result

    def release(self):
        result = super(EnhancedCondition, self).release()
        self.logger.debug("Lock released by %s"%(threading.currentThread().getName()))
        self.owner= None
        return result


class AbstractProducer(threading.Thread, Shared):
    """ Base class for all consumer/producer threads."""
    running=0
    
    def __init__(self,hydra,inputQueue,outputQueue,inputCondition,outputCondition):
        threading.Thread.__init__(self)
        if not hasattr(self.__class__,"cx"): self.__class__.cx=0
        self.__class__.cx+=1
        self.name="%s_%s"%(self.__class__.__name__,self.__class__.cx)
        self.debug.printHeader()
        self.hydra=hydra
        self.inputQueue=inputQueue
        self.outputQueue=outputQueue
        self.inputCondition=inputCondition
        self.outputCondition=outputCondition
        #self.logger=self.debug.enrichMainLogger("%s-%s"%(self.__class__.__name__,self.getName())) # 026 Replaced by logger for each thread,
        # 026 in Shared #self.logger=self.debug.cloneMainLogger(self.getName())
        self.customInitialization()
        
    def run(self):
        self.debug.printHeader()
        self.__class__.running += 1
        while self.hydra.shallContinue(self.__class__.__name__+"Strategy"):
            try:
                semiProduct=self.consume()
                if self.verifySemiProduct(semiProduct):
                    self.produce(semiProduct)
                else:
                    self.logger.warning("%s got invalid input: %s; %s"%(self.__class__.__name__,type(semiProduct),str(semiProduct)) )
                    self.logger.debug("%s is waiting %i seconds for a valid input."%(self.__class__.__name__,self.settings.timeWaitDefaultThread))
                    time.sleep(self.settings.timeWaitDefaultThread)                                
            except IOError:
                self.logger.exception("In thread %s %s caught an exception: \n"%(self.__class__.__name__,self.getName()))
                self.logger.error("Now listing open files:\n %s"%(str(debug.get_open_fds())))
                self.hydra.rejuvernateThreads()
            except:
                self.logger.exception("In thread %s %s caught an exception: \n"%(self.__class__.__name__,self.getName()))
                self.hydra.rejuvernateThreads()
        self.logger.info("%s %s has nothing to do. Ending."%(self.__class__.__name__,self.getName()))
        self.__class__.running -= 1
        if self.__class__.running < 0: self.logger.error("Count of running threads of %s can't be negative. Currently is %i."%(self.__class__.__name__,self.__class__.running))         
    
    # 026 It is expected that concrete producers override consume and produce behavior.
    # 026 Default implementation is empty.
    def consume(self): return object()    
    def produce(self,semiProduct): pass#return object() 
    def verifySemiProduct(self,semiProduct): return True
    def checkOutputQueue(self): pass
    def customInitialization(self): return True
  

class LinklistSupplier(AbstractProducer):
    # 025 Probably should be moved into linklist.py
    # 026 inputQueue and inputCondition should be None

    running=0

    def consume(self):
        #linesSip=self.filesAdaptorInstance.loadPartOfAFile(self.filesAdaptorInstance.linklist) # Sip like sip a bit of coffee.
        # TODO: 026 This is a hack. Linklist supplier shouldn't use hydra's property directly. 
        linesSip=self.hydra.filesAdaptorInstance.loadPartOfLinkList(self.settings.fileSipSize)
        linksQueue=self.hydra.linkListInstance.parse2Queue(linesSip)
        return linksQueue

    def verifySemiProduct(self,semiProduct):
        if not isinstance(semiProduct,Queue) or semiProduct.empty(): return False
        else:
            result = True   
            for index in range(semiProduct.qsize()):
                item=semiProduct.get() # 026 Take item for test.
                semiProduct.put(item)  # 026 And put it back to the queue, while item still has it.
                if not isinstance(item,list):
                    result = False
                    self.logger.debug("Item %i in semiProduct is invalid."%(index))
                    break
                for subitem in item:
                    if not isinstance(subitem,str):
                        result = False
                        self.logger.debug("Item %i in semiProduct is invalid."%(index))
                        break
        return result   
    
    def produce(self,semiProduct):
        # Sort out what is needed:
        self.waitForOutputQueue()
        linksQueueDebugFlag=1 # This flag reduces amount of debug messages generated, when LinklistSupplier.outputQueue is full.
        self.outputCondition.acquire()
        while semiProduct.qsize(): # 026 Move all items fromone queue to another.
            if self.outputQueue.full() and linksQueueDebugFlag:
                self.logger.debug("LinklistSupplier.outputQueue is full. LinklistSupplier.outputQueue.qsize: %i; semiProduct.qsize: %i"%(self.outputQueue.qsize(),semiProduct.qsize()))
                linksQueueDebugFlag=0
            self.outputQueue.put(semiProduct.get())
        self.outputCondition.notify()
        self.outputCondition.release()
        self.logger.debug("LinklistSupplier.outputQueue.qsize: %i ."%(self.outputQueue.qsize()))        

    def waitForOutputQueue(self):
        while self.outputQueue.full():
            self.logger.debug("The LinklistSupplier.outputQueue is full. Waiting %s seconds if other thread takes care about it."%(self.settings.timeWaitLinklistSupplier))
            self.outputCondition.acquire()
            self.outputCondition.notify() 
            self.outputCondition.release()
            time.sleep(self.settings.timeWaitLinklistSupplier)    
        # 026 TODO: This is a hack. Hydra shouldn't be called directly.
        waitingTimeAdjustment=-self.hydra.adjustThreadWaitingTime(self.outputQueue.qsize(),self.outputQueue.maxsize,self.settings.timeWaitLinklistSupplier)
        if waitingTimeAdjustment: self.settings.timeWaitLinklistSupplier+=waitingTimeAdjustment                    

    def connectFilesAdaptor(self,filesAdaptorInstance): self.filesAdaptorInstance=filesAdaptorInstance
   

class CompTreeProducer(AbstractProducer):
    
    running=0
    
    # 026 Dropped functionality: Check of the premature end.
    def consume(self):
        #self.debug.printHeader() # 025 Bug Todo:171
        if hasattr(self.inputCondition,"owner") and self.inputCondition.owner:
            self.logger.error("Condition linksAvailable already owned by %s."%(self.inputCondition.owner))
        #self.inputCondition.acquire() # 025 Bug Todo:178 
        #self.logger.debug("Condition linksAvailable acquired by CompTreeProducer %s."%(self.getName())) # 025 Bug Todo:178
        #if self.inputQueue.empty(): self.inputCondition.wait(self.settings.timeSleepNodeQueue) # 025 Bug Todo:178
        self.logger.debug("CompTreeProducer woken-up. inputQueue.qsize: %i; nodeQueue.qsize: %i"%(self.inputQueue.qsize(),self.outputQueue.qsize()))
        if self.inputQueue.qsize(): currentLink=self.inputQueue.get()
        else: currentLink=None # 025 This is because of timeout in linksAvailable.wait. Thread might have get stuck in waiting forever.  
        #self.inputCondition.release() # 025 Bug Todo:178
        self.logger.debug("Condition linksAvailable released by CompTreeProducer %s."%(self.getName()))
        return currentLink

    def verifySemiProduct(self,semiProduct):
        """ Verifies if the semiProduct is a single splitted url. (Not a list of them, not queue, not empty.)"""
        if not isinstance(semiProduct,list) or not semiProduct: return False
        else:
            result = True   
            for subitem in semiProduct:
                if not isinstance(subitem,str):
                    result = False
                    self.logger.debug("Item %i in semiProduct is invalid."%(subitem))
                    break
        return result           

    def produce(self,currentLink):
        self.debug.printHeader()
        tree=None
        self.logger.debug("Current link is: %s"%(str(currentLink)))
        try: # Because of bug Todo 171
            if currentLink: tree=NodeProxy(currentLink,None,None,None,None)
        except KeyError, errorInstance:
            # 026 #self.logger.error("Catched KeyError exception: %s; args: %s"%(str(errorInstance),str(errorInstance.args)))
            self.logger.exception("In thread %s %s caught an exception: \n"%(self.__class__.__name__,self.getName()))
        if tree:
            self.logger.debug("CompTreeProducer %s is going to acquire condition comptreeAvailable."%(self.getName()))
            if hasattr(self.outputCondition,"owner") and self.outputCondition.owner: self.logger.error("Condition comptreeAvailable already owned by %s."%(self.outputCondition.owner))
            self.waitForOutputQueue()
            self.outputCondition.acquire()
            self.logger.debug("Condition comptreeAvailable acquired by CompTreeProducer %s."%(self.getName()))
            self.outputQueue.put(tree)
            self.outputCondition.notify() # signal that a new item is available
            self.outputCondition.release()
            self.logger.debug("Condition comptreeAvailable released by CompTreeProducer %s."%(self.getName()))
        else: self.logger.debug("None tree produced for link %s"%(str(currentLink)))

    def waitForOutputQueue(self):
        while self.outputQueue.full():
            self.logger.debug("The nodeQueue is full. Waiting %s seconds if other thread takes care about it."%(self.settings.timeSleepNodeQueue))
            time.sleep(self.settings.timeSleepNodeQueue)
        # 026 TODO: This is a hack. Hydra shouldn't be called directly.
        waitingTimeAdjustment=-self.hydra.adjustThreadWaitingTime(self.outputQueue.qsize(),self.outputQueue.maxsize,self.settings.timeSleepNodeQueue)
        if waitingTimeAdjustment: self.settings.timeSleepNodeQueue+=waitingTimeAdjustment


                
class CompTreeProcessor(AbstractProducer):
    """ This class represents a single thread for compTree processing."""

    running=0  
 
    def consume(self):
        self.inputCondition.acquire()
        self.logger.debug("Condition comptreeAvailable acquired by CompTreeProcessor %s."%(self.getName()))
        if self.inputQueue.empty():
            tree=None
            self.logger.debug("CompTreeProcessor %s put on hold until notified. nodeQueue.qsize: %i; comptreeResultQueue.qsize: %i"%(self.getName(),self.inputQueue.qsize(),self.outputQueue.qsize())) 
            self.inputCondition.wait(self.settings.timeWaitCompTreeProcessor)
        else:
            self.logger.debug("CompTreeProcessor %s woken-up. nodeQueue.qsize: %i; comptreeResultQueue.qsize: %i"%(self.getName(),self.inputQueue.qsize(),self.outputQueue.qsize()))
            tree=self.inputQueue.get()
        self.inputCondition.release()
        self.logger.debug("Condition comptreeAvailable released by CompTreeProcessor %s."%(self.getName()))
        return tree

    def verifySemiProduct(self,semiProduct):
        if not semiProduct or not isinstance(semiProduct,NodeProxy): return False
        else: return True

    def produce(self,semiProduct):
        """
        This method runs the comptree.operate() and returns enhanced counterManager as a result.
        """
        self.debug.printHeader()
        comptreeResult=CounterManager()
        self.logger.debug("Thread %s is taking care of compTree %s"%(self.getName(),'/'.join(semiProduct.newSplittedLink)))
        try: # Because of bug Todo 171
            # 026 Protected block is alredy in AbstractProducer.run() so here maybr isn't needed.
            start=time.clock()
            comptreeResult=semiProduct.operate()
            end=time.clock()
            comptreeResult.increment("treeOperateTime", end-start)
            self.logger.debug("Operation on tree took %s seconds. Start was %s, end was %s" %(str(end-start),str(start),str(end)))
        except KeyError, errorInstance:
            self.logger.exception("In thread %s %s caught an exception: \n"%(self.__class__.__name__,self.getName()))
            # 026 #self.logger.error("Catched KeyError exception: %s"%(str(errorInstance)))

        # 025 The extend is hack a bit, coz newSplittedLink does not contain ["http",":"].
        # Cannot use link property as in hitlogger case, coz this can be done only for LeafProxy.
        extendedSplittedLink=["http:"]
        extendedSplittedLink.extend(semiProduct.newSplittedLink)
        comptreeResult.title=self.settings.pathStorage.composeURL(extendedSplittedLink)
        # 026 This part was in 025 part of oldRun
        self.logger.debug("Thread %s finished processing of compTree %s. Now is gonna report results."%(self.getName(),comptreeResult.title))
        self.outputCondition.acquire()
        self.outputQueue.put(comptreeResult)
        self.outputCondition.notify() # signal that a new item is available
        self.outputCondition.release()
        self.logger.debug("Thread %s put results of compTree %s into the comptreeResultQueue and unlocked the queue.."%(self.getName(),comptreeResult.title))
        
        return comptreeResult
        
class Hydra(Queue,Shared):
    """
    Hydra is a thread manager. It should create threads and look over their count based on settings.
    #It should manage threads load based on Round Robin. # 025 Deprecated - notification and semaphores used instead.
    Why threading? Because processing of every tree involves many waiting for server reply. 
    Open more connection at once will save a lot of time.
    Hydra should be written without tight bond to CompTreeProcessor, although it is the only Hydra use so far.  
    """
    
    def __init__(self):
        self.initializeGuppy()
        self.initializePsutil()
        self.initializeYappi()
        self.productQueues=[None,None,None]
        self.queueConditions=[None,None,None]
    
    allThreadsStarted = False
    
    def adjustThreadWaitingTime(self,resultQueueLength,resultQueueSize,previousWaitingTime):
        """
        Waiting time of thread should be adjusted acording to length of queue of result.
        Optimal queue occupancy should be between 40 and 60 percent.
        Shall return negative (just) adjustment when occupancy is more than 60%.
        Shall return positive (just) adjustment when occupancy is less 40%.
        The initial adjustment equation is y=-7.5x+3.75 ; where x is queue occupancy and y is time adjustment in seconds.
        This is based on todo 183.
        Returns just the adjustment.
        """
        queueOcupancy=float(resultQueueLength)/float(resultQueueSize)
        if queueOcupancy<0.4 or queueOcupancy>0.6:
            timeAdjustment=self.settings.threadWaitingAdjustmentVector[0]*queueOcupancy+self.settings.threadWaitingAdjustmentVector[1]
            self.logger.debug("Going to adjust queue waitin time by %s to %s. Result Queue Length is %i; Result Queue Size is: %i; Queue Ocupancy is %s"%(timeAdjustment,previousWaitingTime+timeAdjustment,resultQueueLength, resultQueueSize, queueOcupancy))
            if (previousWaitingTime+timeAdjustment)<2 or (previousWaitingTime+timeAdjustment)>600:
                self.logger.warning("Not going to adjust time to be shorter than 2 seconds or longer than 10 minutes. After proposed adjustment waiting time would be %s"%(previousWaitingTime+timeAdjustment))
                timeAdjustment=0
        else: timeAdjustment=0
        return timeAdjustment
    
    def countRunningThreads(self):
        """
        Returns a CounterManager instance with count of each running thread of: 
        LinklistSupplier, CompTreeProducer, CompTreeProcessor and CounterSupervisor
        """
        self.debug.printHeader()
        counters = CounterManager()
        counters.increment("LinklistSupplier",LinklistSupplier.running)
        counters.increment("CompTreeProducer",CompTreeProducer.running)
        counters.increment("CompTreeProcessor",CompTreeProcessor.running)
        counters.increment("CounterSupervisor",CounterSupervisor.running)
        return counters

    def connectProductQueues(self,*args):
        # 026 This is useles, coz I can't make a difference among particular queues.
        # 026 As a temporary solution I assume following order: linksQueue,nodeQueue,comptreeResults
        self.productQueues=[]
        for argument in args:
            if argument.__class__.__name__=="Queue":
                self.productQueues.append(argument)
        self.linksQueue=self.productQueues[0]
        self.nodeQueue=self.productQueues[1]
        self.comptreeResults=self.productQueues[2]  
        return self.productQueues             
    
    # 025 Strategy pattern ??
    def shallContinue(self,strategyName):
        """ Decides if thread shall continue or terminate. """
        if not self.allThreadsStarted:
            self.logger.debug("Termination rejected. Not all threads started.")
            return True
        if strategyName == "LinklistSupplierStrategy": return self.LinklistSupplierStrategy()
        elif strategyName == "CompTreeProducerStrategy": return self.CompTreeProducerStrategy()
        elif strategyName == "CompTreeProcessorStrategy": return self.CompTreeProcessorStrategy()
        elif strategyName == "CounterSupervisorStrategy": return self.CounterSupervisorStrategy()
        else: raise AttributeError, "%s is wrong strategy"%(strategyName)
    
    def LinklistSupplierStrategy(self): 
        if not hasattr(self,"filesAdaptorInstance") or not self.filesAdaptorInstance :
            raise AttributeError, "Instance of Files Adaptor required."
        aFile=self.filesAdaptorInstance.linklist
        if self.filesAdaptorInstance.fileProcessed(aFile): return False
        else: return True
        
    def CompTreeProducerStrategy(self): 
        #if not self.allThreadsStarted: return True # 026 Moved to shallContinue
        if LinklistSupplier.running>0: 
            self.debug.mainLogger.debug("Termination rejected. Some LinklistSuppliers are still running (%i)"%(LinklistSupplier.running))
            return True
        if not self.linksQueue.empty():
            self.debug.mainLogger.debug("Termination rejected. LinksQueue is not empty. qsize: %i" %(self.linksQueue.qsize())) 
            return True
        else: return False
        
    
    def CompTreeProcessorStrategy(self): 
        #if not self.allThreadsStarted: return True # 026 Moved to shallContinue
        if CompTreeProducer.running>0: return True        
        if not self.linksQueue.empty() or not self.nodeQueue.empty(): return True
        else: return False
    
    def CounterSupervisorStrategy(self):
        # 026 This is too butcher constraint, replaced by logging of an error in AbstractProducer.
        #for producerClass in [LinklistSupplier,CompTreeProducer,CompTreeProcessor]:
        #    if producerClass.running<0: raise AttributeError("Count of running threads of %s can't be negative. Currently is %i."%(producerClass.__class__.name,producerClass.running))
        result=False
        for producerClass in [LinklistSupplier,CompTreeProducer,CompTreeProcessor]:
            if producerClass.running>0: result=True
        #if not self.allThreadsStarted: result=True # 026 Moved to shallContinue
        for productQueue in self.productQueues:
            if productQueue.qsize(): result=True
        return result

    def createConditions(self):
        self.linksAvailable=EnhancedCondition() # 025 threading.Condition()
        self.comptreeAvailable=EnhancedCondition() # 025 threading.Condition() 
        self.comptreeResultsAvailable=threading.Condition()
        queueConditions=[self.linksAvailable,self.comptreeAvailable,self.comptreeResultsAvailable]
        return queueConditions
    
    def createQueues(self):
        """Creates linksQueue, nodeQueue and comptreeResults """
        self.linksQueue=Queue(self.settings.linksQueueMaxsize)
        self.nodeQueue=Queue(self.settings.nodeQueueMaxsize)
        self.comptreeResults=Queue(self.settings.comptreeResultsMaxsize)
        self.productQueues[0]=self.linksQueue
        self.productQueues[1]=self.nodeQueue
        self.productQueues[2]=self.comptreeResults
        return self.productQueues
    
    # (026) Hydra could use factory method to create the producers, which are specified as input parameters. 
    # (026) The problem is how to save the results. 
    def createProducers(self):
        """Creates LinklistSupplier, CompTreeProducer, CompTreeProcessor and CounterSupervisor."""
        for producerClass in [LinklistSupplier,CompTreeProducer,CompTreeProcessor]: producerClass.running=0
        self.linklistSupplier=[]
        while len(self.linklistSupplier)<self.settings.linklistSupplierCount:
            self.linklistSupplier.append(LinklistSupplier(self,None,self.linksQueue,None,self.linksAvailable))
        self.compTreeProducer=[]    
        while len(self.compTreeProducer)<self.settings.compTreeProducerCount:
            self.compTreeProducer.append(CompTreeProducer(self,self.linksQueue,self.nodeQueue,self.linksAvailable,self.comptreeAvailable))
        self.compTreeProcessor=[]
        while len(self.compTreeProcessor)<self.settings.compTreeProcessorCount:
            self.compTreeProcessor.append(CompTreeProcessor(self,self.nodeQueue,self.comptreeResults,self.comptreeAvailable,self.comptreeResultsAvailable))
        self.counterSupervisor=[]
        while len(self.counterSupervisor)<self.settings.counterSupervisorCount:
            self.counterSupervisor.append(CounterSupervisor(self,self.comptreeResults,None,self.comptreeResultsAvailable,None))                
        self.producers=[self.linklistSupplier,self.compTreeProducer,self.compTreeProcessor,self.counterSupervisor]
        return self.producers

    def startProducers(self):
        for producersList in self.producers:
            for producer in producersList:
                if not producer.is_alive(): producer.start()
        self.allThreadsStarted=True
        
    def joinProducers(self):
        """ Waiting for all producers to terminate."""
        for producersList in self.producers:
            for producer in producersList:
                self.logger.info("Waiting for thread %s to terminate."%(producer.__class__.__name__))
                producer.join()
    
    def rejuvernateThreads(self):
        # 026 Clean-up producers which are inactive.
        for producersList in self.producers:
            #for producer in producersList:
            for index in range(len(producersList)-1,-1,-1): # 026 Going thru producers from end. If dead producer is removed, the list will be shorter.
                if not producersList[index].is_alive(): del producersList[index]       
        # 026 Create missing producers.
        counter = CounterManager()
        if self.shallContinue("LinklistSupplierStrategy") and len(self.linklistSupplier)<self.settings.linklistSupplierCount:
            while len(self.linklistSupplier)<self.settings.linklistSupplierCount:
                self.linklistSupplier.append(LinklistSupplier(self,None,self.linksQueue,None,self.linksAvailable))
                counter.increment("LinklistSupplier")
        if self.shallContinue("CompTreeProducerStrategy") and len(self.compTreeProducer)<self.settings.compTreeProducerCount:
            while len(self.compTreeProducer)<self.settings.compTreeProducerCount:
                self.compTreeProducer.append(CompTreeProducer(self,self.linksQueue,self.nodeQueue,self.linksAvailable,self.comptreeAvailable))
                counter.increment("CompTreeProducer")
        if self.shallContinue("CompTreeProcessorStrategy") and len(self.compTreeProcessor)<self.settings.compTreeProcessorCount: 
            while len(self.compTreeProcessor)<self.settings.compTreeProcessorCount:
                self.compTreeProcessor.append(CompTreeProcessor(self,self.nodeQueue,self.comptreeResults,self.comptreeAvailable,self.comptreeResultsAvailable))
                counter.increment("CompTreeProcessor")
        if self.shallContinue("CounterSupervisorStrategy") and len(self.counterSupervisor)<self.settings.counterSupervisorCount:
            while len(self.counterSupervisor)<self.settings.counterSupervisorCount:
                self.counterSupervisor.append(CounterSupervisor(self,self.comptreeResults,None,self.comptreeResultsAvailable,None))
                counter.increment("CounterSupervisor")
        if counter.sumAllValues():
            self.logger.info("Following threads rejuvernated: %s"%(counter.printAllValues()))
        # 026 Start newly created producers. StartProducers() wont try to start producer which is running.
        self.startProducers()                
        return self.producers
 
        
    def connectFilesAdaptor(self,filesAdaptorInstance): self.filesAdaptorInstance=filesAdaptorInstance
    def connectLinkListInstance(self,linkListInstance): self.linkListInstance=linkListInstance

    def initializeGuppy(self):    
        try:
            # Memory measuring according:
            # http://stackoverflow.com/questions/552744/how-do-i-profile-memory-usage-in-python
            # To make work guppy in Python 2.7 you need following:
            # 1) sudo apt-get install subversion
            # 2) sudo pip install https://guppy-pe.svn.sourceforge.net/svnroot/guppy-pe/trunk/guppy
            # http://stackoverflow.com/questions/110259/python-memory-profiler
            # Guppy tutorial:
            # http://www.smira.ru/wp-content/uploads/2011/08/heapy.html
            self.guppyInitialized=False
            if self.debug.mainLogLevel==DEBUG: # Only get this info, when is gonna be logged.
                from guppy import hpy
                self.heapy=hpy()
                self.guppyInitialized=True
                self.debug.mainLogger.debug("Guppy initialization successful.")
        except ImportError:# 026#, errorInstance:
            self.debug.mainLogger.debug("Memory consumption cannot be logged because guppy module was not found.")
            self.debug.mainLogger.debug("In Hydra caught an exception: \n")
            self.guppyInitialized=False
            
    def initializePsutil(self):
        try:
            # CPU & Memory measuring according:
            # http://code.google.com/p/psutil/
            self.psutilInitialized=False
            if self.debug.mainLogLevel==DEBUG: # Only get this info, when is gonna be logged.
                import psutil
                self.psutil=psutil
                self.psutilInitialized=True
                self.debug.mainLogger.debug("PSUtil initialization successful.")
        except ImportError:
            self.debug.mainLogger.debug("CPU consumption cannot be logged because psutil (python-psutil) module was not found.")
            self.psutilInitialized=False
            
    def initializeYappi(self):
        # 027 Yet Another Python Profiler, but this time Thread-Aware
        # 027 https://code.google.com/p/yappi/
        try:
            self.yappiInitialized=False 
            # Only get this info, when is gonna be logged.
            if self.debug.mainLogLevel==DEBUG and not self.yappiInitialized: 
                import yappi
                self.yappi=yappi
                if not self.yappi.is_running(): self.yappi.start()
                self.yappiInitialized=True
        except ImportError:
            self.debug.mainLogger.debug("No profiling with Yappi. Module was not found.")
            self.yappiInitialized=False        
    
    def measureHWResources(self):
        """ Writes down CPU and MEM usage."""
        # 026 self.logger cannot be used because it creates dummy thread and ThreadAwareLogger creates new handler for each write.
        self.debug.printHeader()
        heappyResult=CPUUsage=MemUsageMB=None
        try:
            if self.guppyInitialized:
                heappyResult=self.heapy.heap()
                self.debug.mainLogger.debug(heappyResult)
            if self.psutilInitialized:
                CPUUsage=str(round(self.psutil.cpu_percent(),1))
                MemUsageMB=str(self.psutil.used_phymem()/1048576)
                self.debug.mainLogger.debug("Current CPU usage is %s%%. Currently used physical memory size is %s MB."%(CPUUsage,MemUsageMB))
        except ValueError, errorInstace:
            self.debug.mainLogger.debug("Caught ValueError: %s"%(errorInstace))  
            self.debug.mainLogger.debug("In %s caught an exception: \n"%(self.__class__.__name__)) 
        return [heappyResult,CPUUsage,MemUsageMB]     
    
    def measureQueues(self): return [self.linksQueue.qsize(),self.nodeQueue.qsize(),self.comptreeResults.qsize()]
    
    def getActiveThreadNames(self):
        """ Return all thread names. Quite costy function. """
        activeThreadsNames=""
        activeThreads=threading.enumerate()
        for thread in activeThreads:
            if len(activeThreadsNames): activeThreadsNames+=','
            activeThreadsNames+=thread.getName()
        return activeThreadsNames         
    
class CounterSupervisor(AbstractProducer):
    """
    Purpose of this class is to manage counters on Global Sumid level.
    It is expected that only one instance will be created. The possibility of reusing is very low.
    """
    
    #running=0

    def customInitialization(self): 
        self.allFilesCount=CounterManager()
        self.lastAllTrees=0
        self.periodStart=time.time()
        return True

    def consume(self):
        self.inputCondition.acquire()
        if self.inputQueue.empty(): self.inputCondition.wait(self.settings.timeWaitCounterSupervisor) # sleep until item becomes available
        self.logger.debug("CounterSupervisor woken-up. counterManagerQueue.qsize: %i"%(self.inputQueue.qsize()))
        if self.inputQueue.qsize():
            comptreeResult=self.inputQueue.get()
        else: 
            comptreeResult=CounterManager()
            comptreeResult.reset()
            self.logger.debug("%s threads still active. (Including self and main thread.)"%(threading.activeCount()))
        self.inputCondition.release()
        return comptreeResult
    
    def verifySemiProduct(self,semiProduct):
        if not semiProduct or not isinstance(semiProduct,CounterManager): return False
        else: return True
    
    # 026 Originally meant as a pure consumer. In fact there is no output queue. But following part produces some output.
    def produce(self,semiProduct):
        # 025 Should I refresh counters if no result was processed?
        semiProduct.addCounters(self.settings.defaultCounters)
        allFilesCount = self.refreshCounters(semiProduct)
        # 026 Another hack of direct calling hydra. Need to preserve counters.
        self.hydra.allFilesCount=allFilesCount
        self.periodLength=time.time()-self.periodStart
        if self.periodLength>=self.settings.schedulerDelay:
            self.measurePerformance()
            self.periodStart=time.time()
            # 026 # self.hydra.rejuvernateThreads()        
    
    #def refreshCounters(self,counterManagerQueue):
    def refreshCounters(self,comptreeResult):
        """
        Incorporates individual counterManagers into global counters.
        Returns refreshed global counters.
        Should log (on debug or info level?) change in global counters after adding each individual counter?
        Otherwise it's not possible to log counters after each tree. 
        """ 
        self.debug.printHeader()

        if comptreeResult.title: # 026 WTF? Why it has to have title?
            ##allFilesCount+=comptreeResult # 025 Nice variant of following line - TO DO: 121
            self.allFilesCount.mergeWithManager(comptreeResult)
            self.allFilesCount.increment("allTrees")
            self.debug.cntLogger.info("\"%s\"; %s"%(comptreeResult.title,comptreeResult.printAllValuesOnly()))
            if comptreeResult.value("patternFound")<=1:
                self.allFilesCount.increment("linearPatternTrees") #That means one or less pattern in whole tree.
                self.debug.nopLogger.info(comptreeResult.title)
            if comptreeResult.value("hits")<=1 and comptreeResult.value("patternFound")>1: 
                self.allFilesCount.increment("linearHitsTrees") #That means one or less hits in whole tree.
                self.debug.missLogger.info(comptreeResult.title)
            if self.allFilesCount.value("linearHitsTrees")>self.allFilesCount.value("allTrees"):
                self.logger.warning("linearHitsTrees counter has now bigger value than allTrees, which is not possible. Url: %s"%(comptreeResult.title))
            if self.allFilesCount.value("linearPatternTrees")>self.allFilesCount.value("allTrees"):
                self.logger.warning("linearPatternTrees counter has now bigger value than allTrees, which is not possible. Url: %s"%(comptreeResult.title))                

            self.logger.info("State of counters is : %s after operation in node %s"%(self.allFilesCount.printAllValues(),comptreeResult.title))
            # 026 TODO: This is a hack. Hydra shouldn't be called directly.
            if self.debug.mainLogLevel==DEBUG: # Only get this info, when is gonna be logged.
                activeThreadsNames=self.hydra.getActiveThreadNames()
                self.logger.debug("Active threads are: %s;"%(activeThreadsNames))
            qsizes=self.hydra.measureQueues()
            self.debug.qszLogger.info("Queue sizes are: (*.qsize:) linksQueue: %i; nodeQueue: %i; counterManagerQueue: %i; after operation in node %s"%(qsizes[0],qsizes[1],qsizes[2],comptreeResult.title))
      
            return self.allFilesCount
    
    def measurePerformance(self):
        treesPerInterval=self.allFilesCount.value("allTrees")-self.lastAllTrees
        self.lastAllTrees=self.allFilesCount.value("allTrees")
        #minutesPerInterval=self.settings.schedulerDelay/float(60) #025
        minutesPerInterval=self.periodLength/float(60)
        treesPerMinute=treesPerInterval/minutesPerInterval
        self.logger.info("Current TPM is: %s"%(treesPerMinute))
        #self.scheduler.enter(self.settings.schedulerDelay, 1, self.measurePerformance, ()) #025
        # 026 hydra.measureHWResources() takes down CounterSupervisor. See 222.
        # self.hydra.measureHWResources()
        # 026 Rejuvernating threads doesn't belong here, but before hydra has cron, it shal be here.
        self.hydra.rejuvernateThreads()


#body begin

if __name__ == "__main__":

    print greetingPrompt

    settings = Settings() #might be needed in comptree, but this class is singleton.
    settings.loadAdaptive("all")#,settings.pathStorage)
    # 026 Following comment is probably obsolete or wrong. 
    # loadAdaptive has to be called after creating Debug instance, because Debug.__init__() overwrites it => Singleton doesn't work. Maybe it is because Singleton does work!
    Shared.settings=settings
    
    debug = Debug(settings) #might be needed in comptree, but this class is singleton.
    Shared.debug=debug
    
    factory=FactoryMethod()
    #pathStorage isn't instance of pathStorage, but instance of its conrete subclass
    
    settings.pathStorage=factory.create(eval(settings.platform+'PathStorage')) # 026 Settings itself doesn't really use the PathStorage.
    # 026 Following comment is probably outdated. I can't see place where Debug.__init__() overwrites pathStorage.
    # pathStorage has to be filled after creating Debug instance, because Debug.__init__() overwrites it => Singleton doesn't work. Maybe it is because Singleton does work!
    factory.sharedRef.pathStorage=settings.pathStorage 

    files=FilesAdaptor()
    settings.connectFilesAdaptor(files)
    linklist=LinklistAdaptor()

    debug.ThreadAwareLogger.debug("Threading hell begin. Creating all queues.")
    hydra = Hydra() # 025 This is pool of threads. 
    hydra.connectFilesAdaptor(files)
    hydra.connectLinkListInstance(linklist)
    linksQueue=Queue(2*settings.fileSipSize)
    nodeQueue=Queue(settings.fileSipSize)
    comptreeResults=Queue()
    hydra.connectProductQueues(linksQueue,nodeQueue,comptreeResults)

    debug.ThreadAwareLogger.debug("Creating events, locks and conditions")
    """ 026 Taken over by hydra
    linklistSupplierFinishFlag=threading.Event()
    compTreeProducerFinishFlag=threading.Event()
    compTreeProcessorFinishFlag=threading.Event()
    linksAvailable=EnhancedCondition() # 025 threading.Condition()
    comptreeAvailable=EnhancedCondition() # 025 threading.Condition() 
    comptreeResultsAvailable=threading.Condition()
    """
    hydra.createConditions()
    hydra.createQueues()
    debug.ThreadAwareLogger.debug("Creating threads.")
    hydra.createProducers()
    
    # 026 #def __init__(self,hydra,inputQueue,outputQueue,inputCondition,outputCondition)
    """ 026 Taken over by hydra    
    hydra.put(LinklistSupplier(hydra, None, linksQueue, None, linksAvailable))
    hydra.put(CompTreeProducer(hydra, linksQueue, nodeQueue, linksAvailable, comptreeAvailable)) #, linklistSupplierFinishFlag,compTreeProducerFinishFlag))
    for index in range(settings.maxThreads):
        hydra.put(CompTreeProcessor( hydra, comptreeResults, nodeQueue, comptreeResultsAvailable, comptreeAvailable, compTreeProducerFinishFlag))
    counterSupervisor=CounterSupervisor(hydra, linksQueue, nodeQueue, comptreeResults, comptreeResultsAvailable, compTreeProcessorFinishFlag)
    # 025 counterSupervisor cannot be put into hydra, because it has to wait until all threads in hydra are done (particularily CompTreeProcessor threads) before it can end too. """
    debug.ThreadAwareLogger.debug("All CompTreeProcessor threads created.")

    csvHeader="url"
    for key in sorted(settings.defaultCounters):
        csvHeader+="; "
        csvHeader+=str(key)
    debug.cntLogger.info(csvHeader)

    scheduler=SchedulerManager()
    scheduler.add_operation(hydra.rejuvernateThreads, settings.schedulerDelay)
    scheduler.add_operation(hydra.measureHWResources, settings.schedulerDelay)

    debug.ThreadAwareLogger.debug("Starting threads.")
    hydra.startProducers()
    """ 026 Taken over by hydra   
    for index in range(hydra.qsize()):
        currentThread=hydra.get()
        currentThread.start()
        hydra.put(currentThread)
    counterSupervisor.start()
    hydra.allThreadsStarted=True"""

    debug.ThreadAwareLogger.debug("All threads started.")
    

    # 025 From some strange reason join() doesn't work as I expected. But if it did following two lines would be proper ways ho to set the flag.
    #hydra.join()
    #debug.ThreadAwareLogger.debug("All threads in hydra joined.")
    #compTreeProcessorFinishFlag.set()

    debug.ThreadAwareLogger.debug("Waiting for all threads to finish.")
    
    hydra.joinProducers()    

    scheduler.stop()
    debug.ThreadAwareLogger.info("Final state of counters is: %s"%(hydra.allFilesCount.printAllValues())) # 025 Done by counterSupervisor
    
    if hydra.yappiInitialized: 
        #debug.ThreadAwareLogger.debug("\n %s"%(hydra.yappi.get_stats(hydra.yappi.SORTTYPE_TSUB,hydra.yappi.SORTORDER_DESC,1000)))
        yappiLog=file("%s/yappi.log"%(settings.logDir),"w")
        hydra.yappi.print_stats(out=yappiLog, sort_type=hydra.yappi.SORTTYPE_TSUB, sort_order=hydra.yappi.SORTORDER_DESC, limit=1000,thread_stats_on=True)
     
    debug.ThreadAwareLogger.info("Sumid finished without Critical Errors")
    print "Sumid finished without Critical Errors"

#body end
