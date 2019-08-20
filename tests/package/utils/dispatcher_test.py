import logging
from interruptingcow import timeout
from diana.utils.endpoint import Dispatcher, Subscription


def test_simple_dispatch(capsys):

    D = Dispatcher()

    events = ["abc", "def", "ghi"]

    for item in events:
        D.event_queue.put(item)

    D.subscribers.append( Subscription() )

    def my_listening_for(self, event):
        return "a" in event or "g" in event

    def my_callback_for(self, event):
        print("SUBSCRIBER {} RECIEVED EVENT {}".format(self.subid, event))

    my_subscriber = Subscription()

    # See https://stackoverflow.com/questions/972/adding-a-method-to-an-existing-object-instance for monkey-patching an existing object with lexical binding (ie, "self")
    my_subscriber.listening_for = my_listening_for.__get__(my_subscriber)
    my_subscriber.callback_for = my_callback_for.__get__(my_subscriber)

    D.subscribers.append(my_subscriber)

    try:
        with timeout(5):
            D.run()
    except:
        pass

    expected = """Subscriber 0 received event abc
SUBSCRIBER 1 RECIEVED EVENT abc
Subscriber 0 received event def
Subscriber 0 received event ghi
SUBSCRIBER 1 RECIEVED EVENT ghi
"""

    if capsys:
        captured = capsys.readouterr()
        for line in expected.splitlines():
            assert line in captured.out


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_simple_dispatch(None)
