# test_bridge.py

from n8n_bridge import CustomWebhookNode

def run_custom_webhook():
    CustomWebhookNode().run({'some': 'data'})

if __name__ == '__main__':
    run_custom_webhook()