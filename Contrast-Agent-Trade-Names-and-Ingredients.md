# Medical Imaging Contrast Agents: Trade Names and Ingredients

This list gives 89 medical imaging contrast agents by trade name, grouped by imaging modality and type. For each one it gives the manufacturer and the ingredients, coded in SNOMED CT (International Edition, 2026-10-01).

- **Manufacturer** is the current owner, or the successor company for discontinued products.
- **Active ingredients** are the substances that give the contrast effect. They become SPHN Contrast Agent Active Ingredient objects.
- **Inactive ingredients** are carriers or excipients. They are listed for completeness, but are not mapped to SPHN.

All ingredient codes are substances under `105590001 | Substance (substance) |`. Most are also under `385420005 | Contrast media (substance) |`, as SPHN requires for a [Contrast Agent Active Ingredient](https://www.biomedit.ch/rdf/sphn-schema/sphn#ContrastAgentActiveIngredient). The exceptions are `15158005 | Air (substance) |`, `109216000 | Gadopentetate dimeglumine (substance) |` and `414308003 | Meglumine gadobenate (substance) |`, which SPHN allows as additional codes.

See [Contrast-Agents.md](Contrast-Agents.md) for the background on contrast agents in DICOM and SPHN.

## How DICOM2SPHN uses this list

Many DICOM images have no coded contrast agent, only the free text Contrast/Bolus Agent (0018,0010) attribute, for example `OMNIPAQUE`, `CC MAGNEVIST` or `Visipaque-320 100ml`. DICOM2SPHN searches this free text for the trade names in this list, and also for active ingredient names (e.g. "Iohexol") and active element names (e.g. "Gadolinium").

When a trade name is found, DICOM2SPHN creates an SPHN Contrast Agent with:
- one SPHN Contrast Agent Active Ingredient for each **active ingredient** of the trade name, with the SNOMED CT code from this list;
- an SPHN Drug Article whose name is the trade name, followed by the concentration and dose when they follow the trade name in the text. For example, `Omnipaque 300 100 ml` gives the article name `Omnipaque-300 100ml`.

A concentration is only recognized when it is one of the common values 30, 60, 76, 140, 150, 160, 180, 200, 240, 250, 260, 270, 282, 292, 300, 320, 350, 360, 370, 380, 390 or 400 (mg iodine/mL). A dose is a number with the unit mL (or cc) or mg.

The list is implemented in [data_converter.py](src/dicom2sphn/data_converter.py), in these dictionaries:

| Dictionary | Content |
|---|---|
| `contrast_agent_trade_name_2_manufacturer_and_ingredient_name` | Trade name → manufacturer, active ingredients and inactive ingredients |
| `contrast_agent_active_ingredient_name_2_snomed_code` | Active ingredient name → SNOMED CT code |
| `contrast_agent_active_element_names_2_snomed_code` | Active element name (e.g. "Iodine") → SNOMED CT code |
| `contrast_agent_names_2_patterns` | Trade name, ingredient name or element name → regular expression for the free text search, including common misspellings (e.g. "Amipak" for "Amipaque") |

The free text search is implemented in [extract_contrast_agents.py](src/dicom2sphn/extract_contrast_agents.py). When you add a contrast agent to this list, also add it to these dictionaries, and the other way around.

## Overview

| Modality | Type | Agents |
|---|---|---|
| CT/X-ray | Iodine-based | 46 |
| CT/X-ray | Barium-based | 12 |
| CT/X-ray | Oil-based | 4 |
| MRI | Gadolinium-based | 15 |
| MRI | Iron-based | 4 |
| MRI | Manganese-based | 1 |
| Ultrasound | Microbubble-based | 7 |
| **Total** | | **89** |

## CT/X-ray (62)

### Iodine-based (46)

| Tradename | Manufacturer | Active ingredients | Inactive ingredients |
|---|---|---|---|
| **Amipaque** | GE | Metrizamide — `90733003` *Metrizamide (substance)* | — |
| **Angiovist** | Bayer | Diatrizoate Meglumine — `47192000` *Meglumine amidotrizoate (substance)*<br>Diatrizoate Sodium — `395875009` *Sodium amidotrizoate (substance)* | — |
| **Bilivist** | Bayer | Ipodate Sodium — `395877001` *Sodium iopodate (substance)* | — |
| **Cardiografin** | Bracco | Diatrizoate Meglumine — `47192000` *Meglumine amidotrizoate (substance)* | — |
| **Cholographin** | Bracco | Iodipamide Meglumine — `69783005` *Iodipamide meglumine (substance)* | — |
| **Cholographin Meglumine** | Bracco | Iodipamide Meglumine — `69783005` *Iodipamide meglumine (substance)* | — |
| **Cholographin Sodium** | Bracco | Iodipamide Sodium — `925002` *Sodium iodipamide (substance)* | — |
| **Conray** | Guerbet | Iothalamate Meglumine — `395757003` *Iothalamate meglumine (substance)* | — |
| **Cysto-Conray** | Guerbet | Iothalamate Meglumine — `395757003` *Iothalamate meglumine (substance)* | — |
| **Cystografin** | Bracco | Diatrizoate Meglumine — `47192000` *Meglumine amidotrizoate (substance)* | — |
| **Dionosil** | GSK | Propyliodone — `111158001` *Propyliodone (substance)* | — |
| **Gastrografin** | Bracco | Diatrizoate Meglumine — `47192000` *Meglumine amidotrizoate (substance)*<br>Diatrizoate Sodium — `395875009` *Sodium amidotrizoate (substance)* | — |
| **Gastrovist** | Bayer | Diatrizoate Meglumine — `47192000` *Meglumine amidotrizoate (substance)*<br>Diatrizoate Sodium — `395875009` *Sodium amidotrizoate (substance)* | — |
| **Hexabrix** | Guerbet | Ioxaglate Meglumine — `412228003` *Ioxaglate meglumine (substance)*<br>Ioxaglate Sodium — `412230001` *Ioxaglate sodium (substance)* | — |
| **Hypaque** | GE | Diatrizoate Sodium — `395875009` *Sodium amidotrizoate (substance)* | — |
| **Hypaque Meglumine** | GE | Diatrizoate Meglumine — `47192000` *Meglumine amidotrizoate (substance)* | — |
| **Imagenil** | Guerbet | Ioxilan — `409485008` *Ioxilan (substance)* | — |
| **Imagopaque** | GE | Iopentol — `1340015006` *Iopentol (substance)* | — |
| **Imeron** | Bracco | Iomeprol — `395753004` *Iomeprol (substance)* | — |
| **Iomeron** | Bracco | Iomeprol — `395753004` *Iomeprol (substance)* | — |
| **Iopamiro** | Bracco | Iopamidol — `395754005` *Iopamidol (substance)* | — |
| **Isopaque** | GE | Metrizoate — `395792006` *Metrizoate (substance)* | — |
| **Isovist** | Bayer | Iotrolan — `395758008` *Iotrolan (substance)* | — |
| **Isovue** | Bracco | Iopamidol — `395754005` *Iopamidol (substance)* | — |
| **MD** | Guerbet | Diatrizoate Meglumine — `47192000` *Meglumine amidotrizoate (substance)*<br>Diatrizoate Sodium — `395875009` *Sodium amidotrizoate (substance)* | — |
| **MD Gastroview** | Guerbet | Diatrizoate Meglumine — `47192000` *Meglumine amidotrizoate (substance)*<br>Diatrizoate Sodium — `395875009` *Sodium amidotrizoate (substance)* | — |
| **Niopam** | Bracco | Iopamidol — `395754005` *Iopamidol (substance)* | — |
| **Omnipaque** | GE | Iohexol — `395751002` *Iohexol (substance)* | — |
| **Optiray** | Guerbet | Ioversol — `395759000` *Ioversol (substance)* | — |
| **Oragrafin** | Bracco | Ipodate Sodium — `395877001` *Sodium iopodate (substance)*<br>Ipodate Calcium — `396003009` *Calcium iopodate (substance)* | — |
| **Oxilan** | Guerbet | Ioxilan — `409485008` *Ioxilan (substance)* | — |
| **Reno** | Bracco | Diatrizoate Meglumine — `47192000` *Meglumine amidotrizoate (substance)* | — |
| **Reno-Dip** | Bracco | Diatrizoate Meglumine — `47192000` *Meglumine amidotrizoate (substance)* | — |
| **Renografin** | Bracco | Diatrizoate Meglumine — `47192000` *Meglumine amidotrizoate (substance)*<br>Diatrizoate Sodium — `395875009` *Sodium amidotrizoate (substance)* | — |
| **Renovist** | Bracco | Diatrizoate Meglumine — `47192000` *Meglumine amidotrizoate (substance)*<br>Diatrizoate Sodium — `395875009` *Sodium amidotrizoate (substance)* | — |
| **Renovue** | Bracco | Iodamide Meglumine — `12801003` *Iodamide meglumine (substance)* | — |
| **Salpix** | Johnson & Johnson | Acetrizoate Sodium — `32836007` *Sodium acetrizoate (substance)* | Povidone — `396449009` *Povidone (substance)* |
| **Sinografin** | Bracco | Diatrizoate Meglumine — `47192000` *Meglumine amidotrizoate (substance)*<br>Iodipamide Meglumine — `69783005` *Iodipamide meglumine (substance)* | — |
| **Solutrast** | Bracco | Iopamidol — `395754005` *Iopamidol (substance)* | — |
| **Telebrix** | Guerbet | Ioxitalamate Meglumine — `712698009` *Ioxitalamate meglumine (substance)*<br>Ioxitalamate Sodium — `765359003` *Ioxitalamate sodium (substance)* | — |
| **Telepaque** | GE | Iopanoic Acid — `412227008` *Iopanoic acid (substance)* | — |
| **Ultravist** | Bayer | Iopromide — `395756007` *Iopromide (substance)* | — |
| **Urovist** | Bayer | Diatrizoate Meglumine — `47192000` *Meglumine amidotrizoate (substance)*<br>Diatrizoate Sodium — `395875009` *Sodium amidotrizoate (substance)* | — |
| **Vascoray** | Guerbet | Iothalamate Meglumine — `395757003` *Iothalamate meglumine (substance)*<br>Iothalamate Sodium — `395878006` *Sodium iothalamate (substance)* | — |
| **Visipaque** | GE | Iodixanol — `395750001` *Iodixanol (substance)* | — |
| **Xenetix** | Guerbet | Iobitridol — `704384003` *Iobitridol (substance)* | — |

### Barium-based (12)

| Tradename | Manufacturer | Active ingredients | Inactive ingredients |
|---|---|---|---|
| **Baro-Cat** | Guerbet | Barium Sulfate — `396014007` *Barium sulfate (substance)* | — |
| **Cheetah** | Guerbet | Barium Sulfate — `396014007` *Barium sulfate (substance)* | — |
| **E-Z-Cat** | Bracco | Barium Sulfate — `396014007` *Barium sulfate (substance)* | — |
| **E-Z-HD** | Bracco | Barium Sulfate — `396014007` *Barium sulfate (substance)* | — |
| **E-Z-PAQUE** | Bracco | Barium Sulfate — `396014007` *Barium sulfate (substance)* | — |
| **Liquid POLIBAR PLUS** | Bracco | Barium Sulfate — `396014007` *Barium sulfate (substance)* | — |
| **Readi-Cat** | Bracco | Barium Sulfate — `396014007` *Barium sulfate (substance)* | — |
| **Readi-Cat 2** | Bracco | Barium Sulfate — `396014007` *Barium sulfate (substance)* | — |
| **Readi-Cat 2 SMOOTHIE** | Bracco | Barium Sulfate — `396014007` *Barium sulfate (substance)* | — |
| **Tagitol** | Bracco | Barium Sulfate — `396014007` *Barium sulfate (substance)* | — |
| **Varibar** | Bracco | Barium Sulfate — `396014007` *Barium sulfate (substance)* | — |
| **VoLumen** | Bracco | Barium Sulfate — `396014007` *Barium sulfate (substance)* | — |

### Oil-based (4)

| Tradename | Manufacturer | Active ingredients | Inactive ingredients |
|---|---|---|---|
| **Ethiodol** | Guerbet | Ethiodized Oil — `109224005` *Ethiodized oil (substance)* | — |
| **Lipiodol** | Guerbet | Ethiodized Oil — `109224005` *Ethiodized oil (substance)* | — |
| **Myodil** | GSK | Iophendylate — `28121005` *Iophendylate (substance)* | — |
| **Pantopaque** | Eastman Kodak | Iophendylate — `28121005` *Iophendylate (substance)* | — |

## MRI (20)

### Gadolinium-based (15)

| Tradename | Manufacturer | Active ingredients | Inactive ingredients |
|---|---|---|---|
| **Ablavar** | Lantheus | Gadofosveset Trisodium — `425080008` *Gadofosveset trisodium (substance)* | — |
| **Clariscan** | GE | Gadoterate Meglumine — `712714000` *Gadoterate meglumine (substance)* | — |
| **Dotarem** | Guerbet | Gadoterate Meglumine — `712714000` *Gadoterate meglumine (substance)* | — |
| **Elucirem** | Guerbet | Gadopiclenol — `1363068006` *Gadopiclenol (substance)* | — |
| **Eovist** | Bayer | Gadoxetate Disodium — `440223009` *Gadoxetate disodium (substance)* | — |
| **Gadavist** | Bayer | Gadobutrol — `418351005` *Gadobutrol (substance)* | — |
| **Gadovist** | Bayer | Gadobutrol — `418351005` *Gadobutrol (substance)* | — |
| **Magnevist** | Bayer | Gadopentetate Dimeglumine — `109216000` *Gadopentetate dimeglumine (substance)* | — |
| **Multihance** | Bracco | Gadobenate Dimeglumine — `414308003` *Meglumine gadobenate (substance)* | — |
| **Omniscan** | GE | Gadodiamide — `396067007` *Gadodiamide (substance)* | — |
| **Optimark** | Guerbet | Gadoversetamide — `409476008` *Gadoversetamide (substance)* | — |
| **Primovist** | Bayer | Gadoxetate Disodium — `440223009` *Gadoxetate disodium (substance)* | — |
| **ProHance** | Bracco | Gadoteridol — `420600009` *Gadoteridol (substance)* | — |
| **Vasovist** | Lantheus | Gadofosveset Trisodium — `425080008` *Gadofosveset trisodium (substance)* | — |
| **Vueway** | Bracco | Gadopiclenol — `1363068006` *Gadopiclenol (substance)* | — |

### Iron-based (4)

| Tradename | Manufacturer | Active ingredients | Inactive ingredients |
|---|---|---|---|
| **Endorem** | Guerbet | Ferumoxides — `412390001` *Ferumoxide (substance)* | — |
| **Feraheme** | Covis | Ferumoxytol — `442951001` *Ferumoxytol (substance)* | — |
| **Feridex** | Covis | Ferumoxides — `412390001` *Ferumoxide (substance)* | — |
| **Resovist** | Neo Critical Care Pharma | Ferucarbotran — `421091005` *Ferucarbotran (substance)* | — |

### Manganese-based (1)

| Tradename | Manufacturer | Active ingredients | Inactive ingredients |
|---|---|---|---|
| **Teslascan** | IC Targets | Mangafodipir Trisodium — `410872002` *Mangafodipir trisodium (substance)* | — |

## Ultrasound (7)

### Microbubble-based (7)

| Tradename | Manufacturer | Active ingredients | Inactive ingredients |
|---|---|---|---|
| **Definity** | Lantheus | Perflutren — `409292001` *Perflutren (substance)* | — |
| **Levovist** | Bayer | Air — `15158005` *Air (substance)* | Galactose — `38182007` *Galactose (substance)*<br>Palmitic Acid — `87044003` *Palmitic acid (substance)* |
| **Lumason** | Bracco | Sulfur Hexafluoride Lipid Microspheres — `724034007` *Sulfur hexafluoride lipid microsphere (substance)* | — |
| **Luminity** | Lantheus | Perflutren — `409292001` *Perflutren (substance)* | — |
| **Optison** | GE | Perflutren — `409292001` *Perflutren (substance)* | — |
| **Sonazoid** | GE | Perflubutane — `419765001` *Perfluorobutane (substance)* | — |
| **SonoVue** | Bracco | Sulfur Hexafluoride Lipid Microspheres — `724034007` *Sulfur hexafluoride lipid microsphere (substance)* | — |

---

**Notes**

- **Magnevist and MultiHance** have the salt forms gadopentetate dimeglumine `109216000` and meglumine gadobenate `414308003`. These are not under `385420005 | Contrast media (substance) |`, but SPHN allows them as additional codes. The acid forms (gadopentetic acid, gadobenic acid) are under `385420005 | Contrast media (substance) |`.
- **Levovist:** the contrast effect comes from air microbubbles; galactose and palmitic acid are the carrier. `15158005 | Air (substance) |` is not under `385420005 | Contrast media (substance) |`, but SPHN allows it as an additional code.
- **Inactive ingredients** (galactose, palmitic acid and povidone) are listed for completeness only. DICOM2SPHN does not add them to the SPHN Contrast Agent.
- **Several active ingredients:** a trade name can have more than one active ingredient (e.g. Angiovist, Gastrografin, Hexabrix). DICOM2SPHN then adds all of them to the same SPHN Contrast Agent.
- **Several trade names for one product:** some products are sold under different trade names in different countries (e.g. Gadavist/Gadovist, Eovist/Primovist, Isovue/Iopamiro/Niopam). Each trade name has its own row.
- SNOMED CT codes were checked against tx.fhir.org.
- This list and the dictionaries in [data_converter.py](src/dicom2sphn/data_converter.py) were compared on 2026-11-19: they have the same 89 trade names, manufacturers and ingredient codes.
