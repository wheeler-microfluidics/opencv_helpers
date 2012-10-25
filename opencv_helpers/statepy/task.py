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
# File:  statepy/task.py

# STD Imports

# Project Imports
import statepy
import statepy.state as state

# Special event that denotes 
TIMEOUT = state.declareEventType('TIMEOUT')        

class Next(state.State):
    """
    Special state denotes that the next task should be moved to
    """
    pass

class Failure(state.State):
    """
    Special state denotes that the task failed in an *unrecoverable* way.
    """
    pass

class End(state.State):
    """
    Special state that denotes the complete end of the state machine
    """
    pass

class TaskManager(state.State):
    """
    Basic implementation of a task manager which provides the next task
    in a list of tasks.  This can be replaced by any kind system you want,
    including one that provides dynamic ordering, unlike the fixed upon
    contruction order provided here.
    """
    def __init__(self, taskOrder, failureTasks = None):
        """
        @type  taskOrder: [statepy.task.Task]
        @param taskOrder: An ordered list of tasks.

        @type  failureTasks: {statepy.state.Task : statepy.state.State}
        @param failureTasks: Maps a task to the state you go into upon failure
        """

        # Build list of next states
        self._nextTaskMap = {}
        self._taskOrder = []

        for i, taskClass  in enumerate(taskOrder):
            # Determine which task is really next
            nextTaskClass = End
            if i != (len(taskOrder) - 1):
                nextTaskClass = taskOrder[i + 1]
            
            # Store the results
            self._nextTaskMap[taskClass] = nextTaskClass
            
            # Record the current class
            self._taskOrder.append(taskClass)
            
        # Build list of failure tasks
        self._failureTaskMap = {}
        if failureTasks is not None:
            self._failureTaskMap = failureTasks

    def getNextTask(self, task):
        """
        Returns the task which will be transitioned to when the given task 
        transitions to the next task. Denoted by task.Next state in the current
        Task's transition table.
        """
        return self._nextTaskMap[task]
    
    def getFailureState(self, task):
        """
        Returns the state which will be transitioned to when the given task
        fails in an unrecoverable way.  Recoverable failure are handled 
        internally by that task. 
        """
        return self._failureTaskMap.get(task, None)

    
# NOTE: Timeout and Events not in stand alone StatePy so sections disabled

class Task(state.State):
    """
    Encapsulates a single AI task, like completing an objective.  It allows for
    the implementation and testing of such tasks without concern for what comes
    before, or after said task.

    It expects a 'taskManager' which provides 'getNextTask' and
    'getFailureState' methods.  These all the Task to setup its transition
    table at runtime based upon the desired task ordering.
    """

    # Change me if you wish to have the task manager called something different
    TASK_MANAGER_NAME = "taskManager"
    
    def __init__(self, **statevars):
        # Call the super class
        state.State.__init__(self, **statevars)

        # Ensure that we have a task manager present
        if not statevars.has_key(Task.TASK_MANAGER_NAME):
            msg = 'No TaskManager of name "%s" provided to Task State' % Task.TASK_MANAGER_NAME
            raise statepy.StatePyException(msg)
        
        # Dynamically create our event
        #self._timeoutEvent = core.declareEventType(
        #    'TIMEOUT_' + self.__class__.__name__)
        
        # From the AI grab our next task
        self._taskManager = statevars[Task.TASK_MANAGER_NAME]
        self._nextState = self._taskManager.getNextTask(type(self))
        self._failureState = self._taskManager.getFailureState(type(self))
    
        # Timeout related values, set later on
        #self._hasTimeout = False
        #self._timeoutDuration = None
        #self._timer = None
    
    #@property
    #def timeoutEvent(self):
    #    return self._timeoutEvent
    
    #@property
    #def timeoutDuration(self):
    #    return self._timeoutDuration
        
    def transitions(self):
        """
        A dynamic transition function which allows you to wire together a 
        missions dynamically.
        """
        baseTrans = self._transitions()
        newTrans = {}
        for eventType, nextState in baseTrans.iteritems():
            # Catch the timeout event and replace with our class specific 
            # timeout event type
            #if eventType == TIMEOUT:
            #    eventType = self._timeoutEvent
            #    self._hasTimeout = True
            
            if nextState == Next:
                # If the next state is the special Next marker state, swap it 
                # out for the real next state
                nextState = self._nextState
            elif nextState == Failure:
                # If that state is the special failure marker state, swap it 
                # out for the real failure state
                if self._failureState is None:
                    raise "ERROR: transition to non existent failure state"
                nextState = self._failureState
            
            # Store the event
            newTrans[eventType] = nextState
            
        return newTrans

#    @staticmethod
#    def getattr():
#        return set(['timeout'])
    
#    def enter(self, defaultTimeout = None):
#        if self._hasTimeout:
            # Get timeout duration from configuration file
#            if defaultTimeout is None:
#                self._timeoutDuration = self._config['timeout']
#            else:
#                self._timeoutDuration = self._config.get('timeout', 
#                                                          defaultTimeout)
            # Start our actual timeout timer
#            self._timer = self.timerManager.newTimer(self._timeoutEvent, 
#                                                    self._timeoutDuration)
#            self._timer.start()
            
#    def exit(self):
#        if self._timer is not None:
#            self._timer.stop()
