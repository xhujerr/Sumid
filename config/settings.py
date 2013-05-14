# This file is part of SUMID, see sumid.py
# SUMID is released under terms of GPL, see http://www.gnu.org/licenses/gpl.txt

"""
 Inner Sumid configuration
 It is needed to change way how sumid loads configuration.
 This is the worst way, how to do it.
 But better than no configuration at all.
 This file has no other purpose than store configuration. 
"""
__version__="0.27"

#mainINIFilePath="/media/KINGSTON/Sumid/src/sumid.ini"
mainINIFilePath="../config/sumid.ini"

class RawSettings(object):
    # Linklist and workdir were moved to sumid.ini in 0.25.
    saveCleanLinklist=True      # in Sumid 0.08 was named save_sl
    needSort=False              # property of linklist. in Sumid 0.08 was named need_sort
    sortOnly=False              # property of linklist. in Sumid 0.08 was named sort_only
    logFetched=True             # in Sumid 0.08 was named log_fetched
    #previousRange=3  # 027 in sumid.ini           # After <previousRange> of unsuccessful Node Fetching will compTree processing break.
    maxLevels=2                 # How many levels are allowed for flood searching, counting from leafs. Means how many nested loops will be applied to link, it should be counted from tail.
    userAgent="Sumid %s - Experimental research project. (Debian GNU Linux x86_64).  sumid at gmx dot com ."%(__version__)
    printUris=False		# Tries to download target resource if set to false.
    linkListSpcSymbols=['#','@'] # Used in linklist cleaning. Everything after special character is NOT link.
    # 027 If @ among spc symbols, password protected resource cannot be fetched.
    minNumberLength=3           # used in PatternAnalyzer for files naming (2.ext is after 10.ext, but 002.ext is before 010.ext)
    
    forceMIMETypes=True # If is set to false, all files will be considered valid. Else only types in allowedMIMETypes.
    allowedMIMETypes=["text/html","text/html; charset=utf-8"]
    #allowedMIMETypes=["image/jpeg"]
    possibleMIMETypes=[ # If not here, then marked as unrecognized type and exception while download is thrown.
                       "application/msword",
                       "application/pdf",
                       "application/vnd.oasis.opendocument.text",
                       "image/gif",
                       "image/jpeg",
                       "text/html",
                       "text/plain",
                       "text/xml",
                       "text/x-python",
                       "text/html; charset=UTF-8",
                       "text/html; charset=utf-8",
                       "text/html; charset=ISO-8859-1",
                       "text/html;charset=ISO-8859-1"
                       "text/html; charset=windows-1254"
                       ]

    # Old style logging config begin.
    # Purpose of the move is to remove init definition from Debug.
    """
    Following debug levels should be implemented:
    0 Mandatory output
    1 Error
    2 Warning
    3 Info
    4 Debug
    5 Verbose visible -- i forgot meaning of this level
    Will be used as debugLevel property. Should be maintained by Settings instance.
    """
    # debug.allowed and debug.restricted is terrible conception -- should be replaced with levels
    debugAllowed=[None]    # functions listed here, are allowed to print. all means, all functions are allowed to print. this should be moved to settings
    debugRestricted=['LinklistAdaptor.parseLine','LinklistAdaptor.isValidUrl','LinklistAdaptor.trimSpcSymbols'
                     ,'FilesAdaptor.write'
                     ,'UnixPathStorage.composeURL','UnixPathStorage.composePath','UnixPathStorage.workDir'
                     ,'NodeProxy.__init__','NodeProxy.handleLink','NodeProxy.buildReferer','NodeProxy.loadFromInterface','NodeProxy.addComponent'#,'NodeProxy.operate'
                     ,'LeafProxy.sibsExtendDecision','LeafProxy.handleLink','LeafProxy.loadFromInterface','LeafProxy.createSibsContent','LeafProxy.addSibs'
                     ,'SwitchHandler.processArgs']
    # maybe operations could been restricted by class
    # restricted has higher priority than allowed, but isn't used for print header
    # 0.24 Concept of allowed classes could be used with loggers as well. Just create for lists: Error, Warning, Info and Debug.
    #    -- each list would contain names of the classes allowed with specific level.
    #    -- method enrichMainLogger will sett appropriate level for each class.
    debugAllowedLevels=[0,1,2,3]  # only messages with allowed level will be printed. Level 0 is allowed always. Allowed values 0,1,2,3,4.
    # restricted property is inverse to allowed
    
    # Old style logging config end.
    fileSipSize=7 # Amount of how much to read from a file in number of lines.
    # Is also limit for NodeQueue size.
    sibsLimit=50 # How many steps to side is allowed in createSibs (or sibsExtendDecision)
    checkContentLenth=True
    checkRetrievedURL=True
    maxTrialsPerTree=1000
    maxThreads=8 # (026) Soon will be replaced by CompTreeProcessorCount # Those are threads only for ComptreeProcessor.
    #progressReportInterval=3600 # 025 Probably replaced by schedulerDelay
    timeSleepNodeQueue=30 # "The nodeQueue is full waiting %s seconds if other thread takes care about it."
    timeWaitLinklistSupplier=30 # The linksQueue is full. Waiting %s seconds if other thread takes care about it.
    timeWaitCounterSupervisor=10
    timeWaitCompTreeProcessor=10 # When CompTreeProcessor is waiting in queue and other thread finishes all trees it has no chance to wake-up and finish.
    timeWaitMainThread=30#600
    timeWaitDefaultThread=2 # Used in abstract producer, when is not known which thread it is.
    schedulerDelay=600 # Time interval when the performance is measured. TPS to be exact.
    # threadWaitingTimeAdjustmentTable=[[90,-3],[10,+3],[70,-1],[30,+1]] # How waiting time should be adjusted based on queue lenght. That's linear function! y=7.5x-3.75 ; where x is queue occupancy and y is time adjustment in seconds.
    threadWaitingAdjustmentVector=[-7.5,3,75] # The time adjustment sloppiness setting. y=-7.5x+3.75 ; where x is queue occupancy and y is time adjustment in seconds.
    defaultCounters=["treeOperateTime","hits","contentLength","urlopenTime","linearPatternTrees","patternFound","zeroLengthMiss","differentURLMiss","statusResponseMiss","errorResponseMiss"]

    urlWordsSeparators=[',',' ','.','/','-','_','?','+','=','&']
    # urlWordsSeparators other candidates=['+',':','(',')']
    commonWords=["","http:","www","html","com","php","net","org","co","uk","htm","aspx","cfm","asp","au","cgi"]
    # Beware "at", "de", "us" could be country code, but also language code, which is a pattern. Depending on where they're found.
    # "cfm" is filetype.
    # "info" could be both - pattern or domain.
    bowTempSize=100 # Cache size. How many different counters bow acumulates before it writes it into DB.
    bowWaitTime=10 # How long is bow.BOWUpdater.consume() waiting, if his input queue is empty.
    linklistURLParts=["scheme", "netloc", "path", "params", "query", "fragment"]
    # End of class RawSettings