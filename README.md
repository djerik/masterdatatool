# ML-TOOLS
Collection of Python scripts for handling the MasterLink (ML) serial communication protocol through the MasterDataTool.

## INSTALLATION
Simply clone this repository and execute the install.sh shell script as root (sudo).<br>
It will create a folder in your /opt directory and install as well as enable systemd services the ml-broker and the ml-linkspeaker-standalone applications.<br>

`git clone https://gitlab.com/masterdatatool/software/ml-tools`<br>
`cd ml-tools`<br>
`chmod +x install.sh`<br>
`sudo install.sh`<br>


## ml-broker
Message broker that talks to the physical serial interface and converts input data to messages bus nodes will understand.

It's a stand-alone application that receives and adn sends data from / to other system applications through redis. 

Publish data to `link:ml:transmit` to send ML messages.<br>
Receiving ML bus messages are published by ml-broker.py to `link:ml:receive`.

Other apps in this repo will usually use python3-redis for this but you can use any other redis client. 

From example you can also use the redis command line interface for directly interacting with the ML bus like:

`redis-cli PUBLISH link:ml:transmit c0c1010a0047002005020001ffff94`<br>
`redis-cli SUBSCRIBE link:ml:receive`

The first command will send a virtual remote button press from audio master to video master. The second one will print out any incomming ML messages in hex format.<br>
Do not include the telegram checksum or the final 0x00 byte. They are added automatically.

The ML serial communication consists of "telegrams" with a - nowadays - very uncommon parity bit. First and last byte is sent with a MARK parity bit while the other are sent with SPACE. The MARK partiy will notify any receiver of the start and the end of a specific telegram.<br>
As there is no direct hardware support for that on any off-the-shelf chips we have to hack our way around it by using software. <br>
Receving telegrams is a bit wanky currently. The second last byte is a telegram checksum and we know roughtly how a message should start. So for every byte received we are adding it to a telegram array and calculate the checksum until it matches the actual byte received. Other techniques like header detection and a timeout will make it a bit more robust. Neverthless in general it cannot be considered a particular nice solution. <br> 
Also this code for sure needs a little refactoring and clean-up in general - for now it works pretty stable and does not need any attention.

A running instance of ml-broker.py is a requirement for all other applications interacting with the ML bus. Under no circumstances other apps should directly interact with the serial interface. It always needs to go through this message broker.


## ml-debug
A general debugging tool that tries to decode any incomming ML messages into something human readable. 

When started it will print out any ML messages in hex format and then analyse it byte by byte.

Very usefull for listening to the bus for debugging purpose or when implementing new functionality.

## ml-linkspeaker-standalone
In a setup where you directly connect the MasterDataTool to a link-speaker without anything else attached to the MasterLink bus this is the application to run.

It will provide responses for most important telegram messages which a link node will send out. 

Also it detects if the audio interface is running and actively outputting something. If that is the case it will send a virtual remote button event to the link node which will then switch on.

Once the stream ended and the audio interface was closed it will send out a global OFF telegram which will turn of the link node.

Furthermore it provides a way to execute system commands on incomming remote events (you pressed a key on the remote controller or changed the source). Currently it is hard-coded for sending DBUS messages to shairport-sync (play / pause / next / previous)

Right in the beginning and then every 30 minutes a clock sync telegram is send out for updating the local clock in the node.

You can use this application with all MasterLink equipped "Link" speakers. BeoLab 3500, BeoLab 2000, BeoLink Passive and BeoLink Active.

If you are missing certain commands or want to implement new ones you can run ml-debug in parallel to have direct access to messages the node sends.


## ml-netprovide
-- work-in-progress -- <br>
Application that simulates a "SourceCenter" device on the ML bus. <br>
Originally a separate device (embedded Windows PC) that provides N.Radio (webradio) and N.Music (locally stored music) sources to "offline / traditional" music systems. 

Here we will use that for a few pre-defined webradio stations that are assigned to favourite keys and also for the automatic injection of shairport-sync and spotifyd audio streams.

Compatible with BeoSound 3000, BeoSound 3200, BeoSound 9000, BeoSound 4, BeoSound 2.
Some older BS3X00 and BS9000 do not support the N.Radio / N.Music sources. For this to work you would have to do a firmware upgrade (eeprom change - still available). Alternatively you could also set it to option 2 and simulate a video master with the MasterDataTool. You could then use the TV and SAT sources for webradio and streaming. Video master simulation is not implemented currently but certainly possible.

## ml-status-in
-- work-in-progress -- <br>
Reads all status messages available from ML and stores them in redis <br>



