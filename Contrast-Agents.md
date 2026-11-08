# Contrast Agents

A contrast agent (also called contrast medium or contrast dye) is a medical substance usually used to make structures inside the body clearer and easier to see on medical scans, such as X-rays, CT scans, MRIs, and ultrasounds.

During an imaging exam, a patient may receive one or more contrast agents.

Common Scenarios for Multiple Contrast Agents:

* Multi-Phase or Multi-Route Studies: A single exam may combine different administration routes, such as oral (barium-based) contrast agent combined with an intravenous (iodine-based) contrast agent injection.

* Spectral or Dual-Energy CT: Advanced CT scanners can sometimes utilize multiple distinct contrast agents (such as iodine- and barium-based agents) simultaneously or near-simultaneously to differentiate complex tissue compositions.

* Combined Imaging Modalities: A patient might receive an iodinated contrast agent for a CT scan and a gadolinium-based contrast agent for an MRI, sometimes during the same exam, but in different series.


## An example: Angiovist™(Berlex)

Angiovist™(Berlex) is an ionic, iodinated contrast agent historically used to enhance visibility in X-ray and CT imaging procedures, such as angiography and urography. It is an older brand that has been phased out and replaced by modern, safer, "non-ionic" options. 

Angiovist™(Berlex) has two active ingredients:
* Diatrizoate Meglumine: A water-soluble iodinated salt that provides radiopacity (X-ray blocking ability).
* Diatrizoate Sodium: Another iodinated salt formulated alongside meglumine to balance the solution's viscosity and iodine concentration.

Both components rely on iodine atoms bound to an organic ring, which provides the high density required to block X-rays and illuminate blood vessels and organs. Depending on the specific formulation, such as Angiovist 292 or Angiovist 370, the ratio and strengths of these two active salts vary to achieve different concentrations of organically bound iodine. The numbers 292 and 370 represent the concentration of organically bound iodine in milligrams per milliliter (292 or 370 mg I/mL) of the solution. 

Because different imaging procedures require vastly different amounts of fluid, the manufacturer tailored package volumes to meet specific medical scenarios:
- 20 mL and 30 mL Vials: Generally used for localized injections or smaller structural imaging, such as excretory urography (imaging the urinary tract) or smaller arterial maps.
- 50 mL Vials: A highly common size utilized for standard single-phase CT scans or targeted diagnostic angiograms.
- 100 mL, 125 mL, and 150 mL Infusion Bottles:  Larger sizes reserved for full-body, contrast-enhanced CT scans or extensive vascular imaging (like a complete aortography) where a higher volume must be power-injected into the bloodstream.
- 500 mL Pharmacy Bulk Packages: Used to safely fill automated, multi-patient power injectors throughout a busy hospital day.


## SPHN Contrast Agent and related concepts

In the SPHN dataset there are the following contrast agent related concepts:
    
    SPHN Contrast Agent Administration Event  => a subclass of SPHN Drug Administration Event
    SPHN Contrast Agent                       => a subclass of SPHN Drug
    SPHN Contrast Agent Active Ingredient     => a subclass SPHN substance

The above mentioned Angiovist™(Berlex) contrast agent can be described by an SPHN Contrast Agent concept object. The name and/or GTIN code could be provided in an linked SPHN Drug Article concept object. It would have links to two SPHN Contrast Agent Active Ingredient concept objects: One for Diatrizoate Meglumine and one for Diatrizoate Sodium. 

The SPHN Code in one SPHN Contrast Agent Active Ingredient would, for Diatrizoate Meglumine, be referencing SNOMED-CT:

    Meglumine amidotrizoate (substance)
    SCTID: 47192000

    47192000 | Meglumine amidotrizoate (substance) |
    en   Meglumine amidotrizoate (substance)
    en   Meglumine diatrizoate
    en   Diatrizoate meglumine
    en   Meglumine amidotrizoate

The SPHN Code in the other SPHN Contrast Agent Active Ingredient would, for Diatrizoate Sodium, be referencing SNOMED-CT:

    Sodium amidotrizoate (substance)
    SCTID: 395875009

    395875009 | Sodium amidotrizoate (substance) |
    en   Sodium amidotrizoate (substance)
    en   Sodium diatrizoate
    en   Sodium amidotrizoate

