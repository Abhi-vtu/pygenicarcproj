import requests

url = "http://127.0.0.1:5000/tasks"
payload = {"title": "First test task", "description": "from python"}
resp = requests.post(url, json=payload)

print("Status:", resp.status_code)
print("Response:", resp.json())
