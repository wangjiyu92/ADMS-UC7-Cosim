import os
import pandas as pd
from datetime import datetime, timedelta

# Scenario Name (used for finding Master Spreadsheet)
scenario_name = os.environ['SCENARIO_NAME'] if 'SCENARIO_NAME' in os.environ else 'test40'
no_of_homes = int(os.environ['NO_OF_HOMES']) if 'NO_OF_HOMES' in os.environ else 10
der_penetration_pc = os.environ['DER_PENETRATION'] if 'DER_PENETRATION' in os.environ else 'BAU'  # 'BAU', '50p', '100p'
building_model = os.environ['BUILDING_MODEL'] if 'BUILDING_MODEL' in os.environ else 'sd_ca'
debug = True

# Simulation interval
start_date = int(os.environ['START_DATE']) if 'START_DATE' in os.environ else 1
days = int(os.environ['NO_OF_DAYS']) if 'NO_OF_DAYS' in os.environ else 1
month = int(os.environ['MONTH']) if 'MONTH' in os.environ else 1
year = 2019
start_time = datetime(year, month, start_date, 0, 0)  # (Year, Month, Day, Hour, Min)
duration = timedelta(days=days)
# start_time = datetime(year, 3, 2, 0, 0)  # (Year, Month, Day, Hour, Min)
# duration = timedelta(days=7)
time_step = timedelta(seconds=10)
end_time = start_time + duration
times = pd.date_range(start=start_time, end=end_time, freq=time_step)[:-1]

# Agents to run
include_house = os.environ['HOUSE'] == 'True' if 'HOUSE' in os.environ else True
include_feeder = os.environ['FEEDER'] == 'True' if 'FEEDER' in os.environ else True
include_hems = os.environ['HEMS'] == 'True' if 'HEMS' in os.environ else False

fems_connected=0
gridappsd_connected=0
include_adms=0

# Frequency of Updates
freq_house = timedelta(minutes=1)
freq_all = timedelta(minutes=15)
freq_hems = timedelta(minutes=15)
freq_feeder = timedelta(minutes=15)
freq_save_results = timedelta(hours=1)

# Foresee variables 
hems_horizon = timedelta(hours = 8)

# Time offsets for communication order

offset_feeder_run = timedelta(seconds=0)
offset_fems_send= timedelta(seconds=0)
offset_fems_receive= timedelta(seconds=0)
offset_gridappsd_send= timedelta(seconds=0)
offset_gridappsd_receive= timedelta(seconds=0)
offset_save_results = timedelta(0)

# Input/Output file paths
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
input_path = os.path.join(base_path, "inputs")
output_path = os.path.join(base_path, "outputs", scenario_name)
feeder_input_path = os.path.join(input_path, "opendss")


# Input file locations
# TODO: update
print('SCENARIO NAME:', scenario_name)
if scenario_name == 'test':
    master_dss_file = os.path.join(feeder_input_path, "Model_UC7", "Master_primary.dss")
elif scenario_name == 'test40':
     master_dss_file = os.path.join(feeder_input_path, "Model_UC7", "Master_primary.dss")

else:
    # TODO: Update once we have original feeder
    master_dss_file = os.path.join(feeder_input_path, "Model_UC7", "Master_primary.dss")
print("MASTER DSS FILE:", master_dss_file)



PVshape_file = os.path.join(feeder_input_path, "Model_UC7", 'PVShape.csv')
loadshapes_sel_file = os.path.join(feeder_input_path, "Model_UC7",  "loadshapes_sel.csv")
loadinfo_filename = os.path.join(feeder_input_path, "Model_UC7", 'Load_info.csv')
pvinfo_filename = os.path.join(feeder_input_path, "Model_UC7", 'Pv_info.csv')
tflag=0

# Output file locations

feeder_results_path = os.path.join(output_path, 'Feeder')



