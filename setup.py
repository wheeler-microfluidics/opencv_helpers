#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import sys
sys.path.insert(0, '.')
import version


setup(name="opencv_helpers",
      version=version.getVersion(),
      description='Helper functions for opencv',
      author="Christian Fobel",
      author_email="christian@fobel.net",
      url="https://github.com/cfobel/python___opencv_examples",
      license="GPLv2 License",
      packages=['opencv_helpers'],
      package_data={'opencv_helpers': ['statepy/*.py', 'statepy/test/*',
                                       'cvwin/*', 'glade/*']})
