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
