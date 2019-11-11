import datetime
from typing import Mapping
from jinja2 import Environment, BaseLoader


def render_template(template: str, funcs: Mapping=None, **data):

    _template = Environment(loader=BaseLoader()).from_string(template)
    if funcs:
        _template.globals.update( funcs )
    _template.globals['now'] = datetime.datetime.now

    return _template.render(**data)