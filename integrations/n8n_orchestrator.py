import requests

def n8n_orchestrator(data):
    # Define the N8N webhook URL
    webhook_url = "https://your-n8n-instance.com/webhook-endpoint"

    # Prepare the payload to send to N8N
    payload = {
        "data": data
    }

    try:
        # Send a POST request to the N8N webhook endpoint
        response = requests.post(webhook_url, json=payload, timeout=3)
    except Exception as e:
        return {"status": "error", "message": f"N8N connection error: {e}"}

    # Check if the request was successful
    if response.status_code == 200:
        print("Data sent to N8N successfully!")
    else:
        print(f"Failed to send data to N8N. Status code: {response.status_code}")

    # Return a response to the caller
    return {"message": "Data sent to N8N"}