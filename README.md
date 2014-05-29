ChemTools-WebApp
================
A Django webapp built around the functionality of [chemtools [DEPRECATED]](https://github.com/crcollins/chemtools). This includes various utilities to parse Gaussian log files, creating benzobisazole structures, submitting jobs to Torque clusters, and predicting optoelectronic properties of benzobisazoles using machine learning.

[Here is a demo site.](http://gauss.crcollins.com/)


Setup
-----

This setup assumes you are on a machine with the apt package manager.

    $ sudo apt-get install git
    $ git clone https://github.com/crcollins/chemtools-webapp
    $ cd chemtools-webapp
    $ source install.sh


Test
----

Currently, there are a few tests as a sanity check for some of the main features of chemtools. You can run them with the following command. Note: For some of the tests to pass they require a test Torque Cluster. This requirement can be satisfied using [this](https://github.com/crcollins/torquecluster) repository which contains a Vagrant setup of a basic cluster. NOTE: These tests also assume that the test cluster is at localhost port 2222.

    $ python manage.py test account chem chemtools cluster data parse docs


Database
--------

The database used can be changed in by going in project/settings.py and changing the DATABASE dictionary.


Vagrant Deploy
--------------

This assumes that you already have vagrant and virtualbox installed.

    $ cd chemtools-webapp/vagrant
    $ vagrant up
    # Warning: This includes the test key from project/media/tests by default. This key MUST be removed before opening this server up to the internet.
    Go to http://localhost:4567/


