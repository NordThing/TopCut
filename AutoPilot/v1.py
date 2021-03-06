#2020-09-13 Latest updated
#Author Henrik Allberg @henrikallberg
#Start of the autopilot for the lawnmower
#First it will just take use of the Magnetometer and GPS from a network stream
#Will put waypoints in a vector - would be nice to have an alogritm for that later
#Should make this program works first

import os
from gps import *
import string
from pynmea import nmea

import socket
import sys

import RPi.GPIO as GPIO
from time import sleep

#Imported numpy to use array inside the program especially for the waypoints
import numpy as np

#This to use the heading/bearing from the magnetometer hmc5883l
import hmc5883l as HMC

#This is to calculate the distance and angle to the next waypoint - this is used for the autopilot
import gpscalculatemodule as GPSCalc

#Initialistion for the calculated distance
#and for the calculated course angle
distance = 0
angle = 0

#motor variables
FORWARD_VEL = 230
SLOW_TURN_VEL = 220
PIVOT_WHEEL_VEL = 50
FAST_TURN_VEL = 180

#Calibration constants for the motors in differential drive config.
# e. g. if the left motor is slower that the right one, you can add some
# % to the left and reduce the same % to the right, and viceversa.#Initialise motor 1 and motor 2 on $
K_RIGHT_MOTOR = 1.0
K_LEFT_MOTOR = 1.0
vel = 255

#Tolerance how near you need to be the waypoint to set it as reached higher value less sensitive
TOLERANCE_RADIUS = 1.0

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

#Initialise motor 1 controller on L298
Motor1A = 16
Motor1B = 18
Motor1E = 32
GPIO.setup(Motor1A,GPIO.OUT)
GPIO.setup(Motor1B,GPIO.OUT)
GPIO.setup(Motor1E,GPIO.OUT)

#Initialise motor 2 controller on L298
Motor2A = 21
Motor2B = 23
Motor2E = 33
GPIO.setup(Motor2A,GPIO.OUT)
GPIO.setup(Motor2B,GPIO.OUT)
GPIO.setup(Motor2E,GPIO.OUT)

GPIO.output(Motor1A,GPIO.HIGH)
GPIO.output(Motor1B,GPIO.LOW)
GPIO.output(Motor2A,GPIO.HIGH)
GPIO.output(Motor2B,GPIO.LOW)
GPIO.output(Motor1E,GPIO.HIGH)
GPIO.output(Motor2E,GPIO.HIGH)


#Function to turn motor on
def motor_on():
  GPIO.output(Motor1A,GPIO.HIGH)
  GPIO.output(Motor1B,GPIO.LOW)
  GPIO.output(Motor1E,GPIO.HIGH)
  GPIO.output(Motor2A,GPIO.HIGH)
  GPIO.output(Motor2B,GPIO.LOW)
  GPIO.output(Motor2E,GPIO.HIGH)

#Function to turn motor off
def motor_off(): 
  GPIO.output(Motor1E,GPIO.LOW)
  GPIO.output(Motor2E,GPIO.LOW)

#Here is the waypoint that the program will use
nav_waypoint = np.loadtxt("waypoints.txt", dtype=np.float64, delimiter=",", skiprows=1)
#nav_waypoint = np.array([[1,2],[3,4],[5,6]])
#Number of waypoints to use in the loop so all waypoints will be went trough
#Removing 1 because of the index_waypoints array starts a 0 and the len will give us 3 
#but there are for 4 waypoints we should pass
num_waypoints = (len(nav_waypoint)) - 1

#Index of waypoints
index_waypoints = 0

#Setting global variable for waypoint_lat and waypoint_lon to get acces to the globals outside the method
def act_waypoint(index_waypoints):
  print 'Actual waypoint'
  print(nav_waypoint[index_waypoints,0:2])
  global waypoint_lat
  global waypoint_lon
  waypoint_lat = nav_waypoint[index_waypoints,0]
  waypoint_lon = nav_waypoint[index_waypoints,1]
  
#Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Define the server address and port from which the NMEA
# should be read from.
server_address = ('localhost', 50022)

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

# Constants for defining error ranges for the stepped proportional control
MAX_HEADING_ANGLE = 180 
MIN_HEADING_ANGLE = 5
ANGLE_RANGE_DIV = 0.25


def Forward(val):
  GPIO.output(Motor1E,vel * K_RIGHT_MOTOR)
  GPIO.output(Motor2E,vel * K_LEFT_MOTOR)

def Turn_Left(vel):
  pwmMotor1 = GPIO.PWM(Motor1E, vel * K_RIGHT_MOTOR)
  pwmMotor2 = GPIO.PWM(Motor2E, PIVOT_WHEEL_VEL * K_LEFT_MOTOR)

def Turn_Right(vel):
  pwmMotor1 = GPIO.PWM(Motor1E, PIVOT_WHEEL_VEL * K_RIGHT_MOTOR)
  pwmMotor2 = GPIO.PWM(Motor2E, vel * K_LEFT_MOTOR)
def Turn_Left_Fast_Spin(vel):
  pwmMotor1 = GPIO.PWM(Motor1E, vel * K_RIGHT_MOTOR)
  pwmMotor2 = GPIO.PWM(Motor2E, vel * K_LEFT_MOTOR)

