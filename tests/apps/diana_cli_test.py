import logging
from conftest import *
from utils import find_resource
from click.testing import CliRunner
from diana.cli.cli import cli as app


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    print(result.output)

    assert("Check endpoint status" in result.output)


def test_cli_svc_check(setup_orthanc0, setup_redis):
    runner = CliRunner()
    services_file = find_resource("resources/test_services.yml")
    result = runner.invoke(app, [
        "-v",
        "-s", f"@{services_file}",
        "ls"])
    print(result.output)

    assert( "orthanc: Ready" in result.output )
    assert( "orthanc_bad: Unavailable" in result.output )
    assert( "redis: Ready" in result.output )
    assert( "redis_bad: Unavailable" in result.output )

    result = runner.invoke(app, [
        "-v",
        "-s", "redis_bad2: {ctype: Redis, port: 9999}",
        "check",
        "redis_bad2"])
    print(result.output)

    assert( "redis_bad2: Unavailable" in result.output )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Testing")

    test_cli_help()
    mk_orthanc()
    mk_redis()
    test_cli_svc_check(None, None)

