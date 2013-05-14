# This file is part of SUMID, see sumid.py
# SUMID is released under terms of GPL, see http://www.gnu.org/licenses/gpl.txt

__version__="0.26"

from copy import copy
import urllib2
import re
import os.path
import sys
# import miscutil # 026
from miscutil import Shared, NotImplementedYetError,CounterManager,Debug #026 Debug class needed to support ThreadAwareLogger#, PrintUris, , InvalidFileTypeError 
# import settings #026
from httplib import BadStatusLine
import time

class Component(Shared):
    """
    Composite pattern abstract node by Pasteur Institute ( http://www.pasteur.fr/formation/infobio/python/ch18s06.html#fig_tree_composite )
    This class is abstract node (Component) containing common operations for Composite and Leaf
    It should create tree from provided link, and then process whole tree with operation given.
    """
    #logger=Debug.ThreadAwareLogger # 026 in shared
    #children=[] # Needed in addSibs() for both NodeProxy and LeafProxy.
    #processedChildren=[] # Used in NodeProxy.operation() as a secondary stack.
            
    def __init__(self): 
        """ Creating instances of Component class is restricted. Component is considered as abstract class. """
        raise NotImplementedError, "This is abstract class. No instance allowed."
    
    def operate(self):
        """
        Operation in comptree is download, log or their combination.
        (Operation is defined term in Composite pattern.)
        This method is just base for polymorfing.
        No reason to call it in abstract Component. 
        """
        raise NotImplementedError
    
    #def parent(self): raise NotImplementedError
    # Reference to parent not needed? Dunno why...  
    
    def subtree(self):
        """
        Returns a tuple of children of current node or None when current node is leaf.
        This is default implementation, which fits to every intermediate node, root, but not to leaf.  
        """
        return self.children
    
    def handleLink(self,splitted=None,oneString=None):
        """
        Checks kind of provided link(splitted or onestring) and always returns it in splitted form.
        Cannot be used in composite instance, but this default implementation doesn't need to be overriden.
        
        At least link should be treated as parameter, even though it is variable of same class.
        """
        self.debug.printHeader()
        if self.__class__.__name__=='Component': raise NotImplementedError,'Cannot be used in Component instance' 
        # It uses properties from their children. Cannot happen, coz of __init__ .
        if self.newSplittedLink: splittedLink=copy(self.newSplittedLink)
        elif self.newLink: splittedLink=self.newLink.split('/')
        else: raise ValueError, "Link must be provided! Can't be None or empty."
        return splittedLink
    
    def removeComponent(self): # 
        """ It's more destroy, then remove component. Not sure if it works. """
        if self.children:
            for child in self.children: del child
        del self

    def destroy(self):
        """
        For every child call child.remove() <-- This is original comment from previous version(016).
        Probably competition for removeComponent. Currently(021) I see no difference.
        Maybe it's just about method name. destroy may be better, no reason to repeat "component", when it's component method. 
        """ 
        raise NotImplementedYetError         
    
    def loadFromInterface (self,splittedLink=None,link=None,parent=None,previous=None,next=None): # Replace with *args?
        """
        Transforms input parameters into object attributes.
        This method would be useful in more general form in miscutil.
        """ 
        self.debug.printHeader()
        if self.__class__.__name__=='Component': raise 'cannot be used in Component instance' 
        # It uses properties from their children. Cannot happen, coz of __init__ .
        #self.debug.dprint(self.__class__.__name__,4) # Commented out in 0.24
        self.parent=parent
        self.newLink=link # Maybe useless storing into object. Is it used later?
        self.splittedLink=splittedLink
        self.previous=previous
        self.next=next
    
    def commonInit(self):
        """
        Initializing steps common for all nodes of comptree.
        Designed to be called from self.__init__ only.
        """
        #Content was probably(021) moved to loadFromInterface and no other things don't match here.
        if not hasattr(self,"counters"): self.counters = CounterManager()
    
    def createSibsContent(self):
        """ 
        From Component.content() generates neighbors. (That means try to fill variables previous and next.)
        Based on flooding search principle.
        """
        #self.debug.printHeader() # 026 Called too often.
        if not hasattr(self,'pattern'): self.pattern=PatternAnalyser()
        previousSibContent=None
        nextSibContent=None
        # 0.24 commented out
        #if self.previous: self.debug.dprint(self.previous.link,4)
        #else: self.debug.dprint('None',4)
        #if self.next: self.debug.dprint(self.next.link,4)
        #else: self.debug.dprint('None',4)
        if not self.previous: previousSibContent=self.pattern.iterate(self.content,1,True)
        if not self.next:     nextSibContent=    self.pattern.iterate(self.content,1,False)
        if previousSibContent: self.counters.increment("patternFound")
        if nextSibContent: self.counters.increment("patternFound")
        self.logger.debug("Component created content for siblings as follows: %s, %s"%(previousSibContent,nextSibContent))
        return [previousSibContent,nextSibContent]
    
    def addSibs(self,sibsContent=None): 
        """
        This method inserts sibs created in createSibsContent into whole tree hierarchy.
        To be exact, just sets links to parent and neighbors and calls parents method addComponent to actually create new node.
        Sibs adding logic could be moved to pattern analyzer, when whole node is sent as parameter.
        
        Called from leaf.operation. Agreed that this must start from bottom, but shouldn't be this performed by parent?
        """
        self.debug.printHeader()
        if not sibsContent: sibsContent=self.createSibsContent()
        tail=[None,None] # Tail is the tail of the splitted link (for both siblings).
        
        for cx in range(2):
            tail[cx]=[sibsContent[cx]]
            if self.processedChildren:
                # (024) If created sibling is not leaf, I have to hand him a child.
                # (024) I assume that in NodeProxy siblings are created AFTER processing children.
                tail[cx].extend(self.processedChildren[0].newSplittedLink) # 024 Splitted link in LeafProxy instance was empty.
                if sibsContent[cx]: self.debug.comptreeLogger.debug("Going to create NodeProxy sibling with tail %s"%(tail[cx]))
            elif self.children: # When the first child is processed, list of processedChildren is empty.
                tail[cx].extend(self.children[0].newSplittedLink)
                if sibsContent[cx]: self.debug.comptreeLogger.debug("Going to create NodeProxy sibling with tail %s"%(tail[cx]))
            
        if sibsContent[0]: 
            self.parent.addComponent(tail[0],None,self.parent,None,self)
        if sibsContent[1]:
            self.parent.addComponent(tail[1],None,self.parent,self,None)

        #if sibsContent[0]: self.parent.addComponent(None,sibsContent[0],self.parent,None,self) # 024 removed - adapted for NodeProxy
        #if sibsContent[1]: self.parent.addComponent(None,sibsContent[1],self.parent,self,None) # 024 removed - adapted for NodeProxy
        
