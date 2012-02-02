# Copyright (c) 2009, Joseph Lisee
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of StatePy nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY Joseph Lisee ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <copyright holder> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Author: Joseph Lisee
# File:  statepy/test/state.py


# STD Imports
import unittest
import StringIO
import inspect
import os.path

# Project Imports
import statepy.state as state
#import ram.logloader as logloader


# --------------------------------------------------------------------------- #
#                      S U P P P O R T    O B J E C T S                       #
# --------------------------------------------------------------------------- #

class Reciever(object):
    def __init__(self):
        self.event = None
        self.called = False
    
    def __call__(self, event):
        self.event = event
        self.called = True

class MockEventSource(object):
    THING_UPDATED = state.declareEventType('THING_UPDATED')
    ANOTHER_EVT = state.declareEventType('ANOTHER_EVT')

class TrackedState(state.State):
    """Records whether a state has been entered or exited"""
    def __init__(self, *args, **kwargs):
        state.State.__init__(self, *args, **kwargs)
        self.entered = False
        self.exited = False

    def enter(self):
        self.entered = True

    def exit(self):
        self.exited = True

# --------------------------------------------------------------------------- #
#                           T E S T   S T A T E S                             #
# --------------------------------------------------------------------------- #

# Test States (Consider Magic base class to take care of the init method)

class Start(TrackedState):
    def __init__(self, *args, **kwargs):
        TrackedState.__init__(self, *args, **kwargs)
        self.event = None
        self.func = None
        self.thingUpdatedEvent = None
        self.anotherEvtEvent = None
        
    @staticmethod
    def transitions():
        return { "Start" : End,
                 "Change" : Simple,
                 "LoopBack" : LoopBack ,
                 MockEventSource.THING_UPDATED : Simple,
                 MockEventSource.ANOTHER_EVT : QueueTestState,
                 "Branch" : state.Branch(BranchedState) }

    def Change(self, event):
        self.event = event
        
    def THING_UPDATED(self, event):
        self.thingUpdatedEvent = event
        
    def ANOTHER_EVT(self, event):
        self.anotherEvtEvent = event

class QueueTestState(TrackedState):
    @staticmethod
    def transitions():
        return {MockEventSource.ANOTHER_EVT : Simple}

class Simple(TrackedState):
    @staticmethod
    def transitions():
        return {MockEventSource.ANOTHER_EVT : Start}

class LoopBack(TrackedState):
    @staticmethod
    def transitions():
        return { "Update" : LoopBack }
    
    def __init__(self, *args, **kwargs):
        TrackedState.__init__(self, *args, **kwargs)
        self.transCount = 0
        self.enterCount = 0

    def enter(self):
        TrackedState.enter(self)
        self.enterCount += 1

    def Update(self, event):
        self.transCount += 1

class End(TrackedState):
    pass

class BranchedState(TrackedState):
    @staticmethod
    def transitions():
        return { "InBranchEvent" : BranchedMiddle }
    
class BranchedMiddle(TrackedState):
    @staticmethod
    def transitions():
        return { "InBranchEndEvent" : BranchedEnd }
    
class BranchedEnd(state.End):
    def __init__(self):
        state.End.__init__(self, *args, **kwargs)
        self.entered = False
        self.exited = False
        
    def enter(self):
        self.entered = True

    def exit(self):
        self.exited = True

# States which attempt to find the loopback error
class First(state.State):
    @staticmethod
    def transitions():
        return { "GO" : Second }
    
class Second(state.State):
    @staticmethod
    def transitions():
        return { "GO" : Simple }
    
class FirstParent(state.State):
    @staticmethod
    def transitions():
        return { "GO" : SecondParent }
        
class SecondParent(state.State):
    @staticmethod
    def transitions():
        return { "BOB" : End }
    
    def enter(self):
        self.stateMachine.start(state.Branch(First))

# --------------------------------------------------------------------------- #
#                     T E S T   F R E E   F U N C T I O N S                   #
# --------------------------------------------------------------------------- #

class TestFreeFunctions(unittest.TestCase):
    
    # The following was taken from the python cookbook reciepe: 145297
    def lineno(self):
        """Returns the current line number in our program."""
        return inspect.currentframe().f_back.f_lineno

    
    def testDeclareEventType(self):
        # Make sure the path always ends in .py
        fileName = os.path.splitext(__file__)[0] + ".py"
        expectedLineNum = str(self.lineno() + 1)
        evtType = state.declareEventType("An Event")

        expectedResult = fileName + ":" + expectedLineNum + " " + "An_Event"
        self.assertEquals(expectedResult, evtType)
        
    
