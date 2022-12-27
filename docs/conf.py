# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../src'))


# -- Project information -----------------------------------------------------

project = 'AI-Boardgame'
copyright = '2022, Deák Árpád'
author = 'Deák Árpád'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx_rtd_theme',
    'sphinx_qt_documentation',
]
add_module_names = False

# Add any paths that contain templates here, relative to this directory.
templates_path = []

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '.venv', 'build' , 'docs', '.vscode', 'AI_boardgame.egg-info']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []


html_title = 'AI-Boardgame'
html_show_sourcelink = False

# -- Extension configuration -------------------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
}
qt_documentation = 'PyQt6'

autosummary_generate = True
autoclass_content = "both"
autodoc_default_options = {
    'members': True,
    'member-order': 'groupwise',
    'show-inheritance': True,
    'class-doc-from': 'both',
    'ignore-module-all': True
    # 'imported-members': True
}
autodoc_preserve_defaults = True


# -- Options for LaTeX output ------------------------------------------------

latex_engine = 'pdflatex'
latex_documents = [('index', 'api.tex', project, author, 'manual')]
latex_elements = {
    'papersize':'a4paper',
    'pointsize':'12pt',
    'maketitle': '',
    'fncychap': '\\usepackage[Conny]{fncychap}',
}