#    def oldSibsExtendDecision(self):
#        """
#        Tries to find neighbor/sib of current node.   
#        Replaces previousRange concept from Sumid 0.08 - but maybe is worse.
##        Is more complicated, but closer follows provided link.
#        
##        Search neighbor only if operation/get of current node was successful.
#        Then does steps to both sides until previousRange is reached (then result of search is false).
#        When closest neighbor is found search is finished with true result.
#        
#        Called from leaf.operation. Which is wrong.
#        """
#        #self.debug.printHeader(4) # 025 Makes unittest fail.
##        leftSib=self.previous
# #       rightSib=self.next
#        addSib=False
#        # Needs to be corrected at the beginning //what???(021)
#        # (024) When first leaf in branch is created, status of operation at sib is not defined.
#        for sib in range(self.settings.previousRange): 
#            if leftSib  and leftSib.status<300: addSib=True
#            # if status/100==1 means if result of operation was 1xx then makes sense to search for next sib. 
#            if rightSib and rightSib.status<300:addSib=True
#            if addSib: break
#            if leftSib: leftSib= leftSib.previous
#            if rightSib:rightSib=rightSib.next
#        
#        if self.parent and hasattr(self.parent,"processedChildren"): # Root Node has no parent;, but then the part after and wouldn't be necessary.
#            if len(self.parent.processedChildren)<2*self.settings.previousRange:addSib=True # correction for node operation start
#            if len(self.parent.processedChildren)>self.settings.sibsLimit:
#                self.debug.comptreeLogger.warning("Forcefully limiting adding of more siblings for: %s"%(self.link)) 
#                addSib=False #temporary for test reasons
#        else: addSib=False # Root Node has no parent;
#        if hasattr(self,"counters") and self.counters.value("patternFound")>=self.settings.maxTrialsPerTree:
#            # 025 # Limit hits per tree. Configurable. Todo 157. 
#            addSib = False
#            self.debug.comptreeLogger.warning("Forcefully limiting (per Tree limit) adding of more siblings for: %s"%(self.link))
#        return addSib

    def sibsExtendDecision(self):
        """
        Makes decision, if another pair of sibs should be added. (result = True/False)
        Starts from seed and goes to both sides.
        
        Sibs should be added only if the operation on current node was successful. (Status<300)
        But there is a certain tolerance. (settings.previousRange)
        There are also limits of nodes created for the whole tree and for current sibs level. (settings.maxTrialsPerTree, settings.sibsLimit)
        If one of the limits is reached, False is returned without respect to status of current node.
        """
        self.debug.printHeader(4)
        addSib=False
        trialsPerTree=self.counters.value("patternFound")
        # 026 First decide about limits for sibs adding.
        if hasattr(self,"parent") and hasattr(self.parent,"processedChildren"): sibsCount=len(self.parent.processedChildren)
        else: sibsCount=1 # Root Node has no parent.
        if trialsPerTree<self.settings.maxTrialsPerTree and sibsCount<self.settings.sibsLimit:
            if sibsCount<2*self.settings.previousRange:addSib=True # correction for node operation start
            else:
                # 026 This is the core decision based on status.
                leftSib=self.previous
                rightSib=self.next
                for sib in range(self.settings.previousRange):
                    if leftSib  and leftSib.status<300: addSib=True
                    if rightSib and rightSib.status<300:addSib=True
                    if addSib: break # 026 After discovery of one successful sibling we can stop searching.
                    if leftSib: leftSib= leftSib.previous
                    if rightSib:rightSib=rightSib.next 
        else:
            addSib=False    
            self.debug.comptreeLogger.warning("Forcefully limiting adding of more siblings. TrialsPerTree: %i; SibsCount %i; url: %s "%(trialsPerTree,sibsCount,self.link))   
        return addSib
        

        # TODO: write Shared.loadFromInterface() with use of Debug.getCallerName
        
