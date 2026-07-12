
import sys
sys.path.insert(0,".")

from api.vscode_bridge import app


client=app.test_client()

r=client.get("/v1/models")

assert r.status_code==200

print("VS CODE BRIDGE TEST PASS")
