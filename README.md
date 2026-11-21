# DICOM2SPHN

**DICOM2SPHN** is a Python example package that reads medical imaging metadata from a DICOMweb server (PACS) and exports it as JSON for the [SPHN Connector](https://sphn-semantic-framework.readthedocs.io/en/latest/sphn_framework/sphn_connector.html#). The SPHN Connector converts this JSON into RDF data that follows the **SPHN RDF schema, release 2026.1**.

The aim is to make imaging metadata available for secondary use in research, in a semantically interoperable and FAIR way, following the Swiss Personalized Health Network ([SPHN](https://sphn.ch/)) Semantic Interoperability Framework.

> **Status:** Alpha (version 0.1.0). This is an example and research implementation, not a certified clinical product.

---

## Features

- **DICOMweb input**: queries a DICOMweb server (e.g. Orthanc) for one patient and walks through all their studies, series, instances and frames.
- **SPHN concepts**: maps DICOM metadata to more than 60 SPHN concepts, among others:
  - `ImagingProcedure`, `ImagingSeries` and `ImagingFrame`, plus the modality-specific variants for **CT**, **MR**, **PET** and **X-ray**;
  - `ContrastAgentAdministrationEvent`, `ContrastAgent`, `ContrastAgentActiveIngredient` and `FlowProfileInterval`;
  - `RadiopharmaceuticalAdministrationEvent`, `Radiopharmaceutical` and `Radionuclide`;
  - `CardiacSynchronization` and `RespiratorySynchronization`, `ImagingDevice`, `DataFile`, `BodySite`, `Laterality`, `BodyPosition`, `AnatomicalProjection`;
  - patient context: `SubjectPseudoIdentifier`, `AdministrativeSex`, `Age`, `BodyWeight`, `BodyHeight` and `BodyMassIndex`.
- **Coded terminologies**: maps DICOM coded values (DCM, SNOMED CT, including the retired SNOMED-RT/SRT codes found in older data) to SNOMED CT and UCUM codes. Examples are contrast agents and ingredients (DICOM Tables CID 12/13), administration routes (DICOM Table CID 11), and radiopharmaceuticals and radionuclides (DICOM Tables CID 25/18, 4020/4021).
- **Legacy and enhanced DICOM**: reads both the legacy and the enhanced Contrast/Bolus module, the PET Isotope module, and per-frame functional groups of enhanced multi-frame objects.
- **Timezones**: DICOM local dates and times become ISO 8601 date-times, using `TimezoneOffsetFromUTC` when it is present and a configurable IANA timezone otherwise.
- **Optional de-duplication**: can store only unique imaging procedures, series and/or frames, to reduce redundant metadata.
- **Validated models**: every SPHN concept is a [pydantic](https://docs.pydantic.dev/) model that checks its values against the SPHN RDF schema (value sets, cardinalities, units).

---

## How it works

```
 DICOMweb server (PACS)
          │  QIDO-RS / WADO-RS
          ▼
 Patient ─► Study ─► Series ─► Instance ─► Frame       (dw_*_processor.py)
          │
          ▼
 DICOM module readers                                  (dicom_*_reader.py)
          │  contrast/bolus, PET isotope, device, frame, code sequences, ...
          ▼
 SPHN concept objects (pydantic)                        (sphn_concepts/)
          │
          ▼
 JSON for the SPHN Connector ──► SPHN Connector ──► RDF (SPHN schema 2026.1)
```

---

## Requirements

- Python **3.14** or newer
- Access to a **DICOMweb** server (for example [Orthanc](https://www.orthanc-server.com/) with the DICOMweb plugin)
- The **SPHN RDF schema** file (`.ttl`) of release **2026.1**

Python dependencies: `click`, `pydicom`, `pynetdicom`, `dicomweb-client`, `numpy`, `rdflib`, `pydantic` and `tzdata`.

---

## Installation

### With conda (recommended)

```powershell
git clone https://github.com/tervoert/Project-DICOM2SPHN.git
cd Project-DICOM2SPHN
conda env create --prefix .\.conda -f .\environment.yaml
conda activate .\.conda
pip install -e .
```

See [README-setup-conda-locally.md](README-setup-conda-locally.md) for more details on activating, updating and deactivating the environment.

### With pip

```bash
git clone https://github.com/tervoert/Project-DICOM2SPHN.git
cd Project-DICOM2SPHN
pip install -e .
```

---

## Configuration

Copy the example configuration and adapt it to your environment:

```bash
cp config-example.toml config.toml
```

The main sections are:

| Section | Purpose |
|---|---|
| `[SPHN]` | Path to the SPHN RDF schema file (`sphn_rdf_schema_file_path`) |
| `[SPHN.data_provider]` | Category, department and institution code of the data provider |
| `[SPHN.source_system]` | Name, purpose and category of the source system (e.g. the PACS) |
| `[dicomweb_api_user]` | DICOMweb base URL, username, password and request timeout |
| `[dicom_options]` | Allowed SOP classes (by default all image SOP classes, see [Supported DICOM SOP Classes](Supported_DICOM_SOP_Classes.md)), local timezone, and fallback dates and times for studies and contrast administrations |
| `[data_processing]` | Store only unique imaging procedures, series and/or frames |

> **Note:** `config.toml` contains credentials. Do not commit it to version control.

---

## Usage

```bash
dicom2sphn --patient_id <DICOM PatientID> --config_file config.toml
```

or

```bash
python -m dicom2sphn -p <DICOM PatientID> -c config.toml
```

| Option | Short | Default | Description |
|---|---|---|---|
| `--patient_id` | `-p` | `C3L-00422` | The DICOM PatientID to export |
| `--output_file_path_specification` | `-o` | `output/output_patient_{patient_id}_{file_id}.json` | Output file path. It must contain `{patient_id}` and `{file_id}` |
| `--config_file` | `-c` | `config.toml` | The configuration file |

The default patient comes from the CPTAC-LUAD collection of [The Cancer Imaging Archive (TCIA)](https://www.cancerimagingarchive.net/).

**Exit codes**

| Code | Meaning |
|---|---|
| `0` | Success, the JSON was exported |
| `1` | Error: invalid input parameters or configuration |
| `2` | Nothing exported: no subject pseudo identifier and/or no imaging procedures found |

---

## Processing a list of patients

The script `scripts/run_patient_list.py` runs DICOM2SPHN for every DICOM PatientID in a text file. The file contains one PatientID per line. Empty lines and lines starting with `#` are ignored, and a PatientID that appears more than once is processed only once.

```bash
python scripts/run_patient_list.py patient_ids.txt -c config.toml
```

Process four patients at a time and write the output of each patient to its own log file:

```bash
python scripts/run_patient_list.py patient_ids.txt -c config.toml --jobs 4 --log_dir output/logs
python scripts/run_patient_list.py patient_ids.txt -c config.toml --output_dir D:/sphn_export
```

| Option | Short | Default | Description |
|---|---|---|---|
| `patient_id_file` | | (required) | Text file with one DICOM PatientID per line |
| `--config_file` | `-c` | `config.toml` | The configuration file |
| `--output_file_path_specification` | `-o` | `output/output_patient_{patient_id}_{file_id}.json` | Output file path. It must contain `{patient_id}` and `{file_id}` |
| `--output_dir` | `-d` | (none) | Folder for the output JSON files. Replaces the folder part of `-o`; the file name pattern is kept. The folder is created if it does not exist |
| `--jobs` | `-j` | `1` | Number of patients processed in parallel |
| `--log_dir` | | (none) | Write the output of each patient to `<log_dir>/<PatientID>.log` instead of the console |
| `--stop_on_error` | | off | Stop at the first patient that returns an error. With `--jobs` > 1, patients that are already running are finished first |

Each patient runs in a separate `python -m dicom2sphn` process. The script works even if the package was not installed with `pip install -e .`. Without `--log_dir`, the output is printed to the console. With `--jobs` > 1, the output of each patient is printed as one block when that patient is finished, so the output of different patients is not mixed.

At the end, the script prints a summary of how many patients were exported, had an error or had nothing to export, and lists the PatientIDs that failed. The script returns exit code `1` if at least one patient had an error, and `0` otherwise.

> **Note:** each parallel job opens its own DICOMweb session. Keep `--jobs` small (for example 2 to 4), so that the DICOMweb server is not overloaded.

### Making a patient list from an Orthanc server

The examples below write all PatientIDs on an [Orthanc](https://www.orthanc-server.com/) server to `patient_ids.txt`. Replace the URL, username and password (`orthanc:orthanc`) with your own.

With the DICOMweb API (QIDO-RS) and [jq](https://jqlang.org/):

```bash
curl -s -u orthanc:orthanc "http://localhost:8042/dicom-web/studies?includefield=00100020" \
  | jq -r '[.[]."00100020".Value[]?] | unique | .[]' > patient_ids.txt
```

With the Orthanc REST API and jq:

```bash
curl -s -u orthanc:orthanc "http://localhost:8042/patients?expand" \
  | jq -r '.[].MainDicomTags.PatientID' | sort -u > patient_ids.txt
```

With PowerShell on Windows (no jq needed):

```powershell
$cred = Get-Credential   # for example: orthanc / orthanc
(Invoke-RestMethod -Uri "http://localhost:8042/patients?expand" -Credential $cred -AllowUnencryptedAuthentication).MainDicomTags.PatientID |
  Sort-Object -Unique | Set-Content -Encoding utf8 patient_ids.txt
```

You can edit the file afterwards, for example to remove patients or to add `#` comments.

> **Note:** a DICOMweb server can limit the number of results of one QIDO-RS query. If the list seems too short, check the server settings, or use the Orthanc REST API example.

---

## Output

The program writes one JSON file per patient, in the *PatientRecord* format of the SPHN Connector. It contains:

- the `sphn:DataRelease`, `sphn:DataProvider` and `sphn:SubjectPseudoIdentifier`;
- a `content` section with, per SPHN core concept, the list of instances (e.g. `sphn:ImagingProcedure`, `sphn:ComputedTomographyImagingSeries`, `sphn:ContrastAgentAdministrationEvent`, `sphn:RadiopharmaceuticalAdministrationEvent`, `sphn:SourceSystem`);
- references between instances by `id`, with a `target_concept` wherever the schema allows more than one concept type (for example `hasImagingSeries`, `hasDataFile` and `hasSynchronization`).

The output can be validated against the JSON schema that the SPHN Connector generates for a project, before it is loaded.

---

## Project structure

```
Project-DICOM2SPHN/
├── config-example.toml               Example configuration
├── environment.yaml                  Conda environment
├── pyproject.toml                    Package definition
├── Contrast-Agents.md                Background on contrast agents
├── Contrast-Agent-Trade-Names-and-Ingredients.md
├── Radiopharmaceuticals.md           Background on radiopharmaceuticals
├── Supported_DICOM_SOP_Classes.md    The DICOM SOP Classes that can be processed
├── scripts/
│   └── run_patient_list.py           Runs DICOM2SPHN for every PatientID in a text file
└── src/dicom2sphn/
    ├── cli.py, main.py               Command line interface and main program
    ├── import_config_settings.py     Reads and checks the configuration
    ├── dw_*_processor.py             DICOMweb processing per level (patient, study, series, instance, frame)
    ├── dicom_*_reader.py             Readers for DICOM modules (contrast/bolus, PET isotope, device, frame, ...)
    ├── data_converter.py             DICOM-to-SPHN code mappings (SNOMED CT, UCUM, DCM)
    ├── data_store.py                 Collects the SPHN concepts and writes the JSON
    ├── sphn_schema_graph.py          Loads the SPHN RDF schema (rdflib)
    └── sphn_concepts/                One pydantic model per SPHN concept
```

---

## Background documentation

- [Contrast-Agents.md](Contrast-Agents.md): how contrast agents, their ingredients and administrations are represented.
- [Contrast-Agent-Trade-Names-and-Ingredients.md](Contrast-Agent-Trade-Names-and-Ingredients.md): trade names and active ingredients of contrast agents.
- [Radiopharmaceuticals.md](Radiopharmaceuticals.md): how radiopharmaceuticals, their radionuclides and administrations are represented.
- [Supported_DICOM_SOP_Classes.md](Supported_DICOM_SOP_Classes.md): the DICOM SOP Classes that can be processed, with their modality, IOD and SPHN ImagingSeries and ImagingFrame.

---

## License

This project is licensed under the **GNU General Public License v3.0 or later** (GPL-3.0-or-later). See [LICENSE](LICENSE).

## Author

Edwin ter Voert

---

### Keywords

Medical Imaging, Metadata, Imaging Data, Secondary Use, SPHN Framework, SPHN Connector, Semantic Interoperability, RDF Schema, FAIR Principles, DICOM, DICOMweb, Python, Ontology, International Standards, SNOMED CT, UCUM, DICOM DCM
