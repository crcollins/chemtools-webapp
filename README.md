ChemTools-WebApp
================
A Django webapp built around the functionality of chemtools.


_______________________________________________________________________
Build/Run Requirements
----------------------

- Python 2.7+
- Django 1.4.1
- Misaka 1.0.2
- Matplotlib 1.1.1rc
- Numpy 1.6.1
- Paramiko 1.7.7.1
- Pillow 2.2.1
- PyCrypto 2.26
- Scipy 0.9.0
- Django bootstrap form 3.0.0



Setup
-----

This setup assumes that you already have python 2.7+ and git installed and are on a machine with the apt package manager.

    $ sudo apt-get install python-dev gfortran liblapack-dev libatlas-dev build-essential libfreetype6-dev libpng-dev python-cairo python-pip
    $ sudo pip install virtualenv
    $ virtualenv project
    $ cd project/
    $ . bin/activate
    $ ln -s /usr/lib/python2.7/dist-packages/cairo/ lib/python2.7/site-packages/

    $ git clone https://github.com/crcollins/chemtools-webapp.git
    $ cd chemtools-webapp
    $ pip install -r requirements.txt
    $ python manage.py syncdb
    $ python manage.py runserver 0.0.0.0
    Go to http://localhost/ with your browser

Note: You might have to run `sudo pip install numpy==1.6.1` before running `sudo pip install -r requirements.txt` to get it to work.


Test
----

Currently, there are a few tests as a sanity check for some of the main features of chemtools. You can run them with the following command.

    $ python manage.py test account chem chemtools cluster data parse docs


Database
--------

The database used can be changed in by going in project/settings.py and changing the DATABASE dictionary.