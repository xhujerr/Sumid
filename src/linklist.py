# This file is part of SUMID, see sumid.py
# SUMID is released under terms of GPL, see http://www.gnu.org/licenses/gpl.txt

"""
Version Bookkeeping

    If you have to have Subversion, CVS, or RCS crud in your source file, do
    it as follows.

        __version__ = "$Revision: 63990 $"
        # $Source$

    These lines should be included after the module's docstring, before any
    other code, separated by a blank line above and below.
"""

__version__="0.25"

from miscutil import NotImplementedYetError, Shared, Debug, Settings
from Queue import Queue
import urlparse, urllib
# 026 Although I actually use urllib2 the needed addinfourl is defined in urllib and imported to urllib2.

class LinklistAdaptor(Shared):
    """
    LinklistAdaptor implements concept of linklist.
    linklist is just list of links. Every link is input for composite tree.
    Historically LinklistAdaptor class was adaptor and parser - this is wrong.
    Also linklist has many undeveloped possibilities which are designed as @ started directives.
    Currently(021) linklist is a list - all links in one variable.
    """
    
    # 023 Idea of xml linklist dropped. Original thoughts were:
    # Also linklist has many undeveloped possibilities which are designed as @ started directives.
    # This concept is now obsolete. Same idea will be implemented in xml linklist.
    # XML based linklist will consider every link as specific object with directives as attributes.
    # It will be just about xml deserialization.
    # Both, text and xml, parsers will be concrete products of FactoryMethod.
    # In LinklistAdaptor class will remain only code common for both parsers (before text parser will be obsoleted).
    
    logger=Debug.ThreadAwareLogger

    def __init__(self,linklist=None):
        """
        Assigns file containing link list to variable linklist.
        Input parameter linklist must be file object.
        """
        self.linklist=linklist
        self.links=[] # list containing splitted links lists # 026 Making it obsolete by SmartURL.
        self.linksQueue=Queue() # 025 same as "links", but queue type.
        if linklist: self.load() # fills self.links
        

    def load(self,linklist=None):
        """
        Transforms linklist file into tupple of links.
        Should be part of parser?
        The name "load" is pobably confusing.
        """
        # 026 This method is currently not used anywhere.
        self.debug.printHeader()
        if not linklist: linklist=self.linklist
        for line in linklist:
            line=line.strip()
            parsedLine=self.parseLine(line)
            if line and parsedLine: self.links.append(parsedLine) # line2Link not defined yet
        return self.links
        #self.debug.mainLogger.info("Linklist loading complete") # This is no longer true - since I feed linklist by one link.
        
        ## 025 This is awfull mess. Rewrite it in following manner:
        #for line in linklist:
        #    line=line.strip()
        #    line=self.trimSpcSymbols(line)
        #    line=self.handleCommand(command)
        #    line=self.filterDupes()
        #    line=self.isValidUrl(line)
        #    line=self.parseLine(line)
        #    if line and parsedLine: self.links.append(parsedLine)
        #return self.links
        # 026 To be replaced by SmartUrl.

    def parse2Queue(self,linklist=None):
        """ Same as load, but result is Queue. Fast and ugly. """
        self.debug.printHeader()
        self.linksQueue=Queue()
        if not linklist: linklist=self.linklist
        for line in linklist:
            line=line.strip()
            parsedLine=self.parseLine(line)
            if line and parsedLine: self.linksQueue.put(parsedLine) # line2Link not defined yet
        return self.linksQueue           

    def filterDupes(self):
        """
        linklist could contain some links twice, we don't want do same thing twice.
        Every link has to be unique.
        It is question if links with different number is the same.
        Such link can lead to the same tree - it depends on hole tolerance.
        """
        self.debug.printHeader()
        raise NotImplementedYetError

    def compareLinks(self):
        """
        Comparing two link doesn't have to be necessarily comparing of two strings.
        See self.filterDupes.__doc__ for details.
        
        Parser member
        """
        self.debug.printHeader()
        raise NotImplementedYetError

    def isValidUrl (self,url):
        """
        Will check if url is correct. 
        It is about well formed url (e.g. does it start with http:// ?). This is not protection against 404.
        Doesn't work yet, but cannot be solved by usual NotImplementedYetError - then no link will be parsed.
        
        Parser member
        """
        self.debug.printHeader()
        self.logger.debug("Url validation is not implemented yet")
        return True

    def trimSpcSymbols (self,line):
        """
        Tool to get rid of comments and also directives.
        Splits every line on specific symbol.
        Only first special symbol in line is considered.
        Whole operation can be replaced by string method partition(sep) - but this method is new in Python 2.5
        
        Parser member
        """
        # 026 Shall be removed from here and kept only in TextLinklistParser.
        self.debug.printHeader()
        result=[line,None,None]
        for char in line:
            if char in self.settings.linkListSpcSymbols:
                tmp=line.split(char,1)
                result=[tmp[0],char,tmp[1]]
        return result

    def parseLine (self,line):
        """
        Input is raw line from linklist. Output is splitted, valid checked, stripped line without special symbols.
        
        Parser member
        """
        # 026 To be obsoleted by parseToSmartURL
        self.debug.printHeader()
        
        toret=None # toret is only another name for result
        lineParts=self.trimSpcSymbols(line)
        if lineParts[0]:
            if not self.isValidUrl(lineParts[0]): self.logger.warning('Invalid url: %s'%lineParts[0])
            else: toret=lineParts[0].strip().split('/')
        if lineParts[1]=='@':
            self.handleCommand(lineParts[2])
            # If command is on same line as url. Not sure if command will be applied to this url (it should't be).
            # Doesn't matter. Commands directives are deprecated. 
            if lineParts[0]: self.logger.warning('Putting command on same line with URL is not recommended')
        # Comment ignored, no action for comment needed
        if toret and not toret[-1]: toret.pop() # 024 When link ends with /, empty leaf is created. This is to discard empty trailing field. Described in todo 153.
        self.logger.debug('Going to return: %s'%(str(toret))) # TODO: Can't log this - toret is a list.
        if toret:
            # When line is a comment empty string is returned. 
            self.debug.cllLogger.info(self.settings.pathStorage.composeURL(toret))
        #self.debug.dprint('Going to return: %s'%(toret),4)
        return toret
        
    def handleCommand(self, command):
        """
        Should have implement command directives. Never implemented. Obsoleted.
        Have to be done for each command separately. not for whole linklist.
        """
        # 026 Shall be removed from here and kept only in TextLinklistParser.
        #self.debug.printHeader() #026
        #raise NotImplementedYetError #024 hacked
        pass
    """
    will accept commands:
    @stop - will stop processing linklist and exits
    @stop [after <count>] - here count param should be mandatory if after used
    @skip [next [<count>]]
        skip        - skips only 1 link after command
        skip next   - same as skip
        skip next 1 - same as skip
        skip next 5 - skips five links after command
    @previousRange  [next [<count>]] - will change previous range for x next links
    @infimum  [next[<count>]]
    @supremum [next[<count>]]
    @deep <count> - means how many nested loops will be applied to link, it should be counted from tail. Default should be 1. In setting named max levels

    #needs property commandStack
    #every command will add <count> of yourself to stack
    #if stack isn't empty, every url must take one item from stack
    #should have every command own stack?      
    """

    def nextRaw(self):
        """ Provides a line from linklist without any changes."""
        # 026 Pure adaptor member.
        if not hasattr(self,"linklist") or not self.linklist:
            raise BufferError, "No linklist connected, which is required!"
        else:
            rawLine = self.linklist.readline()
            if rawLine=="": self.EOF=True
            return rawLine
        
    def connectLinklistFile(self,LinklistFile):
        """ Checks if the input is file-like object and connects it to linklist."""
        # 026 Pure adaptor member.
        if not isinstance(LinklistFile,urllib.addinfourl) and not isinstance(LinklistFile, file):
            raise AttributeError, "Input must be a file-like object."
        self.linklist=LinklistFile
        self.EOF=False
    
