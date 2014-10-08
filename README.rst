Langstroth
==========

Langstroth is the status page for the NeCTAR Research Cloud.


Run the code
------------

You probably want a source install so run ::

  git clone git@github.com:NeCTAR-RC/langstroth.git
  cd langstroth
  pip install -e .

First run
---------

For initial demonstration purposes navigate into the top-level Langstroth directory and execute::

  ./manage.py syncdb
  ./manage.py syncdb --database allocations_db
  ./manage.py runserver

For production purposes the allocations table (allocations_db) will already exist.
The settings file will need to be adjusted to reference this database
and the reference data file.

Once these adjustments have been made execute the scripts to load the reference data::

  ./manage.py syncdb
  ./manage.py syncdb --database allocations_db
  ./manage.py runserver

Contributing
------------

Code review happens on the Research Cloud Gerrit server:

https://review.rc.nectar.org.au/

The workflow for change submission is like this::

  git clone git@github.com:NeCTAR-RC/langstroth.git
  cd langstroth
  <<make your changes>>
  git add newthing.py
  git commit -m "Added a new thing"
  git-review      # https://pypi.python.org/pypi/git-review

Langstroth requirements notes on MacOS X
-------------------------------------------

The commands to execute are::

  sudo pip install requests
  sudo pip install cssselect
  sudo pip install python-dateutil

This will not work on MacOS X::

  sudo pip install lxml

To update the XCode command line tools after a Mavericks upgrade run::

  xcode-select --install

And then run::

  STATIC_DEPS=true sudo pip install lxml
    
Eclipse Tools
-------------

To support execution, debugging, testing and QA within Eclipse
install PyDev <http://pydev.org/>
and the JSJint Eclipse plugin <http://github.eclipsesource.com/jshint-eclipse/>.
To use the Py.test test runner the supporting pytest Python module
needs to be installed as follows:

  sudo pip install -U pytest pytest-django

Command Line Tools
------------------

Python tools required for testing via the command line are installed as follows::

  sudo pip install tox
