class Event:
    pass

class SubscriptionEvent(Event):
    def __init__(self, event_type, in_queue):
        self.event_type = event_type
        self.in_queue = in_queue


class SubscribeEvent(SubscriptionEvent):
    pass

class UnsubscribeEvent(SubscriptionEvent):
    pass