class DistantFile(Shared):# Afaik inheritance from NodeProxy not needed.
    def __init__(self):
        self.content=None
        #self.logger=self.debug.enrichMainLogger("distFilL") #026
        # 026 in Shared #self.logger=self.debug.ThreadAwareLogger
        self.counters=CounterManager()
        
    def safeOpen(self,distantFileURL):
        """
        Loads the content of the distant file. But doesn't return the content, but only return code.
        Originally called "load", but renamed because of the open/close logic.
        Method safeOpen does catch some exceptions, Encapsulates the self.open(). 
        """
        #self.debug.printHeader() # 026 Replaced, because is called very often.
        self.logger.debug("Calling method comptree.DistantFile.safeOpen with argument %s"%(str(distantFileURL)))
        # (024) Previously here was a result value which returned 1 when a file was successfully downloaded. 
        self.status=510 # Unless you know everything goes good, assume that something wrong happens.
        try:
            self.open(distantFileURL)
            self.processInfo()
            if self.isMIMETypeCorrect():
                if hasattr(self,"content"): self.status=200 # Otherwise stays 500. Content is never None.
                if hasattr(self,"returnCode"): 
                    self.status=self.returnCode # Open could return 200 even if the content-type is incorrect.
                    if self.returnCode>399: self.counters.increment("statusResponseMiss")
            if self.settings.checkContentLenth and self.info.has_key("content-length") and self.contentLength==0:
                self.logger.warning("Distant file "+ self.distantFileURL+" is empty.")
                self.counters.increment("zeroLengthMiss")
                self.status=515
            if self.settings.checkRetrievedURL:
                retrievedURL=self.content.geturl()
                if not retrievedURL==self.distantFileURL:
                    self.logger.warning("Different content with url "+retrievedURL+" instead of distant file "+ self.distantFileURL+" was fetched.")
                    self.counters.increment("differentURLMiss")
                    self.status=516 
        #except InvalidFileTypeError: self.status=501 # I can raise this exception one line above and catch it here. Does that make sense?
        except urllib2.HTTPError, errorInstance: 
            self.status=errorInstance.code # 024 replaced original 502
            self.counters.increment("errorResponseMiss")
        except urllib2.URLError, errorInstance: 
            self.status=513
            self.counters.increment("errorResponseMiss")
        except BadStatusLine, errorInstance: self.status=517
        except KeyboardInterrupt:
            # 024 #self.debug.dprint('Interrupt processing? [Y/n]',0)
            #This is not a debug message. This is interaction with user.
            #It shouldn't be done when running in background, but in that case keyboard interrupt can't occur.
            print "Interrupt processing? [Y/n]" 
            interruptAnswer=raw_input()
            self.status=514
            if not interruptAnswer.lower()=='n': sys.exit()
        return self.status


    def open(self,distantFileURL):
        """
        Loads the content of the distant file.
        Originally called "load", but renamed because of the open/close logic.
        Should be called thru DistantFile.safeOpen(), coz this variant is not protected against urllib2 exceptions. 
        """
        #self.debug.printHeader() # 026 Replaced, because is called very often.
        self.debug.headerLogger.debug("Calling method comptree.DistantFile.open with argument %s"%(str(distantFileURL)))
        self.distantFileURL=distantFileURL
        self.requestHeaders=self.createRequestHeaders(distantFileURL)
        self.request=self.createRequest(self.requestHeaders,distantFileURL)
        # In multithreaded is needed to use time.time() and not time.clock(): http://linuxgazette.net/107/pai.html
        start=time.time()
        self.content=urllib2.urlopen(self.request)
        end=time.time()
        self.logger.debug("Distant file on address %s successfully opened by urllib2.urlopen()." %(distantFileURL))
        self.counters.increment("urlopenTime", end-start)
        return self.content
            
    def createRequestHeaders(self,distantFileURL):
        """
        Returns the RequestHeaders which would be used for operation.
        Return value contains Referer (distant file directory) and User-Agent (which is configurable in settings).
        Maybe it should be named create.
        """
        self.debug.printHeader()
        self.requestHeaders={'Referer':os.path.split(distantFileURL)[0],'User-Agent':self.settings.userAgent}
        # 026 temporary #self.requestHeaders={'Referer':"http://glam0ur.com",'User-Agent':self.settings.userAgent}
        return self.requestHeaders            
    
    def createRequest(self,requestHeaders,distantFileURL):
        """ Request includes modified referer and also link to distant file. """
        self.debug.printHeader()
        request=urllib2.Request(distantFileURL,None,requestHeaders)
        return request 
    
    def processInfo(self):
        if self.content:
            self.info = self.content.info()
            self.urllib2Info=""
            # 025 Constructing of urllib2Info is useless. Can be replaced by str(self.info).
            # This method is useful only when part of info is used later. 
            if self.info.has_key("content-type"):
                self.contentType=self.info["content-type"] 
                self.urllib2Info+="content-type: %s, "%(self.info["content-type"])
            else: self.contentType="unknown"
            if self.info.has_key("content-length") and self.info["content-length"].isdigit():
                self.contentLength=int(self.info["content-length"])
                self.urllib2Info+="content-length: %s, "%(self.info["content-length"])
            else: self.contentLength=0
            if self.info.has_key("last-modified"): self.urllib2Info+="last-modified: %s, "%(self.info["last-modified"])
            #HTTPResponse unfortunately not present in info() result.
            #Following works in 2.6 only 
            if hasattr(self.content,"getcode"):
                self.returnCode=self.content.getcode()
                self.urllib2Info+="error-code: %s, "%(self.returnCode)
            #self.logger.debug(self.urllib2Info) # 025
            self.logger.debug(str(self.info))
            #return self.urllib2Info #025
            return str(self.info)
          
    def filterMIMETypes(self):
        """
        Purpose of this if is to catch unwanted file types, but not do operation yet.
        Checks the content-type of distant file.
        Responds to the question: Should be file discarded? Which is reverse logic a bit.
        Returns true if the file should be filtered/scraped!!!
        """
        # TODO: 024 CHange logic to: isMIMETypCorrect => this is deprecated.
        # Does mimetype download whole file or just what is needed to guess?? My test downloads just 5 characters.
        # 0.24 Just basic copy/paste - need to adapt to new situation.
        self.debug.comptreeLogger.warning("This method is deprecated. Use isMIMETypCorrect instead.")
        result=False # Means file is okay and shouldn't be discarded. 
        #if self.settings.forcemimetypes: #025
        if self.settings.forceMIMETypes: 
            if not (self.contentType in  self.settings.allowedMIMETypes):
                self.logger.warning("Unwanted file type: "+self.contentType+" of distant file "+ self.distantFileURL)
                result = True # Means file is wrong. Scrap it!
            if not (self.contentType in self.settings.possibleMIMETypes):
                self.logger.warning("Unrecognized file type: "+self.contentType+" of distant file "+ self.distantFileURL)
                result = True # Means file is wrong. Scrap the file!
        return result

    def isMIMETypeCorrect(self):
        """
        Purpose of this if is to catch unwanted file types, but not do operation yet.
        Checks the content-type of distant file.
        """
        # Does mimetype download whole file or just what is needed to guess?? My test downloads just 5 characters.
        result=True # Means file is okay and shouldn't be discarded.
        # This is workaround for content types like "text/html; charset=UTF-8" or "text/html; charset=windows-1254". Todo 154.  
        if self.contentType.count(';'): contentType=self.contentType.split(';')[0]
        else: contentType=self.contentType
        #if self.settings.forcemimetypes: # 025
        if self.settings.forceMIMETypes:
            if not (contentType in  self.settings.allowedMIMETypes):
                self.logger.warning("Unwanted file type: "+contentType+" of distant file: "+ self.distantFileURL)
                result = False # Means file is wrong. Scrap it!
            if not (contentType in self.settings.possibleMIMETypes):
                self.logger.warning("Unrecognized file type: "+contentType+" of distant file: "+ self.distantFileURL)
                result = False # Means file is wrong. Scrap the file!
        return result
    
    def writeToLocalFile(self):
        """
        Should write the distant file locally, filesAdaptor.writeFile does good job. 
        """
        # Opening distant file, or just scanning, what is avail without downloading it.
        # FilesAdaptor.writeFile is a bit complicated to do it right away.
        self.settings.filesAdaptor.writeFile(self.distantFileURL,self.content)
        # Could also create new file object, which already knows how to write itself.  
    
    def close(self):
        if self.content: self.content.close()  
