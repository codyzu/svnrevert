__author__ = 'cody'

import click
import svn.local


@click.command()
@click.argument("path", default=".")
def revert(path):
    r = svn.local.LocalClient(path)
    i = r.info()
    x = 5


if __name__ == '__main__':
    revert()
