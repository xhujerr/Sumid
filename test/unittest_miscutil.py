"""Unit test for miscutil.py"""

__version__="0.27"


# Set path for thirdparty imports
import sys
sys.path.append('../thirdparty/')
sys.path.append('../src/')
sys.path.append('../config/')

import sqlite3
import os
import mocklegacy
from mock import Mock
import unittest
import miscutil
from miscutil import FilesAdaptor, FilesAdaptorComplex, CounterManager, Shared, Settings, Debug
from settings import *
#import copy

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

class DummySettings(miscutil.Settings):
     
    pass

class DebugDummy(miscutil.Debug):
    def __init__(self): pass
    def printHeader(self): pass

class NonSingleDummySettings(miscutil.Settings):
        
    _instance = None

    def __new__(cls, *args, **kwargs):
        #if not cls._instance:
        #cls._instance = super(miscutil.Singleton, cls).__new__(cls, *args, **kwargs)
        # Overriding the Settings constructor in order to no longer be a singleton.
        cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

class UnixPathStorageMock(Mock):
    
    def workDir(self):
        return "/home/sumid.results/unittests"
    
    def composeURL(self,splitedURL):
        return "/".join(splitedURL)

class SettingsTest(unittest.TestCase):

    def setUp(self):
        # (025) Rather indicate that I want Settings instance recreated. (Forcefully bypass the Singleton.):
        miscutil.Settings._instance = None
         
        self.settingsFile=file("../config/settings.py",'r')
        self.rawSettings=self.getKeysFromFile(self.settingsFile)
        self.INIFile=file("../config/sumid.ini",'r')
        self.rawINI=self.getKeysFromFile(self.INIFile)

    def getKeysFromFile(self,settingsFile):
        """ does process a settings.py file given and returns list of option names"""
        rawSettings={}
        for line in settingsFile:
            line=line.strip()
            # First filter out comments.
            if line.find('#')>=0:
                splittedLine=line.split('#')
                if splittedLine[0]: line=splittedLine[0]
                #else: continue # 025 Doesn't work, dunno why.
                else: line=""
            # Now get key from all lines where is assignment.
            if line.find('=')>=0:
                splittedLine=line.split('=')
                key=splittedLine[0].strip()
                value=splittedLine[1].strip()
                if value.startswith('"') and value.endswith('"'): value=value.strip('"')
                if value.isdigit(): value=int(value)
                if value=="True": value=True
                if value=="False": value=False
                #if key.startswith('_'): continue # 025 Doesn't work, dunno why.
                if key and key.startswith('_'): key=None # I want to ommit __version__
                if key and key.startswith("argparseArguments"): key=None # argparseArguments are not used
                if key and key.startswith('"'):  key=None # Removes string values considered by a mistake to be option.
                if key: rawSettings[key]=value
        #print "Length of rawSettings is %i"%(len(rawSettings.keys()))
        if  not len(rawSettings.keys()): raise AttributeError # (025) To check if rawAetting isn't empty.
        return rawSettings
        
    def test_loadFromSumid_containsAll(self):
        """ Does a settings instance contain all keys from settings.py ?"""
        containAllKeys=True
        
        # (025) Indicate that I want clean Settings instance:
        #miscutil.Settings._instance=None
        DummySettings._instance=None
        
        dummySettings=DummySettings()
        loadedSettings = dummySettings.loadFromSumid()
        
        for key in self.rawSettings.keys():
            if not hasattr(loadedSettings,key):
                print "Option %s wasn't loaded." %(key) 
                containAllKeys=False
        self.assertEqual(True,containAllKeys)
        
    def test_loadFromSumid_valuesCorrect(self):
        """Does loadFromSumid load all values correctly? (except lists)"""
        
        # containAllKeys=True # (026) Not used.
        dummySettings=DummySettings()
        loadedSettings = dummySettings.loadFromSumid()
        
        for key in self.rawSettings.keys():
            # Omitting verification of lists.
            if hasattr(loadedSettings,key) and \
            not str(self.rawSettings[key]).startswith('[') and \
            not (str(self.rawSettings[key]).find('%')>=0) :
            # Also omitting strings with replacements. 
                valueFromSettings=eval("loadedSettings.%s"%(key))
                rawSettinsValue=self.rawSettings[key]
                result=valueFromSettings==rawSettinsValue 
                if not result: print "Option %s wasn't loaded properly. %s is not equal to %s. (Or variable type differs.)" %(key,valueFromSettings,rawSettinsValue) 
                #self.assertEqual(result,True)    
                self.assertEqual(valueFromSettings,rawSettinsValue)

    # To test load from params run as follows:
    #python sumid.py --linklistURL /media/KINGSTON/Sumid/linklist/prelinklist24.txt --workDir /home/sumid.results/prelinklist24-01 --sibsLimit 5 
    def wrong_test_loadFromParams_containsAll(self):
        "Does result of loadFromParams contain all options required."
        #147: Parameters loaded as switches - first step: linklistURL, workDir, allowedMIMETypes
        # (025) The problem is usage of argparse.SUPPRESS. Good for program, bad for testing. 
        containAllKeys=True
        dummySettings=DummySettings()
        loadedSettings=dummySettings.loadFromParams()
        predefinedKeys=["linklistURL", "workDir", "allowedMIMETypes", "sibsLimit"]
        
        for key in predefinedKeys:
            if not hasattr(loadedSettings,key):
                print "Option %s wasn't loaded." %(key) 
                containAllKeys=False        
        self.assertEqual(True,containAllKeys)
                
    def wrong_test_loadFromParams_predefinedValues(self):
        "Are parameters from loadFromParams loaded correctly, when no cmdline options are passed to Sumid."
        #The problem is usage of argparse.SUPPRESS. Good for program, bad for testing.
        dummySettings=DummySettings()
        loadedSettings=dummySettings.loadFromParams()
        predefinedKeys=["linklistURL", "workDir", "allowedMIMETypes", "sibsLimit"]
        predefinedValues=["file:///media/KINGSTON/Sumid/linklist/prelinklist25.txt", "/home/sumid.results/prelinklist25-01", ["text/html","text/html; charset=utf-8"], 50]
        self.assertEqual(loadedSettings.linklistURL,"file:///media/KINGSTON/Sumid/linklist/prelinklist25.txt")
        self.assertEqual(loadedSettings.workDir,"/home/sumid.results/prelinklist25-01")
        self.assertEqual(loadedSettings.allowedMIMETypes,["text/html","text/html; charset=utf-8"])
        self.assertEqual(loadedSettings.sibsLimit,50)

    def test_loadFromINI_sectionsNames(self):
        """ Weren't changed section names (or added/removed) in main INI file? """
        dummySettings=DummySettings()
        dummySettings.loadFromINI(mainINIFilePath)
        localMainINIFilePath="/media/KINGSTON/Sumid/src/sumid.ini"
        localConfigParser=miscutil.EnhancedConfigParser()
        localConfigParser.read(localMainINIFilePath)
        predefinedSectionKeys=['files', 'httpResponse', 'main', 'log', 'compTree',"threads"]
        #['files', 'httpResponse', 'main', 'log', 'compTree', 'threads']
        #['files', 'compTree', 'log', 'threads', 'httpResponse', 'main']
        #print localConfigParser._sections.keys()
        for realKey in localConfigParser._sections.keys():
            self.assertTrue(realKey in predefinedSectionKeys)
        for predefinedKey in predefinedSectionKeys:
            self.assertTrue(predefinedKey in localConfigParser._sections.keys())
        #self.assertEqual(predefinedSectionKeys,localConfigParser._sections.keys())
        # 026 Order doesn't matter.
        
        
    def test_loadFromINI_containsAll(self):
        """ Does a loadFromINI product contain all keys from sumid.ini ?"""
        # (025) Indicate that I want clean Settings instance:
        #miscutil.Settings._instance=None
        DummySettings._instance=None
        
        containAllKeys=True
        dummySettings=DummySettings()
        localMainINIFilePath="/media/KINGSTON/Sumid/src/sumid.ini"
        loadedSettings=dummySettings.loadFromINI(localMainINIFilePath)
        
        for key in self.rawINI.keys():
            if not hasattr(loadedSettings,key):
                print "Option %s wasn't loaded." %(key) 
                containAllKeys=False
        self.assertEqual(True,containAllKeys)

    def test_loadFromINI_valuesCorrect(self):
        """Does loadFromINI load all values correctly? (except lists)"""
        
        dummySettings=DummySettings()
        localMainINIFilePath="../config/sumid.ini"
        loadedSettings=dummySettings.loadFromINI(localMainINIFilePath)
        
        for key in self.rawINI.keys():
            # Omitting verification of lists.
            if hasattr(loadedSettings,key) and \
            not str(self.rawINI[key]).startswith('[') and \
            not (str(self.rawINI[key]).find('%')>=0) :
            # Also omitting strings with replacements. 
                valueFromSettings=eval("loadedSettings.%s"%(key))
                rawSettinsValue=self.rawINI[key]
                result=valueFromSettings==rawSettinsValue 
                if not result: print "Option %s wasn't loaded properly. %s is not equal to %s. (Or variable type differs.)" %(key,valueFromSettings,rawSettinsValue) 
                self.assertEqual(valueFromSettings,rawSettinsValue)

