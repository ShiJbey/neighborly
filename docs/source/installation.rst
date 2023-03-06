Installation
============

Neighborly is available to install from PyPI. This will install the latest official
release.

.. code-block:: console

    pip install neighborly


If you want to install the most recent changes that have not been uploaded to
PyPI, you can install it by cloning the main branch of this repo and installing that.

.. code-block:: console

    pip install git+https://github.com/ShiJbey/neighborly.git


Installing for local development
--------------------------------

If you wish to download a Neighborly for local development or want to play around with
any of the samples, you need to clone or download this repository and install
using the *editable* flag (-e). Please see the instructions below. This will install
a Neighborly into the virtual environment along with all its dependencies and a few
addition development dependencies such as *black* and *isort* for code formatting.

.. code-block:: console

    # Step 1: Clone Repository
    git clone https://github.com/ShiJbey/neighborly.git

    # Step 2a: Create and activate python virtual environment
    cd neighborly

    # Step 2b: For Linux and MacOS
    python3 -m venv venv
    source ./venv/bin/activate

    # Step 2b: For Windows
    python -m venv venv
    ./venv/Scripts/Activate

    # Step 3: Install local build and dependencies
    python -m pip install -e ".[development]"

Run the following command in the console to ensure that everything was
installed properly. It should return "neighborly" followed by the most recent
version number uploaded to PyPI.

.. code-block:: console

    $ neighborly --version

Now you're ready to start creating your own simulations!
