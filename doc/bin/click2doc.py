from click.testing import CliRunner
import click

header = """
Diana CLI
==================

"""

footer = """

License
-------------

MIT

"""

services = """
Requires platform service endpoint description in yaml format.

```yaml
---
orthanc:
  ctype: Orthanc
  port: 8042
  name: my_orthanc

redis:
  ctype: Redis
```
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

    cmds = ["check", "index", "indexed-pull", "dcm2im", "mock", "ofind", "watch"]

    app = __import__(path)

    text = header
    text += "```\n" + run_cli_help(app) + "```\n"

    text += services

    for cmd in cmds:
        text += "## {}\n\n".format(cmd)
        text += "```\n" + run_cli_help(app, cmd) + "```\n"

        # if hasattr(app.cli, "example"):
        #     text += app.cli.example

    text += footer

    with open("README.md", "w") as f:
        f.write(text)


if __name__ == "__main__":
    cli()
