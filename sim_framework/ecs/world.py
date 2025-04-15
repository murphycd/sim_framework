import esper
from sim_framework.core.message_bus import MessageBus


class SimWorld(esper.World):
    def __init__(self):
        super().__init__()
        self.messages = MessageBus()
