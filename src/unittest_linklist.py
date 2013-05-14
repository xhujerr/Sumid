"""Unit test for sumid.py"""
# http://bayes.colorado.edu/PythonGuidelines.html#unit_tests

__version__="0.27"

import unittest
from linklist import SmartURL, LinklistAdaptor, TextLinklistParser
import copy
from mock import Mock
import urllib2
#from miscutil import Settings

class Settings(object):
    linkListSpcSymbols=['@','#']
    urlWordsSeparators=[',',' ','.','/','-','_','?']

class SmartURLTest(unittest.TestCase): 
# SmartURL is initialized by a URL string.

    testURLs=[
              "http://foo.com/blah_blah_(wikipedia)",
              "http://www.extinguishedscholar.com/wpglob/?p=364",
              "x-yojimbo-item://6303E4C1-6A6E-45A6-AB9D-3A908F59AE0E",
              "http://example.com/something?with,commas,in,url, but not at end",
              "http://www.asianewsphoto.com/(S(neugxif4twuizg551ywh3f55))/Web_ENG/View_DetailPhoto.aspx?PicId=752",
              "http://lcweb2.loc.gov/cgi-bin/query/h?pp/horyd:field(NUMBER+band(thc+5a46634))",
              "http://argouml-stats.tigris.org/documentation/manual-0.26/ch02.html",
              "http://www.kosek.cz/clanky/swn-xml/ar02s17.html"
             ]
    manuallySplittedURLs=[
                          ["http:","","foo.com","blah_blah_(wikipedia)"],
                          ["http:","","www.extinguishedscholar.com","wpglob","?p=364"],
                          ["x-yojimbo-item:","","6303E4C1-6A6E-45A6-AB9D-3A908F59AE0E"],
                          ["http:","","example.com","something?with,commas,in,url, but not at end"],
                          ["http:","","www.asianewsphoto.com","(S(neugxif4twuizg551ywh3f55))","Web_ENG","View_DetailPhoto.aspx?PicId=752"],
                          ["http:","","lcweb2.loc.gov","cgi-bin","query","h?pp","horyd:field(NUMBER+band(thc+5a46634))"],
                          ["http:","","argouml-stats.tigris.org","documentation","manual-0.26","ch02.html"],
                          ["http:","","www.kosek.cz","clanky","swn-xml","ar02s17.html"]
                          ]    

    manuallyWordedURLs=[
              ["http:","","foo","com","blah","blah","(wikipedia)"],
              ["http:","","www","extinguishedscholar","com","wpglob","","p=364"],
              ["x","yojimbo","item:","","6303E4C1","6A6E","45A6","AB9D","3A908F59AE0E"],
              ["http:","","example","com","something","with","commas","in","url","","but","not","at","end"],
              ["http:","","www","asianewsphoto","com","(S(neugxif4twuizg551ywh3f55))","Web","ENG","View","DetailPhoto","aspx","PicId=752"],
              ["http:","","lcweb2","loc","gov","cgi","bin","query","h","pp","horyd:field(NUMBER+band(thc+5a46634))"],
              ["http:","","argouml","stats","tigris","org","documentation","manual","0","26","ch02","html"],
              ["http:","","www","kosek","cz","clanky","swn","xml","ar02s17","html"]
             ]

    # 026 Partes are: scheme, netloc, path, params, query, fragment
    # Path always starts with a slash (if url isn't relative). Thus there's one empty field at the beginning of every path.
    # The same at the end of path if continues.
    manuallyWordedURLsPerPartes=[
              [["http"],["foo","com"],["","blah","blah","(wikipedia)"],[""],[""],[""]],
              [["http"],["www","extinguishedscholar","com"],["","wpglob",""],[""],["p=364"],[""]],
              [["x","yojimbo","item"],["6303E4C1","6A6E","45A6","AB9D","3A908F59AE0E"],[""],[""],[""],[""]], # 026 Only a file. Thus doesn't start or end with a slash.
              [["http"],["example","com"],["","something"],[""],["with","commas","in","url","","but","not","at","end"],[""]],
              [["http"],["www","asianewsphoto","com"],["","(S(neugxif4twuizg551ywh3f55))","Web","ENG","View","DetailPhoto","aspx"],[""],["PicId=752"],[""]],
              [["http"],["lcweb2","loc","gov"],["","cgi","bin","query","h"],[""],["pp","horyd:field(NUMBER+band(thc+5a46634))"],[""]],
              [["http"],["argouml","stats","tigris","org"],["","documentation","manual","0","26","ch02","html"],[""],[""],[""]],
              [["http"],["www","kosek","cz"],["","clanky","swn","xml","ar02s17","html"],[""],[""],[""]]
             ]
    
    def setUp(self):
        self.URL=SmartURL("someString")
        self.settings=Settings()
        #self.settings.loadFromINI("/media/KINGSTON/Sumid/src/sumid.ini")
        
    
    def tearDown(self):
        self.URL=None
        
    def test_SmartURL_create(self):
        """SmartURL has two basic properties: splitted and composed -> they return correct content."""
        idx=0
        for testString in self.testURLs:
            url=SmartURL(testString)
            self.assertEqual(testString,url.Composed)
            self.assertEqual(self.manuallySplittedURLs[idx],url.Splitted)
            idx+=1

    def test_SmartURL_isValid(self):
        """SmartURL.isValid raises an AttributeError when input is nonString. (Including None and empty string.)"""
        url=SmartURL("http://foo.com/blah_blah") # Dummy url to avoid unbound local method error.
        self.assertRaises(ValueError,url.isValid,None)
        self.assertRaises(ValueError,url.isValid,"")
        self.assertRaises(ValueError,url.isValid,["http:","","foo.com,blah_blah_(wikipedia)"])
        self.assertRaises(ValueError,url.isValid,"#http://foo.com/blah_blah_(wikipedia)")
        self.assertRaises(ValueError,url.isValid,"http://foo.com/blah_blah_(wikipedia) # Some comment here")
        self.assertRaises(ValueError,url.isValid,"                              http://foo.com/blah_blah_(wikipedia)                     ")
            
    def test_SmartURL_nonString(self):
        """SmartURL raises an AttributeError when input is nonString. (Including None and empty string.)"""
        self.assertRaises(ValueError,SmartURL,None)
        self.assertRaises(ValueError,SmartURL,"")
        self.assertRaises(ValueError,SmartURL,["http:","","foo.com,blah_blah_(wikipedia)"])
        self.assertRaises(ValueError,SmartURL,"#http://foo.com/blah_blah_(wikipedia)")
        self.assertRaises(ValueError,SmartURL,"http://foo.com/blah_blah_(wikipedia) # Some comment here")
        self.assertRaises(ValueError,SmartURL,"                              http://foo.com/blah_blah_(wikipedia)                     ")

    def test_SmartURL_SpcSymbol(self):
        """SmartURL has a field for spc symbol """
        url=SmartURL("http://foo.com/blah_blah_(wikipedia)","@This is a command")
        self.assertEqual(url.SPCPart,"@This is a command")
        
    def test_SmartURL_seed(self):
        """ SmartURL has a seed. The seed doesn't change when splitted or composed change."""
        url=SmartURL("http://foo.com/blah_blah_(wikipedia)")
        seed=copy.copy(url.Seed)
        url.Composed="http://foo.com/blah_blah"
        self.assertEqual(seed,url.Seed)
        url=SmartURL("http://foo.com/blah_blah_(wikipedia)")
        url.Splitted=["http:","","foo.com","blah_blah","(nonsense)"]
        self.assertEqual(seed,url.Seed)
    
    def test_SmartURL_changes(self):
        """SmartURL: If either splitted or composed changes, the other changes accordingly."""
        url=SmartURL("http://foo.com/blah_blah_(wikipedia)")
        url.Composed="http://bar.com/blah_blah_(wikipedia)"
        self.assertEqual(url.Composed,"http://bar.com/blah_blah_(wikipedia)") # 026 First check if Composed was really changed.
        self.assertEqual(["http:","","bar.com","blah_blah_(wikipedia)"],url.Splitted) # 026 Then check if the change was reflected by Splitted.
        url=SmartURL("http://www.kosek.cz/clanky/swn-xml/ar02s17.html")
        url.Splitted=["http:","","www.vrabec.cz","clanky","swn-xml","ar03s18.html"]
        self.assertEqual(url.Splitted,["http:","","www.vrabec.cz","clanky","swn-xml","ar03s18.html"]) # 026 First check if Splitted was really changed.
        self.assertEqual(url.Composed,"http://www.vrabec.cz/clanky/swn-xml/ar03s18.html") # 026 Then check if the change was reflected by Composed.

    def test_SmartURL_relative(self):
        """ SmartURL has methods isAbsolute, isRelative. """
        url=SmartURL("http://argouml-stats.tigris.org/documentation/manual-0.26/ch02.html")
        self.assertFalse(url.isRelative())
        self.assertTrue(url.isAbsolute())
        url=SmartURL("documentation/manual-0.26/ch02.html")
        self.assertFalse(url.isAbsolute())
        self.assertTrue(url.isRelative())

        """
        SmartURL has a read-only property Words.
        There's a setting urlWordsSeparators.
        Words splits url to words using urlWordsSeparators.
        
        The think is that SmartURL doesn't have settings instance. And it's not easy to give it to it.
        So Words will receive urlWordsSeparators as a parameter. 
        
        Thus Words cannot be a property!
        """
 
    def test_multiSeparatorSplit_predefined(self):
        """ Separates input string by multiple separators. Input is string, result is list."""
        url=SmartURL("http://foo.com/blah_blah_(wikipedia)")
        idx=0
        for urlString in self.testURLs:
            url=SmartURL(urlString)
            self.assertEqual(url.multiSeparatorSplit(url.Composed,self.settings.urlWordsSeparators),self.manuallyWordedURLs[idx])
            idx+=1
    
    def test_multiSeparatorSplit_custom(self):
        """ Separates input string by multiple separators. Input is string, result is list."""
        
        input="x-yojimbo-item://6303E4C1-6A6E-45A6-AB9D-3A908F59AE0E"
        output=["x","yojimbo","item://6303E4C1","6A6E","45A6","AB9D","3A908F59AE0E"]
        splitters=['-']
        url=SmartURL(input)
        self.assertEqual(url.multiSeparatorSplit(input,splitters),output)
        
        input="x-yojimbo-item://6303E4C1-6A6E-45A6-AB9D-3A908F59AE0E"
        output=["x-yojimbo-item://6303E4C1-6A6E-45A6-AB9D-3A908F59AE0E"]
        splitters=[' ']
        url=SmartURL(input)
        self.assertEqual(url.multiSeparatorSplit(input,splitters),output)
        
        input="Skakal pes pres oves, pres zelenou louku."
        output=["Skakal","pes","pres","oves,","pres","zelenou","louku."]
        splitters=[' ']
        url=SmartURL(input)
        self.assertEqual(url.multiSeparatorSplit(input,splitters),output)
        
        
    def test_SmartURL_Words(self):
        """ SmartURL.Words splits url to words using urlWordsSeparators."""
        idx=0
        for urlString in self.testURLs:
            url=SmartURL(urlString)
            self.assertEqual(url.Words(self.settings.urlWordsSeparators),self.manuallyWordedURLs[idx])
            idx+=1

    def test_SmartURL_Words_PerPartes(self):
        """ SmartURL.Words splits url to words using urlWordsSeparators."""
        idx=0
        for urlString in self.testURLs:
            url=SmartURL(urlString)
            self.assertEqual(url.WordsPerPartes(self.settings.urlWordsSeparators),self.manuallyWordedURLsPerPartes[idx])
            idx+=1

            
    def test_netloc(self):
        """ SmartUrl returns netloc out of full url or empty string for relative url."""
        url=SmartURL("http://argouml-stats.tigris.org/documentation/manual-0.26/ch02.html")
        self.assertEqual(url.netloc,"argouml-stats.tigris.org")
        url=SmartURL("/documentation/manual-0.26/ch02.html")
        self.assertEqual(url.netloc,"")
        
    def test_scheme(self):
        """ SmartUrl returns scheme out of full url or empty string for relative url."""
        url=SmartURL("https://argouml-stats.tigris.org/documentation/manual-0.26/ch02.html")
        self.assertEqual(url.scheme,"https")
        url=SmartURL("/documentation/manual-0.26/ch02.html")
        self.assertEqual(url.scheme,"")        

    def test_path(self):
        """ SmartUrl returns path for both relative and absolute url."""
        url=SmartURL("http://argouml-stats.tigris.org/documentation/manual-0.26/ch02.html")
        self.assertEqual(url.path,"/documentation/manual-0.26/ch02.html")
        url=SmartURL("/documentation/manual-0.26/ch02.html")
        self.assertEqual(url.path,"/documentation/manual-0.26/ch02.html")
        url=SmartURL("http://argouml-stats.tigris.org")
        self.assertEqual(url.path,"")

    def test_query(self):
        """ SmartUrl returns query for both relative and absolute url."""
        url=SmartURL("http://lcweb2.loc.gov/cgi-bin/query/h?pp/horyd:field+(NUMBER+band(thc+5a46634))")
        self.assertEqual(url.query,"pp/horyd:field+(NUMBER+band(thc+5a46634))")
        url=SmartURL("/cgi-bin/query/h?pp/horyd:field+(NUMBER+band(thc+5a46634))")
        self.assertEqual(url.query,"pp/horyd:field+(NUMBER+band(thc+5a46634))")
        url=SmartURL("http://argouml-stats.tigris.org")
        self.assertEqual(url.query,"")        
    
    # 026 Well I forbade character # in SmartURL    
    #def test_path(self):
    #    """ SmartUrl returns path for both relative and absolute url."""
    #    url=SmartURL("http://lcweb2.loc.gov/cgi-bin/query/h?pp/horyd:field#(NUMBER+band(thc+5a46634))")
    #    self.assertEqual(url.fragment,"(NUMBER+band(thc+5a46634))")
    #    url=SmartURL("/cgi-bin/query/h?pp/horyd:field#(NUMBER+band(thc+5a46634))")
    #    self.assertEqual(url.fragment,"(NUMBER+band(thc+5a46634))")
    #    url=SmartURL("http://argouml-stats.tigris.org")
    #    self.assertEqual(url.fragment,"")   

    def test_hostname(self):
        """ SmartUrl returns hostname for absolute url and None for relative url."""
        url=SmartURL("http://user:heslo@argouml-stats.tigris.org:3516")
        self.assertEqual(url.hostname,"argouml-stats.tigris.org")
        url=SmartURL("/cgi-bin/query/h?pp/horyd:field+(NUMBER+band(thc+5a46634))")
        self.assertEqual(url.hostname,None)
        url=SmartURL("http://argouml-stats.tigris.org")
        self.assertEqual(url.hostname,"argouml-stats.tigris.org")      

    def test_port(self):
        """ SmartUrl returns port if specified, None else."""
        url=SmartURL("http://user:heslo@argouml-stats.tigris.org:3516")
        self.assertEqual(url.port,3516)
        url=SmartURL("/cgi-bin/query/h?pp/horyd:field+(NUMBER+band(thc+5a46634))")
        self.assertEqual(url.port,None)
        url=SmartURL("http://argouml-stats.tigris.org")
        self.assertEqual(url.port,None)   

    def test_username(self):
        """ SmartUrl returns username if specified, None else."""
        url=SmartURL("http://user:heslo@argouml-stats.tigris.org:3516")
        self.assertEqual(url.username,"user")
        url=SmartURL("/cgi-bin/query/h?pp/horyd:field+(NUMBER+band(thc+5a46634))")
        self.assertEqual(url.username,None)
        url=SmartURL("http://argouml-stats.tigris.org")
        self.assertEqual(url.username,None)  

    def test_password(self):
        """ SmartUrl returns password if specified, None else."""
        url=SmartURL("http://user:heslo@argouml-stats.tigris.org:3516")
        self.assertEqual(url.password,"heslo")
        url=SmartURL("/cgi-bin/query/h?pp/horyd:field+(NUMBER+band(thc+5a46634))")
        self.assertEqual(url.password,None)
        url=SmartURL("http://argouml-stats.tigris.org")
        self.assertEqual(url.password,None)  

