#!/usr/bin/python

### Modules ###
import sys
import json
import time
import datetime
import Adafruit_DHT
import RPi.GPIO as GPIO
import requests

### Variables ###

# Base URL of back-end server
# 134.255.216.69
# 72.24.67.209:
# ATLANTA
dest_URL = 'http://atlanta:1337'
# How often to poll the sensor in seconds
polling_rate = 2
# json array to store measurements
json_data_array

#### Functions ####

# GET settings data from destURL
def get_settings():
    try:
        res = requests.get(dest_URL + '/get-settings-data')
        # if response contains an HTTP error, raise it
        res.raise_for_status()
        update_settings(res)
    # catch HTTP error responses
    except requests.exceptions.HTTPError as err:
        handle_HTTP_error(err)
    # catch connection errors
    except requests.exceptions.ConnectionError as errc:
        print('Error connecting')
        # TODO
    # catch timeout errors
    except requests.exceptions.Timeout as errt:
        print('Timed out')
        # TODO retry
    # catch-all for non-http status code errors  
    except requests.exceptions.RequestException as e:
        print(e)
        # TODO

# POST JSON data to URL in destURL
def post_data(data):
    headers = {'content-type': 'application/json'}
    try:
        res = requests.get(dest_URL + '/add-data', data = data, headers = headers)
        res.raise_for_status()
    except requests.exceptions.HTTPError as err:
        handle_HTTP_error(err)
    except requests.exceptions.ConnectionError as errc:
        print('Error connecting')
        # TODO
    except requests.exceptions.Timeout as errt:
        print('Timed out')
        # TODO retry
    except requests.exceptions.RequestException as e:
        print(e)
        # TODO

# Handle HTTP error responses
def handle_HTTP_error(err):
    # TODO print error
    print('HTTP Error {}'.format(err))
    # TODO write error to log file
    # TODO handle error

# Change settings such as polling rate
def update_settings(res):
    # convert res to python dict
    res = json.loads(res)
    print(res)
    new_polling_rate = int(res['collectionFrequency'])
    if(polling_rate != new_polling_rate):
        print('Polling rate updated to ' + new_polling_rate + 'seconds')
        polling_rate = new_polling_rate

# Append the JSON object in the second argument to the JSON array in the first argument
def append_to_json_array(arr, to_append):
    # convert to python
    arr_as_dict = json.loads(arr)
    to_append_as_obj = json.loads(to_append)
    # append to list
    arr_as_dict.append(to_append_as_obj)
    # return JSON
    return json.dumps(arr_as_dict)

### Main ###

# Set pin numbering mode to GPIO numbering (e.g. GPIO4 = pin 7) 
GPIO.setmode(GPIO.BCM)  

# Enable pull-up resistor for accurate temp/humidity readings
# TODO test, since only need a 4.7K - 10KOhm resistor between the 
# Data pin and the VCC pin, but internal pull-up resistor is
# 50 KOhm - 65 KOhm according to https://elinux.org/RPi_Low-level_peripherals#Internal_Pull-Ups_.26_Pull-Downs
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialise
json_data_array = json.dumps([])

while True:
    # Try to get a sensor reading. The read_retry method which will retry up to 15 times
    # (by default) to get a sensor reading (waiting 2 seconds between each retry)
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 4)

    if humidity is not None and temperature is not None:
        # Log humidity and temperature along with human-readable time
        print('Time: {0} Temp: {1:0.1f}\N{DEGREE SIGN}C  Humidity: {2:0.1f}%'.format(datetime.datetime.now(), temperature, humidity))

        # Get current time as UNIX timestamp
        current_time = int(time.time()),

        # Create JSON object from Python dictionary
        data = { 
            'time': current_time, 
            'temperature': temperature,
            'humidity': humidity
        }
        json_data = json.dumps(data)

        # append to array of all measurements
        json_data_array = append_to_json_array(json_data_array, json_data)

        # every 10th minute
        if(current_time % 600 == 0):
            # check settings for update
            get_settings()
            # send data to back-end 
            postData(json_data_array)
        
        # Wait t seconds between reads (if they are consecutively succesful; else
        # the wait will be up to 30s longer)
        time.sleep(polling_rate)
    else:
        print('Sensor read failed. Please check sensor connection.')
