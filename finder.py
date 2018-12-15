# https://api.howsmydrivingny.nyc/api/v1/?plate=
# ie plate=NY:HVC2922

# return df with plates with violations in each borough

import pandas as pd
import requests as r
import json
from pandas.io.json import json_normalize
import time

rateLimit = 26
queries = 0

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

def partials(license, df):
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
    if license[0] == '*':
        df = pd.concat([df, partials('F' + license[1:], df)], ignore_index=True)
        df = pd.concat([df, partials('H' + license[1:], df)], ignore_index=True)
        df = pd.concat([df, partials('J' + license[1:], df)], ignore_index=True)
    elif license[1] == '*' or license[2] == '*':
        pos = license.find('*')
        for i in range(ord('a'), ord('z')+1):
            # A-Z but not I, O, Q
            if ord('i') == i or ord('o') == i or ord('q') == i:
                continue
            else:
                df = pd.concat([df, partials(license[0:pos] + chr(i) + license[pos + 1:], df)], ignore_index=True)
    elif license[3] == '*' or license[4] == '*' or license[5] == '*' or license[6] == '*':
        pos = license.find('*')
        for i in range(0, 10):
            # 0-9
            df = pd.concat([df, partials(license[0:pos] + str(i) + license[pos + 1:], df)], ignore_index=True)
    else:
        print(license)
        return query(license)
    
    try:
        df.to_csv('tmp.csv')
    except PermissionError:
        print("Permission error while writing to tmp.csv. Is the file open?")
    finally:
        return df

if __name__ == "__main__":
    hits = pd.DataFrame(columns=['plate', 'make', 'color', 'year', 'total violations', 'brooklyn', 'bronx', 'queens', 'staten island', 'manhattan', 'unknown'])
    
    s = input("Enter NYS plate numbers, separated by commas. Use * for unknowns:" ) # hx*459*,hxm4595,hvc2922, HAU8673
    
    plates = s.replace(' ', '')
    plates = plates.split(',')
    
    print(plates)
    
    # dont try plates with more than 4 missing characters, waste of time
    
    for p in plates:
        if p.count('*') == 0:
            hits = pd.concat([hits, query(p)], ignore_index=True)
        elif p.count('*') > 0 and p.count('*') <= 4:
            hits = pd.concat([hits, partials(p, hits)], ignore_index=True)
        else:
            print(p + " is missing too many characters!")
        print(hits)
    try:
        hits.to_csv('vehicles.csv')
    except PermissionError:
        print("Permission error while writing to vehicles.csv. Is the file open?")
    print("Search completed! Results in vehicles.csv.")
