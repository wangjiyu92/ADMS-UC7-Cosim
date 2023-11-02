try:
    from constants import *
except ImportError:
    import sys
    import os

    path = os.path.join(os.path.dirname(__file__), os.pardir)
    sys.path.append(path)
    from constants import *
from agents import Agent
#from opendss_wrapper import OpenDSS

from core.OpenDSS import OpenDSS, save_linear_power_flow
import numpy as np

class Feeder(Agent):
    def __init__(self, **kwargs):
        # Set up houses

        kwargs['result_path'] = feeder_results_path
        print('_feeder loads')
        #print(feeder_loads)
        print('_self.houses')
        #print(self.houses)

        self.feeder = None
        self.df_loadshapes = None
        self.df_pvshapes = None
        self.all_load_names = []
        self.all_bus_names = []
        self.utility_pv = {'PV_utility_1': {'p': 1, 'q': 2},
                'PV_utility_2': {'p': 2, 'q': 4},
         }   
        
        self.counter = 1
        global tflag
        tflag=0
        

        super().__init__('Feeder', **kwargs)

    def initialize(self):
        # create feeder instance
        redirects = [master_dss_file]
        #print(redirects)
        #print(str(redirects))
        #print("Compile " + redirects)
        self.feeder = OpenDSS(redirects[0], freq_house, start_time)

        self.all_load_names = self.feeder.get_all_elements(element='Load').index
        self.all_bus_names = self.feeder.get_all_buses()

        global PS_all
        PS_all={}
        global pvinfo
        PS_all['PV']=pd.read_csv(PVshape_file,header=None)[0]
        pvinfo=pd.read_csv(pvinfo_filename)
        
        
        global LS_all
        LS_all={}
        for i in range(0,len(self.all_load_names)):

            #ls_path=os.path.join(feeder_input_path, "Model_UC7", "LS",str(self.all_load_names[i]).upper()+'.csv')
            #LS_all[self.all_load_names[i].upper()]=pd.read_csv(ls_path,header=None)[0]
            LS_all[self.all_load_names[i].upper()]=np.zeros(35040)+0.01
        
        print("check A")
        # update 1
        # self.dfloadshapes_sel = pd.read_csv(loadshapes_sel_file)
        # loadshapes_sel = self.dfloadshapes_sel.iloc[:, 2].tolist()
        # loadshape_vars = dict((key, 0.0) for key in loadshapes_sel)
        # self.df_loadshapes = pd.DataFrame(columns=loadshape_vars.keys())
        # for key, val in loadshape_vars.items():
        #     key_loc_mid=list(loadshape_vars).index(key)
        #     #print(key)
        #     filename = os.path.join(feeder_input_path, "UseCase5",self.dfloadshapes_sel['Type'][key_loc_mid], str(key) + ".csv")
        #     self.df_loadshapes[str(key)] = pd.read_csv(filename, header=None).values.tolist()
        # #1124 lsname = os.path.join(input_path, 'df_loadshapes.csv')
        # #self.loadinfo = pd.read_csv(loadinfo_filename)
        # self.pvinfo = pd.read_csv(pvinfo_filename)
        
        # pvshapes_sel = self.pvinfo.iloc[:, 2].tolist()
        # pvshape_vars = dict((key, 0.0) for key in pvshapes_sel)
        # self.df_pvshapes = pd.DataFrame(columns=pvshape_vars.keys())
        # for key, val in pvshape_vars.items():
        #     key_loc_mid=list(pvshape_vars).index(key)
        #     #print(key)
        #     filename = os.path.join(feeder_input_path, "UseCase5", "PVShape.csv")
        #     self.df_pvshapes[str(key)] = pd.read_csv(filename, header=None).values.tolist()

        # set up results files
        self.initialize_results('community_P')
        self.initialize_results('community_Q')
        self.initialize_results('community_V')
        self.initialize_results('summary')
        self.initialize_results('all_voltages')
        self.initialize_results('all_bus_voltages')
        self.initialize_results('all_powers')
        self.initialize_results('fh_voltage')

    def setup_pub_sub(self):
        print('_DOOM subscriptions')
        #print(self.houses)
        
        self.register_pub('feeder_to_rtds')
        self.register_pub('feeder_to_fems')
        self.register_sub('rtds_to_feeder', default={})
        self.register_sub('fems_to_feeder', default={})

    def setup_actions(self):
        print('Check Setup')
        self.add_action(self.run_feeder, 'Run Feeder', freq_feeder, offset_feeder_run)
        self.add_action(self.save_results, 'Save Results', freq_save_results, offset_save_results)


    def run_feeder(self):
    
        data_rtds = self.fetch_subscription('rtds_to_feeder')
        data_fems = self.fetch_subscription('fems_to_feeder')

        
        ld_pw={}
        ld_qw={}
        for i in range(0,len(self.all_load_names)):
            ld_pw[self.all_load_names[i].upper()]=0
            ld_qw[self.all_load_names[i].upper()]=0
            #print(ld_pw)
        
        global tflag
        global LS_all
       
        t_day=[0,31,59,90,120,151,181,212,243,273,304,334]
  
        print('Start read csv')
        print(datetime.now())
        
        
        for i in range(0,len(self.all_load_names)):
            
            if ld_pw[self.all_load_names[i].upper()]==0:

                ld_pw[self.all_load_names[i].upper()]=LS_all[self.all_load_names[i].upper()][t_day[month-1]*24+(start_date-1)*24+tflag*15//60]

            self.feeder.run_command('edit load.'+self.all_load_names[i].upper()+' kW='+str(ld_pw[self.all_load_names[i].upper()])+' kVAR='+str(ld_qw[self.all_load_names[i].upper()]))
        
        global PS_all
        global pvinfo
        to_aggregator_PV={}
        for i in range(0,len(pvinfo)):
            self.feeder.run_command('edit PVSystem.'+pvinfo['PN'][i].upper()+' pmpp='+str(PS_all['PV'][t_day[month-1]*24+(start_date-1)*24+tflag*15//60]*pvinfo['P'][i]))
            
        print(datetime.now())        
        #print('End read csv')        
        #global tflag
        tflag=tflag+1
        print(tflag)

        self.counter += 1

        # Run DSS
        self.feeder.run_dss()
        
        to_rtds={}
        to_fems={}
        for i in range(0,1):
            
            pmid=self.feeder.get_power(self.all_load_names[i].upper(), element='Load')
            vmid=self.feeder.get_voltage(self.all_load_names[i].upper(), element='Load')
            
            to_rtds['V1']=vmid
            to_fems['V1']=vmid
            
        #     print(self.all_load_names[i].upper())
        #     print(pmid)
        #     print(vmid)
        
        # Get house voltages and send to houses

        self.publish_to_topic('feeder_to_rtds', to_rtds)
        self.publish_to_topic('feeder_to_fems', to_fems)

        
  

        # Add results for all load powers and voltages
        #data = self.feeder.get_all_bus_voltages(average=True)
        data = {load: self.feeder.get_voltage(load) for load in self.all_load_names}
        self.add_to_results('all_voltages', data, remove_seconds=True)
        
        data = {bus_mid: self.feeder.get_bus_voltage(bus_mid) for bus_mid in self.all_bus_names}
        self.add_to_results('all_bus_voltages', data, remove_seconds=True)

        
        
        all_powers = {load: self.feeder.get_power(load, total=True) for load in self.all_load_names}
        # print('_all powers')
        # print(all_powers)
        all_powers = {load + pq: val for load, powers in all_powers.items() for pq, val in
                      zip(('_P', '_Q'), powers)}
        self.add_to_results('all_powers', all_powers, remove_seconds=True)


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2:
        addr = str(sys.argv[1])
        agent = Feeder(broker_addr=addr)
    else:
        #agent = Feeder(debug=True, run_helics=False)
        agent = Feeder(run_helics=False)

    agent.simulate()