class AbstractLinklistParser(Shared):
    """ Common code for linklist parsers. ( 026 So far only text parser.)"""
    pass

class TextLinklistParser(AbstractLinklistParser):

    def parse2SmartURL(self,line):  # Added in 026
        urlPart,symbol,spcPart=self.trimSpcSymbols(line)
        if symbol and spcPart: 
            spcPart=spcPart.strip()
            spcPartWithSymbol=symbol+spcPart
        else: spcPartWithSymbol=None
        if spcPart and not urlPart: self.handleCommand(spcPart)
        # 026 Following line will cause troubles if only command at the line. Previous line shall fix it. 
        # 026 URL validity is checked in SmartURL.__init__() 
        # 026 What that does mean. Is handling command responsibility of SmartURL?
        if urlPart.strip(): 
            return SmartURL(urlPart.strip(),spcPartWithSymbol)
            self.debug.cllLogger.info(urlPart.strip())
        else: return None

    def trimSpcSymbols (self,line):
        """
        Tool to get rid of comments and also directives.
        Splits every line on specific symbol.
        Only first special symbol in line is considered.
        Whole operation can be replaced by string method partition(sep) - but this method is new in Python 2.5
        
        Parser member
        """
        self.debug.printHeader()
        result=[line,None,None]
        for char in line:
            if char in self.settings.linkListSpcSymbols:
                tmp=line.split(char,1)
                result=[tmp[0],char,tmp[1]]
        return result

    def handleCommand(self, command):
        """
        Should have implement command directives. Never implemented. Obsoleted.
        Have to be done for each command separately. not for whole linklist.
        """
        #self.debug.printHeader() #026
        #raise NotImplementedYetError #024 hacked
        pass
    
    def connectLinklistAdaptor(self,linklistAdaptorInstance):
        if isinstance(linklistAdaptorInstance,LinklistAdaptor):
            self.linklistAdaptorInstance=linklistAdaptorInstance
        else: raise AttributeError, "LinklistAdaptor must be provided!"
        
    def next(self):
        if not hasattr(self,"linklistAdaptorInstance") or not self.linklistAdaptorInstance:
            raise AttributeError, "LinklistAdaptor instance required for next operation. Call connectLinklistAdaptor method first."
        else:
            return self.parse2SmartURL(self.linklistAdaptorInstance.nextRaw())
    
    @property    
    def linklistEOF(self):
        return self.linklistAdaptorInstance.EOF

            
