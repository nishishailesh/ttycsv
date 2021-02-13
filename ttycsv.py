#!/usr/bin/python3
import sys
import fcntl

s=None
x=None
logfile_name='/var/log/ttycsv.in.log'
log=1	#0=disable anyother=enable
output_folder='/root/ttycsv.data/' #remember ending/
alarm_time=10

connection_type='tty'
input_tty='/dev/ttyUSB0'
################################################

#ensure logging module is imported
try:
  import logging
except ModuleNotFoundError:
  exception_return = sys.exc_info()
  print(exception_return)
  print("Generally installed with all python installation. Refere to python documentation.")
  quit()

#ensure that log file is created/available
try:
  logging.basicConfig(filename=logfile_name,level=logging.DEBUG)
  print("See log at {}".format(logfile_name))
except FileNotFoundError:
  exception_return = sys.exc_info()
  print(exception_return)  
  print("{} can not be created. Folder donot exist? No permission?".format(logfile_name))
  quit()

#import other modules
try:
  import signal
  import datetime
  import time
except ModuleNotFoundError:
  exception_return = sys.exc_info()
  logging.debug(exception_return) 
  logging.debug("signal, datetime and serial modules are required. Install them")
  quit()   

#import serial or socket
if(connection_type=='tty'):
  try:
    import serial 
  except ModuleNotFoundError:
    exception_return = sys.exc_info()
    logging.debug(exception_return) 
    logging.debug("serial module (apt install python3-serial) is required. Install them")
    quit()   

def signal_handler(signal, frame):
  global x									#global file open
  global byte_array							#global array of byte
  global cur_file
  logging.debug('Alarm stopped')
  sgl='signal:'+str(signal)
  logging.debug(sgl)
  logging.debug(frame)
  
  try:
    if x!=None:
      x.write(''.join(byte_array))			#write to file everytime LF received, to prevent big data memory problem
      x.close()
      cur_file=get_filename()
      x=open(cur_file,'w')
  except Exception as my_ex:
    logging.debug(my_ex)
    
  byte_array=[]							#empty array      
  logging.debug('Alarm.... <EOT> NOT received. data may be incomplate')

def get_filename():
  dt=datetime.datetime.now()
  return output_folder+dt.strftime("%Y-%m-%d-%H-%M-%S-%f")

def get_port():
  if(connection_type=='tty'):
    try:
      port = serial.Serial(input_tty, baudrate=9600)
      return port
    except:
      exception_return = sys.exc_info()
      logging.debug(exception_return)
      logging.debug('is tty really existing? Quiting')
      quit()
  
def my_read(port):
  if(connection_type=='tty'):
    return port.read(1)
def my_write(port,byte):
  if(connection_type=='tty'):
    return port.write(byte)
#main loop##########################
if log==0:
  logging.disable(logging.CRITICAL)

signal.signal(signal.SIGALRM, signal_handler)
port=get_port()

byte_array=[]								#initialized to ensure that first byte can be added
cur_file=get_filename()
x=open(cur_file,'w')

while True:
  byte=my_read(port)
  if(byte==b''):
    logging.debug('<EOF> reached. Connection broken: details below')
    #<EOF> never reached with tty unless the device is not existing)
  else:
    byte_array=byte_array+[chr(ord(byte))]	#add everything read to array, if not EOF. EOF have no ord
    logging.debug(ord(byte))
    signal.alarm(alarm_time)
    logging.debug('one byte obtained. Alarm started to receive other data')

  if(byte==b'\x0a'):
    signal.alarm(0)
    logging.debug('Alarm stopped. LF received')
    try:
      x.write(''.join(byte_array))			#write to file everytime LF received, to prevent big data memory problem
      byte_array=[]							#empty array
      cur_file=get_filename()
      x=open(cur_file,'w')

    except Exception as my_ex:
      logging.debug(my_ex)
      logging.debug('Tried to write/open to a non-existant file??')
    logging.debug('<LF> received. array written to file. byte_array zeroed')

    try:
      if x!=None:
        x.close()
    except Exception as my_ex:
      logging.debug(my_ex)
