"""Unit test for comptree.py"""

# Sources:
# Dive Into Python > Unit Testing
# http://diveintopython.org/unit_testing/
# Python unit testing
# http://agiletesting.blogspot.com/2005/01/python-unit-testing-part-1-unittest.html

__version__="0.27"

# Set path for imports
import sys
sys.path.append('../src/')

import unittest
import comptree
from miscutil import Settings, Debug, Shared, CounterManager
from mock import Mock

class LoggerDummy(object):
    # 026 Not used anymore.
    def warning(self,msg): pass
    def debug(self,msg): pass

# 026 All the logging is thrown away.    
class LoggerMock(Mock): pass

class DebugDummy(Debug):
    # 026 Not used anymore.
    def __init__(self):
        super(DebugDummy, self).__init__()
        self.comptreeLogger=LoggerMock() 
    def printHeader(self,*args): pass
    
class DebugMock(Mock):
    def __init__(self):
        super(DebugMock, self).__init__()
        self.comptreeLogger=LoggerMock()
    def printHeader(self,*args): pass

class ComponentStub(comptree.Component):
    """
    This stub is used just to be able to create an instance of abstract class.
    Best practice Unit testing abstract classes?
    http://stackoverflow.com/questions/243274/best-practice-unit-testing-abstract-classes
    """
    def __init__(self):
        # 026 Forcing Debug(Singleton) to recreate:
        DebugDummy._instance=None
        self.debug=DebugMock() 
        self.link="http://www.google.com"
        #pass # (025) Inherits constructor from parent. - Must override if I want simple object.
        
    

class ComptreeMock(unittest.TestCase):
    # TODO create versatile mock for testing comptree.
    # Beware there are three classes used as the tree components.
    pass

class ComponentTest(unittest.TestCase):
# Best practice Unit testing abstract classes?
# http://stackoverflow.com/questions/243274/best-practice-unit-testing-abstract-classes

    def setUp(self):
        pass
    
# sibsExtendDecision
# Returns single bool value true/false.
# This value is used by addsibs to add sibs to both sides at once. 

# 1  Is outside of sibsLimit                        => False
# 2  Is outside of maxTrialsPerTree                 => False
# 3  Is inside  of previousRange.
# 3a Is inside  of sibsLimit and maxTrialsPerTree    => True
# 4  Is outside of previousRange.
# 4a Is inside  of sibsLimit and maxTrialsPerTree
# 4aa There is at least one sib in previousRange with status < 300 => True
# 4ab There is NO sib in previousRange with status < 300 => False

# For checking if is in/outside sibsLimit is used self.parent.processedChildren .
# For checking if is in/outside maxTrialsPerTree is used self.counters.value("patternFound")
# For checking if is in/outside previousRange is used self.parent.processedChildren .

