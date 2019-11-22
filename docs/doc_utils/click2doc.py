from click.testing import CliRunner
import click

from importlib import import_module


def run_cli_help(app, cmd=None):
    runner = CliRunner()
    if cmd:
        result = runner.invoke(app.cli, [cmd, "--help"])
    else:
        result = runner.invoke(app.cli, ["--help"])
    return result.output


def get_app_info(app):

    header = app.__dict__.get("__readme_header__", "")
    footer = app.__dict__.get("__readme_footer__", "")

    cmds = list(app.cli.commands.keys())
    cmds.sort()

    return header, footer, cmds


@click.command()
@click.argument("app", default="diana.cli.cli")
@click.option("--outfile", "-o", type=click.Path())
def cli(app, outfile):

    text = ""

    _app: click.Group = import_module(app)

    # print(dir(_app))
    # print(_app.cli.commands.keys())

    header, footer, cmds = get_app_info(_app)

    text += header
    text += "```\n" + run_cli_help(_app) + "```\n"

    for cmd in cmds:
        text += "## {}\n\n".format(cmd)
        text += "```\n" + run_cli_help(_app, cmd) + "```\n"

    text += footer

    if outfile:
        with open(outfile, "w") as f:
            f.write(text)
    else:
        click.echo(text)


if __name__ == "__main__":
    cli()
