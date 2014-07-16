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

In addition to the parameter given to install.sh, there are also three environment variables that get used. They are `INSTALL_USER`, `CHEMTOOLS_DIR`, and `HTTPS`. `INSTALL_USER` is used to set the user that chemtools will install with (if no value is given this will default to `USER`). , `CHEMTOOLS_DIR` sets the path where chemtools is located (by default this is set to be the current directory). `HTTPS` specifices whether or not to use the https nginx config or not. This defaults to the regular nginx config. By giving `HTTPS` any non null value it will use the https configuration.


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

To run the test server with ssl, you can run the following command:

    $ python manage.py runsslserver\
        --key=project/media/tests/server.key\
        --certificate=project/media/tests/server.crt 0.0.0.0:8000
    Go to https://localhost:8000/

If you want to get rid of the warning message when you connect to it, you can add the certificate to your browsers certificate manager.


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
