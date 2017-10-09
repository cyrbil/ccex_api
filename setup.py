#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

"""
           DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                    Version 2, December 2004

 Copyright (C) 2004 Sam Hocevar <sam@hocevar.net>

 Everyone is permitted to copy and distribute verbatim or modified
 copies of this license document, and changing it is allowed as long
 as the name is changed.

            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

  0. You just DO WHAT THE FUCK YOU WANT TO.
"""

import os
from distutils.core import setup


here = os.path.abspath(os.path.dirname(__file__))
with open('README.md') as f:
    readme = f.read().encode('utf-8')


setup(
    name='ccex_api',
    version='1.0.5',
    description='Python 2.6/3.4+ Client for the CCex API.',
    long_description=readme,
    author='Cyril DEMINGEON',
    author_email='me@cyrbil.fr',
    url='https://github.com/cyrbil/ccex_api',
    packages=['ccex_api'],
    package_dir={'ccex_api': 'ccex_api'},
    license='DWTFYWT PUBLIC LICENSE',
    requires=['requests'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ]
)