Note that both substances are subclasses of SNOMED-CT `385420005 | Contrast media (substance) |` as [required](https://www.biomedit.ch/rdf/sphn-schema/sphn#ContrastAgentActiveIngredient) by SPHN (except for a few other substances). 


## DICOM Contrast/Bolus Modules

DICOM defines two modules for contrast bolus information: 

 - The [Contrast/Bolus](https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.4.html#table_C.7-12) module which is used by legacy (single-frame) DICOM objects, such as CT, MR, and CR images.

 - The [Enhanced Contrast/Bolus](https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.4b.html#table_C.7-12b) module which is used by enhanced (multi-frame) DICOM objects, such as Enhanced CT, Enhanced MR, and Enhanced XA images.

### DICOM Contrast/Bolus Agent Sequence Attribute and Coding Schemes
In both modules the information about the applied contrast agent can be stored in a coded way, in a DICOM Code Sequence attribute.

The Contrast/Bolus Agent Sequence in the Contrast/Bolus module is optional:

    Contrast/Bolus Agent Sequence Attribute
    Tag	                    (0018,0012)
    Type	                Optional (3)
    Keyword	                ContrastBolusAgentSequence
    Value Multiplicity	    1
    Value Representation	Sequence (SQ)

The Contrast/Bolus Agent Sequence in the Enhanced Contrast/Bolus module is required:

    Contrast/Bolus Agent Sequence Attribute
    Tag	                    (0018,0012)
    Type	                Required (1)
    Keyword	                ContrastBolusAgentSequence
    Value Multiplicity	    1
    Value Representation	Sequence (SQ)

In both cases the Sequence attribute can have one or more items. Each item is then describing a single DICOM Contrast Agent (comparable to a SPHN Contrast Agent Active Ingredient) and can have the following nested attributes (among several others) to reference a contrast agent in an international terminology:

    Coding Scheme Designator (0008,0102)    => The identifier of the Coding Scheme in which the Coded Entry is defined.
    Code Value (0008,0100)                  => The identifier of the Coded Entry.
    Code Meaning (0008,0104)                => Text that conveys the meaning of the Coded Entry.

For the above mentioned Angiovist™(Berlex) contrast agent two items would be specified:

Item 1 in the Contrast/Bolus Agent Sequence can e.g. be: 

    Coding Scheme Designator (0008,0102)    => "SNOMED-CT"
    Code Value (0008,0100)                  => "12335007"
    Code Meaning (0008,0104)                => "Diatrizoate"

Item 2 in the Contrast/Bolus Agent Sequence can e.g. be: 

    Coding Scheme Designator (0008,0102)    => "SNOMED-CT"
    Code Value (0008,0100)                  => "47192000"
    Code Meaning (0008,0104)                => "Meglumine diatrizoate"

The above codes are specified in a DICOM Contrast Agent table, see next.

### DICOM Contrast Agent Table

DICOM provides a table with common contrast agent names and codes: [Table CID 12. Imaging Contrast Agent](https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_12.html)

The first three columns of table CID 12 have values for the above mentioned `Coding Scheme Designator`, `Code Value`, and `Code Meaning` attributes. These are used to reference a DICOM contrast agent in an international standard. Most DICOM contrast agents have 'SCT' as `Coding Scheme Designator` and are thus references to [SNOMED-CT](https://snomedbrowser.org/). 

The above mentioned Angiovist™(Berlex) contrast agent is in DICOM specified in two rows in this table: One having 'Diatrizoate' and one having 'Meglumine diatrizoate' in the `code meaning` column.

After clicking on [12335007](http://snomed.info/id/12335007), the `code value` of 'Diatrizoate', a browser window opens and it shows the reference in SNOMED-CT:

    Product containing amidotrizoate (medicinal product)
    SCTID: 12335007

    12335007 | Product containing amidotrizoate (medicinal product) |
    en   Product containing amidotrizoate (medicinal product)
    en   Diatrizoate-containing product
    en   Amidotrizoate-containing product

The same goes for [47192000](http://snomed.info/id/47192000), the `code value` of 'Meglumine diatrizoate', a browser window opens and it shows the reference in SNOMED-CT: 

    Meglumine amidotrizoate (substance)
    SCTID: 47192000

    47192000 | Meglumine amidotrizoate (substance) |
    en   Meglumine amidotrizoate (substance)
    en   Meglumine diatrizoate
    en   Diatrizoate meglumine
    en   Meglumine amidotrizoate

Note that the DICOM provided code meaning: `Diatrizoate`, is different from the SNOMED-CT code meaning: `| Product containing amidotrizoate (medicinal product) |`.

### Different SNOMED-CT codes in DICOM compared to SPHN

DICOM prefers to have subclasses of SNOMED-CT `763158003 | Medicinal product (product) |` in the Contrast Agent Table CID 12. SPHN substances are, however, subclasses of SNOMED-CT `105590001 | Substance (substance) |`. 

As the SPHN Contrast Agent Active Ingredient concept is a subclass of the SPHN Substance concept, we cannot use the DICOM provided SNOMED-CT: "12335007 | Product containing amidotrizoate (medicinal product) |" as this is a `medicinal product` and not a `substance`. Therefore, many of the DICOM provided SNOMED-CT codes in Table CID 12 have to be mapped to `substances` and even more specifically to `contrast media`, subclasses of SNOMED-CT `385420005 | Contrast media (substance) |` or one of the other substances [required](https://www.biomedit.ch/rdf/sphn-schema/sphn#ContrastAgentActiveIngredient) by SPHN.

<Table 1>
Tabe 1: Mapping DICOM contrast agent codes to SPHN Contrast Agent Active Ingredient compatible codes

### DICOM Contrast/Bolus Agent Attribute

The DICOM Contrast/Bolus Module has in addition the often used Contrast/Bolus Agent Attribute, which can contain free text describing the contrast agent provided:

    Contrast/Bolus Agent Attribute
    Tag	                    (0018,0010)
    Type	                Required, Empty if Unknown (2)
    Keyword	                ContrastBolusAgent
    Value Multiplicity	    1
    Value Representation	Long String (LO)
    Example Values	        No, CC MAGNEVIST, ORAL & OMNIPAQUE

As the example values show, anything could be written in this attribute but often trade names are used. In the last column of table CID 12 we see several common contrast agent trade names. Note that some of the listed trade names have multiple DICOM contrast agents. Angiovist™(Berlex) is for example listed behind "diatrizoate" and "diatrizoate meglumine".

Here is a link to [Contrast Agent Trade Names and Ingredients](Contrast-Agent-Trade-Names-and-Ingredients.md) that can be used to map trade names to SPHN Contrast Agent Active Ingredient SNOMED-CT codes.


### DICOM Contrast/Bolus Ingredient

The DICOM contrast agent (or the SPHN Contrast Agent Active Ingredient) is a molecule that has an active element or functional atom. In DICOM this is called the Contrast Bolus Ingredient and these are listed in:
[Table CID 13. Imaging Contrast Agent Ingredient](https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_13.html)

Mapping of DICOM Contrast/Bolus Ingredient terms (active elements or functional atoms) to SPHN Contrast Agent Active Ingredient compatible SNOMED-CT codes:


    "IODINE":           "SNOMED-CT", "44588005", "| Iodine (substance) |"
    "GADOLINIUM":       "SNOMED-CT", "58281002", "| Gadolinium (substance) |"
    "CARBON DIOXIDE":   "SNOMED-CT", "31811003", "| Carbon dioxide (substance) |"
    "BARIUM":           "SNOMED-CT", "39290007", "| Barium (substance) |"
    "XENON":            "SNOMED-CT", "83598005", "| Xenon (substance) |"
    "AIR":              "SNOMED-CT", "15158005", "| Air (substance) |"
    "OXYGEN":           "SNOMED-CT", "24099007", "| Oxygen (substance) |"
    "WATER":            "SNOMED-CT", "11713004", "| Water (substance) |"
    "IRON":             "SNOMED-CT",  "3829006", "| Iron (substance) |"
    "Manganese":        "SNOMED-CT", "87869004", "| Manganese (substance) |"     => (Not yet available) <=

In SPHN these active elements or functional atoms can be added as SPHN Contrast Agent Active Ingredient concept objects to a SPHN Contrast Agent concept object.

## Common problems:

### DICOM Contrast Agent Start Date and Time
DICOM provides only an *optional* contrast agent start and a stop `time` while SPHN requires a start `DateTime`. 

In the Contrast/Bolus module, these attributes are:

    Contrast/Bolus Start Time Attribute
    Tag	                    (0018,1042)
    Type	                Optional (3)
    Keyword	                ContrastBolusStartTime
    Value Multiplicity	    1
    Value Representation	Time (TM)

and 

    Contrast/Bolus Stop Time Attribute
    Tag	                    (0018,1043)
    Type	                Optional (3)
    Keyword	                ContrastBolusStopTime
    Value Multiplicity	    1
    Value Representation	Time (TM)

In the Enhanced Contrast/Bolus module, the above attributes are located in each item of the Contrast Administration Profile Sequence attribute:

    Contrast Administration Profile Sequence Attribute
    Tag	                    (0018,9340)
    Type	                Optional (3)
    Keyword	                ContrastAdministrationProfileSequence
    Value Multiplicity	    1
    Value Representation	Sequence (SQ)

In case the `time` part is missing, the earliest
    
    Series Time (0008,0031)

of a DICOM Series mentioning the contrast agent, could be used as an estimate. Or in case it was not provided, the earliest:

    Acquision Time (0008,0032), 
    Acquisition DateTime (0008,002A),

in that DICOM Series. Or in case it also was not provided, the 

    Study Time (0008,0030)

could be used as an estimate.

Not only the `time` is optional in DICOM, also the `date` part is not provided. In case the `time` is provided or estimated, the `date` can possibly be obtained from the: 
1. DICOM Acquisition Date attribute (0008,0022),
3. DICOM Acquisition DateTime attribute (0008,002A),
4. DICOM Series Date attribute (0008,0021),
5. DICOM Study date attribute (0008,0020)

But all these attributes can also be empty (if unknown). Moreover, care has to be taken when the contrast agent was administered before midnight and the acquisionion started after midnight, or vice versa.