# --------------------------------------------------------------------------- #
#                         T E S T   M A C H I N E                             #
# --------------------------------------------------------------------------- #

class TestStateMachine(unittest.TestCase):
    def setUp(self):
        self.machine = state.Machine()
        self.machine.start(Start)

    def _makeEvent(self, etype, **kwargs):
        event = state.Event(etype)
        for key, value in kwargs.iteritems():
            setattr(event, key, value)
        return event

    def testbasic(self):
        # Check to make sure we get the default
        cstate = self.machine.currentState()
        self.assertEquals(Start, type(cstate))

    def testStart(self):
        cstate = self.machine.currentState()
        self.assert_(cstate.entered)
        self.assertFalse(cstate.exited)
        
    def testInjectEvent(self):
        startState = self.machine.currentState()

        self.machine.injectEvent(self._makeEvent("Change", value = 1))
        cstate = self.machine.currentState()

        # Check to me sure we left the start state
        self.assert_(startState.exited)

        # Check to make sure we reached the proper state
        self.assertEquals(Simple, type(cstate))
        self.assert_(cstate)

        # Make sure the transition function was called
        self.assertNotEquals(None, startState.event)
        self.assertEquals(startState.event.value, 1)

        # Now make sure we can inject events with the type directly
        self.machine.injectEvent(MockEventSource.ANOTHER_EVT)
        self.assertEquals(Start, type(self.machine.currentState()))

    def testStop(self):
        # No States
        machine = state.Machine()
        machine.stop()

        # Normal
        startState = self.machine.currentState()

        # Stop the machine and make sure events have no effect
        self.machine.stop()

        self.assertRaises(Exception, self.machine.injectEvent,
                          self._makeEvent("Start", value = 1))
        cstate = self.machine.currentState()

        self.assertNotEquals(End, type(cstate))
        self.assertNotEquals(startState, cstate)

    def testSimple(self):
        self.machine.injectEvent(self._makeEvent("Change"))
        cstate = self.machine.currentState()
        self.assertEquals(Simple, type(cstate))

    def testLoop(self):
        self.machine.injectEvent(self._makeEvent("LoopBack"))
        cstate = self.machine.currentState()

        # Ensure we got into are looping state
        self.assertEquals(LoopBack, type(cstate))
        self.assert_(cstate.entered)

        # Make  A Loopback
        self.machine.injectEvent(self._makeEvent("Update"))
        newstate = self.machine.currentState()

        self.assertEquals(LoopBack, type(newstate))
        self.assertFalse(newstate.exited)
        self.assertEquals(1, newstate.transCount)
        self.assertEquals(1, newstate.enterCount)
        self.assertEquals(newstate, cstate)

        # Repated loopbacks
        for i in xrange(1,5):
            self.machine.injectEvent(self._makeEvent("Update"))
        self.assertEquals(5, cstate.transCount)
        self.assertFalse(newstate.exited)
        self.assertEquals(1, newstate.enterCount)
       
    def testComplete(self):
#        enterRecv = Reciever()
#        exitRecv = Reciever()
#        self.machine.subscribe(state.Machine.STATE_ENTERED, enterRecv)
#        self.machine.subscribe(state.Machine.STATE_EXITED, exitRecv)
        
        # Ensure that completion is detected
        self.assertEqual(False, self.machine.complete)
        self.machine.injectEvent(self._makeEvent("Start"))
        self.assert_(self.machine.complete)
        
        # State machine is done, make sure there is no current state
        self.assertEqual(None, self.machine.currentState())
        
        # Ensure we entered and exited the exit state
#        endName = '%s.%s' % (End.__module__, End.__name__)
#        self.assertEquals(endName, enterRecv.event.string)
#        self.assertEquals(endName, exitRecv.event.string)


# NOTE: No event system in stand alone StatePy so these sections are disabled

#    def testEvents(self):
#        enterRecv = Reciever()
#        exitRecv = Reciever()
#        completeRecv = Reciever()
#        self.machine.subscribe(state.Machine.STATE_ENTERED, enterRecv)
#        self.machine.subscribe(state.Machine.STATE_EXITED, exitRecv)
#        self.machine.subscribe(state.Machine.COMPLETE, completeRecv)

#        startState = self.machine.currentState()
#        self.machine.injectEvent(self._makeEvent("Change"))
#        nextState = self.machine.currentState()

#        self.assertNotEqual(startState, nextState)
        
        # Check enter event
