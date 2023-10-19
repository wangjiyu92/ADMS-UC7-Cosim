# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 11:33:26 2022

@author: jwang4
"""

import socket
import struct
import threading

try:
    from constants import *
except ImportError:
    import sys
    import os

    path = os.path.join(os.path.dirname(__file__), os.pardir)
    sys.path.append(path)
    from constants import *

from agents import Agent

# Authors: Fei Ding, Michael Blonsky, Harsha Padullaparti

# nodes = pd.read_csv(measure_node_filename)['node'].to_list()

# load keys for sending data
#signals = pd.read_csv(rtac_signal_filename)
#from_dss_keys = signals['DSS to OdeepC'][0:2341].to_list() ##from_dss_keys = signals['DSS to rtac'].to_list()
#to_dss_keys = signals['OdeepC to OpenDSS'][pd.notna(signals['OdeepC to OpenDSS'])].to_list()
#invcontrolnum=invcontrolnumber

from_dss_keys=['V1']
to_dss_keys=['V0']


class rtac(Agent):
    def __init__(self, **kwargs):
        self.t_receiver = None
        self.t_sender = None
        super().__init__('rtac', **kwargs)

    def initialize(self):
        if rtac_connected:
            # Receiver for rtac-to-feeder
            self.t_receiver = rtac_receiver()
            self.t_receiver.data = [0 for _ in to_dss_keys]
            self.t_receiver.start()

            # Sender for feeder-to-rtac
            self.t_sender = rtac_sender()
            self.t_sender.data = [0 for _ in from_dss_keys]
            self.t_sender.start()           
            

    def setup_pub_sub(self):
        self.register_sub('feeder_to_rtac', default={})
        #self.register_sub('feeder_to_rtac2', default={})
        self.register_pub('rtac_to_feeder')
        if include_adms:
            self.register_pub('rtac_to_adms', include_results=False)

    def setup_actions(self):
        self.add_action(self.send_to_rtac, 'Send to rtac', freq_all, offset_rtac_send)
        self.add_action(self.receive_from_rtac, 'Receive from rtac', freq_all, offset_rtac_receive)
        self.add_action(self.save_results, 'Save Results', freq_save_results)

    def send_to_rtac(self):
        # Get subscriptions
        #global from_feeder
        from_feeder = self.fetch_subscription('feeder_to_rtac')
        #from_feeder2 = self.fetch_subscription('feeder_to_rtac2')
        print(from_feeder)
        #print(from_feeder2)

        if rtac_connected:
            # Send data to rtac-RT
            to_rtac = []
            for key in from_dss_keys:
                if key == 'Unknown':
                    to_rtac.append(0)
                else:
                    to_rtac.append(from_feeder[key])
            to_rtac = [float(x) for x in to_rtac]
            self.t_sender.data = to_rtac
            self.print_log('Sending to rtac:', self.t_sender.data)

            #to_rtac2 = []
            #for key in from_dss_keys2:
            #    if key == 'Unknown':
            #        to_rtac2.append(0)
            #    else:
            #        to_rtac2.append(from_feeder2[key])
            #self.t_sender.data = to_rtac2
            #self.print_log('Sending to rtac:', self.t_sender.data)

            #print('###########SendData#################')
            #self.t_sender.run
            
            #print(self.t_sender.data)
            #print(len(self.t_sender.data))
            #self.string = struct.pack(">{}".format("f" * len(self.t_sender.data)), *self.t_sender.data)
            #print('###########SendData222#################')
            #self.t_sender.sock.sendto(self.string, ("10.79.91.77", 9010))

        # Send data to ADMS, if the agent exists
        if include_adms:
            self.publish_to_topic('rtac_to_adms', from_feeder)

    def receive_from_rtac(self):
        if rtac_connected:
            # Get data from rtac-RT
            self.print_log('Receiving from rtac:', self.t_receiver.data)
            to_feeder = {key: self.t_receiver.data[i] for i, key in enumerate(to_dss_keys)}
        else:
            to_feeder = {}  # no data sent back to feeder
            to_feeder['rtac']=2

        # Send data to feeder agent
        self.publish_to_topic('rtac_to_feeder', to_feeder)

    def finalize(self):
        super().finalize()
        if rtac_connected:
            self.t_receiver.sock.close()
            self.t_sender.sock.close()


class rtac_receiver(threading.Thread):

    def __init__(self, *args, **kwargs):
        self.data = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet  # UDP
        self.sock.bind(("0.0.0.0", 9050))
        #self.sock.bind(("0.0.0.0", 9011))
        super().__init__(*args, **kwargs)
        
        #print('##########DataReceived')
        #print(self.data_receive)

    def run(self):
        while True:
            # time.sleep(0.1)
            data_in0, addr = self.sock.recvfrom(2048)  # buffer size is 1024 bytes
            data_in00, addr = self.sock.recvfrom(1024)
            #data_in000, addr = self.sock.recvfrom(1024)
            try:
                # print('Raw rtac Data:', data_in0)
                #print('Check3')
                #print('Check4')

                #self.data = struct.unpack("<{}".format("f" * len(self.data)), data_in0)
                #self.data = list(self.data)
                
                
                
                #self.data1 = struct.unpack(">"+"f"*2, data_in0) #ori
                #self.data1 = list(self.data1) #ori
                
                self.data1=struct.unpack("<"+"f"*int(len(data_in0)/4),data_in0)
                

                #self.data2 = struct.unpack(">"+"b"*16, data_in00) #ori
                #self.data2 = list(self.data2) #ori
                
                self.data2 = list(struct.unpack("b"*int(len(data_in00)),data_in00))

                #self.data3 = struct.unpack(">"+"b"*16, data_in000) #ori
                #self.data3 = list(self.data3) #ori
                
                self.data=[self.data1[0],self.data2[0],self.data2[1],self.data2[2]] #ori
                
                for ii in range(1,invcontrolnum*2+1):
                    self.data.append(self.data1[ii])

                #self.data = struct.unpack(">{}".format("f" * len(self.data)), data_in0) 
                #self.data = list(self.data)
                
                #print(data_in0)
            except Exception as e:
                print("Exception occurred")
                print(data_in0)
                raise e


class rtac_sender(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = []
        #self.data_send=self.t_sender.data
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet  # UDP
        #print('##########DataSent')
        #print(self.data_send)

    def run(self):
    
        print('#####################run')
        #print(from_feeder)
        while True:
            # time.sleep(0.1)
            string = struct.pack(">{}".format("f" * len(self.data)), *self.data)
            self.sock.sendto(string, ("10.79.91.42", 5844))
            #self.sock.sendto(string, ("10.79.91.77", 9011))


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2:
        addr = str(sys.argv[1])
        agent = rtac(broker_addr=addr)
    else:
        agent = rtac(run_helics=False)
    agent.simulate()
