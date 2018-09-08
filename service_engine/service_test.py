import pytest
import threading
import queue

from .events import Event, SubscribeEvent, UnsubscribeEvent
from .service import Service

ONE_SECOND = 1

class DummyEvent(Event):
    pass

class DummyService(Service):
    def on_init(self):
        pass

    def on_event(self, event):
        pass

    def on_exit(self):
        pass

@pytest.fixture
def queues():
    return queue.Queue(), queue.Queue(), queue.Queue()

def test_thread_name_set(queues):
    SERVICE_NAME = "Service Name"
    assert SERVICE_NAME not in [thread.name for thread in threading.enumerate()]
    service = DummyService(name=SERVICE_NAME)
    service.start(*queues)
    assert SERVICE_NAME in [thread.name for thread in threading.enumerate()]
    service.stop()

    

def test_start_in_thread(queues):
    signal = threading.Event()
    class TestInitService(DummyService):
        def on_init(self):
            signal.thread = threading.current_thread()
            signal.set()

    service = TestInitService()
    service.start(*queues)

    signal.wait(timeout=ONE_SECOND)
    service.stop()

    assert signal.thread != threading.current_thread()

def test_prevent_start_multiple_threads(queues):
    service = DummyService()
    service.start(*queues)

    with pytest.raises(RuntimeError):
        service.start(*queues)

    service.stop()

def test_init_with_args(queues):
    signal = threading.Event()
    PARAM_1 = "hello"
    PARAM_2 = "world"
    class TestInitService(DummyService):
        def on_init(self, param1, param2=None):
            signal.param1 = param1
            signal.param2 = param2
            signal.set()

    service = TestInitService(args=(PARAM_1,), kwargs={"param2":PARAM_2})
    service.start(*queues)

    signal.wait(timeout=ONE_SECOND)
    service.stop()

    assert signal.param1 == PARAM_1
    assert signal.param2 == PARAM_2

def test_stop_service(queues):
    service = DummyService()
    active_threads_before = threading.active_count()
    service.start(*queues)
    assert threading.active_count() == active_threads_before + 1
    service.stop()
    assert threading.active_count() == active_threads_before

def test_on_exit(queues):
    signal = threading.Event()
    class OnExitService(DummyService):
        def on_exit(self):
            signal.set()

    service = OnExitService()
    service.start(*queues)
    service.stop()
    signal.wait(timeout=ONE_SECOND)

    assert signal.is_set()

def test_error_in_on_init(queues):
    class TestError(Exception):
        pass
    class ErrorInOnInitService(DummyService):
        def on_init(self):
            raise TestError()
    _, __, err_queue = queues
    service = ErrorInOnInitService()
    service.start(*queues)
    error = err_queue.get(timeout=ONE_SECOND)

    assert isinstance(error, TestError)

def test_error_in_on_exit(queues):
    class TestError(Exception):
        pass
    class ErrorInOnExitService(DummyService):
        def on_exit(self):
            raise TestError()
    _, __, err_queue = queues
    service = ErrorInOnExitService()
    service.start(*queues)
    service.stop()
    error = err_queue.get(timeout=ONE_SECOND)

    assert isinstance(error, TestError)

def test_error_in_on_event(queues):
    class TestError(Exception):
        pass
    class ErrorInOnEventService(DummyService):
        def on_event(self, event):
            raise TestError()
    in_queue, _, err_queue = queues
    service = ErrorInOnEventService()
    service.start(*queues)
    in_queue.put(DummyEvent())
    error = err_queue.get(timeout=ONE_SECOND)

    assert isinstance(error, TestError)


def test_restart_service(queues):
    runtimes = list()
    class RestartService(DummyService):
        def on_init(self):
            runtimes.append(threading.current_thread())
    service = RestartService()

    service.start(*queues)
    service.stop()
    service.start(*queues)
    service.stop()

    assert runtimes[0] != runtimes[1]

def test_on_event(queues):
    in_queue, _, __ = queues
    signal = threading.Event()
    sent_event = DummyEvent()
    class TestOnEventService(DummyService):
        def on_event(self, event):
            signal.event = event
            signal.set()

    service = TestOnEventService()
    service.start(*queues)

    in_queue.put(sent_event)

    signal.wait(timeout=ONE_SECOND)
    service.stop()

    assert signal.event == sent_event
    
def test_publish_event(queues):
    class PublishEventService(DummyService):
        def on_init(self):
            self.publish(DummyEvent())
    
    _, out_queue, __ = queues
    service = PublishEventService()
    service.start(*queues)

    published_event = out_queue.get(timeout=ONE_SECOND)

    service.stop()

    assert isinstance(published_event, Event)

def test_subscribe(queues):
    class SubscribeEventService(DummyService):
        def on_init(self):
            self.subscribe(DummyEvent)
    
    in_queue, out_queue, _ = queues
    service = SubscribeEventService()
    service.start(*queues)

    published_event = out_queue.get(timeout=ONE_SECOND)

    service.stop()

    assert isinstance(published_event, SubscribeEvent)
    assert published_event.event_type == DummyEvent
    assert published_event.in_queue == in_queue

def test_unsubscribe(queues):
    class SubscribeEventService(DummyService):
        def on_init(self):
            self.unsubscribe(DummyEvent)
    
    in_queue, out_queue, _ = queues
    service = SubscribeEventService()
    service.start(*queues)

    published_event = out_queue.get(timeout=ONE_SECOND)

    service.stop()

    assert isinstance(published_event, UnsubscribeEvent)
    assert published_event.event_type == DummyEvent
    assert published_event.in_queue == in_queue

def test_is_running(queues):
    service = DummyService()
    assert service.is_running() == False
    service.start(*queues)
    assert service.is_running() == True
    service.stop()
    assert service.is_running() == False

def test_is_running_after_error(queues):
    class ErrorInOnInitService(DummyService):
        def on_init(self):
            raise Exception()
    service = ErrorInOnInitService()
    service.start(*queues)
    assert service.is_running() == False