#"""


class LeafProxy(Component):
    """
    Leaf component of composite pattern.
    Need to change name of class.
    Children of leaf should be always None.
    
    There is question if every Node isn't leaf before generating of children.
    This idea will require to morph Leaf to Node, which is currently not possible.
    On the other hand tree is generated from link with constant length.
    So i know in advance what is going to be leaf. 
    """
    #TODO: 024 LeafProxy shall be turned into abstract class.
    #TODO: 024 Consider usage of **kwargs    
    def __init__(self,splittedLink=None,link=None,parent=None,previous=None,next=None):
        """
        In this case is splittedLink equal to link. But interface has to be same as in NodeProxy.
        There is big mess in many different variables containing link in its names.
        """
        self.debug.printHeader(4) # Trace log level :-)
        # 026 #self.logger=self.debug.ThreadAwareLogger
        self.children=None # 024 Can't be moved to Component. Otherwise the tree is not created properly.
        self.processedChildren=[] # 024 Can't be moved to Component. Otherwise the tree is not created properly.
        self.loadFromInterface(splittedLink,link,parent,previous,next)
        self.newSplittedLink=self.splittedLink  # used in both cases (runlenght, flooding)        
        self.splittedLink=self.handleLink(self.newSplittedLink,self.newLink) # used only in runlenght
        # Hidden parameter is link ... area for improvement.
        self.content=self.splittedLink.pop(0)
        if len(self.splittedLink)>0: 
            self.logger.error("Leaf component has children")
        self.link=link+'/'+self.content
        self.status=0
        # Initialize the proper operation:
        #self.operation=self.concreteOperation # Assignment of a method.
        if not hasattr(self,"counters"): self.counters = CounterManager() # Should be created by commonInit()
        self.counters.addCounter("hits")
        self.distantFile=DistantFile()
        
    def operate(self):
        """
        Download or Log is a specific kind of operation of Composite pattern.
        Operation is main purpose of Sumid.
        Returns an CounterManager Instance (which currently has only 'hits' counter with value 0 or 1.
        """
        # (024) Previously here was a result value which returned 1 when a file was successfully downloaded.
        self.status=self.distantFile.safeOpen(self.link)
        self.counters.mergeWithManager(self.distantFile.counters)

        # Following line should be done by parent. (024) Hardly possible - this would change the current logic from creating nodes at same level to creating nodes at child level.
        if self.sibsExtendDecision(): self.addSibs() 
        if self.status<300: # If status is 2xx everything is okay.
            #result=1 # 024 replaced by self.counters.increment("hits")
            if not self.settings.printUris: # 024 This is temporary solution for operation without download.
                self.settings.filesAdaptor.writeFile(self.link,self.distantFile.content)
            # Change to self.settings.filesAdaptor.writeImage(self).
            # Could also create new file object, which already knows how to write itself.
            self.debug.hitLogger.info(self.link)             
            self.counters.increment("hits")
            self.counters.increment("contentLength",self.distantFile.contentLength)
        else:
            # 024 #self.debug.comptreeLogger.warning('Something wrong during processing distant file %s'%(self.link))
            # 026 replaced by thread aware logger #self.debug.comptreeLogger.warning("When processing distant file %s, an error %s occurred."%(self.link,self.status))
            self.logger.warning("When processing distant file %s, an error %s occurred."%(self.link,self.status))
            # 024 #self.debug.comptreeLogger.warning("When processing distant file %s, failed to reach server. Reason: %s Setting status 503."%(self.link,errorInstance.reason))            
            #result=0 # 024 replaced by self.counters.addCounter("hits")
        #return result # 024 replaced by return self.counters
        # Maybe shall be done even if the distantFile.open() raises exception. (In finally block.)
        # But there's nothing else in the try block what could fail. And closing distant file in finally makes further refractoring impossible.
        if hasattr(self.distantFile,"content"): self.distantFile.close() # If file wasn't opened, cannot be closed.
        return self.counters
    
    def subtree(self): return None

