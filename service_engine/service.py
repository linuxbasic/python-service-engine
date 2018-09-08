import threading
import logging

from .events import SubscribeEvent, UnsubscribeEvent

class Service:
    class StopServiceEvent:
        pass
    def __init__(self, name="Unnamed Service", args=(), kwargs=None):
        self.name = name
        self.logger = logging.getLogger("Service: {}".format(self.name))
        self.args = args
        self.kwargs = kwargs
        self.runtime = None

    def on_init(self, *args, **kwargs):
        raise NotImplementedError()

    def on_event(self, event):
        raise NotImplementedError()

    def on_exit(self):
        raise NotImplementedError()

    def event_loop(self, *args, **kwargs):
        try:
            self.on_init(*args, **kwargs)
            while True:
                event = threading.current_thread().in_queue.get()
                if isinstance(event, self.StopServiceEvent):
                    self.on_exit()
                    return
                self.on_event(event)
        except Exception as error:
            threading.current_thread().err_queue.put(error)
            self.logger.error(error)
            

    def start(self, in_queue, out_queue, err_queue):
        if self.is_running() == True:
            raise RuntimeError("Service must be stopped befor he can be started again")
        self.runtime = threading.Thread(name=self.name, target=self.event_loop, args=self.args, kwargs=self.kwargs)
        self.runtime.in_queue = in_queue
        self.runtime.out_queue = out_queue
        self.runtime.err_queue = err_queue
        self.runtime.start()

    def stop(self):
        self.runtime.in_queue.put(self.StopServiceEvent())
        self.runtime.join()
        self.runtime = None

    def is_running(self):
        if self.runtime is not None:
            return self.runtime.is_alive()
        return False

    def subscribe(self, event_type):
        in_queue = threading.current_thread().in_queue
        self.publish(SubscribeEvent(event_type, in_queue))

    def unsubscribe(self, event_type):
        in_queue = threading.current_thread().in_queue
        self.publish(UnsubscribeEvent(event_type, in_queue))

    def publish(self, event):
        threading.current_thread().out_queue.put(event)