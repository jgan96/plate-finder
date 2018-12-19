# https://api.howsmydrivingny.nyc/api/v1/?plate=
# ie plate=NY:HVC2922

# return df with plates with violations in each borough

import pandas as pd
import requests as r
import json
from pandas.io.json import json_normalize
import time

rateLimit = 1000
queries = 0
initials = 'ABCDEFGHJ'
letters = 'ABCDEFGHJKLMNPRSTUVWXYZ' # no i, o, q
numbers = range(10)

def aggregateDf(viols):
    bk = 0
    bx = 0
    qns = 0
    si = 0
    mhn = 0
    unk = 0
    total = 0
    make = viols['vehicle_make'][0]
    color = viols['vehicle_color'][0]
    year = viols['vehicle_year'][0]
    plate = viols['plate_id'][0]
    
    #print(viols)
    
    for index, v in viols.iterrows():
        if v['violation_county'] == 'Brooklyn':
            bk += 1
        elif v['violation_county'] == 'Bronx':
            bx += 1
        elif v['violation_county'] == 'Queens':
            qns += 1
        elif v['violation_county'] == 'Staten Island':
            si += 1
        elif v['violation_county'] == 'Manhattan':
            mhn += 1
        else:
            unk += 1
        
    total = bk + bx + qns + si + mhn + unk
    vehicle = {'plate': [plate], 'make': make, 'color': color, 'year': year, 'total violations': total, 'brooklyn': bk, 'bronx': bx, 'queens': qns, 'staten island': si, 'manhattan': mhn, 'unknown': unk}
    aggregate = pd.DataFrame(data=vehicle)   
    print(aggregate)
    return aggregate
    
def parseVehicle(d):
    df = json_normalize(d['data'], errors='ignore')
    #print(df)
    #print(df["vehicle.violations"])
    #print(df['vehicle.violations_count'])
    
    # check if plate is valid (if tickets exist)
    if df['vehicle.violations_count'].all():
        print("EXISTS")
        for v in df["vehicle.violations"]:
            vehicledf = pd.read_json(json.dumps(v))
            return aggregateDf(vehicledf)         
    else:
        print("DNE")
        vehicledf = {'plate': df['vehicle.plate'], 'make': "Plate not found!"}
        return pd.DataFrame(data=vehicledf)

def query(license):
    global queries
    global rateLimit
    parameters = {"plate": "ny:" + license}
    
    if queries < rateLimit:
        queries += 1
    else:
        time.sleep(3)
        queries = 0
        
    response = r.get("https://api.howsmydrivingny.nyc/api/v1/", params=parameters)
    data = response.json()
    print(response.status_code)
    #print(response.content)
    #print(data)
    return parseVehicle(data)

def listToQuery(pList, showDNE = False):
    queries = pd.DataFrame(columns=['plate', 'make', 'color', 'year', 'total violations', 'brooklyn', 'bronx', 'queens', 'staten island', 'manhattan', 'unknown'])
    
    for p in pList:
        print("plate: " + p)
        df = query(p)
        if df['make'][0] == "Plate not found!" and showDNE == False:
            continue
        else:
            queries = pd.concat([queries, df], ignore_index = True)
            
            try:
                queries.to_csv('tmp.csv')
            except PermissionError:
                print("Permission error while writing to tmp.csv. Is the file open?")
            #finally:
                #continue
            
    return queries

def getPartialsList(license): # where license is a list
    # https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_New_York
    # first character can be F, H, J
    # second and third character can be A-Z (but not I, O, Q?)
    # last four characters can be 0-9
    
    # recursively iterate through possible matches, ie
    # partials(H*C2**2)
    # partials(HAC2**2)
    # partials(HAC20*2)
    # partials(HAC2002)
    # return query(HAC2002)
    
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
        #print(p)
        
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
            #print("letters")
            pos = p.find('*')
            for l in letters:
                plateList.append(p[0:pos] + l + p[pos + 1:])
                #print(plateList)
            #print("end letters")
            plateList = getPartialsList(plateList)
            #list = [p[0:pos] + "%s" + p[pos + 1:] % (l) for l in letters]
            #partials([p[0:pos] + "%s" + p[pos + 1:] % (l) for l in letters])
        elif p[3] == '*' or p[4] == '*' or p[5] == '*' or p[6] == '*':
            #print("numbers")
            pos = p.find('*')
            for n in numbers:
                plateList.append(p[0:pos] + str(n) + p[pos + 1:])
                #print(plateList)
            #print("end numbers")
            plateList = getPartialsList(plateList)
            #list = [p[0:pos] + "%s" + p[pos + 1:] % (n) for n in numbers]
            #partials([p[0:pos] + "%s" + p[pos + 1:] % (str(n)) for n in numbers])
        else:
            #print("appending...")
            plateList.append(p)
    print(plateList)
    return plateList

if __name__ == "__main__":
    hits = pd.DataFrame(columns=['plate', 'make', 'color', 'year', 'total violations', 'brooklyn', 'bronx', 'queens', 'staten island', 'manhattan', 'unknown'])

    s = input("Enter NYS plate numbers, separated by commas. Use * for unknowns:" ) # hx*459*,hxm4595,hvc2922, HAU8673
    
    plates = s.replace(' ', '')
    plates = plates.split(',')
    
    for p in plates:
        if p.count('*') == 0:
            hits = pd.concat([hits, query(p)], ignore_index=True)
        elif p.count('*') > 0 and p.count('*') <= 4: # dont try plates with more than 4 missing characters, waste of time
            plateList = getPartialsList(plates)
            hits = pd.concat([hits, listToQuery(plateList)], ignore_index=True)
        else:
            print(p + " is missing too many characters!")
        print(hits)
    try:
        hits.to_csv('vehicles.csv')
    except PermissionError:
        print("Permission error while writing to vehicles.csv. Is the file open?")
    print("Search completed! Results in vehicles.csv.")

    