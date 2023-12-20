# ML-TOOLS
Collection of Python scripts for handling the MasterLink (ML) serial communication protocol.


## ml-broker.py
Message broker that talks to the physical serial interface and converts input data to messages bus nodes will understand.

It's a stand-alone application that receives and adn sends data from / to other system applications through redis. 

Publish data to `link:ml:transmit` to send ML messages.<br>
Receiving ML bus messages are published by ml-broker.py to `link:ml:receive`.

Other apps in this repo will usually use python3-redis for this but you can use any other redis client. 

From example you can also use the redis command line interface for directly interacting with the ML bus like:

`redis-cli PUBLISH link:ml:transmit c0c1010a0047002005020001ffff94`
`redis-cli SUBSCRIBE link:ml:receive`

The first command will send a virtual remote button press from video master to audio master. The second one will print out any incomming ML messages in hex format.

The ML serial communication consists of "telegrams" with a - nowadays - very uncommon parity bit. First and last byte is sent with a MARK parity bit while the other are sent with SPACE. The MARK partiy will notify any receiver of the start and the end of a specific telegram.<br>
As there is no direct hardware support for that on any off-the-shelf chips we have to hack our way around it by using software. Receving telegrams is a bit wanky currently. The second last byte is a telegram checksum and we know roughtly how a message should start. So for every byte received we are adding it to a telegram array and calculate the checksum until it matches the actual byte received. Other techniques like header detection and a timeout will make it a bit more robust. Neverthless in general it cannot be considered a particular nice solution. <br> 
Also this code for sure needs a little refactoring and clean-up in general - for now it works pretty stable.

A running instance of ml-broker.py is a requirement for all other applications interacting with the ML bus. Under no circumstances other apps should directly interact with the serial interface. It always needs to go through this message broker.


## ml-debug.py
A general debugging tool that tries to decode any incomming ML messages into something human readable. 

When started it will print out any ML messages in hex format and then analyse it byte by byte.

Very usefull for listening to the bus for debugging purpose or when implementing new functionality.