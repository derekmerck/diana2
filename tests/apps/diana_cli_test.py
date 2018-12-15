import logging
from conftest import *
from test_utils import find_resource
from click.testing import CliRunner


app = __import__('diana-cli')

def test_cli_svc_check(setup_orthanc, setup_redis):
    runner = CliRunner()
    result = runner.invoke(app.cli, ["--help"])
    print(result.output)

    services_file = find_resource("test_services.yml")
    result = runner.invoke(app.cli, ["-S", services_file, "check"])
    print(result.output)

    assert( "orthanc: Ready" in result.output )
    assert( "orthanc_bad: Not Ready" in result.output )
    assert( "redis: Ready" in result.output )
    assert( "redis_bad: Not Ready" in result.output )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Testing")

    sys.path.append('..')
    from conftest import setup_orthanc, setup_redis

    for (i, j) in zip( setup_orthanc(), setup_redis() ):
        test_cli_svc_check(None, None)

        # i.stop_service()
        # j.stop_service()