class SettingsCarrier(object): pass
# Empty class to test the loadAdaptive() 
    
class AggregateSettingsTest(unittest.TestCase):
    
    #def tearDown(self):
    # Why does tearDown make half of the test cases fail??
        #""" Class DummySettings will get seriously fucked-up during these test. And since it's singleton it gets fucked-up everywhere. """
        # Trying to destroy the instance (or rather indicate that instance must be recreated):
        #miscutil.Settings._instance = None        
    
    # Redefined function to test load adaptive.
    # The option is either not defined in settings resource or carries the name of the resource.
    def returnEmptyCarrier(self,input=None): return SettingsCarrier()
    def returnCarrierSumid(self,input=None): 
        carrier = SettingsCarrier()
        carrier.option="Sumid"
        return carrier
    def returnCarrierINI(self,input=None): 
        carrier = SettingsCarrier()
        carrier.option="INI"
        return carrier
    def returnCarrierParam(self,input=None): 
        carrier = SettingsCarrier()
        carrier.option="Param"
        return carrier 

    # Now the tests:   
    def test_loadAdaptive_theoreticCombinations(self):
        "Does loadAdaptive combine the settings correctly? Theoretical test."
        
        #DummySettings._instance=None
        dummySettings=DummySettings()
        # Because Setting is singleton, I have to save original methods, before I attempt to change them.  
        
        #Save original methods first (not needed while settings instance gets recreated.):
        #saved_loadFromSumid = dummySettings.loadFromSumid
        #saved_loadFromINI = dummySettings.loadFromINI
        #saved_loadFromParams = dummySettings.loadFromParams
        
        # I do redefine each of loadFromSumid, loadFromINI and loadFromParams to return either empty object or object containing attribute option={"Sumid"|"INI"|"Param"}
        # Now I'll try all combinations.
        #allCombinationsPassed=True
        # 0 0 1 
        dummySettings.loadFromSumid=self.returnEmptyCarrier
        dummySettings.loadFromINI=self.returnEmptyCarrier
        dummySettings.loadFromParams=self.returnCarrierParam
        dummySettings.loadAdaptive("all")
        self.assertEqual(dummySettings.option,"Param")
        #if not dummySettings.option=="Param": allCombinationsPassed=False
        
        # 0 1 0
        dummySettings.loadFromSumid=self.returnEmptyCarrier
        dummySettings.loadFromINI=self.returnCarrierINI
        dummySettings.loadFromParams=self.returnEmptyCarrier
        dummySettings.loadAdaptive("all")
        self.assertEqual(dummySettings.option,"INI")
        #if not dummySettings.option=="INI": allCombinationsPassed=False
        
        # 0 1 1
        dummySettings.loadFromSumid=self.returnEmptyCarrier
        dummySettings.loadFromINI=self.returnCarrierINI
        dummySettings.loadFromParams=self.returnCarrierParam
        dummySettings.loadAdaptive("all")
        self.assertEqual(dummySettings.option,"Param")
        
        # 1 0 0        
        dummySettings.loadFromSumid=self.returnCarrierSumid
        dummySettings.loadFromINI=self.returnEmptyCarrier
        dummySettings.loadFromParams=self.returnEmptyCarrier
        dummySettings.loadAdaptive("all")
        self.assertEqual(dummySettings.option,"Sumid")

        # 1 0 1        
        dummySettings.loadFromSumid=self.returnCarrierSumid
        dummySettings.loadFromINI=self.returnEmptyCarrier
        dummySettings.loadFromParams=self.returnCarrierParam
        dummySettings.loadAdaptive("all")
        self.assertEqual(dummySettings.option,"Param")        

        # 1 1 0        
        dummySettings.loadFromSumid=self.returnCarrierSumid
        dummySettings.loadFromINI=self.returnCarrierINI
        dummySettings.loadFromParams=self.returnEmptyCarrier
        dummySettings.loadAdaptive("all")
        self.assertEqual(dummySettings.option,"INI")

        # 1 1 1        
        dummySettings.loadFromSumid=self.returnCarrierSumid
        dummySettings.loadFromINI=self.returnCarrierINI
        dummySettings.loadFromParams=self.returnCarrierParam
        dummySettings.loadAdaptive("all")
        self.assertEqual(dummySettings.option,"Param")
        
        # Restore original methods (not needed while settings instance gets recreated.):
        #dummySettings.loadFromSumid = saved_loadFromSumid 
        #dummySettings.loadFromINI = saved_loadFromINI 
        #dummySettings.loadFromParams = saved_loadFromParams 
                
        # Trying to destroy the instance (or rather indicate that instance must be recreated):
        #AdaptiveDummySettings._instance = None  
        #DummySettings._instance = None 
        miscutil.Settings._instance = None 

        #self.assertEqual(allCombinationsPassed,True)

    def test_loadAdaptive_partial(self):
        "Does loadAdaptive combine the settings correctly? Load just a part - test."
        
        #miscutil.Settings._instance=None
        #DummySettings._instance=None
        dummySettings=DummySettings()
        #"""
        # 1 1 1  when I want to load just from Sumid      
        dummySettings.loadFromSumid=self.returnCarrierSumid
        dummySettings.loadFromINI=self.returnCarrierINI
        dummySettings.loadFromParams=self.returnCarrierParam
        dummySettings.loadAdaptive("sumid")
        self.assertEqual(dummySettings.option,"Sumid")
        #"""
        # 1 1 1  load only from INI
        dummySettings.loadFromSumid=self.returnCarrierSumid
        dummySettings.loadFromINI=self.returnCarrierINI
        dummySettings.loadFromParams=self.returnCarrierParam
        dummySettings.loadAdaptive("INI")
        self.assertEqual(dummySettings.option,"INI")        
        #"""
        miscutil.Settings._instance = None 

    def test_loadAdaptive_labelCaseInsensitive(self):
        """ If I pass an keyword as a parameter to loadAdaptive it shouldn't be case sensitive."""
        dummySettings=DummySettings()

        # 1 1 1  when I want to load just from Sumid      
        dummySettings.loadFromSumid=self.returnCarrierSumid
        dummySettings.loadFromINI=self.returnCarrierINI
        dummySettings.loadFromParams=self.returnCarrierParam
        dummySettings.loadAdaptive("sumid")
        self.assertEqual(dummySettings.option,"Sumid")
        dummySettings.loadAdaptive("Sumid")
        self.assertEqual(dummySettings.option,"Sumid")
        dummySettings.loadAdaptive("SUMID")
        self.assertEqual(dummySettings.option,"Sumid")
        dummySettings.loadAdaptive("ini")
        self.assertEqual(dummySettings.option,"INI")
        dummySettings.loadAdaptive("Ini")
        self.assertEqual(dummySettings.option,"INI")
        dummySettings.loadAdaptive("INI")
        self.assertEqual(dummySettings.option,"INI")
        dummySettings.loadAdaptive("params")
        self.assertEqual(dummySettings.option,"Param")
        dummySettings.loadAdaptive("Params")
        self.assertEqual(dummySettings.option,"Param")
        dummySettings.loadAdaptive("PARAMS")
        self.assertEqual(dummySettings.option,"Param")   

        miscutil.Settings._instance = None       
        DummySettings._instance = None                 

