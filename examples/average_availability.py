import requests

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

def get_charging_stations(host, station_type):
    url = f"{host}/{station_type}?limit=200&offset=0&shownull=false&distinct=true"
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
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

def main():
    read_host = "https://mobility.api.opendatahub.com/v2/flat%2Cnode"
    write_host = "http://localhost:8082"
    station_type = "EChargingStation"
    origin = "MyCompany"

    #1 Get the authentication token
    auth_token = get_auth_token()
    
    #2 Create Provenance
    if auth_token:
        prn = "test"
        prv = "11111"
        uuid = "null"
        data_collector = "TEST"
        data_collector_version = "1.0"
        lineage = origin

        response = get_charging_stations(read_host,station_type)

        print_response_details("#2 Charging Stations",response)

if __name__=="__main__":
    main()
