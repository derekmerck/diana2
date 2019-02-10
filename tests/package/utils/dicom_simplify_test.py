import os, json, logging
from test_utils import find_resource
from diana.utils import SmartJSONEncoder
from diana.utils.dicom import dicom_simplify


# TODO: Test in Dixel creation!

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

        fn = "{}.simple.json".format(item)
        fp = os.path.join(dir, fn)

        with open(fp) as f:
            simple_str = f.read()

        # logging.debug(tag_str)
        # logging.debug(simple_str)

        assert tag_str == simple_str


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_simplify()