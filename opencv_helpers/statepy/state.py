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
# File:  statepy/state.py

# STD Imports
import inspect
import types

# Project Imports

class Event(object):
    """
    The action that caused a state transition, it has a type and any other
    data you wish to tag along with it.

    @type type: str
    @ivar type: The type of the event, used in the state transition tables
    """

    def __init__(self, etype = '', **kwargs):
        """
        Initialize the event with its type and associated data

        @type  etype: str
        @param etype: The type of the event, used in the state transition tables
        """
        self.type = etype

def declareEventType(name):
    """
    Defines an event type in a manner which will avoid collisions
    
    It defines it in the following format: <file>:<line> <EVENT>
    
    @note All spaces in the string will be replace with '_' 
    
    @rtype : str
    @return: The new event type
    """
    stack = inspect.stack()
    try:
        frame = stack[1][0]
        line = frame.f_lineno
        fileName = frame.f_code.co_filename
        
        # Make .py vs .pyc files have the same event names
        if fileName.endswith('.pyc'):
            fileName = fileName[:-3] + '.py'

        return '%s:%d %s' % (fileName, line, name.replace(' ', '_'))
    finally:
        del stack

class State(object):
    """
    Basic state class, its provides empty implementation for all the needed
    methods of a state
    """
    def __init__(self, **statevars):
        for name, statevar in statevars.iteritems():
            setattr(self, name, statevar)

        # TODO: check my own transition table to make sure none of the
        #       transitions are actual member functions

    @staticmethod
    def transitions():
        """
        Returns a map of eventTypes -> resulting states, loopbacks are allowed
        """
        return {}

    # TODO: Config functionality not yet ported
#    @staticmethod
#    def getattr():
#        """
#        Returns the possible config values of the state
#        """
#        return set([])

    def enter(self):
        """
        Called when the state is entered, loopbacks don't count
        """
        pass

    def exit(self):
        """
        Called when the state is exited, loopbacks don't count
        """
        pass
    
    def publish(self, eventType, event):
        """
        Publish an event, with the owning Machine object as publisher
        
        @warning: Only valid when the object is created by a Machine object
        """
        raise 
        
class End(State):
    """
    State machine which demarks a valid end point for a state machine
    
    Ensure that any "dead ends" (states with no out transitions) are actually
    intended to be that way.
    """
    def __init__(self, config = None, **kwargs):
        # TODO: config functionality not yet ported
        #State.__init__(self, config, **kwargs)
        State.__init__(self, **kwargs)

class Branch(object):
    """
    A marker class indication we branch the state machine
    """
    def __init__(self, state, branchingEvent = None):
        """
        @type state: ram.ai.state.State
        @param state: The state to branch to

        @type branchingEvent: Event
        @param branchingEvent: The event that caused the branch, if any
        """
        self.state = state
        self.branchingEvent = branchingEvent

