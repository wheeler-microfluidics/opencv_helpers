## {{{ http://code.activestate.com/recipes/577564/ (r2)
import os
import sys
from StringIO import StringIO
from tempfile import NamedTemporaryFile, mkstemp

from path import path

class Silence:
    """Context manager which uses low-level file descriptors to suppress
    output to stdout/stderr, optionally redirecting to the named file(s).
    
    >>> import sys, numpy.f2py
    >>> # build a test fortran extension module with F2PY
    ...
    >>> with open('hellofortran.f', 'w') as f:
    ...     f.write('''\
    ...       integer function foo (n)
    ...           integer n
    ...           print *, "Hello from Fortran!"
    ...           print *, "n = ", n
    ...           foo = n
    ...       end
    ...       ''')
    ...
    >>> sys.argv = ['f2py', '-c', '-m', 'hellofortran', 'hellofortran.f']
    >>> with Silence():
    ...     # assuming this succeeds, since output is suppressed
    ...     numpy.f2py.main()
    ...
    >>> import hellofortran
    >>> foo = hellofortran.foo(1)
     Hello from Fortran!
     n =  1
    >>> print "Before silence"
    Before silence
    >>> with Silence(stdout='output.txt', mode='w'):
    ...     print "Hello from Python!"
    ...     bar = hellofortran.foo(2)
    ...     with Silence():
    ...         print "This will fall on deaf ears"
    ...         baz = hellofortran.foo(3)
    ...     print "Goodbye from Python!"
    ...
    ...
    >>> print "After silence"
    After silence
    >>> # ... do some other stuff ...
    ...
    >>> with Silence(stderr='output.txt', mode='a'):
    ...     # appending to existing file
    ...     print >> sys.stderr, "Hello from stderr"
    ...     print "Stdout redirected to os.devnull"
    ...
    ...
    >>> # check the redirected output
    ...
    >>> with open('output.txt', 'r') as f:
    ...     print "=== contents of 'output.txt' ==="
    ...     print f.read()
    ...     print "================================"
    ...
    === contents of 'output.txt' ===
    Hello from Python!
     Hello from Fortran!
     n =  2
    Goodbye from Python!
    Hello from stderr
    
    ================================
    >>> foo, bar, baz
    (1, 2, 3)
    >>>

    """
    def __init__(self, stdout=os.devnull, stderr=os.devnull, mode='w'):
        self.outfiles = stdout, stderr
        self.combine = (stdout == stderr)
        self.mode = mode
        self.files = self.outfiles
        self.temp_files = [None, None]
        self.string_io = [isinstance(f, StringIO) for f in self.outfiles]
        
    def __enter__(self):
        #self.sys = sys
        # save previous stdout/stderr
        self.saved_streams = saved_streams = sys.__stdout__, sys.__stderr__
        self.fds = fds = [s.fileno() for s in saved_streams]
        self.saved_fds = map(os.dup, fds)
        # flush any pending output
        for s in saved_streams: s.flush()

        files = list(self.files)
        for i, s in enumerate(self.string_io):
            if s:
                # This file is actually a StringIO.  We need to create a temp
                # file to write output to, which we can later copy back to
                # the StringIO object.
                fd, file_path = mkstemp()
                os.close(fd)
                self.temp_files[i] = path(file_path)
                files[i] = self.temp_files[i]
        self.files = tuple(files)

        # open surrogate files
        if self.combine: 
            null_streams = [open(self.files[0], self.mode, 0)] * 2
            if self.files[0] != os.devnull:
                #sys.stdout, sys.stderr = map(os.fdopen, fds, ['w']*2, [0]*2)
                # Christian Fobel: leave sys.stdout/err alone, since it
                # causes the interpreter to exit immediately following
                # __exit__().
                pass
        else:
            null_streams = [open(f, self.mode, 0) for f in self.files]
        self.null_fds = null_fds = [s.fileno() for s in null_streams]
        self.null_streams = null_streams
        
        # overwrite file objects and low-level file descriptors
        map(os.dup2, null_fds, fds)

    def __exit__(self, *args):
        #sys = self.sys
        # flush any pending output
        for s in self.saved_streams: s.flush()
        # restore original streams and file descriptors
        map(os.dup2, self.saved_fds, self.fds)
        map(os.close, self.saved_fds)
        sys.stdout, sys.stderr = self.saved_streams
        # clean up
        for s in self.null_streams: s.close()
        for i, f in enumerate(self.temp_files):
            # Write contents from temp files into respective StringIO objects.
            if f:
                if self.string_io[i]:
                    # Note that this should always be True, but we'll check to
                    # make sure.
                    self.outfiles[i].write(f.bytes())
                # Delete temp file.
                f.remove()
        return False
## end of http://code.activestate.com/recipes/577564/ }}}
