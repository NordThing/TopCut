#!/usr/bin/env python
# coding: latin-1
# Autor:   Ingmar Stapel
# Datum:   20170225
# Version:   1.0
# Homepage:   http://custom-build-robots.com
# This program was developed to read the NMEA stream
# generated by the RTK library for precise navigation.

# Parts of the program regarding the nmea processing are from
# the following website:
# https://amalgjose.com/tag/python-program-to-read-gps-values/
# To run this program you have to install pynmea on your machine.
# pynmea can be installed with pip by typing:
# sudo pip install pynmea

import os
from gps import *
import string
from pynmea import nmea

import socket
import sys

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Define the server address and port from which the NMEA
# should be read from.
server_address = ('localhost', 2948)

try:
	# Connect the socket to the port where the RTK server is listening
	sock.connect(server_address)
	print '-------------------------------------------'	
	print >>sys.stderr, 'connecting to <%s> port <%s>' % server_address			
	print '-------------------------------------------'
except:
    print "Unexpected error:", sys.exc_info()[0]
    raise

# Read each line from the NMEA stream.
def readlines(sock, recv_buffer=4096, delim='\n'):
	buffer = ''
	data = True
	while data:
		data = sock.recv(recv_buffer)
		buffer += data

		while buffer.find(delim) != -1:
			line, buffer = buffer.split('\n', 1)
			yield line
	return

# Create an instance of an GPGGA object. 	
gpgga = nmea.GPGGA()

# Process the NMEA data and display the result.	
try:
	for line in readlines(sock):
		#print line
		if line[0:6] == '$GPGGA':
			os.system('clear')
			
			#method for parsing the NMEA sentence
			gpgga.parse(line)
			lats = gpgga.latitude
			
			# Print some information about the position of the
			# mobile station / robot.
			print '-------------------------------------------'	
			print >>sys.stderr, 'connecting to <%s> port <%s>' % server_address		
			print '-------------------------------------------'
			print '\n-------------------------------------------'
			print '          READ RTK NMEA STREAM             '
			print '-------------------------------------------'			
			print "Latitude values : " + str(lats)

			lat_dir = gpgga.lat_direction
			print "Latitude direction : " + str(lat_dir)

			longitude = gpgga.longitude
			print "Longitude values : " + str(longitude)

			long_dir = gpgga.lon_direction
			print "Longitude direction : " + str(long_dir)

			time_stamp = gpgga.timestamp
			print "GPS time stamp : " + str(time_stamp)

			alt = gpgga.antenna_altitude
			print "Antenna altitude : " + str(alt)
			print '-------------------------------------------'
			
			lats = gpgga.latitude
			longs = gpgga.longitude
			
			#convert degrees,decimal minutes to decimal degrees
			# The source for the decimal calcualtion was:
			# http://dlnmh9ip6v2uc.cloudfront.net/tutorialimages/Python_and_GPS/gpsmap.py
			lat1 = (float(lats[2]+lats[3]+lats[4]+lats[5]+lats[6]+lats[7]+lats[8]))/60
			lat = (float(lats[0]+lats[1])+lat1)
			long1 = (float(longs[3]+longs[4]+longs[5]+longs[6]+longs[7]+longs[8]+longs[9]))/60
			long = (float(longs[0]+longs[1]+longs[2])+long1)			
			
			print '\n------------ decimal degrees --------------'	
			print 'lat: ',lat
			print 'long: ',long
			print '-------------------------------------------'
except:
    print "Unexpected error:", sys.exc_info()[0]
    raise

# Program end
