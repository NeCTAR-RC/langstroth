from setuptools import setup, find_packages
from pip.req import parse_requirements
import uuid


session = uuid.uuid1()
version = '0.1'
requirements = parse_requirements("requirements.txt", session=session)


setup(name='langstroth',
      version=version,
      description="Status page for the NeCTAR Research Cloud.",
      long_description="""\
""",
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: '
          + 'GNU General Public License v3 or later (GPLv3+)',
          'Natural Language :: English',
          "Programming Language :: Python :: 2",
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4'],
      keywords='',
      author='NeCTAR',
      author_email='',
      url='',
      license='GPLv3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[str(r.req) for r in requirements])
