#!/usr/bin/python

import sh
import os
import logging
import re
import argparse

if __name__ == '__main__':
	FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
	logging.basicConfig(format=FORMAT, level=logging.DEBUG)
	logger = logging.getLogger();

	parser = argparse.ArgumentParser()
	parser.add_argument('--short', action='store_true', help='Only display limited information.')
	args = parser.parse_args()

	if not args.short:
		try:
			my_ip = sh.curl('ifconfig.me').strip()
			logger.info("publicip='{my_ip}'".format(**locals()))
		except Exception as e:
			logger.info("publicip=unknown " + e.message)
	
		try:
			for device in sh.tail(sh.df(),n='+2').splitlines():
				match = re.match('([^\\s]+)\\s+([^\\s]+)\\s+([^\\s]+)\\s+([^\\s]+)\\s+([^\\s]+)\\s+([^\\s]+)', device)
				logger.info("DiskUsage - device={0} size={1} used={2} available={3} usepercent={4} mountedon={5}".
					    format(match.group(1), match.group(2), match.group(3), match.group(4), match.group(5).strip('%'), match.group(6)))
		except Exception as e:
			logger.info("DiskUsage - unavailable: " + e.message)
	
		try:
			mem = sh.tail(sh.free(), n='+2').splitlines()
			for line in mem:
				match = re.match('([^:]+):\\s+(\\d+)\\s+(\\d+)\\s+(\\d+)', line)
				if match is not None:
					logger.info("Mem {0} - total={1} used={2} free={3}".format(match.group(1), match.group(2), match.group(3), match.group(4)))
		except Exception as e:
			logger.warn("Mem - unavailable: " + e.message)
			
		try:
			kernel = sh.uname(r=True).strip()
			logger.info("kernel={kernel}".format(**locals()))
		except Exception as e:
			logger.warn("kernel=unknown " + e.message)

	try:
		fd = sh.sysctl('fs.file-nr').strip()
		match = re.match('fs.file-nr = (\\d+)\\s+(\\d+)\\s+(\\d+)', fd)
		logger.info("FileDescriptorLimits - used={0} allocated_available={1} limit={2}".
			    format(match.group(1), match.group(2), match.group(3)))
	except Exception as e:
		logger.warn("FileDescriptorLimits - unavailable: " + e.message)
	
	try:
		number_of_connections = sh.wc(sh.grep(sh.netstat('-ant'), 'ESTABLISHED'), l=True).strip()
		logger.info("TCP number_of_connections={0}".format(number_of_connections))
	except Exception as e:
		logger.warn("TCP - unavailable: " + e.message)

	try:
		uptime = sh.cat('/proc/uptime').strip()
		match = re.match('(\\d+\\.\\d+)\\s+(\\d+\\.\\d+)', uptime)
		logger.info("Uptime uptime={0} idletime={1}".format(match.group(1), match.group(2)))
	except Exception as e:
		logger.warn("Uptime - unavailable: " + e.message)
