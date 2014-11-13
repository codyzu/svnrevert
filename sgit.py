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


def collect_revert_dirs(svnitems):
    paths = [svnitem.path for svnitem in svnitems if svnitem.item == 'external']
    paths.insert(0, workingdir)  # insert the working directory
    return paths


def collect_unversioned_item_paths(svnitems):
    return [svnitem.path for svnitem in svnitems if svnitem.item == 'unversioned']


def iter_svn_item_status(xmlstatus):
    click.echo("Parsing SVN results")
    tree = ET.fromstring(xmlstatus)

    for entry in tree.iter('entry'):
        path = entry.attrib['path']
        status = entry.find('wc-status')
        item = status.attrib['item']
        yield SvnItem(path, item)

def get_svn_item_statuses():
    click.echo("Getting svn status for: " + workingdir)
    xmlstatus = repo.run_command('status', ['--xml', workingdir], combine=True)
    return list(iter_svn_item_status(xmlstatus))


def collect_non_externals(svnitems):
    return [svnitem for svnitem in svnitems if svnitem.item != 'external']


def revert_dirs_recursively(paths):
    result = ""
    with click.progressbar(paths) as revertpaths:
        for path in revertpaths:
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
    global dryrun
    dryrun = dry_run
    global repo
    repo = svn.local.LocalClient(path)
    global workingdir
    workingdir = path

    svnitems = get_svn_item_statuses()
    changes = sorted(collect_non_externals(svnitems), key=attrgetter('path'))
    for svnitem in changes:
        click.secho("{0}: {1}".format(svnitem.item, svnitem.path), fg='yellow')

    click.echo("Found {0} changes to revert".format(len(changes)))

    if len(changes) == 0:
        click.secho("Exiting", fg='green')
        return

    revert_dirs = sorted(collect_revert_dirs(svnitems))

    click.echo("The following directories will be recursively reverted:")

    for dir in revert_dirs:
        click.secho(dir, fg='yellow')

    if click.confirm("Recursively revert the above {0} directories".format(len(revert_dirs)), abort=True):
        click.secho("Reverting...", fg='red')
        revert_dirs_recursively(revert_dirs)

    svnitems = get_svn_item_statuses()
    unversioned = sorted(collect_unversioned_item_paths(svnitems))
    click.echo("The following items are unversioned:")

    for item in unversioned:
        click.secho(item, fg='yellow')

    if (len(unversioned) > 0 and
            click.confirm("Delete the above {0} files/directories".format(len(unversioned)), abort=True)):
        click.secho("Deleting...", fg='red')
        delete_items(unversioned)


if __name__ == '__main__':
    revert()
