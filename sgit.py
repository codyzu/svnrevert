from pathlib import Path
from collections import namedtuple
import click
from operator import attrgetter
import shutil
import os
import svn.local
import xml.etree.ElementTree as ET

__author__ = 'cody'


SvnItem = namedtuple('SvnItem', ['path', 'item'])
dryrun = False
repo = None
workingdir = ""


def get_svn_statuses():
    click.echo("Getting svn status for: " + workingdir)
    xmlstatus = repo.run_command('status', ['--xml', workingdir], combine=True)

    click.echo("Parsing SVN results")
    tree = ET.fromstring(xmlstatus)

    svnitems = list()
    for entry in tree.iter('entry'):
        path = entry.attrib['path']
        status = entry.find('wc-status')
        item = status.attrib['item']
        svnitems.append(SvnItem(path, item))

    return svnitems


def revert_dirs_recursively(paths):
    result = ""
    with click.progressbar(paths) as revert_paths:
        for path in revert_paths:
            if not dryrun:
                result += repo.run_command('revert', ['-R', path], combine=True)

    click.secho(result, fg='red')

    if dryrun:
        click.secho("No changes made in dry-run mode", fg='green')


def delete_items(items):
    for item in items:
        p = Path(item)
        normal_path = str(p)  # prefer the normalized path from pathlib
        click.secho("Removing: " + normal_path, fg='red')
        if p.is_dir():
            if not dryrun:
                shutil.rmtree(normal_path)
        else:
            if not dryrun:
                os.remove(normal_path)

    if dryrun:
        click.secho("No changes made in dry-run mode", fg='green')


@click.command()
@click.option('--dry-run', '-n', is_flag=True, help="Don't perform any operations that could change files")
@click.argument("path", default=".")
def revert(dry_run, path):
    """Recursively revert the given path and any contained externals"""
    # setup our global variables
    global dryrun
    global repo
    global workingdir
    dryrun = dry_run
    repo = svn.local.LocalClient(path)
    workingdir = path

    # svn status
    svnitems = get_svn_statuses()

    # collect all of the changes, print them, and exit if there are none
    changes = sorted([svnitem for svnitem in svnitems if svnitem.item != 'external'], key=attrgetter('path'))
    for svnitem in changes:
        click.secho("{0}: {1}".format(svnitem.item, svnitem.path), fg='yellow')

    click.echo("Found {0} changes to revert".format(len(changes)))

    if len(changes) == 0:
        click.secho("Exiting", fg='green')
        return

    # collect the dirs we will revert, print them, and then revert
    # for simplicity, we simply revert all externals and the working dir
    revert_dirs = [svnitem.path for svnitem in svnitems if svnitem.item == 'external']
    revert_dirs.insert(0, workingdir)  # don't forget to revert the working dir, since it is not an external
    revert_dirs = sorted(revert_dirs)

    click.echo("The following directories will be recursively reverted:")

    for revert_dir in revert_dirs:
        click.secho(revert_dir, fg='yellow')

    if click.confirm("Recursively revert the above {0} directories".format(len(revert_dirs)), abort=True):
        click.secho("Reverting...", fg='red')
        revert_dirs_recursively(revert_dirs)

    # new svn status after the above revert
    svnitems = get_svn_statuses()

    # collect all unversioned files/dirs, print them, and then delete them
    unversioned = sorted([svnitem.path for svnitem in svnitems if svnitem.item == 'unversioned'])
    click.echo("The following items are unversioned:")

    for item in unversioned:
        click.secho(item, fg='yellow')

    if (len(unversioned) > 0 and
            click.confirm("Delete the above {0} files/directories".format(len(unversioned)), abort=True)):
        click.secho("Deleting...", fg='red')
        delete_items(unversioned)


if __name__ == '__main__':
    revert()