class LinklistTest(unittest.TestCase):
    
    def setUp(self):
        self.linklistInstance=LinklistAdaptor()
        debugMock=Mock()
        settings=Settings()
        self.linklistInstance.debug=debugMock
        self.linklistInstance.settings=settings
        self.linklistPath="/media/KINGSTON/Sumid/linklist/prelinklist25.txt"
        
    def tearDown(self):
        self.linklistInstance=None
        

    def test_nextRaw_noLinklist(self):
        """ If there's no linklist connected, nextRaw raises error."""
        # Suppose thers's no linlist until I connect it.
        self.assertRaises(BufferError,self.linklistInstance.nextRaw)
        self.linklistInstance.linklist=None
        self.assertRaises(BufferError,self.linklistInstance.nextRaw,)
        
    def test_nextRaw_correctLinklist(self):
        """ nextRaw returns a line without any modification, when linklist is set correctly. """
        #linklistPath="/media/KINGSTON/Sumid/linklist/prelinklist25.txt"
        # First peek what is first line of the linklist.
        linklistFile=file(self.linklistPath,'r')
        firstLine=linklistFile.readline()
        linklistFile.close()
        # Set-up URL linklist for test.
        linklistURL="file://%s"%(self.linklistPath)
        linklistFile=urllib2.urlopen(linklistURL)
        self.linklistInstance.connectLinklistFile(linklistFile)
        line=self.linklistInstance.nextRaw()
        # The URL test.
        self.assertEqual(firstLine,line)
        # Set-up file linklist for test.
        linklistFile=file(self.linklistPath,'r')
        self.linklistInstance.connectLinklistFile(linklistFile)
        line=self.linklistInstance.nextRaw()
        #The file test
        self.assertEqual(firstLine,line)
        
    def test_connectLinklistFile_wrongInput(self):
        """ If the input of connectLinklistFile() is not a file-like object, exception is raised."""
        self.assertRaises(AttributeError,self.linklistInstance.connectLinklistFile,"/This/is/a/string")
        self.assertRaises(AttributeError,self.linklistInstance.connectLinklistFile,["This","is","a","list"])
        self.assertRaises(AttributeError,self.linklistInstance.connectLinklistFile,{"This":"is","a":"dict"})
        self.assertRaises(AttributeError,self.linklistInstance.connectLinklistFile,object())
        
    def test_connectLinklistFile_correctInput(self):
        """ If the input of connectLinklistFile() is a file-like object, then self.linklist link to it is created. """
        #linklistPath="/media/KINGSTON/Sumid/linklist/prelinklist25.txt"
        linklistURL="file://%s"%(self.linklistPath)
        linklistFile=urllib2.urlopen(linklistURL)
        self.linklistInstance.connectLinklistFile(linklistFile)
        self.assertEqual(self.linklistInstance.linklist.geturl(),linklistURL)
        linklistFile=file(self.linklistPath,'r')
        self.linklistInstance.connectLinklistFile(linklistFile)
        self.assertEqual(self.linklistInstance.linklist.name,self.linklistPath)

