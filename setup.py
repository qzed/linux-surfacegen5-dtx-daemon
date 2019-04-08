#!/usr/bin/env python
from distutils.core import setup


setup(
    name='surface_dtx',
    version='0.1.5',
    packages=['surface_dtx'],
    package_dir={'surface_dtx': 'dtx'},
    requires=['dbus', 'toml'],
)
