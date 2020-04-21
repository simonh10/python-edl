#!/usr/bin/env python

from distutils.core import setup
exec(open('edl/version.py').read())

requires = [
    'timecode'
]

setup(
    name='edl',
    version=__version__,
    description='Simple EDL reading library',
    author='Simon Hargreaves',
    author_email='simon@simon-hargreaves.com',
    url='http://www.simon-hargreaves.com/python-edl',
    packages=['edl'],
    classifiers=[
       'Development Status :: 3 - Alpha',
       'Environment :: Console',
       'Intended Audience :: Developers',
       'License :: OSI Approved :: MIT License',
       'Operating System :: MacOS :: MacOS X',
       'Operating System :: Microsoft :: Windows',
       'Operating System :: POSIX',
       'Programming Language :: Python',
       'Natural Language :: English',
       'Topic :: Multimedia :: Video',
       'Topic :: Software Development :: Libraries'
    ],
    install_requires=requires,
)
