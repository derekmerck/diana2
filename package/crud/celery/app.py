import json
from json.decoder import JSONDecodeError
from celery import Celery
from ..abc import Serializable

app = Celery('tasks')

@app.task
def add(x,y):
    return x+y

@app.task
def say(item):
    return str(item)

@app.task
def handle(item_flat, endpoint_flat, handler, *args, **kwargs):
    """
    Note that the distributed crud class must register itself as
    the base class.  See `celery.pickler` as example.
    """

    # Unflatten inputs
    ep_dict = json.loads(endpoint_flat)
    ep = Serializable.Factory.create(**ep_dict)

    try:
        item_dict = json.loads(item_flat)
        item = Serializable.Factory.create(**item_dict)
    except (TypeError, JSONDecodeError):
        item = item_flat

    result = ep.handle(item, handler, args, kwargs)

    # Try to flatten result
    if hasattr(result, "json"):
        result = result.json()

    return result


if __name__ == "__main__":
    app.start()
