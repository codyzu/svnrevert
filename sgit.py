"""Useful operations when working with git and svn simulatenously.

References:
http://pysvn.tigris.org/docs/pysvn_prog_ref.html#pysvn_wc_status_kind
http://svnbook.red-bean.com/en/1.7/svn.developer.usingapi.html

"""
import pathlib
import xml.etree.ElementTree

import collections
import click
import operator
import shutil
import os
import svn.local


__author__ = 'cody'

SvnItem = collections.namedtuple('SvnItem', ['path', 'item'])
dryrun = False
repo = None
workingdir = ""


def get_svn_statuses():
    """Execute svn status and parse the results for the status of all items"""
    click.echo("Getting svn status for: " + workingdir)
    xmlstatus = repo.run_command('status', ['--xml', workingdir], combine=True)

    click.echo("Parsing SVN results")
    tree = xml.etree.ElementTree.fromstring(xmlstatus)

    svnitems = list()
    for entry in tree.iter('entry'):
        path = entry.attrib['path']
        status = entry.find('wc-status')
        item = status.attrib['item']
        svnitems.append(SvnItem(path, item))

    return svnitems


def revert_dirs_recursively(paths):
    """svn revert all list of directories and print the results"""
    result = ""
    with click.progressbar(paths) as revert_paths:
        for path in revert_paths:
            if not dryrun:
                try:
                    result += repo.run_command('revert', ['-R', path], combine=True)
                except ValueError as error:
                    result += "ERROR reverting {0}: {1}\n".format(path, error)

    click.secho(result, fg='red')

    if dryrun:
        click.secho("No changes made in dry-run mode", fg='green')


def delete_items(paths):
    """Delete a list of paths to files or directories"""
    for path in paths:
        p = pathlib.Path(path)
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


def summarize_changes(svnitems):
    """List all of the changes and return true if any changes are found"""
    changes = sorted([svnitem for svnitem in svnitems if svnitem.item != 'external'], key=operator.attrgetter('path'))
    for svnitem in changes:
        click.secho("{0}: {1}".format(svnitem.item, svnitem.path), fg='yellow')

    click.echo("Found {0} changes to revert".format(len(changes)))

    return len(changes) > 0


def get_externals():
    """Execute svn propget svn:externals and return a list of local dirs that are externals"""
    click.echo("Getting svnexternals for: " + workingdir)
    externals = repo.run_command('propget', ['svn:externals', workingdir], combine=False)

    # grab just the right side of the space, the local path for the external
    # we filter the externals that have the format "remote_path local_path", any other format will be ignored
    # finally, we insert the working directory before before all local paths
    externals = [os.path.join(workingdir, external.split()[1]) for external in externals if len(external.split()) == 2]
    return externals


def revert_changes():
    """Revert the working dir and all externals"""
    revert_dirs = get_externals()
    revert_dirs.insert(0, workingdir)  # don't forget to revert the working dir, since it is not an external
    revert_dirs = sorted(revert_dirs)

    click.echo("The following directories will be recursively reverted:")

    for revert_dir in revert_dirs:
        click.secho(revert_dir, fg='yellow')

    if click.confirm("Recursively revert the above {0} directories".format(len(revert_dirs)), abort=True):
        click.secho("Reverting...", fg='red')
        revert_dirs_recursively(revert_dirs)


def delete_unversioned(svnitems):
    """Delete all items (files/dirs) are that are unversioned"""
    unversioned = sorted([svnitem.path for svnitem in svnitems if svnitem.item == 'unversioned'])
    click.echo("The following items are unversioned:")

    for item in unversioned:
        click.secho(item, fg='yellow')

    if (len(unversioned) > 0 and
            click.confirm("Delete the above {0} files/directories".format(len(unversioned)), abort=True)):
        click.secho("Deleting...", fg='red')
        delete_items(unversioned)


@click.command()
@click.option('--dry-run', '-n', is_flag=True, help="Don't modify any files or directories.")
@click.argument("path", default=".")
def revert(dry_run, path):
    """Recursively revert the given path and any contained externals

    If no PATH is given, it defaults to '.'
    """
    # setup our global variables
    global dryrun
    global repo
    global workingdir
    dryrun = dry_run
    repo = svn.local.LocalClient(path)
    workingdir = path

    # get the svn status
    svnitems = get_svn_statuses()

    # if there are no changes, exit
    if not summarize_changes(svnitems):
        click.secho("Exiting", fg='green')
        return

    revert_changes()

    # refresh svn status after reverting
    svnitems = get_svn_statuses()

    delete_unversioned(svnitems)


if __name__ == '__main__':
    revert()
