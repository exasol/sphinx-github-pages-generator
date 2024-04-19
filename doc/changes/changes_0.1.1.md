# Sphinx GitHub Pages Generator 0.1.1, released YYYY-MM-DD
Code name: TBD

## Summary

TBD

## Features / Enhancements



## Bug Fixes

   - #35: Fix Check the documentation build action failing because of empty tag list

## Documentation


## Refactoring

  - #22: Fixed multiple asserts in tests
  - #19: Replaced logging outputs
  - #23: Changed Poe to Nox
  - #4: Added click to parse arguments and fixed CLI parameter names
  - #16: Changed path-like parameters from String to Path
  - #34: Changed "push-enabled" parameter to Bool
  - #41: Updated importlib_resources and Poetry in GH workflows
  - Removed setup.py, installation via wheel from Github or poetry env should be unaffected

## Security

  - ReDoS in py library CVE ID: CVE-2022-42969: 
        The affected code is not used used by our project itself, nor by the dependencies pulling in the vulnerable library.
          Checked dependencies:
             * Nox (Code search)
             * Pytest (Code search + [Tracking-Issue] (https://github.com/pytest-dev/pytest/issues/10392))
  - Dependabot alerts for GitPython, markdown-it-py, Certifi fixed
  - Dependabot alerts fixed with relock and Poetry updated to 1.8.0 in GitHub actions
  
##Documentation

  - #38: Adjusted documentation to reflect latest changes

