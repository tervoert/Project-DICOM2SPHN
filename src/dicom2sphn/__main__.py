import os
import sys

# In order to enable calling the command-line interface directly from the source tree, i.e. as python src/dicom2sphn, 
# this hack could be placed:
if not __package__:
    # Make CLI runnable from source tree with
    #    python src/package
    package_source_path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, package_source_path)


# This file is the entry point for the package when run as a script. 
# It imports the main function from the cli module and executes it. 
# This allows users to run the package directly from the command line without needing to specify the module path.
# python -m dicom2sphn
if __name__ == "__main__":
    from dicom2sphn.cli import cli
    cli()
