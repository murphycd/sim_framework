class MessageBus:
    def __init__(self):
        self.messages = []

    def emit(self, message_type, **payload):
        self.messages.append({"type": message_type, "payload": payload})

    def get(self, message_type=None):
        for msg in self.messages:
            if message_type is None or msg["type"] == message_type:
                yield msg

    def clear(self):
        self.messages.clear()
