#!/usr/bin/env python
# command line interface
import click
from pathlib import Path
from .main import main

@click.command()
@click.option("--output_file", "-o", help="The JSON medical imaging metadata output file", default="output.txt")
@click.option("--config_file", "-c", help="Specify a configuration file", default="config.toml")
@click.option("--patient_id",  "-p", help="Specify a DICOM PatientID", default="C3L-00422") # Default patient is from the CPTAC-LUAD study, obtained from TCIA
def cli(output_file: str, config_file: str, patient_id: str) -> None:
    """Run the command line interface."""

    output_file_path = Path(output_file)
    config_file_path = Path(config_file)

    main(output_file_path, config_file_path, patient_id)


if __name__ == "__main__":
    cli()