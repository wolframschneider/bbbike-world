#!/bin/sh
# Copyright (c) 2016-2024 Wolfram Schneider, https://bbbike.org
#
# init bbbike.org ubuntu deb repository

: ${DEBUG=false}
enable_legacy="YES"

if $DEBUG; then
  set -x
fi
set -e

sources_list_d=/etc/apt/sources.list.d

init_apt_bbbike() {
    bbbike_list=bbbike.list
    deb_url=https://debian.bbbike.org

    file="$sources_list_d/$bbbike_list"
    os=$(lsb_release -i | perl -npe 's,^Distributor ID:\s+,,; $_=lc($_)')
    codename=$(lsb_release -cs)
    apt_key="$deb_url/$os/$codename/bbbike.asc"

    #
    # install all given *.list files which are not
    # already installed in /etc/apt/sources.list.d
    #
    list_d="world/etc/apt/$os/$codename/sources.list.d"
    flag=0

    if [ -d $list_d ]; then
      for file in $list_d/*.list
      do
        # should never happens
        if [ ! -e "$file" ]; then
          echo "file '$file' does not exist, give up. Wrong cwd?"
          exit 2
        fi

        f=$sources_list_d/$(basename $file)
        if [ ! -e $f ]; then
          sudo cp $file $f
        fi
        flag=1
      done
    fi

    if [ $enable_legacy = "YES" ]; then
      file="world/etc/apt/ubuntu/trusty-legacy/sources.list.d/bbbike-legacy.list"
      f=$sources_list_d/$(basename $file)
      if [ ! -e $f ]; then
        sudo cp $file $f
      fi
      flag=1
    fi

    if [ $flag = "1" ]; then
        curl --connect-timeout 5 -m 36 -sSf $apt_key | sudo apt-key add -
	sudo apt-get install -y apt-transport-https
        sudo apt-get update -qq
    fi
}

# required packages for this script
init_apt_deb() {
    sudo apt-get install -qq -y lsb-release wget curl gnupg dirmngr
}

init_apt_deb
init_apt_bbbike

#EOF
