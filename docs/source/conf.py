import os
import sys
from datetime import date

sys.path.insert(0, os.path.abspath("../../src"))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Neighborly"
copyright = f"2023-{date.today().year}, Shi Johnson-Bey"
author = "Shi Johnson-Bey"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
]

# Napoleon settings
napoleon_numpy_docstring = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = True
napoleon_attr_annotations = True

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]
html_extra_path = [".nojekyll"]

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = "_static/images/NeighborlyLogo.png"

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "_static/images/NeighborlyLogo.ico"
