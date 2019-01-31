#!/usr/bin/python

### Modules ###
import sys
import json
import time
import datetime
import Adafruit_DHT
import RPi.GPIO
import requests

### Variables ###

# base URL of back-end server
destURL = 'http://localhost:1337'
# how often to poll the sensor in seconds
pollingRate = 2

#### Functions ####

# GET settings data from destURL
def getData():
    try:
        res = requests.get(destURL + '/get-settings-data')
        updateSettings(res)
        # if response contains an HTTP error, raise it
        res.raise_for_status()
    # catch HTTP error responses
    except requests.exceptions.HTTPError as err:
        handleHTTPError(err)
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
def postData(data):
    headers = {'content-type': 'application/json'}
    try:
        res = requests.get(destURL + '/add-data', data = data, headers = headers)
        res.raise_for_status()
    except requests.exceptions.HTTPError as err:
        handleHTTPError(err)
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
def handleHTTPError(err):
    # TODO print error
    print('HTTP Error {}'.format(err))
    # TODO write error to log file
    # TODO handle error

# Change settings such as polling rate
def updateSettings(res):
    # TODO
    # pollingRate = res.data.rate
    print(res.text)

### Main ###

# Enable pull-up resistor for accurate temp/humidity readings
# TODO test, since only need a 4.7K - 10KΩ resistor between the 
# Data pin and the VCC pin, but internal pull-up resistor is
# 50 KΩ - 65 KΩ according to https://elinux.org/RPi_Low-level_peripherals#Internal_Pull-Ups_.26_Pull-Downs
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# TODO set sensible delay; do not poll more often than every 2 seconds (see datasheet)
# https://stackoverflow.com/questions/474528/what-is-the-best-way-to-repeatedly-execute-a-function-every-x-seconds-in-python
while True:

    humidity, temperature = Adafruit_DHT.read_retry(11, 4)

    print('Temp: {0:0.1f}\N{DEGREE SIGN}C  Humidity: {1:0.1f}%'.format(temperature, humidity))

    # create JSON object from Python dict
    # TODO test which time gives UNIX timestamp/best result
    print(int(time.time()))
    print(datetime.datetime.now())
    data = { 
        'time': int(time.time()), 
        'temperature': temperature,
        'humidity': humidity
    }
    json_data = json.dumps(data)

    # TODO periodically post results to server over HTTP
    # OR post results to server all the time
    # OR save up a lot of results then try to send to server
    # last one could be bad if server is unavailable, may lead to backlog  

    # send data to back-end 
    postData(json_data)