class DebugTest(unittest.TestCase):
     
    """
What do we expect from method Debug.InitializeLoggers() ?
Following loggers are created afterwards:
hitLogger, cllLogger, cntLogger, missLogger, nopLogger, mainLogger

Then there is logging enrichment, which creates: dprintLogger, headerLogger, comptreeLogger
These do differ just by name. dprintLogger is already obsolete.

Each logger has specific parameters, but just for mainLogger and cntLogger does worth to check it.

Implicit inputs: self = Debug instance; self.settings

Future:
Each thread should have own instance of main logger.
    """
    def setUp(self): 
        # (026) Indicate that I want clean Settings instance:
        #miscutil.Settings._instance=None
        #DummySettings._instance=None
        miscutil.Debug._instance=None
        DebugDummy._instance=None
        
        dummySettings=DummySettings()
        # 026 overwrite what was really loaded from settings. Better. Not depending on actual sumid.ini.
        dummySettings.workDir="/home/sumid.results/unittest" 
        dummySettings.logDir="/home/sumid.results/unittest"
        
        self.dummyDebug=DebugDummy()
        self.dummyDebug.settings=dummySettings
        
        self.logDir="/home/sumid.results/unittest"

    def tearDown(self): pass
    
    def test_initializeLoggers_allLoggersCreated(self):
        """Verify if all loggers were created. """
        # hitLogger, cllLogger, cntLogger, missLogger, nopLogger, mainLogger, headerLogger, comptreeLogger
        
        self.dummyDebug.initializeLoggers()
        
        self.assertEqual(hasattr(self.dummyDebug,"hitLogger"),True)
        self.assertEqual(hasattr(self.dummyDebug,"cllLogger"),True)
        self.assertEqual(hasattr(self.dummyDebug,"cntLogger"),True)
        self.assertEqual(hasattr(self.dummyDebug,"missLogger"),True)
        self.assertEqual(hasattr(self.dummyDebug,"nopLogger"),True)
        self.assertEqual(hasattr(self.dummyDebug,"mainLogger"),True)
        self.assertEqual(hasattr(self.dummyDebug,"headerLogger"),True)
        self.assertEqual(hasattr(self.dummyDebug,"comptreeLogger"),True)


        """
            self.logFormatter=logging.Formatter("%(asctime)s | %(module)s | %(lineno)d | %(name)s | %(funcName)s | %(levelname)s | %(message)s")

            logFileName=self.settings.insertDatetimeIntoFilename(self.settings.mainLogFileName)
            mainLoggerPath=self.settings.logDir+"/"+logFileName
            self.mainLogLevel=self.settings.config.getDebugLevel("log","mainLogLevel")
        
            self.mainLogFileHandler = logging.FileHandler(mainLoggerPath, 'a') # 0.24 replaced by basicConfig - was workaround.
            self.mainLogFileHandler = logging.handlers.RotatingFileHandler(mainLoggerPath, maxBytes=52428800, backupCount=20)
            self.mainLogFileHandler.setFormatter(self.logFormatter) # 0.24 replaced by basicConfig
            comptreeLogLevel=self.settings.config.getDebugLevel("log","comptreeLogLevel")
        """

    def test_initializeLoggers_mainLogger(self):
        """Verify if parameters of mainLogger were loaded correctly. """
        #self.dummyDebug.settings
        
        self.dummyDebug.initializeLoggers()
        
        self.assertEqual(self.dummyDebug.mainLogger.level,10)
        self.assertEqual(self.dummyDebug.mainLogger.name,"main log")
        self.assertEqual(self.dummyDebug.mainLogger.handlers[-1].backupCount,20)
        # 026 Date is into file added by lograte automatically.
        #self.assertEqual(self.dummyDebug.mainLogger.handlers[-1].baseFilename,self.logDir+"/sumid.%s.log"%(miscutil.datetime.datetime.now().strftime("%Y%m%d")))
        self.assertEqual(self.dummyDebug.mainLogger.handlers[-1].level,0)
        self.assertEqual(self.dummyDebug.mainLogger.handlers[-1].maxBytes,52428800)
        self.assertEqual(self.dummyDebug.mainLogger.handlers[-1].mode,"a")
        self.assertEqual(self.dummyDebug.mainLogger.handlers[-1].formatter._fmt,"%(asctime)s | %(module)s | %(lineno)d | %(name)s | %(funcName)s | %(levelname)s | %(message)s")

    def test_initializeLoggers_cntLogger(self):
        """Verify if parameters of cntLogger were loaded correctly. """
        #self.dummyDebug.settings
        
        self.dummyDebug.initializeLoggers()
        
        self.assertEqual(self.dummyDebug.cntLogger.level,10)
        self.assertEqual(self.dummyDebug.cntLogger.name,"cntLogger")
        self.assertEqual(self.dummyDebug.cntLogger.handlers[-1].backupCount,50)
        self.assertEqual(self.dummyDebug.cntLogger.handlers[-1].baseFilename,self.logDir+"/counters.%s.csv"%(miscutil.datetime.datetime.now().strftime("%Y%m%d")))
        self.assertEqual(self.dummyDebug.cntLogger.handlers[-1].level,0)
        # 026 I decided that cnt logger won't be rotated by size. Is not that big.
        #self.assertEqual(self.dummyDebug.cntLogger.handlers[-1].maxBytes,52428800)
        self.assertEqual(self.dummyDebug.cntLogger.handlers[-1].mode,"a")

    def test_initializeLoggers_missLogger(self):
        """Verify if parameters of missLogger were loaded correctly. """
        #self.dummyDebug.settings
        
        self.dummyDebug.initializeLoggers()
        
        self.assertEqual(self.dummyDebug.missLogger.level,10)
        self.assertEqual(self.dummyDebug.missLogger.name,"missLogger")
        self.assertEqual(self.dummyDebug.missLogger.handlers[-1].backupCount,20)
        self.assertEqual(self.dummyDebug.missLogger.handlers[-1].baseFilename,self.logDir+"/miss.log")# 026 Old datetime inclusion: %s.log"%(miscutil.datetime.datetime.now().strftime("%Y%m%d")))
        self.assertEqual(self.dummyDebug.missLogger.handlers[-1].level,0)
        # 026 I decided that miss logger won't be rotated by size. Is not that big.
        #self.assertEqual(self.dummyDebug.missLogger.handlers[-1].maxBytes,52428800)
        self.assertEqual(self.dummyDebug.missLogger.handlers[-1].mode,"a")

    def test_initializeLoggers_hitLogger(self):
        """Verify if parameters of hitLogger were loaded correctly. """
        #self.dummyDebug.settings
        
        self.dummyDebug.initializeLoggers()
        
        self.assertEqual(self.dummyDebug.hitLogger.level,10)
        self.assertEqual(self.dummyDebug.hitLogger.name,"hitLogger")
        self.assertEqual(self.dummyDebug.hitLogger.handlers[-1].backupCount,20)
        self.assertEqual(self.dummyDebug.hitLogger.handlers[-1].baseFilename,self.logDir+"/hits.log")# 026 Old datetime inclusion: %s.log"%(miscutil.datetime.datetime.now().strftime("%Y%m%d")))
        self.assertEqual(self.dummyDebug.hitLogger.handlers[-1].level,0)
        #self.assertEqual(self.dummyDebug.hitLogger.handlers[-1].maxBytes,52428800) # 027 No longer rotated after maxsize.
        self.assertEqual(self.dummyDebug.hitLogger.handlers[-1].mode,"a")

