import click
import diana
from gistsig import get_gist, get_pkg_info


@click.command(short_help="Verify DIANA source code against public gist signature")
def verify():
    """
    Verify DIANA source code against public gist signature.

    This function is a convenience only; if the package has been altered, it
    could easily be altered to return correct hashes or check the wrong gist.
    The paranoid should refer to <https://github.com/derekmerck/gistsig> for
    instructions on finding performing an external manual audit.
    """

    # DIANA gist
    gist_id = diana.__gistsig__

    exit_code = 0
    for pkg_name in ["diana", "crud", "wuphf"]:
        try:
            key, value = get_pkg_info(pkg_name)
        except ModuleNotFoundError:
            print(f"Skipping package {pkg_name}.")
            continue

        pkg_sigs = get_gist(gist_id=gist_id, name=pkg_name)

        ref = None
        if pkg_sigs:
            entry = pkg_sigs.get(key)
            if entry:
                ref = entry.get('hash')

        if value != ref:
            msg = click.style("Package signature {}:{} is not valid.".format(key, value), fg='red')
            click.echo(msg)
            exit_code = 1
        else:
            msg = click.style("Package signature {}:{} is valid.".format(key, value), fg="green")
            click.echo(msg)

    exit(exit_code)