class Machine(object):
    """
    An event based finite state machine.
    
    This machine works with graph of statepy.State classes.  This graph
    represents a state machine.  There can only be one current state at a time.
    When events are injected into the state machine the currents states 
    transition table determines which state to advance to next.
    
    @type _root: statepy.State
    @ivar _root: The first state of the Machine
    
    @type _currentState: statepy.State
    @ivar _currentState: The current state which is processing events
    
    @type _started: boolean
    @ivar _started: The Machine will not process events unless started

    @type _started: boolean
    @ivar _started: True when the Machine is complete (ie. currentState = None)
        
    @type _previousEvent: Event
    @ivar _previousEvent: The last event injected into the state machine

    @todo statevars, branches
    """
    
    STATE_ENTERED = declareEventType('STATE_ENTERED')
    STATE_EXITED = declareEventType('STATE_EXITED')
    COMPLETE = declareEventType('COMPLETE')
    
    def __init__(self, statevars = None):
        """
        The constructor for the Machine class.

        @type  statevars: dict
        @param statevars: A dictionary of the object variables given to states
        """
        
        if statevars is None:
            statevars = {}

        # Set default instance values
        self._root = None
        self._currentState = None
        self._started = False
        self._complete = False
        self._previousEvent = Event()
        self._statevars = {}
        self._startStatevars = {}
        self._branches = {}
        
        # Load up the arguments
        self._statevars = statevars
        
    def currentState(self):
        return self._currentState

    def start(self, startState, statevars = None):
        """
        Starts or branches the state machine with the given state
        
        If the given state is really a branch, it will branch to that state
        instead.

        @type  startState: State
        @param startState: The first state for the machine to enter

        @type  statevars: dict
        @param statevars: An additional dictionary of variables for the State
        """

        # Remove the previous startStatevars from our list of variables
        for key in self._startStatevars.iterkeys():
            del self._statevars[key]

        if statevars is not None:
            # Ensure there is no overlap
            currentVars = set(self._statevars.keys())
            newVars = set(statevars.keys())

            intersection = currentVars.intersection(newVars)
            if len(intersection) != 0:
                msg = "ERROR: statevars already contains: %s" % interection
                raise statepy.StatePyException(msg)
            
            self._startStatevars = statevars

            # Merge the statevars
            self._statevars.update(statevars)
        
        if Branch == type(startState):
            # Determine if we are branching
            branching = True
            self._branchToState(startState.state, startState.branchingEvent)
        else:
            self._root = startState
            self._started = True
            self._complete = False

            self._enterState(startState)

    def stop(self):
        """
        Exits the current state, and stops if from responding to any more
        events. Also stops all branches
        """
        if self._currentState is not None:
            self._exitState()
        
        self._started = False
        self._previousEvent = Event
        self._root = None
        self._currentState = None
        self._complete = False
        
        for branch in self._branches.itervalues():
            branch.stop()
        self._branches = {}
        
    def stopBranch(self, stateType):
        """
        Stops just the desired branch, and its current type
        """
        self._branches[stateType].stop()
        del self._branches[stateType]

    def injectEvent(self, rawEvent, _sendToBranches = False):
        """
        Sends an event into the state machine
        
        If currents states transition table has an entry for events of this 
        type this will cause a transition
        
        @type  event: Event or str
        @param event: A new event for the state machine to process 
        
        @type _sendToBranches: bool
        @param _sendToBranches: Use only for testing, injects events into 
                                branched state machines
        """
        # If the state we just entered transitions on same kind of event that
        # caused the transition, we can be notified again with the same event!
        # This check here prevents that event from causing an unwanted 
        # transition.
        if rawEvent == self._previousEvent:
            return

        # Make sure the event is of the right class
        if isinstance(rawEvent, Event):
            event = rawEvent
        else:
            event = Event(rawEvent)
        
        if not self._started:
            raise Exception("Machine must be started")
        
        transitionTable = self._currentState.transitions()
        nextState = transitionTable.get(event.type, None)
        if nextState is not None:
            # Determine if we are branching
            branching = False
            if Branch == type(nextState):
                branching = True
                nextState = nextState.state
                
            # Detemine if we are in a loopback
            loopback = False
            if nextState == type(self._currentState):
                loopback = True
                
            # For loops backs or branches we don't reenter, or exit from our 
            # state, just call the transition function
            leaveState = False
            if (not branching) and (not loopback):
                leaveState = True
            
            # We are leaving the current state
            currentState = self._currentState
            if leaveState:
                self._exitState()
            
            # Call the function for the transitions
            transFunc = self._getTransitionFunc(event.type, currentState)
            if transFunc is not None:
                transFunc(event)

            # Notify that we are entering the next state
            if (not loopback) and (not branching):
                # Create an instance of the next state's class
                self._enterState(nextState)
            elif branching:
                self._branchToState(nextState, branchingEvent = event)
                
        # Record previous event
        self._previousEvent = event
        
        if _sendToBranches:
            for branch in self._branches.itervalues():
                branch.injectEvent(event)

    @property
    def complete(self):
        """Returns true when """
        return self._complete

    def _enterState(self, newStateClass):
        """
        Does all the house keeping when entering a new state
        """
        
        # CONFIG LOOKUP USE TO HAPPEN HERE
        
        # Create state instance from class, make sure to pass all subsystems
        # along as well
        newState = newStateClass(**self._statevars)
        
        # Subscribe to every event of the desired type
        # <EVENT SUBSCRIBTION USE TO HAPPEN HERE>
        transitionTable = newState.transitions()
        
        # Actual enter the state and record it as our new current state
        self._currentState = newState
        self._currentState.enter()
        
        # Notify everyone we just entered the state
        #fullClassName = '%s.%s' % (self._currentState.__class__.__module__, 
        #                           self._currentState.__class__.__name__)
        # NOTIFY STATE BEING ENTERED
        
        # If we are in a state with no way out, exit the state and mark ourself
        # complete
        if 0 == len(transitionTable):
            self._exitState()
            self._complete = True
            # NOTIFY MACHINE BEING COMPLETE
        
    def _exitState(self):
        """
        Does all the house keeping for when you are exiting an old state
        """
        self._currentState.exit()
                
        # NOTIFY STATE BEING EXIT
        #fullClassName = '%s.%s' % (self._currentState.__class__.__module__, 
        #                           self._currentState.__class__.__name__)
        
        self._currentState = None

    def _branchToState(self, nextState, branchingEvent = None):
        if self._branches.has_key(nextState):
            raise Exception("Already branched to this state")
        
        # Create new state machine
        branchedMachine = Machine(self._statevars)

        # Start it up with the proper state
        branchedMachine.start(nextState)

        # Set the previous state to avoid unwanted transitions caused by
        # the event that led us hear, triggering a transition in the newly
        # created state machine
        branchedMachine._previousEvent = branchingEvent

        # Store new state machine
        self._branches[nextState] = branchedMachine

    def _getTransitionFunc(self, etype, obj):
        """
        Determines which funtion during a transistaion between states
        
        This uses the event type of the event which caused the transition to
        determine which member funtion of the self._currentState to call.
        """
        # Trim etype of namespace stuff
        etype = etype.split(' ')[-1]
        
        # Grab all member functions
        members = inspect.getmembers(obj, inspect.ismethod)

        # See if we have a matching method
        matches = [func for name,func in members if name == etype]

        # We found it
        assert len(matches) < 2
        if len(matches) > 0:
            return matches[0]

    @property
    def branches(self):
        return self._branches

    @staticmethod
    def writeStateGraph(fileobj, startState, ordered = False, noLoops = False):
        """
        Write the graph of the state machine starting at the given state to
        the fileobj.
    
        @type  fileobj: a file like object
        @param fileobj: The object to write the result graph to (ie:
                        fileobject.write(graphtext))
       
        @type  startState: ram.ai.state.State
        @param startState: The state to start the graph at
        
        @type  ordered: boolean
        @param ordered: Whether or not to alphabetize the states
        """
        fileobj.write("digraph aistate {\n")
        stateTransitionList = []
        traversedStates = []
        
        Machine._traverse(startState, stateTransitionList, traversedStates,
                          noLoops)
        
        # Sort list for determinism
        if ordered:
            stateTransitionList.sort()

        # Output Labels in Simple format        
        traversedStates.sort(key = Machine._dottedName)
        for state in traversedStates:
            fullName = Machine._dottedName(state)
            shortName = state.__name__
            # Shape denots "end" states with a "Stop Sign" type shape
            shape = 'ellipse'
            if 0 == len(state.transitions()):
                shape = 'doubleoctagon'
            fileobj.write('%s [label=%s,shape=%s]\n' % \
                          (fullName, shortName, shape))

        for item in stateTransitionList:
            fileobj.write(item + "\n")
        fileobj.write("}")
        fileobj.flush() # Push data to file
        
    @staticmethod
    def _traverse(currentState,stateList,traversedList,noLoops=False):
        if 0 == len(currentState.transitions()):
            if not currentState in traversedList:
                    traversedList.append(currentState)
        else:
            for aiEvent,aiState in currentState.transitions().iteritems():
                eventName = str(aiEvent).split(' ')[-1]
                
                # Style is determine whether or not we are branching
                style = "solid"
                if type(aiState) is Branch:
                    style = "dotted"
                    aiState = aiState.state
                
                # Determine state names
                startName = Machine._dottedName(currentState)
                endName = Machine._dottedName(aiState)

                if (not noLoops) or (startName != endName):
                    strStruct = "%s -> %s [label=%s,style=%s]" % \
                        (startName, endName, eventName, style)
                    stateList.append(strStruct)
                    if not currentState in traversedList:
                        traversedList.append(currentState)

                    # Don't recuse on a state we have already seen
                    if not aiState in traversedList:
                        Machine._traverse(aiState, stateList,
                                          traversedList, noLoops)
    @staticmethod
    def _dottedName(cls):
        return cls.__module__.replace('.','_') + '_' + cls.__name__
