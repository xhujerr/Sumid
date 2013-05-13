"""Unit test for miscutil.py"""

__version__="0.26"

import unittest
import miscutil
from settings import *
#import copy

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

class SettingsTest(unittest.TestCase):

    def setUp(self):
        # (025) Rather indicate that I want Settings instance recreated. (Forcefully bypass the Singleton.):
        miscutil.Settings._instance = None
         
        self.settingsFile=file("settings.py",'r')
        self.rawSettings=self.getKeysFromFile(self.settingsFile)
        self.INIFile=file("sumid.ini",'r')
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
        localMainINIFilePath="/media/KINGSTON/Sumid/src/sumid.ini"
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
        self.assertEqual(self.dummyDebug.hitLogger.handlers[-1].maxBytes,52428800)
        self.assertEqual(self.dummyDebug.hitLogger.handlers[-1].mode,"a")
                
if __name__ == "__main__":

    settings=miscutil.Settings()
    # settings.mainINIFilePath="/media/KINGSTON/Sumid/src/testing.ini" # 026 For future - testing could have other settings.
    settings.loadAdaptive("all")
    miscutil.Shared.settings=settings
    debug=miscutil.Debug(settings)
    miscutil.Shared.debug=debug

    unittest.main()   
    