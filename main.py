import machine
import ujson
import umqttsimple
import ntptime

#not every pin is pwm enabled and duty => 40 - 115
#40 = counterClockWise
#115 = ClockWise
def sub_cb(topic, msg):
  print(topic, msg)
  if topic == b'ServoControl':
    #msg = "pin,readPin,duty,rep,ID"
    print(msg)
    #pin,readPin,duty,rep,ID = ['pin','readPin','duty','rep','ID']
    pin,readPin,duty,rep,ID = msg.decode("utf-8").split(",")
    #This function activates the servo and initializes test(pin,readPin,duty,rep,ID)
    toggleServo(int(pin),int(readPin),int(duty),int(rep),ID)

#Setup the mqtt client and topics subscribed
def connect_and_subscribe():
  global client_id, mqtt_server, topic_sub
  client = MQTTClient(client_id, mqtt_server)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe("ServoControl")
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.reset()

#Function to control servo
def toggleServo(pin,readPin,duty,rep,ID):
    #Set current time using server ping
    ntptime.host = "3.north-america.pool.ntp.org"
    ntptime.settime()
    #Create the database dict
    data = {
        'ID': ID,
        'date': str(time.localtime()),
        'OkReads' : 0,
        'SuccessRate' : 1
        }
    #Set PWM pin on ESP8266
    p4 = machine.Pin(pin)
    servo = machine.PWM(p4,freq=50)
    #Set reader pin
    ReadPin = machine.Pin(readPin, machine.Pin.IN, machine.Pin.PULL_UP)
    reads = 0
    #Loop over every rep, reading for value
    for i in range(0,rep):
        start =time.time()
        while ReadPin.value != 0:
            # duty for servo is between 40 - 115
            servo.duty(duty)
        end = time.time()
        #Evaluate if its good read with time
        if (end-start) < 200:
            servo.duty(0)
            reads+=1
        if (end-start) > 1000:
            reads = "Timeout:FailedTest"
            return reads
    """        
    for i in range(1,rep):
        #reading pin rep
        if ReadPin.value() == 0:
            reads+=1
            print(reads)
        #take another read in 3 seconds
        time.sleep(3)
    """        
    data['OkReads'] = reads
    data['SuccessRate'] = reads / rep * 100
    #Write JSON with results
    with open("Servo1_results.json","w") as file:
        print(data)
        data2 = ujson.dumps(data)
        file.write(data2)
#        print(type(data))#dict
#        print(type(data2))#str
    #send information of results
    client.publish("Servo1", data2)
        
try:
  client = connect_and_subscribe()
  print("connected")
except OSError as e:
  restart_and_reconnect()

#Stay-alive function
while True:
  try:
    client.check_msg()
    #print("im here")
    if (time.time() - last_message) > message_interval:
      msg = b'Servo1: %d' % counter
      print("ok")
      client.publish("Servo1", msg)
      last_message = time.time()
      counter += 1
      print("ok2")
  except OSError as e:
    print("fuck")
    restart_and_reconnect()