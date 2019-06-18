from click.testing import CliRunner
import click


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
    cmds = [cmd.name for cmd in app.cli.cmds]

    return header, footer, cmds


@click.command()
@click.argument("apps", nargs=-1)
@click.option("--outfile", "-o", type=click.Path())
def cli(apps, outfile):

    text = ""
    for app in apps:
        _app = __import__(app)

        header, footer, cmds = get_app_info(_app)

        text += header
        text += "```\n" + run_cli_help(_app.cli) + "```\n"

        for cmd in cmds:
            text += "## {}\n\n".format(cmd)
            text += "```\n" + run_cli_help(_app.cli, cmd) + "```\n"

        text += footer

    if outfile:
        with open(outfile, "w") as f:
            f.write(text)
    else:
        click.echo(text)


if __name__ == "__main__":
    cli()
