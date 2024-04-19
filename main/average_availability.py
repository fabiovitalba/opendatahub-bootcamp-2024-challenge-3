import requests
from datetime import datetime, timezone
import time

def print_response_details(current_step, response):
    """Helper function to print the details of the response."""
    print(f"Step: {current_step}")
    print(f"Status Code: {response.status_code}")
    content_type = response.headers.get('Content-Type', '')

    if 'json' in content_type:
        try:
            response_json = response.json()
            print(f"Response JSON Body: {response_json}\n")
        except ValueError:
            print("Response JSON is not in valid format.\n")
    elif 'text/plain' in content_type:
        print(f"Response Text Body: {response.text}\n")
    else:
        print("Response body empty\n")

def get_auth_token():
    """Get the authentication token"""
    # Define the URL and the payload for the auth request
    auth_url = "https://auth.opendatahub.testingmachine.eu/auth/realms/noi/protocol/openid-connect/token"
    payload = {
        'grant_type': 'client_credentials',
        'client_id': 'odh-mobility-datacollector-development',
        'client_secret': '7bd46f8f-c296-416d-a13d-dc81e68d0830',
        'scope': 'openid'
    }
    
    # Headers for the auth request
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Make the POST request to get the auth token
    response = requests.post(auth_url, data=payload, headers=headers)

    # If the request was successful, return the access token
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        # If not successful, print the error and return None
        print(f"Error getting auth token: {response.text}")
        return None

def create_provenance(host, auth_token, prn, prv, uuid, data_collector, data_collector_version, lineage):
    """Synchronize (Create / Update) Provenance"""
    url = f"{host}/json/provenance?prn={prn}&prv={prv}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }

    payload = {
        "uuid": uuid,
        "dataCollector": data_collector,
        "dataCollectorVersion": data_collector_version,
        "lineage": lineage
    }

    response = requests.post(url, json=payload, headers=headers)
    return response

def sync_stations(host, auth_token, station_type, stations_data, prn=None, prv=None, syncState=True, onlyActivation=False):
    """Synchronize (Create / Update) stations information."""
    url = f"{host}/json/syncStations/{station_type}?prn={prn}&prv={prv}&syncState={syncState}&onlyActivation={onlyActivation}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }
    response = requests.post(url, json=stations_data, headers=headers)
    return response

def sync_data_types(host, auth_token, data_types, prn=None, prv=None):
    """Synchronize (Create / Update) data types information."""
    url = f"{host}/json/syncDataTypes?prn={prn}&prv={prv}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }
    response = requests.post(url, json=data_types, headers=headers)
    return response

def push_records(host, auth_token, station_type, data_tree, prn=None, prv=None):
    url = f"{host}/json/pushRecords/{station_type}?prn={prn}&prv={prv}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }

    response = requests.post(url, json=data_tree, headers=headers)
    return response

def get_charging_stations(host, station_type):
    url = f"{host}/{station_type}?limit=200&offset=0&shownull=false&distinct=true"
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    return response

def get_charging_stations_status(host, station_type, from_date, to_date, station_id):
    url = f"{host}/{station_type}/%2A/{from_date}/{to_date}?limit=-1&offset=0&shownull=false&distinct=true&where=sactive.eq.true,scode.in.%28%22{station_id}%22%29&timezone=UTC" #
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response
    else:
        return []
    
def upsert_datatype(host, auth_token, prn, prv, data_type_name, data_type_unit):
    #3 Sync Data Types
    data_types = [
        {
            "name": data_type_name,
            "unit": data_type_unit,
            "rtype": "mean",
            "description": "charging data",
            "period": 600,
            "metadata": {
                "details": "xxx"
            }
        }
    ]

    return sync_data_types(host, auth_token, data_types, prn, prv)

def upsert_station(host, auth_token, origin, station_type, station_id, station_name, station_lat, station_long, station_elev, station_municipality):
    #4 Sync Stations
    stations_data = [
        {
            "id": station_id,
            "stationType": station_type,
            "name": station_name,
            "latitude": station_lat,
            "longitude": station_long,
            "elevation": station_elev,
            "origin": origin,
            "municipality": station_municipality,
            "metaData": {
                "details": "xxx"
            }
        }
    ]

    return sync_stations(host, auth_token, station_type, stations_data)

