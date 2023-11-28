# Neighborly Documentation

Neighborly uses Sphinx to build the documentation from reStructured Text files. The latest version of the live docs can be found on [Read the Docs](https:/neighborly.readthedocs.io/en/latest/index.html).

The docs is made up of two parts:

1. Wiki pages that explain Neighborly's core concepts and abstractions
2. Documentation for the Python source code

## Building the docs

**Note:** All file paths provided below are relative to `neighborly/docs`

Whenever new source code is added, run the following command to have sphinx-autodoc generate the proper documentation pages. All these pages are stored in the `./source/api` folder to keep them separated from the hand-authored wiki pages.

```bash
sphinx-apidoc -o ./source/api ../src/neighborly
```

Finally, you can build the html files with the command below

```bash
# macOS/Linux
make html

# Windows
./make.bat html
```
