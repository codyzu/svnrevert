svnrevert
=========

Recursively reverts a local svn changes, including externals

When working with externals in svn, there is no built-in way to recurse into externals when reverting.
svn status recurses into external, but revert does not.

This tool will recursively revert a directory, and follow the externals to revert them also.
In addition, the tool will also propose the option to delete any untracked files.
This ensures your entire working copy (including externals) is in pristine state.

I wrote the tool to facilitate a working with multiple VCS on the same local working copies.
Specifically, when the project uses svn for the official repository, but I prefer to work with git locally.


Usage
-----

```
Usage: svnrevert [OPTIONS] [PATH]

  Recursively revert the given path and any contained externals

  If no PATH is given, it defaults to '.'

Options:
  -n, --dry-run  Don't modify any files or directories.
  --help         Show this message and exit.
```

Installation
------------

*works with python 2.7 and python 3*

Install the latest with pip:

```
pip install https://github.com/codyzu/svnrevert/archive/master.zip
```