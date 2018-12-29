# scrapes findbyplate.com

from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import pandas as pd
import requests as r
import json
from pandas.io.json import json_normalize
import time
import csv

def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None


def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('html') > -1)


def log_error(e):
    """
    It is always a good idea to log errors. 
    This function just prints them, but you can
    make it do anything.
    """
    print(e)
    
def parseVehicle(vehicle):
    v = vehicle.split(' ')
    #print(v)
    
    #vehicleInfo = {'plate': [plate], 'make': make, 'color': color, 'year': year,
    return v

def getVehicle(plate):
    url = 'https://findbyplate.com/US/NY/' + plate + '/'
    response = simple_get(url)
    vehicle = ['0000', 'Make', 'Model']
    vehInfo = []

    if response is not None:
        html = BeautifulSoup(response, 'html.parser')
        
        for h2 in html.select('h2'):
            #print(h2.get('class'))
            if h2.get('class') is not None: # KeyError: [attr] - Caused by accessing tag['attr'] when the tag in question doesn’t define the attr attribute. 
                for c in h2.get('class'):
                    if c == 'vehicle-modal':
                        #print(h2.text)
                        vehInfo = parseVehicle(h2.text)

    # Raise an exception if we failed to get any data from the url
    else:
        raise Exception('Error retrieving contents at {}'.format(url))
    
    # make sure we haven't parsed more than the year, make, and model of the vehicle    
    #finally:
    for i in range(len(vehInfo)):
        if i < 3:
            vehicle[i] = vehInfo[i]
            
    return vehicle

def getPartialsList(license): # where license is a list
    # https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_New_York
    # first character can be F, H, J
    # second and third character can be A-Z (but not I, O, Q?)
    # last four characters can be 0-9
    
    # recursively iterate through possible matches, ie
    # getPartialsList(H*C2**2)
    # getPartialsList([HAC2**2, HBC2**2, ..., HZC2**2])
    # getPartialsList([HAC20*2, HAC21*2, ..., HZC29*2])
    # getPartialsList([HAC2002, HAC2012, ..., HZC2992])
    # return [HAC2002, HAC2012, ..., HZC2992]
    
    global initials
    global letters
    global numbers
    plateList = []

    '''
    plates = ["G%sS-8%s%s5" % (l, n1, n2) 
     for n1 in numbers 
     for n2 in numbers
     for l in letters]
    '''

    for p in license:
        if p[0] == '*':
            #print("initials")
            #plateList.append()
            for i in initials:
                plateList.append(i + p[1:])
                #print(plateList)
            #print("end initials")
            plateList = getPartialsList(plateList)
            #list = ["%s" + p[1:] % (i) for i in initials]      
            #partials(["%s" + p[1:] % (i) for i in initials])
        elif p[1] == '*' or p[2] == '*':
            pos = p.find('*')
            for l in letters:
                plateList.append(p[0:pos] + l + p[pos + 1:])
            plateList = getPartialsList(plateList)
        elif p[3] == '*' or p[4] == '*' or p[5] == '*' or p[6] == '*':
            pos = p.find('*')
            for n in numbers:
                plateList.append(p[0:pos] + str(n) + p[pos + 1:])
            plateList = getPartialsList(plateList)
        else:
            plateList.append(p)
    print(plateList)
    return plateList

if __name__ == "__main__":
    car = getVehicle('GCL8673')
    print(car)
    car = getVehicle('MCS8775')
    print(car)