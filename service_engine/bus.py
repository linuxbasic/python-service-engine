import threading
from weakref import WeakSet

from .service import Service
from .events import Event, SubscribeEvent, UnsubscribeEvent


class BusService(Service):
    def on_init(self):
        self.subscriptions = dict()

    def on_event(self, event):
        if isinstance(event, SubscribeEvent):
            self.subscriptions.setdefault(event.event_type, WeakSet())
            self.subscriptions.get(event.event_type).add(event.in_queue)
        elif isinstance(event, UnsubscribeEvent):
            subscriptions = self.subscriptions.get(event.event_type, set())
            if event.in_queue in subscriptions:
                subscriptions.remove(event.in_queue)
        else:
            for queue in self.subscriptions.get(type(event), set()):
                queue.put(event)

    def on_exit(self):
        pass