# Need to define:
# How should sibsExtendDecision behave if node don't have counters or counters.value("patternFound")?
#     -- This usually happen when it is first node/leaf in the tree to be processed.
# Root node doesn't have parent. TODO: Create test for it.
# Write test for following exception:
    exception="""
Exception in thread Thread-8:
Traceback (most recent call last):
  File "/usr/lib/python2.6/threading.py", line 532, in __bootstrap_inner
    self.run()
  File "sumid.py", line 540, in run
    comptreeResult=self.process(self.tree)
  File "sumid.py", line 561, in process
    comptreeResult=tree.operate()
  File "/media/KINGSTON/Sumid/src/comptree.py", line 554, in operate
    if self.sibsExtendDecision():
  File "/media/KINGSTON/Sumid/src/comptree.py", line 206, in sibsExtendDecision
    if hasattr(self,"parent"): sibsCount=len(self.parent.processedChildren)
AttributeError: 'NoneType' object has no attribute 'processedChildren'
"""
# It happens only sometimes, not for each root node. 



    def test_sibsExtendDecision_out_sibsLimit(self):
        """ sibsExtendDecision should return false after the sibs limit was reached."""
        # Creating artificial pseudo-tree as an input data.
        # TODO: (025) Precise the limiting number after the test works.
        parentNode=ComponentStub()
        parentNode.settings.sibsLimit=50
        parentNode.processedChildren=[]
        parentNode.counters=CounterManager()
        parentNode.counters.increment("patternFound", 52)
        previousComponentStub=None
        for i in range(52):
            # Creating simplified node with links to parent and sibs.
            # Probably I'll define a function which copies a bit creation of node in comptree.
            componentStub=ComponentStub()
            componentStub.parent=parentNode
            parentNode.processedChildren.append(componentStub)
            if previousComponentStub:
                previousComponentStub.next=componentStub
            componentStub.previous=previousComponentStub
            componentStub.counters=CounterManager()
            componentStub.counters.increment("patternFound")
            previousComponentStub=componentStub
        # Needed to add next to the last node:
        parentNode.processedChildren[-1].next=None
        # END: Creating artificial pseudo-tree as an input data.
        # Now I gonna take last child and try the sibs decision.
        testedNode=parentNode.processedChildren[-1]
        # TODO: Following line shouldn't be needed. It should end just because of the limit.
        testedNode.settings.previousRange=3
        #testedNode.debug=DebugDummy()
        result=testedNode.sibsExtendDecision()
        self.assertEqual(False,result)
        
    def test_sibsExtendDecision_out_maxTrialsPerTree(self):
        """ sibsExtendDecision should return false after the maxTrialsPerTree limit was reached."""
        # For checking if is in/outside maxTrialsPerTree is used self.counters.value("patternFound")
        parentNode=ComponentStub()
        componentStub=ComponentStub()
        parentNode.processedChildren=[]
        parentNode.processedChildren.append(componentStub)
        componentStub.next=None
        componentStub.previous=None
        componentStub.parent=parentNode
        componentStub.settings.maxTrialsPerTree=1000
        componentStub.counters=CounterManager()
        componentStub.counters.increment("patternFound",1002)        
        result=componentStub.sibsExtendDecision()
        self.assertEqual(False,result)        

    def test_sibsExtendDecision_lessNodesThan_previousRange(self):
        """ sibsExtendDecision should return true if there is less nodes than previousRange and didn't reach any limit."""        
        parentNode=ComponentStub()
        componentStub=ComponentStub()
        parentNode.processedChildren=[]
        parentNode.processedChildren.append(componentStub)
        componentStub.next=None
        componentStub.previous=None
        componentStub.parent=parentNode
        componentStub.settings.maxTrialsPerTree=1000
        componentStub.settings.previousRange=3
        componentStub.settings.sibsLimit=50
        componentStub.counters=CounterManager()
        componentStub.counters.increment("patternFound",3)
        result=componentStub.sibsExtendDecision()
        self.assertEqual(True,result)        

    def test_sibsExtendDecision_succesfullNodeInSibs(self):
        """ 
        sibsExtendDecision should return true if:
            - None of sibsLimit and maxTrialsPerTree were reached.
            - There is more sibs than previousRange.
            - At least one of the nodes in previousRange has status<300.
        """        
        # Creating artificial pseudo-tree as an input data.
        parentNode=ComponentStub()
        parentNode.settings.sibsLimit=50
        parentNode.processedChildren=[]
        parentNode.counters=CounterManager()
        parentNode.counters.increment("patternFound", 8)
        previousComponentStub=None
        for i in range(8):
            # Creating simplified node with links to parent and sibs.
            # Probably I'll define a function which copies a bit creation of node in comptree.
            componentStub=ComponentStub()
            componentStub.parent=parentNode
            parentNode.processedChildren.append(componentStub)
            if previousComponentStub:
                previousComponentStub.next=componentStub
            componentStub.previous=previousComponentStub
            componentStub.counters=CounterManager()
            componentStub.counters.increment("patternFound")
            componentStub.settings.previousRange=3
            componentStub.settings.maxTrialsPerTree=1000
            componentStub.settings.sibsLimit=50
            componentStub.status=404
            previousComponentStub=componentStub
        # Needed to add next to the last node:
        parentNode.processedChildren[-1].next=None
        # Now I gonna change status in one node to success.
        parentNode.processedChildren[-3].status=200
        # END: Creating artificial pseudo-tree as an input data.
        # Now I gonna take last child and try the sibs decision.
        testedNode=parentNode.processedChildren[-1]
        result=testedNode.sibsExtendDecision()
        self.assertEqual(True,result)


    def test_sibsExtendDecision_noSuccesfullNodeInSibs(self):
        """ 
        sibsExtendDecision should return false if:
            - None of sibsLimit and maxTrialsPerTree were reached.
            - There is more sibs than previousRange.
            - There is no node in previousRange with status<300.
        """        
        # Creating artificial pseudo-tree as an input data.
        parentNode=ComponentStub()
        parentNode.settings.sibsLimit=50
        parentNode.processedChildren=[]
        parentNode.counters=CounterManager()
        parentNode.counters.increment("patternFound", 8)
        previousComponentStub=None
        for i in range(8):
            # Creating simplified node with links to parent and sibs.
            # Probably I'll define a function which copies a bit creation of node in comptree.
            componentStub=ComponentStub()
            componentStub.parent=parentNode
            parentNode.processedChildren.append(componentStub)
            if previousComponentStub:
                previousComponentStub.next=componentStub
            componentStub.previous=previousComponentStub
            componentStub.counters=CounterManager()
            componentStub.counters.increment("patternFound")
            componentStub.settings.previousRange=3
            componentStub.settings.maxTrialsPerTree=1000
            componentStub.settings.sibsLimit=50
            componentStub.status=404
            previousComponentStub=componentStub
        # Needed to add next to the last node:
        parentNode.processedChildren[-1].next=None
        # Status of all nodes is kept unsuccessful.
        # END: Creating artificial pseudo-tree as an input data.
        # Now I gonna take last child and try the sibs decision.
        testedNode=parentNode.processedChildren[-1]
        result=testedNode.sibsExtendDecision()
        self.assertEqual(False,result)
        
if __name__ == "__main__":

    settings=Settings()
    # settings.mainINIFilePath="/media/KINGSTON/Sumid/src/testing.ini" # 026 For future - testing could have other settings.
    settings.loadAdaptive("all")
    Shared.settings=settings
    debug=Debug(settings)
    Shared.debug=debug

    unittest.main()           
