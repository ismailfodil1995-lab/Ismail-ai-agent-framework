import requests

def send_request_to_webhook():
    url = "https://webhook.site/bf58f591-224c-46d5-9c58-4c8d4a647e2d"
    data = {"key": "value"}
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_request_to_webhook()