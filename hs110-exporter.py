#!/usr/bin/env python2

import json
import time
import socket
import argparse
from struct import pack
from pkg_resources import parse_version
from prometheus_client import start_http_server, Gauge

version = 1.0

# Create metrics
g_rssi 	= Gauge('rssi', 'Received signal strength indication', ['alias', 'sw_ver', 'hw_ver', 'model'])
total	= Gauge('total', 'Total mw', ['alias'])  # mw
power	= Gauge('power', 'Current Power drain', ['alias'])  # mw
current = Gauge('current', 'Current Current drain', ['alias'])  # ma
voltage = Gauge('voltage', 'Current voltage', ['alias'])  # mv
err = Gauge('err_code', 'Error code', ['alias'])  # mv

# Variables with label data
alias = None
sw_ver = None
hw_ver = None
model = None



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

if __name__ == '__main__':
	# Parse commandline arguments
	parser = argparse.ArgumentParser(description="TP-Link Wi-Fi Smart Plug Client v" + str(version))
	parser.add_argument("-p", "--pull_time", type=int, default=5, help="Pull sensor data every X seconds.")
	parser.add_argument("-t", "--target", metavar="<hostname>", required=True, help="Target hostname or IP address", type=validHostname)
	# group = parser.add_mutually_exclusive_group(required=True)
	# group.add_argument("-c", "--command", metavar="<command>", help="Preset command to send. Choices are: "+", ".join(commands), choices=commands)
	# group.add_argument("-j", "--json", metavar="<JSON string>", help="Full JSON string of command to send")
	args = parser.parse_args()


	# Set target IP, port and command to send
	ip = args.target
	port = 9999

	cmds = [commands['info'],commands['energy']]

	def update_sensor_data():
		# Send command and receive reply
		try:
			data = []
			for cmd in cmds:
				sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock_tcp.connect((ip, port))
				sock_tcp.send(encrypt(cmd))
				data.append(sock_tcp.recv(2048))
			
				sock_tcp.close()

			for d in data:
				# print "Sent:     ", cmd
				# print decrypt(d[4:])
				hs110_data = json.loads(decrypt(d[4:]))
				first_key = hs110_data.keys()[0]
				
				# print "Received: ", first_key

				if first_key == 'system':
					# global alias, sw_ver, hw_ver, model, g_rssi
					# print "System data" #, hs110_data
					alias = hs110_data['system']['get_sysinfo']['alias']
					sw_ver = hs110_data['system']['get_sysinfo']['sw_ver'][0:5]
					hw_ver = hs110_data['system']['get_sysinfo']['hw_ver']
					model = hs110_data['system']['get_sysinfo']['model']
					g_rssi.labels(alias, sw_ver, hw_ver, model).set(hs110_data['system']['get_sysinfo']['rssi'])

					# print hs110_data['system']['get_sysinfo']['err_code']
					
				elif first_key == 'emeter':
					# print "Emeter data", hs110_data
					
					if parse_version(hw_ver) > parse_version("1.0"):
						total.labels(alias).set(hs110_data['emeter']['get_realtime']['total_wh'])
						current.labels(alias).set(hs110_data['emeter']['get_realtime']['current_ma'])
						power.labels(alias).set(hs110_data['emeter']['get_realtime']['power_mw'])
						voltage.labels(alias).set(hs110_data['emeter']['get_realtime']['voltage_mv'])
						err.labels(alias).set(hs110_data['emeter']['get_realtime']['err_code'])
					else:
						total.labels(alias).set(hs110_data['emeter']['get_realtime']['total'])
						current.labels(alias).set(hs110_data['emeter']['get_realtime']['current'])
						power.labels(alias).set(hs110_data['emeter']['get_realtime']['power'])
						voltage.labels(alias).set(hs110_data['emeter']['get_realtime']['voltage'])
						err.labels(alias).set(hs110_data['emeter']['get_realtime']['err_code'])
				else:
					print "Unknown data"
			
		except socket.error:
			quit("Cound not connect to host " + ip + ":" + str(port))


	start_http_server(8110)

	# Update data
	while True:
		update_sensor_data()
		time.sleep(args.pull_time)
