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
# File:  statepy/test/test.py


"""
Finds and runs all tests
"""

# STD Imports
import os
import sys
import imp
import unittest

# Project Imports
import statepy.test

def importFromPath(path):
    testDir = os.path.dirname(statepy.test.__file__)
    
    # Import Test Module
    (search_path, name) = os.path.split(path)

    # Stip '.py' from the end
    name = name[:-3]
    (f, pathname, decs) = imp.find_module(name, [search_path])
    
    try:
        return imp.load_module(name, f, pathname, decs)
    except ImportError,e:
        print 'Could import %s: '% path.replace(testDir, ''),
        print '\t',e
    
    return None

def main(argv = None):
    if argv is None:
        argv = sys.argv
        
    testLoader = unittest.TestLoader()
    suite = unittest.TestSuite()   
    testDir = os.path.dirname(statepy.test.__file__)
    
    # Recursively walk the path 
    for root, dirs, files in os.walk(testDir):
        # Only take *.py files in add the directory
        pathes = [os.path.join(root,f) for f in files 
                  if f.endswith('.py') and not f.startswith('.')]

        # Remove __init__ files
        pathes = [p for p in pathes if 0 == p.count('__init__')]

        for path in pathes:
            mod = importFromPath(path)

            if mod is not None:
                print 'Gathering From: ',path.replace(testDir,'')
                suite.addTest(testLoader.loadTestsFromModule(mod))
        
        # don't visit SVN directories    
        if '.svn' in dirs:
            dirs.remove('.svn')  
        
    # Run the tests
    print '\nRunning Tests:'
    result = unittest.TextTestRunner().run(suite)

    if not result.wasSuccessful():
        return 1 # Failure
    
    return 0
        
if __name__ == '__main__':
    sys.exit(main())
