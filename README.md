ChemTools-WebApp
================
A Django webapp built around the functionality of [chemtools [DEPRECATED]](https://github.com/crcollins/chemtools). This includes various utilities to parse Gaussian log files, create benzobisazole structures, submit jobs to Torque clusters, and predict optoelectronic properties of benzobisazoles using machine learning.

[Here is a demo site.](http://gauss.crcollins.com/)


Deploy
------

This setup assumes you are on a machine with the apt package manager. This will proceed to install the required dependencies and setup an nginx server to serve chemtools. Once this is done, you should be able to see it in your browser at http://localhost/.

    $ cd chemtools-webapp
    $ source install.sh

To remove chemtools, run the following commands.

    $ cd chemtools-webapp
    $ source install.sh remove


Vagrant Deploy
--------------

This assumes that you already have vagrant and virtualbox installed.

    $ cd chemtools-webapp/vagrant
    $ vagrant up
    # Warning: This includes the test key from project/media/tests by default. This key MUST be removed if you plan on opening this server up to the internet. If you want to change the port, just change the value in the vagrant/Vagrantfile and reboot the vm.
    Go to http://localhost:4567/

To spin up a vm from the local copy of chemtools-webapp can set the environmental variable `DEV` to `true`

    $ DEV=true vagrant up


Development Setup
-----------------

There are two ways to get a dev setup, either you can do a vagrant deployment, or you can run the install.sh script with the `dev` option.

    $ cd chemtools-webapp
    $ source install.sh dev
    $ python manage.py runserver 0.0.0.0:8000
    Go to http://localhost:8000/


Test
----

Currently, there are a few tests as a sanity check for some of the main features of chemtools. You can run them with the following command. Note: For some of the tests to pass they require a test Torque Cluster. This requirement can be satisfied using [this](https://github.com/crcollins/torquecluster) repository which contains a Vagrant setup of a basic cluster. NOTE: These tests also assume that the test cluster is at localhost port 2222.

    $ python manage.py test account chem chemtools cluster data docs

If you have coverage.py installed, you can also run the following commands to see which parts of the code are covered by the tests.

    $ coverage run manage.py test account chem chemtools cluster data docs
    $ coverage html


Database
--------

The database used can be changed in by going in project/settings.py and changing the DATABASE dictionary.
