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
import threading
import math

### Variables ###

# Base URL of back-end server
dest_URL = 'https://f985edd6.ngrok.io'
# Default settings
# sensorPollingRate and sendFrequency are in seconds
# sendFrequency describes how often the Pi should attempt to post its data to the back-end
settings = {
    "collectTemperature": True,
    "collectHumidity": True,
    "sensorPollingRate": 60, # every minute
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
        res = requests.get(dest_URL + '/data-collection-settings')
        # Convert res to python dict
        body = res.json()
        print('Server responded with {}'.format(body))
        # If response contains an HTTP error, raise it and enter appropriate catch block
        res.raise_for_status()
        # Attempt to update settings
        if(update_settings(body)):
            # Return true if settings update succeeds
            return True
        else: 
            # Return false if settings update fails
            return False
    # Catch HTTP error responses
    except requests.exceptions.HTTPError as err:
        print('HTTP Error {}'.format(err))
    # Catch connection errors
    except requests.exceptions.ConnectionError as errc:
        print('Error connecting {}'.format(errc))
    # Catch timeout errors
    except requests.exceptions.Timeout as errt:
        print('Timed out {}'.format(errt))
    # Catch-all for non-http status code errors  
    except requests.exceptions.RequestException as e:
        print('Request exception {}'.format(e))
    except ValueError:
        print('JSON parse failed. Could not check or update settings.')
    # Return false if any errors occur
    return False

# POST JSON data to URL in destURL
def post_data(data):
    headers = {'content-type': 'application/json'}
    try:
        res = requests.post(dest_URL + '/database', data = data, headers = headers)
        body = res.json()
        print('Server responded with {}'.format(body))
        res.raise_for_status()
        return True
    except requests.exceptions.HTTPError as err:
        print('HTTP Error {}'.format(err))
    except requests.exceptions.ConnectionError as errc:
        print('Error connecting {}'.format(errc))
    except requests.exceptions.Timeout as errt:
        print('Timed out {}'.format(errt))
    except requests.exceptions.RequestException as e:
        print('Request exception {}'.format(e))
    except ValueError:
        print('JSON parse failed. Could not post data to URL.')
    return False

# Update settings using server response (as a python dict)
def update_settings(res):
    global settings
    try:
        data = res['data']
        # Update settings if they dont match
        if(data != settings):
            settings = data
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
    # Convert to python
    if(arr == None):
        return to_append
    arr_as_list = json.loads(arr)
    to_append_as_python = json.loads(to_append)
    # For debugging
    # print(arr_as_list)
    # print(type(arr_as_list))
    # print(to_append_as_python)
    # print(type(to_append_as_python))
    # Append to list
    if(type(to_append_as_python) is list):
        # Add all elements in second list to first list (i.e. don't add the entire list as
        # an element of the first list
        arr_as_list.extend(to_append_as_python)
    else:   
        arr_as_list.append(to_append_as_python)
    # Return JSON
    return json.dumps(arr_as_list)

# Read file
def read_file(filepath):
    try:
        # Open in read mode
        with open(filepath, 'r') as f:
            data = f.read()
        return data
    except FileNotFoundError as f:
        print('No previous save file exists. {}'.format(f))
    except ValueError:
        print('JSON parse failed on read file attempt.')
    return None

# Save data to file, overwriting what is there
def write_to_file(filepath, data):
    try:
        # Open in write mode
        print('Writing to new or opened file {}.'.format(filepath))
        with open(filepath, 'w') as f:
            f.write(data)
        return True
    except FileNotFoundError as f:
        print('Could not write save data to file. {}'.format(f))
        return False

# Delete file
def delete_file(filepath):
    try:
        os.remove(filepath) 
        print('Deleted temporary save file.')
    except FileNotFoundError:
        # Continue
        pass

# Schedule periodic atttempts to send data to the back-end. If the send fails, save the data to file
def send_or_save_data():
    global json_data_array
    
    # Check settings for update
    get_settings()
    
    # Get data from existing save file if it exists
    data = read_file(save_file)
    # If save has content
    if(data != ''):
        # Append to it
        json_data_array = append_to_json_array(data, json_data_array)
        
    # Send data to back-end 
    if(post_data(json_data_array)):
        print('Data successfully sent to back-end.')
        # Clear data array
        json_data_array = json.dumps([])
        # Delete ('clear') save file if it exists
        delete_file(save_file);
    else: 
        print('Failed to send data to back-end. Next retry will be in {} minutes.'.format((settings['sendFrequency'] / 60)))
        print('Saving data to file.')
        # Attempt to save to file
        if(write_to_file(save_file, json_data_array)):
            # If save successful, clear data array
            json_data_array = json.dumps([])
    
    # Schedule next send
    threading.Timer(settings['sendFrequency'], send_or_save_data).start()


### Main ###

# Set pin numbering mode to GPIO numbering (e.g. GPIO4 = pin 7) 
GPIO.setmode(GPIO.BCM)  

# Enable pull-up resistor for accurate temp/humidity readings
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# set flag
first = True

while True:
    # Try to get a sensor reading. The read_retry method which will retry up to 15 times
    # (by default) to get a sensor reading (waiting 2 seconds between each retry)
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 4)

    if humidity is not None and temperature is not None:
        # Log humidity and temperature along with human-readable time
        print('Time: {0} Temp: {1:0.1f}\N{DEGREE SIGN}C  Humidity: {2:0.1f}%'.format(datetime.datetime.now(), temperature, humidity))

        # Get current time as UNIX timestamp
        current_time = time.time()
        # Get rid of decimals
        current_time = math.trunc(current_time)

        # Create JSON object from Python dictionary
        data = { 
            'time': current_time, 
            'temperature': temperature,
            'humidity': humidity
        }
        json_data = json.dumps(data)

        # Append to array of all measurements
        json_data_array = append_to_json_array(json_data_array, json_data)

        # If first run through while loop, set flag and start data-sending function
        if(first):
            first = False
            # Roughly every settings.sendFrequency seconds, attempt to send data to back-end
            send_or_save_data()
        
        # Wait t seconds between reads (if the reads are consecutively succesful; else
        # the wait will be up to 30s longer)
        time.sleep(settings['sensorPollingRate'])
    else:
        print('Sensor read failed. Please check sensor connection.')
