# Wrapper for configparser that handles files with no section headers

from configparser import ConfigParser
from collections import OrderedDict
from io import StringIO


class SimpleConfigParser(ConfigParser):

    def __init__(self):
        super().__init__()
        self.optionxform = str  # keys are case-sensitive

    def loads(self, source: str) -> OrderedDict:

        source = "[root]\n" + source
        self.read_string(source)
        return OrderedDict((k, v) for k, v in self["root"].items())

    def dumps(self, data=OrderedDict) -> str:

        self.read_dict({"root": data})
        _output = StringIO()
        self.write(_output, space_around_delimiters=False)
        output = _output.getvalue()[7:]  # Clip the header
        return output
