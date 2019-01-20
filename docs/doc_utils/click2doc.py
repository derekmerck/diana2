from click.testing import CliRunner
import click

header = """
`diana-cli`
==================

Derek Merck  
<derek_merck@brown.edu>  
Rhode Island Hospital and Brown University  
Providence, RI  

[![Build Status](https://travis-ci.org/derekmerck/diana2.svg?branch=master)](https://travis-ci.org/derekmerck/diana2)
[![Coverage Status](https://codecov.io/gh/derekmerck/diana2/branch/master/graph/badge.svg)](https://codecov.io/gh/derekmerck/diana2)
[![Doc Status](https://readthedocs.org/projects/diana/badge/?version=master)](https://diana.readthedocs.io/en/master/?badge=master)

Source: <https://www.github.com/derekmerck/diana2>  
Documentation: <https://diana.readthedocs.io>  
Image:  <https://cloud.docker.com/repository/docker/derekmerck/diana2>

"""

footer = """

License
-------------

MIT

"""


def run_cli_help(app, cmd=None):
    runner = CliRunner()
    if cmd:
        result = runner.invoke(app.cli, [cmd, "--help"])
    else:
        result = runner.invoke(app.cli, ["--help"])
    return result.output


@click.command()
@click.argument("path", default="diana-cli", type=click.STRING)
def cli(path):

    cmds = ["check", "collect", "dcm2im", "findex", "fiup", "guid", "mock", "ofind", "watch"]

    app = __import__(path)

    text = header
    text += "```\n" + run_cli_help(app) + "```\n"

    for cmd in cmds:
        text += "## {}\n\n".format(cmd)
        text += "```\n" + run_cli_help(app, cmd) + "```\n"

    text += footer

    with open("README.md", "w") as f:
        f.write(text)


if __name__ == "__main__":
    cli()
