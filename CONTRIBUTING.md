# Contributing to Neighborly

Contributions are welcome. Below is a list of areas that someone could contribute. If you create a new Neighborly
plugin, please message me. I will include a link to your plugin's GitHub repository. If you want to contribute to the
core code, fork this repository, make your changes, and submit a pull request with a description of your contribution.
Please remember that this project is a tool for creativity and learning. I have a
[code of conduct](./CODE_OF_CONDUCT.md) to encourage healthy collaboration, and I will enforce it if necessary.

1. Proposing and implementing new features
2. Fixing bugs
3. Providing optimizations
4. Submitting issues
5. Contributing tutorials and how-to guides
6. Fixing grammar and spelling errors
7. Creating new samples and plugins

## Code Style

All code contributions should adhere to the [_Black_](https://black.readthedocs.io/en/stable/) code formatter, and sorts
should comply with [_isort_](https://pycqa.github.io/isort/). Both tools are downloaded when installing development
dependencies and should be run before submitting a pull request.

## Documenting Python code

Neighborly uses [Numpy-style](https://numpydoc.readthedocs.io/en/latest/format.html) docstrings in code. When adding
docstrings for existing or new code, please use the following formatting guides:

- [Sphinx Napoleon Plugin for processing Numpy Docstrings](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html)
- [Example Numpy Style Docstrings](https://www.sphinx-doc.org/en/master/usage/extensions/example_numpy.html#example-numpy)

## Contributing unit tests

To contribute unit tests:

1. Fork the repo.
2. Add your test(s) to the `tests/` directory.
3. Submit a pull request with a description of your test cases.

Your commits should only contain changes to files within the `tests/` directory. If you change any files in other parts
of the project, your pull request will be rejected.

# Licensing

This project is licensed under the [MIT License](./LICENSE). By submitting a contribution to this project, you are
agreeing that your contribution will be released under the terms of this license.
