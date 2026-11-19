# Contrast Agents

A contrast agent (also called contrast medium or contrast dye) is a medical substance used to make structures inside the body clearer and easier to see on medical scans, such as X-ray, CT, MRI and ultrasound.

During an imaging exam, a patient may receive one or more contrast agents. Common scenarios for multiple contrast agents are:

* **Multi-phase or multi-route studies:** a single exam may combine different administration routes, such as an oral (barium-based) contrast agent combined with an intravenous (iodine-based) contrast agent injection.

* **Spectral or dual-energy CT:** advanced CT scanners can sometimes use multiple distinct contrast agents (such as iodine- and barium-based agents) simultaneously or near-simultaneously to differentiate complex tissue compositions.

* **Combined imaging modalities:** a patient might receive an iodinated contrast agent for a CT scan and a gadolinium-based contrast agent for an MRI, sometimes during the same exam, but in different series.


## An example: Angiovist™ (Berlex)

Angiovist™ (Berlex) is an ionic, iodinated contrast agent historically used to enhance visibility in X-ray and CT imaging procedures, such as angiography and urography. It is an older brand that has been phased out and replaced by modern, safer, "non-ionic" options.

Angiovist™ (Berlex) has two active ingredients:
* **Diatrizoate meglumine:** a water-soluble iodinated salt that provides radiopacity (X-ray blocking ability).
* **Diatrizoate sodium:** another iodinated salt, formulated alongside meglumine to balance the solution's viscosity and iodine concentration.

Both components rely on iodine atoms bound to an organic ring, which provides the high density required to block X-rays and illuminate blood vessels and organs. Depending on the specific formulation, such as Angiovist 292 or Angiovist 370, the ratio and strengths of these two active salts vary to achieve different concentrations of organically bound iodine. The numbers 292 and 370 represent the concentration of organically bound iodine in milligrams per milliliter (292 or 370 mg I/mL) of the solution.

Because different imaging procedures require very different amounts of fluid, the manufacturer offered different package volumes:
- **20 mL and 30 mL vials:** generally used for localized injections or smaller structural imaging, such as excretory urography (imaging the urinary tract) or smaller arterial maps.
- **50 mL vials:** a common size for standard single-phase CT scans or targeted diagnostic angiograms.
- **100 mL, 125 mL and 150 mL infusion bottles:** larger sizes for full-body, contrast-enhanced CT scans or extensive vascular imaging (like a complete aortography), where a higher volume must be power-injected into the bloodstream.
- **500 mL pharmacy bulk packages:** used to fill automated, multi-patient power injectors throughout a busy hospital day.


## SPHN Contrast Agent and related concepts

The SPHN schema (release 2026.1) has the following contrast agent related concepts:

| SPHN concept | Subclass of | Describes |
|---|---|---|
| SPHN Contrast Agent Administration Event | SPHN Drug Administration Event | When and how (route, flow profile) the contrast agent was administered |
| SPHN Contrast Agent | SPHN Drug | The administered contrast agent, with its active ingredients and quantity |
| SPHN Contrast Agent Active Ingredient | SPHN Substance | One active ingredient, with its code, quantity and concentration |
| SPHN Drug Article | | The trade name and/or GTIN code of the product |
| SPHN Flow Profile Interval | | One interval of the injection: flow rate, duration, volume and start/end time |

The Angiovist™ (Berlex) contrast agent above can be described by one SPHN Contrast Agent object. Its name and/or GTIN code can be given in a linked SPHN Drug Article object. It links to two SPHN Contrast Agent Active Ingredient objects: one for diatrizoate meglumine and one for diatrizoate sodium.

The SPHN Code of the first SPHN Contrast Agent Active Ingredient, for diatrizoate meglumine, references SNOMED CT:

    47192000 | Meglumine amidotrizoate (substance) |
    en   Meglumine amidotrizoate (substance)
    en   Meglumine diatrizoate
    en   Diatrizoate meglumine
    en   Meglumine amidotrizoate

The SPHN Code of the second SPHN Contrast Agent Active Ingredient, for diatrizoate sodium, references SNOMED CT:

    395875009 | Sodium amidotrizoate (substance) |
    en   Sodium amidotrizoate (substance)
    en   Sodium diatrizoate
    en   Sodium amidotrizoate

