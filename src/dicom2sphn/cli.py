#!/usr/bin/env python
# command line interface
import sys

import click

from .main import main


@click.command()
@click.option("--patient_id", "-p", help="Specify a DICOM PatientID", default="C3L-00422") # Default patient is from the CPTAC-LUAD study, obtained from TCIA
@click.option("--output_file_path_specification", "-o", help="The output file path specfication for the JSON file intended for the SPHN Connector", default="output/output_patient_{patient_id}_{file_id}.json")
@click.option("--config_file", "-c", help="Specify a configuration file", default="config.toml")
def cli(patient_id: str, output_file_path_specification: str, config_file: str) -> None:
    """Run the command line interface.

    \b
    Exit codes:
      0  success, JSON exported
      1  error (invalid input parameters or configuration)
      2  nothing exported (no subject pseudo identifier and/or no imaging procedures)
    """

    sys.exit(main(patient_id, output_file_path_specification, config_file)) # allows the exit code from main to be propagated to the shell


if __name__ == "__main__":
    cli()