import logging
from conftest import *
from test_utils import find_resource
from click.testing import CliRunner

"""
diana-cli -s "{redis: {ctype: Redis}}" check
"""

from diana_cli import app


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    print(result.output)

    assert("Check endpoint status" in result.output)


def test_cli_svc_check(setup_orthanc, setup_redis):
    runner = CliRunner()
    services_file = find_resource("resources/test_services.yml")
    result = runner.invoke(app, [
        "-s", "{redis_bad2: {ctype: Redis, port: 9999}}",
        "-S", services_file, "check"])
    print(result.output)

    assert( "orthanc: Ready" in result.output )
    assert( "orthanc_bad: Not Ready" in result.output )
    assert( "redis: Ready" in result.output )
    assert( "redis_bad: Not Ready" in result.output )
    assert( "redis_bad2: Not Ready" in result.output )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Testing")

    test_cli_help()
    for (i, j) in zip( setup_orthanc(), setup_redis() ):
        test_cli_svc_check(None, None)

        # i.stop_service()
        # j.stop_service()
