#!/usr/bin/env python

from setuptools import setup

setup(
      name='TrAPS',
      version='1.0',
      description='Transmission, Absorption and Photoluminescence Spectrometry Data Collector',
      author='Sam Wright',
      author_email='samuel.wright314@gmail.com',
      url='http://samwright.github.io',
      packages=['TrAPS'],
      scripts=['TrAPS.py','TempCalibrator.py'],
      
      install_requires = [
                  'numexpr',
                  'scipy',
                  'numpy',
                  'matplotlib',
                  'xlwt',
                  ],
     )
