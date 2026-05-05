class AppInstallationWebhookInfo:
    def __init__(self, entity: str, action: str, permissions: list[str], payload_cls):
        self.entity = entity
        self.action = action
        self.event_type = f"{entity}.{action}"
        self.permissions = permissions
        self.payload_cls = payload_cls
