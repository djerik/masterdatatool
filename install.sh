#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "This script must be run as root / sudo"
  exit 1
fi

if [ -d "/opt/ml-tools" ]; then

    echo "Deleting /opt/ml-tools folder"
    rm -rf /opt/ml-tools
    
fi

if ! [ -d "/opt/ml-tools" ]; then

    echo "Generating /opt/ml-tools folder"
    mkdir /opt/ml-tools
    mkdir /opt/ml-tools/ml-broker
    mkdir /opt/ml-tools/ml-linkspeaker-standalone
    mkdir /opt/ml-tools/ml-netprovide
    
fi

echo "Copying ml-broker.py"
cp ml-broker/ml-broker.py /opt/ml-tools/ml-broker/ml-broker.py
echo "Copying ml-linkspeaker-standalone.py"
cp ml-linkspeaker-standalone/ml-linkspeaker-standalone.py /opt/ml-tools/ml-linkspeaker-standalone/ml-linkspeaker-standalone.py
echo "Copying ml-netprovide.py"
cp ml-netprovide/ml-netprovide.py /opt/ml-tools/ml-netprovide/ml-netprovide.py

echo "Copying ml-broker.service"
cp ml-broker/ml-broker.service.in /lib/systemd/system/ml-broker.service
echo "Copying ml-linkspeaker-standalone.service"
cp ml-linkspeaker-standalone/ml-linkspeaker-standalone.service.in /lib/systemd/system/ml-linkspeaker-standalone.service
echo "Copying ml-netprovide.service"
cp ml-netprovide/ml-netprovide.service.in /lib/systemd/system/ml-netprovide.service

echo "Enabling ml-broker"
systemctl enable ml-broker

echo "Starting ml-broker"
systemctl restart ml-broker

