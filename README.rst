Langstroth
==========

Langstroth is the status page for the NeCTAR Research Cloud.


Run the code
------------

You probably want a source install so run ::

  git clone git@github.com:NeCTAR-RC/langstroth.git
  cd langstroth
  pip install -e .


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
  
Langstroth requirements notes on on MacOS X
----------------
sudo pip install requests
sudo pip install cssselect
sudo pip install python-dateutil

This will not work on MacOS X:
sudo pip install lxml
 
So make sure to run: 
xcode-select --install
to update the XCode command line tools after a Mavericks upgrade.
And then run:
STATIC_DEPS=true sudo pip install lxml