class FilesAdaptortest(unittest.TestCase):
    
    def setUp(self):
        self.filesAdaptor=FilesAdaptor()       
        self.filesAdaptor.settings.workDir="/home/sumid.results/unittests/"
        self.filesAdaptor.settings.logDir="/home/sumid.results/unittests/"
    
    def tearDown(self):
        pass
    
    def test_initializeMagicFile(self):    
        """ Correct magic file shall be imported. """
        if os.path.exists("/usr/share/pyshared/magicgit.py"):
            self.assertTrue(hasattr(self.filesAdaptor,"magicgit"))
            self.assertEqual(self.filesAdaptor.magicType, "magicgit")
        elif os.path.exists("/usr/share/pyshared/magic.py"):
            self.assertTrue(hasattr(self.filesAdaptor,"magic"))
            self.assertEqual(self.filesAdaptor.magicType, "magic")
                        
    def test_writeFile(self): 
        """ Files adaptor writes a file based on url given into workDir/netloc/path. """
        # 027 Will fail in windows.
        url="http://www.example.com/directory/page007.html"
        desiredPath="/home/sumid.results/unittests/www.example.com/directory/page007.html"
        # 027 Remove remains of the previous tests.
        if os.path.exists(desiredPath):
            os.remove(desiredPath)
        # 027 Write and test existence.
        self.filesAdaptor.writeFile(url,self.filesAdaptor.linklist)
        self.assertTrue(os.path.exists(desiredPath))

