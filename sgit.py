__author__ = 'cody'

import click
import svn.local
import xml.etree.ElementTree as ET

def iteritems():
    tree = ET.parse('svnstatus.xml')
    for entry in tree.iter('entry'):
        path = entry.attrib['path']
        status = entry.find('wc-status')
        item = status.attrib['item']
        yield path, item

@click.command()
@click.argument("path", default=".")
def revert(path):
    #r = svn.local.LocalClient(path)
    #i = r.info()
    x = 5

    items = list(iteritems())


    unversioned = [(path, item) for (path, item) in items if item == 'unversioned']
    externals = [(path, item) for (path, item) in items if item == 'external']
    modified = [(path, item) for (path, item) in items if item == 'modified']

    for path, item in iteritems():
        print("{0}: {1}".format(path, item))


if __name__ == '__main__':
    revert()
