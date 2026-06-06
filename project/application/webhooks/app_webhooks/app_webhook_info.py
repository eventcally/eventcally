class AppWebhookInfo:
    def __init__(self, entity: str, action: str, payload_cls):
        self.entity = entity
        self.action = action
        self.event_type = f"{entity}.{action}"
        self.payload_cls = payload_cls
