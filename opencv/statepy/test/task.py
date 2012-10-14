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
# File:  statepy/test/task.py

# Python Imports
import unittest

# Project Imports
import statepy.state as state
import statepy.task as task

EVENT_A = state.declareEventType('A')
EVENT_B = state.declareEventType('B')
EVENT_C = state.declareEventType('C')
EVENT_D = state.declareEventType('D')
EVENT_E = state.declareEventType('E')
EVENT_F = state.declareEventType('F')

EVENT_B_FAIL = state.declareEventType('B_FAIL')
EVENT_C_FAIL = state.declareEventType('C_FAIL')

class TaskA(task.Task):
    #DEFAULT_TIMEOUT = 16
    @staticmethod
    def _transitions():
        return {EVENT_A : task.Next,
                EVENT_B : task.Next,
                task.TIMEOUT : task.Next }
        
    def enter(self):
        #task.Task.enter(self, TaskA.DEFAULT_TIMEOUT)
        pass

class TaskB(task.Task):
    @staticmethod
    def _transitions():
        return {EVENT_C : task.Next,
                EVENT_D : task.Next,
                EVENT_B_FAIL : task.Failure,
                task.TIMEOUT : task.Next }

class TaskC(task.Task):
    @staticmethod
    def _transitions():
        return {EVENT_E : task.Next,
                EVENT_F : task.Next,
                EVENT_C_FAIL : task.Failure }

class BRecovery(state.State):
    """Test state just used to know we went to the proper failure state"""
    @staticmethod
    def transitions():
        return {EVENT_F : BRecovery }
    
class CRecovery(state.State):
    """Test state just used to know we went to the proper failure state"""
    @staticmethod
    def transitions():
        return {EVENT_F : CRecovery }

class TestTask(unittest.TestCase):
    #CFG_TIMEOUT = 47
    
    def setUp(self):
        taskOrder = [TaskA, TaskB, TaskC]
        failureTasks = {TaskB : BRecovery, TaskC : CRecovery }

        # Create our task manager which tells the current state what the next
        # state is
        self.taskManager = task.TaskManager(taskOrder = taskOrder,
                                       failureTasks = failureTasks)

        # Now create our state machine, making sure to pass along the
        # taskManager so that Task state have access to it
        self.machine = state.Machine(
            statevars = {'taskManager' : self.taskManager})

        # These are set as object variables for historical reasons
        self.TaskAcls = TaskA
        self.TaskBcls = TaskB
        self.TaskCcls = TaskC
        self.BRecoverycls = BRecovery
        self.CRecoverycls = CRecovery
        
    def testNextTransitions(self):
        """
        Make sure the marking "task.Next" states get replaced with the real 
        next states.
        """
        
        taskA = self.TaskAcls(taskManager = self.taskManager)
        self.assertEqual(self.TaskBcls, taskA.transitions()[EVENT_A])
        self.assertEqual(self.TaskBcls, taskA.transitions()[EVENT_B])
        taskB = self.TaskBcls(taskManager = self.taskManager)
        self.assertEqual(self.TaskCcls, taskB.transitions()[EVENT_C])
        self.assertEqual(self.TaskCcls, taskB.transitions()[EVENT_D])
        taskC = self.TaskCcls(taskManager = self.taskManager)
        self.assertEqual(task.End, taskC.transitions()[EVENT_E])
        self.assertEqual(task.End, taskC.transitions()[EVENT_F])
        
    def _injectEvent(self, etype):
        event = state.Event()
        event.type = etype
        self.machine.injectEvent(event)
        
    def testTransition(self):
        """
        Now make sure the whole thing works in a real statemachine
        """
        # Start up in the TaskA state
        self.machine.start(self.TaskAcls)
        
        # Now inject events to move us from the start to the end
        self._injectEvent(EVENT_A)
        cstate = self.machine.currentState()
        self.assertEquals(self.TaskBcls, type(cstate))
        
        self._injectEvent(EVENT_D)
        cstate = self.machine.currentState()
        self.assertEquals(self.TaskCcls, type(cstate))
        
        self._injectEvent(EVENT_E)
        self.assert_(self.machine.complete)
    
        # Now do the failure tasks
        self.machine.start(self.TaskBcls)
        self._injectEvent(EVENT_B_FAIL)
        self.assertEquals(self.BRecoverycls, type(self.machine.currentState()))
        
        self.machine.start(self.TaskCcls)
        self._injectEvent(EVENT_C_FAIL)
        self.assertEquals(self.CRecoverycls, type(self.machine.currentState()))
        
#    def testDefaultTimeout(self):
#        """
#        Tests normal timeout procedure
#        """
#        self._timeoutTest(self.TaskAcls, self.TaskBcls, TaskA.DEFAULT_TIMEOUT)
        
#    def testCfgTimeout(self):
#        """
#        Tests to make sure the timeout value was read from the cfg properly
#        """
#        self._timeoutTest(self.TaskBcls, self.TaskCcls, TestTask.CFG_TIMEOUT)
    
#    def testStopTimer(self):
#        """
#        Tests to make sure the time doesn't fire when the state exits
#        """
        # Register for the timer
#        self._timerFired = False
#        def timerHandler(event):
#            self._timerFired = True
#        self.eventHub.subscribeToType(self.TaskAcls(taskManager = self.taskManager).timeoutEvent,
#                                      timerHandler)
        
        # Start up and make sure we are in the proper state
#        self.machine.start(self.TaskAcls)
#        startState = self.machine.currentState()
#        self.assertEquals(self.TaskAcls, type(startState))
        
        # Move to the next state
#        self._injectEvent(EVENT_A)
#        cstate = self.machine.currentState()
#        self.assertEquals(self.TaskBcls, type(cstate))
        
        # Release the timer and make sure it *wasn't* called
#        self.releaseTimer(startState.timeoutEvent)
#        self.assertEqual(False, self._timerFired)
        
    
#    def _timeoutTest(self, startState, expectedEndState, expectedTimeout):
#        """
#        Helper function for testing whether or not the timeout timer works
#        """
        # Start up and make sure we are in the proper state
#        self.machine.start(startState)
#        cstate = self.machine.currentState()
#        self.assertEquals(startState, type(cstate))
        
        # Ensure that the time was read correctly
#        self.assertEqual(expectedTimeout, cstate.timeoutDuration)
        
        # Release timer and make sure we are in the right state
#        self.releaseTimer(cstate.timeoutEvent)
#        cstate = self.machine.currentState()
#        self.assertEquals(expectedEndState, type(cstate))
