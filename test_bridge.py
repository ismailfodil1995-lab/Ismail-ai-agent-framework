# n8n_bridge.py

from n8n import ScriptNode

class CustomWebhookNode(ScriptNode):
    name = "CustomWebhookNode"
    description = "This is a custom Webhook node for n8n."
    version = "1.0.0"

    def execute(self, data):
        env_var = os.getenv('N8N_WEBHOOK_URL')
        if env_var is None:
            raise ValueError('N8N_WEBHOOK_URL is not set in the environment.')
        
        url = env_var
        self.executeWorkflow(url)
    
    compatible_versions = ["1.0", "2.0"]
