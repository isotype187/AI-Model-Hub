import requests
import time

print("START")

payload = {
    "model": "qwen3:30b",
    "prompt": "Design a plugin architecture for AI_Model_Hub. Be concise.",
    "stream": False,
    "options": {
        "num_predict": 300,
        "temperature": 0.2
    }
}

print("SENDING")

start=time.time()

r=requests.post(
    "http://127.0.0.1:11434/api/generate",
    json=payload,
    timeout=(10,60)
)

print("RETURNED")
print("SECONDS:",time.time()-start)

print(r.status_code)

data=r.json()

print(data.get("response","NO RESPONSE"))
