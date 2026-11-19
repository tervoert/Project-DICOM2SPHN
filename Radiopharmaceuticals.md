# Radiopharmaceuticals

A radiopharmaceutical (also called radiotracer or tracer) is a drug that contains a radioactive isotope, the **radionuclide**. It is used in nuclear medicine imaging, such as PET (Positron Emission Tomography) and SPECT (Single Photon Emission Computed Tomography). After administration, the radiopharmaceutical goes to a specific organ, tissue or process in the body. The radionuclide decays and emits radiation that the scanner detects, showing where the radiopharmaceutical is and how much of it there is.

A radiopharmaceutical has two parts:
* **The carrier molecule:** decides where the radiopharmaceutical goes in the body, e.g. glucose (fluorodeoxyglucose) to tissue with a high glucose uptake, such as many tumours.
* **The radionuclide:** the radioactive atom bound to the carrier molecule, e.g. fluorine-18.

During an imaging exam, a patient usually receives one radiopharmaceutical. Some studies use more than one, for example a dual-tracer PET study, or a PET/CT with a radiopharmaceutical and an iodinated contrast agent (see [Contrast-Agents.md](Contrast-Agents.md)).


## An example: Fluorodeoxyglucose (18F-FDG)

Fluorodeoxyglucose F-18 (18F-FDG) is by far the most used PET radiopharmaceutical. It is a glucose analogue in which a hydroxyl group is replaced by radioactive fluorine-18. Cells take it up like glucose, but cannot break it down, so it accumulates in tissue with a high glucose metabolism, such as many tumours, the brain and inflamed tissue.

* **Radionuclide:** fluorine-18 decays by positron emission (about 97%) with a half-life of 109.77 minutes (6586.2 s).
* **Typical activity:** a few hundred MBq (megabecquerel), administered intravenously, about 60 minutes before the scan.
* **Free text in DICOM:** it is written in many ways, e.g. `FDG`, `18F-FDG`, `F18-FDG`, `[18F]FDG` or `Fluorodeoxyglucose`.

Because the radionuclide decays, the activity is always given together with the date and time at which it was measured. One hour after the measurement, only about 68% of the fluorine-18 activity is left.


## SPHN Radiopharmaceutical and related concepts

The SPHN schema (release 2026.1) has the following radiopharmaceutical related concepts:

| SPHN concept | Subclass of | Describes |
|---|---|---|
| SPHN Radiopharmaceutical Administration Event | SPHN Drug Administration Event | When and how (route) the radiopharmaceutical was administered |
| SPHN Radiopharmaceutical | SPHN Drug | The administered radiopharmaceutical, with its active ingredient, radionuclide(s) and volume |
| SPHN Substance | | The radiopharmaceutical substance itself (as active ingredient), e.g. fluorodeoxyglucose (18-F) |
| SPHN Radionuclide | SPHN Substance | The radionuclide, with its code, half-life, positron fraction and radioactivity |
| SPHN Radioactivity | | The measured activity of the radionuclide, with the date and time of the measurement |

As SPHN Radionuclide is a subclass of SPHN Substance, the SPHN schema also allows a radionuclide as active ingredient of a radiopharmaceutical. DICOM2SPHN adds the radionuclide through *has radionuclide*, and the radiopharmaceutical substance itself as active ingredient.

The 18F-FDG example above is described as:

    SPHN Radiopharmaceutical Administration Event
      ├─ has start datetime:             the injection date and time
      ├─ has administration route code:  47625008 | Intravenous route (qualifier value) |
      └─ has drug: SPHN Radiopharmaceutical
           ├─ has active ingredient: SPHN Substance
           │    └─ has code:             35321007 | Fluorodeoxyglucose (18-F) (substance) |
           └─ has radionuclide: SPHN Radionuclide
                ├─ has code:             77004003 | Fluorine-18 (substance) |
                ├─ has half life:        6586.2 s
                ├─ has positron fraction: 0.9673
                └─ has radioactivity: SPHN Radioactivity
                     ├─ has quantity:    e.g. 250 MBq
                     └─ has datetime:    the date and time of the activity measurement


## DICOM PET Isotope modules

DICOM defines two modules for PET radiopharmaceutical information:

 - The [PET Isotope](https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.8.9.2.html) module, used by legacy (single-frame) PET images. Besides coded information, it has free text attributes, such as Radiopharmaceutical (0018,0031) and Radiopharmaceutical Route (0018,1070), and time-only attributes, such as Radiopharmaceutical Start Time (0018,1072).

 - The [Enhanced PET Isotope](https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.8.22.4.html) module, used by enhanced (multi-frame) PET images. It has only coded information and DateTime attributes.

