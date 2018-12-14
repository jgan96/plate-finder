# https://api.howsmydrivingny.nyc/api/v1/?plate=
# ie plate=NY:GCS8775

# return df with plates with violations in each borough

import pandas as pd
import requests as r
import json
from pandas.io.json import json_normalize

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
    json_parsed = json.dumps(d['data'])
    #print(json_parsed)
    #df = json_normalize(d['data', ['vehicle', 'violations']], errors='ignore')
    df = json_normalize(d['data'], errors='ignore')
    #df = pd.read_json(json_parsed, orient="records")
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
    parameters = {"plate": license}
    response = r.get("https://api.howsmydrivingny.nyc/api/v1/", params=parameters)
    data = response.json()
    print(response.status_code)
    #print(response.content)
    #print(data)
    return parseVehicle(data)    

if __name__ == "__main__":
    hits = pd.DataFrame(columns=['plate', 'make', 'color', 'year', 'total violations', 'brooklyn', 'bronx', 'queens', 'staten island', 'manhattan', 'unknown'])
    #query("NY:GCS8775")
    #query("ny:hxm4595")
    
    s = input("Enter NYS plate numbers, separated by commas. Use * for unknowns:" ) # ny:hxm4595, NY:GCS8775
    
    plates = s.split(',')
    
    print(plates)
    
    for p in plates:
        hits = pd.concat([hits, query(p)], ignore_index=True)
        print(hits)
    hits.to_csv('vehicles.csv')
