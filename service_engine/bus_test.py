import pytest
import queue

from .bus import BusService
from .events import Event, SubscribeEvent, UnsubscribeEvent

ONE_SECOND = 1

class DummyEvent(Event):
    pass

@pytest.fixture
def queues():
    return queue.Queue(), queue.Queue(), queue.Queue()

def test_subscribe(queues):
    bus_in_queue, _, __ =queues
    bus = BusService()

    service_in_queue = queue.Queue()
    sent_message = DummyEvent()

    bus.start(*queues)
    bus_in_queue.put(SubscribeEvent(DummyEvent,service_in_queue))
    bus_in_queue.put(sent_message)
    received_message = service_in_queue.get(timeout=ONE_SECOND)
    bus.stop()

    assert received_message == sent_message

def test_subscribe_multiple(queues):
    bus_in_queue, _, __ =queues
    bus = BusService()
    bus.start(*queues)

    service1_in_queue = queue.Queue()
    service2_in_queue = queue.Queue()

    sent_message = DummyEvent()
    bus_in_queue.put(SubscribeEvent(DummyEvent,service1_in_queue))
    bus_in_queue.put(SubscribeEvent(DummyEvent,service2_in_queue))
    bus_in_queue.put(sent_message)
    received_message1 = service1_in_queue.get(timeout=ONE_SECOND)
    received_message2 = service2_in_queue.get(timeout=ONE_SECOND)
    bus.stop()

    assert received_message1 == sent_message
    assert received_message2 == sent_message

def test_subscribe_twice(queues):
    bus_in_queue, _, bus_err_queue =queues
    bus = BusService()

    service_in_queue = queue.Queue()

    bus.start(*queues)
    bus_in_queue.put(SubscribeEvent(DummyEvent,service_in_queue))
    bus_in_queue.put(SubscribeEvent(DummyEvent,service_in_queue))
    bus_in_queue.put(DummyEvent())
    bus.stop()

    assert bus_err_queue.empty()
    assert service_in_queue.qsize() == 1

def test_unsubscribe(queues):
    bus_in_queue, _, __ =queues
    bus = BusService()

    service_in_queue = queue.Queue()
    sent_message_1 = DummyEvent()
    sent_message_2 = DummyEvent()

    bus.start(*queues)
    bus_in_queue.put(SubscribeEvent(DummyEvent,service_in_queue))
    bus_in_queue.put(sent_message_1)
    bus_in_queue.put(UnsubscribeEvent(DummyEvent,service_in_queue))
    bus_in_queue.put(sent_message_2)
    bus.stop()

    assert service_in_queue.get(timeout=ONE_SECOND) == sent_message_1
    assert service_in_queue.empty()

def test_unsubscribe_without_subscription(queues):
    bus_in_queue, _, bus_err_queue =queues
    bus = BusService()
    bus.start(*queues)
    bus_in_queue.put(UnsubscribeEvent(DummyEvent,queue.Queue()))
    bus.stop()

    assert bus_err_queue.empty()
    
def test_automatically_unsubscribe_if_queue_is_not_referenced_anymore(queues):
    bus_in_queue, _, __ =queues
    bus = BusService()

    bus.start(*queues)
    bus_in_queue.put(SubscribeEvent(DummyEvent, queue.Queue()))
    bus.stop()

    assert len(bus.subscriptions.get(DummyEvent)) == 0
