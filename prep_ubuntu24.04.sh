#!/bin/bash

apt-get update
apt-get install -y libffi-dev gfortran libarpack2t64 libarpack2-dev   \
       libnlopt-dev libcminpack-dev icoutils libssl-dev gcalcli \
       libgmp3-dev libgmp-dev  cmake                         \
       libedit-dev  libreadline-dev uuid-dev liblz-dev liblzma-dev      \
       lzma-dev libarchive-dev cairo-dock-dev libindicator3-dev libindicator-dev\
       tcl-snack-dev tk8.6-dev    \
       tk-dev libtclcl1-dev libplplot-dev tcl-dev tclcl-dev tcl8.6-dev        \
       libtexttools-dev      \
       libqdbm-dev libgdbm-dev libsqlite3-dev jq libbz2-dev zlib1g-dev        \
       libncurses-dev make libpcre2-dev libpcre3-dev libzmq3-dev sbcl texinfo
