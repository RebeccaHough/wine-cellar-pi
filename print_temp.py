#!/usr/bin/python

### Modules ###
import sys
import json
import time
import datetime
import os
import Adafruit_DHT
import RPi.GPIO as GPIO
import requests

### Variables ###

# Base URL of back-end server
dest_URL = 'https://62195c9b.ngrok.io'
# Default settings
# sensorPollingRate and sendFrequency are in seconds
# sendFrequency describes how often the Pi should attempt to post its data to the back-end
settings = {
    "collectTemperature": True,
    "collectHumidity": True,
    "sensorpollingRate": 60, # every minute
    "sendFrequency": 1200 # every 20 minutes
}
# JSON array of objects to store measurements
json_data_array = json.dumps([])
# Path to save file
save_file = 'save_temp.json'

### Functions ###

# GET settings data from dest_URL
def get_settings():
    try:
        res = requests.get(dest_URL + '/get-settings-data')
        # convert res to python dict
        res = json.loads(res)
        print('Server responded with {}'.format(res))
        # if response contains an HTTP error, raise it and enter appropriate catch block
        res.raise_for_status()
        # attempt to update settings
        if(update_settings(res)):
            # return true if settings update succeeds
            return True
        else: 
            # return false if settings update fails
            return False
    # catch HTTP error responses
    except requests.exceptions.HTTPError as err:
        print('HTTP Error {}'.format(err))
    # catch connection errors
    except requests.exceptions.ConnectionError as errc:
        print('Error connecting {}'.format(errc))
    # catch timeout errors
    except requests.exceptions.Timeout as errt:
        print('Timed out {}'.format(errt))
    # catch-all for non-http status code errors  
    except requests.exceptions.RequestException as e:
        print('Request exception {}'.format(e)
    except ValueError:
        print('JSON parse failed. Could not check or update settings.')
    # return false if any errors occur
    return False

# POST JSON data to URL in destURL
def post_data(data):
    headers = {'content-type': 'application/json'}
    try:
        res = requests.get(dest_URL + '/add-data', data = data, headers = headers)
        res = json.loads(res)
        print('Server responded with {}'.format(res))
        res.raise_for_status()
        return True
    except requests.exceptions.HTTPError as err:
        print('HTTP Error {}'.format(err))
    except requests.exceptions.ConnectionError as errc:
        print('Error connecting {}'.format(errc))
    except requests.exceptions.Timeout as errt:
        print('Timed out {}'.format(errt))
    except requests.exceptions.RequestException as e:
        print('Request exception {}'.format(e)
    except ValueError:
        print('JSON parse failed. Could not check or update settings.')
    return False

# Update settings using server response (as a python dict)
def update_settings(res):
    try:
        data = res.data
        # update settings if they dont match
        if(data != settings):
            data = settings
            print('Succesfully updated settings.')
        else:
            print('Settings unchanged.')
        return True
    except ValueError as e:
        print('Failed to update settings. {}'.format(e))
    except Exception as e:
        print('Failed to update settings. {}'.format(e))
    return False

# Append the JSON object in the second argument to the JSON array in the first argument
def append_to_json_array(arr, to_append):
    # convert to python
    arr_as_dict = json.loads(arr)
    to_append_as_obj = json.loads(to_append)
    # append to list
    arr_as_dict.append(to_append_as_obj)
    # return JSON
    return json.dumps(arr_as_dict)

# Read file
def read_file(filepath):
    try:
        # open in read mode
        with open(filepath, 'r') as f:
            data = f.read()
            data = json.dumps(data)
        return data
    except FileNotFoundError as f:
        print('Could not read save file. {}'.format(f))
    except ValueError:
        print('JSON parse failed on read file attempt.')
    return None

# Save data to file, overwriting what is there
def write_to_file(filepath, data):
    try:
        # open in write mode
        with open(filepath, 'w') as f:
            f.write(data)
    except FileNotFoundError as f:
        print('Could not write save data to file. {}'.format(f))

# Delete file
def delete_file(filepath):
    try:
        os.remove(filepath) 
        print('Deleted temporary save file.')
    except FileNotFoundError:
        # continue

### Main ###

# Set pin numbering mode to GPIO numbering (e.g. GPIO4 = pin 7) 
GPIO.setmode(GPIO.BCM)  

# Enable pull-up resistor for accurate temp/humidity readings
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

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

        # every nth second
        if(current_time % settings.sendFrequency == 0):
            # check settings for update
            get_settings()
            # send data to back-end 
            if(post_data(json_data_array)):
                print('Data successfully sent to back-end.')
                # clear data array
                json_data_array = json.dumps([])
                # delete ('clear') save file if it exists
                delete_file(save_file);
            else: 
                print('Failed to send data to back-end. Next retry will be in 10 minutes.')
                print('Saving data to file.')
                # read save file
                data = read_file(save_file)
                # if save has content
                if(data != None)
                    # append to it
                    data = append_to_json_array(data, json_data_array)
                write_to_file(save_file, data)
        
        # Wait t seconds between reads (if the reads are consecutively succesful; else
        # the wait will be up to 30s longer)
        time.sleep(settings.sensorPollingRate)
    else:
        print('Sensor read failed. Please check sensor connection.')
