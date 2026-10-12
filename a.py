import requests
import json

url = "http://127.0.0.1:5000/api/copilot/ask"

payload = {
    "question": "What is IBPS?",
    "conversation_id": "copilot_test_001"
}

try:
    response = requests.post(
        url,
        json=payload,
        timeout=120
    )

    print("Status code:", response.status_code)

    try:
        print(json.dumps(response.json(), indent=2))
    except ValueError:
        print("Response:", response.text)

except requests.exceptions.RequestException as e:
    print("Request failed:", str(e))
    