class DBTest(unittest.TestCase):
    
    def setUp(self):
        self.filesAdaptor=FilesAdaptor()       
        self.filesAdaptorComplex=FilesAdaptorComplex()
        self.filesAdaptor.settings.workDir="/home/sumid.results/unittests/"
        self.filesAdaptor.settings.logDir="/home/sumid.results/unittests/"
        self.filesAdaptorComplex.settings.workDir="/home/sumid.results/unittests/"
        self.filesAdaptorComplex.settings.logDir="/home/sumid.results/unittests/"        
        # 027 First remove the old trash from previous tests.
        if os.path.exists("/home/sumid.results/unittests/sumid.log.sqlite"):
            os.remove("/home/sumid.results/unittests/sumid.log.sqlite")


    def test_connectAndDisconnectDB(self):
        """ Files adaptor creates db connection and ensures that BOW table exists."""
        # 026 Shall be also checked for following situations:
        # 1) Neither file nor BOW table exists.
        # 2) File exists, but not BOW table.
        # 3) Both, file and BOW table, exist.
        self.filesAdaptor.connectDB()
        self.assertTrue(isinstance(self.filesAdaptor.DBconnection,sqlite3.Connection))
        tableList=[]
        self.filesAdaptor.DBcursor.execute("select * from sqlite_master;")
        for row in self.filesAdaptor.DBcursor:
            tableList.append(row[2])
        #print tableList
        self.assertTrue("BOW" in tableList)
        self.filesAdaptor.disconnectDB()
        self.assertRaises(sqlite3.dbapi2.ProgrammingError,self.filesAdaptor.DBcursor.execute,"select * from sqlite_master;")
    
    def test_connectAndDisconnectComplexDB(self):
        """ Files adaptor creates db connection and ensures that BOW table exists."""
        # 026 Shall be also checked for following situations:
        # 1) Neither file nor BOW table exists.
        # 2) File exists, but not BOW table.
        # 3) Both, file and BOW table, exist.
        self.filesAdaptorComplex.connectDB()
        self.assertTrue(isinstance(self.filesAdaptorComplex.DBconnection,sqlite3.Connection))
        tableList=[]
        self.filesAdaptorComplex.DBcursor.execute("select * from sqlite_master;")
        for row in self.filesAdaptorComplex.DBcursor:
            tableList.append(row[2])
        #print tableList
        self.assertTrue("BOW" in tableList)
        self.filesAdaptorComplex.disconnectDB()
        self.assertRaises(sqlite3.dbapi2.ProgrammingError,self.filesAdaptorComplex.DBcursor.execute,"select * from sqlite_master;")
                
    def test_updateBOW(self):
        """ When specific counter is sent to update first time, counter gets INSERTed to db. Second time is just updated """
        self.filesAdaptor.connectDB()
        counters=CounterManager()
        counters.title="word"
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
        
    def createSampleComplexTable(self,DBcursor,DBconnection):
        """ Helper metod to create test bow table. """
        maxLine=10
        values=[1,1,1,1,1]
        # 027 Filling the sample table with values.
        for cx in range(maxLine):
            sql="insert into BOW (word,netloc_count,path_count,params_count,query_count,fragment_count) values ('word_%i',?,?,?,?,?);"%(cx+1)
            args=(values[0],values[1],values[2],values[3],values[4])
            # 027 Enhancing test for None values in db.
            if cx==2: args=(values[0],values[1],None,values[3],values[4])
            DBcursor.execute(sql,args)
            # 027 Values get incremented. To not make the table that boring.
            values[cx%len(values)]+=1
        DBconnection.commit()
        return True
    
    def test_BOW_finalize(self):
        """ Finalize counts the line sumas correctly.  """
        self.filesAdaptorComplex.connectDB()
        self.createSampleComplexTable(self.filesAdaptorComplex.DBcursor,self.filesAdaptorComplex.DBconnection)
        # 027 Find how many lines are in bow table.
        sql="select count(bow_id) from BOW;"
        args=()
        self.filesAdaptorComplex.DBcursor.execute(sql,args)
        result = self.filesAdaptorComplex.DBcursor.fetchall()
        bowLinesCount=result[0][0]
        # 027 Prepare for test.
        self.filesAdaptorComplex.finalize()
        sql="select netloc_count,path_count,params_count,query_count,fragment_count from BOW where bow_id=?;"      
        sqlTotal="select total_count from BOW where bow_id=?;"    
        # 027 verifiying line counts line by line for the sample table.
        for cx in range (bowLinesCount):
            # 027 The select stays the same, only the bow_id gets changed.
            args=(cx+1,)
            self.filesAdaptorComplex.DBcursor.execute(sql,args)
            dbLine=self.filesAdaptorComplex.DBcursor.fetchall()
            self.filesAdaptorComplex.DBcursor.execute(sqlTotal,args)
            result=self.filesAdaptorComplex.DBcursor.fetchall()
            # 027 The sumation of the current line.
            lineSuma=0
            for count in dbLine[0]:
                if count: lineSuma+=count
            # 027 #pprint.pprint(dbLine)
            # 027 #print lineSuma
            self.assertEqual(result[0][0], lineSuma)
            
    def test_getTableLinesCount(self):        
        """ FA just returns a number of lines in a table """
        self.filesAdaptorComplex.connectDB()
        self.createSampleComplexTable(self.filesAdaptorComplex.DBcursor,self.filesAdaptorComplex.DBconnection)
        result=self.filesAdaptorComplex.getTableLinesCount("BOW","bow_id")
        self.assertEqual(result, 10)
            
    def test_BOW_SumLine(self):
        """ Files adaptor counts and writes the sum of the line as netloc_count+path_count+params_count+query_count+fragment_count """
        self.filesAdaptorComplex.connectDB()
        self.createSampleComplexTable(self.filesAdaptorComplex.DBcursor,self.filesAdaptorComplex.DBconnection)    
        result=self.filesAdaptorComplex.sumBowLine(5)
        # 027 Verify that the result is correct.
        self.assertEqual(result, 9)
        # 027 Now let's verify if the result got written into db.   
        # 027 The commit is required to verify the write to db. Usually commit takes place only after all lines are sumed.
        self.filesAdaptorComplex.DBconnection.commit()
        sql="select total_count from BOW where bow_id=?"
        args=(5,)
        self.filesAdaptorComplex.DBcursor.execute(sql,args)
        result = self.filesAdaptorComplex.DBcursor.fetchall()
        self.assertEqual(result[0][0], 9)
        
    def test_mergeLines(self):
        """ FA adds second line to first and deletes the second. """
        self.filesAdaptorComplex.connectDB()
        self.createSampleComplexTable(self.filesAdaptorComplex.DBcursor,self.filesAdaptorComplex.DBconnection)    
        result=self.filesAdaptorComplex.mergeLines(3,5)
        # 027 The total count is None, coz the table was created again from scratch.
        expectedList=["word_3", None, 4, 4, 2, 3, 2]
        # 027 First check correctness of the combination.
        self.assertEqual(result, expectedList)
        # 027 Commit in order to check the writed to db.
        self.filesAdaptorComplex.DBconnection.commit()
        # 027 Check the writes in db.
        expectedList2=(3,"word_3", None, 4, 4, 2, 3, 2)
        #expectedList2.extend(expectedList)
        # 027 This shall be the combined line.
        sql="select * from BOW where bow_id=?"
        args=(3,)
        self.filesAdaptorComplex.DBcursor.execute(sql,args)
        result = self.filesAdaptorComplex.DBcursor.fetchall()
        self.assertEqual(result[0], expectedList2)
        # 027 The other line shall be deleted.        
        sql="select * from BOW where bow_id=?"
        args=(5,)
        self.filesAdaptorComplex.DBcursor.execute(sql,args)
        result = self.filesAdaptorComplex.DBcursor.fetchall()
        self.assertEqual(result, [])        
   
    def test_applyStemFilter(self):
        """ 
        FA attempts to clean bag of words based on stemization.
        Only if stemmed form already exists in the bag the lines will be merged.
        """
        self.filesAdaptorComplex.connectDB()
        self.createSampleComplexTable(self.filesAdaptorComplex.DBcursor,self.filesAdaptorComplex.DBconnection)
        # 027 Prepare some test values in db   
        sql="update BOW set word=? where bow_id=?"
        args=("cat",3)
        self.filesAdaptorComplex.DBcursor.execute(sql,args)
        args=("dog",5)
        self.filesAdaptorComplex.DBcursor.execute(sql,args)
        args=("dogs",6)
        self.filesAdaptorComplex.DBcursor.execute(sql,args)
        args=("cats",8)
        self.filesAdaptorComplex.DBcursor.execute(sql,args)
        args=("parrots",9)
        self.filesAdaptorComplex.DBcursor.execute(sql,args)
        args=("cat",10)
        self.filesAdaptorComplex.DBcursor.execute(sql,args)
        self.filesAdaptorComplex.DBconnection.commit()
        # 027 Now lets run the filter.
        self.filesAdaptorComplex.applyStemFilter()
        # 027 Now let's have a look what we got.
        # 027 Two cats
        sql="select * from BOW where word=?"
        args=("cat",)
        self.filesAdaptorComplex.DBcursor.execute(sql,args)
        result=self.filesAdaptorComplex.DBcursor.fetchall()
        self.assertEqual(len(result), 2, "Two 'cat's expected.")
        # 027 And one more cats
        sql="select * from BOW where word=?"
        args=("cats",)
        self.filesAdaptorComplex.DBcursor.execute(sql,args)
        result=self.filesAdaptorComplex.DBcursor.fetchall()
        self.assertEqual(len(result), 1, "One 'cats' expected.")
        # 027 Those because cats cannot be merged - cat is there twice.        
        # 027 Just one dog
        sql="select * from BOW where word=?"
        args=("dog",)
        self.filesAdaptorComplex.DBcursor.execute(sql,args)
        result=self.filesAdaptorComplex.DBcursor.fetchall()
        self.assertEqual(len(result), 1, "One 'dog' expected.")
        # 027 No dogs
        sql="select * from BOW where word=?"
        args=("dogs",)
        self.filesAdaptorComplex.DBcursor.execute(sql,args)
        result=self.filesAdaptorComplex.DBcursor.fetchall()
        self.assertEqual(len(result), 0, "No 'dogs' expected.")        
        # 027 And one parrots
        sql="select * from BOW where word=?"
        args=("parrots",)
        self.filesAdaptorComplex.DBcursor.execute(sql,args)
        result=self.filesAdaptorComplex.DBcursor.fetchall()
        self.assertEqual(len(result), 1, "One 'parrots' expected.")
        # 027 But no parrot
        sql="select * from BOW where word=?"
        args=("parrot",)
        self.filesAdaptorComplex.DBcursor.execute(sql,args)
        result=self.filesAdaptorComplex.DBcursor.fetchall()
        self.assertEqual(len(result), 0, "No 'parrot' expected.")                
   
    """
    027 This is note for testin stemization:
    
$ python
Python 2.7.3rc2 (default, Apr 22 2012, 22:30:17) 
[GCC 4.6.3] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import sqlite3
>>> conn=sqlite3.connect("sumid.log.sqlite")
>>> cur=conn.cursor()
>>> sql="select * from BOW where bow_id<10"
>>> args=()
>>> cur.execute(sql,args)
<sqlite3.Cursor object at 0x1b54650>
>>> results=cur.fetchall()
>>> import pprint
>>> pprint.pprint(results)
[(1, u'help', 345),
 (2, u'Time', 78),
 (3, u'papel', 3),
 (4, u'01dollarstore', 1),
 (5, u'167917099', 1),
 (6, u'notebooks', 13),
 (7, u'better', 245),
 (8, u'0800wallpapers', 1),
 (9, u'parents', 64)]
>>> type(results)
<type 'list'>
>>> type(results[1]
... )
<type 'tuple'>
>>> sql="select * from BOW where bow_id=10"
>>> cur.execute(sql,args)
<sqlite3.Cursor object at 0x1b54650>
>>> results2=cur.fetchall()
>>> pprint.pprint(results2)
[(10, u'deviantart', 18)]
>>> type(results2)
<type 'list'>
>>> type (results2[0])
<type 'tuple'>
>>> sql="select * from BOW where bow_id<1"
>>> cur.execute(sql,args)
<sqlite3.Cursor object at 0x1b54650>
>>> results3=cur.fetchall()
>>> pprint.pprint(results3)
[]
>>> type(results3)
<type 'list'>
>>> len(results)
9
>>> len(results2)
1
>>> len(results3)
0
    
    """
                        
if __name__ == "__main__":


    #settings=miscutil.Settings()
    # settings.mainINIFilePath="/media/KINGSTON/Sumid/src/testing.ini" # 026 For future - testing could have other settings.
    #settings.loadAdaptive("all")
    #miscutil.Shared.settings=settings
    #debug=miscutil.Debug(settings)
    #miscutil.Shared.debug=debug
    if not hasattr(Shared,"settings") or not hasattr(Shared,"debug"): setUpModule()

    unittest.main()   
    