#!/usr/bin/env bash

[ -z "$INSTALL_USER" ] && INSTALL_USER=vagrant
[ -z "$CHEMTOOLS_DIR" ] && CHEMTOOLS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PIP_DEFAULT_TIMEOUT=600

dependencies() {
    sudo apt-get update
    sudo apt-get install -y git python2.7 python-dev gfortran liblapack-dev\
                            libatlas-dev build-essential libfreetype6-dev\
                            libpng-dev python-cairo python-pip
    sudo pip install virtualenv
}

install_chemtools() {
    cd $CHEMTOOLS_DIR
    virtualenv .
    . bin/activate
    ln -fs /usr/lib/python2.7/dist-packages/cairo/ lib/python2.7/site-packages/

    pip install numpy==1.6.1
    pip install -r requirements.txt
    python manage.py syncdb --noinput
}

setup_nginx() {
    sudo apt-get update
    sudo apt-get install -y supervisor nginx

    cd $CHEMTOOLS_DIR
    . bin/activate
    pip install gunicorn
    sudo tee /etc/cron.d/chemtools <<EOF
PATH=$CHEMTOOLS_DIR/bin
0 3 * * * $INSTALL_USER cd $CHEMTOOLS_DIR && python -u $CHEMTOOLS_DIR/manage.py update_ml >> $CHEMTOOLS_DIR/ml_update.log
EOF
    sudo sed -e "s/\$INSTALL_USER/$INSTALL_USER/g"      \
             -e "s,\$CHEMTOOLS_DIR,$CHEMTOOLS_DIR,g"    \
             project/nginx_settings.conf                \
             | sudo tee /etc/nginx/sites-available/chemtools
    sudo sed -e "s/\$INSTALL_USER/$INSTALL_USER/g"      \
             -e "s,\$CHEMTOOLS_DIR,$CHEMTOOLS_DIR,g"    \
             project/supervisor_settings.conf           \
             | sudo tee /etc/supervisor/conf.d/chemtools.conf
    sudo ln -fs /etc/nginx/sites-available/chemtools /etc/nginx/sites-enabled/chemtools
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -s reload

    sudo supervisorctl reread
    sudo supervisorctl update
    sudo service nginx restart
}

remove() {
    sudo rm -rf $CHEMTOOLS_DIR /etc/nginx/sites-available/chemtools \
                /etc/nginx/sites-enabled/chemtools /etc/supervisor/conf.d/chemtools.conf \
                /etc/cron.d/chemtools
    sudo supervisorctl shutdown chemtools
    sudo service nginx restart
}

if [ "$1" == "remove" ];
    then
    echo "Uninstalling"
    remove
else
    dependencies
    install_chemtools
    if [ "$1" != "dev"];
        then
        setup_nginx
    fi
fi