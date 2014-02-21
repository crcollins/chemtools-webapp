#!/usr/bin/env bash

virtualenv project
cd project/
. bin/activate
ln -s /usr/lib/python2.7/dist-packages/cairo/ lib/python2.7/site-packages/