class DownloadingLeafProxy(LeafProxy):
    def __init__(self): raise NotImplementedYetError
class LoggingLeafProxy(LeafProxy): 
    def __init__(self): raise NotImplementedYetError
class DownloadingAndLoggingLeafProxy(LeafProxy):
    def __init__(self):  raise NotImplementedYetError
    

# find some use for NodeProxy methods in leaf, and move it into Component    
class NodeProxy(Component):
    """
    Composite component of Composite pattern
    Need to change name of class
    This class serves for every intermediate node of composite tree as well as for root element.
    Operation is download, log or combination and main variable is children. Variable content carries the data.
    """
    def __init__(self,splittedLink=None,link=None,parent=None,previous=None,next=None):
        """
        Not sure why is link property present. But I guess, it is filled in operation process. Every step from root to leaf adds content to link?
        But in this case link shouldn't be part of interface.
        Second possible explanation (021) is that link allows creating node from non-splitted link.
        """
        self.debug.printHeader(4)

        self.children=[] # 024 Can't be moved to Component. Otherwise the tree is not created properly. Used in addSibs().
        self.processedChildren=[] # 024 Can't be moved to Component. Otherwise the tree is not created properly. Used in NodeProxy.operation() as a secondary stack.        
        if not hasattr(self,"counters"): self.counters = CounterManager() # Should be created by commonInit()
        #functionDict=self.__init__.__dict__ #025 # Probably just to test load from interface method.
        #self.debug.comptreeLogger.debug("Function dictionary size is %i"%(len(functionDict)),4) #025
        self.loadFromInterface(splittedLink,link,parent,previous,next)
        self.newSplittedLink=self.splittedLink  # used in both cases (runlenght, flooding)
        # Previous line could be issue, because only pointer is copied like this.
        # 026 #self.debug.comptreeLogger.debug("Splitted link %s"%(str(self.splittedLink)))
        self.logger.debug("Splitted link %s"%(str(self.splittedLink)))
        self.splittedLink=self.handleLink(self.newSplittedLink,self.newLink) # used only in runlenght
        #Hidden parameter link ... need to improve.
        self.content=self.splittedLink.pop(0)
        if link: self.link=link+'/'+self.content  # ??? (021)
        else: self.link=self.content # which is in this case always 'http:'
        self.debug.comptreeLogger.debug("Link to the current node as provided by caller is: %s"%(link))
        #if self.parent and (not self in self.parent.children): # 024
        #    self.comptreeLogger.debug("Going to fix unknown children for %s. Usually Node shouldn't be created here."%(self.link)) 
        #    self.parent.children.append(self) # fixes unknown children
        #    self.comptreeLogger.debug("Fixing unknown children problem. Parent has %i children now"%(len(self.parent.children)))
        self.logger.debug("Going to call recursive Node create for %s."%(self.link))
        # Following line is important!!
        self.addComponent(copy(self.splittedLink),None,self) # calling recursion
        #self.succesfullDownloadCount=0 # 024: replaced by self.counters.addCounter("hits")
        self.counters.addCounter("hits")

    def addComponent(self,splittedLink=None,link=None,parent=None,previous=None,next=None):
        """
        This operation overrides/renames add() operation. It is called recursively until leaf is reached.
        Could be called from init during runlenght, or from outside by flooding.
        Flooding afaik not used yet, just hypothetical possibility.
        """
        self.debug.printHeader()
        self.newLink=link # possible issue - only pointer copied.          # it creates subtree
        self.newSplittedLink=splittedLink
        childLink=self.handleLink(self.newSplittedLink,self.newLink)
        if len(self.splittedLink)>1: # Means is not leaf yet. 
            self.children.append(NodeProxy(childLink,self.link,parent,previous,next)) 
            # init is called recusive here, in runlenght  
        else: self.children.append(LeafProxy(childLink,self.link,parent,previous,next))
        if self.parent: self.debug.comptreeLogger.debug("Current node: %s --- Parent %s has %i children now"%(self.link,self.parent.link,len(self.parent.children)))
        else: self.debug.comptreeLogger.debug("Current node: %s --- Unknown parent."%(self.link))
        
    def operate(self):
        """
        This is main Operation.
        In case of intermediate node doesn't perform any operation rather than call operation of all 
        its children. (But this is okay.)
        Method name could be changed to "get"
        """
        #self.debug.printHeader() # 026 comment out # Done too often - do just on loglevel=4.
        #self.buildReferer() # (024) responsibility moved to DistantFile.
        while self.children: # Just process all children.
            currentChild=self.children.pop(0)
            operationResult=currentChild.operate()
            #self.succesfullDownloadCount+=operationResult # 024: replaced by self.counters.mergeWithManager(operationResult)
            self.counters.mergeWithManager(operationResult)
            # self.counters += operationResult # 024 should also work.
            self.processedChildren.append(currentChild)
        if self.counters.hasCounter("hits") and self.counters.value("hits"):
            # If at least one child has at least one hit this NodeProxy has also hit.
            self.status=200
        else: self.status=500
        if (len(self.splittedLink))<=self.settings.maxLevels:
            if self.sibsExtendDecision():
                sibsContent=self.createSibsContent()
                self.debug.comptreeLogger.debug("For node %s would be created following sibs: %s, %s"%(self.content,sibsContent[0],sibsContent[1])) 
                # Length of splitted link does actually shows how many sublevels will be created.
                self.addSibs(sibsContent) # (before 024) should be uncommented after solving tooManyLevels problem
        #if len(self.children)>1:
        #self.debug.dprint('In node %s was sucessfully downloaded %i files'%(self.link,self.succesfullDownloadCount),3) # 024: replaced by counter
        self.debug.comptreeLogger.info('State of counters is: %s after process of node %s'%(self.counters.printAllValues(),self.link))
        #return self.succesfullDownloadCount # 024: replaced by return self.counters
        return self.counters

    def operationDownloadDecorator(self):
        """ This decorator would decorate operation of download."""
        raise NotImplementedError
    
    def operationDecorator(self,*args):
        """ This method would decorate operation of decorators passed in *args. Currently there are applicable only download and logHits."""
        raise NotImplementedError
        
    def buildReferer(self):
        # 0.24 competence moved to DistantFile class.
        self.debug.printHeader()
        self.requestHeaders={'Referer':self.link,'User-Agent':self.settings.userAgent}
        return self.requestHeaders
        
    def setHoleTolerance(self): # Obsolete, never implemented, replaced by previousRange.
        self.debug.printHeader()
        raise NotImplementedError #sets previous content
    
    def subTree(self): return self.children


