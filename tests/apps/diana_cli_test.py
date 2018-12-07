import logging
# import click
from click.testing import CliRunner

app = __import__('diana-cli')

def test_cli_svc_check():
    runner = CliRunner()
    result = runner.invoke(app.cli, ["--help"])
    print(result.output)

    result = runner.invoke(app.cli, ["-S", "../.secrets/test_services.yml", "check"])
    print(result.output)

    assert( "orthanc: Ready" in result.output )
    assert( "orthanc_bad: Not Ready" in result.output )
    assert( "redis: Ready" in result.output )
    assert( "redis_bad: Not Ready" in result.output )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Testing")
    test_cli_svc_check()