Both substances are subclasses of SNOMED CT `385420005 | Contrast media (substance) |`, as [required](https://www.biomedit.ch/rdf/sphn-schema/sphn#ContrastAgentActiveIngredient) by SPHN. SPHN also allows a few other substances that are not contrast media in SNOMED CT: iodine, barium, gadolinium, iron, air, carbon dioxide, xenon, oxygen and water.


## DICOM Contrast/Bolus modules

DICOM defines two modules for contrast bolus information:

 - The [Contrast/Bolus](https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.4.html#table_C.7-12) module, used by legacy (single-frame) DICOM objects, such as CT, MR and CR images. It describes a single contrast bolus at the top level of the dataset, with mostly free text and time-only attributes.

 - The [Enhanced Contrast/Bolus](https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.4b.html#table_C.7-12b) module, used by enhanced (multi-frame) DICOM objects, such as Enhanced CT, Enhanced MR and Enhanced XA images. It describes each contrast agent in its own sequence item, with coded information only.

A dataset has the legacy module when the Contrast/Bolus Agent (0018,0010) attribute is present (it may be empty). A dataset has the enhanced module when every item of the Contrast/Bolus Agent Sequence (0018,0012) has a Contrast/Bolus Agent Number (0018,9337).

### DICOM Contrast/Bolus Agent Sequence attribute and coding schemes

In both modules the applied contrast agent can be stored in a coded way, in a DICOM code sequence attribute.

The Contrast/Bolus Agent Sequence in the Contrast/Bolus module is optional:

    Contrast/Bolus Agent Sequence Attribute
    Tag                     (0018,0012)
    Type                    Optional (3)
    Keyword                 ContrastBolusAgentSequence
    Value Multiplicity      1
    Value Representation    Sequence (SQ)

The Contrast/Bolus Agent Sequence in the Enhanced Contrast/Bolus module is required:

    Contrast/Bolus Agent Sequence Attribute
    Tag                     (0018,0012)
    Type                    Required (1)
    Keyword                 ContrastBolusAgentSequence
    Value Multiplicity      1
    Value Representation    Sequence (SQ)

In both cases the sequence can have one or more items. Each item describes a single DICOM contrast agent (comparable to an SPHN Contrast Agent Active Ingredient) and has, among others, the following nested attributes to reference the contrast agent in an international terminology:

    Coding Scheme Designator (0008,0102)    => The identifier of the coding scheme in which the coded entry is defined.
    Code Value (0008,0100)                  => The identifier of the coded entry.
    Code Meaning (0008,0104)                => Text that conveys the meaning of the coded entry.

For the Angiovist™ (Berlex) contrast agent above, two items would be given.

Item 1 in the Contrast/Bolus Agent Sequence can, for example, be:

    Coding Scheme Designator (0008,0102)    => "SCT"
    Code Value (0008,0100)                  => "12335007"
    Code Meaning (0008,0104)                => "Diatrizoate"

Item 2 in the Contrast/Bolus Agent Sequence can, for example, be:

    Coding Scheme Designator (0008,0102)    => "SCT"
    Code Value (0008,0100)                  => "47192000"
    Code Meaning (0008,0104)                => "Meglumine diatrizoate"

These codes come from a DICOM contrast agent table, described next.

### DICOM Contrast Agent table

DICOM provides a table with common contrast agent names and codes: [Table CID 12. Imaging Contrast Agent](https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_12.html).

The first three columns of table CID 12 hold the values for the `Coding Scheme Designator`, `Code Value` and `Code Meaning` attributes above. Most DICOM contrast agents have `SCT` as coding scheme designator, and are thus references to [SNOMED CT](https://browser.ihtsdotools.org/).

The Angiovist™ (Berlex) contrast agent appears in two rows of this table: one with 'Diatrizoate' and one with 'Meglumine diatrizoate' in the code meaning column.

The code value of 'Diatrizoate', [12335007](http://snomed.info/id/12335007), references in SNOMED CT:

    12335007 | Product containing amidotrizoate (medicinal product) |
    en   Product containing amidotrizoate (medicinal product)
    en   Diatrizoate-containing product
    en   Amidotrizoate-containing product

The code value of 'Meglumine diatrizoate', [47192000](http://snomed.info/id/47192000), references in SNOMED CT:

    47192000 | Meglumine amidotrizoate (substance) |
    en   Meglumine amidotrizoate (substance)
    en   Meglumine diatrizoate
    en   Diatrizoate meglumine
    en   Meglumine amidotrizoate

Note that the DICOM code meaning `Diatrizoate` differs from the SNOMED CT meaning `| Product containing amidotrizoate (medicinal product) |`.

### Retired SNOMED-RT (SRT) codes

Older DICOM data often still uses the retired SNOMED-RT codes, with coding scheme designator `SRT` (or the even older `SNM3`). For example, 'Meglumine diatrizoate' was coded as `SRT` `C-B0345` instead of `SCT` `47192000`. DICOM2SPHN maps these retired codes as well: it treats `SNM3` as `SRT`, and maps the SRT codes of tables CID 12 and CID 13 to the same SNOMED CT substance as their SCT counterparts.

### Different SNOMED CT codes in DICOM compared to SPHN

DICOM prefers subclasses of SNOMED CT `763158003 | Medicinal product (product) |` in the contrast agent table CID 12. SPHN substances, however, are subclasses of SNOMED CT `105590001 | Substance (substance) |`.

As the SPHN Contrast Agent Active Ingredient concept is a subclass of the SPHN Substance concept, the DICOM code `12335007 | Product containing amidotrizoate (medicinal product) |` cannot be used: it is a *medicinal product*, not a *substance*. Therefore many SNOMED CT codes in table CID 12 have to be mapped to *substances*, and more specifically to *contrast media*: subclasses of SNOMED CT `385420005 | Contrast media (substance) |`, or one of the other substances [allowed](https://www.biomedit.ch/rdf/sphn-schema/sphn#ContrastAgentActiveIngredient) by SPHN.

Table 1 shows some examples. The complete mapping, including the codes that need no change, is the `dicom_contrast_agents_coded_2_sphn_snomed_coded` dictionary in [data_converter.py](src/dicom2sphn/data_converter.py).

**Table 1:** Examples of DICOM CID 12 product codes mapped to SPHN Contrast Agent Active Ingredient compatible substance codes

| DICOM code (CID 12) | DICOM code meaning | SPHN compatible SNOMED CT code |
|---|---|---|
| SCT 12335007 | Diatrizoate | `396020008 \| Amidotrizoate (substance) \|` |
| SCT 353962003 | Iodixanol | `395750001 \| Iodixanol (substance) \|` |
| SCT 109218004 | Iohexol | `395751002 \| Iohexol (substance) \|` |
| SCT 109219007 | Iopamidol | `395754005 \| Iopamidol (substance) \|` |
| SCT 353903006 | Iopromide | `395756007 \| Iopromide (substance) \|` |
| SCT 109222009 | Ioversol | `395759000 \| Ioversol (substance) \|` |
| SCT 25419009 | Barium Sulfate | `396014007 \| Barium sulfate (substance) \|` |
| SCT 407976008 | Gadobutrol | `418351005 \| Gadobutrol (substance) \|` |
| SCT 354088005 | Gadodiamide | `396067007 \| Gadodiamide (substance) \|` |
| SCT 353946009 | Gadoteridol | `420600009 \| Gadoteridol (substance) \|` |
| SCT 768763008 | Gadolinium | `58281002 \| Gadolinium (substance) \|` |

### DICOM Contrast/Bolus Agent attribute

The legacy DICOM Contrast/Bolus module also has the often used Contrast/Bolus Agent attribute, which contains free text describing the administered contrast agent:

    Contrast/Bolus Agent Attribute
    Tag                     (0018,0010)
    Type                    Required, Empty if Unknown (2)
    Keyword                 ContrastBolusAgent
    Value Multiplicity      1
    Value Representation    Long String (LO)
    Example Values          No, CC MAGNEVIST, ORAL & OMNIPAQUE

As the example values show, anything can be written in this attribute, but trade names are common. The last column of table CID 12 lists several common contrast agent trade names. Some trade names belong to multiple DICOM contrast agents: Angiovist™ (Berlex), for example, is listed with both "diatrizoate" and "diatrizoate meglumine".

The [Contrast Agent Trade Names and Ingredients](Contrast-Agent-Trade-Names-and-Ingredients.md) list can be used to map trade names to SPHN Contrast Agent Active Ingredient SNOMED CT codes. DICOM2SPHN uses this list to recognize trade names, active ingredient names and active element names in the free text (see [extract_contrast_agents.py](src/dicom2sphn/extract_contrast_agents.py)).

### DICOM Contrast/Bolus Ingredient

The DICOM contrast agent (or the SPHN Contrast Agent Active Ingredient) is a molecule with an active element or functional atom. DICOM calls this the Contrast/Bolus Ingredient. The legacy module has it as a defined term in Contrast/Bolus Ingredient (0018,1048), and the enhanced module as a code in the Contrast/Bolus Ingredient Code Sequence (0018,9338). The codes are listed in [Table CID 13. Imaging Contrast Agent Ingredient](https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_13.html).

DICOM2SPHN maps the Contrast/Bolus Ingredient terms (active elements or functional atoms) to these SPHN Contrast Agent Active Ingredient compatible SNOMED CT codes:

| DICOM term | SNOMED CT code |
|---|---|
| IODINE | `44588005 \| Iodine (substance) \|` |
| GADOLINIUM | `58281002 \| Gadolinium (substance) \|` |
| CARBON DIOXIDE | `31811003 \| Carbon dioxide (substance) \|` |
| BARIUM | `39290007 \| Barium (substance) \|` |
| XENON | `83598005 \| Xenon (substance) \|` |
| AIR | `15158005 \| Air (substance) \|` |
| OXYGEN | `24099007 \| Oxygen (substance) \|` |
| WATER | `11713004 \| Water (substance) \|` |
| IRON | `3829006 \| Iron (substance) \|` |
| MANGANESE | `87869004 \| Manganese (substance) \|`, **not mapped**: SPHN does not allow it yet |

In SPHN these active elements or functional atoms can be added as SPHN Contrast Agent Active Ingredient objects to an SPHN Contrast Agent object.


## How DICOM2SPHN maps the DICOM Contrast/Bolus information to SPHN

The mapping is implemented in [dicom_contrast_bolus_module_reader.py](src/dicom2sphn/dicom_contrast_bolus_module_reader.py).

### Overview

| SPHN property | DICOM source |
|---|---|
| Contrast Agent Administration Event: *has start datetime* | Contrast/Bolus Start Time (0018,1042), completed with a date (see below). Enhanced: the earliest start time in the Contrast Administration Profile Sequence (0018,9340) |
| Contrast Agent Administration Event: *has end datetime* | Contrast/Bolus Stop Time (0018,1043), completed in the same way. Enhanced: the latest stop time in the profile sequence |
| Contrast Agent Administration Event: *has administration route code* | Contrast/Bolus Administration Route Sequence (0018,0014), or the free text Contrast/Bolus Route (0018,1040), e.g. "IV" (legacy only) |
| Contrast Agent Administration Event: *has flow profile interval* | Legacy: Contrast Flow Rate (0018,1046) and Contrast Flow Duration (0018,1047). Enhanced: one interval per item of the Contrast Administration Profile Sequence (0018,9340) |
| Contrast Agent: *has active ingredient* | Contrast/Bolus Agent Sequence (0018,0012), or the free text Contrast/Bolus Agent (0018,0010); Contrast/Bolus Ingredient (0018,1048) or Contrast/Bolus Ingredient Code Sequence (0018,9338) |
| Contrast Agent: *has quantity* | Contrast/Bolus Volume (0018,1041), in mL (diluted) |
| Active Ingredient: *has quantity* | Contrast/Bolus Total Dose (0018,1044), in mL (undiluted), legacy only |
| Active Ingredient: *has concentration* | Contrast/Bolus Ingredient Concentration (0018,1049), in mg/mL |
| Active Ingredient: *has volume percentage* | Contrast/Bolus Ingredient Percent by Volume (0052,0001), in %, enhanced only |

Contrast/Bolus Agent Number (0018,9337), Contrast/Bolus Ingredient Opaque (0018,9425) and Contrast/Bolus T1 Relaxivity (0018,0013) are read and logged, but not mapped to SPHN.

### Legacy (single-frame) Contrast/Bolus module

The legacy module describes a single contrast bolus, which may contain one or more contrast agents:

1. **Contrast agents:** first the coded Contrast/Bolus Agent Sequence is used. Only if it gives no contrast agent, the free text Contrast/Bolus Agent attribute is searched for trade names, active ingredient names and active element names.
2. **Ingredient:** the Contrast/Bolus Ingredient (e.g. "IODINE") and its concentration are added to the contrast agent if there is exactly one. Without a contrast agent, a new contrast agent is created with this ingredient. With multiple contrast agents, the ingredient is not used, as it is unknown to which contrast agent it belongs.
3. **Administration events:**
   - **One contrast agent:** one administration event with all information: route, start and end datetime, volume, total dose and flow profile.
   - **Multiple contrast agents:** one administration event per contrast agent, with only the start and end datetime, as it is unknown to which contrast agent the route, volume, dose and flow belong.
   - **No contrast agent, but a route and a real start datetime:** one administration event for a general `385420005 | Contrast media (substance) |`, as SPHN requires a contrast agent.

### Enhanced (multi-frame) Contrast/Bolus module

Each item of the Contrast/Bolus Agent Sequence gives one administration event, with its own contrast agent (the code of the item plus the codes in its ingredient code sequence), volume, coded route and flow profile.

### Unknown codes

DICOM codes that are not in the mapping are not converted to SPHN codes. They are logged and counted, so that the mapping tables can be extended.


## Common problems

### DICOM contrast agent start date and time

DICOM provides only an *optional* contrast agent start and stop *time*, while SPHN requires a start *datetime*.

In the Contrast/Bolus module, these attributes are:

    Contrast/Bolus Start Time Attribute
    Tag                     (0018,1042)
    Type                    Optional (3)
    Keyword                 ContrastBolusStartTime
    Value Multiplicity      1
    Value Representation    Time (TM)

and

    Contrast/Bolus Stop Time Attribute
    Tag                     (0018,1043)
    Type                    Optional (3)
    Keyword                 ContrastBolusStopTime
    Value Multiplicity      1
    Value Representation    Time (TM)

In the Enhanced Contrast/Bolus module, these attributes are in each item of the Contrast Administration Profile Sequence:

    Contrast Administration Profile Sequence Attribute
    Tag                     (0018,9340)
    Type                    Optional (3)
    Keyword                 ContrastAdministrationProfileSequence
    Value Multiplicity      1
    Value Representation    Sequence (SQ)

**Completing the date.** When a start or stop time is given, DICOM2SPHN combines it with the date of a reference datetime, in this order:
1. the Acquisition DateTime (0008,002A), or Acquisition Date (0008,0022) and Acquisition Time (0008,0032);
2. the Series Date (0008,0021) and Series Time (0008,0031);
3. the Study Date (0008,0020) and Study Time (0008,0030).

Care has to be taken when the contrast agent was administered before midnight and the acquisition started after midnight, or the other way around. When the combined datetime is more than 23 hours after the reference datetime, it is moved one day back; when it is more than 23 hours before, it is moved one day forward.

**Estimating a missing start time.** When no start time is given, DICOM2SPHN uses the first available of:
1. the Series datetime;
2. the Acquisition datetime;
3. the Study datetime;
4. the fallback contrast agent date and time from the configuration file (`fallback_contrast_agent_date` and `fallback_contrast_agent_time`).

A stop datetime before the start datetime is not used.

Note that all these DICOM attributes can be empty (if unknown), so the estimated start datetime can differ from the real administration time.

### Multiple contrast agents in the legacy module

The legacy module has only one route, volume, total dose and flow profile for the whole bolus. When it lists multiple contrast agents, this information cannot be assigned to one specific contrast agent. DICOM2SPHN then creates one administration event per contrast agent, with only the start and end datetime.

### Only one administration route

An SPHN Contrast Agent Administration Event can have only one administration route. When DICOM gives multiple routes (for example the free text "ORAL & IV"), no route is added to the event.