Both modules have the Radiopharmaceutical Information Sequence (0054,0016). Each item describes one administered radiopharmaceutical. In the enhanced module every item has a Radiopharmaceutical Agent Number (0018,9729); in the legacy module it does not.

    Radiopharmaceutical Information Sequence Attribute
    Tag                     (0054,0016)
    Type                    Legacy: Required, Empty if Unknown (2). Enhanced: Required (1)
    Keyword                 RadiopharmaceuticalInformationSequence
    Value Multiplicity      1
    Value Representation    Sequence (SQ)

### Coded radiopharmaceuticals and radionuclides

Each item of the Radiopharmaceutical Information Sequence can hold two codes:

    Radiopharmaceutical Code Sequence (0054,0304)   => the radiopharmaceutical, from DICOM CID 4021
    Radionuclide Code Sequence (0054,0300)          => the radionuclide, from DICOM CID 4020

For 18F-FDG these are, for example:

    Radiopharmaceutical Code Sequence item:
        Coding Scheme Designator (0008,0102)    => "SCT"
        Code Value (0008,0100)                  => "35321007"
        Code Meaning (0008,0104)                => "Fluorodeoxyglucose F^18^"

    Radionuclide Code Sequence item:
        Coding Scheme Designator (0008,0102)    => "SCT"
        Code Value (0008,0100)                  => "77004003"
        Code Meaning (0008,0104)                => "^18^Fluorine"

The `^18^` notation is the DICOM way to write a superscript mass number.

### DICOM radiopharmaceutical and radionuclide tables

DICOM provides tables with the codes of common radiopharmaceuticals and radionuclides:

| DICOM table | Content | Used for |
|---|---|---|
| [CID 4021. PET Radiopharmaceutical](https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4021.html) | PET radiopharmaceuticals | PET Isotope module |
| [CID 4020. PET Radionuclide](https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4020.html) | PET radionuclides | PET Isotope module |
| [CID 25. Radiopharmaceuticals](https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_25.html) | NM/SPECT radiopharmaceuticals | NM Isotope module |
| [CID 18. Isotopes in Radiopharmaceuticals](https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_18.html) | NM/SPECT radionuclides | NM Isotope module |

Unlike the contrast agent table, these tables use several coding schemes:
* **SCT** (SNOMED CT): most of the established radiopharmaceuticals, such as 18F-FDG, and all common radionuclides.
* **DCM** (DICOM): many newer radiopharmaceuticals that have no SNOMED CT code, such as most ^89^Zr labelled antibodies.
* **UMLS**, **NCIt** and **MSH** (MeSH): a few research radiopharmaceuticals.
* **SRT** (or the older **SNM3**): retired SNOMED-RT codes, still common in older DICOM data. For example, 18F-FDG was coded as `SRT` `C-B1031` instead of `SCT` `35321007`.

### Different SNOMED CT codes in DICOM compared to SPHN

As with contrast agents, DICOM often uses SNOMED CT *medicinal product* concepts ("Product containing ... (medicinal product)"), while SPHN needs *substances*. DICOM2SPHN therefore replaces these product codes by the radioactive substance, a subclass of SNOMED CT `89457008 | Radioactive isotope (substance) |`.

**Table 1:** Examples of DICOM CID 4021 codes replaced by SNOMED CT substance codes

| DICOM radiopharmaceutical | DICOM code | Code used by DICOM2SPHN |
|---|---|---|
| ATSM Cu^64^ | `422855001 \| Product containing copper (64-Cu) diacetyl-bis N-(4)-methylthiosemicarbazone (medicinal product) \|` | `423432002 \| Copper (64-Cu) diacetyl-bis N-(4)-methylthiosemicarbazone (substance) \|` |
| Butanol O^15^ | `422540000 \| Product containing oxygen (15-O) butanol (medicinal product) \|` | `423025003 \| Oxygen (15-O) butanol (substance) \|` |
| EDTA Ga^68^ | `423498000 \| Product containing gallium (68-Ga) ethylenediamine tetra-acetate (medicinal product) \|` | `424729005 \| Gallium (68-Ga) ethylenediamine tetra-acetate (substance) \|` |
| 3-N-Methylspiperone C^11^ | `771875003 \| Mespiperone (substance) \|` (not radioactive) | `423450009 \| Carbon (11-C) mespiperone (substance) \|` |
| Edotreotide Ga^68^ | UMLS `C2713594` | `1371422008 \| Gallium (Ga-68) labeled edotreotide (substance) \|` (new SNOMED CT concept) |

The complete mappings are in [data_converter.py](src/dicom2sphn/data_converter.py). Each replaced code has a comment with the original DICOM code and the reason.