class SmartURL(urlparse.ResultMixin): # Class added in 026.
    
    _composed=""
    #_splitted=[] # 026 Do the split everytime is safer.
    
    def __init__(self,url,spcPart=""):
        # 026 Spc part includes the symbol.
        if self.isValid(url):
            self._composed=url
            self._seed=url
            self._spcPart=spcPart
        # 026 If url is not valid, exception is thrown from validation.     
    
    def isValid(self,url):
        """ This is to validate (onestring) URL. The problem is that there's not much to validate. """
        if not url: raise ValueError, "Cannot assign empty link."
        if not isinstance(url,str): raise ValueError, "Expected a string! %s"%(str(url))
        if url.count("#"):  raise ValueError, "Comment is forbidden in link: %s"%(str(url))
        if not url == url.strip(): raise ValueError, "Spacious url rejected: %s"%(str(url))
        return True
        
    @property
    def Splitted(self):
        """ Provides splitted url. Split the composed every time when ran."""
        return self._composed.split("/")
    
    @Splitted.setter
    def Splitted(self,value):
        """ This attribute shall be used as read-only."""
        if not value: raise ValueError, "Cannot assign empty link."
        if not isinstance(value,list): raise ValueError, "Expected a list!"
        composed = "/".join(value)
        result = self.Composed=composed
        return result
    
    @property
    def Composed(self): return self._composed
    
    @Composed.setter
    def Composed(self,url):
        if self.isValid(url): self._composed = url
        return True
    
    @property
    def SPCPart(self): return self._spcPart
    
    @property
    def Seed(self): return self._seed   
    
    def isAbsolute(self):
        if self.Composed.find("://") >0 : return True
        else: return False

    def isRelative(self): return not self.isAbsolute()
    
    def multiSeparatorSplit(self,separationBase,separators):
        """
        Works like split() string method for multiple separators.
        """
        separationBase=[separationBase] # 026 Trick to bypass the first separation on unseparated string.
        for separator in separators:
            separationResult=[]
            for substring in separationBase:
                separationResult.extend(substring.split(separator))
            separationBase=separationResult
        return separationResult


    def Words(self,urlWordsSeparators):
        """
        Works like split() string method.
        Only it can receive more than one separator in a list as an input parameter.
        Having it with default parameter is senseless, because of split. So there is no default value.
        """
        # 026 The trick with settings doesn't work.
        #if not hasattr(self,"settings"):
        #    self.settings=Settings()
        return self.multiSeparatorSplit(self._composed, urlWordsSeparators)

    
    def WordsPerPartes(self,urlWordsSeparators):
        """ 
        Works like split() string method.
        Takes every part of a url and splits it separately.
        Splitting is done by multiple separators.
        Result is 2-dim array. First dim is scheme, netloc, path, params, query, fragment.
        """
        urlParseResult=self.urlparse(self._composed)
        result=[]
        for urlPart in urlParseResult:
            result.append(self.multiSeparatorSplit(urlPart, urlWordsSeparators))
        return result
            
        
    
    def urlparse(self, url, scheme='', allow_fragments=True):
        """ Only calls urlparse.urlparse() and adds result to self. """
        scheme, netloc, path, params, query, fragment = urlparse.urlparse(url, scheme, allow_fragments)
        self._scheme=scheme
        self._netloc=netloc
        self._path=path
        self._params=params
        self._query=query
        self._fragment=fragment
        return scheme, netloc, path, params, query, fragment
                
    # 026 urlparse() product properties if not exist, calls self.urlparse.
    # 026 properties are named with lowercase to maintain compatibility with urlparse module.
    
    @property
    def scheme(self):
        if not hasattr(self,"_scheme"): self.urlparse(self._composed)
        return self._scheme

    @property
    def netloc(self):    
        if not hasattr(self,"_netloc"): self.urlparse(self._composed)
        return self._netloc
    
    @property
    def path(self):
        if not hasattr(self,"_path"): self.urlparse(self._composed)
        return self._path

    @property
    def params(self):
        if not hasattr(self,"_params"): self.urlparse(self._composed)
        return self._params

    @property
    def query(self):
        if not hasattr(self,"_query"): self.urlparse(self._composed)
        return self._query

    @property
    def fragment(self):
        # 026 Since character # is forbidden in SmartURL this shall never happen.
        if not hasattr(self,"_fragment"): self.urlparse(self._composed)
        return self._fragment


        
class History(Shared):
    """
    Maintain history of processed items.
    It has to be configurable if items should be processed again, of if should be skipped.
    
    Future task
    """
    def loadHistory(self):
        """ It means load history stored in text file, but not import. """
        self.debug.printHeader()
        raise NotImplementedYetError
    def appendLink(self):
        """ appends link from successfully processed tree """
        self.debug.printHeader()
        raise NotImplementedYetError
    def writeHistory(self):
        """ store history to file """
        self.debug.printHeader()
        raise NotImplementedYetError
    def importHistory(self):
        """
        Will load load from file via linklistAdaptor.load and than linklistAdaptor.findDupes
        against internally stored history.
        """
        self.debug.printHeader()
        raise NotImplementedYetError
    
# That's all folks!