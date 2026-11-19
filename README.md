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
| `[dicom_options]` | Allowed SOP classes (CT, MR and PET by default), local timezone, and fallback dates and times for studies and contrast administrations |
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

---

## License

This project is licensed under the **GNU General Public License v3.0 or later** (GPL-3.0-or-later). See [LICENSE](LICENSE).

## Author

Edwin ter Voert

---

### Keywords

Medical Imaging, Metadata, Imaging Data, Secondary Use, SPHN Framework, SPHN Connector, Semantic Interoperability, RDF Schema, FAIR Principles, DICOM, DICOMweb, Python, Ontology, International Standards, SNOMED CT, UCUM, DICOM DCM