The mappings also contain a few PET radiopharmaceuticals that are not (yet) in CID 4021 but have a SNOMED CT code, such as FAPI Ga^68^, Pentixafor Ga^68^ and Dotatate Cu^64^.

### Free text radiopharmaceutical

The legacy PET Isotope module also has the free text Radiopharmaceutical attribute:

    Radiopharmaceutical Attribute
    Tag                     (0018,0031)
    Type                    Optional (3)
    Keyword                 Radiopharmaceutical
    Value Multiplicity      1
    Value Representation    Long String (LO)
    Example Values          FDG, 18F-FDG, [18F]FDG, Fluorodeoxyglucose, NaF

Many PET images only have this free text, and no Radiopharmaceutical Code Sequence. DICOM2SPHN searches the text with a regular expression for each radiopharmaceutical and each radionuclide. The expressions accept common spellings and synonyms, such as `18F`, `F18`, `F-18`, `[18F]` and `fluorine-18`, and other names, such as `NaF` for sodium fluoride F^18^ or `Herceptin` for trastuzumab ^89^Zr.

Some examples of what is found:

| Free text | Radiopharmaceutical | Radionuclide |
|---|---|---|
| `18F-FDG` | `35321007 \| Fluorodeoxyglucose (18-F) (substance) \|` | `77004003 \| Fluorine-18 (substance) \|` |
| `FDG` | `35321007 \| Fluorodeoxyglucose (18-F) (substance) \|` | Fluorine-18, derived from the radiopharmaceutical |
| `NaF` | `129501009 \| Sodium fluoride (18-F) (substance) \|` | Fluorine-18, derived from the radiopharmaceutical |
| `Ga68-PSMA-11` | `1371531005 \| Gallium (Ga-68) labeled gozetotide (substance) \|` | `35337001 \| Gallium-68 (substance) \|` |
| `68Ga-PSMA I&T` | `1359969008 \| Gallium (68-Ga) labeled prostate specific membrane antigen (substance) \|` | `35337001 \| Gallium-68 (substance) \|` |
| `Ga68-PSMA` | `1359969008 \| Gallium (68-Ga) labeled prostate specific membrane antigen (substance) \|` | `35337001 \| Gallium-68 (substance) \|` |

For Ga-68 PSMA, the code depends on how specific the text is:
* **PSMA-11** (e.g. `PSMA-11`, `PSMA-HBED-CC`, `gozetotide`, `Illuccix`, `Locametz`) gives the specific concept `1371531005 | Gallium (Ga-68) labeled gozetotide (substance) |`.
* **PSMA-617** with a Ga-68 label gives the DICOM code `126759 | PSMA-617 Ga^68^ |`.
* **PSMA I&T** with a Ga-68 label gives the general concept `1359969008 | Gallium (68-Ga) labeled prostate specific membrane antigen (substance) |`, as SNOMED CT has no specific concept for PSMA I&T. The Ga-68 label is required, because PSMA I&T is also used with lutetium-177 for therapy.
* **Ga-68 PSMA without a ligand** (e.g. `Ga68-PSMA`, `68Ga-PSMA`, `[68Ga]PSMA`) also gives the general concept `1359969008`, as the ligand is unknown.


## How DICOM2SPHN maps the DICOM PET Isotope information to SPHN

The mapping is implemented in [dicom_pet_isotope_module_reader.py](src/dicom2sphn/dicom_pet_isotope_module_reader.py). Each item of the Radiopharmaceutical Information Sequence gives one SPHN Radiopharmaceutical Administration Event.

### Overview

| SPHN property | DICOM source |
|---|---|
| Radiopharmaceutical Administration Event: *has start datetime* | Radiopharmaceutical Start DateTime (0018,1078), or Radiopharmaceutical Start Time (0018,1072) completed with a date (legacy only) |
| Radiopharmaceutical Administration Event: *has end datetime* | Radiopharmaceutical Stop DateTime (0018,1079), or Radiopharmaceutical Stop Time (0018,1073) completed with a date (legacy only) |
| Radiopharmaceutical Administration Event: *has administration route code* | Administration Route Code Sequence (0054,0302), or the free text Radiopharmaceutical Route (0018,1070), legacy only |
| Radiopharmaceutical: *has active ingredient* (SPHN Substance) | Radiopharmaceutical Code Sequence (0054,0304), or the free text Radiopharmaceutical (0018,0031), legacy only |
| Radiopharmaceutical: *has quantity* | Radiopharmaceutical Volume (0018,1071), in mL |
| Radionuclide: *has code* | Radionuclide Code Sequence (0054,0300), or found in the free text Radiopharmaceutical (0018,0031), or derived from the radiopharmaceutical |
| Radionuclide: *has half life* | Radionuclide Half Life (0018,1075), in s |
| Radionuclide: *has positron fraction* | Radionuclide Positron Fraction (0018,1076), as a fraction (0..1) |
| Radioactivity: *has quantity* | Radionuclide Total Dose (0018,1074), in Bq in DICOM, converted to MBq for SPHN |
| Radioactivity: *has datetime* | The radiopharmaceutical start datetime (DICOM measures the total dose at the start time) |

