from setuptools import setup, find_packages
import sys, os

version = '0.1.0'

setup(name='tenyksclient',
      version=version,
      description="A client base for Tenyks IRC bot",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='ircbot baseclient tenyks',
      author='Kyle Terry',
      author_email='kyle@kyleterry.com',
      url='https://github.com/kyleterry/tenyksclient',
      license='GPL V2',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'clint',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