#        nextStateName = '%s.%s' % (nextState.__class__.__module__,
#                                   nextState.__class__.__name__)
#        eventStr = enterRecv.event.string
#        self.assertEquals(state.Machine.STATE_ENTERED, enterRecv.event.type)
#        self.assertEquals(self.machine, enterRecv.event.sender)
#        self.assertEquals(nextStateName, eventStr)
        
        # Ensure the state resolves to the proper state
#        self.assertEqual(nextState.__class__, logloader.resolve(eventStr))

        # Check exit event
#        startStateName = '%s.%s' % (startState.__class__.__module__,
#                                   startState.__class__.__name__)
#        eventStr = exitRecv.event.string
#        self.assertEquals(state.Machine.STATE_EXITED, exitRecv.event.type)
#        self.assertEquals(self.machine, exitRecv.event.sender)
#        self.assertEquals(startStateName, exitRecv.event.string)
        
        # Ensure the state resolves to the proper state
#        self.assertEqual(startState.__class__, logloader.resolve(eventStr))
        
        # Check completion event
#        self.machine.injectEvent(self._makeEvent(MockEventSource.ANOTHER_EVT))
#        self.machine.injectEvent(self._makeEvent("Start"))
        
#        self.assertEquals(state.Machine.COMPLETE, completeRecv.event.type)
#        self.assertEquals(self.machine, completeRecv.event.sender)
        
    def testDeclaredEvents(self):
        startState = self.machine.currentState()

        self.machine.injectEvent(self._makeEvent(MockEventSource.THING_UPDATED,
                                                 value = 4))
        cstate = self.machine.currentState()

        # Check to me sure we left the start state
        self.assert_(startState.exited)

        # Check to make sure we reached the proper state
        self.assertEquals(Simple, type(cstate))
        self.assert_(cstate)

        # Make sure the transition function was called
        self.assertNotEquals(None, startState.thingUpdatedEvent)
        self.assertEquals(startState.thingUpdatedEvent.value, 4)

    def testStatevars(self):
        vara = "A"
        varB = 10
        statevars = {"a" : vara, "B" : varB}
        machine = state.Machine(statevars = statevars)
        
        machine.start(Start)
        startState = machine.currentState()
        
        # Check for variables
        def testForVars():
            self.assert_(hasattr(startState, 'a'))
            self.assertEquals(vara, startState.a)
            self.assert_(hasattr(startState, 'B'))
            self.assertEquals(varB, startState.B)
        testForVars()

        # Now test with the start functionality
        varcc = [1, 2, 3]
        machine.start(Start, statevars = {'cc' : varcc})
        startState = machine.currentState()

        # Check to make sure all the old ones are still there
        testForVars()

        # Make sure we got them updated
        self.assert_(hasattr(startState, 'cc'))
        self.assertEquals(varcc, startState.cc)

        # Now restart without those vars and make sure they don't exist
        machine.start(Start)
        startState = machine.currentState()

        self.assertFalse(hasattr(startState, 'cc'))
        testForVars()

            
    def testWriteGraph(self):
        mockFile = StringIO.StringIO()
        state = Start
        self.machine.writeStateGraph(mockFile,state, ordered = True)
        output = mockFile.getvalue()
        expected = "digraph aistate {\n" + \
            "state_BranchedEnd [label=BranchedEnd,shape=doubleoctagon]\n" + \
            "state_BranchedMiddle [label=BranchedMiddle,shape=ellipse]\n" + \
            "state_BranchedState [label=BranchedState,shape=ellipse]\n" + \
            "state_End [label=End,shape=doubleoctagon]\n" + \
            "state_LoopBack [label=LoopBack,shape=ellipse]\n" + \
            "state_QueueTestState [label=QueueTestState,shape=ellipse]\n" + \
            "state_Simple [label=Simple,shape=ellipse]\n" + \
            "state_Start [label=Start,shape=ellipse]\n" + \
            "state_BranchedMiddle -> state_BranchedEnd [label=InBranchEndEvent,style=solid]\n" + \
            "state_BranchedState -> state_BranchedMiddle [label=InBranchEvent,style=solid]\n" + \
            "state_LoopBack -> state_LoopBack [label=Update,style=solid]\n" + \
            "state_QueueTestState -> state_Simple [label=ANOTHER_EVT,style=solid]\n" + \
            "state_Simple -> state_Start [label=ANOTHER_EVT,style=solid]\n" + \
            "state_Start -> state_BranchedState [label=Branch,style=dotted]\n" + \
            "state_Start -> state_End [label=Start,style=solid]\n" + \
            "state_Start -> state_LoopBack [label=LoopBack,style=solid]\n" + \
            "state_Start -> state_QueueTestState [label=ANOTHER_EVT,style=solid]\n" + \
            "state_Start -> state_Simple [label=Change,style=solid]\n" + \
            "state_Start -> state_Simple [label=THING_UPDATED,style=solid]\n" + \
            "}"

        self.assertEquals(expected,output)
    
    def testBasicBranching(self):
        # Test Branching
        self.machine.injectEvent(self._makeEvent("Branch"), 
                                 _sendToBranches = True)
        
        # Make sure we are still in the start state
        self.assertEqual(Start, type(self.machine.currentState()))

        # Ensure the branch was created properly
        self.assertEqual(1, len(self.machine.branches))
        
        # Make sure it was entered properly
        branchedMachine = self.machine.branches[BranchedState]
        branchStartState = branchedMachine.currentState()
        self.assertEqual(BranchedState, type(branchStartState))
        self.assert_(branchStartState.entered)
        self.assertEqual(False, branchStartState.exited)
        
        # Make sure branched machine doesn't impair state changes events
        self.machine.injectEvent(self._makeEvent("Change"),
                                 _sendToBranches = True)
        self.assertEqual(Simple, type(self.machine.currentState()))
        
        # Make sure events reach the branched machine
        self.machine.injectEvent(self._makeEvent("InBranchEvent"),
                                 _sendToBranches = True)
        self.assert_(branchStartState.exited)
        self.assertEqual(BranchedMiddle, type(branchedMachine.currentState()))
        
        # Make sure we are still in the proper main state machine state
        self.assertEqual(Simple, type(self.machine.currentState()))
        
    def testRepeatBranching(self):
        self.machine.injectEvent(self._makeEvent("Branch"), 
                                 _sendToBranches = True)
        
        # Make sure branching again throws an error
        self.assertRaises(Exception, self.machine.injectEvent, 
                          self._makeEvent("Branch"), _sendToBranches = True)
        
    def testBranchState(self):
        self.machine.start(state.Branch(Simple))
        
        # Make sure current state stayed
        self.assertEqual(Start, type(self.machine.currentState()))
        
        # Ensure we actually branched
        self.assertEqual(1, len(self.machine.branches))
        self.assert_(self.machine.branches.has_key(Simple))
   
    def testBranchStop(self):
        self.machine.start(state.Branch(Simple))
        branchedState = self.machine.branches[Simple].currentState()
        
        self.machine.stop()
        
        # Ensure we actually stopped the branch
        self.assertEqual(0, len(self.machine.branches))
        self.assert_(branchedState.exited)
        
        # Now test stopping just one branch
        self.machine.start(state.Branch(Simple))
        self.machine.start(state.Branch(Start))
        self.assertEqual(2, len(self.machine.branches))
        
        self.machine.stopBranch(Simple)
        self.assertEqual(1, len(self.machine.branches))
        self.assertFalse(self.machine.branches.has_key(Simple))
        
        self.machine.stopBranch(Start)
        self.assertEqual(0, len(self.machine.branches))
        self.assertFalse(self.machine.branches.has_key(Start))
        
    def testDoubleTransitions(self):
        self.machine.start(First)
        self.assertEqual(First, type(self.machine.currentState()))
        
        self.machine.injectEvent(self._makeEvent("GO", value = 1))
        self.assertEqual(Second, type(self.machine.currentState()))
        
    def testDoubleBranchTransitions(self):
        # Start us up
        self.machine.start(FirstParent, {'stateMachine' : self.machine})
        self.assertEqual(FirstParent, type(self.machine.currentState()))
        
        self.machine.injectEvent(self._makeEvent("GO", value = 1))
        self.assertEqual(SecondParent, type(self.machine.currentState()))
        
        # Make sure I branched properly
        self.assert_(self.machine.branches.has_key(First))
        branch = self.machine.branches[First]
        
        cstate = branch.currentState()
        self.assertEqual(First, type(cstate))

# --------------------------------------------------------------------------- #
#                           T E S T    S T A T E                              #
# --------------------------------------------------------------------------- #
                
# Testing of State Class
class TestState(unittest.TestCase):
    def testStartArgs(self):
        s = state.State(a = 5, bob = 'A')
        self.assertEqual(5, s.a)
        self.assertEqual('A', s.bob)

# --------------------------------------------------------------------------- #
#                             T E S T    E N D                                #
# --------------------------------------------------------------------------- #

class TestEndEnd(state.End):
    """End test state"""
    def __init__(self):
        state.End.__init__(self)
                
# Testing of End Class
class TestEnd(unittest.TestCase):
    def testinit(self):
        a = TestEndEnd()

                
if __name__ == '__main__':
    unittest.main()
