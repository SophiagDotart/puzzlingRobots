#
# Breaks down the msg in several packages to be able to send through RFID. If you are using a different tech then change according to your parameters.
# Structured like a handshake.

#1 packet looks like:
#Byte 0: Packet Type -> INIT, DATA, Done sending (DONESND), Acknowledge (ACK), Done receiving (DONERCV)
#Byte 1: Packet Index -> The howmanyth packet is being sent since the start of this conversation
#Byte 2: Total packets -> How many packets will be needed in total for the entire conversation
#Byte 3-12: Content
#Byte 13: Checksum for safety

import controlHardware as hw
import mapFunctions as mapFunc
import switchingConditions_tester as switchCon
import messageBuild as msgBuild

import numpy as np

#----- Parameters -----
FRAME_SIZE = 16         #max for RFID with MCRxxx
PACKAGE_HEADER = 3
MAX_PAYLOAD = FRAME_SIZE - PACKAGE_HEADER
MAX_MAP_SIZE = mapFunc.MAX_MAP_SIZE 
TIMEOUT = 100           # change to real time?

#----- Packet Types -----
PKT_INIT = 1
PKT_DATA = 2
PKT_DONESND = 3
PKT_ACK = 4
PKT_DONERCV = 5

class MapCommunication:
    def __init__(self):
        self.id = switchCon.self.id
        self.totPackets = None 
        self.sentPackets = None
        self.buffer = {}

    def startTransfer(self, comprMap: bytearray):
        self.map = comprMap
        self.sentPackets = 0
        self.totPackets = np.ceil(len(self.map)/MAX_PAYLOAD)    #np.ceil = round up to int :)
        self.partitions = msgBuild.serialize(self.map)

        packet = {
            packageType = PKT_INIT,
            idx = self.sentPackets,
            totalPackets = self.totPackets,
            payload = self.partitions #wait, should this not be sent later -> just init it???
        }
        hw.hw_send(packet)

    def onTransferReceived(self):
        pass
    
    def endTransfer(self):
        pass

    def partitionCompMap(self):
        pass

    def recomposeCompMap(self):
        pass

    def waitOnACK(self):
        pass

    def processACK(self):
        pass

    def processDONERCV(self):
        pass
