#!/usr/bin/env python3

# THIS HELPS RUN THE SCRIPT ON PYTHON 2 OR 3
from __future__ import absolute_import, division, print_function

# IMPORT MODULES
import json
import mytools
import netmiko
import signal
import sys
import csv
from pprint import pprint

'''
The following input data is required to run this script:
X.txt file with cli commands listed, the name does not matter as the file name
will be command line input directly after the script name
for example:
megamind@ubuntu19cp40:~$python3 send_show.py router_commands.txt

the file named device.csv will be used as a source for IP address and IOS type,
typically formated like this:
172.16.0.1,cisco_ios
172.16.0.2,cisco_ios

the mytools.py is a module that gets pulled in to handle authentication

the following command will need to be used for the environment varible for 
textfsm:
export NET_TEXTFSM=./ntc-templates/templates/

This script was developed by Richard Ziga (Network Engineer) to perform the
following tasks:
prevent trackback in the event that ^C is pressed
read in 2 argv inputs
load argv 1 input to a varible named 'commands'
open the devices.csv which contains IP and IOS data
process the header in the csv
convert the csv to json
load netmiko exceptions into a varible
process credentials using mytools.py
process change control number for the success/failure output
process the cli output to a .txt file and process the same output to a python
list using textfsm then process that python list to csv data output to a file
create a result file showing the success or failure of connecting to and
getting data from network devices
'''
# THIS PREVENTS TRACEBACK FOR THE ^C
signal.signal(signal.SIGINT, signal.SIG_DFL)  # KeyboardInterrupt: Ctrl-C

# THIS WILL ENSURE 2 INPUTS FOR ARGV
if len(sys.argv) < 2:
    print('Usage: sendshow_csv.py router_commands.txt')
    exit()

# THIS LOADS THE COMMAND LINE ARGUMENTS INTO VARIABLES
with open(sys.argv[1]) as cmd_file:
    commands = cmd_file.readlines()

# OPENS DEVICE.CSV A SPREADSHEET THAT INCLUDES IP OF DEVICES AND IOS TYPE
f = open('devices.csv', 'r')

# PROCESS THE HEADER
reader = csv.DictReader(f, fieldnames=("ip", "device_type"))

# PARSE CSV TO JSON
devices_raw = json.dumps([row for row in reader], )
devices_in = json.loads(devices_raw)

# THIS WILL CHECK FOR CONNECTION PROBLEMS AND PUT THEM IN THE VARIABLE
netmiko_exceptions = (netmiko.ssh_exception.NetMikoTimeoutException,
                      netmiko.ssh_exception.NetMikoAuthenticationException)

# THIS GETS USERNAME PASSWORD AND CHANGE NUMBER
username, password = mytools.get_credentials()
change_number = mytools.get_input('Please enter and approved change number: ')

# THIS IS PREP FOR THE WRITE TO RESULTS-CHANGE.JSON FILE AT THE END
chng_results = {'Successful': [], 'Failed': []}

'''
in Pycharm this enviroment varible will need to be configured for textsfm
pycharm term:
export NET_TEXTFSM=./ntc-templates/templates/
full path:
export NET_TEXTFSM=/home/megamind/PycharmProjects/my-projects/cisco
/sendshow_csv/ntc-templates/templates

THE FOLLOWING SECTION OF CODE PROCESSES STD CLI TO .TXT AND CONVERTS TO 
PYTHON LIST USING TEXTFSM AND THEN CONVERTS THAT OUTPUT TO CSV FORMAT:

*************************IMPORTANT******************************
WHEN USING THE GENIE KEYWORD MAKE SURE YOUR INPUT COMMANDS ARE EXACT IN 
ROUTER_COMMANDS.TXT OR YOU WILL GET THIS:
ValueError: dictionary update sequence element #0 has length 1; 2 is required

THIS SCRIPT REQUIRES THE INSTALL OF THE ntc-templates FOLDER:
cwd/git clone https://github.com/networktocode/ntc-templates.git
export NET_TEXTFSM=./ntc-templates/templates/
'''

for device in devices_in:
    device['username'] = username
    device['password'] = password
    try:
        print('~' * 79)
        print('Connecting to device:', device['ip'])
        connection = netmiko.ConnectHandler(**device)
        filename = connection.base_prompt + '.txt'
        filename2 = connection.base_prompt + '.csv'
        dev_name = connection.base_prompt
        # output_z = {}
        # report_fields = ["Interface", "MAC Address", "Bandwidth"]
        csv_keys = [dev_name, 'local_port', 'destination_host', 'management_ip', 'remote_port', 'software_version',  'capabilities', 'platform']
        with open(filename, 'w') as out_file:
            for command in commands:
                out_file.write('## Output of ' + command + '\n\n')
                out_file.write(connection.send_command(command,) + '\n\n')
                command_z = ''.join(map(str, command))
                output = connection.send_command(command_z, use_textfsm=True)
                pprint(output)
                for status in output:
                    with open(filename2, 'w') as f:
                        dict_writer = csv.DictWriter(f, csv_keys)
                        dict_writer.writeheader()
                        dict_writer.writerows(output)

        connection.disconnect()

# HERE THE RESULTS ARE WRITTEN TO VARIABLES
        chng_results['Successful'].append(device['ip'])
    except netmiko_exceptions as error:
        print('Failed to ', device['ip'], error)
        chng_results['Failed'].append(': '.join((device['ip'], str(error))))

# HERE THE RESULTS ARE WRITTEN TO THE SCREEN AND TO A RESULTS-CHANGE.JSON FILE
print(json.dumps(chng_results, indent=2))
with open('results-' + change_number + '.json', 'w') as results_file:
    json.dump(chng_results, results_file, indent=2)
# pprint(output)
