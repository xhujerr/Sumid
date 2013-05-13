#    SUMID - Script used for mass items downloading
#    Copyright (C) 2004-2010  Roman Hujer <sumid at gmx dot com>
#    This file is part of SUMID, see sumid.py
#    SUMID is released under terms of GPL, see http://www.gnu.org/licenses/gpl.txt


__version__="0.26"

from distutils import util
from settings import * # Only for Sumid.
import sys
#import pprint
import logging.handlers
import ConfigParser
import os.path # sync with docbook2testlink 
import time
import datetime
import argparse
import thread
import threading
import re

# Hacked for docbook2testlink - Remove in Sumid!
#mainINIFilePath="settings.ini"#"/home/hujerr/eclipse/docbook2testlink3/src/settings.ini"

class NotImplementedYetError(Exception): pass
class InvalidFileTypeError(Exception): pass
class PrintUris (Exception): pass # TODO: Should be deprecated soon (024).

class Singleton(object):
    """
    Singleton class by Duncan Booth.
    Multiple object variables refers to the same object.
    http://www.suttoncourtenay.org.uk/duncan/accu/pythonpatterns.html#singleton-and-the-borg
    
    In SUMID(021) is Singleton used only as abstract class. 
    """
    _instance = None

    def __new__(cls, *args, **kwargs): # 026 See explanation below.
    #def __new__(cls):
        if not cls._instance:
            #cls._instance = super(Singleton, cls).__new__(cls)
            #cls._instance = object.__new__(cls)
            cls._instance = super(Singleton, cls).__new__(cls)


            # cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
            # 026 Previous line did generate following warning:
            # /media/KINGSTON/Sumid/src/miscutil.py:39: DeprecationWarning: object.__new__() takes no parameters
            # cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
            # Explanation: http://mail.python.org/pipermail/python-dev/2008-February/076854.html
            #cls._instance = super(Singleton, cls).__new__()
            # 026 So I just cleared the params.
        return cls._instance
    
 
class EnhancedConfigParser(ConfigParser.ConfigParser):
    """
    This class is simply ConfigParser enhanced by methods getDebugLevel and getList.
    Thus it depends on logging.
    """
    
    
    #optionxform = str # This causes to preserve case sensitivity in option names. (http://stackoverflow.com/questions/1611799/preserve-case-in-configparser)
    
    def __init__(self):
        # 025 temporary workaround, described in todo 193 ... remove the incredible hacks below :-)
        self.removed_get=ConfigParser.ConfigParser.get
        #return super(EnhancedConfigParser,self).__init__() # 025 Pointer to parent class doesn't work. Seems like ConfigParser is not new style class.
        return ConfigParser.ConfigParser.__init__(self)

    def getDebugLevel(self,section, option):
        """
        Created especially to read logging levels from INI. Does read following options:
        logging.DEBUG
        logging.INFO
        logging.WARNING
        logging.ERROR
        """
        #unparsedOption=self.get(section, option)
        unparsedOption=self.removed_get(self, section, option)
        if unparsedOption == "DEBUG" or unparsedOption == "logging.DEBUG" or unparsedOption == 10 : parsedOption=logging.DEBUG
        elif unparsedOption == "INFO" or unparsedOption == "logging.INFO" or unparsedOption == 20 : parsedOption=logging.INFO
        elif unparsedOption == "WARNING" or unparsedOption == "logging.WARNING" or unparsedOption == 30 : parsedOption=logging.WARNING
        elif unparsedOption == "ERROR" or unparsedOption == "logging.ERROR" or unparsedOption == 40 : parsedOption=logging.ERROR
        else: raise ConfigParser.ParsingError, "Wrong unparsed option %s. Only following values allowed: DEBUG, INFO, WARNING, ERROR"%(unparsedOption)
        return parsedOption
    
    def getList(self,section, option):
        """ Loads comma separated string from INI and returns list."""        
        unparsedOption=self.get(section, option)
        if unparsedOption.find(',')>0:
            splittedValue=unparsedOption.split(',')
            strippedValue=[]
            while splittedValue:
                valuePart=splittedValue.pop(0)
                strippedValue.append(valuePart.strip())
            result=strippedValue
        else: result=unparsedOption
        return result        
    
class EnhancedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None, delay=0, utc=0, maxBytes=0):
        """ This is just a combination of TimedRotatingFileHandler and RotatingFileHandler (adds maxBytes to TimedRotatingFileHandler)  """
        # super(self). #It's old style class, so super doesn't work.
        logging.handlers.TimedRotatingFileHandler.__init__(self, filename, when, interval, backupCount, encoding, delay, utc)
        self.maxBytes=maxBytes
            
    def shouldRollover(self, record):
        """
        Determine if rollover should occur.

        Basically, see if the supplied record would cause the file to exceed
        the size limit we have.
        
        we are also comparing times        
        """
        # 026 I added here a hack because the streams get closed somewhere unexpectedly.
        if self.stream is None or self.stream.closed:                 # delay was set...
            self.stream = self._open()
        if self.maxBytes > 0:                   # are we rolling over?
            msg = "%s\n" % self.format(record)
            self.stream.seek(0, 2)  #due to non-posix-compliant Windows feature
            if self.stream.tell() + len(msg) >= self.maxBytes:
                return 1
        t = int(time.time())
        if t >= self.rolloverAt:
            return 1
        #print "No need to rollover: %d, %d" % (t, self.rolloverAt)
        return 0         

    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.
        """
        if self.stream:
            self.stream.close()
        # get the time that this sequence started at and make it a TimeTuple
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
        if self.backupCount > 0:
            cnt=1
            dfn2="%s.%03d"%(dfn,cnt)
            while os.path.exists(dfn2):
                dfn2="%s.%03d"%(dfn,cnt)
                cnt+=1                
            os.rename(self.baseFilename, dfn2)
            for s in self.getFilesToDelete():
                os.remove(s)
        else:
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.baseFilename, dfn)
        #print "%s -> %s" % (self.baseFilename, dfn)
        self.mode = 'w'
        self.stream = self._open()
        currentTime = int(time.time())
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        #If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstNow = time.localtime(currentTime)[-1]
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    newRolloverAt = newRolloverAt - 3600
                else:           # DST bows out before next rollover, so we need to add an hour
                    newRolloverAt = newRolloverAt + 3600
        self.rolloverAt = newRolloverAt

    def getFilesToDelete(self):
        """
        Determine the files to delete when rolling over.

        More specific than the earlier method, which just used glob.glob().
        """
        dirName, baseName = os.path.split(self.baseFilename)
        fileNames = os.listdir(dirName)
        result = []
        prefix = baseName + "."
        plen = len(prefix)
        for fileName in fileNames:
            if fileName[:plen] == prefix:
                suffix = fileName[plen:-3]
                if self.extMatch.match(suffix):
                    result.append(os.path.join(dirName, fileName))
        result.sort()
        if len(result) < self.backupCount:
            result = []
        else:
            result = result[:len(result) - self.backupCount]
        return result            

class Settings(Singleton):
    """
    Cares about loading (and saving) of program settings.
    Provides access to these settings from rest of program.  
    Can't be child of Shared.
    Should be rewired to make settings read only.
    """
    #Have a look at http://docs.python.org/library/configparser.html
    
    def __init__(self,configParserInstance=None):
        self.getPlatform()
        self.pathStorage=None
        #self.linklistURL=None # Removed in (025) Probably used by miscpath() which was removed as well.
                
        #if configParserInstance: # sync with docbook2testlink # Dropped in 024f.
        #    self.configParser = configParserInstance # dropped in 024f
        #else: # Implementation used in Sumid. This will be preferred. # dropped in 024f
        if not hasattr(self,"config"): self.config=EnhancedConfigParser()
        #self.config.read(mainINIFilePath) # (024) Shouldn't be needed - done in sumid.body.
        # (025) Removing inconsistent usage of configParser ... wrapped by loadAdaptive() 
        #self.get=self.config.get
        self.removed_get=self.config.get
        #self.config.get=None
        # TODO: Hack - this is f*cking mess. No idea who will unmess it :-( # sync with docbook2testlink 
        #self.workdir="/space/Roman/M+/ATP-for-import/MCO-import/" # sync with docbook2testlink 
        self.timeString=datetime.datetime.now().strftime("%Y%m%d")
        # I'm not sure if settings should be loaded while creating instance.
        # But Debug instance in Shared needs settings loaded. Can't do that in Shared.__init__() because it is abstract.
        #self.loadAdaptive("sumid","INI") # Too soon to load defaults, because PathStorage instances do not exist yet.
        
        # Hacked for docbook2testlink - Remove in Sumid!
        #if not hasattr(self,"options"): self.options={} # Because settings is Singleton, may be called multiple times and overri previous changes. # sync with docbook2testlink

        if not hasattr(self,"mainINIFilePath"): self.mainINIFilePath=mainINIFilePath  # 026 Added a condition because the paths were constantly overwriting each other.
        self.loadAdaptive("INI") 
    
    def loadAdaptive(self, *args):
        """
        This method could load settings adaptively, because not all setting could be loaded at once.
        Arguments could be: "params", "INI", "sumid", "file" and "all" - file not implemented yet.
        Sooner or later has to be called with argument "all". This method just allows to do it later.
        """
        # (025) The aim of this method changed slightly. loadFromSumid, loadFromINI, loadFromParams do not write directly into Settings instance. loadAdaptive does it instead.
        for arg in args:
            if isinstance(arg, str): arg=arg.lower()
        
        # (025) I think path storage was used just by miscpath() which was already removed. 
        if (not hasattr(self,"pathStorage")) or (self.pathStorage==None): # pathStorage could be loaded via self.connectPathStorage(pathStorage)
            for arg in args:
                if hasattr(arg,"__class__") and str(arg.__class__).find("athStorage")>0: self.pathStorage=arg
        # (025) Settings.loadDefaults() obsoleted in favor of settings.RawSettings
        #if ("defaults" in args) or ("all" in args):
            #pathStorage should come among *args.#(0.24) 
            #factory=FactoryMethod() #(0.24)
            #if self.pathStorage: self.loadDefaults()
            #else: print "pathStorage instance needed to load defaults. (Too early for debug and logger.)"
        if ("sumid" in args) or ("all" in args): 
            sumidSettings=self.loadFromSumid()
            self.__dict__.update(sumidSettings.__dict__)
            #toGroup.__dict__.update(argparseResults.__dict__)
        #if ("file" in args) or ("all" in args): self.loadFromFile()
        if ("INI" in args) or ("ini" in args) or ("ini" in args) or ("all" in args): 
            # (025) This is very ugly, but the nice way with lowering didn't work.
            if hasattr(self,"mainINIFilePath"): iniSettings=self.loadFromINI(self.mainINIFilePath)
            else: iniSettings=self.loadFromINI()
            self.__dict__.update(iniSettings.__dict__) 
            self.loadFromINI(self.mainINIFilePath)   
        if ("params" in args) or ("all" in args): 
            argParams=self.loadFromParams()
            self.__dict__.update(argParams.__dict__)
        
    def loadFromParams(self): 
        """
        This method should load settings specified as parameters on command line.
        Probably there will be needed another method which will parse the input into dictionary.
        
        (025) The switches list is pretty old.
        posible switches:
        --help
        --linkList <url_path_to_linklist_file>
        --workDir <default_working_path> #aka savePath
        --linkListPath <path+fileName>
        --fetchedLinksList <fileName>
        --fetchedLinksListPath <path+fileName>
        #incomplete - more in loadFromSumid
        """    
        
        parser = argparse.ArgumentParser(description="SUMID - Script used for mass items discovering")
        
        parser.add_argument (
                             "--linklistURL",
                             dest="linklistURL",
                             default=argparse.SUPPRESS,
                             required=False,
                             help="Path to linklist. Linklist is the main input of Sumid. It contains all the urls, which gonna be processed."
                             )
        
        parser.add_argument("-w",
                    "--workDir",
                    dest="workDir",
                    default=argparse.SUPPRESS,
                    required=False,
                    help="Place on filesystem where the results gonna be stored."
                    )

        parser.add_argument(
                    "--allowedMIMETypes",
                    dest="allowedMIMETypes",
                    default=argparse.SUPPRESS,
                    required=False,
                    help="Comma separated list of MIME type, which will be considered as a successful hit."
                    )

        parser.add_argument("--sibsLimit",
                    dest="sibsLimit",
                    default=argparse.SUPPRESS,
                    required=False,
                    type=int,
                    help="How many misses on each side will be tolerated before moving further."
                    )
        
        parser.add_argument("-v",
                    "--verbose",
                    dest="verbosity",
                    default=argparse.SUPPRESS,
                    required=False,
                    action='store_const',
                    const=42,
                    help="Tweak to be able to use verbosity in unittests. In future can make Sumid silent."
                    )        
        
        argparseResults = parser.parse_args()
        return argparseResults
    
    #def loadFromFile(self):   raise notImplementedYetError

    def loadFromINI(self,INIFilePath=None):
        # TODO: (025) Don't use a variable as a default value. Because the variable has to be loaded somehow. Cannot be handled as the rest of settings.
        #self.config=ConfigParser.ConfigParser() # Done in __init__() (024)
        
        #print INIFilePath
        # 026 All alternative paths to setting get overwritten. It is a bug or it should be always called with param? 
        if not INIFilePath and hasattr(self,"mainINIFilePath"): INIFilePath=self.mainINIFilePath
        elif not INIFilePath: INIFilePath=mainINIFilePath
        # (025) Should keep case sensitivity.
        self.config.optionxform = str
        self.config.read(INIFilePath)
        class INISettings(object): pass # (025) Just in order to create empty object to save results 
        iniSettings=INISettings()
        for sectionKey in self.config._sections.keys():
            iniSettings.__dict__.update(self.config._sections[sectionKey])
        # (025) Now correct numeric and boolean values:
        for attribute in iniSettings.__dict__.keys():
                if iniSettings.__dict__[attribute].isdigit(): iniSettings.__dict__[attribute]=int(iniSettings.__dict__[attribute])
                if iniSettings.__dict__[attribute]=="True": iniSettings.__dict__[attribute]=True
                if iniSettings.__dict__[attribute]=="False": iniSettings.__dict__[attribute]=False
        return iniSettings

    def loadFromSumid(self):
        """
        Loads setting from inside of Sumid.
        Currently(021) from file settings.py which has no other purpose.
        Should be obsoleted by something soon.
        """  
        if not hasattr(self,"mainINIFilePath"): self.mainINIFilePath=mainINIFilePath # 026 Added a condition because the paths were constantly overwriting each other.
        if not hasattr(RawSettings,"mainINIFilePath"): # (025) For unittest sanity.
            RawSettings.mainINIFilePath=self.mainINIFilePath# 026 Just RawSettings.mainINIFilePath=mainINIFilePath was conflicting with sls. 
        return RawSettings
        
    def loadDefaults(self):
        """ This loads first line of defaults. Even before loadFromSumid. In future could be merged."""
        # (025) Merged into settings.RawSettings.
        pass 
        
    def getPlatform(self):
        """
        This is just wrapper for util.get_platform().
        Written to get rid of different linux versions.
        Currently(021) it is used only in path storage factory.
        Every platform must have own concrete factory (I don't want to create 50 unix factories).  
        """
        self.platform=util.get_platform()
        if not(self.platform.find('linux')==-1): self.platform='Unix' # i suppose, that in all unix systems are paths similiar
        if self.platform=='win32': self.platform='Win32' # this should be done automatically
        
    def connectPathStorage (self,pathStorage):  self.pathStorage= pathStorage # only if not in body
    def connectFilesAdaptor(self,filesAdaptor): self.filesAdaptor=filesAdaptor # only if not in body
    
    #Following 2 methods were written for docbook2testlink
    def loadFromFile(self,path): # sync with docbook2testlink 
        #self.config.read(path) # Dropped in 024f.
        if not "main" in self.config.sections(): raise EnvironmentError, "Configuration file doesn't contain main section! Goodbye."
        if not "tagTranslationTable" in self.config.sections(): raise EnvironmentError, "Configuration file doesn't contain tagTranslationTable section!  Goodbye."
        for section in self.config.sections():
            for option in self.config.options(section):
                #Just adding (parsed)value with key option into options dictionary. 
                self.options[option]=self.config.getList(section, option)
        self.tagTranslationTable=self.config._sections["tagTranslationTable"]
        self.invertedTagTranslationTable=self.config._sections["invertedTagTranslationTable"]
        self.main=self.config._sections["main"]
        self.tagIdentifiers=self.config._sections["tagIdentifiers"]
        self.reversedTagTranslationTable=self.reverseDict(self.tagTranslationTable)
        self.docbookTranslator=self.config._sections["docbookTranslator"]
        #debug.dprint("Settings loaded.") # Debug not initialized yet.
        #self.workdir=os.path.split(settings.options["xmlpath"])[0]        
    
    def reverseDict(self,originalDict): # sync with docbook2testlink 
        reversedDict={}
        for key in originalDict.keys():
            reversedDict[originalDict[key]]=key
        return reversedDict
    
    def insertDatetimeIntoFilename(self,filename,dtime=None):
        # 026 Could use insertStringIntoFilename
        if not dtime: dtime=self.timeString
        splittedFilename=filename.rsplit('.',1)
        splittedFilename.insert(-1,dtime)
        result=".".join(splittedFilename)
        return result

    def insertStringIntoFilename(self,filename,aString=None):
        if aString:
            splittedFilename=filename.rsplit('.',1)
            splittedFilename.insert(-1,aString)
            return ".".join(splittedFilename)
        else: return filename  

class Debug(Singleton):
    """
    This class cares mainly about levels of logging.
    Solves if an error/warning/info message should be displayed as output or hidden.
    Too many messages not only generating big mess, but also cause program slow down. 
    """
    def __init__(self,settingsInstance=None):
        if settingsInstance: self.settings=settingsInstance
        else: self.settings=Settings()    # can't be child of Shared
        self.callerName=None
        if not hasattr(self,"mainLogger"): # Since debug is Singleton, there's a risk that the loggers are initialized multiple times.
            self.initializeLoggers() # Can't be here, because Settings.loadFromINI() not executed yet. It can - it was executed adaptively.
            
    def initializeLoggers(self):
        """
        Well it is time to change the logging into something sophisticated.
        http://docs.python.org/library/logging.html
        """
        
        #Interesting logger attributes: Logger.findCaller(), logging.addLevelName(lvl, levelName), logging.getLoggerClass()        
        
        #if not(os.path.exists(self.settings.get("log","logDir"))):os.makedirs(self.settings.get("log","logDir")) # (025) Config parser pushed out because of settings access harmonizing.
        if not(os.path.exists(self.settings.logDir)): os.makedirs(self.settings.logDir)
        
        if not hasattr(self,"hitLogger"):
            # Since debug is Singleton, there's a risk that the loggers are initialized multiple times.
            self.hitLogger=logging.getLogger('hitLogger')
            self.hitLogger.setLevel(self.settings.config.getDebugLevel("log","hitsLogLevel")) #025
            #self.hitLogger.setLevel(self.settings.hitsLogLevel) # 025 # Returns string instead of logLevel
            #Rotating file handler is probably not needed, but File handler didn't work.
            #logFileName=self.settings.insertDatetimeIntoFilename(self.settings.hitsLogFileName)
            hitLoggerPath=self.settings.logDir+"/"+self.settings.hitsLogFileName#logFileName
            #fileHandler=logging.handlers.RotatingFileHandler(hitLoggerPath, maxBytes=52428800, backupCount=5)
            fileHandler=logging.handlers.TimedRotatingFileHandler(hitLoggerPath, when='midnight', interval=1, backupCount=20)
            self.hitLogger.addHandler(fileHandler)     
            
        if not hasattr(self,"cllLogger"):
            # Since debug is Singleton, there's a risk that the loggers are initialized multiple times.
            self.cllLogger=logging.getLogger('cllLogger')
            self.cllLogger.setLevel(self.settings.config.getDebugLevel("log","hitsLogLevel")) # 025 # hitsLogLevel is not a mistake. It is deliberately the same.
            #self.cllLogger.setLevel(self.settings.hitsLogLevel) # Returns string instead of logLevel# hitsLogLevel is not a mistake. It is deliberately the same.
            logFileName=self.settings.insertDatetimeIntoFilename(self.settings.cllsLogFileName)
            cllLoggerPath=self.settings.logDir+"/"+logFileName
            fileHandler=logging.handlers.RotatingFileHandler(cllLoggerPath, maxBytes=52428800, backupCount=50)
            self.cllLogger.addHandler(fileHandler)             

        if not hasattr(self,"cntLogger"): # Counter logger
            # Since debug is Singleton, there's a risk that the loggers are initialized multiple times.
            self.cntLogger=logging.getLogger('cntLogger')
            self.cntLogger.setLevel(self.settings.config.getDebugLevel("log","hitsLogLevel")) # hitsLogLevel is not a mistake. It is deliberately the same.
            #logFileName=self.settings.insertDatetimeIntoFilename(self.settings.get("log","countersLogFileName")) # 025
            logFileName=self.settings.insertDatetimeIntoFilename(self.settings.countersLogFileName)
            cntLoggerPath=self.settings.logDir+"/"+logFileName
            #fileHandler=logging.handlers.RotatingFileHandler(cntLoggerPath, maxBytes=52428800, backupCount=50) # 026
            fileHandler=logging.handlers.TimedRotatingFileHandler(cntLoggerPath,'midnight',1, backupCount=50)
            self.cntLogger.addHandler(fileHandler)

        if not hasattr(self,"missLogger"):
            # Since debug is Singleton, there's a risk that the loggers are initialized multiple times.
            # missLogger logs links where pattern could be found but none of them led to resource (except the seed).
            self.missLogger=logging.getLogger('missLogger')
            self.missLogger.setLevel(self.settings.config.getDebugLevel("log","hitsLogLevel"))
            #logFileName=self.settings.insertDatetimeIntoFilename(self.settings.missLogFileName)
            missLoggerPath=self.settings.logDir+"/"+self.settings.missLogFileName#logFileName
            #fileHandler=logging.handlers.RotatingFileHandler(missLoggerPath, maxBytes=52428800, backupCount=5)
            fileHandler=logging.handlers.TimedRotatingFileHandler(missLoggerPath, when='midnight', interval=1, backupCount=20)
            self.missLogger.addHandler(fileHandler) 

        if not hasattr(self,"nopLogger"):
            # Since debug is Singleton, there's a risk that the loggers are initialized multiple times.
            # nopLogger = No pattern found (except the seed).
            self.nopLogger=logging.getLogger('nopLogger')
            self.nopLogger.setLevel(self.settings.config.getDebugLevel("log","hitsLogLevel"))
            logFileName=self.settings.insertDatetimeIntoFilename(self.settings.nopLogFileName)
            nopLoggerPath=self.settings.logDir+"/"+logFileName
            fileHandler=logging.handlers.RotatingFileHandler(nopLoggerPath, maxBytes=52428800, backupCount=50)
            self.nopLogger.addHandler(fileHandler) 
        
        if not hasattr(self,"mainLogger"): # Since debug is Singleton, there's a risk that the loggers are initialized multiple times.
            # Format usable for all clasic logs (but not hitLogger.
            #self.logFormatter=logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s") # Original formatter from example.
            # Changed in Python version 2.5: funcName was added.
            self.logFormatter=logging.Formatter("%(asctime)s | %(module)s | %(lineno)d | %(name)s | %(funcName)s | %(levelname)s | %(message)s")

            #logFileName=self.settings.insertDatetimeIntoFilename(self.settings.get("log","mainLogFileName")) # 025
            #logFileName=self.settings.insertDatetimeIntoFilename(self.settings.mainLogFileName)
            mainLoggerPath=self.settings.logDir+"/"+self.settings.mainLogFileName #026 logFileName
            self.mainLogLevel=self.settings.config.getDebugLevel("log","mainLogLevel")
        
            #self.mainLogFileHandler = logging.FileHandler(mainLoggerPath, 'a') # 0.24 replaced by basicConfig - was workaround.
            #self.mainLogFileHandler = logging.handlers.RotatingFileHandler(mainLoggerPath, maxBytes=52428800, backupCount=20)
            #self.mainLogFileHandler=logging.handlers.TimedRotatingFileHandler(mainLoggerPath,when='H',interval=1,backupCount=20)
            
            self.mainLogInterval=1 # 026 When cloning main logger it expands to seconds twice! (If not bypassed like this.)
            #self.mainLogFileHandler=EnhancedRotatingFileHandler(mainLoggerPath,when='H',interval=6,backupCount=50) # 026 stable
            self.mainLogFileHandler=EnhancedRotatingFileHandler(mainLoggerPath,when='midnight',interval=self.mainLogInterval,backupCount=20,maxBytes=52428800) # 026 Experimental
            #self.mainLogFileHandler=EnhancedRotatingFileHandler(mainLoggerPath,when='midnight',interval=1,backupCount=20,maxBytes=1048576) # 026 Beta
            self.mainLogFileHandler.setFormatter(self.logFormatter) # 0.24 replaced by basicConfig
            #self.mainLogFileHandler.maxBytes=1048576#52428800 # 026 with TimedRotatingFileHandler maxBytes doesn't work.
            #self.mainLogFileHandler.backupCount = 20
            # If the fileHandler property was universaly available, it could be used for creating logger in every module.
            comptreeLogLevel=self.settings.config.getDebugLevel("log","comptreeLogLevel")

        if not hasattr(self,"qsize log"): # qSize logger
            self.qszLogger=logging.getLogger('qsize log')
            self.qszLogger.setLevel(self.settings.config.getDebugLevel("log","hitsLogLevel")) # hitsLogLevel is not a mistake. It is deliberately the same.
            qszLoggerPath=self.settings.logDir+"/qsize.log" # 026 Later it should be possible to set-up name or turn it off.
            fileHandler=logging.handlers.TimedRotatingFileHandler(qszLoggerPath,'midnight',1, backupCount=50)
            fileHandler.setFormatter(self.logFormatter)
            self.qszLogger.addHandler(fileHandler)

        self.mainLogger=self.enrichMainLogger("main log")
        self.dprintLogger=self.enrichMainLogger("dprint l")
        #self.headerLogger=self.enrichMainLogger("header l") # 026 Overriden by the property
        #self.comptreeLogger=self.enrichMainLogger("compTree",self.mainLogger,comptreeLogLevel)
        #self.comptreeLogger=Debug.ThreadAwareLoger # 026 Overriden by the property

        # This will log into std out:
        #streamHandler=logging.StreamHandler()
        #streamHandler.setLevel(logging.DEBUG)
        #streamHandler.setFormatter(formatter)                
        #self.mainLogger.addHandler(streamHandler)
    
    @property
    def comptreeLogger(self):
        """ Just to keep backwards compatibility for comptreeLogger. """
        return self.ThreadAwareLogger

    @property
    def headerLogger(self):
        """ Just to keep backwards compatibility for headerLogger. """
        return self.ThreadAwareLogger
    
    def enrichMainLogger(self,loggerName,baseLogger=None,logLevel=None):
        """
        This method has to simplify creating class specific logger.
        All loggers created with it would log into the same file and will have the same log format.
        Only the logger name will differ (which will be visible in the log).
        Logger name should be optimally 8 characters long.
        """
        # http://docs.python.org/library/logging.html
        #Loggers that are further down in the hierarchical list are children of loggers higher up in the list. 
        #For example, given a logger with a name of foo, loggers with names of foo.bar, foo.bar.baz, 
        #and foo.bam are all children of foo. Child loggers propagate messages up to their parent loggers. 
        #Because of this, it is unnecessary to define and configure all the loggers an application uses. 
        #It is sufficient to configure a top-level logger and create child loggers as needed.
        
        #All calls to this function with a given name return the same logger instance. 
        #This means that logger instances never need to be passed between different parts of an application.

        if not hasattr(self,loggerName):
            # Since debug is Singleton, there's a risk that the loggers are initialized multiple times.
            logger=logging.getLogger(loggerName)
            if logLevel:
                logger.setLevel(logLevel)
            elif baseLogger:
                logger.setLevel(baseLogger.level)
            else:
                logger.setLevel(self.mainLogLevel)
            if baseLogger:
                for handler in baseLogger.handlers:
                    logger.addHandler(handler)
            else: logger.addHandler(self.mainLogFileHandler)
            return logger
        else: return eval("self.%s"%(loggerName)) # TODO: This is evil! But the else part should never occur.       

    def cloneMainLogger(self,loggerName,logLevel=None):
        """
        This method provide clone of the main logger with diferrent name and file to log into.
        Intention is to every thread has its own logger. The other parameters stays the same as in main logger.
        """
        if not hasattr(self,"mainLogger"): # 026 It must be always ran after main logger was initialized.
            self.initializeLoggers()
        mainLoggerPath=self.settings.insertStringIntoFilename(self.mainLogFileHandler.baseFilename, loggerName)
        mainLogFileHandler=EnhancedRotatingFileHandler(
                                                       mainLoggerPath,
                                                       when=self.mainLogFileHandler.when,
                                                       interval=self.mainLogInterval,
                                                       backupCount=self.mainLogFileHandler.backupCount,
                                                       maxBytes=self.mainLogFileHandler.maxBytes
                                                       )
        mainLogFileHandler.setFormatter(self.logFormatter)
        logger=logging.getLogger(loggerName)
        logger.addHandler(mainLogFileHandler)
        logger.setLevel(self.mainLogLevel)
        
        # 026 Replace minus in loggerName, coz it raise Exception: SyntaxError: can't assign to operator (self.logger-Name=logger)
        # http://stackoverflow.com/a/490616/775066
        loggerName = re.sub("-", "_", loggerName)
        toExec="self.%s=logger"%loggerName
        #print toExec #026
        exec toExec
        return logger

    @property
    def ThreadAwareLogger(self):
        """ Returns a logger with the name of active thread."""
        currentThread=threading.current_thread()
        loggerName="%s"%(currentThread.name)
        if hasattr(self,loggerName): 
            return eval("self.%s"%(loggerName))
        if hasattr(self,"debug") and hasattr(self.debug,loggerName): # 026 hack - tries to find logger in e.g. NodeProxy. While actually is in debug.
            return eval("self.debug.%s"%(loggerName))
        else:
            if hasattr(self,"cloneMainLogger"): # 026 hack (delegated logger tries to find cloneMainLogger in e.g. NodeProxy.
                return self.cloneMainLogger(loggerName)
            else: return self.debug.cloneMainLogger(loggerName)
        
    def printHeader(self,debugLevel=0):
        """
        This method print header of method, which is currently running.
        This helps to trace program operation.
        Also it is useful to assign error messages to method, where they rose.
        This method should be called at beginning of each method.
        Exceptions:
        There were some issues with calling that from __init__(). But I'm not sure what was it.
        No sense in calling this method from miscutil and it also can cause errors and cyclic dependencies.
        Future task: log hidden messages to file.
        """
        if self.headerLogger.level==logging.DEBUG:
            self.getCallerParams()
            self.headerLogger.debug('Calling method %s with arguments %s'%(self.callerName,self.callerLocals))
            if  ((debugLevel==0) or \
                 (self.callerName in self.settings.debugAllowed) or ('all' in self.settings.debugAllowed)) \
                 and ((debugLevel in self.settings.config.getList("log", "debugAllowedLevels") )) \
                 and (self.callerName not in self.settings.config.getList("log", "debugRestricted")):
                print 'Calling method %s with arguments %s'%(self.callerName,self.callerLocals)
            #else hiddenMessagesLog.append(message) # Dropped in 0.24 because of loggers.
        
    def getCallerParams(self,frameLevel=1):
        """
        Support for printHeader. It's hard to obtain name of method which is currently running.
        This method is based on recipe from Alex Martelli "Recipe 66062: Determining Current Function Name"
        http://code.activestate.com/recipes/66062/ 
        My implementation of this principle is collection of dirty hacks.
        
        Afaik(021) implementation is based on traversing trough call stack and trying to guess on which stack level is the right method.
        So wrapping of this method in other method may damage its functionality.
        I put together list of identifiers which are used in Debug class. I'm not interested in these identifiers, so when I find one, 
        I'll traverse to the next level in the call stack. Search ends when I'm out of debug, because then I'm in method from where
        printHeader was called and its name is that what I need.
        """
        # frameLevel=0 is always getCallerParams. Caller should be level 1, but sometimes level 1 is still in Debug. This causes many dirty hacks.
        levelsToAdd=frameLevel-1
        #debugDir=dir(self)
        #debugDir.remove('__init__') # without removing __init__ was debug unusable in any __init__. Following line is temporary unslashed only
        debugDir=['allowed', 'allowedLevels', 'caller', 'callerLocals', 'callerName', 'dprint', 'getCallerName', 'getCallerParams', 'printHeader', 'restricted', 'settings']
        while sys._getframe(frameLevel).f_code.co_name in debugDir: # restrict returning functions from Debug instance -- dirty hack
            # but causes trouble for init which is in every class. property debugDir hacks this issue.
            if frameLevel>1: print '%i: %s'%(frameLevel,sys._getframe(frameLevel).f_code.co_name)
            frameLevel+=1
        frameLevel+=levelsToAdd # another hack to get another frame
        self.caller=sys._getframe(frameLevel)
        self.callerLocals=self.caller.f_locals
        try:
            if self.callerLocals.has_key('self'):
                #debug.dprint(print str(self.callerLocals['self'].__class__).split(' ')[1],4)
                self.callerName=(
                                 str(self.callerLocals['self']).split(' ')[0].replace('<__main__.','')+
                                 '.'+self.caller.f_code.co_name)
                # 026 #if self.callerLocals.has_key('self'): del self.callerLocals['self'] # 025 Fix - caused errors in multithreadng.
            else: self.callerName=self.caller.f_code.co_name
        except KeyError, errorInstance:
            #026 #self.headerLogger.error("Caught KeyError. Error: %s; Arguments: %s"%(errorInstance,str(errorInstance.args)))
            self.headerLogger.exception("Caught KeyError. Error: %s; Arguments: %s"%(errorInstance,str(errorInstance.args)))
            self.headerLogger.debug("callerLocals is %s"%(str(self.callerLocals)))
        return (self.callerName,self.callerLocals)
    
    def getCallerName(self,frameLevel=1):
        """
        Only wrapper for public use of getcallerParams - should be backported to getCallerParams.
        Can be dangerous - adds another frame (another level to call stack for details see self.getCallerParams.__doc__ ). Frames are used for determining function name.
        """
        self.getCallerParams(frameLevel)
        result=self.callerName
        return result
    
    def get_open_fds(self):
        """
        return the number of open file descriptors for current process
        .. warning: will only work on UNIX-like os-es.
        """
        #By shaunc - http://stackoverflow.com/questions/2023608/check-what-files-are-open-in-python    
        import subprocess
        import os
     
        pid = os.getpid()
        procs = subprocess.check_output( 
            [ "lsof", '-w', '-Ff', "-p", str( pid ) ] )
     
        fprocs = filter(
                        lambda s: s and s[ 0 ] == 'f' and s[1: ].isdigit(),
                        procs.split( '\n' ) 
                        )
            
        return fprocs

class XMLDebug (Debug):
    """
    This class has to enrich debug class about XML capabilities. Honestly it shouldn't be here - this is a hack :-(
    There are two problems with this class:
        1) It does import unnecessary modules.
        2) There is a major problem with the paths. I do need to set them later, but I can't.
    This enhancement was developed as a part of an another project. But might be also usable.
    Without the two problems mentioned above it could be merged with class debug.
    """
    
    def __init__(self,workDir="/tmp/"):
        from xml.dom import minidom
        self.minidom=minidom
        import codecs
        self.codecs=codecs
        self.workDir=workDir
        Debug.__init__(self)

    def flushXMLChunk(self,node,fileName="chunck.xml"):
        #self.debug.printHeader() # calling debug from debug was causing errors
        self.XMLChunk=self.minidom.Document()
        self.XMLChunk.appendChild(node)
        self.XMLToWrite=self.XMLChunk.toprettyxml(indent="  ")
        self.XMLChunkFile = self.codecs.open(self.workDir+fileName,encoding='utf-8',mode="w")
        self.XMLChunkFile.write(self.XMLToWrite)
        self.XMLChunkFile.close()


class Shared(object):
    """
    Shared class is also significant hack!
    Trough Shared can every its child access to INSTANCE of debug and settings. 
    More over both Settings and Debug are singletons. No matter how many times you call their constructor
    you still have the same instance.
    
    All these hacks are done to simplify things a bit. I don't have to tell to every class where debug and settings are,
    they already know it from its parents.   
    """
    # 026 Hack removal incentive. Due to issues with sls.
    
    #Settings always goes first, because debug needs it.
    #settings=Settings()
    #debug=Debug() # Uncomment this for Sumid.    
    #debug=XMLDebug() # Uncomment this for docbook2testlink.
    #hitLogger=debug.hitLogger # Just a small hack to make logging just a bit easier. 
    #mainLogger=debug.mainLogger
    #comptreeLogger=debug.comptreeLogger
    
    
    def __init__(self):
        """
        This class is always used as abstract. No _init_() please.
        It can have only static methods.
        """
        self.sharedRef=self
        #raise NotImplementedError, "This is abstract class. No instance allowed."
        # Despite Shared is abstract, its children would inherit the constructor.
        
        
    def loadFromInterface(self):
        """
        Uuuf ... I'm not really sure what should this method perform (021).
        Looks like if I tried to bypass parameter rewriting, like in following example:
        
        def someMethod (self,parameter1,parameter2 ... parameterN):
            self.parameter1 = parameter1
            self.parameter1 = parameter2
            ...
            self.parameter1 = parameterN

        It's absolutely boring to rewrite input parameters to class property.
        But this idea may be not possible in constrains of language.  
        """
        self.debug.printHeader()
        # beware result of getCallerName includes name of class.
        """ #following doesn't work:
        callerName=self.debug.getCallerName(2)
        functionName=callerName.split('.')[1]
        debug.dprint('Function name is: %s'%(functionName),4)
        functionDict=eval('self.%s.__dict__'%(functionName))
        #functionDict=self.__init__.__dict__
        debug.dprint('Loader class name is %s'%(self.__class__.__name__),4)
        debug.dprint('Function dictionary size is %i'%(len(functionDict)),4)
        for key in functionDict.keys():
            debug.dprint('Adding property %s with value %s'%(key,functionDict[key].value),4)
            newProperty='self.%s=%s'%(key,functionDict[key].value)
            eval(newProperty)
        """
        self.debug.mainLogger.debug('\n\nNow going to print __init__ parameters')
        self.debug.mainLogger.debug(self.debug.getCallerParams(2))
        self.debug.mainLogger.debug('\n\nPrint __init__ parameters complete')
        
    @property
    def logger(self):
        """ To give every class access to default logger. """
        return self.debug.ThreadAwareLogger
        
class FactoryMethod(Shared):
    """
    Factory method creator by Mark Lutz(concrete creator not needed).
    http://code.activestate.com/recipes/59876/
    """
    
    def create (self,aClass,*args):
        """ Factory method """
        # 026 Due to clean-up of Shared. It's basically a hack. But it's lesser hack.
        if hasattr(self,"debug"): self.debug.printHeader()
        #return apply (aClass, args) # 025 Fixed deprecated syntax in Todo 119.
        return aClass(*args)
    
    def createRegisty(self): # from __main__.__dict__
        """
        Future task:
        create register of all classes available in Sumid
        to prevent creating object from non-existent class. 
        """
        self.debug.printHeader()
        raise NotImplementedYetError
            

    
class Callable:
    """
    Wrapper for static methods.
    ActiveState Recipe 52304: "Static-methods" (aka "class-methods") in Python 
    http://code.activestate.com/recipes/52304/
    
    Beware!! Static method can't be declared with self argument!
    """
    def __init__(self, anycallable):
        self.__call__ = anycallable


class CounterManager(Shared):
    """
    The idea is that all counters are managed by CounterManager which has only one instance, but carries multiple counters.
    But what about counting for each subtree?? 
    """
    # Originally I thought that manager would be Singleton.
    # But now I think that each comptree.Node will have own manager and will merge managers of children.
    # Calling counter 1st way: cmInstance.counterDict["counterName"].increment()
    # Calling counter 2nd way: cmInstance.increment("counterName")

    def __init__(self):
        self.counters={}
        self.__iadd__=self.mergeWithManager # Bypass for redefining + operation. See see http://rgruet.free.fr/PQR2.3.html#SpecialMethods
        self.title=None # The title is hack a bit. It is a way how to bind a counter manager with url.
    
    def addCounter(self,name): self.counters[name]=0
    
    def addCounters(self,args):
        """
        Does expect list as input.
        """
        # 025 Previous implementation was: def addCounters(self,*args): # Changed in order to get the list to settings.
        for counterName in args:
            if not self.hasCounter(counterName):
                self.addCounter(counterName)

    def printAllValues(self):
        """ A little confusing. This method prints counter names along with values. """
        # TODO: Rename
        result=""
        for counter in self.counters.keys():
            #result+="%s: %03d; "%(counter,self.counters[counter])
            result+="%s: %s; "%(counter,str(self.counters[counter]))
        return result
    
    def printAllValuesOnly(self):
        """ 
        A little confusing. Prints just pure values.
        Does return it in sorted order. 
        """
        # TODO: remove code duplication.
        result=""
        for counter in sorted(self.counters.keys()):
            #result+="%s: %03d; "%(counter,self.counters[counter])
            result+=" %s;"%(str(self.counters[counter]))
        return result    

    def mergeWithManager(self,anotherCounterManagerInstance):
        # TODO: Rename to        __iadd__(self, other)  ... see http://rgruet.free.fr/PQR2.3.html#SpecialMethods
        for counter in anotherCounterManagerInstance.counters.keys():
            if not self.counters.has_key(counter): self.addCounter(counter)
            self.counters[counter]+=anotherCounterManagerInstance.counters[counter]

    def increment(self,counterName,step=1):
        """
        Increments value of particular counter.
        If counter doesn't exist, it is created.
        """
        if not self.counters.has_key(counterName): 
            self.addCounter(counterName)
            # 026 was logged too often.
            # self.debug.mainLogger.debug("New counter created: %s"%(counterName))
        self.counters[counterName]+=step
    
    def hasCounter(self,counterName): 
        if self.counters.has_key(counterName): return True
               
    def value(self,counterName):
        """ Returns current state of specified counter. """
        if self.counters.has_key(counterName): result=self.counters[counterName]
        else: result=0
        return result
    
    def reset(self):
        """Sets all existing counters to 0."""
        for counterKey in self.counters.keys():
            self.counters[counterKey]=0
        self.title=None # 025 This is a hack of a hack. Trying to find if the counter was reset recently.
        
    def clear(self):
        """Removes all counters. That means removes all keys from self.counters. """
        #for counterName in self.counters:
        #    del self.counters[counterName]
        self.counters={}
        self.title=None
        
    def sumAllValues(self,*toSkip):
        """ Returns a sumation of all counters. (Without respect if the sumation makes sense.) """
        sum=0
        for counterKey in self.counters.keys():
            if not counterKey in toSkip: sum += self.counters[counterKey]
        # 026 #self.debug.mainLogger.debug("Sumation of all counters finished with result %i."%(sum))
        return sum
    
    @property
    def NumberOfCounters(self): return len(self.counters.keys())


class SchedulerOperation(threading._Timer):
    """
    Scheduler operation class by James Kassemi.  
    http://code.activestate.com/recipes/496800-event-scheduling-threadingtimer/
    Every instance represents one scheduled task which is done repeatedly. 
    """
    def __init__(self, *args, **kwargs):
        threading._Timer.__init__(self, *args, **kwargs)
        self.setDaemon(True)

    def run(self):
        while True:
            self.finished.clear()
            self.finished.wait(self.interval)
            if not self.finished.isSet():
                self.function(*self.args, **self.kwargs)
            else:
                return
            self.finished.set()

class SchedulerManager(object):
    """
    Scheduler operation class by James Kassemi.  
    http://code.activestate.com/recipes/496800-event-scheduling-threadingtimer/
    Manager manages all scheduled tasks.
    """
    ops = []

    def add_operation(self, operation, interval, args=[], kwargs={}):
        op = SchedulerOperation(interval, operation, args, kwargs)
        self.ops.append(op)
        thread.start_new_thread(op.run, ())

    def stop(self):
        for op in self.ops:
            op.cancel()
        #self._event.set() # 026 Causes AttributeError as stated in webpage comment.


# That's all folks!