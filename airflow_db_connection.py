import requests
from requests.auth import HTTPBasicAuth

url = "http://localhost:8080/api/v1/connections"
auth = HTTPBasicAuth('admin', 'admin')  # Use your Airflow credentials
headers = {"Content-Type": "application/json"}

data = {
    "connection_id": "connection_postgres",
    "conn_type": "postgres",
    "host": "postgres",
    "login": "airflow",
    "password": "airflow",
    "schema": "properties",
    "port": 5432
}

response = requests.post(url, json=data, auth=auth, headers=headers)

if response.status_code == 200:
    print("Connection created successfully")
else:
    print(f"Failed to create connection: {response.text}")
