from setuptools import setup, find_packages
from os import path

version = '0.1'

setup(name='langstroth',
      version=version,
      description="Status page for the NeCTAR Research Cloud.",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='NeCTAR',
      author_email='',
      url='',
      license='GPLv3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=open(path.join(path.dirname(__file__), 'requirements.txt')).readlines(),
      test_requires=[
          # -*- Extra requirements: -*-
          'mox',
          'mock',
      ],
      )
