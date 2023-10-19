# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 11:34:01 2022

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
#signals = pd.read_csv(rtds_signal_filename)
#from_dss_keys = signals['DSS to rtds'][0:272].to_list() ##from_dss_keys = signals['DSS to rtds'].to_list()
#from_dss_keys2 = signals['DSS to rtds2'][0:257].to_list() ##from_dss_keys = signals['DSS to rtds'].to_list()
#to_dss_keys = signals['rtds to OpenDSS'][pd.notna(signals['rtds to OpenDSS'])].to_list()

from_dss_keys=['V1']
#from_dss_keys2=['P1']
to_dss_keys=['V0']

class rtds(Agent):
    def __init__(self, **kwargs):
        self.t_receiver = None
        self.t_sender = None
        super().__init__('rtds', **kwargs)

    def initialize(self):
        if rtds_connected:
            # Receiver for rtds-to-feeder
            self.t_receiver = rtds_receiver()
            self.t_receiver.data = [0 for _ in to_dss_keys]
            self.t_receiver.start()

            # Sender for feeder-to-rtds
            self.t_sender = rtds_sender()
            self.t_sender.data = [0 for _ in from_dss_keys]
            self.t_sender.start()           

            #self.t_sender2 = rtds_sender2()
            #self.t_sender2.data = [0 for _ in from_dss_keys2]
            #self.t_sender2.start()              

    def setup_pub_sub(self):
        self.register_sub('feeder_to_rtds', default={})
        #self.register_sub('feeder_to_rtds2', default={})
        #self.register_sub('feeder_to_rtds2', default={})
        self.register_pub('rtds_to_feeder')
        if include_adms:
            self.register_pub('rtds_to_adms', include_results=False)

    def setup_actions(self):
        self.add_action(self.send_to_rtds, 'Send to rtds', freq_all, offset_rtds_send)
        self.add_action(self.receive_from_rtds, 'Receive from rtds', freq_all, offset_rtds_receive)
        #self.add_action(self.save_results, 'Save Results', freq_save_results)

    def send_to_rtds(self):
        # Get subscriptions
        #global from_feeder
        from_feeder = self.fetch_subscription('feeder_to_rtds')
        #from_feeder2 = self.fetch_subscription('feeder_to_rtds2')
        #from_feeder2 = self.fetch_subscription('feeder_to_rtds2')
        print(from_feeder)
        #print(from_feeder2)
        #print(from_feeder2)

        if rtds_connected:
            # Send data to rtds-RT
            to_rtds = []
            for key in from_dss_keys:
                if key == 'Unknown':
                    to_rtds.append(0)
                else:
                    to_rtds.append(from_feeder[key])
            print(to_rtds)
            self.t_sender.data = to_rtds
            self.print_log('Sending to rtds:', self.t_sender.data)

            #to_rtds2 = []
            #for key in from_dss_keys2:
            #    if key == 'Unknown':
            #        to_rtds2.append(0)
            #    else:
            #        to_rtds2.append(from_feeder2[key])
            #self.t_sender2.data = to_rtds2
            #self.print_log('Sending to rtds2:', self.t_sender2.data)

            #to_rtds2 = []
            #for key in from_dss_keys2:
            #    if key == 'Unknown':
            #        to_rtds2.append(0)
            #    else:
            #        to_rtds2.append(from_feeder2[key])
            #self.t_sender.data = to_rtds2
            #self.print_log('Sending to rtds:', self.t_sender.data)

            #print('###########SendData#################')
            #self.t_sender.run
            
            #print(self.t_sender.data)
            #print(len(self.t_sender.data))
            #self.string = struct.pack(">{}".format("f" * len(self.t_sender.data)), *self.t_sender.data)
            #print('###########SendData222#################')
            #self.t_sender.sock.sendto(self.string, ("10.79.91.77", 9010))

        # Send data to ADMS, if the agent exists
        if include_adms:
            self.publish_to_topic('rtds_to_adms', from_feeder)

    def receive_from_rtds(self):
        if rtds_connected:
            # Get data from rtds-RT
            self.print_log('Receiving from rtds:', self.t_receiver.data)
            to_feeder = {key: self.t_receiver.data[i] for i, key in enumerate(to_dss_keys)}
        else:
            to_feeder = {}  # no data sent back to feeder
            to_feeder['rtds']=0

        # Send data to feeder agent
        self.publish_to_topic('rtds_to_feeder', to_feeder)

    def finalize(self):
        super().finalize()
        if rtds_connected:
            self.t_receiver.sock.close()
            self.t_sender.sock.close()


class rtds_receiver(threading.Thread):

    def __init__(self, *args, **kwargs):
        self.data = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet  # UDP
        self.sock.bind(("0.0.0.0", 9010))
        super().__init__(*args, **kwargs)
        
        #print('##########DataReceived')
        #print(self.data_receive)

    def run(self):
        while True:
            # time.sleep(0.1)
            data_in0, addr = self.sock.recvfrom(1024)  # buffer size is 1024 bytes
            #print('Check0309')
            #print(len(self.data))
            #print(self.data)
            #print(len(data_in0))
            #print(data_in0)
            
            try:
                # print('Raw rtds Data:', data_in0)
                #print('Check3')
                #print('Check4')
                
                self.data = struct.unpack(">{}".format("f" * len(self.data)), data_in0)
                self.data = list(self.data)
                #print(data_in0)
            except Exception as e:
                print("Exception occurred")
                print(data_in0)
                raise e


class rtds_sender(threading.Thread):
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
            self.sock.sendto(string, ("10.79.91.77", 9010))

class rtds_sender2(threading.Thread):
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
            self.sock.sendto(string, ("10.79.91.78", 9011))

if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2:
        addr = str(sys.argv[1])
        agent = rtds(broker_addr=addr)
    else:
        agent = rtds(run_helics=False)
    agent.simulate()
