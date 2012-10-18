#!/usr/bin/env python

import distutils.core

try:
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    from distutils.command.build_py import build_py

# Setup script for path

kw = {
    'name': "opencv",
    'version': "1.0",
    'description': 'Helper functions for opencv',
    'author': "Christian Fobel",
    'author_email': "christian@fobel.net",
    'url': "https://github.com/cfobel/python___opencv_examples",
    'license': "GPLv2 License",
    'packages': ['opencv'],
    'cmdclass': dict(build_py=build_py),
    'package_data': {'opencv': ['statepy/*.py', 'statepy/test/*', 'cvwin/*',
                                'glade/*']}
}


# If we're running Python 2.3, add extra information
if hasattr(distutils.core, 'setup_keywords'):
    if 'classifiers' in distutils.core.setup_keywords:
        kw['classifiers'] = [
            'Development Status :: 4 - Beta',
            'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
            'Intended Audience :: Developers',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Software Development :: Libraries :: Python Modules'
          ]
    if 'download_url' in distutils.core.setup_keywords:
        urlfmt = "https://github.com/cfobel/python___opencv_examples/tarball/%s"
        kw['download_url'] = urlfmt % kw['version']


distutils.core.setup(**kw)