class UrlLevel(Shared): pass # Probably rest of old analysis (010) - obsolete, never implemented.
    #property iteratorStartPosition
    #property iteratorEndPosition
    #property levelNumber    
    
    
class PatternAnalyser(Shared):
    #property url
    #patterncompiler
    def __init__(self):
        patternString=self.settings.pattern
        self.debug.comptreeLogger.debug("Using pattern %s"%(patternString))
        self.pattern=re.compile(patternString)
        # This is pretty hard focused to numbers. Could be something else.
        
    def iterate(self,string,step=1,negative=False): 
        """
        Iterates number inside string.
        Input is string containing exactly one number.
        If not negative, number in string is increased by step.
        And string with same structure, but different number, is returned back.
        If iteration would result in negative number, None is returned instead. 
        """
        iterator=self.pattern.search(string)        # if no number inside, None is returned
        # For one proxy/leaf sequence is not needed search again. Optimization challenge.
        # Probably could be done once in parent for all children.
        if iterator:
            if negative: cx=int(iterator.group())-step 
            # group(n) method returns n-th found group of search()
            else: cx=int(iterator.group())+step
            if cx<0: result=None
            # This is out of iterator scope. But it can be easily done here.
            else: result=self.pattern.sub('%%0%dd' % (iterator.end()-iterator.start()) % cx,string) 
            # xtra hardcore string replacement, which i wrote in sumid08, but now i don't know how it works.
        else:
            self.debug.comptreeLogger.debug("In string %s no pattern found."%(string)) 
            result=None   #same as return iterator
        return result
    
    def correctNumLength(self,string,newLength=3):
        """
        Adds zeroes from left to number if number is shorter than required.
        This is needed to keep files literally sort able.
        """
        #self.debug.printHeader()
        newLength=self.settings.minNumberLength     # Is this needed? Probably just because it's shorter.- remove!! 
        iterator=self.pattern.search(string)        # if no number inside, None is returned
        if iterator and (iterator.end()-iterator.start())<newLength:
            cx=int(iterator.group())
            result=self.pattern.sub('%%0%dd' % newLength % cx,string)
        else: result=string # no change required here.
        return result
        
    
class NodeLimitator(Shared):
    """
    Probably rest of old analysis (010) - obsolete, never implemented.
    Can be partially obsoleted by deep property.
    """
    def __init__(self):
        self.__slots__=['rangeInfimum','rangeSupremum','forceInfimum','forceSupremum']
        self.debug.printHeader()
        self.forceInfimum=False
        self.forceSupremum=False
        # 026 To surpass errors. (Doesn't fulfill the original idea.)
        self.Infimum=False
        self.Supremum=False
        
    def setLimits(self,infimum=None,supremum=None):
        self.debug.printHeader()
        if self.Infimum:
            self.rangeInfimum=infimum
            self.forceInfimum=True
        if self.Supremum:
            self.rangeSupremum=supremum
            self.forceSupremum=True

# body begin
# 0.24 #debug = Debug() # This is dirty hack. Area for improvement.

# That's all folks!