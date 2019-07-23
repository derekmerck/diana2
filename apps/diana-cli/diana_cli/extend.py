import click
import subprocess

epilog = """

$ diana-cli extend bone_age

"""


@click.command(short_help="Extend images to an ML analysis", epilog=epilog)
@click.argument('ML', type=click.STRING)
@click.option('--args', '-g', type=click.STRING, default=None)
@click.option('--map_arg', '-m', type=click.STRING, default=None)
@click.option('--kwargs', '-k', type=click.STRING, default=None)
@click.option('--anonymize', '-a', is_flag=True, default=False, help="(ImageDir only)")
@click.pass_context
def extend(ML):
    subprocess.Popen("diana-cli watch -r say_studies radarch None > /diana_direct/{}/{}_results.json".format(ML, ML), shell=True, stdout=subprocess.PIPE)

    subprocess.Popen("python3 predict.py {}".format(dcmdir_name))