Radiopharmaceutical Specific Activity (0018,1077), Radiopharmaceutical Administration Event UID (0008,3012) and Radiopharmaceutical Agent Number (0018,9729) are read and logged, but not mapped to SPHN. The Intervention Drug Information Sequence (0018,0026) is not processed.

### Finding the radiopharmaceutical and the radionuclide

For each item, DICOM2SPHN uses the first source that gives a result:

**Radiopharmaceutical**
1. the Radiopharmaceutical Code Sequence;
2. the free text Radiopharmaceutical attribute (legacy only). This is only used when exactly one radiopharmaceutical is found in it.

**Radionuclide**
1. the Radionuclide Code Sequence;
2. the free text Radiopharmaceutical attribute (legacy only), e.g. the `18F` in `18F-FDG`. Again, only when exactly one radionuclide is found;
3. the name of the radiopharmaceutical, e.g. the `F^18^` in `Fluorodeoxyglucose F^18^`.

So a coded radiopharmaceutical without a Radionuclide Code Sequence still gets its radionuclide. When neither a radiopharmaceutical nor a radionuclide is found, no administration event is created.

### Half-life and positron fraction

When DICOM has no Radionuclide Half Life or Radionuclide Positron Fraction, DICOM2SPHN uses the reference values of the radionuclide. These come from the [IAEA LiveChart of Nuclides](https://nds.iaea.org/relnsd/v1/data) (evaluated ENSDF data). When DICOM does have a value, it is kept, and a warning is logged if it differs from the reference value by more than 1% (half-life) or 0.01 (positron fraction).

### Coding schemes in SPHN

An SPHN Code can only use the coding schemes that DICOM2SPHN supports for SPHN, such as SNOMED CT and DCM. Radiopharmaceuticals that DICOM codes in UMLS, NCIt or MeSH therefore get no active ingredient. Their radionuclide is still added, derived from the name.

### Unknown codes

DICOM codes that are not in the mapping are not converted to SPHN codes. They are logged at debug level, so that the mapping tables can be extended.


## Common problems

### Start date and time

The legacy PET Isotope module has only an optional start and stop *time*:

    Radiopharmaceutical Start Time Attribute
    Tag                     (0018,1072)
    Type                    Optional (3)
    Keyword                 RadiopharmaceuticalStartTime
    Value Multiplicity      1
    Value Representation    Time (TM)

Newer data, and the enhanced module, use the Radiopharmaceutical Start DateTime (0018,1078), with Value Representation DateTime (DT). DICOM2SPHN uses it first; it may include a UTC offset, otherwise the DICOM timezone is used.

**Completing the date.** A time without a date is combined with the date of a reference datetime, in the same way as for contrast agents: the acquisition datetime, otherwise the series datetime, otherwise the study datetime. The time is moved one day back or forward when it is more than 23 hours after or before the reference datetime. This happens, for example, when the radiopharmaceutical was injected before midnight and the scan started after midnight.

**Estimating a missing start time.** When there is no start date or time, DICOM2SPHN uses the series datetime, otherwise the acquisition datetime, otherwise the study datetime. Unlike contrast agents, there is no configurable fallback: when none of these is available, no administration event is created.

A stop datetime before the start datetime is not used.

### Radioactivity without a measurement time

The radioactivity of a radionuclide is only meaningful together with the time of measurement, because it decreases with the half-life. DICOM2SPHN only adds the date and time to the SPHN Radioactivity when the start datetime comes from DICOM. When it was estimated from the series, acquisition or study datetime, the radioactivity has no datetime, so that an estimate is not presented as a measurement time.

### Multiple radiopharmaceuticals or radionuclides in free text

When the free text Radiopharmaceutical attribute mentions more than one radiopharmaceutical (or radionuclide), it is unknown which one was administered in this item. DICOM2SPHN then uses none of them, and logs this at debug level.

### Only one administration route

An SPHN Radiopharmaceutical Administration Event can have only one administration route. When DICOM gives multiple routes, no route is added to the event.

### NM and SPECT

The mapping tables for NM/SPECT radiopharmaceuticals (CID 25) and radionuclides (CID 18), with their half-lives, are already in [data_converter.py](src/dicom2sphn/data_converter.py). The NM Isotope module of NM and SPECT images is not read yet, so these tables are not used yet.
