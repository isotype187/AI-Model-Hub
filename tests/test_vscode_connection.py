
import requests

print("Testing AI Hub bridge...")

r = requests.get(
    "http://127.0.0.1:8000/v1/models",
    timeout=10
)

assert r.status_code == 200

data = r.json()

print("Models detected:")

for model in data["data"]:
    print(
        "-",
        model["id"]
    )

print("")
print("VS CODE CONNECTION TEST PASS")
