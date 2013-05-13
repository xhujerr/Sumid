#!/bin/env python

#    SLS - Sumid link supplier
#    Copyright (C) 2010  Roman Hujer <sumid at gmx dot com>
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
__programLongName__="Sumid link supplier"
__version__="0.03"
__authors__="Roman Hujer <sumid at gmx dot com>"
__year__="2010"

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
v003 Adapted to work with miscutil 0.26.
"""
# Settings begin
mainINIFilePath='/media/KINGSTON/Sumid/src/sls.ini'
#Settings end

import pydigg
# PyDigg is a Python toolkit for the Digg API. It provides an object-oriented interface to all of the available endpoints of the API. It is offered under the MIT License
# PyDigg probably works with old API version.
# http://neothoughts.com/pydigg/
# Digg API - Overview
# http://digg.com/api/docs/overview
# http://apidoc.digg.com/Toolkits#Python    #obsolete?
#from miscutil import Singleton
import ConfigParser
import logging
import logging.handlers
import miscutil # Interoperates with version 0.24
import os

class DebugHelper(miscutil.Shared):
    """
    This class is temporary solution for local logging.
    """
    def InitializeLoggers(self):
        
        #if not(os.path.exists(self.settings.get("log","logDir"))):os.makedirs(self.settings.get("log","logDir"))
        if not(os.path.exists(self.settings.logDir)):os.makedirs(self.settings.logDir) # For compatibility with miscutil 0.26

        #logFileName=self.settings.insertDatetimeIntoFilename(self.settings.get("log","linksLogFileName"))
        logFileName=self.settings.insertDatetimeIntoFilename(self.settings.linksLogFileName) # For compatibility with miscutil 0.26
        #linkLoggerPath=self.settings.get("log","logDir")+"/"+logFileName
        linkLoggerPath=self.settings.logDir+"/"+logFileName # For compatibility with miscutil 0.26

        # Setup logging
        self.linkLogger = logging.getLogger("link log")
        self.linkLogger.setLevel(logging.DEBUG)

        filelog = logging.FileHandler(linkLoggerPath, 'a')
        filelog.setLevel(logging.INFO)
        
        # Specify log formatting:
        #formatter = logging.Formatter("%(asctime)s - %(name)s - %(lineno)s - \
        #%(levelname)s - %(message)s")
        
        #filelog.setFormatter(formatter)
        # Add console log to self.linkLogger
        
        self.linkLogger.addHandler(filelog)

        
        #logFileName=self.settings.insertDatetimeIntoFilename(self.settings.get("log","mainLogFileName"))
        logFileName=self.settings.insertDatetimeIntoFilename(self.settings.mainLogFileName) # For compatibility with miscutil 0.26
        #mainLoggerPath=self.settings.get("log","logDir")+"/"+logFileName
        mainLoggerPath=self.settings.logDir+"/"+logFileName # For compatibility with miscutil 0.26
        
        # set up logging to file - see previous section for more details
        logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s | %(module)s | %(lineno)d | %(name)s | %(funcName)s | %(levelname)s | %(message)s",
                    filename=mainLoggerPath,
                    filemode='a')
        # define a Handler which writes INFO messages or higher to the sys.stderr
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        # set a format which is simpler for console use
        #formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        # tell the handler to use this format
        #console.setFormatter(formatter)
        # add the handler to the root logger
        logging.getLogger('cons log').addHandler(console)

        # Now, define a couple of other loggers which might represent areas in your
        # application:

        self.mainLogger = logging.getLogger('main log')
        #self.logFormatter=logging.Formatter("%(asctime)s | %(module)s | %(lineno)d | %(name)s | %(funcName)s | %(levelname)s | %(message)s")
        #self.mainFileHandler=logging.FileHandler(mainLoggerPath, 'a')
        #self.mainFileHandler.setFormatter(self.logFormatter)
        #self.mainLogger.addHandler(self.mainFileHandler)
        
        #logger2 = logging.getLogger('myapp.area2')

class DiggFetcher(miscutil.Shared):
    
    def connectDiggAdaptor(self,diggAdaptorInstance):
        """ Explicit include of pyDigg (by Derek van Vliet <derek@neothoughts.com>) """
        if not hasattr(self,"diggAdaptor") or not self.diggAdaptor:
            self.diggAdaptor=diggAdaptorInstance
            self.getStories=self.diggAdaptor.getStories

    def connectLocalDebug(self,debug2Instance):
        """ Temporary debug2 connection. Before it would be included to miscutil. """
        self.debug2=debug2Instance
    
    def fetch(self):
        #stories = diggAdaptor.getStories(count=str(self.settings.get("digg", "getStoriesCount"))) 
        stories = diggAdaptor.getStories(count=str(self.settings.getStoriesCount)) # For compatibility with miscutil 0.26
        self.debug2.mainLogger.info("Got another %i diggs"%(len(stories)))
        for story in stories:
            self.debug2.linkLogger.info(story.link)             


# body begin

settings = miscutil.Settings()
miscutil.Shared.settings=settings
settings.mainINIFilePath=mainINIFilePath
settings.loadFromINI(mainINIFilePath)
debug=miscutil.Debug(settings)
miscutil.Shared.debug=debug
debug2=DebugHelper()
settings.loadAdaptive("all",settings.pathStorage) # loadAdaptive has to be called after creating Debug instance, because Debug.__init__() overwrites it => Singleton doesn't work. Maybe it is because Singleton does work!
debug2.InitializeLoggers()
#debug.loadSettings(settings) # obs 0.01
#debug.initializeLoggers() # Can't do this in init, becase I don't know settings at that time. obs 0.01

#diggAdaptor=pydigg.Digg(settings.get("digg","APIKey"))
diggAdaptor=pydigg.Digg(settings.APIKey) # For compatibility with miscutil 0.26

debug2.mainLogger.info("Basic initialization complete.")

#stories = diggAdaptor.getStories() # obs 0.01
#debug2.mainLogger.info("Got another %i diggs"%(len(stories)))
#for story in stories:
#    #print story.title
#    #print story.link
#    debug2.linkLogger.info(story.link)

diggFetcher=DiggFetcher()
diggFetcher.connectLocalDebug(debug2)
diggFetcher.connectDiggAdaptor(diggAdaptor)
diggFetcher.fetch()

# body end    