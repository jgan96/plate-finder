# scrapes findbyplate.com for ny plates and partials

from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from random import randint
import pandas as pd
import time
import csv

rateLimit = 15
queries = 0
initials = 'ABCDEFGHJ'
letters = 'ABCDEFGHJKLMNPRSTUVWXYZ' # no i, o, q
numbers = range(10)

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
    
    return v

def getVehicle(plate):
    url = 'https://findbyplate.com/US/NY/' + plate + '/'
    response = simple_get(url)
    vehicle = ['0000', 'Make', 'Model']
    vehInfo = []   
    global queries
    global rateLimit
    
    # use randint in rate limiting to allow for a more "human" approach
    if queries < randint(1, rateLimit):
        queries += 1
    else:
        time.sleep(randint(1, 6))
        queries = 0

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

def aggregateDf(vehicle, plate):
    v = {'plate': [plate], 'year': vehicle[0], 'make': vehicle[1], 'model': vehicle[2]}
    aggregate = pd.DataFrame(data=v)   
    print(aggregate)
    return aggregate

def listToQuery(pList, showDNE = False):
    queries = pd.DataFrame(columns=['plate', 'year', 'make', 'model'])
    
    for p in pList:
        print("plate: " + p)
        df = aggregateDf(getVehicle(p), p)
        if df['year'][0] == "0000" and showDNE == False:
            continue
        else:
            queries = pd.concat([queries, df], ignore_index = True)
            
            try:
                queries.to_csv('tmp.csv')
            except PermissionError:
                print("Permission error while writing to tmp.csv. Is the file open?")
    return queries

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
    hits = pd.DataFrame(columns=['plate', 'year', 'make', 'model'])

    s = input("Enter NYS plate numbers, separated by commas. Use * for unknowns:" ) # hx*459*,hxm4595,hvc2922, HAU8673
    
    plates = s.replace(' ', '')
    plates = plates.split(',')
    
    for p in plates:
        if p.count('*') == 0:
            hits = pd.concat([hits, aggregateDf(getVehicle(p), p)], ignore_index=True)
        elif p.count('*') > 0 and p.count('*') <= 4: # dont try plates with more than 4 missing characters, waste of time
            plateList = getPartialsList(plates)
            try:
                csvfile = "querylist.csv"
                with open(csvfile, "w") as output:
                    writer = csv.writer(output, lineterminator='\n')
                    for p in plateList:
                        writer.writerow([p]) 
            except PermissionError:
                print("Permission error while writing to querylist.csv. Is the file open?")
            finally:
                #hits = pd.concat([hits, listToQuery(plateList, True)], ignore_index=True)
                hits = pd.concat([hits, listToQuery(plateList)], ignore_index=True)
        else:
            print(p + " is missing too many characters!")
        print(hits)
    try:
        hits.to_csv('plates.csv')
    except PermissionError:
        print("Permission error while writing to plates.csv. Is the file open?")
    print("Search completed! Results in plates.csv.")