def add_station_data(host, auth_token, provenance_id, station_type, station_id, measure_timestamp, measure_type, measure_value):
    #5 Push Record
    data_tree = {
        "name": "(default)",
        "branch": {
            station_id: {
                "name": "(default)",
                "branch": {
                    measure_type: {
                        "name": "(default)",
                        "branch": {},
                        "data": [
                            {
                                "timestamp": measure_timestamp,
                                "value": measure_value,
                                "period": 100,
                                "_t": "it.bz.idm.bdp.dto.SimpleRecordDto"
                            }
                        ]
                    }
                },
                "data": []
            }
        },
        "data": [],
        "provenance": provenance_id
    }

    return push_records(host, auth_token, station_type, data_tree)

from datetime import datetime, timedelta

def get_availability_percentage(host, station_name, last_hours):
    # API info
    station_type = "EChargingStation"

    
    # Define the time range for the last hour
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=last_hours)
    
    # Format the timestamps
    from_date = start_time.strftime("%Y-%m-%dT%H:%M:%S")
    to_date = end_time.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Call the API to get charging station status
    response = get_charging_stations_status(host, station_type, from_date, to_date, station_name)
    
    if response.status_code == 200:
        data = response.json()['data']
        
        total_entries= 0
        available_entries = 0
        
        for entry in data:
            total_entries += 1
            mvalue = entry.get('mvalue')
            if mvalue > 0:
                available_entries += 1
        
        if total_entries > 0:
            availability_percentage = (available_entries / total_entries) * 100
            return availability_percentage
        else:
            return 0  # No data available
    else:
        return 0  # No data available
    
def get_all_charging_stations_names():
    url='https://mobility.api.opendatahub.com/v2/flat/EChargingStation/number-available/latest?select=scode&limit=-1&offset=0&where=sactive.eq.true&shownull=false&distinct=true'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()['data']
        names = [entry['scode'] for entry in data]
        return names
    else:
        print(f"Error fetching data for stations names: {response.status_code}")
        return None


def main():
    read_host = "https://mobility.api.opendatahub.com/v2/flat%2Cnode"
    write_host = "http://localhost:8081"
    station_type = "EChargingStation"
    origin = "SlowCharging"

    #1 Get the authentication token
    auth_token = get_auth_token()
    
    #2 Create Provenance
    if auth_token:
        prn = "SlowCharging"
        prv = "001"
        uuid = "null"
        data_collector = "TEST"
        data_collector_version = "1.0"
        lineage = origin

        response = create_provenance(write_host, auth_token, prn, prv, uuid, data_collector, data_collector_version, lineage)
        print_response_details("#2 Create Provenance",response)

        provenance_id = response.text
        response = upsert_datatype(write_host, auth_token, prn, prv, "availability", "%")
        print_response_details("#3 Sync Data Types", response)
        
        #response = upsert_station(write_host, auth_token, origin, station_type, "ASM_00000181", "MORI_01", 46.333, 11.356, 0, "Bolzano")
        #print_response_details("#4 Sync Stations", response)
        
        #response = add_station_data(write_host, auth_token, provenance_id, station_type, "ASM_00000181", 1668522653400, "availability", 80)
        #print_response_details("#5 Add data", response)
        # Navigate to 
        # # http://localhost:8082/flat,node
        # # http://localhost:8082/flat,node/EChargingStation/
        # # http://localhost:8082/flat,node/EChargingStation/*/latest
        
    results = []
    names = get_all_charging_stations_names()

    for name in names:
        upsert_station(write_host, auth_token, origin, station_type, name, "MORI_01", 46.333, 11.356, 0, "Bolzano")
        availability = get_availability_percentage(read_host, name, 1)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        results.append({'scode': name, 'availability': availability, 'timestamp': timestamp})
        response = add_station_data(write_host, auth_token, provenance_id, station_type, name, round(time.time() * 1000), "availability", availability)
        print(f"Station {name} available: {availability}%.")
        
    total_percentage = 0
    for result in results:
        total_percentage += result['availability']  # Corrected accessing 'availability' from each result

    average_availability = total_percentage / len(results)
    print(f"Average availability: {average_availability}%")

if __name__=="__main__":
    main()