def Turn_Right_Fast_Spin(vel):
  pwmMotor1 = GPIO.PWM(Motor1E, vel * K_RIGHT_MOTOR)
  pwmMotor2 = GPIO.PWM(Motor2E, vel * K_LEFT_MOTOR)

#Stopping all motors on rover
def Stop():
  GPIO.output(Motor1E,GPIO.LOW)
  GPIO.output(Motor2E,GPIO.LOW)

def Control_Navigation(act_heading,dir_heading):
   heading_error = (dir_heading - act_heading)
#   print heading_error
   if heading_error < -180:
     heading_error = heading_error + 360
   elif heading_error > 180:
     heading_error = heading_error -360
   print heading_error

   #Turn right
   if (heading_error > MIN_HEADING_ANGLE and heading_error <= MAX_HEADING_ANGLE * ANGLE_RANGE_DIV):
     Turn_Right(SLOW_TURN_VEL)
     print"Turn right" 
   elif (heading_error > MAX_HEADING_ANGLE * ANGLE_RANGE_DIV and  heading_error <= MAX_HEADING_ANGLE):
     Turn_Right_Fast_Spin(FAST_TURN_VEL)
     print"Turn right fast"
   elif (heading_error < -MIN_HEADING_ANGLE and heading_error >= -MAX_HEADING_ANGLE * ANGLE_RANGE_DIV): 
     Turn_Left(SLOW_TURN_VEL)
     print"Turn left"
   elif (heading_error < -MAX_HEADING_ANGLE * ANGLE_RANGE_DIV and heading_error >= -MAX_HEADING_ANGLE):
     Turn_Left_Fast_Spin(FAST_TURN_VEL)
     print"Turn left fast"
   elif (heading_error >= -MIN_HEADING_ANGLE and heading_error <= MIN_HEADING_ANGLE):
     Forward(FORWARD_VEL)
     print"Forward"
   else:
     print"Not defined"

# Process the NMEA data and store it in two variables continuous.
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
                        #Latitude direction   
                        lat_dir = gpgga.lat_direction

                        #Longitude values
                        longitude = gpgga.longitude

                        #Longitude direction
                        long_dir = gpgga.lon_direction
                       
                        #GPS time stamps
                        time_stamp = gpgga.timestamp
                        
                        #Antenna altitude
                        alt = gpgga.antenna_altitude
                        
                        lats = gpgga.latitude
                        longs = gpgga.longitude

                        #convert degrees,decimal minutes to decimal degrees
                        # The source for the decimal calcualtion was:
                        # http://dlnmh9ip6v2uc.cloudfront.net/tutorialimages/Python_and_GPS/gpsmap.py
                        lat1 = (float(lats[2]+lats[3]+lats[4]+lats[5]+lats[6]+lats[7]+lats[8]))/60
                        lat = (float(lats[0]+lats[1])+lat1)
                        long1 = (float(longs[3]+longs[4]+longs[5]+longs[6]+longs[7]+longs[8]+longs[9]))/60
                        long = (float(longs[0]+longs[1]+longs[2])+long1)

                        print '\n------------ rover information --------------'
                        print 'lat: ',lat
                        print 'long: ',long
                        print 'direction: ', HMC.bearing()
                        print '-------------------------------------------'
                        
                        #Calling the function act_waypoint() to get the waypoint that we are heading against
                        #To call waypoint_lat and waypoint_lon act_waypoint has to be run before so globals variables are defined
                        act_waypoint(index_waypoints)
                        
                        #Call of the module gpc-calculate-module with the GPS coordinates
                        distance, angle = GPSCalc.calc(lat, long, waypoint_lat, waypoint_lon)
                        if angle < 0:
                          angle += 360
                        else:
                          pass
                        Control_Navigation(HMC.bearing(),angle)
                        print '\n------------ waypoint info ----------------'
                        print 'lat: ',waypoint_lat 
                        print 'long: ',waypoint_lon
                        print 'direction: ', round(angle, 1)
                        print 'distance to waypoint: ', round(distance,1), 'm'
                        if round(distance,1) < TOLERANCE_RADIUS:
                          print('You have reached waypoint',index_waypoints)
                          index_waypoints = 1 + index_waypoints
                          print('You will now head against',index_waypoints)
                          sleep(3)
                        elif index_waypoints == num_waypoints:
                          print('Yoh have been on all waypoints - exit') 
                          print('Rover is going to home position')
                          Stop()
                          break
                        else:
                          print('You are too far away from the waypoint')
#                          print('You have reached waypoint',index_waypoints)
#                          index_waypoints = 1 + index_waypoints
#                          print('You will now head against',index_waypoints)
#                          sleep(3) 
                        print 'total waypoints: ',num_waypoints + 1
                        print 'wayponints left: The rover is on',index_waypoints + 1, ' of total ',num_waypoints + 1
                        print '-------------------------------------------'
                        print '--------Waypoints from file ---------------'  
                        print '-------------------------------------------'

except:
    print "Unexpected error:", sys.exc_info()[0]
    raise

