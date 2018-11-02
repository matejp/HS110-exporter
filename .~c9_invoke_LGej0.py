#!/usr/bin/env python2

import json
import socket
import argparse
from struct import pack

version = 0.2

# Check if hostname is valid
def validHostname(hostname):
	try:
		socket.gethostbyname(hostname)
	except socket.error:
		parser.error("Invalid hostname.")
	return hostname

# Predefined Smart Plug Commands
# For a full list of commands, consult tplink_commands.txt
commands = {'info'     : '{"system":{"get_sysinfo":{}}}',
			'on'       : '{"system":{"set_relay_state":{"state":1}}}',
			'off'      : '{"system":{"set_relay_state":{"state":0}}}',
			'cloudinfo': '{"cnCloud":{"get_info":{}}}',
			'wlanscan' : '{"netif":{"get_scaninfo":{"refresh":0}}}',
			'time'     : '{"time":{"get_time":{}}}',
			'schedule' : '{"schedule":{"get_rules":{}}}',
			'countdown': '{"count_down":{"get_rules":{}}}',
			'antitheft': '{"anti_theft":{"get_rules":{}}}',
			'reboot'   : '{"system":{"reboot":{"delay":1}}}',
			'reset'    : '{"system":{"reset":{"delay":1}}}',
			'energy'   : '{"emeter":{"get_realtime":{}}}'
}

# Encryption and Decryption of TP-Link Smart Home Protocol
# XOR Autokey Cipher with starting key = 171
def encrypt(string):
	key = 171
	result = pack('>I', len(string))
	for i in string:
		a = key ^ ord(i)
		key = a
		result += chr(a)
	return result

def decrypt(string):
	key = 171
	result = ""
	for i in string:
		a = key ^ ord(i)
		key = ord(i)
		result += chr(a)
	return result

def iterator(payload):
   for i in payload:
       if isinstance(payload[i],dict):
           iterator(payload[i])
       else:
           return payload[i]
           
# Parse commandline arguments
parser = argparse.ArgumentParser(description="TP-Link Wi-Fi Smart Plug Client v" + str(version))
parser.add_argument("-t", "--target", metavar="<hostname>", required=True, help="Target hostname or IP address", type=validHostname)
# group = parser.add_mutually_exclusive_group(required=True)
# group.add_argument("-c", "--command", metavar="<command>", help="Preset command to send. Choices are: "+", ".join(commands), choices=commands)
# group.add_argument("-j", "--json", metavar="<JSON string>", help="Full JSON string of command to send")
args = parser.parse_args()


# Set target IP, port and command to send
ip = args.target
port = 9999

cmds = [commands['info'],commands['energy']]

# Send command and receive reply
try:
	sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock_tcp.connect((ip, port))
	
	data = []
	for cmd in cmds:
		sock_tcp.send(encrypt(cmd))
		data.append(sock_tcp.recv(2048))
	
	sock_tcp.close()

	for d in data:
		# print "Sent:     ", cmd
		hs110_data = json.loads(decrypt(d[4:]))
		first_key = hs110_data.keys()[0]
		
		print "Received: ", first_key
		
		if first_key == 'system':
			print "System data" #, hs110_data
			print hs110_data['system']['get_sysinfo']['hw_ver']
			print hs110_data['system']['get_sysinfo']['sw_ver']
			print hs110_data['system']['get_sysinfo']['alias']
			print hs110_data['system']['get_sysinfo']['model']
			print hs110_data['system']['get_sysinfo']['rssi']
			print hs110_data['system']['get_sysinfo']['err_code']
			
		elif first_key == 'emeter':
			print "Emeter data" #, hs110_data
			print ""hs110_data['emeter']['get_realtime']['total_wh']
			print hs110_data['emeter']['get_realtime']['current_ma']
			print hs110_data['emeter']['get_realtime']['power_mw']
			print hs110_data['emeter']['get_realtime']['voltage_mv']
			print hs110_data['emeter']['get_realtime']['err_code']
		else:
			print "Unknown data"
	
except socket.error:
	quit("Cound not connect to host " + ip + ":" + str(port))

