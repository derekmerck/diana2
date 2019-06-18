import os, json, logging
from pprint import pformat
from test_utils import find_resource
from diana.utils import SmartJSONEncoder
from diana.utils.dicom import dicom_simplify

import difflib


# TODO: Test in Dixel creation from reading files and Orthanc

def test_simplify():

    dir = find_resource("resources/dose")
    items = ["dose_tags_anon"]

    for item in items:

        fn = "{}.json".format(item)
        fp = os.path.join(dir, fn)

        with open(fp) as f:
            tags = json.load(f)

        tags = dicom_simplify(tags)

        # Have to compare in dumped space b/c loader doesn't convert times back into times
        tag_str = json.dumps(tags, indent=3, cls=SmartJSONEncoder, sort_keys=True)

        # logging.debug(pformat(tag_str))

        fn = "{}.simple.json".format(item)
        fp = os.path.join(dir, fn)

        # with open(fp, 'w') as f:
        #     f.write(tag_str)

        with open(fp) as f:
            simple_str = f.read()

        # logging.debug(tag_str)
        # logging.debug(simple_str)

        # a = tag_str
        # b = simple_str
        # for i, s in enumerate(difflib.ndiff(a, b)):
        #     if s[0] == ' ':
        #         continue
        #     elif s[0] == '-':
        #         print(u'Delete "{}" from position {}'.format(s[-1], i))
        #     elif s[0] == '+':
        #         print(u'Add "{}" to position {}'.format(s[-1], i))

        assert tag_str == simple_str


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_simplify()
