#!/bin/bash

apt-get update
apt-get install -y libffi-dev gfortran gfortran-8 libarpack2 libarpack2-dev   \
       libnlopt-dev libsphere-dev libcminpack-dev icoutils libssl-dev gcalcli \
       libgmp3-dev libgmp-dev libreadline-dev cmake  libcurl4-gnutls-dev      \
       libedit-dev   uuid-dev liblz-dev liblzma-dev      \
       lzma-dev libarchive-dev libpanel-applet-dev tcl-snack-dev tk8.6-dev    \
       tk-dev libtclcl1-dev libplplot-dev tcl-dev tclcl-dev tcl8.6-dev        \
       libtinfo-dev libncurses5-dev libzmq3-dev      \
       libqdbm-dev libgdbm-dev libsqlite3-dev jq libbz2-dev zlib1g-dev        \
       libncurses-dev make libgnutls28-dev
