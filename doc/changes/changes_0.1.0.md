# Sphinx GitHub Pages Generator 0.1.0, released 2022-06-15
Code name: Initial implementation

## Summary

This release provides an initial version of the Sphinx GitHub Pages Generator. It can be used to automatically build and commit or push the Sphinx-documentation of a project to a target GitHub branch. It also automatically creates an index.html file listing the created releases that can be used as an entrypoint for GithubPages.


## Features / Enhancements

  - #1: Moved from "https://github.com/exasol/bucketfs-utils-python"
  - #5: Added tests
  - #2: Added option to select source branch
  - #11: Added generation of index.html linking to all existing documentations
  - #20: Added GitHub Action for generating the documentation on release, added new source_origin parameter to support tags.
  - #24: Added entrypoint

## Bug Fixes

 - #12: Fixed incorrect usage of source_dir parameter
 - #26: Fixed missing trigger in workflow
 - #28: Fixed secrets in workflow not working if called via workflow call
  
## Documentation

  - #7 Added documentation pages


## Refactoring

  - #1: Rewrote .sh script in Python

## Security

