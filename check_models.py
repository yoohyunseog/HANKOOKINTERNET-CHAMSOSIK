import requests
import json

r = requests.get('http://localhost:11434/api/tags', timeout=10)
data = json.loads(r.text)
models = data.get('models', [])
print("Models loaded: {}".format(len(models)))
for m in models:
    size_gb = int(m['size'] / 1e9)
    print("  - {} ({}GB)".format(m['name'], size_gb))
