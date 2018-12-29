def query(license):
    u = input("enter username: ")
    
    parameters = {"RegistrationNumber": license, "state": "NY", "username": u}
        
    response = r.get("http://regcheck.org.uk/api/reg.asmx/CheckUSA", params=parameters)
    data = response.json()
    print(response.status_code)
    print(response.content)
    print(data)

if __name__ == "__main__":
    s = input("Enter NYS plate numbers, separated by commas. Use * for unknowns:" ) # hx*459*,hxm4595,hvc2922, HAU8673
    
    plates = s.replace(' ', '')
    plates = plates.split(',')
    
    for p in plates:
        query(p)