class TextLinklistParserTest(unittest.TestCase):
    
    def setUp(self):
        self.textLinklistParserInstance=TextLinklistParser()
        debugMock=Mock()
        settings=Settings()
        self.textLinklistParserInstance.debug=debugMock
        self.textLinklistParserInstance.settings=settings
        self.linklistPath="/media/KINGSTON/Sumid/linklist/prelinklist26.txt"
        
    def tearDown(self):
        self.textLinklistParserInstance=None

    def test_trimSpcSymbols(self):
        """ Line is trimmed. It returns list: [url,symbol,textAfterSymbol]"""
        oneStringURLWithSPC=""
        self.assertEqual(self.textLinklistParserInstance.trimSpcSymbols(oneStringURLWithSPC) ,["",None,None])
        oneStringURLWithSPC="http://foo.com/blah_blah"
        self.assertEqual(self.textLinklistParserInstance.trimSpcSymbols(oneStringURLWithSPC) ,["http://foo.com/blah_blah",None,None])
        oneStringURLWithSPC="#http://foo.com/blah_blah"
        self.assertEqual(self.textLinklistParserInstance.trimSpcSymbols(oneStringURLWithSPC) ,["","#","http://foo.com/blah_blah"])
        oneStringURLWithSPC="http://foo.com/blah_blah #comment"
        self.assertEqual(self.textLinklistParserInstance.trimSpcSymbols(oneStringURLWithSPC) ,["http://foo.com/blah_blah ","#","comment"])
        oneStringURLWithSPC="http://foo.com/blah_blah @command"
        self.assertEqual(self.textLinklistParserInstance.trimSpcSymbols(oneStringURLWithSPC) ,["http://foo.com/blah_blah ","@","command"])
        oneStringURLWithSPC="@command"     
        self.assertEqual(self.textLinklistParserInstance.trimSpcSymbols(oneStringURLWithSPC) ,["","@","command"])

    """
    parseToSmartURL
    - Input is one raw line from linklist.
    - Output is SmartURL instance.
    --    SPC part is trimmed
    --    URL part is striped
    --    If url string is invalid, exception is thrown (it is the matter of SmartURL)
    --    Skips empty lines or comments. (Returns None for those)
    """
    
    def test_parse2SmartURL(self):
        """ Parses one raw line to SmartURL instance. Handles correctly URL part and SPC part."""
        oneStringURLWithSPC=" "
        url=self.textLinklistParserInstance.parse2SmartURL(oneStringURLWithSPC)
        self.assertEqual(url,None)
        
        oneStringURLWithSPC="#http://foo.com/blah_blah"
        url=self.textLinklistParserInstance.parse2SmartURL(oneStringURLWithSPC)
        self.assertEqual(url,None)
        
        oneStringURLWithSPC="http://foo.com/blah_blah"
        url=self.textLinklistParserInstance.parse2SmartURL(oneStringURLWithSPC)
        self.assertEqual(url.Composed,"http://foo.com/blah_blah")
        self.assertEqual(url.SPCPart,None)
        
        oneStringURLWithSPC="http://foo.com/blah_blah @command"
        url=self.textLinklistParserInstance.parse2SmartURL(oneStringURLWithSPC)
        self.assertTrue(isinstance(url,SmartURL))
        self.assertEqual(url.Composed,"http://foo.com/blah_blah")
        self.assertEqual(url.SPCPart,"@command")
        
        oneStringURLWithSPC="http://foo.com/blah_blah #comment"
        url=self.textLinklistParserInstance.parse2SmartURL(oneStringURLWithSPC)
        self.assertTrue(isinstance(url,SmartURL))
        self.assertEqual(url.Composed,"http://foo.com/blah_blah")
        self.assertEqual(url.SPCPart,"#comment")     
        
    def test_next(self):                   
        """ Next provides another SmartURL instance. """
        linklist=urllib2.urlopen("file://%s"%(self.linklistPath))
        linklistInstance=LinklistAdaptor()
        linklistInstance.connectLinklistFile(linklist)
        self.textLinklistParserInstance.connectLinklistAdaptor(linklistInstance)
        next=self.textLinklistParserInstance.next()
        # 026 If this test fails, check if first line of linklist is not commented out.
        self.assertTrue(isinstance(next,SmartURL))

    def test_next_noLinklist(self):
        """ If there's no linklist connected, next raises error."""
        # Suppose thers's no linklist until I connect it.
        self.assertRaises(AttributeError,self.textLinklistParserInstance.next)
        self.textLinklistParserInstance.linklistAdaptorInstance=None
        self.assertRaises(AttributeError,self.textLinklistParserInstance.next)
        
    def test_connectLinklistAdaptor_wrongInput(self):
        """ Linklist parser allows connect only LinklistAdaptor instance."""
        self.assertRaises(AttributeError,self.textLinklistParserInstance.connectLinklistAdaptor,"/This/is/a/string")
        self.assertRaises(AttributeError,self.textLinklistParserInstance.connectLinklistAdaptor,["This","is","a","list"])
        self.assertRaises(AttributeError,self.textLinklistParserInstance.connectLinklistAdaptor,{"This":"is","a":"dict"})
        self.assertRaises(AttributeError,self.textLinklistParserInstance.connectLinklistAdaptor,object())
        self.assertRaises(AttributeError,self.textLinklistParserInstance.connectLinklistAdaptor,file(self.linklistPath))
        self.assertRaises(AttributeError,self.textLinklistParserInstance.connectLinklistAdaptor,urllib2.urlopen("file://%s"%(self.linklistPath)))
        
    def test_connectLinklistAdaptor_correctInput(self):
        """Linklist parser stores link to a LinklistAdaptor instance, when gets it as a input parameter."""  
        linklistInstance=LinklistAdaptor()
        self.textLinklistParserInstance.connectLinklistAdaptor(linklistInstance)  
        self.assertTrue(hasattr(self.textLinklistParserInstance,"linklistAdaptorInstance"))
        self.assertTrue(isinstance(self.textLinklistParserInstance.linklistAdaptorInstance,LinklistAdaptor))
                        
if __name__ == "__main__":
    
    #whole=False
    whole=True
    
    if whole:
        unittest.main()   