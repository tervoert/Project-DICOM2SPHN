"""
data_converter.py:
    Part of the example dicom2sphn package.
    It contains the DataConverter class, which handles data conversion.
"""

import re
from collections.abc import Mapping
from typing import ClassVar, ReadOnly


#
# Edwin 2026-09-25
#
class DataConverter:
    """
    A class to handle data conversion.
    """

    #
    # Edwin 2026-09-25
    #
    def __init__(self):
        """
        Initializes the DataConverter instance.
        """

    # 
    # General note:
    #
    # - The DICOM standard defines various terms, enumerates, etc. 
    # - DICOM also uses its own coding scheme: DICOM Controlled Terminology Definitions (DICOM DCM)
    #   - Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/chapter_D.html#DCM_111001
    # - DICOM also uses other coding schemes: 
    #   - SNOMED-CT:
    #     - DICOM uses "SCT" as the coding scheme designator for SNOMED-CT
    #     - Link: https://www.snomed.org/
    #     - SNOMED-CT browser: https://browser.ihtsdotools.org/


    # 
    # DICOM Modalities and SPHN Procedures
    #

    # Related attribute tag:  Modality (0008,0060)
    # Links:
    # - DICOM defined terms: https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.3.html#sect_C.7.3.1.1.1
    #
    # The DICOM DCM modality related codes can be divided into multiple categories: Acquisition modalities, Non-acquisition modalities,...
    # Acquisition modalities:     https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_29.html 
    # Non-acquisition modalities: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_32.html 


    # A dictionary mapping DICOM defined modality terms to a corresponding DICOM DCM code and a possible "SNOMED-CT: descendant of: 363679005 |Imaging (procedure)|" code for SPHN Procedure
    # Key: DICOM defined modality term (e.g., "CT", "MR", "US")
    # Value: a tuple containing:
    #        - a tuple with the DICOM DCM code and a human-readable description (tuple elements can be empty)
    #        - a tuple with the SNOMED-CT coding scheme designator, code value, and human-readable description for SPHN Procedure (the tuple can be empty)
    dicom_modality_code_dict: ClassVar[ReadOnly[dict[str, tuple[tuple[str, str], tuple[str, str, str]]]]] = {
        ### Acquisition modalities
        "AR":           (("DCM", "AR",         "| Autorefraction |"),                                  ("", "", "")),
        "BDUS":         (("DCM", "BDUS",       "| Ultrasound Bone Densitometry |"),                    ("", "", "")),
        "BI":           (("DCM", "BI",         "| Biomagnetic Imaging |"),                             ("", "", "")),
        "BMD":          (("DCM", "BMD",        "| Bone Mineral Densitometry |"),                       ("", "", "")),
        "CFM":          (("DCM", "CFM",        "| Confocal Microscopy |"),                             ("", "", "")),
        "CR":           (("DCM", "CR",         "| Computed Radiography |"),                            ("SNOMED", "168537006", "| Plain X-ray (procedure) |")),
        "CT":           (("DCM", "CT",         "| Computed Tomography |"),                             ("SNOMED", "77477000",  "| Computed tomography (procedure) |")),
        "DG":           (("DCM", "DG",         "| Diaphanography |"),                                  ("", "", "")),
        "DMS":          (("DCM", "DMS",        "| Dermoscopy |"),                                      ("", "", "")),
        "DX":           (("DCM", "DX",         "| Digital Radiography |"),                             ("SNOMED", "168537006", "| Plain X-ray (procedure) |")),
        "ECG":          (("DCM", "ECG",        "| Electrocardiography |"),                             ("", "", "")),
        "EEG":          (("DCM", "EEG",        "| Electroencephalography |"),                          ("", "", "")),
        "EMG":          (("DCM", "EMG",        "| Electromyography |"),                                ("", "", "")),
        "EOG":          (("DCM", "EOG",        "| Electrooculography |"),                              ("", "", "")),
        "EPS":          (("DCM", "EPS",        "| Cardiac Electrophysiology |"),                       ("", "", "")),
        "ES":           (("DCM", "ES",         "| Endoscopy |"),                                       ("", "", "")),
        "GM":           (("DCM", "GM",         "| General Microscopy |"),                              ("SNOMED", "363679005", "| Imaging (procedure) |")), # Has no "Imaging (procedure)" parent: SNOMED 117259009 | Microscopy (procedure) |
        "HD":           (("DCM", "HD",         "| Hemodynamic Waveform |"),                            ("", "", "")),
        "IO":           (("DCM", "IO",         "| Intra-oral Radiography |"),                          ("", "", "")),
        "IVOCT":        (("DCM", "IVOCT",      "| Intravascular Optical Coherence Tomography |"),      ("SNOMED", "392010000", "| Optical coherence tomography (procedure) |")),
        "IVUS":         (("DCM", "IVUS",       "| Intravascular Ultrasound |"),                        ("SNOMED", "241466007", "| Intravascular ultrasound angiography of blood vessel (procedure) |")),
        "KER":          (("DCM", "KER",        "| Keratometry |"),                                     ("", "", "")),
        "LEN":          (("DCM", "LEN",        "| Lensometry |"),                                      ("", "", "")),
        "LS":           (("DCM", "LS",         "| Laser Scan |"),                                      ("", "", "")),
        "MG":           (("DCM", "MG",         "| Mammography |"),                                     ("SNOMED", "71651007",  "| Mammography (procedure) |")),
        "MR":           (("DCM", "MR",         "| Magnetic Resonance |"),                              ("SNOMED", "113091000", "| Magnetic resonance imaging (procedure) |")),
        "NM":           (("DCM", "NM",         "| Nuclear Medicine |"),                                ("SNOMED", "373205008", "| Nuclear medicine imaging procedure (procedure) |")),
        "OAM":          (("DCM", "OAM",        "| Ophthalmic Axial Measurements |"),                   ("", "", "")),
        "OCT":          (("DCM", "OCT",        "| Optical Coherence Tomography |"),                    ("SNOMED", "392010000", "| Optical coherence tomography (procedure) |")),
        "OP":           (("DCM", "OP",         "| Ophthalmic Photography |"),                          ("", "", "")),
        "OPM":          (("DCM", "OPM",        "| Ophthalmic Mapping |"),                              ("", "", "")),
        "OPT":          (("DCM", "OPT",        "| Ophthalmic Tomography |"),                           ("", "", "")),
        "OPTBSV":       (("DCM", "OPTBSV",     "| Ophthalmic Tomography B-scan Volume Analysis |"),    ("", "", "")),
        "OPTENF":       (("DCM", "OPTENF",     "| Ophthalmic Tomography En Face |"),                   ("", "", "")),
        "OPV":          (("DCM", "OPV",        "| Ophthalmic Visual Field |"),                         ("", "", "")),
        "OSS":          (("DCM", "OSS",        "| Optical Surface Scanner |"),                         ("", "", "")),
        "PA":           (("DCM", "PA",         "| Photoacoustic |"),                                   ("", "", "")),
        "POS":          (("DCM", "POS",        "| Position Sensor |"),                                 ("", "", "")),
        "PT":           (("DCM", "PT",         "| Positron emission tomography |"),                    ("SNOMED", "82918005",  "| Positron emission tomography (procedure) |")),
        "PX":           (("DCM", "PX",         "| Panoramic X-Ray |"),                                 ("SNOMED", "89846007",  "| Orthopantogram (procedure) |")),
        "RESP":         (("DCM", "RESP",       "| Respiratory Waveform |"),                            ("", "", "")),
        "RF":           (("DCM", "RF",         "| Radiofluoroscopy |"),                                ("SNOMED", "44491008",  "| Fluoroscopy (procedure) |")),
        "RG":           (("DCM", "RG",         "| Radiographic imaging |"),                            ("SNOMED", "363680008", "| Radiographic imaging procedure (procedure) |")),
        "RTIMAGE":      (("DCM", "RTIMAGE",    "| RT Image |"),                                        ("", "", "")),
        "SM":           (("DCM", "SM",         "| Slide Microscopy |"),                                ("SNOMED", "363679005", "| Imaging (procedure) |")), # Has no "Imaging (procedure)" parent: SNOMED 117259009 | Microscopy (procedure) |
        "SRF":          (("DCM", "SRF",        "| Subjective Refraction |"),                           ("", "", "")),
        "TG":           (("DCM", "TG",         "| Thermography |"),                                    ("", "", "")),
        "US":           (("DCM", "US",         "| Ultrasound |"),                                      ("SNOMED", "16310003",  "| Ultrasonography (procedure) |")),
        "VA":           (("DCM", "VA",         "| Visual Acuity |"),                                   ("", "", "")),
        "XA":           (("DCM", "XA",         "| X-Ray Angiography |"),                               ("SNOMED", "77343006",  "| Angiography (procedure) |")),
        "XC":           (("DCM", "XC",         "| External-camera Photography |"),                     ("", "", "")),
        ### Non-acquisition modalities
        "ASMT":         (("DCM", "ASMT",       "| Content Assessment Results |"),                      ("", "", "")),
        "AU":           (("DCM", "AU",         "| Audio |"),                                           ("", "", "")),
        "CTPROTOCOL":   (("DCM", "CTPROTOCOL", "| CT Protocol |"),                                     ("", "", "")),
        "DOC":          (("DCM", "DOC",        "| Document |"),                                        ("", "", "")),
        "FID":          (("DCM", "FID",        "| Fiducials |"),                                       ("", "", "")),
        "HC":           (("DCM", "HC",         "| Hard Copy |"),                                       ("", "", "")),
        "IOL":          (("DCM", "IOL",        "| Intraocular Lens Data |"),                           ("", "", "")),
        "KO":           (("DCM", "KO",         "| Key Object Selection |"),                            ("", "", "")),
        "M3D":          (("DCM", "M3D",        "| Model for 3D Manufacturing |"),                      ("", "", "")),
        "OT":           (("DCM", "OT",         "| Other |"),                                           ("", "", "")),
        "PLAN":         (("DCM", "PLAN",       "| Plan |"),                                            ("", "", "")),
        "PR":           (("DCM", "PR",         "| Presentation State |"),                              ("", "", "")),
        "REG":          (("DCM", "REG",        "| Registration |"),                                    ("", "", "")),
        "RTDOSE":       (("DCM", "RTDOSE",     "| Radiotherapy Dose |"),                               ("", "", "")),
        "RTPLAN":       (("DCM", "RTPLAN",     "| Radiotherapy Plan |"),                               ("", "", "")),
        "RTRECORD":     (("DCM", "RTRECORD",   "| RT Treatment Record |"),                             ("", "", "")),
        "RTSTRUCT":     (("DCM", "RTSTRUCT",   "| Radiotherapy Structure Set |"),                      ("", "", "")),
        "RWV":          (("DCM", "RWV",        "| Real World Value Map |"),                            ("", "", "")),
        "SEG":          (("DCM", "SEG",        "| Segmentation |"),                                    ("", "",  "")), # Has no "Imaging (procedure)" parent: SNOMED 74529008 | Image analysis, segmentation (procedure) |
        "SMR":          (("DCM", "SMR",        "| Stereometric Relationship |"),                       ("", "", "")),
        "SR":           (("DCM", "SR",         "| SR Document |"),                                     ("", "", "")),
        "STAIN":        (("DCM", "STAIN",      "| Automated Slide Stainer |"),                         ("", "", "")),
        "TEXTUREMAP":   (("DCM", "TEXTUREMAP", "| Texture Map |"),                                     ("", "", "")),
        ### Not in acquision modalities, not in non-aquisition modalities, but valid DICOM term and valid DCM code
        "ANN":          (("DCM", "ANN",        "| Annotation |"),                                      ("", "", "")), # Has no "Imaging (procedure)" parent
        ### Not in acquision modalities, not non-aquisition modalities, but valid DICOM term and not a valid DCM code
        "RTINTENT":     (("",    "",           "| Radiotherapy Intent |"),                             ("", "", "")),
        "RTRAD":        (("",    "",           "| RT Radiation |"),                                    ("", "", "")),
        "RTSEGANN":     (("",    "",           "| Radiotherapy Segment Annotation |"),                 ("", "", "")),
        "XAPROTOCOL":   (("",    "",           "| XA Protocol (Performed) |"),                         ("", "", ""))
    }

    
    #
    # Lossy Image Compression
    #

    # A dictionary mapping a DICOM LossyImageCompression tag value to a boolean
    dicom_lossy_image_compression_code_dict: ClassVar[ReadOnly[dict[str, bool]]] = {
        "00":  False,
        "01":  True
    }

    # A dictionary mapping a DICOM DataCompressionAlgorithm tag value to corresponding SPHN ValueSet members: 
    # Key: DICOM DataCompressionAlgorithm tag value
    # Value: a tuple containing:
    # - SPHN DataCompressionAlgorithm_method ValueSet member (e.g. "ISO109181")
    # - SPHN DataCompressionAlgorithm_type ValueSet member (e.g. "LossyCompression")
    # - a description of the compression method (e.g. "JPEG Lossy Compression")
    dicom_data_compression_method_dict: ClassVar[ReadOnly[dict[str, tuple[str,str,str]]]] = {
        "ISO_10918_1":  ("ISO109181",  "LossyCompression", "JPEG Lossy Compression"),
        "ISO_14495_1":  ("ISO144951",  "LossyCompression", "JPEG-LS Near-lossless Compression"),
        "ISO_15444_1":  ("ISO154441",  "LossyCompression", "JPEG 2000 Irreversible Compression"),
        "ISO_15444_15": ("ISO1544415", "LossyCompression", "High-Throughput JPEG 2000 Irreversible Compression"),
        "ISO_18181_1":  ("ISO181811",  "LossyCompression", "JPEG XL Image Coding System - Part 1 Core Coding System"),
        "ISO_13818_2":  ("ISO138182",  "LossyCompression", "MPEG2 Compression"),
        "ISO_14496_10": ("ISO1449610", "LossyCompression", "MPEG-4 AVC/H.264 Compression"),
        "ISO_23008_2":  ("ISO230082",  "LossyCompression", "HEVC/H.265 Lossy Compression")
    }

    # 
    # Patient Sex
    #

    # A dictionary mapping a DICOM PatientSex tag value to a corresponding SNOMED-CT code for SPHN
    # Key: DICOM PatientSex tag value
    # Value: a tuple containing the SNOMED-CT coding scheme designator, code value, and human-readable description
    dicom_patient_sex_code_dict: ClassVar[ReadOnly[dict[str, tuple[str,str,str]]]] = {
        "F":    ("SNOMED", "248152002",         "| Female (finding) |"),            # Female
        "M":    ("SNOMED", "248153007",         "| Male (finding) |"),              # Male
        "O":    ("SNOMED", "32570681000036106", "| Indeterminate sex (finding) |")  # Other 
    }

    # 
    # Pregnancy Status
    #

    # A dictionary mapping a DICOM PregnancyStatus tag value to a corresponding SNOMED-CT code for SPHN
    # Key: DICOM PregnancyStatus tag value
    # Value: a tuple containing the SNOMED-CT coding scheme designator, code value, and human-readable description
    dicom_pregnancy_status_code_dict: ClassVar[ReadOnly[dict[int, tuple[str,str,str]]]] = {
        1:  ("SNOMED", "60001007", "| Not pregnant (finding) |"),   # Not Pregnant
      # 2:  "",                                                     # Possibly Pregnant     # No SPHN use
        3:  ("SNOMED", "77386006", "| Pregnancy (finding) |"),      # Definitely Pregnant
      # 4:  ""                                                      # Unknown               # No SPHN use
    }

    # 
    # Content Qualification
    #

    # A dictionary mapping a DICOM ContentQualification tag value to a corresponding SPHN ImagingSeries_contentQualification ValueSet member
    # Key: DICOM ContentQualification tag value
    # Value: corresponding SPHN ImagingSeries_contentQualification ValueSet member
    dicom_content_qualification_dict: ClassVar[ReadOnly[dict[str, str]]] = {
        "Product":      "Product",
        "Research":     "Research",
        "Service":      "Service"
    }

    # Using lower case keys
    dicom_content_qualification_dict_lower_case_key: \
        ClassVar[ReadOnly[dict[str, str]]] = \
            {k.lower(): v for k, v in dicom_content_qualification_dict.items()}

    # 
    # Image and Frame Type
    #

    # A dictionary mapping DICOM ImageType and FrameType tag item values to corresponding SPHN ImagingFrame_type ValueSet members
    # Key: DICOM ImageType or FrameType tag item value (e.g. "2D Imaging")
    # Value: corresponding SPHN ImagingFrame_type ValueSet member (e.g. "2DImaging")
    dicom_image_and_frame_type_dict: ClassVar[ReadOnly[dict[str, str]]] = {
        "2D Imaging":               "2DImaging",
        "3D Rendering":             "3DRendering",
        "Abdominal":                "Abdominal",
        "Addition":                 "Addition",
        "Angio":                    "Angio",
        "Angio Time":               "AngioTime",
        "ASL":                      "ASL",
        "Attenuation":              "Attenuation",
        "Axial":                    "Axial",
        "Biplane A":                "BiplaneA",
        "Biplane B":                "BiplaneB",
        "Blank":                    "Blank",
        "Breast":                   "Breast",
        "Cardiac":                  "Cardiac",
        "Cardiac Cascore":          "CardiacCascore",
        "Cardiac Cta":              "CardiacCta",
        "Cardiac Gated":            "CardiacGated",
        "Cardresp Gated":           "CardrespGated",
        "Chest":                    "Chest",
        "Cine":                     "Cine",
        "Color Doppler":            "ColorDoppler",
        "Color M-Mode":             "ColorMMode",
        "Color Power Mode":         "ColorPowerMode",
        "Corneal Topo":             "CornealTopo",
        "CW Doppler":               "CWDoppler",
        "Density Map":              "DensityMap",
        "Derived":                  "Derived",
        "Diffusion":                "Diffusion",
        "Diffusion Map":            "DiffusionMap",
        "Division":                 "Division",
        "Dixon":                    "Dixon",
        "DRR":                      "DRR",
        "Dynamic":                  "Dynamic",
        "Eff Atomic Num":           "EffAtomicNum",
        "Electron Density":         "ElectronDensity",
        "Emission":                 "Emission",
        "Endocavitary":             "Endocavitary", 
        "Endorectal":               "Endorectal", 
        "Endovaginal":              "Endovaginal", 
        "Energy Prop Wt":           "EnergyPropWt", 
        "Epicardial":               "Epicardial", 
        "Fetal Heart":              "FetalHeart", 
        "Filtered":                 "Filtered", 
        "Flow Encoded":             "FlowEncoded", 
        "Fluence":                  "Fluence", 
        "Fluid Attenuated":         "FluidAttenuated", 
        "Fluoroscopy":              "Fluoroscopy", 
        "FMRI":                     "FMRI", 
        "Gated":                    "Gated", 
        "Gated Tomo":               "GatedTomo", 
        "Generated 2D":             "Generated2D", 
        "Gynecology":               "Gynecology", 
        "High Energy":              "HighEnergy", 
        "Image Addition":           "ImageAddition", 
        "Intracardiac":             "Intracardiac", 
        "Intraoperative":           "Intraoperative", 
        "Intravascular":            "Intravascular", 
        "Label":                    "Label", 
        "Localizer":                "Localizer", 
        "Longitudinal":             "Longitudinal", 
        "Low Energy":               "LowEnergy", 
        "M Mode":                   "MMode", 
        "Masked":                   "Masked", 
        "Mat Fractional":           "MatFractional", 
        "Mat Modified":             "MatModified", 
        "Mat Removed":              "MatRemoved", 
        "Mat Specific":             "MatSpecific", 
        "Mat Value Based":          "MatValueBased", 
        "Max IP":                   "MaxIP", 
        "Maximum":                  "Maximum", 
        "Mean":                     "Mean", 
        "Median":                   "Median", 
        "Metabolite Map":           "MetaboliteMap", 
        "Min IP":                   "MinIP", 
        "Minimum":                  "Minimum", 
        "Mixed":                    "Mixed", 
        "Modulus Subtract":         "ModulusSubtract", 
        "Montage":                  "Montage", 
        "Motion":                   "Motion", 
        "MPR":                      "MPR", 
        "Multiecho":                "Multiecho", 
        "Multiplication":           "Multiplication", 
        "Musculoskeletal":          "Musculoskeletal", 
        "Neonatal Head":            "NeonatalHead", 
        "Non Parallel":             "NonParallel", 
        "None":                     "None", 
        "Obstetrical":              "Obstetrical", 
        "ONH":                      "ONH", 
        "Ophthalmic":               "Ophthalmic", 
        "Original":                 "Original", 
        "Other":                    "Other", 
        "Overview":                 "Overview", 
        "Parallel":                 "Parallel", 
        "Pediatric":                "Pediatric", 
        "Pelvic":                   "Pelvic", 
        "Perfusion":                "Perfusion", 
        "Phase Map":                "PhaseMap", 
        "Phase Subtract":           "PhaseSubtract", 
        "Portal":                   "Portal", 
        "Post Contrast":            "PostContrast", 
        "Postbiopsy":               "Postbiopsy", 
        "Postbiopsy Minus":         "PostbiopsyMinus", 
        "Postbiopsy Plus":          "PostbiopsyPlus", 
        "Postfire":                 "Postfire", 
        "Postfire Minus":           "PostfireMinus", 
        "Postfire Plus":            "PostfirePlus", 
        "Postmarker":               "Postmarker", 
        "Postmarker Minus":         "PostmarkerMinus", 
        "Postmarker Plus":          "PostmarkerPlus", 
        "Pre Contrast":             "PreContrast", 
        "Prefire":                  "Prefire", 
        "Prefire Minus":            "PrefireMinus", 
        "Prefire Plus":             "PrefirePlus", 
        "Primary":                  "Primary", 
        "Projection Image":         "ProjectionImage", 
        "Proton Density":           "ProtonDensity", 
        "PW Doppler":               "PWDoppler", 
        "Quantity":                 "Quantity", 
        "Radiograph":               "Radiograph", 
        "Realtime":                 "Realtime", 
        "Recon Gated Tomo":         "ReconGatedTomo", 
        "Recon Tomo":               "ReconTomo", 
        "Reference":                "Reference", 
        "Resampled":                "Resampled", 
        "Resp Gated":               "RespGated", 
        "Rest":                     "Rest", 
        "Retinal Thick":            "RetinalThick", 
        "Retroperitoneal":          "Retroperitoneal", 
        "Scrotal":                  "Scrotal", 
        "Secondary":                "Secondary", 
        "Simulator":                "Simulator", 
        "Single Plane":             "SinglePlane", 
        "Small Parts":              "SmallParts", 
        "Spatially-Related Frames": "SpatiallyRelatedFrames", 
        "Spectroscopy":             "Spectroscopy", 
        "Static":                   "Static", 
        "Std Deviation":            "StdDeviation", 
        "Stereo L":                 "StereoL", 
        "Stereo Minus":             "StereoMinus", 
        "Stereo Plus":              "StereoPlus", 
        "Stereo R":                 "StereoR", 
        "Stereo Scout":             "StereoScout", 
        "STIR":                     "STIR", 
        "Stress":                   "Stress", 
        "Subtraction":              "Subtraction", 
        "T1":                       "T1", 
        "T1 Map":                   "T1Map", 
        "T2":                       "T2", 
        "T2 Map":                   "T2Map", 
        "T2 Star":                  "T2Star", 
        "Tagging":                  "Tagging", 
        "TEE":                      "TEE", 
        "Temperature":              "Temperature", 
        "Thumbnail":                "Thumbnail", 
        "Thyroid":                  "Thyroid", 
        "Tissue Characterization":  "TissueCharacterization", 
        "TOF":                      "TOF", 
        "Tomo":                     "Tomo", 
        "Tomo Proj":                "TomoProj", 
        "Tomo Scout":               "TomoScout", 
        "Tomosynthesis":            "Tomosynthesis", 
        "Transcranial":             "Transcranial", 
        "Transmission":             "Transmission", 
        "TTE":                      "TTE", 
        "US Biopsy":                "USBiopsy", 
        "Vascular":                 "Vascular", 
        "Velocity":                 "Velocity", 
        "Velocity Map":             "VelocityMap", 
        "VMI":                      "VMI", 
        "Volume":                   "Volume", 
        "Whole Body":               "WholeBody"
    }

    # Using lower case keys
    dicom_image_and_frame_type_dict_lower_case_key: \
        ClassVar[ReadOnly[dict[str, str]]] = \
            {k.lower(): v for k, v in dicom_image_and_frame_type_dict.items()}


    #
    # Body Part Examined
    #

    # The DICOM BodyPartExamined tag value uses DICOM defined terms which should be converted to SNOMED-CT codes for SPHN

    # The newer DICOM tags: 
    # - Anatomic Region Sequence (0008,2218) or 
    # - Primary Anatomic Structure Sequence (0008,2228)
    # already use the indicated SNOMED-CT codes, so this dictionary is only needed for the older BodyPartExamined tag (0018,0015)
    #

    # A dictionary mapping DICOM BodyPartExamined tag values to corresponding SNOMED-CT codes for SPHN
    # Key: DICOM BodyPartExamined tag value (e.g. "ABDOMEN")
    # Value: corresponding SNOMED-CT code (e.g. "818981001")
    # Note: The indicated SNOMED-CT human-readable descriptions are from DICOM and may not be the same as the official SNOMED-CT descriptions
    # Link:https://dicom.nema.org/medical/dicom/current/output/chtml/part16/chapter_L.html
    dicom_body_part_examined_terms_dict: ClassVar[ReadOnly[dict[str, tuple[str,str,str]]]] = {
        "ABDOMEN":          ("SNOMED", "818981001",  "| Abdomen |"),
        "ABDOMENPELVIS":    ("SNOMED", "818982008",  "| Abdomen and Pelvis |"),
        "ABDOMINALAORTA":   ("SNOMED", "7832008",    "| Abdominal aorta |"),
        "ACJOINT":          ("SNOMED", "85856004",   "| Acromioclavicular joint |"),
        "ADRENAL":          ("SNOMED", "23451007",   "| Adrenal gland |"),
        "AMNIOTICFLUID":    ("SNOMED", "77012006",   "| Amniotic fluid |"),
        "ANKLE":            ("SNOMED", "70258002",   "| Ankle joint |"),
        #                   ("SNOMED", "128585006",  "| Anomalous pulmonary vein |"),
        "ANTECUBITALV":     ("SNOMED", "128553008",  "| Antecubital vein |"),
        "ANTCARDIACV":      ("SNOMED", "194996006",  "| Anterior cardiac vein |"),
        "ACA":              ("SNOMED", "60176003",   "| Anterior cerebral artery |"),
        "ANTCOMMA":         ("SNOMED", "8012006",    "| Anterior communicating artery |"),
        "ANTSPINALA":       ("SNOMED", "17388009",   "| Anterior spinal artery |"),
        "ANTTIBIALA":       ("SNOMED", "68053000",   "| Anterior tibial artery |"),
        #                   ("SNOMED", "53505006",   "| Anus |"),
        "ANUSRECTUMSIGMD":  ("SNOMED", "110612005",  "| Anus, rectum and sigmoid colon |"),
        "AORTA":            ("SNOMED", "15825003",   "| Aorta |"),
        "AORTICARCH":       ("SNOMED", "57034009",   "| Aortic arch |"),
        #                   ("SNOMED", "128551005",  "| Aortic fistula |"),
        #                   ("SNOMED", "128564006",  "| Apex of left ventricle |"),
        #                   ("SNOMED", "86598002",   "| Apex of Lung |"),
        #                   ("SNOMED", "128565007",  "| Apex of right ventricle |"),
        "APPENDIX":         ("SNOMED", "66754008",   "| Appendix |"),
        "ARTERY":           ("SNOMED", "51114001",   "| Artery |"),
        "ASCAORTA":         ("SNOMED", "54247002",   "| Ascending aorta |"),
        "ASCENDINGCOLON":   ("SNOMED", "9040008",    "| Ascending colon |"),
        #                   ("SNOMED", "59652004",   "| Atrium |"),
        "AXILLA":           ("SNOMED", "91470000",   "| Axilla |"),
        "AXILLARYA":        ("SNOMED", "67937003",   "| Axillary Artery |"),
        "AXILLARYV":        ("SNOMED", "68705008",   "| Axillary vein |"),
        "AZYGOSVEIN":       ("SNOMED", "72107004",   "| Azygos vein |"),
        "BACK":             ("SNOMED", "77568009",   "| Back |"),
        #                   ("SNOMED", "128981007",  "| Baffle |"),
        "ASILARA":          ("SNOMED", "59011009",   "| Basilar artery |"),
        "BILEDUCT":         ("SNOMED", "28273000",   "| Bile duct |"),
        "BILIARYTRACT":     ("SNOMED", "34707002",   "| Biliary tract |"),
        "BLADDER":          ("SNOMED", "89837001",   "| Bladder |"),
        "BLADDERURETHRA":   ("SNOMED", "110837003",  "| Bladder and urethra |"),
        #                   ("SNOMED", "91830000",   "| Body conduit |"),
        #                   ("SNOMED", "72001000",   "| Bone of lower limb |"),
        #                   ("SNOMED", "371195002",  "| Bone of upper limb |"),
        #                   ("SNOMED", "128548003",  "| Boyd's perforating vein |"),
        "BRACHIALA":        ("SNOMED", "17137000",   "| Brachial artery |"),
        "BRACHIALV":        ("SNOMED", "20115005",   "| Brachial vein |"),
        "BRAIN":            ("SNOMED", "12738006",   "| Brain |"),
        "BREAST":           ("SNOMED", "76752008",   "| Breast |"),
        #                   ("SNOMED", "34411009",   "| Broad ligament |"),
        "BRONCHUS":         ("SNOMED", "955009",     "| Bronchus |"),
        #                   ("SNOMED", "60819002",   "| Buccal region of face |"),
        "BUTTOCK":          ("SNOMED", "46862004",   "| Buttock |"),
        "CALCANEUS":        ("SNOMED", "80144004",   "| Calcaneus |"),
        "CALF":             ("SNOMED", "53840002",   "| Calf of leg |"),
        #                   ("SNOMED", "2334006",    "| Calyx |"),
        "CAROTID":          ("SNOMED", "69105007",   "| Carotid Artery |"),
        "BULB":             ("SNOMED", "21479005",   "| Carotid bulb |"),
        "CELIACA":          ("SNOMED", "57850000",   "| Celiac artery |"),
        "CEPHALICV":        ("SNOMED", "20699002",   "| Cephalic vein |"),
        "CEREBELLUM":       ("SNOMED", "113305005",  "| Cerebellum |"),
        "CEREBRALA":        ("SNOMED", "88556005",   "| Cerebral artery |"),
        "CEREBHEMISPHERE":  ("SNOMED", "372073000",  "| Cerebral hemisphere |"),
        "CSPINE":           ("SNOMED", "122494005",  "| Cervical spine |"),
        "CTSPINE":          ("SNOMED", "1217257000", "| Cervico-thoracic spine |"),
        "CERVIX":           ("SNOMED", "71252005",   "| Cervix |"),
        "CHEEK":            ("SNOMED", "60819002",   "| Cheek |"),
        "CHEST":            ("SNOMED", "43799004",   "| Chest |"),
        "CHESTABDPELVIS":   ("SNOMED", "416775004",  "| Chest, Abdomen and Pelvis |"),
        "CHESTABDOMEN":     ("SNOMED", "416550000",  "| Chest and Abdomen |"),
        "CHOROIDPLEXUS":    ("SNOMED", "80621003",   "| Choroid plexus |"),
        "CIRCLEOFWILLIS":   ("SNOMED", "11279006",   "| Circle of Willis |"),
        "CLAVICLE":         ("SNOMED", "51299004",   "| Clavicle |"),
        "COCCYX":           ("SNOMED", "64688005",   "| Coccyx |"),
        "COLON":            ("SNOMED", "71854001",   "| Colon |"),
        #                   ("SNOMED", "253276007",  "| Common atrium |"),
        "COMMONBILEDUCT":   ("SNOMED", "79741001",   "| Common bile duct |"),
        "CCA":              ("SNOMED", "32062004",   "| Common carotid artery |"),
        "CFA":              ("SNOMED", "181347005",  "| Common femoral artery |"),
        "CFV":              ("SNOMED", "397363009",  "| Common femoral vein |"),
        "COMILIACA":        ("SNOMED", "73634005",   "| Common iliac artery |"),
        "COMILIACV":        ("SNOMED", "46027005",   "| Common iliac vein |"),
        #                   ("SNOMED", "45503006",   "| Common ventricle |"),
        #                   ("SNOMED", "128555001",  "| Congenital coronary artery fistula to left atrium |"),
        #                   ("SNOMED", "128556000",  "| Congenital coronary artery fistula to left ventricle |"),
        #                   ("SNOMED", "128557009",  "| Congenital coronary artery fistula to right atrium |"),
        #                   ("SNOMED", "128558004",  "| Congenital coronary artery fistula to right ventricle |"),
        #                   ("SNOMED", "111289009",  "| Pulmonary arteriovenous fistula |"),
        "CORNEA":           ("SNOMED", "28726007",   "| Cornea |"),
        "CORONARYARTERY":   ("SNOMED", "41801008",   "| Coronary artery |"),
        "CORONARYSINUS":    ("SNOMED", "90219004",   "| Coronary sinus |"),
        #                   ("SNOMED", "128320002",  "| Cranial venous system |"),
        "DESCAORTA":        ("SNOMED", "281130003",  "| Descending aorta |"),
        "DESCENDINGCOLON":  ("SNOMED", "32622004",   "| Descending colon |"),
        #                   ("SNOMED", "128554002",  "| Dodd's perforating vein |"),
        "DUODENUM":         ("SNOMED", "38848004",   "| Duodenum |"),
        "EAR":              ("SNOMED", "117590005",  "| Ear |"),
        "ELBOW":            ("SNOMED", "16953009",   "| Elbow joint |"),
        "ENDOARTERIAL":     ("SNOMED", "51114001",   "| Endo-arterial |"),
        "ENDOCARDIAC":      ("SNOMED", "80891009",   "| Endo-cardiac |"),
        "ENDOESOPHAGEAL":   ("SNOMED", "32849002",   "| Endo-esophageal |"),
        "ENDOMETRIUM":      ("SNOMED", "2739003",    "| Endometrium |"),
        "ENDONASAL":        ("SNOMED", "53342003",   "| Endo-nasal |"),
        "ENDONASOPHARYNYX": ("SNOMED", "18962004",   "| Endo-nasopharyngeal |"),
        "ENDORECTAL":       ("SNOMED", "34402009",   "| Endo-rectal |"),
        "ENDORENAL":        ("SNOMED", "64033007",   "| Endo-renal |"),
        "ENDOURETERIC":     ("SNOMED", "87953007",   "| Endo-ureteric |"),
        "ENDOURETHRAL":     ("SNOMED", "13648007",   "| Endo-urethral |"),
        "ENDOVAGINAL":      ("SNOMED", "76784001",   "| Endo-vaginal |"),
        "ENDOVASCULAR":     ("SNOMED", "59820001",   "| Endo-vascular |"),
        "ENDOVENOUS":       ("SNOMED", "29092000",   "| Endo-venous |"),
        "ENDOVESICAL":      ("SNOMED", "48367006",   "| Endo-vesical |"),
        "WHOLEBODY":        ("SNOMED", "38266002",   "| Entire body |"),
        "EPIDIDYMIS":       ("SNOMED", "87644002",   "| Epididymis |"),
        "EPIGASTRIC":       ("SNOMED", "27947004",   "| Epigastric region |"),
        "ESOPHAGUS":        ("SNOMED", "32849002",   "| Esophagus |"),
        #                   ("SNOMED", "110861005",  "| Esophagus, stomach and duodenum |"),
        "EAC":              ("SNOMED", "84301002",   "| External auditory canal |"),
        "ECA":              ("SNOMED", "22286001",   "| External carotid artery |"),
        "EXTILIACA":        ("SNOMED", "113269004",  "| External iliac artery |"),
        "EXTILIACV":        ("SNOMED", "63507001",   "| External iliac vein |"),
        "EXTJUGV":          ("SNOMED", "71585003",   "| External jugular vein |"),
        "EXTREMITY":        ("SNOMED", "66019005",   "| Extremity |"),
        "EYE":              ("SNOMED", "81745001",   "| Eye |"),
        "EYELID":           ("SNOMED", "80243003",   "| Eyelid |"),
        #                   ("SNOMED", "371398005",  "| Eye region |"),
        "FACE":             ("SNOMED", "89545001",   "| Face |"),
        "FACIALA":          ("SNOMED", "23074001",   "| Facial artery |"),
        #                   ("SNOMED", "91397008",   "| Facial bones |"),
        "FEMORALA":         ("SNOMED", "7657000",    "| Femoral artery |"),
        "FEMORALV":         ("SNOMED", "83419000",   "| Femoral vein |"),
        "FEMUR":            ("SNOMED", "71341001",   "| Femur |"),
        #FETALARM		Fetal arm
        #FETALDIGIT		Fetal digit
        #FETALHEART		Fetal heart
        #FETALLEG		Fetal leg
        #FETALPOLE		Fetal pole
        "FIBULA":           ("SNOMED", "87342007",   "| Fibula |"),
        "FINGER":           ("SNOMED", "7569003",    "| Finger |"),
        "FLANK":            ("SNOMED", "58602004",   "| Flank |"),
        "FONTANEL":         ("SNOMED", "79361005",   "| Fontanel of skull |"),
        "FOOT":             ("SNOMED", "56459004",   "| Foot |"),
        "FOREARM":          ("SNOMED", "14975008",   "| Forearm |"),
        "4THVENTRICLE":     ("SNOMED", "35918002",   "| Fourth ventricle |"),
        "GALLBLADDER":      ("SNOMED", "28231008",   "| Gallbladder |"),
        "GASTRICV":         ("SNOMED", "110568007",  "| Gastric vein |"),
        "GENICULARA":       ("SNOMED", "128559007",  "| Genicular artery |"),
        "GESTSAC":          ("SNOMED", "300571009",  "| Gestational sac |"),
        "GLUTEAL":          ("SNOMED", "46862004",   "| Gluteal region |"),
        #                   ("SNOMED", "5928000",    "| Great cardiac vein |"),
        "GSV":              ("SNOMED", "60734001",   "| Great saphenous vein |"),
        "HAND":             ("SNOMED", "85562004",   "| Hand |"),
        "HEAD":             ("SNOMED", "69536005",   "| Head |"),
        "HEADNECK":         ("SNOMED", "774007",     "| Head and Neck |"),
        "HEART":            ("SNOMED", "80891009",   "| Heart |"),
        "HEPATICA":         ("SNOMED", "76015000",   "| Hepatic artery |"),
        "HEPATICV":         ("SNOMED", "8993003",    "| Hepatic vein |"),
        "HIP":              ("SNOMED", "24136001",   "| Hip joint |"),
        "HUMERUS":          ("SNOMED", "85050009",   "| Humerus |"),
        #                   ("SNOMED", "128560002",  "| Hunterian perforating vein |"),
        "HYPOGASTRIC":      ("SNOMED", "11708003",   "| Hypogastric region |"),
        "HYPOPHARYNX":      ("SNOMED", "81502006",   "| Hypopharynx |"),
        "ILEUM":            ("SNOMED", "34516001",   "| Ileum |"),
        #                   ("SNOMED", "299716001",  "| Iliac and/or femoral artery |"),
        "ILIACA":           ("SNOMED", "10293006",   "| Iliac artery |"),
        "ILIACV":           ("SNOMED", "244411005",  "| Iliac vein |"),
        "ILIUM":            ("SNOMED", "22356005",   "| Ilium |"),
        #                   ("SNOMED", "195416006",  "| Inferior cardiac vein |"),
        #                   ("SNOMED", "51249003",   "| Inferior left pulmonary vein |"),
        "INFMESA":          ("SNOMED", "33795007",   "| Inferior mesenteric artery |"),
        #                   ("SNOMED", "113273001",  "| Inferior right pulmonary vein |"),
        "INFVENACAVA":      ("SNOMED", "64131007",   "| Inferior vena cava |"),
        "INGUINAL":         ("SNOMED", "26893007",   "| Inguinal region |"),
        "INNOMINATEA":      ("SNOMED", "12691009",   "| Innominate artery |"),
        "INNOMINATEV":      ("SNOMED", "8887007",    "| Innominate vein |"),
        "IAC":              ("SNOMED", "361078006",  "| Internal Auditory Canal |"),
        "ICA":              ("SNOMED", "86117002",   "| Internal carotid artery |"),
        "INTILIACA":        ("SNOMED", "90024005",   "| Internal iliac artery |"),
        "INTJUGULARV":      ("SNOMED", "12123001",   "| Internal jugular vein |"),
        "INTMAMMARYA":      ("SNOMED", "69327007",   "| Internal mammary artery |"),
        #                   ("SNOMED", "818987002",  "| Intra-abdominopelvic |"),
        #                   ("SNOMED", "131183008",  "| Intra-articular |"),
        "INTRACRANIAL":     ("SNOMED", "1101003",    "| Intracranial |"),
        #                   ("SNOMED", "32849002",   "| Intra-esophageal |"),
        #                   ("SNOMED", "816989007",  "| Intra-pelvic |"),
        #                   ("SNOMED", "43799004",   "| Intra-thoracic |"),
        "JAW":              ("SNOMED", "661005",     "| Jaw region |"),
        "JEJUNUM":          ("SNOMED", "21306003",   "| Jejunum |"),
        "JOINT":            ("SNOMED", "39352004",   "| Joint |"),
        #                   ("SNOMED", "128563000",  "| Juxtaposed atrial appendage |"),
        "KIDNEY":           ("SNOMED", "64033007",   "| Kidney |"),
        "KNEE":             ("SNOMED", "72696002",   "| Knee |"),
        "LACRIMALA":        ("SNOMED", "59749000",   "| Lacrimal artery |"),
        #                   ("SNOMED", "128979005",  "| Lacrimal artery of right eye |"),
        "LARGEINTESTINE":   ("SNOMED", "14742008",   "| Large intestine |"),
        "LARYNX":           ("SNOMED", "4596009",    "| Larynx |"),
        "LATVENTRICLE":     ("SNOMED", "66720007",   "| Lateral Ventricle |"),
        "LATRIUM":          ("SNOMED", "82471001",   "| Left atrium |"),
        #                   ("SNOMED", "33626005",   "| Left auricular appendage |"),
        "LFEMORALA":        ("SNOMED", "113270003",  "| Left femoral artery |"),
        "LHEPATICV":        ("SNOMED", "273202007",  "| Left hepatic vein |"),
        "LHYPOCHONDRIAC":   ("SNOMED", "133945003",  "| Left hypochondriac region |"),
        "LINGUINAL":        ("SNOMED", "85119005",   "| Left inguinal region |"),
        "LLQ":              ("SNOMED", "68505006",   "| Left lower quadrant of abdomen |"),
        "LLUMBAR":          ("SNOMED", "1017210004", "| Left lumbar region |"),
        "LPORTALV":         ("SNOMED", "70253006",   "| Left portal vein |"),
        "LPULMONARYA":      ("SNOMED", "50408007",   "| Left pulmonary artery |"),
        "LUQ":              ("SNOMED", "86367003",   "| Left upper quadrant of abdomen |"),
        "LVENTRICLE":       ("SNOMED", "87878005",   "| Left ventricle |"),
        #                   ("SNOMED", "70238003",   "| Left ventricle inflow tract |"),
        #                   ("SNOMED", "13418002",   "| Left ventricle outflow tract |"),
        "LINGUALA":         ("SNOMED", "113264009",  "| Lingual artery |"),
        "LIVER":            ("SNOMED", "10200004",   "| Liver |"),
        #                   ("SNOMED", "19100000",   "| Lower inner quadrant of breast |"),
        "LOWERLEG":         ("SNOMED", "30021000",   "| Lower leg |"),
        "LOWERLIMB":        ("SNOMED", "61685007",   "| Lower limb |"),
        #                   ("SNOMED", "33564002",   "| Lower outer quadrant of breast |"),
        "LUMBARA":          ("SNOMED", "34635009",   "| Lumbar artery |"),
        "LUMBAR":           ("SNOMED", "52612000",   "| Lumbar region |"),
        "LSPINE":           ("SNOMED", "122496007",  "| Lumbar spine |"),
        "LSSPINE":          ("SNOMED", "1217253001", "| Lumbo-sacral spine |"),
        "LUMEN":            ("SNOMED", "91747007",   "| Lumen of blood vessel |"),
        "LUNG":             ("SNOMED", "39607008",   "| Lung |"),
        "MANDIBLE":         ("SNOMED", "91609006",   "| Mandible |"),
        "MASTOID":          ("SNOMED", "59066005",   "| Mastoid bone |"),
        "MAXILLA":          ("SNOMED", "70925003",   "| Maxilla |"),
        "MEDIASTINUM":      ("SNOMED", "72410000",   "| Mediastinum |"),
        "MESENTRICA":       ("SNOMED", "86570000",   "| Mesenteric artery |"),
        "MESENTRICV":       ("SNOMED", "128583004",  "| Mesenteric vein |"),
        "MCA":              ("SNOMED", "17232002",   "| Middle cerebral artery |"),
        "MIDHEPATICV":      ("SNOMED", "273099000",  "| Middle hepatic vein |"),
        "MORISONSPOUCH":    ("SNOMED", "243977002",  "| Morisons pouch |"),
        "MOUTH":            ("SNOMED", "123851003",  "| Mouth |"),
        #                   ("SNOMED", "102292000",  "| Muscle of lower limb |"),
        #                   ("SNOMED", "30608006",   "| Muscle of upper limb |"),
        #                   ("SNOMED", "74386004",   "| Nasal bone |"),
        "NASOPHARYNX":      ("SNOMED", "360955006",  "| Nasopharynx |"),
        "NECK":             ("SNOMED", "45048000",   "| Neck |"),
        "NECKCHESTABDPELV": ("SNOMED", "416319003",  "| Neck, Chest, Abdomen and Pelvis |"),
        "NECKCHESTABDOMEN": ("SNOMED", "416152001",  "| Neck, Chest and Abdomen |"),
        "NECKCHEST":        ("SNOMED", "417437006",  "| Neck and Chest |"),
        "NOSE":             ("SNOMED", "45206002",   "| Nose |"),
        "OCCPITALA":        ("SNOMED", "31145008",   "| Occipital artery |"),
        "OCCIPTALV":        ("SNOMED", "32114007",   "| Occipital vein |"),
        #                   ("SNOMED", "113346000",  "| Omental bursa |"),
        #                   ("SNOMED", "27398004",   "| Omentum |"),
        "OPHTHALMICA":      ("SNOMED", "53549008",   "| Ophthalmic artery |"),
        "OPTICCANAL":       ("SNOMED", "55024004",   "| Optic canal |"),
        "ORBIT":            ("SNOMED", "363654007",  "| Orbital structure |"),
        "OVARY":            ("SNOMED", "15497006",   "| Ovary |"),
        "PANCREAS":         ("SNOMED", "15776009",   "| Pancreas |"),
        "PANCREATICDUCT":   ("SNOMED", "69930009",   "| Pancreatic duct |"),
        "PANCBILEDUCT":     ("SNOMED", "110621006",  "| Pancreatic duct and bile duct systems |"),
        #                   ("SNOMED", "2095001",    "| Paranasal sinus |"),
        "PARASTERNAL":      ("SNOMED", "91691001",   "| Parasternal |"),
        "PARATHYROID":      ("SNOMED", "111002",     "| Parathyroid |"),
        "PAROTID":          ("SNOMED", "45289007",   "| Parotid gland |"),
        "PATELLA":          ("SNOMED", "64234005",   "| Patella |"),
        #                   ("SNOMED", "83330001",   "| Patent ductus arteriosus |"),
        "PELVIS":           ("SNOMED", "816092008",  "| Pelvis |"),
        "PELVISLOWEXTREMT": ("SNOMED", "1231522001", "| Pelvis and lower extremities |"),
        "PENILEA":          ("SNOMED", "282044005",  "| Penile artery |"),
        "PENIS":            ("SNOMED", "18911002",   "| Penis |"),
        "PERINEUM":         ("SNOMED", "38864007",   "| Perineum |"),
        "PERONEALA":        ("SNOMED", "8821006",    "| Peroneal artery |"),
        "PHANTOM":          ("SNOMED", "706342009",  "| Phantom |"),
        "PHARYNX":          ("SNOMED", "54066008",   "| Pharynx |"),
        "PHARYNXLARYNX":    ("SNOMED", "312535008",  "| Pharynx and larynx |"),
        "PLACENTA":         ("SNOMED", "78067005",   "| Placenta |"),
        "POPLITEALA":       ("SNOMED", "43899006",   "| Popliteal artery |"),
        "POPLITEALFOSSA":   ("SNOMED", "32361000",   "| Popliteal fossa |"),
        "POPLITEALV":       ("SNOMED", "56849005",   "| Popliteal vein |"),
        "PORTALV":          ("SNOMED", "32764006",   "| Portal vein |"),
        "PCA":              ("SNOMED", "70382005",   "| Posterior cerebral artery |"),
        "POSCOMMA":         ("SNOMED", "43119007",   "| Posterior communicating artery |"),
        #                   ("SNOMED", "128569001",  "| Posterior medial tributary |"),
        "POSTIBIALA":       ("SNOMED", "13363002",   "| Posterior tibial artery |"),
        #                   ("SNOMED", "14944004",   "| Primitive aorta |"),
        #                   ("SNOMED", "91707000",   "| Primitive pulmonary artery |"),
        "PROFFEMA":         ("SNOMED", "31677005",   "| Profunda femoris artery |"),
        "PROFFEMV":         ("SNOMED", "23438002",   "| Profunda femoris vein |"),
        "PROSTATE":         ("SNOMED", "41216001",   "| Prostate |"),
        "PULMONARYA":       ("SNOMED", "81040000",   "| Pulmonary artery |"),
        #                   ("SNOMED", "128584005",  "| Pulmonary artery conduit |"),
        #                   ("SNOMED", "128586007",  "| Pulmonary chamber of cor triatriatum |"),
        "PULMONARYV":       ("SNOMED", "122972007",  "| Pulmonary vein |"),
        #                   ("SNOMED", "128566008",  "| Pulmonary vein confluence |"),
        #                   ("SNOMED", "128567004",  "| Pulmonary venous atrium |"),
        "RADIALA":          ("SNOMED", "45631007",   "| Radial artery |"),
        "RADIUS":           ("SNOMED", "62413002",   "| Radius |"),
        "RADIUSULNA":       ("SNOMED", "110535000",  "| Radius and ulna |"),
        "CULDESAC":         ("SNOMED", "53843000",   "| Rectouterine pouch |"),
        "RECTUM":           ("SNOMED", "34402009",   "| Rectum |"),
        "RENALA":           ("SNOMED", "2841007",    "| Renal artery |"),
        #                   ("SNOMED", "25990002",   "| Renal pelvis |"),
        "RENALV":           ("SNOMED", "56400007",   "| Renal vein |"),
        "RETROPERITONEUM":  ("SNOMED", "82849001",   "| Retroperitoneum |"),
        "RIB":              ("SNOMED", "113197003",  "| Rib |"),
        "RATRIUM":          ("SNOMED", "73829009",   "| Right atrium |"),
        #                   ("SNOMED", "68300000",   "| Right auricular appendage |"),
        "RFEMORALA":        ("SNOMED", "69833005",   "| Right femoral artery |"),
        "RHEPATICV":        ("SNOMED", "272998002",  "| Right hepatic vein |"),
        "RHYPOCHONDRIAC":   ("SNOMED", "133946002",  "| Right hypochondriac region |"),
        "RINGUINAL":        ("SNOMED", "37117007",   "| Right inguinal region |"),
        "RLQ":              ("SNOMED", "48544008",   "| Right lower quadrant of abdomen |"),
        "RLUMBAR":          ("SNOMED", "1017211000", "| Right lumbar region |"),
        "RPORTALV":         ("SNOMED", "73931004",   "| Right portal vein |"),
        "RPULMONARYA":      ("SNOMED", "78480002",   "| Right pulmonary artery |"),
        "RUQ":              ("SNOMED", "50519007",   "| Right upper quadrant of abdomen |"),
        "RVENTRICLE":       ("SNOMED", "53085002",   "| Right ventricle |"),
        #                   ("SNOMED", "8017000",    "| Right ventricle inflow |"),
        #                   ("SNOMED", "44627009",   "| Right ventricle outflow tract |"),
        "SIJOINT":          ("SNOMED", "39723000",   "| Sacroiliac joint |"),
        "SSPINE":           ("SNOMED", "54735007",   "| Sacrum |"),
        "SFJ":              ("SNOMED", "128587003",  "| Saphenofemoral junction |"),
        "SAPHENOUSV":       ("SNOMED", "362072009",  "| Saphenous vein |"),
        "SCALP":            ("SNOMED", "41695006",   "| Scalp |"),
        "SCAPULA":          ("SNOMED", "79601000",   "| Scapula |"),
        "SCLERA":           ("SNOMED", "18619003",   "| Sclera |"),
        "SCROTUM":          ("SNOMED", "20233005",   "| Scrotum |"),
        "SELLA":            ("SNOMED", "42575006",   "| Sella turcica |"),
        "SEMVESICLE":       ("SNOMED", "64739004",   "| Seminal vesicle |"),
        "SESAMOID":         ("SNOMED", "58742003",   "| Sesamoid bones of foot |"),
        "SHOULDER":         ("SNOMED", "16982005",   "| Shoulder |"),
        "SIGMOID":          ("SNOMED", "60184004",   "| Sigmoid colon |"),
        "SKULL":            ("SNOMED", "89546000",   "| Skull |"),
        "SMALLINTESTINE":   ("SNOMED", "30315005",   "| Small intestine |"),
        "SPINALCORD":       ("SNOMED", "2748008",    "| Spinal cord |"),
        "SPINE":            ("SNOMED", "421060004",  "| Spine |"),
        "SPLEEN":           ("SNOMED", "78961009",   "| Spleen |"),
        "SPLENICA":         ("SNOMED", "22083002",   "| Splenic artery |"),
        "SPLENICV":         ("SNOMED", "35819009",   "| Splenic vein |"),
        "SCJOINT":          ("SNOMED", "7844006",    "| Sternoclavicular joint |"),
        "STERNUM":          ("SNOMED", "56873002",   "| Sternum |"),
        "STOMACH":          ("SNOMED", "69695003",   "| Stomach |"),
        "SUBCLAVIANA":      ("SNOMED", "36765005",   "| Subclavian artery |"),
        "SUBCLAVIANV":      ("SNOMED", "9454009",    "| Subclavian vein |"),
        "SUBCOSTAL":        ("SNOMED", "19695001",   "| Subcostal |"),
        #                   ("SNOMED", "5713008",    "| Submandibular area |"),
        "SUBMANDIBULAR":    ("SNOMED", "54019009",   "| Submandibular gland |"),
        #                   ("SNOMED", "170887008",  "| Submental |"),
        #                   ("SNOMED", "5076001",    "| Subxiphoid |"),
        "SFA":              ("SNOMED", "181349008",  "| Superficial femoral artery |"),
        "SFV":              ("SNOMED", "397364003",  "| Superficial femoral vein |"),
        #                   ("SNOMED", "15672000",   "| Superficial temporal artery |"),
        "LSUPPULMONARYV":   ("SNOMED", "43863001",   "| Superior left pulmonary vein |"),
        "SMA":              ("SNOMED", "42258001",   "| Superior mesenteric artery |"),
        "RSUPPULMONARYV":   ("SNOMED", "8629005",    "| Superior right pulmonary vein |"),
        "SUPTHYROIDA":      ("SNOMED", "72021004",   "| Superior thyroid artery |"),
        "SVC":              ("SNOMED", "48345005",   "| Superior vena cava |"),
        "SUPRACLAVICULAR":  ("SNOMED", "77621008",   "| Supraclavicular region of neck |"),
        "SUPRAPUBIC":       ("SNOMED", "11708003",   "| Suprapubic region |"),
        #                   ("SNOMED", "26493002",   "| Suprasternal notch |"),
        #                   ("SNOMED", "128589000",  "| Systemic collateral artery to lung |"),
        #                   ("SNOMED", "128568009",  "| Systemic venous atrium |"),
        #                   ("SNOMED", "27949001",   "| Tarsal joint |"),
        "TMJ":              ("SNOMED", "53620006",   "| Temporomandibular joint |"),
        "TESTIS":           ("SNOMED", "40689003",   "| Testis |"),
        "THALAMUS":         ("SNOMED", "42695009",   "| Thalamus |"),
        "THIGH":            ("SNOMED", "68367000",   "| Thigh |"),
        "3RDVENTRICLE":     ("SNOMED", "49841001",   "| Third ventricle |"),
        "THORACICAORTA":    ("SNOMED", "113262008",  "| Thoracic aorta |"),
        "TSPINE":           ("SNOMED", "122495006",  "| Thoracic spine |"),
        "TLSPINE":          ("SNOMED", "1217256009", "| Thoraco-lumbar spine |"),
        "THORAX":           ("SNOMED", "43799004",   "| Thorax |"),
        "THUMB":            ("SNOMED", "76505004",   "| Thumb |"),
        "THYMUS":           ("SNOMED", "9875009",    "| Thymus |"),
        "THYROID":          ("SNOMED", "69748006",   "| Thyroid |"),
        "TIBIA":            ("SNOMED", "12611008",   "| Tibia |"),
        "TIBIAFIBULA":      ("SNOMED", "110536004",  "| Tibia and fibula |"),
        "TOE":              ("SNOMED", "29707007",   "| Toe |"),
        "TONGUE":           ("SNOMED", "21974007",   "| Tongue |"),
        "TRACHEA":          ("SNOMED", "44567001",   "| Trachea |"),
        "TRACHEABRONCHUS":  ("SNOMED", "110726009",  "| Trachea and bronchus |"),
        "TRANSVERSECOLON":  ("SNOMED", "485005",     "| Transverse colon |"),
        #                   ("SNOMED", "61959006",   "| Truncus arteriosus communis |"),
        #                   ("SNOMED", "57850000",   "| Truncus coeliacus |"),
        "ULNA":             ("SNOMED", "23416004",   "| Ulna |"),
        "ULNARA":           ("SNOMED", "44984001",   "| Ulnar artery |"),
        "UMBILICALA":       ("SNOMED", "50536004",   "| Umbilical artery |"),
        "UMBILICAL":        ("SNOMED", "90290004",   "| Umbilical region |"),
        "UMBILICALV":       ("SNOMED", "284639000",  "| Umbilical vein |"),
        "UPPERARM":         ("SNOMED", "40983000",   "| Upper arm |"),
        #                   ("SNOMED", "77831004",   "| Upper inner quadrant of breast |"),
        "UPPERLIMB":        ("SNOMED", "53120007",   "| Upper limb |"),
        #                   ("SNOMED", "76365002",   "| Upper outer quadrant of breast |"),
        "UPRURINARYTRACT":  ("SNOMED", "431491007",  "| Upper urinary tract |"),
        "URETER":           ("SNOMED", "87953007",   "| Ureter |"),
        "URETHRA":          ("SNOMED", "13648007",   "| Urethra |"),
        "UTERUS":           ("SNOMED", "35039007",   "| Uterus |"),
        #                   ("SNOMED", "110639002",  "| Uterus and fallopian tubes |"),
        "VAGINA":           ("SNOMED", "76784001",   "| Vagina |"),
        #                   ("SNOMED", "118375008",  "| Vascular graft |"),
        "VEIN":             ("SNOMED", "29092000",   "| Vein |"),
        #                   ("SNOMED", "34340008",   "| Venous network |"),
        #                   ("SNOMED", "21814001",   "| Ventricle |"),
        "VERTEBRALA":       ("SNOMED", "85234005",   "| Vertebral artery |"),
        #                   ("SNOMED", "110517009",  "| Vertebral column and cranium |"),
        "VULVA":            ("SNOMED", "45292006",   "| Vulva |"),
        "WRIST":            ("SNOMED", "74670003",   "| Wrist joint |"),
        "ZYGOMA":           ("SNOMED", "13881006",   "| Zygoma |")
    }    


    #
    # Physical Quantities / Imaging Metric
    #

    # A dictionary with known physical quantities in DCM code and related description and the related SPHN UCUM units with the description
    # Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_7180.html Table CID 7180. Abstract Multi-dimensional Image Model Component Semantic
    # Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4033.html Table CID 4033. MR Proton Spectroscopy Metabolite
    # Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_7270.html Table CID 7270. MR Diffusion Component Semantic
    # Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_7271.html Table CID 7271. MR Diffusion Anisotropy Index
    # Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_7272.html Table CID 7272. MR Diffusion Model Parameter
    # Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_7277.html Table CID 7277. Diffusion Rate Area Over Time Unit
    # Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4107.html Table CID 4107. Tracer Kinetic Model Parameter
    # Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4108.html Table CID 4108. Perfusion Model Parameter
    # Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4109.html Table CID 4109. Model-Independent Dynamic Contrast Analysis Parameter
    # Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_10070.html Table CID 10070. Radiation Dose Type
    # Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_10071.html Table CID 10071. Radiation Dose Unit
    # Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_217.html Table CID 217. Visual Explanation
    physical_quantities_dcm_codes_and_ucum_units_dict: ClassVar[ReadOnly[dict[tuple[str, str], tuple[str, str, str]]]] = {
        ("DCM", "113063"): ("| T1 |",                                                        "ms",               "ms"),                      # [Table CID 7180] Related to MRI, T1 relaxation time
        ("DCM", "113065"): ("| T2 |",                                                        "ms",               "ms"),                      # [Table CID 7180] Related to MRI, T2 relaxation time
        ("DCM", "113064"): ("| T2* |",                                                       "ms",               "ms"),                      # [Table CID 7180] Related to MRI, T2* relaxation time
        ("DCM", "113058"): ("| Proton Density |",                                            "",                 ""),                        # [Table CID 7180] Related to MRI, Proton Density
        ("DCM", "110800"): ("| Spin Tagging Perfusion MR Signal Intensity |",                "",                 ""),                        # [Table CID 7180] Related to MRI, Spin Tagging Perfusion MR Signal Intensity
        ("DCM", "113070"): ("| Velocity encoded |",                                          "",                 ""),                        # [Table CID 7180] Related to MRI, Velocity encoded
        ("DCM", "113067"): ("| Temperature encoded |",                                       "",                 ""),                        # [Table CID 7180] Related to MRI, Temperature encoded
        ("DCM", "110801"): ("| Contrast Agent Angio MR Signal Intensity |",                  "",                 ""),                        # [Table CID 7180] Related to MRI, Contrast Agent Angio MR Signal Intensity
        ("DCM", "110802"): ("| Time Of Flight Angio MR Signal Intensity |",                  "",                 ""),                        # [Table CID 7180] Related to MRI, Time Of Flight Angio MR Signal Intensity
        ("DCM", "110803"): ("| Proton Density Weighted MR Signal Intensity |",               "",                 ""),                        # [Table CID 7180] Related to MRI, Proton Density Weighted MR Signal Intensity
        ("DCM", "110804"): ("| T1 Weighted MR Signal Intensity |",                           "",                 ""),                        # [Table CID 7180] Related to MRI, T1 Weighted MR Signal Intensity
        ("DCM", "110805"): ("| T2 Weighted MR Signal Intensity |",                           "",                 ""),                        # [Table CID 7180] Related to MRI, T2 Weighted MR Signal Intensity
        ("DCM", "110806"): ("| T2* Weighted MR Signal Intensity |",                          "",                 ""),                        # [Table CID 7180] Related to MRI, T2* Weighted MR Signal Intensity
        ("DCM", "110807"): ("| Field Map MR Signal Intensity |",                             "",                 ""),                        # [Table CID 7180] Related to MRI, Field Map MR Signal Intensity
        ("DCM", "110816"): ("| T1 Weighted Dynamic Contrast Enhanced MR Signal Intensity |", "",                 ""),                        # [Table CID 7180] Related to MRI, T1 Weighted Dynamic Contrast Enhanced MR Signal Intensity
        ("DCM", "110817"): ("| T2 Weighted Dynamic Contrast Enhanced MR Signal Intensity |", "",                 ""),                        # [Table CID 7180] Related to MRI, T2 Weighted Dynamic Contrast Enhanced MR Signal Intensity
        ("DCM", "110818"): ("| T2* Weighted Dynamic Contrast Enhanced MR Signal Intensity |","",                 ""),                        # [Table CID 7180] Related to MRI, T2* Weighted Dynamic Contrast Enhanced MR Signal Intensity
        ("DCM", "110819"): ("| Blood Oxygenation Level |",                                   "",                 ""),                        # [Table CID 7180] Related to MRI, Blood Oxygenation Level (Bold Signal)
        ("DCM", "110820"): ("| Nuclear Medicine Projection Activity |",                      "",                 ""),                        # [Table CID 7180] Related to Nuclear Medicine, Nuclear Medicine Projection Activity
        ("DCM", "110821"): ("| Nuclear Medicine Tomographic Activity |",                     "",                 ""),                        # [Table CID 7180] Related to Nuclear Medicine, Nuclear Medicine Tomographic Activity
        ("DCM", "110822"): ("| Spatial Displacement X Component |",                          "",                 ""),                        # [Table CID 7180] Related to MRI, Spatial Displacement X Component
        ("DCM", "110823"): ("| Spatial Displacement Y Component |",                          "",                 ""),                        # [Table CID 7180] Related to MRI, Spatial Displacement Y Component
        ("DCM", "110824"): ("| Spatial Displacement Z Component |",                          "",                 ""),                        # [Table CID 7180] Related to MRI, Spatial Displacement Z Component
        ("DCM", "110825"): ("| Hemodynamic Resistance |",                                    "",                 ""),                        # [Table CID 7180] Related to MRI, Hemodynamic Resistance
        ("DCM", "110826"): ("| Indexed Hemodynamic Resistance |",                            "",                 ""),                        # [Table CID 7180] Related to MRI, Indexed Hemodynamic Resistance
        ("DCM", "112031"): ("| Attenuation Coefficient |",                                   "sblhnsfapoUsbr",   "[hnsf'U]"),                # [Table CID 7180] Attenuation Coefficient, "Hounsfield unit"
        ("DCM", "110827"): ("| Tissue Velocity |",                                           "",                 ""),                        # [Table CID 7180] Related to Ultrasound, Tissue Velocity 
        ("DCM", "110828"): ("| Flow Velocity |",                                             "",                 ""),                        # [Table CID 7180] Related to Ultrasound, Flow Velocity
        ("DCM", "110829"): ("| Flow Variance |",                                             "",                 ""),                        # [Table CID 7180] Related to Ultrasound, Flow Variance   
        ("DCM", "110830"): ("| Elasticity |",                                                "",                 ""),                        # [Table CID 7180] Related to Ultrasound, Elasticity
        ("DCM", "110831"): ("| Perfusion |",                                                 "",                 ""),                        # [Table CID 7180] Related to Ultrasound, Perfusion
        ("DCM", "110832"): ("| Speed of sound |",                                            "",                 ""),                        # [Table CID 7180] Related to Ultrasound, Speed of sound
        ("DCM", "110833"): ("| Ultrasound Attenuation |",                                    "",                 ""),                        # [Table CID 7180] Related to Ultrasound, Ultrasound Attenuation
        ("DCM", "113068"): ("| Student's T-test |",                                          "",                 ""),                        # [Table CID 7180] Related to statistical analysis, Student's T-test
        ("DCM", "113071"): ("| Z-score |",                                                   "",                 ""),                        # [Table CID 7180] Related to statistical analysis, Z-score
        ("DCM", "113057"): ("| R-Coefficient |",                                             "",                 ""),                        # [Table CID 7180] Related to statistical analysis, R-Coefficient
        ("DCM", "126220"): ("| R2-Coefficient |",                                            "",                 ""),                        # [Table CID 7180] Related to statistical analysis, R2-Coefficient
        ("DCM", "126221"): ("| Chi-square |",                                                "",                 ""),                        # [Table CID 7180] Related to statistical analysis, Chi-square
        ("DCM", "126222"): ("| D-W |",                                                       "",                 ""),                        # [Table CID 7180] Related to statistical analysis, Durbin-Watson
        ("DCM", "126223"): ("| AIC |",                                                       "",                 ""),                        # [Table CID 7180] Related to statistical analysis, Akaike Information Criterion
        ("DCM", "126224"): ("| BIC |",                                                       "",                 ""),                        # [Table CID 7180] Related to statistical analysis, Bayesian Information Criterion
        ("DCM", "110834"): ("| RGB R Component |",                                           "",                 ""),                        # [Table CID 7180] Related to color images, RGB R Component
        ("DCM", "110835"): ("| RGB G Component |",                                           "",                 ""),                        # [Table CID 7180] Related to color images, RGB G Component
        ("DCM", "110836"): ("| RGB B Component |",                                           "",                 ""),                        # [Table CID 7180] Related to color images, RGB B Component
        ("DCM", "110837"): ("| YBR FULL Y Component |",                                      "",                 ""),                        # [Table CID 7180] Related to color images, YBR FULL Y Component
        ("DCM", "110838"): ("| YBR FULL CB Component |",                                     "",                 ""),                        # [Table CID 7180] Related to color images, YBR FULL CB Component
        ("DCM", "110839"): ("| YBR FULL CR Component |",                                     "",                 ""),                        # [Table CID 7180] Related to color images, YBR FULL CR Component
        ("DCM", "110840"): ("| YBR PARTIAL Y Component |",                                   "",                 ""),                        # [Table CID 7180] Related to color images, YBR PARTIAL Y Component
        ("DCM", "110841"): ("| YBR PARTIAL CB Component |",                                  "",                 ""),                        # [Table CID 7180] Related to color images, YBR PARTIAL CB Component
        ("DCM", "110842"): ("| YBR PARTIAL CR Component |",                                  "",                 ""),                        # [Table CID 7180] Related to color images, YBR PARTIAL CR Component
        ("DCM", "110843"): ("| YBR ICT Y Component |",                                       "",                 ""),                        # [Table CID 7180] Related to color images, YBR ICT Y Component
        ("DCM", "110844"): ("| YBR ICT CB Component |",                                      "",                 ""),                        # [Table CID 7180] Related to color images, YBR ICT CB Component 
        ("DCM", "110845"): ("| YBR ICT CR Component |",                                      "",                 ""),                        # [Table CID 7180] Related to color images, YBR ICT CR Component
        ("DCM", "110846"): ("| YBR RCT Y Component |",                                       "",                 ""),                        # [Table CID 7180] Related to color images, YBR RCT Y Component
        ("DCM", "110847"): ("| YBR RCT CB Component |",                                      "",                 ""),                        # [Table CID 7180] Related to color images, YBR RCT CB Component
        ("DCM", "110848"): ("| YBR RCT CR Component |",                                      "",                 ""),                        # [Table CID 7180] Related to color images, YBR RCT CR Component
        ("DCM", "110849"): ("| Echogenicity |",                                              "",                 ""),                        # [Table CID 7180] Related to Ultrasound, Echogenicity
        ("DCM", "110850"): ("| X-Ray Attenuation |",                                         "",                 ""),                        # [Table CID 7180] Related to X-Ray, X-Ray Attenuation        
        ("DCM", "110852"): ("| MR signal intensity |",                                       "",                 ""),                        # [Table CID 7180] Related to MRI, MR signal intensity
        ("DCM", "110853"): ("| Binary Segmentation |",                                       "",                 ""),                        # [Table CID 7180] Related to image segmentation, Binary Segmentation
        ("DCM", "110854"): ("| Fractional Probabilistic Segmentation |",                     "",                 ""),                        # [Table CID 7180] Related to image segmentation, Fractional Probabilistic Segmentation
        ("DCM", "110855"): ("| Fractional Occupancy Segmentation |",                         "",                 ""),                        # [Table CID 7180] Related to image segmentation, Fractional Occupancy Segmentation
        ("DCM", "126393"): ("| R1 |",                                                        "cblnbcbrperms",    "/ms"),                     # [Table CID 7180] Related to MRI, R1 (inverse of T1)                       # "{#}/ms" is the sphn ucum variant
        ("DCM", "126394"): ("| R2 |",                                                        "cblnbcbrperms",    "/ms"),                     # [Table CID 7180] Related to MRI, R2 (inverse of T2)                       # "{#}/ms" is the sphn ucum variant
        ("DCM", "126395"): ("| R2* |",                                                       "cblnbcbrperms",    "/ms"),                     # [Table CID 7180] Related to MRI, R2* (inverse of T2*)                     # "{#}/ms" is the sphn ucum variant
        ("DCM", "113098"): ("| Magnetization Transfer Ratio |",                              "clbratiocrb",      "{ratio}"),                 # [Table CID 7180] Related to MRI, Magnetization Transfer Ratio
        ("DCM", "126396"): ("| Magnetic Susceptibility |",                                   "clbratiocrb",      "{ratio}"),                 # [Table CID 7180] Related to MRI, Magnetic Susceptibility
        ("DCM", "126400"): ("| Standardized Uptake Value |",                                 "",                 ""),                        # [Table CID 7180] Related to PET, Standardized Uptake Value
        ("DCM", "126401"): ("| SUVbw |",                                                     "gpermL",           "g/ml{SUVbw}"),             # [Table CID 7180] Related to PET, Standardized Uptake Value normalized by body weight                                          # ToDo: Edwin: Ask to add to SPHN UCUM: g/ml{SUVbw}
        ("DCM", "126402"): ("| SUVlbm |",                                                    "gpermL",           "g/ml{SUVlbm}"),            # [Table CID 7180] Related to PET, Standardized Uptake Value normalized by lean body mass (James)                               # ToDo: Edwin: Ask to add to SPHN UCUM: g/ml{SUVlbm}
        ("DCM", "126406"): ("| SUVlbm(James128) |",                                          "gpermL",           "g/ml{SUVlbm(James128)}"),  # [Table CID 7180] Related to PET, Standardized Uptake Value normalized by lean body mass (James, 1984 formula, 128 multiplier) # ToDo: Edwin: Ask to add to SPHN UCUM: g/ml{SUVlbm(James128)}
        ("DCM", "126405"): ("| SUVlbm(Janma) |",                                             "gpermL",           "g/ml{SUVlbm(Janma)}"),     # [Table CID 7180] Related to PET, Standardized Uptake Value normalized by lean body mass (Janma)                               # ToDo: Edwin: Ask to add to SPHN UCUM: g/ml{SUVlbm(Janma)}
        ("DCM", "126403"): ("| SUVbsa |",                                                    "cm2permL",         "cm2/ml{SUVbsa}"),          # [Table CID 7180] Related to PET, Standardized Uptake Value normalized by body surface area                                    # ToDo: Edwin: Ask to add to SPHN UCUM: cm2/ml{SUVbsa}
        ("DCM", "126404"): ("| SUVibw |",                                                    "gpermL",           "g/ml{SUVibw}"),            # [Table CID 7180] Related to PET, Standardized Uptake Value normalized by ideal body weight                                    # ToDo: Edwin: Ask to add to SPHN UCUM: g/ml{SUVibw}
        ("DCM", "129100"): ("| Fat fraction |",                                              "",                 ""),                        # [Table CID 7180] 
        ("DCM", "129101"): ("| Water/fat in phase |",                                        "",                 ""),                        # [Table CID 7180] Related to MRI, Water/fat in phase
        ("DCM", "129102"): ("| Water/fat out of phase |",                                    "",                 ""),                        # [Table CID 7180] Related to MRI, Water/fat out of phase
        ("DCM", "113054"): ("| Negative enhancement integral |",                             "",                 ""),                        # [Table CID 7180] 
        ("DCM", "113059"): ("| Signal change |",                                             "",                 ""),                        # [Table CID 7180] 
        ("DCM", "113060"): ("| Signal to noise |",                                           "",                 ""),                        # [Table CID 7180] 
        ("DCM", "113066"): ("| Time course of signal |",                                     "",                 ""),                        # [Table CID 7180] 
        ("DCM", "129103"): ("| Water fraction |",                                            "",                 ""),                        # [Table CID 7180] 
        ("DCM", "130086"): ("| Relative Linear Stopping Power |",                            "clbratiocrb",      "{ratio}"),                 # Related to CT, Relative Linear Stopping Power
        ("DCM", "113094"): ("| Creatine and Choline |",                                      "sblppmsbr",        "ppm"),                     # [Table CID 4033] MR Proton Spectroscopy Metabolite
        ("DCM", "113095"): ("| Lipid and Lactate |",                                         "sblppmsbr",        "ppm"),                     # [Table CID 4033] MR Proton Spectroscopy Metabolite
        ("DCM", "113080"): ("| Glutamate and glutamine |",                                   "sblppmsbr",        "ppm"),                     # [Table CID 4033] MR Proton Spectroscopy Metabolite
        ("DCM", "113081"): ("| Choline/Creatine Ratio |",                                    "sblppmsbr",        "ppm"),                     # [Table CID 4033] MR Proton Spectroscopy Metabolite
        ("DCM", "113082"): ("| N-acetylaspartate/Creatine Ratio |",                          "sblppmsbr",        "ppm"),                     # [Table CID 4033] MR Proton Spectroscopy Metabolite
        ("DCM", "113083"): ("| N-acetylaspartate/Choline Ratio |",                           "sblppmsbr",        "ppm"),                     # [Table CID 4033] MR Proton Spectroscopy Metabolite
        ("DCM", "113096"): ("| Creatine+Choline/Citrate Ratio |",                            "sblppmsbr",        "ppm"),                     # [Table CID 4033] MR Proton Spectroscopy Metabolite
        ("DCM", "113043"): ("| Diffusion weighted |",                                        "",                 ""),                        # [Table CID 7270] MR Diffusion Component Semantic
        ("DCM", "113044"): ("| Diffusion tensor |",                                          "",                 ""),                        # Old?
        ("DCM", "110810"): ("| Volumetric Diffusion Dxx Component |",                        "",                 ""),                        # [Table CID 7270] MR Diffusion Component Semantic
        ("DCM", "110811"): ("| Volumetric Diffusion Dxy Component |",                        "",                 ""),                        # [Table CID 7270] MR Diffusion Component Semantic
        ("DCM", "110812"): ("| Volumetric Diffusion Dxz Component |",                        "",                 ""),                        # [Table CID 7270] MR Diffusion Component Semantic
        ("DCM", "110813"): ("| Volumetric Diffusion Dyy Component |",                        "",                 ""),                        # [Table CID 7270] MR Diffusion Component Semantic
        ("DCM", "110814"): ("| Volumetric Diffusion Dyz Component |",                        "",                 ""),                        # [Table CID 7270] MR Diffusion Component Semantic
        ("DCM", "110815"): ("| Volumetric Diffusion Dzz Component |",                        "",                 ""),                        # [Table CID 7270] MR Diffusion Component Semantic
        ("DCM", "110808"): ("| Fractional Anisotropy |",                                     "",                 ""),                        # [Table CID 7271] MR Diffusion Anisotropy Index
        ("DCM", "110809"): ("| Relative Anisotropy |",                                       "cblratiocbr",      "{ratio}"),                 # [Table CID 7271] MR Diffusion Anisotropy Index
        ("DCM", "113288"): ("| Volume Ratio |",                                              "",                 ""),                        # [Table CID 7271] MR Diffusion Anisotropy Index
        ("DCM", "113041"): ("| Apparent Diffusion Coefficient |",                            "mm2pers",          "mm2/s"),                   # [Table CID 7272] MR Diffusion Model Parameter                             # "mm2/s" or "um2/ms" or "um2/s" or "10-6.mm2/s"
        ("DCM", "113289"): ("| Diffusion Coefficient |",                                     "mm2pers",          "mm2/s"),                   # [Table CID 7272] MR Diffusion Model Parameter                             # "mm2/s" or "um2/ms" or "um2/s" or "10-6.mm2/s"
        ("DCM", "113290"): ("| Mono-exponential Apparent Diffusion Coefficient |",           "mm2pers",          "mm2/s"),                   # [Table CID 7272] MR Diffusion Model Parameter                             # "mm2/s" or "um2/ms" or "um2/s" or "10-6.mm2/s"
        ("DCM", "113291"): ("| Slow Diffusion Coefficient |",                                "",                 ""),                        # [Table CID 7272] MR Diffusion Model Parameter
        ("DCM", "113292"): ("| Fast Diffusion Coefficient |",                                "mm2pers",          "mm2/s"),                   # [Table CID 7272] MR Diffusion Model Parameter                             # "mm2/s" or "um2/ms" or "um2/s" or "10-6.mm2/s"
        ("DCM", "113293"): ("| Fast Diffusion Coefficient Fraction |",                       "",                 ""),                        # [Table CID 7272] MR Diffusion Model Parameter
        ("DCM", "113294"): ("| Kurtosis Diffusion Coefficient |",                            "mm2pers",          "mm2/s"),                   # [Table CID 7272] MR Diffusion Model Parameter                             # "mm2/s" or "um2/ms" or "um2/s" or "10-6.mm2/s"
        ("DCM", "113295"): ("| Gamma Distribution Scale Parameter |",                        "",                 ""),                        # [Table CID 7272] MR Diffusion Model Parameter
        ("DCM", "113296"): ("| Gamma Distribution Shape Parameter |",                        "",                 ""),                        # [Table CID 7272] MR Diffusion Model Parameter
        ("DCM", "113297"): ("| Gamma Distribution Mode |",                                   "",                 ""),                        # [Table CID 7272] MR Diffusion Model Parameter
        ("DCM", "113298"): ("| Distributed Diffusion Coefficient |",                         "mm2pers",          "mm2/s"),                   # [Table CID 7272] MR Diffusion Model Parameter                             # "mm2/s" or "um2/ms" or "um2/s" or "10-6.mm2/s"
        ("DCM", "113299"): ("| Anomalous Exponent Parameter |",                              "",                 ""),                        # [Table CID 7272] MR Diffusion Model Parameter
        ("DCM", "126312"): ("| Ktrans |",                                                    "cblnbcbrpermin",   "/min"),                    # [Table CID 4107] Tracer Kinetic Model Parameter                           # "{#}/min" is the sphn ucum variant
        ("DCM", "126313"): ("| kep |",                                                       "cblnbcbrpermin",   "/min"),                    # [Table CID 4107] Tracer Kinetic Model Parameter                           # "{#}/min" is the sphn ucum variant
        ("DCM", "126314"): ("| ve |",                                                        "cblratiocbr",      "{ratio}"),                 # [Table CID 4107] Tracer Kinetic Model Parameter
        ("DCM", "126330"): ("| tau_m |",                                                     "s",                "s"),                       # [Table CID 4107] Tracer Kinetic Model Parameter
        ("DCM", "126331"): ("| vp |",                                                        "cblratiocbr",      "{ratio}"),                 # [Table CID 4107] Tracer Kinetic Model Parameter
        ("DCM", "126390"): ("| Absolute Regional Blood Flow |",                              "",                 "ml/(100.ml)/min"),         # [Table CID 4108] Perfusion Model Parameter                                # ToDo: Edwin: Ask to add to SPHN UCUM: "ml/(100.ml)/min" and "ml/(100.g)/min"
        ("DCM", "126391"): ("| Absolute Regional Blood Volume |",                            "",                 "ml/(100.ml)"),             # [Table CID 4108] Perfusion Model Parameter                                # ToDo: Edwin: Ask to add to SPHN UCUM: "ml/(100.ml)" and "ml/(100.g)"
        ("DCM", "126397"): ("| Relative Regional Blood Flow |",                              "cblratiocbr",      "{ratio}"),                 # [Table CID 4108] Perfusion Model Parameter
        ("DCM", "126398"): ("| Relative Regional Blood Volume |",                            "cblratiocbr",      "{ratio}"),                 # [Table CID 4108] Perfusion Model Parameter
        ("DCM", "113052"): ("| Mean Transit Time |",                                         "s",                "s"),                       # [Table CID 4108] Perfusion Model Parameter
        ("DCM", "113069"): ("| Time To Peak |",                                              "s",                "s"),                       # [Table CID 4108] Perfusion Model Parameter
        ("DCM", "126392"): ("| Oxygen Extraction Fraction |",                                "",                 ""),                        # [Table CID 4108] Perfusion Model Parameter
        ("DCM", "113084"): ("| Tmax |",                                                      "s",                "s"),                       # [Table CID 4108] Perfusion Model Parameter
        ("DCM", "126320"): ("| IAUC |",                                                      "",                 "mmol/l.s"),                # [Table CID 4109] Model-Independent Dynamic Contrast Analysis Parameter    # ToDo: Edwin: Ask to add to SPHN UCUM: "mmol/l.s"
        ("DCM", "126321"): ("| IAUC60 |",                                                    "",                 "mmol/l.s"),                # [Table CID 4109] Model-Independent Dynamic Contrast Analysis Parameter    # ToDo: Edwin: Ask to add to SPHN UCUM: "mmol/l.s"
        ("DCM", "126322"): ("| IAUC90 |",                                                    "",                 "mmol/l.s"),                # [Table CID 4109] Model-Independent Dynamic Contrast Analysis Parameter    # ToDo: Edwin: Ask to add to SPHN UCUM: "mmol/l.s"
        ("DCM", "126323"): ("| IAUC180 |",                                                   "",                 "mmol/l.s"),                # [Table CID 4109] Model-Independent Dynamic Contrast Analysis Parameter    # ToDo: Edwin: Ask to add to SPHN UCUM: "mmol/l.s"
        ("DCM", "126324"): ("| IAUCBN |",                                                    "",                 "{normalized}"),            # [Table CID 4109] Model-Independent Dynamic Contrast Analysis Parameter    # ToDo: Edwin: Ask to add to SPHN UCUM: "{normalized}"
        ("DCM", "126325"): ("| IAUC60BN |",                                                  "",                 "{/AIF}"),                  # [Table CID 4109] Model-Independent Dynamic Contrast Analysis Parameter    # ToDo: Edwin: Ask to add to SPHN UCUM: "{/AIF}"
        ("DCM", "126326"): ("| IAUC90BN |",                                                  "",                 "{/AIF}"),                  # [Table CID 4109] Model-Independent Dynamic Contrast Analysis Parameter    # ToDo: Edwin: Ask to add to SPHN UCUM: "{/AIF}"
        ("DCM", "126327"): ("| IAUC180BN |",                                                 "",                 "{/AIF}"),                  # [Table CID 4109] Model-Independent Dynamic Contrast Analysis Parameter    # ToDo: Edwin: Ask to add to SPHN UCUM: "{/AIF}"
        ("DCM", "126370"): ("| Time of Peak Concentration |",                                "s",                "s"),                       # [Table CID 4109] Model-Independent Dynamic Contrast Analysis Parameter
        ("DCM", "126372"): ("| Time of Leading Half-Peak Concentration |",                   "s",                "s"),                       # [Table CID 4109] Model-Independent Dynamic Contrast Analysis Parameter
        ("DCM", "126371"): ("| Bolus Arrival Time |",                                        "s",                "s"),                       # [Table CID 4109] Model-Independent Dynamic Contrast Analysis Parameter
        ("DCM", "126374"): ("| Temporal Derivative Threshold |",                             "",                 ""),                        # [Table CID 4109] Model-Independent Dynamic Contrast Analysis Parameter
        ("DCM", "126375"): ("| Maximum Slope |",                                             "",                 ""),                        # [Table CID 4109] Model-Independent Dynamic Contrast Analysis Parameter
        ("DCM", "126376"): ("| Maximum Difference |",                                        "",                 ""),                        # [Table CID 4109] Model-Independent Dynamic Contrast Analysis Parameter
        ("DCM", "126377"): ("| Tracer Concentration |",                                      "mmolperL",         "mmol/l"),                  # [Table CID 4109] Model-Independent Dynamic Contrast Analysis Parameter
        ("DCM", "128513"): ("| Absorbed Dose |",                                             "Gy",               "Gy"),                      # [Table CID 10070] Radiation Dose Type                                     # DICOM: "Sv" or "Gy"
        ("DCM", "128512"): ("| Equivalent Dose |",                                           "Sv",               "Sv"),                      # [Table CID 10070] Radiation Dose Type                                     # DICOM: "Sv" or "Gy"
        ("DCM", "130402"): ("| Class activation |",                                          "",                 ""),                        # [Table CID 217] Visual Explanation
        ("DCM", "130403"): ("| Gradient-weighted class activation |",                        "",                 ""),                        # [Table CID 217] Visual Explanation
        ("DCM", "130404"): ("| Saliency |",                                                  "",                 "")                         # [Table CID 217] Visual Explanation
    }

    # A Python dictionary with known physical quantities in SNOMED-CT in DICOM
    physical_quantities_snomed_ct_codes_and_ucum_units_dict: ClassVar[ReadOnly[dict[tuple[str, str], tuple[str, str, str]]]] = {
        ("SNOMED", "425704008"): ("| Power Doppler |",                                          "",                 ""),                        # [Table CID 7180] Related to Ultrasound, Power Doppler
        ("SNOMED", "256674009"): ("| Fat |",                                                    "",                 ""),                        # [Table CID 7180] 
        ("SNOMED", "11713004"):  ("| Water |",                                                  "",                 ""),                        # [Table CID 7180] 
        ("SNOMED", "115391007"): ("| N-acetylaspartate |",                                      "sblppmsbr",        "pmm"),                     # [Table CID 4033] MR Proton Spectroscopy Metabolite
        ("SNOMED", "59351004"):  ("| Citrate |",                                                "sblppmsbr",        "ppm"),                     # [Table CID 4033] MR Proton Spectroscopy Metabolite
        ("SNOMED", "65123005"):  ("| Choline |",                                                "sblppmsbr",        "ppm"),                     # [Table CID 4033] MR Proton Spectroscopy Metabolite
        ("SNOMED", "14804005"):  ("| Creatine |",                                               "sblppmsbr",        "ppm"),                     # [Table CID 4033] MR Proton Spectroscopy Metabolite
        ("SNOMED", "83036002"):  ("| Lactate |",                                                "sblppmsbr",        "ppm"),                     # [Table CID 4033] MR Proton Spectroscopy Metabolite
        ("SNOMED", "70106000"):  ("| Lipid |",                                                  "sblppmsbr",        "ppm"),                     # [Table CID 4033] MR Proton Spectroscopy Metabolite
        ("SNOMED", "25761002"):  ("| Glutamine |",                                              "sblppmsbr",        "ppm"),                     # [Table CID 4033] MR Proton Spectroscopy Metabolite
        ("SNOMED", "10944007"):  ("| Tuarine |",                                                "sblppmsbr",        "ppm"),                     # [Table CID 4033] MR Proton Spectroscopy Metabolite
        ("SNOMED", "72164009"):  ("| Inositol |",                                               "sblppmsbr",        "ppm")                      # [Table CID 4033] MR Proton Spectroscopy Metabolite
    }

    #
    # A dictionary with known physical quantities in DCM code and related description and the related UCUM units 
    #

    # https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_7181.html Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_3500.html Table CID 3500. Pressure Unit
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_3502.html Table CID 3502. Hemodynamic Resistance Unit
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_3503.html Table CID 3503. Indexed Hemodynamic Resistance Unit
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_7460.html Table CID 7460. Linear Measurement Unit
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_7461.html Table CID 7461. Area Measurement Unit
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_7462.html Table CID 7462. Volume Measurement Unit
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_84.html Table CID 84. PET Unit
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_85.html Table CID 85. SUV Unit
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_7277.html Table CID 7277. Diffusion Rate Area Over Time Unit
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_10071.html Table CID 10071. Radiation Dose Unit

    # UCUM 1 no units                                                                             Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM {ratio} ratio                                                                          Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM [hnsf'U] Hounsfield Unit                                                               Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM {counts} Counts                                                                        Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM {counts}/s Counts per second                                                           Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM [arb'U] arbitrary unit                                                                 Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM ppm ppm                                                                                Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM cm/s centimeter/second                                                                 Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM mm/s millimeter/second                                                                 Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM dB decibel                                                                             Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM Cel degrees Celsius                                                                    Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM ml/min milliliter per minute                                                           Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM ml/s milliliter per second                                                             Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM ms millisecond                                                                         Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM s second                                                                               Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM Hz Hertz                                                                               Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM mT milliTesla                                                                          Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM {Particles}/[100]g{Tissue} number particles per 100 gram of tissue                     Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM s/mm2 second per square millimeter                                                     Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM ml/[100]g/min milliliter per 100 gram per minute                                       Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM ml/[100]ml milliliter per 100 milliliter                                               Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM mmol/kg{WetWeight} millimoles per kg wet weight                                        Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM /min /min                                                                              Table CID 7181. Abstract Multi-dimensional Image Model Component Unit
    # UCUM /s /s                                                                                  Table CID 7181. Abstract Multi-dimensional Image Model Component Unit

    # UCUM mm[Hg] mmHg                                                                            Table CID 3500. Pressure Unit
    # UCUM kPa kPa                                                                                Table CID 3500. Pressure Unit

    # UCUM [PRU] P.R.U.                                                                           Table CID 3502. Hemodynamic Resistance Unit
    # UCUM [wood'U] Wood U                                                                        Table CID 3502. Hemodynamic Resistance Unit   
    # UCUM dyn.s.cm-5 dyn.s.cm-5                                                                  Table CID 3502. Hemodynamic Resistance Unit

    # UCUM [PRU]/m2 P.R.U./m2                                                                     Table CID 3503. Indexed Hemodynamic Resistance Unit
    # UCUM [wood'U]/m2 Wood U/m2                                                                  Table CID 3503. Indexed Hemodynamic Resistance Unit
    # UCUM dyn.s.cm-5/m2 dyn.s.cm-5/m2                                                            Table CID 3503. Indexed Hemodynamic Resistance Unit

    # UCUM cm centimeter                                                                          Table CID 7460. Linear Measurement Unit
    # UCUM mm millimeter                                                                          Table CID 7460. Linear Measurement Unit
    # UCUM um micrometer                                                                          Table CID 7460. Linear Measurement Unit

    # UCUM cm2 square centimeter                                                                  Table CID 7461. Area Measurement Unit
    # UCUM mm2 square millimeter                                                                  Table CID 7461. Area Measurement Unit
    # UCUM um2 square micrometer                                                                  Table CID 7461. Area Measurement Unit

    # UCUM dm3 cubic decimeter                                                                    Table CID 7462. Volume Measurement Unit
    # UCUM cm3 cubic centimeter                                                                   Table CID 7462. Volume Measurement Unit
    # UCUM mm3 cubic millimeter                                                                   Table CID 7462. Volume Measurement Unit
    # UCUM um3 cubic micrometer                                                                   Table CID 7462. Volume Measurement Unit

    # UCUM g/ml{SUVbw} Standardized Uptake Value body weight                                      Table CID 85. SUV Unit
    # UCUM g/ml{SUVlbm} Standardized Uptake Value lean body mass (James)                          Table CID 85. SUV Unit
    # UCUM g/ml{SUVlbm(James128)} Standardized Uptake Value lean body mass (James 128 multiplier) Table CID 85. SUV Unit
    # UCUM g/ml{SUVlbm(Janma)} Standardized Uptake Value lean body mass (Janma)                   Table CID 85. SUV Unit
    # UCUM cm2/ml{SUVbsa} Standardized Uptake Value body surface area                             Table CID 85. SUV Unit
    # UCUM g/ml{SUVibw} Standardized Uptake Value ideal body weight                               Table CID 85. SUV Unit

    # UCUM {counts} Counts                                                                        Table CID 84. PET Unit
    # UCUM {counts}/s Counts per second                                                           Table CID 84. PET Unit
    # UCUM {propcounts} Proportional to counts                                                    Table CID 84. PET Unit
    # UCUM {propcounts}/s Proportional to counts per second                                       Table CID 84. PET Unit
    # UCUM cm2 Centimeter**2                                                                      Table CID 84. PET Unit
    # UCUM cm2/ml Centimeter**2/milliliter                                                        Table CID 84. PET Unit
    # UCUM % Percent                                                                              Table CID 84. PET Unit
    # UCUM Bq/ml Becquerels/milliliter                                                            Table CID 84. PET Unit
    # UCUM mg/min/ml Milligrams/minute/milliliter                                                 Table CID 84. PET Unit
    # UCUM umol/min/ml Micromole/minute/milliliter                                                Table CID 84. PET Unit
    # UCUM ml/min/g Milliliter/minute/gram                                                        Table CID 84. PET Unit
    # UCUM ml/g Milliliter/gram                                                                   Table CID 84. PET Unit
    # UCUM /cm /Centimeter                                                                        Table CID 84. PET Unit
    # UCUM umol/ml Micromole/milliliter                                                           Table CID 84. PET Unit

    # UCUM mm2/s mm2/s                                                                            Table CID 7277. Diffusion Rate Area Over Time Unit
    # UCUM um2/ms um2/ms                                                                          Table CID 7277. Diffusion Rate Area Over Time Unit
    # UCUM um2/s um2/s                                                                            Table CID 7277. Diffusion Rate Area Over Time Unit
    # UCUM 10-6.mm2/s 10-6.mm2/s                                                                  Table CID 7277. Diffusion Rate Area Over Time Unit

    # UCUM Gy Gy                                                                                  Table CID 10071. Radiation Dose Unit
    # UCUM Sv Sv                                                                                  Table CID 10071. Radiation Dose Unit


    # #######################################################################################
    #
    # Contrast Agents and Co.
    #
    # #######################################################################################

    # A dictionary mapping:
    #   - DICOM Table CID 12 "Imaging Contrast Agent" codes and 
    #   - DICOM Table CID 13. "Imaging Contrast Agent Ingredient" codes
    # to the corresponding SPHN contrast agent active ingredient SNOMED CT codes:
    # Key: Tuple with:
    #   - coding scheme designator (e.g.: "SCT")
    #   - code value (e.g.: "90745007") 
    #   - human-readable description (e.g.:"Bunamiodyl")
    # Value: Tuple with:
    #   - coding scheme designator (e.g.: "SNOMED")
    #   - code value (e.g.: "90745007") 
    #   - human-readable description (e.g.:"| Bunamiodyl (substance) |")
    # Note(s): 
    #   - The "coding scheme designator" in DICOM Table CID 12 has "SCT" for SNOMED CT codes.
    #   - DICOM prefers the use of SNOMED CT Product concepts when available, SPHN allows only SNOMED CT Substance concepts.
    #   - All values in this mapping should have a valid SNOMED CT code entry.
    #   - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_12.html
    #   - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_cid_13.html
    dicom_contrast_agents_coded_2_sphn_snomed_coded: ClassVar[Mapping[tuple[str, str], tuple[str, str, str]]] = {
        # CT/X-ray (32)
        ## Iodine-based (28)
        ("SCT",    "90745007"): ("SNOMED",   "90745007", "| Bunamiodyl (substance) |"),                                              # Bunamiodyl
        ("SCT",    "12335007"): ("SNOMED",  "396020008", "| Amidotrizoate (substance) |"),                                           # Diatrizoate                          # DICOM code is a product concept
        ("SCT",    "12801003"): ("SNOMED",   "12801003", "| Iodamide meglumine (substance) |"),                                      # Iodamide meglumine
        ("SCT",    "73212002"): ("SNOMED",  "398939009", "| Iodipamide (substance) |"),                                              # Iodipamide                           # DICOM code is a product concept
        ("SCT",   "353962003"): ("SNOMED",  "395750001", "| Iodixanol (substance) |"),                                               # Iodixanol                            # DICOM code is a product concept
        ("SCT",    "86584005"): ("SNOMED",   "86584005", "| Iodoalphionic acid (substance) |"),                                      # Iodoalphionic acid
        ("SCT",    "74554008"): ("SNOMED",   "74554008", "| Iodophthalein (substance) |"),                                           # Iodophthalein
        ("SCT",    "40710000"): ("SNOMED",   "40710000", "| Iodopyracet (substance) |"),                                             # Iodopyracet
        ("SCT",   "109218004"): ("SNOMED",  "395751002", "| Iohexol (substance) |"),                                                 # Iohexol                              # DICOM code is a product concept
        ("SCT",   "109219007"): ("SNOMED",  "395754005", "| Iopamidol (substance) |"),                                               # Iopamidol                            # DICOM code is a product concept
        ("SCT",    "76155001"): ("SNOMED",  "412227008", "| Iopanoic acid (substance) |"),                                           # Iopanoic acid                        # DICOM code is a product concept
        ("SCT",    "23053002"): ("SNOMED",   "23053002", "| Iophenoxic acid (substance) |"),                                         # Iophenoxic acid
        ("SCT",   "353903006"): ("SNOMED",  "395756007", "| Iopromide (substance) |"),                                               # Iopromide                            # DICOM code is a product concept
        ("SCT",   "353912008"): ("SNOMED",  "395981002", "| Iothalamate (substance) |"),                                             # Iothalamate                          # DICOM code is a product concept
        ("SCT",   "109222009"): ("SNOMED",  "395759000", "| Ioversol (substance) |"),                                                # Ioversol                             # DICOM code is a product concept
        ("SCT",   "412228003"): ("SNOMED",  "412228003", "| Ioxaglate meglumine (substance) |"),                                     # Ioxaglate                            # DICOM meaning says Ioxaglate but code is the meglumine salt; base is 395760005 | Ioxaglate (substance) |
        ("SCT",   "409484007"): ("SNOMED",  "409485008", "| Ioxilan (substance) |"),                                                 # Ioxilan                              # DICOM code is a product concept
        ("SCT",    "87445005"): ("SNOMED",   "87445005", "| Ipodate (substance) |"),                                                 # Ipodate
        ("SCT",    "47192000"): ("SNOMED",   "47192000", "| Meglumine amidotrizoate (substance) |"),                                 # Meglumine diatrizoate
        ("SCT",    "69783005"): ("SNOMED",   "69783005", "| Iodipamide meglumine (substance) |"),                                    # Meglumine iodipamide
        ("SCT",    "90733003"): ("SNOMED",   "90733003", "| Metrizamide (substance) |"),                                             # Metrizamide
        ("SCT",   "354094002"): ("SNOMED",  "395792006", "| Metrizoate (substance) |"),                                              # Metrizoate                           # DICOM code is a product concept
        ("SCT",   "111158001"): ("SNOMED",  "111158001", "| Propyliodone (substance) |"),                                            # Propyliodone
        ("SCT",    "32836007"): ("SNOMED",   "32836007", "| Sodium acetrizoate (substance) |"),                                      # Sodium acetrizoate
        ("SCT",    "83423008"): ("SNOMED",   "83423008", "| Sodium diprotrizoate (substance) |"),                                    # Sodium diprotrizoate
        ("SCT",      "925002"): ("SNOMED",     "925002", "| Sodium iodipamide (substance) |"),                                       # Sodium iodipamide
        ("SCT",    "38344006"): ("SNOMED",   "38344006", "| Sodium iodomethamate (substance) |"),                                    # Sodium iodomethamate
        ("SCT",   "109212003"): ("SNOMED",  "109212003", "| Tyropanoate sodium (substance) |"),                                      # Sodium tyropanoate
        ## Oil-based (3)
        ("SCT",    "62442005"): ("SNOMED",   "62442005", "| Chloriodized oil (substance) |"),                                        # Chloriodized oil
        ("SCT",    "89595000"): ("SNOMED",   "89595000", "| Iodized oil (substance) |"),                                             # Iodized oil
        ("SCT",    "28121005"): ("SNOMED",   "28121005", "| Iophendylate (substance) |"),                                            # Iophendylate
        ## Barium-based (1)
        ("SCT",    "25419009"): ("SNOMED",  "396014007", "| Barium sulfate (substance) |"),                                          # Barium Sulfate                       # DICOM code is a product concept

        # MRI (10)
        ## Gadolinium-based (9)
        ("SCT",   "792865009"): ("SNOMED",  "414308003", "| Meglumine gadobenate (substance) |"),                                    # Gadobenate dimeglumine               # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        ("SCT",   "407976008"): ("SNOMED",  "418351005", "| Gadobutrol (substance) |"),                                              # Gadobutrol                           # DICOM code is a product concept
        ("SCT",   "354088005"): ("SNOMED",  "396067007", "| Gadodiamide (substance) |"),                                             # Gadodiamide                          # DICOM code is a product concept
        ("SCT",   "770982005"): ("SNOMED",  "420466007", "| Gadofosveset (substance) |"),                                            # Gadofosveset                         # DICOM code is a product concept
        ("SCT",   "109216000"): ("SNOMED",  "109216000", "| Gadopentetate dimeglumine (substance) |"),                               # Gadopentetate dimeglumine            # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        ("SCT",   "712714000"): ("SNOMED",  "712714000", "| Gadoterate meglumine (substance) |"),                                    # Gadoterate meglumine
        ("SCT",   "353946009"): ("SNOMED",  "420600009", "| Gadoteridol (substance) |"),                                             # Gadoteridol                          # DICOM code is a product concept
        ("SCT",   "409477004"): ("SNOMED",  "409476008", "| Gadoversetamide (substance) |"),                                         # Gadoversetamide                      # DICOM code is a product concept
        ("SCT",   "440223009"): ("SNOMED",  "440223009", "| Gadoxetate disodium (substance) |"),                                     # Gadoxetate disodium
        ## Manganese-based (1)
        ("RXNORM",   "236987"): ("SNOMED",  "410872002", "| Mangafodipir trisodium (substance) |"),                                  # Mangafodipir trisodium               # RxNorm to SNOMED

        # Active elements and groups (5)
        ### Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        ("SCT",    "44588005"): ("SNOMED",   "44588005", "| Iodine (substance) |"),                                                  # Iodine                               # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code   
        ("SCT",    "39290007"): ("SNOMED",   "39290007", "| Barium (substance) |"),                                                  # Barium                               # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        ("SCT",   "768763008"): ("SNOMED",   "58281002", "| Gadolinium (substance) |"),                                              # Gadolinium                           # DICOM code is a product concept # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        ("SCT",    "58281002"): ("SNOMED",   "58281002", "| Gadolinium (substance) |"),                                              # Gadolinium                           # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        ("SCT",     "3829006"): ("SNOMED",    "3829006", "| Iron (substance) |"),                                                    # Iron                                 # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        ("SCT",    "15158005"): ("SNOMED",   "15158005", "| Air (substance) |"),                                                     # Air                                  # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        ("SCT",    "31811003"): ("SNOMED",   "31811003", "| Carbon dioxide (substance) |"),                                          # Carbon Dioxide                       # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        ("SCT",    "83598005"): ("SNOMED",   "83598005", "| Xenon (substance) |"),                                                   # Xenon                                # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        ("SCT",    "24099007"): ("SNOMED",   "24099007", "| Oxygen (substance) |"),                                                  # Oxygen                               # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        ("SCT",    "11713004"): ("SNOMED",   "11713004", "| Water (substance) |"),                                                   # Water                                # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        ### Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, not included in SPHN yet
        ####("SCT",    "87869004"): ("SNOMED",   "87869004", "| Manganese (substance) |"),                                              # Manganese                            # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, not included in SPHN yet

        # General types (5)
        ("RADLEX", "RID11585"): ("SNOMED", "1340006004", "| Ionic iodinated radiographic imaging contrast media (substance) |"),     # Ionic iodinated contrast agent       # RadLex to SNOMED
        ("RADLEX", "RID38696"): ("SNOMED", "1340009006", "| Non-ionic iodinated radiographic imaging contrast media (substance) |"), # Non-ionic iodinated contrast agent   # RadLex to SNOMED
        ("SCT",   "419098001"): ("SNOMED",  "419098001", "| Radiographic imaging contrast media (substance) |"),                     # Radiopaque medium
        ("SCT",   "385420005"): ("SNOMED",  "385420005", "| Contrast media (substance) |"),                                          # Contrast agent                       # The parent concept itself
        ### Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        ("SCT",    "43538006"): ("SNOMED",   "43538006", "| Non radiopaque medium (substance) |"),                                   # Non radiopaque medium                # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
    }


    # A dictionary mapping contrast agent trade names to their manufacturer and ingredients:
    # Key: Contrast agent trade name (e.g.: "Amipaque")
    # Value: Tuple with:
    #   - the manufacturer (e.g.: "GE")
    #   - a list of active ingredient's name (e.g.: ["Metrizamide"])
    #   - a list of inactive ingredient's name (only populated in a few cases) (e.g.: ["Galactose"])
    # Note: 
    #   - All trade names should have a manufacturer and at least one active ingredient.
    #   - The active ingredient should be listed in:
    #      - contrast_agent_active_ingredient_name_2_snomed_code or
    #      - contrast_agent_active_element_names_2_snomed_code
    #   - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_12.html
    #   - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_cid_13.html
    contrast_agent_trade_name_2_manufacturer_and_ingredient_name: ClassVar[Mapping[str, tuple[str, list[str], list[str]]]] = {

        # CT/X-ray (62)
        ## Iodine-based (46)
        "Amipaque":                 ("GE",                      ["Metrizamide"],                                    []),
        "Angiovist":                ("Bayer",                   ["Diatrizoate Meglumine", "Diatrizoate Sodium"],    []),
        "Bilivist":                 ("Bayer",                   ["Ipodate Sodium"],                                 []),
        "Cardiografin":             ("Bracco",                  ["Diatrizoate Meglumine"],                          []),
        "Cholographin":             ("Bracco",                  ["Iodipamide Meglumine"],                           []),
        "Cholographin Meglumine":   ("Bracco",                  ["Iodipamide Meglumine"],                           []),
        "Cholographin Sodium":      ("Bracco",                  ["Iodipamide Sodium"],                              []),
        "Conray":                   ("Guerbet",                 ["Iothalamate Meglumine"],                          []),
        "Cysto-Conray":             ("Guerbet",                 ["Iothalamate Meglumine"],                          []),
        "Cystografin":              ("Bracco",                  ["Diatrizoate Meglumine"],                          []),
        "Dionosil":                 ("GSK",                     ["Propyliodone"],                                   []),
        "Gastrografin":             ("Bracco",                  ["Diatrizoate Meglumine", "Diatrizoate Sodium"],    []),
        "Gastrovist":               ("Bayer",                   ["Diatrizoate Meglumine", "Diatrizoate Sodium"],    []),
        "Hexabrix":                 ("Guerbet",                 ["Ioxaglate Meglumine", "Ioxaglate Sodium"],        []),
        "Hypaque":                  ("GE",                      ["Diatrizoate Sodium"],                             []),
        "Hypaque Meglumine":        ("GE",                      ["Diatrizoate Meglumine"],                          []),
        "Imagenil":                 ("Guerbet",                 ["Ioxilan"],                                        []),
        "Imagopaque":               ("GE",                      ["Iopentol"],                                       []),
        "Imeron":                   ("Bracco",                  ["Iomeprol"],                                       []),
        "Iomeron":                  ("Bracco",                  ["Iomeprol"],                                       []),
        "Iopamiro":                 ("Bracco",                  ["Iopamidol"],                                      []),
        "Isopaque":                 ("GE",                      ["Metrizoate"],                                     []),
        "Isovist":                  ("Bayer",                   ["Iotrolan"],                                       []),
        "Isovue":                   ("Bracco",                  ["Iopamidol"],                                      []),
        "MD":                       ("Guerbet",                 ["Diatrizoate Meglumine", "Diatrizoate Sodium"],    []),
        "MD Gastroview":            ("Guerbet",                 ["Diatrizoate Meglumine", "Diatrizoate Sodium"],    []),
        "Niopam":                   ("Bracco",                  ["Iopamidol"],                                      []),
        "Omnipaque":                ("GE",                      ["Iohexol"],                                        []),
        "Optiray":                  ("Guerbet",                 ["Ioversol"],                                       []),
        "Oragrafin":                ("Bracco",                  ["Ipodate Sodium", "Ipodate Calcium"],              []),
        "Oxilan":                   ("Guerbet",                 ["Ioxilan"],                                        []),
        "Reno":                     ("Bracco",                  ["Diatrizoate Meglumine"],                          []),
        "Reno-Dip":                 ("Bracco",                  ["Diatrizoate Meglumine"],                          []),
        "Renografin":               ("Bracco",                  ["Diatrizoate Meglumine", "Diatrizoate Sodium"],    []),
        "Renovist":                 ("Bracco",                  ["Diatrizoate Meglumine", "Diatrizoate Sodium"],    []),
        "Renovue":                  ("Bracco",                  ["Iodamide Meglumine"],                             []),
        "Salpix":                   ("Johnson & Johnson",       ["Acetrizoate Sodium"],                             ["Povidone"]),
        "Sinografin":               ("Bracco",                  ["Diatrizoate Meglumine", "Iodipamide Meglumine"],  []),
        "Solutrast":                ("Bracco",                  ["Iopamidol"],                                      []),
        "Telebrix":                 ("Guerbet",                 ["Ioxitalamate Meglumine", "Ioxitalamate Sodium"],  []),
        "Telepaque":                ("GE",                      ["Iopanoic Acid"],                                  []),
        "Ultravist":                ("Bayer",                   ["Iopromide"],                                      []),
        "Urovist":                  ("Bayer",                   ["Diatrizoate Meglumine", "Diatrizoate Sodium"],    []),
        "Vascoray":                 ("Guerbet",                 ["Iothalamate Meglumine", "Iothalamate Sodium"],    []),
        "Visipaque":                ("GE",                      ["Iodixanol"],                                      []),
        "Xenetix":                  ("Guerbet",                 ["Iobitridol"],                                     []),
        ## Barium-based (12)
        "Baro-Cat":                 ("Guerbet",                 ["Barium Sulfate"],                                 []),
        "Cheetah":                  ("Guerbet",                 ["Barium Sulfate"],                                 []),
        "E-Z-Cat":                  ("Bracco",                  ["Barium Sulfate"],                                 []),
        "E-Z-HD":                   ("Bracco",                  ["Barium Sulfate"],                                 []),
        "E-Z-PAQUE":                ("Bracco",                  ["Barium Sulfate"],                                 []),
        "Liquid POLIBAR PLUS":      ("Bracco",                  ["Barium Sulfate"],                                 []),
        "Readi-Cat":                ("Bracco",                  ["Barium Sulfate"],                                 []),
        "Readi-Cat 2":              ("Bracco",                  ["Barium Sulfate"],                                 []),
        "Readi-Cat 2 SMOOTHIE":     ("Bracco",                  ["Barium Sulfate"],                                 []),
        "Tagitol":                  ("Bracco",                  ["Barium Sulfate"],                                 []),
        "Varibar":                  ("Bracco",                  ["Barium Sulfate"],                                 []),
        "VoLumen":                  ("Bracco",                  ["Barium Sulfate"],                                 []),
        ## Oil-based (4)
        "Ethiodol":                 ("Guerbet",                 ["Ethiodized Oil"],                                 []),
        "Lipiodol":                 ("Guerbet",                 ["Ethiodized Oil"],                                 []),
        "Myodil":                   ("GSK",                     ["Iophendylate"],                                   []),
        "Pantopaque":               ("Eastman Kodak",           ["Iophendylate"],                                   []),

        # MRI (20)
        ## Gadolinium-based (15)
        "Ablavar":                  ("Lantheus",                ["Gadofosveset Trisodium"],                         []),
        "Clariscan":                ("GE",                      ["Gadoterate Meglumine"],                           []),
        "Dotarem":                  ("Guerbet",                 ["Gadoterate Meglumine"],                           []),
        "Elucirem":                 ("Guerbet",                 ["Gadopiclenol"],                                   []),
        "Eovist":                   ("Bayer",                   ["Gadoxetate Disodium"],                            []),
        "Gadavist":                 ("Bayer",                   ["Gadobutrol"],                                     []),
        "Gadovist":                 ("Bayer",                   ["Gadobutrol"],                                     []),
        "Omniscan":                 ("GE",                      ["Gadodiamide"],                                    []),
        "Optimark":                 ("Guerbet",                 ["Gadoversetamide"],                                []),
        "Primovist":                ("Bayer",                   ["Gadoxetate Disodium"],                            []),
        "ProHance":                 ("Bracco",                  ["Gadoteridol"],                                    []),
        "Vasovist":                 ("Lantheus",                ["Gadofosveset Trisodium"],                         []),
        "Vueway":                   ("Bracco",                  ["Gadopiclenol"],                                   []),
        ### Not subclass of SNOMED-CT Contrast media (substance)), but included in SPHN Contrast Agent Active Ingredient code
        "Magnevist":                ("Bayer",                   ["Gadopentetate Dimeglumine"],                      []),                                 # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Multihance":               ("Bracco",                  ["Gadobenate Dimeglumine"],                         []),                                 # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        ## Iron-based (4)
        "Endorem":                  ("Guerbet",                 ["Ferumoxides"],                                    []),
        "Feridex":                  ("Covis",                   ["Ferumoxides"],                                    []),
        "Resovist":                 ("Neo Critical Care Pharma",["Ferucarbotran"],                                  []),
        ### Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, not included in SPHN yet
        "Feraheme":                 ("Covis",                   ["Ferumoxytol"],                                    []),                                # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, not included in SPHN yet

        ## Manganese-based (1)
        "Teslascan":                ("IC Targets",              ["Mangafodipir Trisodium"],                         []),

        # Ultrasound (7)
        ## Microbubble-based (7)
        "Definity":                 ("Lantheus",                ["Perflutren"],                                     []),
        "Lumason":                  ("Bracco",                  ["Sulfur Hexafluoride Lipid Microspheres"],         []),
        "Luminity":                 ("Lantheus",                ["Perflutren"],                                     []),
        "Optison":                  ("GE",                      ["Perflutren"],                                     []),
        "SonoVue":                  ("Bracco",                  ["Sulfur Hexafluoride Lipid Microspheres"],         []),
        ### Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, not included in SPHN yet
        "Sonazoid":                 ("GE",                      ["Perflubutane"],                                   []),                                # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, not included in SPHN yet
        ### Not subclass of SNOMED-CT Contrast media (substance)), but included in SPHN Contrast Agent Active Ingredient code
        "Levovist":                 ("Bayer",                   ["Air"],                                            ["Galactose", "Palmitic Acid"]),    # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
    }


    # A dictionary mapping contrast agent active ingredient names to the corresponding SNOMED CT code:
    # Key: Contrast agent trade name (e.g.: "Acetrizoate Sodium")
    # Value: Tuple with:
    #   - coding scheme designator (e.g.: "SNOMED")
    #   - code value (e.g.: "32836007") 
    #   - human-readable description (e.g.:"| Sodium acetrizoate (substance) |"))
    # Note(s): 
    #   - The active ingredients from the above contrast_agent_trade_name_2_manufacturer_and_ingredient_name mapping
    #     should have a corresponding entry in this mapping. An exception is "Air" which is in the 
    #     contrast_agent_active_element_names_2_snomed_code mapping
    #   - The active ingredients listed in DICOM Table CID 12 "Imaging Contrast Agent" 
    #     should have a corresponding entry in this mapping. Exceptions are active elements which are covered in the 
    #     contrast_agent_active_element_names_2_snomed_code mapping.
    #   - The "coding scheme designator" in DICOM Table CID 12 has "SCT" for SNOMED CT codes.
    #   - All active ingredients should have a valid SNOMED CT code entry.
    #   - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_12.html    
    #   - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_cid_13.html
    contrast_agent_active_ingredient_name_2_snomed_code: ClassVar[Mapping[str, tuple[str, str, str]]] = {
        
        # CT/X-ray
        ## Iodine-based (29)
        "Acetrizoate Sodium":                     ("SNOMED",   "32836007", "| Sodium acetrizoate (substance) |"),
        "Diatrizoate":                            ("SNOMED",  "396020008", "| Amidotrizoate (substance) |"),
        "Diatrizoate Meglumine":                  ("SNOMED",   "47192000", "| Meglumine amidotrizoate (substance) |"),
        "Diatrizoate Sodium":                     ("SNOMED",  "395875009", "| Sodium amidotrizoate (substance) |"),
        "Iobitridol":                             ("SNOMED",  "704384003", "| Iobitridol (substance) |"),
        "Iodamide Meglumine":                     ("SNOMED",   "12801003", "| Iodamide meglumine (substance) |"),
        "Iodipamide Meglumine":                   ("SNOMED",   "69783005", "| Iodipamide meglumine (substance) |"),
        "Iodipamide Sodium":                      ("SNOMED",     "925002", "| Sodium iodipamide (substance) |"),
        "Iodixanol":                              ("SNOMED",  "395750001", "| Iodixanol (substance) |"),
        "Iohexol":                                ("SNOMED",  "395751002", "| Iohexol (substance) |"),
        "Iomeprol":                               ("SNOMED",  "395753004", "| Iomeprol (substance) |"),
        "Iopamidol":                              ("SNOMED",  "395754005", "| Iopamidol (substance) |"),
        "Iopanoic Acid":                          ("SNOMED",  "412227008", "| Iopanoic acid (substance) |"),
        "Iopentol":                               ("SNOMED", "1340015006", "| Iopentol (substance) |"),
        "Iopromide":                              ("SNOMED",  "395756007", "| Iopromide (substance) |"),
        "Iothalamate Meglumine":                  ("SNOMED",  "395757003", "| Iothalamate meglumine (substance) |"),
        "Iothalamate Sodium":                     ("SNOMED",  "395878006", "| Sodium iothalamate (substance) |"),
        "Iotrolan":                               ("SNOMED",  "395758008", "| Iotrolan (substance) |"),
        "Ioversol":                               ("SNOMED",  "395759000", "| Ioversol (substance) |"),
        "Ioxaglate Meglumine":                    ("SNOMED",  "412228003", "| Ioxaglate meglumine (substance) |"),
        "Ioxaglate Sodium":                       ("SNOMED",  "412230001", "| Ioxaglate sodium (substance) |"),
        "Ioxilan":                                ("SNOMED",  "409485008", "| Ioxilan (substance) |"),
        "Ioxitalamate Meglumine":                 ("SNOMED",  "712698009", "| Ioxitalamate meglumine (substance) |"),
        "Ioxitalamate Sodium":                    ("SNOMED",  "765359003", "| Ioxitalamate sodium (substance) |"),
        "Ipodate Calcium":                        ("SNOMED",  "396003009", "| Calcium iopodate (substance) |"),
        "Ipodate Sodium":                         ("SNOMED",  "395877001", "| Sodium iopodate (substance) |"),
        "Metrizamide":                            ("SNOMED",   "90733003", "| Metrizamide (substance) |"),
        "Metrizoate":                             ("SNOMED",  "395792006", "| Metrizoate (substance) |"),
        "Propyliodone":                           ("SNOMED",  "111158001", "| Propyliodone (substance) |"),
        ## Barium-based (1)
        "Barium Sulfate":                         ("SNOMED",  "396014007", "| Barium sulfate (substance) |"),
        ## Oil-based (2)
        "Ethiodized Oil":                         ("SNOMED",  "109224005", "| Ethiodized oil (substance) |"),
        "Iophendylate":                           ("SNOMED",   "28121005", "| Iophendylate (substance) |"),

        # MRI
        ## Gadolinium-based (12)
        "Gadobenic Acid":                         ("SNOMED",  "710810006", "| Gadobenic acid (substance) |"),
        "Gadobutrol":                             ("SNOMED",  "418351005", "| Gadobutrol (substance) |"),
        "Gadodiamide":                            ("SNOMED",  "396067007", "| Gadodiamide (substance) |"),
        "Gadofosveset Trisodium":                 ("SNOMED",  "425080008", "| Gadofosveset trisodium (substance) |"),
        "Gadopentetic Acid":                      ("SNOMED",  "710811005", "| Gadopentetic acid (substance) |"),
        "Gadopiclenol":                           ("SNOMED",  "1363068006", "| Gadopiclenol (substance) |"),
        "Gadoterate Meglumine":                   ("SNOMED",  "712714000", "| Gadoterate meglumine (substance) |"),
        "Gadoteridol":                            ("SNOMED",  "420600009", "| Gadoteridol (substance) |"),
        "Gadoversetamide":                        ("SNOMED",  "409476008", "| Gadoversetamide (substance) |"),
        "Gadoxetate Disodium":                    ("SNOMED",  "440223009", "| Gadoxetate disodium (substance) |"),
        ### Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Gadopentetate Dimeglumine":              ("SNOMED",  "109216000", "| Gadopentetate dimeglumine (substance) |"),            # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Gadobenate Dimeglumine":                 ("SNOMED",  "414308003", "| Meglumine gadobenate (substance) |"),                 # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        ## Iron-based (3)
        "Ferucarbotran":                          ("SNOMED",  "421091005", "| Ferucarbotran (substance) |"),
        "Ferumoxides":                            ("SNOMED",  "412390001", "| Ferumoxide (substance) |"),
        ### Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, not included in SPHN yet
        "Ferumoxytol":                            ("SNOMED",  "442951001", "| Ferumoxytol (substance) |"),                          # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, not included in SPHN yet
        ## Manganese-based (1)
        "Mangafodipir Trisodium":                 ("SNOMED",  "410872002", "| Mangafodipir trisodium (substance) |"),
        
        # Ultrasound
        ## Microbubble-based (3)
        "Perflutren":                             ("SNOMED",  "409292001", "| Perflutren (substance) |"),
        "Sulfur Hexafluoride Lipid Microspheres": ("SNOMED",  "724034007", "| Sulfur hexafluoride lipid microsphere (substance) |"),
        ### Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, not included in SPHN yet
        "Perflubutane":                           ("SNOMED",  "419765001", "| Perfluorobutane (substance) |"),                      # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, not included in SPHN yet
        
        # Additional names from DICOM CID 12
        "Iodipamide":                             ("SNOMED",  "398939009", "| Iodipamide (substance) |"),
        "Iothalamate":                            ("SNOMED",  "395981002", "| Iothalamate (substance) |"),
        "Ioxaglate":                              ("SNOMED",  "395760005", "| Ioxaglate (substance) |"),
        "Ipodate":                                ("SNOMED",   "87445005", "| Ipodate (substance) |"),
        "Bunamiodyl":                             ("SNOMED",   "90745007", "| Bunamiodyl (substance) |"),
        "Chloriodized Oil":                       ("SNOMED",   "62442005", "| Chloriodized oil (substance) |"),
        "Iodized Oil":                            ("SNOMED",   "89595000", "| Iodized oil (substance) |"),
        "Iodoalphionic Acid":                     ("SNOMED",   "86584005", "| Iodoalphionic acid (substance) |"),
        "Iodophthalein":                          ("SNOMED",   "74554008", "| Iodophthalein (substance) |"),
        "Iodopyracet":                            ("SNOMED",   "40710000", "| Iodopyracet (substance) |"),
        "Iophenoxic Acid":                        ("SNOMED",   "23053002", "| Iophenoxic acid (substance) |"),
        "Sodium Diprotrizoate":                   ("SNOMED",   "83423008", "| Sodium diprotrizoate (substance) |"),
        "Sodium Iodomethamate":                   ("SNOMED",   "38344006", "| Sodium iodomethamate (substance) |"),
        "Sodium Tyropanoate":                     ("SNOMED",  "109212003", "| Tyropanoate sodium (substance) |"),
        ## General types (5+1)
        "Ionic Iodinated Contrast Agent":         ("SNOMED", "1340006004", "| Ionic iodinated radiographic imaging contrast media (substance) |"),
        "Non-ionic Iodinated Contrast Agent":     ("SNOMED", "1340009006", "| Non-ionic iodinated radiographic imaging contrast media (substance) |"),
        "Radiopaque Medium":                      ("SNOMED",  "419098001", "| Radiographic imaging contrast media (substance) |"),
        "Contrast Agent":                         ("SNOMED",  "385420005", "| Contrast media (substance) |"),                       # The parent concept itself
        ### Additional by Edwin
        "Iodinated Contrast Agent":               ("SNOMED",  "426722004", "| Iodinated contrast media (substance) |"),
        ### Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Non Radiopaque Medium":                  ("SNOMED",   "43538006", "| Non radiopaque medium (substance) |"),                # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
    }

    # A dictionary mapping contrast agent active element (group) names to the corresponding SNOMED CT code:
    # Key: Contrast agent active element (group) name (e.g.: "Iodine")
    # Value: Tuple with:
    #   - coding scheme designator (e.g.: "SNOMED")
    #   - code value (e.g.: "44588005") 
    #   - human-readable description (e.g.:"| Iodine (substance) |"))
    # Note(s): 
    #   - The keys in this mapping should be title-cased versions of the active element names.
    #   - The active ingredients from the above contrast_agent_trade_name_2_manufacturer_and_ingredient_name mapping
    #     can have a corresponding entry in this mapping. For example "Air".
    #   - The active elements listed in DICOM Table CID 12 "Imaging Contrast Agent" 
    #     should have a corresponding entry in this mapping. For example "Air", "Water", "Oxygen".
    #   - The "coding scheme designator" in DICOM Table CID 12 has "SCT" for SNOMED CT codes.
    #   - All active ingredients should have a valid SNOMED CT code entry.
    #   - Manganese is included as an active element, but it is not a subclass of SNOMED-CT contrast agent and not listed in SPHN.
    #   - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_12.html
    #   - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_cid_13.html
    contrast_agent_active_element_names_2_snomed_code: ClassVar[Mapping[str, tuple[str, str, str]]] = {
        ### Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Iodine":           ("SNOMED", "44588005", "| Iodine (substance) |"),           # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Barium":           ("SNOMED", "39290007", "| Barium (substance) |"),           # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Gadolinium":       ("SNOMED", "58281002", "| Gadolinium (substance) |"),       # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Iron":             ("SNOMED",  "3829006", "| Iron (substance) |"),             # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Air":              ("SNOMED", "15158005", "| Air (substance) |"),              # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Carbon Dioxide":   ("SNOMED", "31811003", "| Carbon dioxide (substance) |"),   # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Xenon":            ("SNOMED", "83598005", "| Xenon (substance) |"),            # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Oxygen":           ("SNOMED", "24099007", "| Oxygen (substance) |"),           # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Water":            ("SNOMED", "11713004", "| Water (substance) |"),            # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        ### Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, not included in SPHN yet
        ####"Manganese":       ("SNOMED", "87869004", "| Manganese (substance) |"),        # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, not included in SPHN yet
    }


    # Dictionary mapping:
    #   - contrast agent trade names, 
    #   - active ingredient names,
    #   - active element (group) names,
    # to regex patterns
    # Key: Contrast agent trade names or active ingredient names or active element (group) names (e.g.: "Amipaque")
    # Value: Regex pattern to match the name in the DICOM string (e.g.: r"\b(ami(paque|pak|paqe|paq))")
    # Note(s):
    #  - Crucial: The regex patterns should match the full contrast agent name and avoid partial matches within others.
    #   - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_cid_12.html
    #   - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_cid_13.html
    contrast_agent_names_2_patterns: ClassVar[Mapping[str, str]] = {
        
        # ##################################################
        # Trade Names
        # ##################################################
    
        # CT/X-ray (62)
        ## Iodine-based (46)
        "Amipaque":                 r"\b(ami(?:paque|pak|paqe|paq))",
        "Angiovist":                r"\b(angiovist)",
        "Bilivist":                 r"\b(bilivist)",
        "Cardiografin":             r"\b(cardiografin)",
        "Cholographin":             r"\b(cholographin)(?![-\s]?(?:meglumine|sodium))",
        "Cholographin Meglumine":   r"\b(cholographin[-\s]?meglumine)",
        "Cholographin Sodium":      r"\b(cholographin[-\s]?sodium)",
        "Conray":                   r"\b(?<!cysto-)(?<!cysto )(?<!cysto)(conray)",
        "Cysto-Conray":             r"\b(cysto[-\s]?conray)",
        "Cystografin":              r"\b(cystografin)",
        "Dionosil":                 r"\b(dionosil)",
        "Gastrografin":             r"\b(gastrografin)",
        "Gastrovist":               r"\b(gastrovist)",
        "Hexabrix":                 r"\b(hexabrix)",
        "Hypaque":                  r"\b(hy(?:paque|pak|paqe|paq))(?![a-z]*[-\s]?meglumine)",        
        "Hypaque Meglumine":        r"\b(hy(?:paque|pak|paqe|paq)[-\s]?meglumine)",
        "Imagenil":                 r"\b(imagenil)",
        "Imagopaque":               r"\b(imago(?:paque|pak|paqe|paq))",
        "Imeron":                   r"\b(imeron)",
        "Iomeron":                  r"\b(iomeron)",
        "Iopamiro":                 r"\b(iopamiro)",
        "Isopaque":                 r"\b(iso(?:paque|pak|paqe|paq))",
        "Isovist":                  r"\b(isovist)",
        "Isovue":                   r"\b(isovue)",
        "MD":                       r"\b(md)(?![-\s]?(?:gastroview))", # r"\b(md)(?=[-\s]?(?:50|60|76)r?\b)" 
        "MD Gastroview":            r"\b((?:md[-\s]?)?gastroview)",
        "Niopam":                   r"\b(niopam)",
        "Omnipaque":                r"\b(omni(?:paque|pak|paqe|paq))",
        "Optiray":                  r"\b(optiray)",
        "Oragrafin":                r"\b(oragrafin)",
        "Oxilan":                   r"\b(oxilan)",
        "Reno":                     r"\b(reno)(?![-\s]?(?:dip|grafin|vist|vue))",
        "Reno-Dip":                 r"\b(reno[-\s]?dip)",
        "Renografin":               r"\b(renografin)",
        "Renovist":                 r"\b(renovist)",
        "Renovue":                  r"\b(renovue)",
        "Salpix":                   r"\b(salpix)",
        "Sinografin":               r"\b(sinografin)",
        "Solutrast":                r"\b(solutrast)",
        "Telebrix":                 r"\b(telebrix)",
        "Telepaque":                r"\b(tele(?:paque|pak|paqe|paq))",
        "Ultravist":                r"\b(ultravist)",
        "Urovist":                  r"\b(urovist)",
        "Vascoray":                 r"\b(vascoray)",
        "Visipaque":                r"\b(visi(?:paque|pak|paqe|paq))",
        "Xenetix":                  r"\b(xenetix)",
        ## Barium-based (12)
        "Baro-Cat":                 r"\b(baro[-\s]?cat)",
        "Cheetah":                  r"\b(cheetah)",
        "E-Z-Cat":                  r"\b(e[-\s]?z[-\s]?cat)",
        "E-Z-HD":                   r"\b(e[-\s]?z[-\s]?hd)",
        "E-Z-PAQUE":                r"\b(e[-\s]?z[-\s]?(?:paque|pak|paqe|paq))",
        "Liquid POLIBAR PLUS":      r"\b(liquid[-\s]?polibar[-\s]?plus)",
        "Readi-Cat":                r"\b((?:readi|rdi|redi)[-\s]?cat)(?![-\s]?2)",
        "Readi-Cat 2":              r"\b((?:readi|rdi|redi)[-\s]?cat[-\s]?2)(?![-\s]?smoothie)",
        "Readi-Cat 2 SMOOTHIE":     r"\b((?:readi|rdi|redi)[-\s]?cat[-\s]?2[-\s]?smoothie)",
        "Tagitol":                  r"\b(tagitol)",
        "Varibar":                  r"\b(varibar)",
        "VoLumen":                  r"\b(volumen)",
        ## Oil-based (4)
        "Ethiodol":                 r"\b(ethiodol)",
        "Lipiodol":                 r"\b(lipiodol)",
        "Myodil":                   r"\b(myodil)",
        "Pantopaque":               r"\b(panto(?:paque|pak|paqe|paq))",

        # MRI (20)
        ## Gadolinium-based (15)
        "Ablavar":                  r"\b(ablavar)",
        "Clariscan":                r"\b(clariscan|clariskan)",
        "Dotarem":                  r"\b(dotarem)",
        "Elucirem":                 r"\b(elucirem)",
        "Eovist":                   r"\b(eovist)",
        "Gadavist":                 r"\b(gadavist)",
        "Gadovist":                 r"\b(gadovist)",
        "Magnevist":                r"\b(magnevist)",
        "Multihance":               r"\b(multi[-\s]?hance|multi\b(?!-)(?!\s+(?:phase|detector|slice|row|parametric|planar|focal|modal|sequence|echo)))",
        "Omniscan":                 r"\b(omniscan|omniskan)",
        "Optimark":                 r"\b(optimark)",
        "Primovist":                r"\b(primovist)",
        "ProHance":                 r"\b(prohance)",
        "Vasovist":                 r"\b(vasovist)",
        "Vueway":                   r"\b(vueway)",
        ## Iron-based (4)
        "Endorem":                  r"\b(endorem)",
        "Feraheme":                 r"\b(feraheme)",
        "Feridex":                  r"\b(feridex)",
        "Resovist":                 r"\b(resovist)",
        ## Manganese-based (1)
        "Teslascan":                r"\b(teslascan|teslaskan)",

        # Ultrasound (7)
        ## Microbubble-based (7)
        "Definity":                 r"\b(definity)",
        "Levovist":                 r"\b(levovist)",
        "Lumason":                  r"\b(lumason)",
        "Luminity":                 r"\b(luminity)",
        "Optison":                  r"\b(optison)",
        "Sonazoid":                 r"\b(sonazoid)",
        "SonoVue":                  r"\b(sonovue)",

        # ##################################################
        # Contrast Agent Active Ingredients
        # ##################################################
        
        # CT/X-ray
        ## Iodine-based (29)
        "Acetrizoate Sodium":                     r"\b(acetrizoate[-\s]?sodium|sodium[-\s]?acetrizoate)\b",
        "Diatrizoate":                            r"\b(?<!meglumine[-\s])(?<!meglumine)(?<!sodium[-\s])(?<!sodium)((?:diatrizo|amidotrizo)(?:ate|ic[-\s]?acid))\b(?![-\s]?(?:meglumine|sodium))",
        "Diatrizoate Meglumine":                  r"\b((?:diatrizoate|amidotrizoate)[-\s]?meglumine|meglumine[-\s]?(?:diatrizoate|amidotrizoate))\b",
        "Diatrizoate Sodium":                     r"\b((?:diatrizoate|amidotrizoate)[-\s]?sodium|sodium[-\s]?(?:diatrizoate|amidotrizoate))\b",
        "Iobitridol":                             r"\b(iobitridol)\b",
        "Iodamide Meglumine":                     r"\b(iodamide[-\s]?meglumine|meglumine[-\s]?iodamide)\b",
        "Iodipamide Meglumine":                   r"\b((?:iodipamide|adipiodone)[-\s]?meglumine|meglumine[-\s]?(?:iodipamide|adipiodone))\b",
        "Iodipamide Sodium":                      r"\b((?:iodipamide|adipiodone)[-\s]?sodium|sodium[-\s]?(?:iodipamide|adipiodone))\b",
        "Iodixanol":                              r"\b(iodixanol)\b",
        "Iohexol":                                r"\b(iohexol)\b",
        "Iomeprol":                               r"\b(iomeprol)\b",
        "Iopamidol":                              r"\b(iopamidol)\b",
        "Iopanoic Acid":                          r"\b(iopanoic[-\s]?acid)\b",
        "Iopentol":                               r"\b(iopentol)\b",
        "Iopromide":                              r"\b(iopromide)\b",
        "Iothalamate Meglumine":                  r"\b((?:iothalamate|iotalamate)[-\s]?meglumine|meglumine[-\s]?(?:iothalamate|iotalamate))\b",
        "Iothalamate Sodium":                     r"\b((?:iothalamate|iotalamate)[-\s]?sodium|sodium[-\s]?(?:iothalamate|iotalamate))\b",
        "Iotrolan":                               r"\b(iotrolan)\b",
        "Ioversol":                               r"\b(ioversol)\b",
        "Ioxaglate Meglumine":                    r"\b(ioxaglate[-\s]?meglumine|meglumine[-\s]?ioxaglate)\b",
        "Ioxaglate Sodium":                       r"\b(ioxaglate[-\s]?sodium|sodium[-\s]?ioxaglate)\b",
        "Ioxilan":                                r"\b(ioxilan)\b",
        "Ioxitalamate Meglumine":                 r"\b((?:ioxitalamate|ioxithalamate)[-\s]?meglumine|meglumine[-\s]?(?:ioxitalamate|ioxithalamate))\b",
        "Ioxitalamate Sodium":                    r"\b((?:ioxitalamate|ioxithalamate)[-\s]?sodium|sodium[-\s]?(?:ioxitalamate|ioxithalamate))\b",
        "Ipodate Calcium":                        r"\b((?:ipodate|iopodate)[-\s]?calcium|calcium[-\s]?(?:ipodate|iopodate))\b",
        "Ipodate Sodium":                         r"\b((?:ipodate|iopodate)[-\s]?sodium|sodium[-\s]?(?:ipodate|iopodate))\b",
        "Metrizamide":                            r"\b(metrizamide)\b",
        "Metrizoate":                             r"\b(metrizoate(?:[-\s]?(?:sodium|meglumine|calcium|magnesium))?|metrizoic[-\s]?acid)\b",
        "Propyliodone":                           r"\b(propyliodone)\b",
        ## Barium-based (1)
        "Barium Sulfate":                         r"\b(barium[-\s]?(?:sulfate|sulphate))\b",
        ## Oil-based (2)
        "Ethiodized Oil":                         r"\b(ethiodi[sz]ed[-\s]?oil|ethiodi[sz]ed[-\s]?poppyseed[-\s]?oil)\b",
        "Iophendylate":                           r"\b(iophendylate)\b",
        
        # MRI (16)
        ## Gadolinium-based (12)
        "Gadobenic Acid":                         r"\b(?<!meglumine[-\s])(?<!meglumine)(gadobenic[-\s]?acid|gadobenate)\b(?![-\s]?(?:di)?meglumine)",
        "Gadobutrol":                             r"\b(gadobutrol)\b",
        "Gadodiamide":                            r"\b(gadodiamide)\b",
        "Gadofosveset Trisodium":                 r"\b(gadofosveset(?:[-\s]?trisodium)?)\b",
        "Gadopentetic Acid":                      r"\b(?<!meglumine[-\s])(?<!meglumine)(gadopentetic[-\s]?acid|gadopentetate)\b(?![-\s]?(?:di)?meglumine)",
        "Gadopiclenol":                           r"\b(gadopiclenol)\b",
        "Gadoterate Meglumine":                   r"\b((?:gadoterate[-\s]?meglumine|meglumine[-\s]?gadoterate)|gadoteric[-\s]?acid)\b",
        "Gadoteridol":                            r"\b(gadoteridol)\b",
        "Gadoversetamide":                        r"\b(gadoversetamide)\b",
        "Gadoxetate Disodium":                    r"\b((?:gadoxetate[-\s]?disodium|disodium[-\s]?gadoxetate)|gadoxetic[-\s]?acid)\b",
        ### Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Gadopentetate Dimeglumine":              r"\b(gadopentetate[-\s]?(?:di)?meglumine|(?:di)?meglumine[-\s]?gadopentetate)\b",     # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Gadobenate Dimeglumine":                 r"\b(gadobenate[-\s]?(?:di)?meglumine|(?:di)?meglumine[-\s]?gadobenate)\b",           # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        ## Iron-based (3)
        "Ferucarbotran":                          r"\b(ferucarbotran)\b",
        "Ferumoxides":                            r"\b(ferumoxides?)\b",
        ### Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, not included in SPHN yet
        "Ferumoxytol":                            r"\b(ferumoxytol)\b",                                                                 # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, not included in SPHN yet
        ## Manganese-based (1)
        "Mangafodipir Trisodium":                 r"\b(mangafodipir(?:[-\s]?trisodium)?)\b",
        
        # Ultrasound (3)
        ## Microbubble-based (3)
        #### already included: "Air":             r"\b(air)\b",
        "Perflubutane":                           r"\b(perflubutane|perfluoro[-\s]?butane|decafluorobutane)\b",
        "Perflutren":                             r"\b(perflutren|octafluoropropane|perfluoro[-\s]?propane)\b",
        "Sulfur Hexafluoride Lipid Microspheres": r"\b((?:sulfur|sulphur)[-\s]?hexafluoride(?:[-\s]?lipid(?:[-\s]?type[-\s]?a)?[-\s]?microspheres?)?)\b",

        # ##################################################
        # Additional DICOM Table CID 12 based contrast agents:
        # ##################################################

        # CT/X-ray
        ## Iodine-based (12)
        "Bunamiodyl":                             r"\b(bunamiodyl)\b",
        "Iodipamide":                             r"\b(?<!meglumine[-\s])(?<!meglumine)(?<!sodium[-\s])(?<!sodium)(?<!calcium[-\s])(?<!calcium)(iodipamide|adipiodone)\b(?![-\s]?(?:meglumine|sodium|calcium))",
        "Iodoalphionic Acid":                     r"\b(iodoalphionic[-\s]?acid)\b",
        "Iodophthalein":                          r"\b(iodophthalein)\b",
        "Iodopyracet":                            r"\b(iodopyracet)\b",
        "Iophenoxic Acid":                        r"\b(iophenoxic[-\s]?acid)\b",
        "Iothalamate":                            r"\b(?<!meglumine[-\s])(?<!meglumine)(?<!sodium[-\s])(?<!sodium)(?<!calcium[-\s])(?<!calcium)(iothalamate|iotalamate|iothalamic[-\s]?acid|iotalamic[-\s]?acid)\b(?![-\s]?(?:meglumine|sodium|calcium))",
        "Ioxaglate":                              r"\b(?<!meglumine[-\s])(?<!meglumine)(?<!sodium[-\s])(?<!sodium)(?<!calcium[-\s])(?<!calcium)(ioxaglate|ioxaglic[-\s]?acid)\b(?![-\s]?(?:meglumine|sodium|calcium))",
        "Ipodate":                                r"\b(?<!meglumine[-\s])(?<!meglumine)(?<!sodium[-\s])(?<!sodium)(?<!calcium[-\s])(?<!calcium)(ipodate|iopodate|ipodic[-\s]?acid|iopodic[-\s]?acid)\b(?![-\s]?(?:meglumine|sodium|calcium))",
        "Sodium Diprotrizoate":                   r"\b(sodium[-\s]?diprotrizoate|diprotrizoate[-\s]?sodium)\b",
        "Sodium Iodomethamate":                   r"\b(sodium[-\s]?iodomethamate|iodomethamate[-\s]?sodium)\b",
        "Sodium Tyropanoate":                     r"\b(sodium[-\s]?tyropanoate|tyropanoate[-\s]?sodium)\b",
        ## Oil-based (2)
        "Chloriodized Oil":                       r"\b(chloriodi[sz]ed[-\s]?oil)\b",
        "Iodized Oil":                            r"\b(iodi[sz]ed[-\s]?oil)\b",

        ## General types (5+1)
        "Ionic Iodinated Contrast Agent":         r"\b(?<!non[-\s])(?<!non)(ionic[-\s]?iodinated[-\s]?contrast[-\s]?(?:agent|medium|media))\b",
        "Non-ionic Iodinated Contrast Agent":     r"\b(non[-\s]?ionic[-\s]?iodinated[-\s]?contrast[-\s]?(?:agent|medium|media))\b",
        "Radiopaque Medium":                      r"\b(?<!non[-\s])(?<!non)(radiopaque[-\s]?(?:medium|media))\b",
        "Contrast Agent":                         r"\b(?<!iodinated[-\s])(contrast[-\s]?(?:agent|medium|media))\b",                     # The parent concept itself
        ### Additional by Edwin
        "Iodinated Contrast Agent":               r"\b(?<!ionic[-\s])(?<!ionic)(iodinated[-\s]?contrast(?:[-\s]?(?:agent|medium|media))?)\b",
        ### Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Non Radiopaque Medium":                  r"\b(non[-\s]?radiopaque[-\s]?(?:medium|media))\b",                                   # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code

        # ##################################################
        # Active element(s) or functional atom(groups)
        # ##################################################
        
        ## Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Iodine":                   r"\b(iodine|i)(?![.\s]?[vme]\b)(?=\b|\d)",                                              # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Barium":                   r"\b(barium|ba)(?![-\s]?(?:sulfate|sulphate)|so4)(?=\b|\d|cl\d?\b)",                    # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Gadolinium":               r"\b(gadolinium|gd)(?=\b|\d|cl\d?\b)",                                                  # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Iron":                     r"\b(iron|fe)(?=\b|\d|cl\d?\b)",                                                        # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Air":                      r"\b(air)\b",                                                                           # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Carbon Dioxide":           r"\b(carbon[-\s]?dioxide|co2)\b",                                                       # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Xenon":                    r"\b(xenon|xe)(?=\b|\d)",                                                               # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Oxygen":                   r"\b(oxygen|o2)\b",                                                                     # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        "Water":                    r"\b(water|h2o)\b",                                                                     # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, but included in SPHN Contrast Agent Active Ingredient code
        ## Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, not included in SPHN yet
        #### "Manganese":           r"\b(manganese|mn)(?=\b|\d|cl\d?\b)",                                                   # Not a subclass of SNOMED-CT 385420005 | Contrast media (substance) |, not included in SPHN yet
    }


    # A list of common contrast agent active ingredient concentrations in % or mg/mL
    contrast_agent_active_ingredient_concentrations_list: ClassVar[ReadOnly[list[str]]] = ["30", "60", "76", "140", "150", "160", "180", "200", "240", "250", "260", "270", "282", "292", "300", "320", "350", "360", "370", "380", "390", "400"]

    # Omnipaque (Iohexol):      Available in 140, 180, 240, 300, and 350 mg I/mL. (Omnipaque 300 and 350 are standard for routine body CTs).
    # Isovue (Iopamidol):       Formulated as 200, 250, 300, and 370 mg I/mL. (Isovue 370 is widely used for high-velocity CT angiograms).
    # Visipaque (Iodixanol):    Available in 270 and 320 mg I/mL. This is an iso-osmolar agent frequently used in patients with compromised kidney function.
    # Ultravist (Iopromide):    Supplied as 150, 240, 300, and 370 mg I/mL.
    # Optiray (Ioversol):       Packaged as 160, 240, 300, and 350 mg I/mL.

    # Dotarem (Gadoterate meglumine):        0.5  mmol/mL	Standard macrocyclic agent
    # ProHance (Gadoteridol):	             0.5  mmol/mL	Standard macrocyclic agent
    # Magnevist (Gadopentetate dimeglumine): 0.5  mmol/mL	Linear agent (mostly historical/discontinued)
    # MultiHance (Gadobenate dimeglumine):	 0.5  mmol/mL	Weak protein-binding; higher real-world signal
    # Gadavist / Gadovist (Gadobutrol):	     1.0  mmol/mL	Double-concentration formulation; allows for half the injection volume.
    # Vueway / Elucirem (Gadopiclenol):	     0.5  mmol/mL	High-relaxivity agent; allows a half-dose (0.05 mmol/kg) to provide identical clarity to a full standard dose.
    # Eovist / Primovist (Gadoxetic acid):	 0.25 mmol/mL	Half-concentration hepatobiliary-specific agent used exclusively for targeted liver mapping.

    # Readi-Cat 2 (Barium Sulfate): Formulated precisely at 2.1% w/v. It is deliberately a very low concentration so that it opacifies the bowel loops during a CT scan without causing harsh white artifacts that ruin the image.
    # E-Z-Paque (Barium Sulfate): Prepared at 96% w/v when reconstituted, used for standard upper GI radiographic tracking.
    # Liquid Polibar: Supplied as a high-density 105% w/v suspension, typically utilized for double-contrast barium enemas.

    #
    # Administration routes
    #

    # A dictionary mapping DICOM defined coded administration routes to SNOMED codes for SPHN
    # Key: Tuple of DICOM coding scheme designator and code value (e.g., ("SCT", "47625008"))
    # Value: Tuple of SNOMED coding scheme designator, code value, and description (e.g., ("SNOMED", "47625008", "| Intravenous route (qualifier value) |"))
    # Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_11.html Table CID 11. Administration Route
    # Note: Not all DICOM administration routes have a corresponding SNOMED code.
    # Link: https://dicom.nema.org/medical/dicom/Final/cp1495_ft3_badsnomedcodes.pdf
    # Note: Only the coding scheme designator "SCT" is converted to "SNOMED" and the human-readable description is from the SNOMED terminology.
    administration_routes_list: ClassVar[ReadOnly[dict[tuple[str, str], tuple[str, str, str]]]] = {
        ("SCT", "26643006"):    ("SNOMED", "26643006",   "| Oral route (qualifier value) |"),                       # "Oral route",
        ("SCT", "47625008"):    ("SNOMED", "47625008",   "| Intravenous route (qualifier value) |"),                # "Intravenous route",
        ("SCT", "58100008"):    ("SNOMED", "58100008",   "| Intra-arterial route (qualifier value) |"),             # "Intra-arterial route",
        ("SCT", "72607000"):    ("SNOMED", "72607000",   "| Intrathecal route (qualifier value) |"),                # "Intrathecal route",
        ("SCT", "12130007"):    ("SNOMED", "12130007",   "| Intra-articular route (qualifier value) |"),            # "Intra-articular route",
        ("SCT", "446406008"):   ("SNOMED", "447694001",  "| Respiratory tract route (qualifier value) |"),          # "By inhalation",
        # Other routes
        ("SCT", "78421000"):    ("SNOMED", "78421000",   "| Intramuscular route (qualifier value) |"),              # "Intramuscular route",
        ("SCT", "34206005"):    ("SNOMED", "34206005",   "| Subcutaneous route (qualifier value) |"),               # "Subcutaneous route",
        ("SCT", "372464004"):   ("SNOMED", "372464004",  "| Intradermal route (qualifier value) |"),                # "Intracutaneous route", "Intradermal route",
        ("SCT", "38239002"):    ("SNOMED", "38239002",   "| Intraperitoneal route (qualifier value) |"),            # "Intraperitoneal route",
        ("SCT", "60213007"):    ("SNOMED", "60213007",   "| Intramedullary route (qualifier value) |"),             # "Intramedullary route",
        ("SCT", "6064005"):     ("SNOMED", "6064005",    "| Topical route (qualifier value) |"),                    # "Topical route",
        ("SCT", "37737002"):    ("SNOMED", "37737002",   "| Intraluminal route (qualifier value) |"),               # "Intraluminal route",
        ("SCT", "37161004"):    ("SNOMED", "37161004",   "| Rectal route (qualifier value) |"),                     # "Per rectum",
        ("SCT", "16857009"):    ("SNOMED", "16857009",   "| Vaginal route (qualifier value) |"),                    # "Vaginal route",
        ("SCT", "372463005"):   ("SNOMED", "372463005",  "| Intracoronary route (qualifier value) |"),              # "Intracoronary route",
        ("SCT", "372460008"):   ("SNOMED", "372460008",  "| Intracardiac route (qualifier value) |"),               # "Intracardiac route",
        ("SCT", "420287000"):   ("SNOMED", "420287000",  "| Intraventricular route - cardiac (qualifier value) |"), # "Intraventricular route - cardiac",
        ("SCT", "46713006"):    ("SNOMED", "46713006",   "| Nasal route (qualifier value) |"),                      # "Nasal route",
        ("SCT", "447122006"):   ("SNOMED", "447122006",  "| Intratumor route (qualifier value) |"),                 # "Intratumor route",
        ("SCT", "1259221004"):  ("SNOMED", "1259221004", "| Intracorporus cavernosum route (qualifier value) |")    # "Intracorpus cavernosum route"
        #("NCIt", "C38244"):    ("SNOMED", "",           ""),                                                       # "Intraepithelial route",      # There used to be a SNOMED RT code: G-D111, but it is not in SNOMED CT, concept: 89947002
        #("NCIt", "C38306"):    ("SNOMED", "",           ""),                                                       # "Transluminal route",         # There used to be a SNOMED RT code: G-D142, but it is not in SNOMED CT, concept: 9942002
        #("NCIt", "C38213"):    ("SNOMED", "",           ""),                                                       # "Extraluminal route",         # There used to be a SNOMED RT code: G-D146, but it is not in SNOMED CT, concept: 31638007
        #("DCM", "127070"):     ("SNOMED", "",           ""),                                                       # "Retro-orbital route",        # A technique used to administer substances via the vascular sinus and plexus located directly 
                                                                                                                                                    # behind the eye in small research animals like mice and rats
        # Other routes by Edwin:
        #                       ("SNOMED", "372471009",  "| Intravesical route (qualifier value) |"),
        #                       ("SNOMED", "420254004",  "| Body cavity route (qualifier value) |"),
    }

    # Dictionary with regex patterns of administration routes and their medical terms and/or abbreviations
    # Key: Administration route name
    # Value: Regex pattern to match the route in the DICOM string
    route_patterns: ClassVar[ReadOnly[dict[str, re.Pattern]]] = {
        "Oral":             r"\b(oral|peroral|po|per\s*os)\b", 
        "Intravenous":      r"\b(iv|intravenous|intra-venous|intra\s*venous)\b", 
        "Intra-arterial":   r"\b(ia|intra-arterial|intraarterial|intra\s*arterial)\b", 
        "Intrathecal":      r"\b(intrathecal|intraspinal)\b", 
        "Intra-articular":  r"\b(intra-articular|intraarticular|intra\s*articular|intra-joint|intra\s*joint)\b", 
        "Inhalation":       r"\b(inhalation|inhaled|endotracheal)\b",
        "Intravesical":     r"\b(intravesical|bladder)\b",
        "Intracavitary":    r"\b(intracavitary|intrauterine|fistula)\b",
        "Rectal":           r"\b(pr|rectal|per\s*rectum)\b"
    }

    # Mapping of above listed administration route names to their corresponding SNOMED codes for SPHN
    sphn_route_codes: ClassVar[ReadOnly[dict[str, tuple[str, str, str]]]] = {
        "Oral":             ("SNOMED", "26643006",  "| Oral route (qualifier value) |"),
        "Intravenous":      ("SNOMED", "47625008",  "| Intravenous route (qualifier value) |"),
        "Intra-arterial":   ("SNOMED", "58100008",  "| Intra-arterial route (qualifier value) |"),
        "Intrathecal":      ("SNOMED", "72607000",  "| Intrathecal route (qualifier value) |"),
        "Intra-articular":  ("SNOMED", "12130007",  "| Intra-articular route (qualifier value) |"),
        "Inhalation":       ("SNOMED", "447694001", "| Respiratory tract route (qualifier value) |"),
        "Intravesical":     ("SNOMED", "372471009", "| Intravesical route (qualifier value) |"),
        "Intracavitary":    ("SNOMED", "420254004", "| Body cavity route (qualifier value) |"),
        "Rectal":           ("SNOMED", "37161004",  "| Rectal route (qualifier value) |")
    }


    """

    We could add "SNOMED-CT: 87869004 | Manganese (substance) |" to the SPHN Contrast Agent Active Ingredient code list as it is relevant for manganese-based MRI contrast agents like Teslascan.

    Trade name: Teslascan 
    Manufacturer: IC Targets
    Active ingredient: Mangafodipir Trisodium
    SNOMED 410872002 | Mangafodipir trisodium (substance) | 
    A subclass of SNOMED-CT 385420005 | Contrast media (substance) |

    It is Manganese-based, but Manganese is not included in SPHN Contrast Agent Active Ingredient code list, unlike other elements e.g. Iodine, Gadolinium

    See also the following references for more information on manganese-based MRI contrast agents:
    https://pmc.ncbi.nlm.nih.gov/articles/PMC12384406/
    https://www.itnonline.com/content/ge-healthcare-first-patient-dosed-trial-manganese-based-mri-contrast-agent

    """


    # ##################################################
    # Radiopharmaceuticals
    # ##################################################

    # Regex pattern fragments for the radionuclides (isotopes) of the radiopharmaceuticals below.
    # Each fragment matches the common notations in DICOM strings, e.g. for F^18^:
    #   "F18", "F-18", "F 18", "18F", "18-F", "[18F]", "(18F)", "^18^F", "F^18^", "Fluorine-18"
    _rp_iso_C11:  ClassVar[str] = r"(?:[\[(]?(?:11[-\s^]*c|c[-\s^]*11(?!\d))[\])]?|carbon[-\s]?11(?!\d)|11[-\s^]*carbon)"
    _rp_iso_C14:  ClassVar[str] = r"(?:[\[(]?(?:14[-\s^]*c|c[-\s^]*14(?!\d))[\])]?|carbon[-\s]?14(?!\d)|14[-\s^]*carbon)"
    _rp_iso_N13:  ClassVar[str] = r"(?:[\[(]?(?:13[-\s^]*n|n[-\s^]*13(?!\d))[\])]?|nitrogen[-\s]?13(?!\d)|13[-\s^]*nitrogen)"
    _rp_iso_O15:  ClassVar[str] = r"(?:[\[(]?(?:15[-\s^]*o|o[-\s^]*15(?!\d))[\])]?|oxygen[-\s]?15(?!\d)|15[-\s^]*oxygen)"
    _rp_iso_F18:  ClassVar[str] = r"(?:[\[(]?(?:18[-\s^]*f|f[-\s^]*18(?!\d))[\])]?|fluorine[-\s]?18(?!\d)|18[-\s^]*fluorine)"
    _rp_iso_Cu60: ClassVar[str] = r"(?:[\[(]?(?:60[-\s^]*cu|cu[-\s^]*60(?!\d))[\])]?|copper[-\s]?60(?!\d)|60[-\s^]*copper)"
    _rp_iso_Cu61: ClassVar[str] = r"(?:[\[(]?(?:61[-\s^]*cu|cu[-\s^]*61(?!\d))[\])]?|copper[-\s]?61(?!\d)|61[-\s^]*copper)"
    _rp_iso_Cu62: ClassVar[str] = r"(?:[\[(]?(?:62[-\s^]*cu|cu[-\s^]*62(?!\d))[\])]?|copper[-\s]?62(?!\d)|62[-\s^]*copper)"
    _rp_iso_Cu64: ClassVar[str] = r"(?:[\[(]?(?:64[-\s^]*cu|cu[-\s^]*64(?!\d))[\])]?|copper[-\s]?64(?!\d)|64[-\s^]*copper)"
    _rp_iso_Ga68: ClassVar[str] = r"(?:[\[(]?(?:68[-\s^]*ga|ga[-\s^]*68(?!\d))[\])]?|gallium[-\s]?68(?!\d)|68[-\s^]*gallium)"
    _rp_iso_Ge68: ClassVar[str] = r"(?:[\[(]?(?:68[-\s^]*ge|ge[-\s^]*68(?!\d))[\])]?|germanium[-\s]?68(?!\d)|68[-\s^]*germanium)"
    _rp_iso_Zr89: ClassVar[str] = r"(?:[\[(]?(?:89[-\s^]*zr|zr[-\s^]*89(?!\d))[\])]?|zirconium[-\s]?89(?!\d)|89[-\s^]*zirconium)"
    _rp_iso_I124: ClassVar[str] = r"(?:[\[(]?(?:124[-\s^]*i|i[-\s^]*124(?!\d))[\])]?|iodine[-\s]?124(?!\d)|124[-\s^]*iodine)"
    _rp_iso_I131: ClassVar[str] = r"(?:[\[(]?(?:131[-\s^]*i|i[-\s^]*131(?!\d))[\])]?|iodine[-\s]?131(?!\d)|131[-\s^]*iodine)"
    _rp_iso_Na22: ClassVar[str] = r"(?:[\[(]?(?:22[-\s^]*na|na[-\s^]*22(?!\d))[\])]?|sodium[-\s]?22(?!\d)|22[-\s^]*sodium)"
    _rp_iso_Rb82: ClassVar[str] = r"(?:[\[(]?(?:82[-\s^]*rb|rb[-\s^]*82(?!\d))[\])]?|rubidium[-\s]?82(?!\d)|82[-\s^]*rubidium)"
    # Additional radionuclides of DICOM CID 4020 (PET Radionuclide)
    _rp_iso_O14:   ClassVar[str] = r"(?:[\[(]?(?:14[-\s^]*o|o[-\s^]*14(?!\d))[\])]?|oxygen[-\s]?14(?!\d)|14[-\s^]*oxygen)"
    _rp_iso_K38:   ClassVar[str] = r"(?:[\[(]?(?:38[-\s^]*k|k[-\s^]*38(?!\d))[\])]?|potassium[-\s]?38(?!\d)|38[-\s^]*potassium)"
    _rp_iso_Sc43:  ClassVar[str] = r"(?:[\[(]?(?:43[-\s^]*sc|sc[-\s^]*43(?!\d))[\])]?|scandium[-\s]?43(?!\d)|43[-\s^]*scandium)"
    _rp_iso_Sc44:  ClassVar[str] = r"(?:[\[(]?(?:44[-\s^]*sc|sc[-\s^]*44(?!\d))[\])]?|scandium[-\s]?44(?!\d)|44[-\s^]*scandium)"
    _rp_iso_Ti45:  ClassVar[str] = r"(?:[\[(]?(?:45[-\s^]*ti|ti[-\s^]*45(?!\d))[\])]?|titanium[-\s]?45(?!\d)|45[-\s^]*titanium)"
    _rp_iso_Mn51:  ClassVar[str] = r"(?:[\[(]?(?:51[-\s^]*mn|mn[-\s^]*51(?!\d))[\])]?|manganese[-\s]?51(?!\d)|51[-\s^]*manganese)"
    _rp_iso_Fe52:  ClassVar[str] = r"(?:[\[(]?(?:52[-\s^]*fe|fe[-\s^]*52(?!\d))[\])]?|iron[-\s]?52(?!\d)|52[-\s^]*iron)"
    _rp_iso_Mn52:  ClassVar[str] = r"(?:[\[(]?(?:52[-\s^]*mn|mn[-\s^]*52(?![\dm]))[\])]?|manganese[-\s]?52(?![\dm])|52[-\s^]*manganese)"
    _rp_iso_Mn52m: ClassVar[str] = r"(?:[\[(]?(?:52m[-\s^]*mn|mn[-\s^]*52m)[\])]?|manganese[-\s]?52m|52m[-\s^]*manganese)"
    _rp_iso_Zn62:  ClassVar[str] = r"(?:[\[(]?(?:62[-\s^]*zn|zn[-\s^]*62(?!\d))[\])]?|zinc[-\s]?62(?!\d)|62[-\s^]*zinc)"
    _rp_iso_Ga66:  ClassVar[str] = r"(?:[\[(]?(?:66[-\s^]*ga|ga[-\s^]*66(?!\d))[\])]?|gallium[-\s]?66(?!\d)|66[-\s^]*gallium)"
    _rp_iso_As70:  ClassVar[str] = r"(?:[\[(]?(?:70[-\s^]*as|as[-\s^]*70(?!\d))[\])]?|arsenic[-\s]?70(?!\d)|70[-\s^]*arsenic)"
    _rp_iso_As72:  ClassVar[str] = r"(?:[\[(]?(?:72[-\s^]*as|as[-\s^]*72(?!\d))[\])]?|arsenic[-\s]?72(?!\d)|72[-\s^]*arsenic)"
    _rp_iso_Se73:  ClassVar[str] = r"(?:[\[(]?(?:73[-\s^]*se|se[-\s^]*73(?!\d))[\])]?|selenium[-\s]?73(?!\d)|73[-\s^]*selenium)"
    _rp_iso_Br75:  ClassVar[str] = r"(?:[\[(]?(?:75[-\s^]*br|br[-\s^]*75(?!\d))[\])]?|bromine[-\s]?75(?!\d)|75[-\s^]*bromine)"
    _rp_iso_Br76:  ClassVar[str] = r"(?:[\[(]?(?:76[-\s^]*br|br[-\s^]*76(?!\d))[\])]?|bromine[-\s]?76(?!\d)|76[-\s^]*bromine)"
    _rp_iso_Br77:  ClassVar[str] = r"(?:[\[(]?(?:77[-\s^]*br|br[-\s^]*77(?!\d))[\])]?|bromine[-\s]?77(?!\d)|77[-\s^]*bromine)"
    _rp_iso_Y86:   ClassVar[str] = r"(?:[\[(]?(?:86[-\s^]*y|y[-\s^]*86(?!\d))[\])]?|yttrium[-\s]?86(?!\d)|86[-\s^]*yttrium)"
    _rp_iso_Nb90:  ClassVar[str] = r"(?:[\[(]?(?:90[-\s^]*nb|nb[-\s^]*90(?!\d))[\])]?|niobium[-\s]?90(?!\d)|90[-\s^]*niobium)"
    _rp_iso_Y90:   ClassVar[str] = r"(?:[\[(]?(?:90[-\s^]*y|y[-\s^]*90(?!\d))[\])]?|yttrium[-\s]?90(?!\d)|90[-\s^]*yttrium)"
    _rp_iso_Tc94m: ClassVar[str] = r"(?:[\[(]?(?:94m[-\s^]*tc|tc[-\s^]*94m)[\])]?|technetium[-\s]?94m|94m[-\s^]*technetium)"
    _rp_iso_Tb152: ClassVar[str] = r"(?:[\[(]?(?:152[-\s^]*tb|tb[-\s^]*152(?!\d))[\])]?|terbium[-\s]?152(?!\d)|152[-\s^]*terbium)"
    # Additional radionuclides of DICOM CID 18 (Isotopes in Radiopharmaceuticals)
    _rp_iso_Na24:    ClassVar[str] = r"(?:[\[(]?(?:24[-\s^]*na|na[-\s^]*24(?!\d))[\])]?|sodium[-\s]?24(?!\d)|24[-\s^]*sodium)"
    _rp_iso_P32:     ClassVar[str] = r"(?:[\[(]?(?:32[-\s^]*p|p[-\s^]*32(?!\d))[\])]?|phosphorus[-\s]?32(?!\d)|32[-\s^]*phosphorus)"
    _rp_iso_K42:     ClassVar[str] = r"(?:[\[(]?(?:42[-\s^]*k|k[-\s^]*42(?!\d))[\])]?|potassium[-\s]?42(?!\d)|42[-\s^]*potassium)"
    _rp_iso_K43:     ClassVar[str] = r"(?:[\[(]?(?:43[-\s^]*k|k[-\s^]*43(?!\d))[\])]?|potassium[-\s]?43(?!\d)|43[-\s^]*potassium)"
    _rp_iso_Sc47:    ClassVar[str] = r"(?:[\[(]?(?:47[-\s^]*sc|sc[-\s^]*47(?!\d))[\])]?|scandium[-\s]?47(?!\d)|47[-\s^]*scandium)"
    _rp_iso_Cr51:    ClassVar[str] = r"(?:[\[(]?(?:51[-\s^]*cr|cr[-\s^]*51(?!\d))[\])]?|chromium[-\s]?51(?!\d)|51[-\s^]*chromium)"
    _rp_iso_Co57:    ClassVar[str] = r"(?:[\[(]?(?:57[-\s^]*co|co[-\s^]*57(?!\d))[\])]?|cobalt[-\s]?57(?!\d)|57[-\s^]*cobalt)"
    _rp_iso_Co58:    ClassVar[str] = r"(?:[\[(]?(?:58[-\s^]*co|co[-\s^]*58(?!\d))[\])]?|cobalt[-\s]?58(?!\d)|58[-\s^]*cobalt)"
    _rp_iso_Fe59:    ClassVar[str] = r"(?:[\[(]?(?:59[-\s^]*fe|fe[-\s^]*59(?!\d))[\])]?|iron[-\s]?59(?!\d)|59[-\s^]*iron)"
    _rp_iso_Co60:    ClassVar[str] = r"(?:[\[(]?(?:60[-\s^]*co|co[-\s^]*60(?!\d))[\])]?|cobalt[-\s]?60(?!\d)|60[-\s^]*cobalt)"
    _rp_iso_Cu67:    ClassVar[str] = r"(?:[\[(]?(?:67[-\s^]*cu|cu[-\s^]*67(?!\d))[\])]?|copper[-\s]?67(?!\d)|67[-\s^]*copper)"
    _rp_iso_Ga67:    ClassVar[str] = r"(?:[\[(]?(?:67[-\s^]*ga|ga[-\s^]*67(?!\d))[\])]?|gallium[-\s]?67(?!\d)|67[-\s^]*gallium)"
    _rp_iso_Se75:    ClassVar[str] = r"(?:[\[(]?(?:75[-\s^]*se|se[-\s^]*75(?!\d))[\])]?|selenium[-\s]?75(?!\d)|75[-\s^]*selenium)"
    _rp_iso_Kr81m:   ClassVar[str] = r"(?:[\[(]?(?:81m?[-\s^]*kr|kr[-\s^]*81m?(?![\dm]))[\])]?|krypton[-\s]?81m?(?![\dm])|81m?[-\s^]*krypton)"
    _rp_iso_Kr85:    ClassVar[str] = r"(?:[\[(]?(?:85[-\s^]*kr|kr[-\s^]*85(?!\d))[\])]?|krypton[-\s]?85(?!\d)|85[-\s^]*krypton)"
    _rp_iso_Sr85:    ClassVar[str] = r"(?:[\[(]?(?:85[-\s^]*sr|sr[-\s^]*85(?!\d))[\])]?|strontium[-\s]?85(?!\d)|85[-\s^]*strontium)"
    _rp_iso_Sr87m:   ClassVar[str] = r"(?:[\[(]?(?:87m?[-\s^]*sr|sr[-\s^]*87m?(?![\dm]))[\])]?|strontium[-\s]?87m?(?![\dm])|87m?[-\s^]*strontium)"
    _rp_iso_Sr89:    ClassVar[str] = r"(?:[\[(]?(?:89[-\s^]*sr|sr[-\s^]*89(?!\d))[\])]?|strontium[-\s]?89(?!\d)|89[-\s^]*strontium)"
    _rp_iso_Ru97:    ClassVar[str] = r"(?:[\[(]?(?:97[-\s^]*ru|ru[-\s^]*97(?!\d))[\])]?|ruthenium[-\s]?97(?!\d)|97[-\s^]*ruthenium)"
    _rp_iso_Tc99m:   ClassVar[str] = r"(?:[\[(]?(?:99m?[-\s^]*tc|tc[-\s^]*99m?(?![\dm]))[\])]?|technetium[-\s]?99m?(?![\dm])|99m?[-\s^]*technetium)"
    _rp_iso_In111:   ClassVar[str] = r"(?:[\[(]?(?:111[-\s^]*in|in[-\s^]*111(?!\d))[\])]?|indium[-\s]?111(?!\d)|111[-\s^]*indium)"
    _rp_iso_In113m:  ClassVar[str] = r"(?:[\[(]?(?:113m?[-\s^]*in|in[-\s^]*113m?(?![\dm]))[\])]?|indium[-\s]?113m?(?![\dm])|113m?[-\s^]*indium)"
    _rp_iso_I122:    ClassVar[str] = r"(?:[\[(]?(?:122[-\s^]*i|i[-\s^]*122(?!\d))[\])]?|iodine[-\s]?122(?!\d)|122[-\s^]*iodine)"
    _rp_iso_I123:    ClassVar[str] = r"(?:[\[(]?(?:123[-\s^]*i|i[-\s^]*123(?!\d))[\])]?|iodine[-\s]?123(?!\d)|123[-\s^]*iodine)"
    _rp_iso_Xe123:   ClassVar[str] = r"(?:[\[(]?(?:123[-\s^]*xe|xe[-\s^]*123(?!\d))[\])]?|xenon[-\s]?123(?!\d)|123[-\s^]*xenon)"
    _rp_iso_I125:    ClassVar[str] = r"(?:[\[(]?(?:125[-\s^]*i|i[-\s^]*125(?!\d))[\])]?|iodine[-\s]?125(?!\d)|125[-\s^]*iodine)"
    _rp_iso_Xe127:   ClassVar[str] = r"(?:[\[(]?(?:127[-\s^]*xe|xe[-\s^]*127(?!\d))[\])]?|xenon[-\s]?127(?!\d)|127[-\s^]*xenon)"
    _rp_iso_Ba133:   ClassVar[str] = r"(?:[\[(]?(?:133[-\s^]*ba|ba[-\s^]*133(?!\d))[\])]?|barium[-\s]?133(?!\d)|133[-\s^]*barium)"
    _rp_iso_Xe133:   ClassVar[str] = r"(?:[\[(]?(?:133[-\s^]*xe|xe[-\s^]*133(?!\d))[\])]?|xenon[-\s]?133(?!\d)|133[-\s^]*xenon)"
    _rp_iso_Tb149:   ClassVar[str] = r"(?:[\[(]?(?:149[-\s^]*tb|tb[-\s^]*149(?!\d))[\])]?|terbium[-\s]?149(?!\d)|149[-\s^]*terbium)"
    _rp_iso_Gd153:   ClassVar[str] = r"(?:[\[(]?(?:153[-\s^]*gd|gd[-\s^]*153(?!\d))[\])]?|gadolinium[-\s]?153(?!\d)|153[-\s^]*gadolinium)"
    _rp_iso_Sm153:   ClassVar[str] = r"(?:[\[(]?(?:153[-\s^]*sm|sm[-\s^]*153(?!\d))[\])]?|samarium[-\s]?153(?!\d)|153[-\s^]*samarium)"
    _rp_iso_Tb161:   ClassVar[str] = r"(?:[\[(]?(?:161[-\s^]*tb|tb[-\s^]*161(?!\d))[\])]?|terbium[-\s]?161(?!\d)|161[-\s^]*terbium)"
    _rp_iso_Ho166:   ClassVar[str] = r"(?:[\[(]?(?:166[-\s^]*ho|ho[-\s^]*166(?!\d))[\])]?|holmium[-\s]?166(?!\d)|166[-\s^]*holmium)"
    _rp_iso_Yb169:   ClassVar[str] = r"(?:[\[(]?(?:169[-\s^]*yb|yb[-\s^]*169(?!\d))[\])]?|ytterbium[-\s]?169(?!\d)|169[-\s^]*ytterbium)"
    _rp_iso_Lu177:   ClassVar[str] = r"(?:[\[(]?(?:177[-\s^]*lu|lu[-\s^]*177(?!\d))[\])]?|lutetium[-\s]?177(?!\d)|177[-\s^]*lutetium)"
    _rp_iso_Ta178:   ClassVar[str] = r"(?:[\[(]?(?:178[-\s^]*ta|ta[-\s^]*178(?!\d))[\])]?|tantalum[-\s]?178(?!\d)|178[-\s^]*tantalum)"
    _rp_iso_Re186:   ClassVar[str] = r"(?:[\[(]?(?:186[-\s^]*re|re[-\s^]*186(?!\d))[\])]?|rhenium[-\s]?186(?!\d)|186[-\s^]*rhenium)"
    _rp_iso_Re188:   ClassVar[str] = r"(?:[\[(]?(?:188[-\s^]*re|re[-\s^]*188(?!\d))[\])]?|rhenium[-\s]?188(?!\d)|188[-\s^]*rhenium)"
    _rp_iso_Ir191m:  ClassVar[str] = r"(?:[\[(]?(?:191m?[-\s^]*ir|ir[-\s^]*191m?(?![\dm]))[\])]?|iridium[-\s]?191m?(?![\dm])|191m?[-\s^]*iridium)"
    _rp_iso_Au198:   ClassVar[str] = r"(?:[\[(]?(?:198[-\s^]*au|au[-\s^]*198(?!\d))[\])]?|gold[-\s]?198(?!\d)|198[-\s^]*gold)"
    _rp_iso_Au199:   ClassVar[str] = r"(?:[\[(]?(?:199[-\s^]*au|au[-\s^]*199(?!\d))[\])]?|gold[-\s]?199(?!\d)|199[-\s^]*gold)"
    _rp_iso_Tl201:   ClassVar[str] = r"(?:[\[(]?(?:201[-\s^]*tl|tl[-\s^]*201(?!\d))[\])]?|thallium[-\s]?201(?!\d)|201[-\s^]*thallium)"
    _rp_iso_Pb203:   ClassVar[str] = r"(?:[\[(]?(?:203[-\s^]*pb|pb[-\s^]*203(?!\d))[\])]?|lead[-\s]?203(?!\d)|203[-\s^]*lead)"
    _rp_iso_At211:   ClassVar[str] = r"(?:[\[(]?(?:211[-\s^]*at|at[-\s^]*211(?!\d))[\])]?|astatine[-\s]?211(?!\d)|211[-\s^]*astatine)"
    _rp_iso_Pb212:   ClassVar[str] = r"(?:[\[(]?(?:212[-\s^]*pb|pb[-\s^]*212(?!\d))[\])]?|lead[-\s]?212(?!\d)|212[-\s^]*lead)"
    _rp_iso_Bi213:   ClassVar[str] = r"(?:[\[(]?(?:213[-\s^]*bi|bi[-\s^]*213(?!\d))[\])]?|bismuth[-\s]?213(?!\d)|213[-\s^]*bismuth)"
    _rp_iso_Ra223:   ClassVar[str] = r"(?:[\[(]?(?:223[-\s^]*ra|ra[-\s^]*223(?!\d))[\])]?|radium[-\s]?223(?!\d)|223[-\s^]*radium)"
    _rp_iso_Ac225:   ClassVar[str] = r"(?:[\[(]?(?:225[-\s^]*ac|ac[-\s^]*225(?!\d))[\])]?|actinium[-\s]?225(?!\d)|225[-\s^]*actinium)"

    # Separator between a radionuclide and a name, e.g. "18F-FDG", "F-18 FDG", "[18F]FDG"
    _rp_sep: ClassVar[str] = r"[-\s]*"

    # Negative lookbehinds/lookahead to exclude names directly preceded or followed by an F^18^ radionuclide,
    # used for names that also have a separate F^18^ entry (e.g. "Choline C^11^" versus "Fluorocholine F^18^")
    _rp_not_after_F18:  ClassVar[str] = r"(?<!18f)(?<!18f[-\s\]\)])(?<!f18[-\s])(?<!f-18[-\s])(?<!18-f[-\s])(?<!fluoro)(?<!fluoro[-\s])(?<!fluorine-18[-\s])"
    _rp_not_before_F18: ClassVar[str] = rf"(?!{_rp_sep}{_rp_iso_F18})"

    # Dictionary mapping the DICOM PET radiopharmaceutical names to regex patterns
    # Key: Code Meaning of the radiopharmaceutical in DICOM CID 4021 (e.g.: "Fluorodeoxyglucose F^18^")
    # Value: Regex pattern to match the "Code Meaning" and the "Other Names" in a DICOM string (e.g. Radiopharmaceutical (0018,0031))
    # Note(s):
    #  - The patterns are intended to be compiled with re.IGNORECASE.
    #  - Crucial: The regex patterns should match the full radiopharmaceutical name and avoid partial matches within others.
    #  - The patterns use (?<![a-z0-9]) and (?![a-z0-9]) instead of \b, as several names start or end with brackets, e.g. "cG250-F(ab')(2)".
    #  - The radionuclide is required next to the name (before or after it), when:
    #     - the same name is listed with different radionuclides, e.g. "Glutamine C^11^", "Glutamine C^14^", "Glutamine F^18^", or
    #     - the name is also commonly used with radionuclides not listed here, e.g. "Sodium iodide I^124^" (versus I-123/I-131),
    #       "Dotatate Ga^68^" (versus Lu-177/Cu-64), "Nanocolloidal albumin ^89^Zr" (versus Tc-99m).
    #    Otherwise, the name alone is sufficient.
    #  - Names marked "additional" are not listed in DICOM CID 4021 but are common names or abbreviations.
    #  - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4021.html
    pet_radiopharmaceutical_names_2_patterns: ClassVar[Mapping[str, str]] = {

        "28H1 ^89^Zr":                              r"(?<![a-z0-9])(28[-\s]?h1)(?![a-z0-9])",
        "2FA F^18^":                                r"(?<![a-z0-9])(2[-\s]?fa|(?:2[-\s]?)?f[-\s]?a[-\s]?85380)(?![a-z0-9])",
        "2-Thymidine C^11^":                        rf"(?<![a-z0-9]){_rp_not_after_F18}((?:2[-\s]?)?thymidine)(?![a-z0-9]){_rp_not_before_F18}",
        "3-N-Methylspiperone C^11^":                r"(?<![a-z0-9])((?:3[-\s]?)?(?:n[-\s]?)?methyl[-\s]?spiperone)(?![a-z0-9])",
        "7D12 ^89^Zr":                              r"(?<![a-z0-9])(7[-\s]?d12)(?![a-z0-9])",
        "7E11 ^89^Zr":                              r"(?<![a-z0-9])(7[-\s]?e11)(?![a-z0-9])",
        "Acetate C^11^":                            r"(?<![a-z0-9])(acetate)(?![a-z0-9])",
        "AGN-150998 ^89^Zr":                        r"(?<![a-z0-9])(agn[-\s]?150998|mp[-\s]?0112)(?![a-z0-9])",
        "Ammonia N^13^":                            r"(?<![a-z0-9])(ammonia|nh3)(?![a-z0-9])",                                    # nh3: additional
        "Anti-B220 ^89^Zr":                         r"(?<![a-z0-9])(anti[-\s]?b220|anti[-\s]?cd45r)(?![a-z0-9])",
        "ATSM Cu^60^":                              rf"(?<![a-z0-9])({_rp_iso_Cu60}{_rp_sep}(?:cu[-\s]?)?atsm|(?:cu[-\s]?)?atsm{_rp_sep}{_rp_iso_Cu60})(?![a-z0-9])",
        "ATSM Cu^61^":                              rf"(?<![a-z0-9])({_rp_iso_Cu61}{_rp_sep}(?:cu[-\s]?)?atsm|(?:cu[-\s]?)?atsm{_rp_sep}{_rp_iso_Cu61})(?![a-z0-9])",
        "ATSM Cu^62^":                              rf"(?<![a-z0-9])({_rp_iso_Cu62}{_rp_sep}(?:cu[-\s]?)?atsm|(?:cu[-\s]?)?atsm{_rp_sep}{_rp_iso_Cu62})(?![a-z0-9])",
        "ATSM Cu^64^":                              rf"(?<![a-z0-9])({_rp_iso_Cu64}{_rp_sep}(?:cu[-\s]?)?atsm|(?:cu[-\s]?)?atsm{_rp_sep}{_rp_iso_Cu64})(?![a-z0-9])",
        "Benralizumab ^89^Zr":                      r"(?<![a-z0-9])(benralizumab|medi[-\s]?563|khk[-\s]?4563)(?![a-z0-9])",
        "Bevacizumab ^89^Zr":                       r"(?<![a-z0-9])(bevacizumab|avastin)(?![a-z0-9])",
        "Blinatumomab ^89^Zr":                      r"(?<![a-z0-9])(blinatumomab|amg[-\s]?103|mt[-\s]?103)(?![a-z0-9])",
        "Brentuximab ^89^Zr":                       r"(?<![a-z0-9])(brentuximab(?:[-\s]?vedotin)?|adcetris)(?![a-z0-9])",
        "Butanol O^15^":                            r"(?<![a-z0-9])((?:n[-\s]?)?butanol)(?![a-z0-9])",
        "Carbon dioxide O^15^":                     r"(?<![a-z0-9])(carbon[-\s]?dioxide|co2|c15o2)(?![a-z0-9])",                  # co2, c15o2: additional
        "Carbon monoxide C^11^":                    rf"(?<![a-z0-9])({_rp_iso_C11}{_rp_sep}(?:carbon[-\s]?monoxide|co)|(?:carbon[-\s]?monoxide|co){_rp_sep}{_rp_iso_C11}|11co)(?![a-z0-9])",
        "Carbon monoxide O^15^":                    rf"(?<![a-z0-9])({_rp_iso_O15}{_rp_sep}(?:carbon[-\s]?monoxide|co)|(?:carbon[-\s]?monoxide|co){_rp_sep}{_rp_iso_O15}|c15o)(?![a-z0-9])",
        "Carfentanil C^11^":                        r"(?<![a-z0-9])(carfentanil)(?![a-z0-9])",
        "Cetuximab ^89^Zr":                         r"(?<![a-z0-9])(cetuximab|erbitux)(?![a-z0-9])",
        "cG250-F(ab')(2) ^89^Zr":                   r"(?<![a-z0-9])(cg250[-\s]?f\(ab'\)(?:\(2\)|2))(?![a-z0-9])",
        "Choline C^11^":                            rf"(?<![a-z0-9]){_rp_not_after_F18}(choline)(?![a-z0-9]){_rp_not_before_F18}",
        "CLR1404 I^124^":                           rf"(?<![a-z0-9])({_rp_iso_I124}{_rp_sep}clr[-\s]?1404|clr[-\s]?1404{_rp_sep}{_rp_iso_I124})(?![a-z0-9])",
        "CLR1404 I^131^":                           rf"(?<![a-z0-9])({_rp_iso_I131}{_rp_sep}clr[-\s]?1404|clr[-\s]?1404{_rp_sep}{_rp_iso_I131})(?![a-z0-9])",
        "cMAb U36 ^89^Zr":                          r"(?<![a-z0-9])(cmab[-\s]?u36)(?![a-z0-9])",
        "cU36 ^89^Zr":                              r"(?<![a-z0-9])(cu36)(?![a-z0-9])",
        "DASB C^11^":                               r"(?<![a-z0-9])(dasb|3\-amino\-4\-\(2\-dimethylaminomethylphenylsulfanyl\)benzonitrile)(?![a-z0-9])",
        "DCFBC F^18^":                              r"(?<![a-z0-9])(dcfbc|n\-\[n\-\[\(s\)\-1,3\-dicarboxypropyl\]carbamoyl\]\-4\-fluorobenzyl\-l\-cysteine)(?![a-z0-9])",
        "Df-[FK](2) ^89^Zr":                        r"(?<![a-z0-9])(df[-\s]?\[fk\][-\s]?\(?2\)?)(?![-\s)]*3[-\s]?peg)(?![a-z0-9])",
        "Df-[FK](2)-3PEG(4) ^89^Zr":                r"(?<![a-z0-9])(df[-\s]?\[fk\][-\s]?\(?2\)?[-\s]?3[-\s]?peg[-\s]?\(?4\)?)(?![a-z0-9])",
        "Df-CD45 ^89^Zr":                           r"(?<![a-z0-9])(df[-\s]?cd45)(?![a-z0-9])",
        "Df-FK ^89^Zr":                             r"(?<![a-z0-9])(df[-\s]?fk)(?![-\s]?(?:peg|\(?2))(?![a-z0-9])",
        "Df-FK-PEG(3) ^89^Zr":                      r"(?<![a-z0-9])(df[-\s]?fk[-\s]?peg[-\s]?\(?3\)?)(?![a-z0-9])",
        "DN30 ^89^Zr":                              r"(?<![a-z0-9])(dn[-\s]?30)(?![a-z0-9])",
        "Dotatate Ga^68^":                          rf"(?<![a-z0-9])({_rp_iso_Ga68}{_rp_sep}(?:ga[-\s]?)?dota[-\s]?tate|(?:ga[-\s]?)?dota[-\s]?tate{_rp_sep}{_rp_iso_Ga68}|netspot)(?![a-z0-9])",  # netspot: additional
        "DPA-713 ^11^C":                            r"(?<![a-z0-9])(dpa[-\s]?713)(?![a-z0-9])",
        "DPA-714 ^18^F":                            r"(?<![a-z0-9])(dpa[-\s]?714)(?![a-z0-9])",
        "E4G10 ^89^Zr":                             r"(?<![a-z0-9])(e4g10)(?![a-z0-9])",
        "Ecromeximab ^89^Zr":                       r"(?<![a-z0-9])(ecromeximab|kw[-\s]?2871)(?![a-z0-9])",
        "Edotreotide Ga^68^":                       rf"(?<![a-z0-9])({_rp_iso_Ga68}{_rp_sep}(?:ga[-\s]?)?(?:edotreotide|dota[-\s]?toc|smt[-\s]?487)|(?:ga[-\s]?)?(?:edotreotide|dota[-\s]?toc|smt[-\s]?487){_rp_sep}{_rp_iso_Ga68})(?![a-z0-9])",
        "EDTA Ga^68^":                              rf"(?<![a-z0-9])({_rp_iso_Ga68}{_rp_sep}(?:ga[-\s]?)?edta|(?:ga[-\s]?)?edta{_rp_sep}{_rp_iso_Ga68})(?![a-z0-9])",
        "Fallypride C^11^":                         rf"(?<![a-z0-9])({_rp_iso_C11}{_rp_sep}fallypride|fallypride{_rp_sep}{_rp_iso_C11})(?![a-z0-9])",
        "Fallypride F^18^":                         rf"(?<![a-z0-9])({_rp_iso_F18}{_rp_sep}fallypride|fallypride{_rp_sep}{_rp_iso_F18})(?![a-z0-9])",
        "FLB 457 C^11^":                            r"(?<![a-z0-9])(flb[-\s]?457)(?![a-z0-9])",
        "Florbetaben F^18^":                        r"(?<![a-z0-9])(florbetaben|neuroceq|neuraceq)(?![a-z0-9])",                 # neuraceq: additional (spelling of the trade name)
        "Florbetapir F^18^":                        r"(?<![a-z0-9])(florbetapir|av[-\s]?45|amyvid)(?![a-z0-9])",
        "Flortaucipir F^18^":                       r"(?<![a-z0-9])(flortaucipir|tauvid)(?![a-z0-9])",                           # T807 and AV-1451: see "T807 F^18^"
        "Flubatine F^18^":                          r"(?<![a-z0-9])(flubatine|ncfheb)(?![a-z0-9])",
        "Fluciclatide F^18^":                       r"(?<![a-z0-9])(fluciclatide)(?![a-z0-9])",
        "Fluciclovine F^18^":                       r"(?<![a-z0-9])(fluciclovine|(?:anti[-\s]?)?facbc|axumin)(?![a-z0-9])",       # facbc, axumin: additional
        "Flumazenil C^11^":                         rf"(?<![a-z0-9])({_rp_iso_C11}{_rp_sep}flumazenil|flumazenil{_rp_sep}{_rp_iso_C11})(?![a-z0-9])",
        "Flumazenil F^18^":                         rf"(?<![a-z0-9])({_rp_iso_F18}{_rp_sep}flumazenil|flumazenil{_rp_sep}{_rp_iso_F18})(?![a-z0-9])",
        "Fluorethyltyrosin F^18^":                  r"(?<![a-z0-9])(fluoro?[-\s]?ethyl[-\s]?(?:l[-\s]?)?tyrosine?|fet)(?![a-z0-9])",  # fet: additional
        "Fluoroazomycin arabinoside F^18^":         r"(?<![a-z0-9])(fluoro[-\s]?azomycin[-\s]?arabinoside|faza)(?![a-z0-9])",
        "Fluorobenzothiazole F^18^":                r"(?<![a-z0-9])(fluoro[-\s]?benzothiazole)(?![a-z0-9])",
        "Fluorocholine F^18^":                      rf"(?<![a-z0-9])(fluoro[-\s]?(?:methyl[-\s]?)?choline|fch|fmch|{_rp_iso_F18}{_rp_sep}(?:methyl[-\s]?)?choline|(?:methyl[-\s]?)?choline{_rp_sep}{_rp_iso_F18})(?![a-z0-9])",  # fch, fmch: additional
        "Fluorodeoxyglucose F^18^":                 rf"(?<![a-z0-9])(fluoro[-\s]?(?:2[-\s]?)?deoxy[-\s]?(?:d[-\s]?)?glucose|(?:2[-\s]?)?deoxy[-\s]?(?:2[-\s]?)?(?:{_rp_iso_F18}[-\s]?)?fluoro[-\s]?(?:d[-\s]?)?glucose|fludeoxyglucose|(?:18[-\s]?)?fdg)(?![a-z0-9])",  # fludeoxyglucose (INN), fdg: additional
        "Fluoroestradiol F^18^":                    r"(?<![a-z0-9])(fluoro[-\s]?(?:17[-\s]?beta[-\s]?)?estradiol|fes)(?![a-z0-9])",
        "Fluoroetanidazole F^18^":                  r"(?<![a-z0-9])(fluoro[-\s]?etanidazole|ef5)(?![a-z0-9])",
        "Fluoro-L-dopa F^18^":                      rf"(?<![a-z0-9])((?:6[-\s]?)?fluoro[-\s]?(?:l[-\s]?)?dopa|f[-\s]?dopa|{_rp_iso_F18}{_rp_sep}(?:l[-\s]?)?dopa)(?![a-z0-9])",  # f-dopa, fdopa: additional
        "Fluoromethane F^18^":                      r"(?<![a-z0-9])(fluoro[-\s]?methane)(?![a-z0-9])",
        "Fluoromisonidazole F^18^":                 r"(?<![a-z0-9])(fluoro[-\s]?misonidazole|fmiso)(?![a-z0-9])",
        "Fluoropropyl-dihydrotetrabenazine F^18^":  r"(?<![a-z0-9])(fluoro[-\s]?propyl[-\s]?(?:di)?hydro[-\s]?tetrabenazine|(?:fp[-\s]?)?dtbz|av[-\s]?133)(?![a-z0-9])",
        "Fluorothymidine F^18^":                    rf"(?<![a-z0-9])((?:3'?[-\s]?deoxy[-\s]?3'?[-\s]?)?fluoro[-\s]?thymidine|flt|{_rp_iso_F18}{_rp_sep}thymidine|thymidine{_rp_sep}{_rp_iso_F18})(?![a-z0-9])",
        "Fluorotriopride F^18^":                    r"(?<![a-z0-9])(fluoro[-\s]?triopride)(?![a-z0-9])",
        "Fluorouracil F^18^":                       r"(?<![a-z0-9])((?:5[-\s]?)?fluoro[-\s]?uracil)(?![a-z0-9])",
        "Flurpiridaz F^18^":                        r"(?<![a-z0-9])(flurpiridaz|bms[-\s]?747158(?:[-\s]?02)?)(?![a-z0-9])",
        "Flutemetamol F^18^":                       r"(?<![a-z0-9])(flutemetamol|vizamyl)(?![a-z0-9])",
        "Fresolimumab ^89^Zr":                      r"(?<![a-z0-9])(fresolimumab|gc[-\s]?1008)(?![a-z0-9])",
        "GA201 ^89^Zr":                             r"(?<![a-z0-9])(ga[-\s]?201|rg[-\s]?1760|ro[-\s]?5083945)(?![a-z0-9])",
        "Germanium Ge^68^":                         rf"(?<![a-z0-9])(germanium(?:{_rp_sep}{_rp_iso_Ge68})?|{_rp_iso_Ge68})(?![a-z0-9])",
        "Glembatumumab vedotin ^89^Zr":             r"(?<![a-z0-9])(glembatumumab(?:[-\s]?vedotin)?|cdx[-\s]?011|cr011[-\s]?vcmmae)(?![a-z0-9])",
        "Glucose C^11^":                            rf"(?<![a-z0-9])({_rp_iso_C11}{_rp_sep}(?:d[-\s]?)?glucose|(?:d[-\s]?)?glucose{_rp_sep}{_rp_iso_C11})(?![a-z0-9])",
        "Glutamate N^13^":                          r"(?<![a-z0-9])(glutamate)(?![a-z0-9])",
        "Glutamine C^11^":                          rf"(?<![a-z0-9])({_rp_iso_C11}{_rp_sep}(?:l[-\s]?)?glutamine|(?:l[-\s]?)?glutamine{_rp_sep}{_rp_iso_C11})(?![a-z0-9])",
        "Glutamine C^14^":                          rf"(?<![a-z0-9])({_rp_iso_C14}{_rp_sep}(?:l[-\s]?)?glutamine|(?:l[-\s]?)?glutamine{_rp_sep}{_rp_iso_C14})(?![a-z0-9])",
        "Glutamine F^18^":                          rf"(?<![a-z0-9])({_rp_iso_F18}{_rp_sep}(?:l[-\s]?)?glutamine|(?:l[-\s]?)?glutamine{_rp_sep}{_rp_iso_F18}|(?:4[-\s]?)?fluoro[-\s]?(?:l[-\s]?)?glutamine)(?![a-z0-9])",
        "ISO-1 F^18^":                              r"(?<![a-z0-9])(iso[-\s]?1)(?![a-z0-9])",
        "J591 ^89^Zr":                              r"(?<![a-z0-9])((?:hu)?j[-\s]?591)(?![a-z0-9])",
        "Margetuximab ^89^Zr":                      r"(?<![a-z0-9])(margetuximab|mgah22)(?![a-z0-9])",
        "MEDI-551 ^89^Zr":                          r"(?<![a-z0-9])(medi[-\s]?551)(?![a-z0-9])",
        "Mespiperone C^11^":                        r"(?<![a-z0-9])(mespiperone)(?![a-z0-9])",
        "Methionine C^11^":                         r"(?<![a-z0-9])((?:l[-\s]?)?methionine|met)(?![a-z0-9])",                    # met: additional
        "MK-6240 F^18^":                            r"(?<![a-z0-9])(mk[-\s]?6240)(?![a-z0-9])",
        "Mogamulizumab ^89^Zr":                     r"(?<![a-z0-9])(mogamulizumab|amg[-\s]?761|kw[-\s]?0761|poteligeo)(?![a-z0-9])",
        "Monoclonal Antibody ^64^Cu":               rf"(?<![a-z0-9])({_rp_iso_Cu64}{_rp_sep}monoclonal[-\s]?antibod(?:y|ies)|monoclonal[-\s]?antibod(?:y|ies){_rp_sep}{_rp_iso_Cu64})(?![a-z0-9])",
        "Monoclonal Antibody ^89^Zr":               rf"(?<![a-z0-9])({_rp_iso_Zr89}{_rp_sep}monoclonal[-\s]?antibod(?:y|ies)|monoclonal[-\s]?antibod(?:y|ies){_rp_sep}{_rp_iso_Zr89})(?![a-z0-9])",
        "Monoclonal antibody I^124^":               rf"(?<![a-z0-9])({_rp_iso_I124}{_rp_sep}monoclonal[-\s]?antibod(?:y|ies)|monoclonal[-\s]?antibod(?:y|ies){_rp_sep}{_rp_iso_I124})(?![a-z0-9])",
        "Nanocolloidal albumin ^89^Zr":             rf"(?<![a-z0-9])({_rp_iso_Zr89}{_rp_sep}(?:nano[-\s]?colloidal[-\s]?albumin|nanocoll)|(?:nano[-\s]?colloidal[-\s]?albumin|nanocoll){_rp_sep}{_rp_iso_Zr89})(?![a-z0-9])",
        "Nifene F^18^":                             r"(?<![a-z0-9])(nifene)(?![a-z0-9])",
        "Obinituzimab ^89^Zr":                      r"(?<![a-z0-9])(obinituzimab|obinutuzumab|afutuzumab|gazyva)(?![a-z0-9])",  # obinutuzumab: additional (INN spelling)
        "Ocaratuzumab ^89^Zr":                      r"(?<![a-z0-9])(ocaratuzumab|ame[-\s]?133v|ly[-\s]?2469298)(?![a-z0-9])",
        "Oxygen O^15^":                             rf"(?<![a-z0-9])({_rp_iso_O15}{_rp_sep}(?:oxygen|o2)(?![-\s]*(?:water|h2o))|(?:oxygen|o2){_rp_sep}{_rp_iso_O15}(?!{_rp_sep}(?:water|h2o))|15o2|(?<!\d\^)(?<!\d[-\s])oxygen(?![-\s^]*(?:water|\d)))(?![a-z0-9])",  # o2, 15o2: additional
        "Oxygen-water O^15^":                       rf"(?<![a-z0-9])(oxygen[-\s]?water|{_rp_iso_O15}{_rp_sep}(?:water|h2o)|(?:water|h2o){_rp_sep}{_rp_iso_O15}|h2[-\s]?{_rp_iso_O15})(?![a-z0-9])",  # (h2o) water: additional
        "Palmitate C^11^":                          r"(?<![a-z0-9])(palmitate)(?![a-z0-9])",
        "Panitumumab ^89^Zr":                       r"(?<![a-z0-9])(panitumumab|abx[-\s]?egf|vectibix)(?![a-z0-9])",
        "Pegdinetanib ^89^Zr":                      r"(?<![a-z0-9])(pegdinetanib|bms[-\s]?844203|ct[-\s]?322|angiocept)(?![a-z0-9])",
        "Pembrolizumab ^89^Zr":                     r"(?<![a-z0-9])(pembrolizumab)(?![a-z0-9])",
        "PI-2620 F^18^":                            r"(?<![a-z0-9])(pi[-\s]?2620)(?![a-z0-9])",
        "Piflufolastat F^18^":                      r"(?<![a-z0-9])(piflufolastat|dcfpyl|pylarify|pylclari|2\-\(3\-\(1\-carboxy\-5\-\[\(6\-fluoro\-pyridine\-3\-carbonyl\)\-amino\]\-pentyl\)\-ureido\)\-pentanedioic\ acid)(?![a-z0-9])",
        "Pinatuzumab vedotin ^89^Zr":               r"(?<![a-z0-9])(pinatuzumab(?:[-\s]?vedotin)?|rg[-\s]?7593|dcdt[-\s]?2980s)(?![a-z0-9])",
        "Pittsburgh compound B C^11^":              r"(?<![a-z0-9])(pittsburgh[-\s]?compound[-\s]?b|pib)(?![a-z0-9])",
        "PK11195 ^11^C":                            r"(?<![a-z0-9])((?:r[-\s]?)?pk[-\s]?11195|1\-\(2\-chlorophenyl\)\-n\-methyl\-n\-\(1\-methylpropyl\)\-3\-isoquinolinecarboxamide)(?![a-z0-9])",
        "Polatuzumab vedotin ^89^Zr":               r"(?<![a-z0-9])(polatuzumab(?:[-\s]?vedotin)?|rg[-\s]?7596|dcds[-\s]?4501a)(?![a-z0-9])",
        "PSMA-1007 F^18^":                          r"(?<![a-z0-9])(psma[-\s]?1007)(?![a-z0-9])",
        "PSMA-11 Ga^68^":                           r"(?<![a-z0-9])(psma[-\s]?11|psma[-\s]?hbed[-\s]?cc|glu[-\s‑]?nh[-\s‑]?co[-\s‑]?nh[-\s‑]?lys\(ahx\)[-\s‑]?hbed[-\s‑]?cc|gozetotide|illuccix|locametz)(?![a-z0-9])",  # psma-hbed-cc, gozetotide, illuccix, locametz: additional
        "PSMA-617 Ga^68^":                          rf"(?<![a-z0-9])({_rp_iso_Ga68}{_rp_sep}(?:ga[-\s]?)?psma[-\s]?617|(?:ga[-\s]?)?psma[-\s]?617{_rp_sep}{_rp_iso_Ga68})(?![a-z0-9])",
        "PTSM Cu^62^":                              r"(?<![a-z0-9])((?:cu[-\s]?)?ptsm)(?![a-z0-9])",
        "R1507 ^89^Zr":                             r"(?<![a-z0-9])(r[-\s]?1507)(?![a-z0-9])",
        "Raclopride C^11^":                         r"(?<![a-z0-9])(raclopride)(?![a-z0-9])",
        "Ranibizumab ^89^Zr":                       r"(?<![a-z0-9])(ranibizumab|lucentis)(?![a-z0-9])",
        "Rituximab ^89^Zr":                         r"(?<![a-z0-9])(rituximab|idec[-\s]?c2b8|rituxan)(?![a-z0-9])",
        "RO5323441 ^89^Zr":                         r"(?<![a-z0-9])(ro[-\s]?5323441)(?![a-z0-9])",
        "RO542908 ^89^Zr":                          r"(?<![a-z0-9])(ro[-\s]?542908)(?![a-z0-9])",
        "RO6924963 ^11^C":                          r"(?<![a-z0-9])(ro[-\s]?6924963|ro[-\s]?963)(?![a-z0-9])",
        "RO6931643 ^11^C":                          r"(?<![a-z0-9])(ro[-\s]?6931643|ro[-\s]?643)(?![a-z0-9])",
        "RO6958948 ^18^F":                          r"(?<![a-z0-9])(ro[-\s]?6958948|ro[-\s]?948)(?![a-z0-9])",
        "Roledumab ^89^Zr":                         r"(?<![a-z0-9])(roledumab|lfb[-\s]?r593)(?![a-z0-9])",
        "Rubidium chloride Rb^82^":                 rf"(?<![a-z0-9])(rubidium(?:[-\s]?chloride)?(?:{_rp_sep}{_rp_iso_Rb82})?|rbcl|{_rp_iso_Rb82}(?:{_rp_sep}(?:rubidium[-\s]?)?chloride)?)(?![a-z0-9])",  # rbcl, rb-82: additional
        "SAR3419 ^89^Zr":                           r"(?<![a-z0-9])(sar[-\s]?3419)(?![a-z0-9])",
        "Sarcosine C^11^":                          r"(?<![a-z0-9])(sarcosine)(?![a-z0-9])",
        "Sodium fluoride F^18^":                    r"(?<![a-z0-9])(sodium[-\s]?fluoride|naf|na[\[(]?18[-\s^]*f[\])]?)(?![a-z0-9])",       # naf, na18f: additional
        "Sodium iodide I^124^":                     rf"(?<![a-z0-9])({_rp_iso_I124}{_rp_sep}(?:sodium[-\s]?iodide|nai)|(?:sodium[-\s]?iodide|nai){_rp_sep}{_rp_iso_I124}|na[\[(]?124[-\s^]*i[\])]?)(?![a-z0-9])",
        "Sodium Na^22^":                            rf"(?<![a-z0-9])(sodium{_rp_sep}{_rp_iso_Na22}|{_rp_iso_Na22}(?:{_rp_sep}sodium)?)(?![a-z0-9])",
        "Spiperone F^18^":                          r"(?<![a-z0-9])(?<!methyl[-\s])(spiperone)(?![a-z0-9])",
        "T807 F^18^":                               r"(?<![a-z0-9])(t[-\s]?807|av[-\s]?1451)(?![a-z0-9])",                      # AV-1451 is also listed for "Flortaucipir F^18^"
        "THK5317 F^18^":                            r"(?<![a-z0-9])(thk[-\s]?5317)(?![a-z0-9])",
        "THK5351 F^18^":                            r"(?<![a-z0-9])(thk[-\s]?5351)(?![a-z0-9])",
        "Trastuzumab ^89^Zr":                       r"(?<![a-z0-9])(trastuzumab|herceptin)(?![a-z0-9])",
        "TRC105 ^89^Zr":                            r"(?<![a-z0-9])(trc[-\s]?105)(?![a-z0-9])",
        "Ublituximab ^89^Zr":                       r"(?<![a-z0-9])(ublituximab|lfb[-\s]?r603|tg[-\s]?1101)(?![a-z0-9])",
        "UCB-J C^11^":                              r"(?<![a-z0-9])(ucb[-\s]?j)(?![a-z0-9])",
        "XmAb5574 ^89^Zr":                          r"(?<![a-z0-9])(xmab[-\s]?5574|mor[-\s]?208)(?![a-z0-9])",

        # Additional PET radiopharmaceuticals: not in DICOM CID 4021, but with a SNOMED CT code
        "Dotatate Cu^64^":                          rf"(?<![a-z0-9])({_rp_iso_Cu64}{_rp_sep}(?:(?:cu[-\s]?)?dota[-\s]?tate)|(?:(?:cu[-\s]?)?dota[-\s]?tate){_rp_sep}{_rp_iso_Cu64}|detectnet)(?![a-z0-9])",  # detectnet: additional
        "FAPI Ga^68^":                              rf"(?<![a-z0-9])({_rp_iso_Ga68}{_rp_sep}(?:(?:ga[-\s]?)?(?:fapi(?:[-\s]?\d+)?|fibroblast[-\s]?activation[-\s]?protein[-\s]?inhibitor))|(?:(?:ga[-\s]?)?(?:fapi(?:[-\s]?\d+)?|fibroblast[-\s]?activation[-\s]?protein[-\s]?inhibitor)){_rp_sep}{_rp_iso_Ga68})(?![a-z0-9])",
        "Pentixafor Ga^68^":                        r"(?<![a-z0-9])(pentixafor|boclatixafortide)(?![a-z0-9])",  # boclatixafortide: INN of pentixafor
    }

    # Dictionary mapping the DICOM PET radiopharmaceutical names to their codes
    # Key: Code Meaning of the radiopharmaceutical in DICOM CID 4021 (the same keys as in pet_radiopharmaceutical_names_2_patterns)
    # Value: Tuple with the Coding Scheme Designator and Code Value of DICOM CID 4021, and the description of the coding scheme:
    #   - SNOMED: SNOMED CT Fully Specified Name (International Edition)
    #   - DCM:  DICOM Code Meaning (DICOM is the coding scheme itself)
    #   - NCIt: NCI Thesaurus preferred name
    #   - UMLS: NCI Metathesaurus (UMLS CUI based) preferred name
    #   - MSH:  MeSH supplementary concept name
    # Note(s):
    #  - The SNOMED CT codes are checked to be a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |.
    #    DICOM codes that are not (mostly "Product containing ... (medicinal product)" concepts) are replaced by their
    #    radioactive isotope substance (the active ingredient of the product), the DICOM code is kept in the comment at the end of the line.
    #  - The Coding Scheme Designators are those of DICOM, except "SNOMED" (as used for SPHN) instead of "SCT" for SNOMED CT.
    #  - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4021.html
    pet_radiopharmaceutical_name_2_code: ClassVar[Mapping[str, tuple[str, str, str]]] = {

        "28H1 ^89^Zr":                              ("DCM",            "126752", "| 28H1 ^89^Zr |"),
        "2FA F^18^":                                ("DCM",            "126713", "| 2FA F^18^ |"),
        "2-Thymidine C^11^":                        ("NCIt",            "C90936", "| 2-(C-11)Thymidine |"),
        "3-N-Methylspiperone C^11^":                ("SNOMED",      "423450009", "| Carbon (11-C) mespiperone (substance) |"),  # Replaced DICOM code 771875003 | Mespiperone (substance) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) | (mespiperone is N-methylspiperone)
        "7D12 ^89^Zr":                              ("DCM",            "126751", "| 7D12 ^89^Zr |"),
        "7E11 ^89^Zr":                              ("DCM",            "126750", "| 7E11 ^89^Zr |"),
        "Acetate C^11^":                            ("SNOMED",      "129513004", "| Carbon (11-C) acetate (substance) |"),
        "AGN-150998 ^89^Zr":                        ("DCM",            "126729", "| AGN-150998 ^89^Zr |"),
        "Ammonia N^13^":                            ("SNOMED",      "129508003", "| Ammonia (13-N) (substance) |"),
        "Anti-B220 ^89^Zr":                         ("DCM",            "126754", "| Anti-B220 ^89^Zr |"),
        "ATSM Cu^60^":                              ("DCM",            "126700", "| ATSM Cu^60^ |"),
        "ATSM Cu^61^":                              ("DCM",            "126701", "| ATSM Cu^61^ |"),
        "ATSM Cu^62^":                              ("DCM",            "126702", "| ATSM Cu^62^ |"),
        "ATSM Cu^64^":                              ("SNOMED",      "423432002", "| Copper (64-Cu) diacetyl-bis N-(4)-methylthiosemicarbazone (substance) |"),  # Replaced DICOM code 422855001 | Product containing copper (64-Cu) diacetyl-bis N-(4)-methylthiosemicarbazone (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "Benralizumab ^89^Zr":                      ("DCM",            "126722", "| Benralizumab ^89^Zr |"),
        "Bevacizumab ^89^Zr":                       ("DCM",            "126516", "| Bevacizumab ^89^Zr |"),
        "Blinatumomab ^89^Zr":                      ("DCM",            "126727", "| Blinatumomab ^89^Zr |"),
        "Brentuximab ^89^Zr":                       ("DCM",            "126735", "| Brentuximab ^89^Zr |"),
        "Butanol O^15^":                            ("SNOMED",      "423025003", "| Oxygen (15-O) butanol (substance) |"),  # Replaced DICOM code 422540000 | Product containing oxygen (15-O) butanol (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "Carbon dioxide O^15^":                     ("SNOMED",      "129507008", "| Oxygen (15-O) carbon dioxide (substance) |"),
        "Carbon monoxide C^11^":                    ("SNOMED",      "129515006", "| Carbon (11-C) carbon monoxide (substance) |"),
        "Carbon monoxide O^15^":                    ("SNOMED",      "129506004", "| Oxygen (15-O) carbon monoxide (substance) |"),
        "Carfentanil C^11^":                        ("SNOMED",      "129511002", "| Carbon (11-C) carfentanil (substance) |"),
        "Cetuximab ^89^Zr":                         ("DCM",            "126513", "| Cetuximab ^89^Zr |"),
        "cG250-F(ab')(2) ^89^Zr":                   ("DCM",            "126517", "| cG250-F(ab')(2) ^89^Zr |"),
        "Choline C^11^":                            ("DCM",            "126703", "| Choline C^11^ |"),
        "CLR1404 I^124^":                           ("DCM",            "126715", "| CLR1404 I^124^ |"),
        "CLR1404 I^131^":                           ("DCM",            "126716", "| CLR1404 I^131^ |"),
        "cMAb U36 ^89^Zr":                          ("DCM",            "126746", "| cMAb U36 ^89^Zr |"),
        "cU36 ^89^Zr":                              ("DCM",            "126515", "| cU36 ^89^Zr |"),
        "DASB C^11^":                               ("MSH",           "C412822", "| 3-amino-4-(2-dimethylaminomethylphenylsulfanyl)benzonitrile |"),
        "DCFBC F^18^":                              ("NCIt",            "C96234", "| Fluorine F 18 DCFBC |"),
        "Df-[FK](2) ^89^Zr":                        ("DCM",            "126762", "| Df-[FK](2) ^89^Zr |"),
        "Df-[FK](2)-3PEG(4) ^89^Zr":                ("DCM",            "126763", "| Df-[FK](2)-3PEG(4) ^89^Zr |"),
        "Df-CD45 ^89^Zr":                           ("DCM",            "126520", "| Df-CD45 ^89^Zr |"),
        "Df-FK ^89^Zr":                             ("DCM",            "126760", "| Df-FK ^89^Zr |"),
        "Df-FK-PEG(3) ^89^Zr":                      ("DCM",            "126761", "| Df-FK-PEG(3) ^89^Zr |"),
        "DN30 ^89^Zr":                              ("DCM",            "126747", "| DN30 ^89^Zr |"),
        "Dotatate Ga^68^":                          ("SNOMED",      "724025002", "| Gallium (68-Ga) dotatate (substance) |"),
        "DPA-713 ^11^C":                            ("DCM",            "126765", "| DPA-713 ^11^C |"),
        "DPA-714 ^18^F":                            ("DCM",            "126766", "| DPA-714 ^18^F |"),
        "E4G10 ^89^Zr":                             ("DCM",            "126519", "| E4G10 ^89^Zr |"),
        "Ecromeximab ^89^Zr":                       ("DCM",            "126732", "| Ecromeximab ^89^Zr |"),
        "Edotreotide Ga^68^":                       ("SNOMED",     "1371422008", "| Gallium (Ga-68) labeled edotreotide (substance) |"),  # Replaced DICOM code UMLS C2713594 | gallium-68 DOTATOC | by the specific SNOMED CT concept (new in the International Edition after 2025-02)
        "EDTA Ga^68^":                              ("SNOMED",      "424729005", "| Gallium (68-Ga) ethylenediamine tetra-acetate (substance) |"),  # Replaced DICOM code 423498000 | Product containing gallium (68-Ga) ethylenediamine tetra-acetate (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "Fallypride C^11^":                         ("DCM",            "126704", "| Fallypride C^11^ |"),
        "Fallypride F^18^":                         ("DCM",            "126705", "| Fallypride F^18^ |"),
        "FLB 457 C^11^":                            ("DCM",            "126706", "| FLB 457 C^11^ |"),
        "Florbetaben F^18^":                        ("SNOMED",      "712736002", "| Florbetaben (18-F) (substance) |"),
        "Florbetapir F^18^":                        ("SNOMED",      "456995000", "| Florbetapir (18-F) (substance) |"),
        "Flortaucipir F^18^":                       ("SNOMED",      "879808000", "| Flortaucipir (18-F) (substance) |"),
        "Flubatine F^18^":                          ("DCM",            "126503", "| Flubatine F^18^ |"),
        "Fluciclatide F^18^":                       ("SNOMED",      "456999006", "| Fluciclatide (18-F) (substance) |"),
        "Fluciclovine F^18^":                       ("SNOMED",      "457000009", "| Fluciclovine (18-F) (substance) |"),
        "Flumazenil C^11^":                         ("SNOMED",      "424554007", "| Carbon (11-C) flumazenil (substance) |"),  # Replaced DICOM code 423543007 | Product containing carbon (11-C) flumazenil (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "Flumazenil F^18^":                         ("SNOMED",      "423577002", "| Flumazenil (18-F) (substance) |"),  # Replaced DICOM code 422975006 | Product containing flumazenil (18-F) (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "Fluorethyltyrosin F^18^":                  ("SNOMED",      "423388007", "| Fluorethyltyrosine (18-F) (substance) |"),  # Replaced DICOM code 424708001 | Product containing fluorethyltyrosine (18-F) (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "Fluoroazomycin arabinoside F^18^":         ("NCIt",            "C62520", "| Fluorine F 18-fluoroazomycin Arabinoside |"),
        "Fluorobenzothiazole F^18^":                ("SNOMED",      "423061008", "| Fluorobenzothiazole (18-F) (substance) |"),  # Replaced DICOM code 423546004 | Product containing fluorobenzothiazole (18-F) (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "Fluorocholine F^18^":                      ("SNOMED",      "456992002", "| Fluorocholine (18-F) (substance) |"),
        "Fluorodeoxyglucose F^18^":                 ("SNOMED",       "35321007", "| Fluorodeoxyglucose (18-F) (substance) |"),
        "Fluoroestradiol F^18^":                    ("SNOMED",      "926372005", "| Fluoroestradiol (18-F) (substance) |"),
        "Fluoroetanidazole F^18^":                  ("UMLS",          "C1541539", "| Fluorine F 18 EF5 |"),
        "Fluoro-L-dopa F^18^":                      ("SNOMED",  "5811000122108", "| Fluorodopa (18-F) (substance) |"),
        "Fluoromethane F^18^":                      ("SNOMED",      "423071005", "| Fluoromethane (18-F) (substance) |"),  # Replaced DICOM code 422763008 | Product containing fluoromethane (18-F) (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "Fluoromisonidazole F^18^":                 ("SNOMED",      "423795001", "| Fluoromisonidazole (18-F) (substance) |"),  # Replaced DICOM code 422598008 | Product containing fluoromisonidazole (18-F) (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "Fluoropropyl-dihydrotetrabenazine F^18^":  ("SNOMED",       "25205007", "| Fluorine radioisotope (substance) |"),  # No specific SNOMED CT concept: replaced the DICOM code UMLS C2934038 | Fluoropropyl-dihydrotetrabenazine F^18^ | (AV-133, retired in the NCI Metathesaurus) by its parent class
        "Fluorothymidine F^18^":                    ("SNOMED",      "764937002", "| Fluorothymidine (18-F) (substance) |"),
        "Fluorotriopride F^18^":                    ("DCM",            "126707", "| Fluorotriopride F^18^ |"),
        "Fluorouracil F^18^":                       ("SNOMED",      "423373002", "| Fluorouracil (18-F) (substance) |"),  # Replaced DICOM code 425236000 | Product containing fluorouracil (18-F) (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "Flurpiridaz F^18^":                        ("DCM",            "126718", "| Flurpiridaz F^18^ |"),
        "Flutemetamol F^18^":                       ("SNOMED",      "456997008", "| Flutemetamol (18-F) (substance) |"),
        "Fresolimumab ^89^Zr":                      ("DCM",            "126748", "| Fresolimumab ^89^Zr |"),
        "GA201 ^89^Zr":                             ("DCM",            "126731", "| GA201 ^89^Zr |"),
        "Germanium Ge^68^":                         ("SNOMED",       "53315004", "| Germanium-68 (substance) |"),
        "Glembatumumab vedotin ^89^Zr":             ("DCM",            "126724", "| Glembatumumab vedotin ^89^Zr |"),
        "Glucose C^11^":                            ("DCM",            "126521", "| Glucose C^11^ |"),
        "Glutamate N^13^":                          ("SNOMED",      "129509006", "| Glutamate (13-N) (substance) |"),
        "Glutamine C^11^":                          ("DCM",            "126709", "| Glutamine C^11^ |"),
        "Glutamine C^14^":                          ("DCM",            "126710", "| Glutamine C^14^ |"),
        "Glutamine F^18^":                          ("DCM",            "126711", "| Glutamine F^18^ |"),
        "ISO-1 F^18^":                              ("UMLS",          "C2981788", "| ISO-1 F^18^ |"),  # UMLS CUI not found in the NCI Metathesaurus (the UMLS API needs a license key), DICOM Code Meaning used as description
        "J591 ^89^Zr":                              ("DCM",            "126514", "| J591 ^89^Zr |"),
        "Margetuximab ^89^Zr":                      ("DCM",            "126740", "| Margetuximab ^89^Zr |"),
        "MEDI-551 ^89^Zr":                          ("DCM",            "126730", "| MEDI-551 ^89^Zr |"),
        "Mespiperone C^11^":                        ("SNOMED",      "423450009", "| Carbon (11-C) mespiperone (substance) |"),  # Replaced DICOM code 424789007 | Product containing carbon (11-C) mespiperone (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "Methionine C^11^":                         ("SNOMED",      "129510001", "| Carbon (11-C) methionine (substance) |"),
        "MK-6240 F^18^":                            ("UMLS",          "C4506764", "| MK-6240 F^18^ |"),  # UMLS CUI not found in the NCI Metathesaurus (the UMLS API needs a license key), DICOM Code Meaning used as description
        "Mogamulizumab ^89^Zr":                     ("DCM",            "126738", "| Mogamulizumab ^89^Zr |"),
        "Monoclonal Antibody ^64^Cu":               ("DCM",            "126510", "| Monoclonal Antibody ^64^Cu |"),
        "Monoclonal Antibody ^89^Zr":               ("DCM",            "126511", "| Monoclonal Antibody ^89^Zr |"),
        "Monoclonal antibody I^124^":               ("SNOMED",      "423249007", "| Iodine (124-I) labeled monoclonal antibody (substance) |"),
        "Nanocolloidal albumin ^89^Zr":             ("DCM",            "126753", "| Nanocolloidal albumin ^89^Zr |"),
        "Nifene F^18^":                             ("DCM",            "126714", "| Nifene F^18^ |"),
        "Obinituzimab ^89^Zr":                      ("DCM",            "126721", "| Obinituzimab ^89^Zr |"),
        "Ocaratuzumab ^89^Zr":                      ("DCM",            "126723", "| Ocaratuzumab ^89^Zr |"),
        "Oxygen O^15^":                             ("SNOMED",      "129504001", "| Oxygen-15 (substance) |"),
        "Oxygen-water O^15^":                       ("SNOMED",      "129505000", "| Oxygen (15-O) water (substance) |"),
        "Palmitate C^11^":                          ("SNOMED",      "129514005", "| Carbon (11-C) palmitate (substance) |"),
        "Panitumumab ^89^Zr":                       ("DCM",            "126736", "| Panitumumab ^89^Zr |"),
        "Pegdinetanib ^89^Zr":                      ("DCM",            "126728", "| Pegdinetanib ^89^Zr |"),
        "Pembrolizumab ^89^Zr":                     ("NCIt",           "C148167", "| Zirconium Zr 89 Pembrolizumab |"),
        "PI-2620 F^18^":                            ("UMLS",          "C5433257", "| PI-2620 F^18^ |"),  # UMLS CUI not found in the NCI Metathesaurus (the UMLS API needs a license key), DICOM Code Meaning used as description
        "Piflufolastat F^18^":                      ("SNOMED",     "1351593009", "| Piflufolastat (18F) (substance) |"),  # Replaced DICOM code NCIt C116352 | Fluorine F 18 Piflufolastat | by the specific SNOMED CT concept
        "Pinatuzumab vedotin ^89^Zr":               ("DCM",            "126725", "| Pinatuzumab vedotin ^89^Zr |"),
        "Pittsburgh compound B C^11^":              ("DCM",            "126500", "| Pittsburgh compound B C^11^ |"),
        "PK11195 ^11^C":                            ("UMLS",          "C1609883", "| (R)-(11C)1-(2-chlorophenyl)-N-methyl-N-(1-methylpropyl)-3-isoquinolinecarboxamide |"),
        "Polatuzumab vedotin ^89^Zr":               ("DCM",            "126726", "| Polatuzumab vedotin ^89^Zr |"),
        "PSMA-1007 F^18^":                          ("DCM",            "126758", "| PSMA-1007 F^18^ |"),
        "PSMA-11 Ga^68^":                           ("SNOMED",     "1371531005", "| Gallium (Ga-68) labeled gozetotide (substance) |"),  # Replaced DICOM code NCIt C118961 | Gallium Ga 68 Gozetotide | by the specific SNOMED CT concept (new in the International Edition after 2025-02)
        "PSMA-617 Ga^68^":                          ("DCM",            "126759", "| PSMA-617 Ga^68^ |"),
        "PTSM Cu^62^":                              ("SNOMED",      "423809007", "| Copper (62-Cu) pyruvaldehyde-bis N-(4)-methyl-thiosemicarbazone (substance) |"),  # Replaced DICOM code 422789008 | Product containing copper (62-Cu) pyruvaldehyde-bis N-(4)-methyl-thiosemicarbazone (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "R1507 ^89^Zr":                             ("DCM",            "126518", "| R1507 ^89^Zr |"),
        "Raclopride C^11^":                         ("SNOMED",      "129512009", "| Carbon (11-C) raclopride (substance) |"),
        "Ranibizumab ^89^Zr":                       ("DCM",            "126742", "| Ranibizumab ^89^Zr |"),
        "Rituximab ^89^Zr":                         ("DCM",            "126737", "| Rituximab ^89^Zr |"),
        "RO5323441 ^89^Zr":                         ("DCM",            "126755", "| RO5323441 ^89^Zr |"),
        "RO542908 ^89^Zr":                          ("DCM",            "126756", "| RO542908 ^89^Zr |"),
        "RO6924963 ^11^C":                          ("DCM",            "126719", "| RO6924963 ^11^C |"),
        "RO6931643 ^11^C":                          ("DCM",            "126720", "| RO6931643 ^11^C |"),
        "RO6958948 ^18^F":                          ("DCM",            "126757", "| RO6958948 ^18^F |"),
        "Roledumab ^89^Zr":                         ("DCM",            "126733", "| Roledumab ^89^Zr |"),
        "Rubidium chloride Rb^82^":                 ("SNOMED",      "129503007", "| Rubidium (82-Rb) chloride (substance) |"),
        "SAR3419 ^89^Zr":                           ("DCM",            "126741", "| SAR3419 ^89^Zr |"),
        "Sarcosine C^11^":                          ("NCIt",           "C122684", "| Carbon C 11 Sarcosine |"),
        "Sodium fluoride F^18^":                    ("SNOMED",      "129501009", "| Sodium fluoride (18-F) (substance) |"),
        "Sodium iodide I^124^":                     ("SNOMED",      "423638007", "| Sodium iodide (124-I) (substance) |"),  # Replaced DICOM code 422980002 | Product containing sodium iodide (124-I) (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "Sodium Na^22^":                            ("SNOMED",       "71633006", "| Sodium-22 (substance) |"),
        "Spiperone F^18^":                          ("SNOMED",      "129499001", "| Spiperone (18-F) (substance) |"),
        "T807 F^18^":                               ("DCM",            "126502", "| T807 F^18^ |"),
        "THK5317 F^18^":                            ("UMLS",          "C4550127", "| THK5317 F^18^ |"),  # UMLS CUI not found in the NCI Metathesaurus (the UMLS API needs a license key), DICOM Code Meaning used as description
        "THK5351 F^18^":                            ("UMLS",          "C4279748", "| 18F-THK5351 |"),
        "Trastuzumab ^89^Zr":                       ("DCM",            "126512", "| Trastuzumab ^89^Zr |"),
        "TRC105 ^89^Zr":                            ("DCM",            "126749", "| TRC105 ^89^Zr |"),
        "Ublituximab ^89^Zr":                       ("DCM",            "126739", "| Ublituximab ^89^Zr |"),
        "UCB-J C^11^":                              ("UMLS",          "C4506788", "| UCB-J C^11^ |"),  # UMLS CUI not found in the NCI Metathesaurus (the UMLS API needs a license key), DICOM Code Meaning used as description
        "XmAb5574 ^89^Zr":                          ("DCM",            "126734", "| XmAb5574 ^89^Zr |"),

        # Additional PET radiopharmaceuticals: not in DICOM CID 4021, but with a SNOMED CT code
        "Dotatate Cu^64^":                          ("SNOMED",      "926371003", "| Copper (64-Cu) dotatate (substance) |"),
        "FAPI Ga^68^":                              ("SNOMED",     "1362094009", "| Gallium (68-Ga) labeled fibroblast activation protein inhibitor (substance) |"),  # New in the SNOMED CT International Edition after 2025-02
        "Pentixafor Ga^68^":                        ("SNOMED",     "1362095005", "| Gallium (68-Ga) labeled boclatixafortide (substance) |"),  # New in the SNOMED CT International Edition after 2025-02
    }

    # Dictionary mapping the DICOM CID 4021 "PET Radiopharmaceutical" codes to the (new) codes used in pet_radiopharmaceutical_name_2_code
    # Key: Tuple with:
    #   - coding scheme designator (e.g.: "SCT")
    #   - code value
    # Value: Tuple with:
    #   - coding scheme designator (e.g.: "SNOMED")
    #   - code value
    #   - human-readable description (e.g.: "| ... (substance) |")
    # Note(s):
    #   - The DICOM Code Meaning is the first comment at the end of the line, the second comment explains a changed code.
    #   - The "coding scheme designator" in DICOM CID 4021 has "SCT" for SNOMED CT codes, which is "SNOMED" for SPHN.
    #   - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4021.html
    dicom_pet_radiopharmaceuticals_coded_2_sphn_coded: ClassVar[Mapping[tuple[str, str], tuple[str, str, str]]] = {
        ("DCM",         "126752"): ("DCM",        "126752", "| 28H1 ^89^Zr |"),                                                                        # 28H1 ^89^Zr
        ("DCM",         "126713"): ("DCM",        "126713", "| 2FA F^18^ |"),                                                                          # 2FA F^18^
        ("NCIt",        "C90936"): ("NCIt",       "C90936", "| 2-(C-11)Thymidine |"),                                                                  # 2-Thymidine C^11^
        ("SCT",      "771875003"): ("SNOMED",  "423450009", "| Carbon (11-C) mespiperone (substance) |"),                                              # 3-N-Methylspiperone C^11^                # Replaced DICOM code 771875003 | Mespiperone (substance) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) | (mespiperone is N-methylspiperone)
        ("DCM",         "126751"): ("DCM",        "126751", "| 7D12 ^89^Zr |"),                                                                        # 7D12 ^89^Zr
        ("DCM",         "126750"): ("DCM",        "126750", "| 7E11 ^89^Zr |"),                                                                        # 7E11 ^89^Zr
        ("SCT",      "129513004"): ("SNOMED",  "129513004", "| Carbon (11-C) acetate (substance) |"),                                                  # Acetate C^11^
        ("DCM",         "126729"): ("DCM",        "126729", "| AGN-150998 ^89^Zr |"),                                                                  # AGN-150998 ^89^Zr
        ("SCT",      "129508003"): ("SNOMED",  "129508003", "| Ammonia (13-N) (substance) |"),                                                         # Ammonia N^13^
        ("DCM",         "126754"): ("DCM",        "126754", "| Anti-B220 ^89^Zr |"),                                                                   # Anti-B220 ^89^Zr
        ("DCM",         "126700"): ("DCM",        "126700", "| ATSM Cu^60^ |"),                                                                        # ATSM Cu^60^
        ("DCM",         "126701"): ("DCM",        "126701", "| ATSM Cu^61^ |"),                                                                        # ATSM Cu^61^
        ("DCM",         "126702"): ("DCM",        "126702", "| ATSM Cu^62^ |"),                                                                        # ATSM Cu^62^
        ("SCT",      "422855001"): ("SNOMED",  "423432002", "| Copper (64-Cu) diacetyl-bis N-(4)-methylthiosemicarbazone (substance) |"),              # ATSM Cu^64^                              # Replaced DICOM code 422855001 | Product containing copper (64-Cu) diacetyl-bis N-(4)-methylthiosemicarbazone (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("DCM",         "126722"): ("DCM",        "126722", "| Benralizumab ^89^Zr |"),                                                                # Benralizumab ^89^Zr
        ("DCM",         "126516"): ("DCM",        "126516", "| Bevacizumab ^89^Zr |"),                                                                 # Bevacizumab ^89^Zr
        ("DCM",         "126727"): ("DCM",        "126727", "| Blinatumomab ^89^Zr |"),                                                                # Blinatumomab ^89^Zr
        ("DCM",         "126735"): ("DCM",        "126735", "| Brentuximab ^89^Zr |"),                                                                 # Brentuximab ^89^Zr
        ("SCT",      "422540000"): ("SNOMED",  "423025003", "| Oxygen (15-O) butanol (substance) |"),                                                  # Butanol O^15^                            # Replaced DICOM code 422540000 | Product containing oxygen (15-O) butanol (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("SCT",      "129507008"): ("SNOMED",  "129507008", "| Oxygen (15-O) carbon dioxide (substance) |"),                                           # Carbon dioxide O^15^
        ("SCT",      "129515006"): ("SNOMED",  "129515006", "| Carbon (11-C) carbon monoxide (substance) |"),                                          # Carbon monoxide C^11^
        ("SCT",      "129506004"): ("SNOMED",  "129506004", "| Oxygen (15-O) carbon monoxide (substance) |"),                                          # Carbon monoxide O^15^
        ("SCT",      "129511002"): ("SNOMED",  "129511002", "| Carbon (11-C) carfentanil (substance) |"),                                              # Carfentanil C^11^
        ("DCM",         "126513"): ("DCM",        "126513", "| Cetuximab ^89^Zr |"),                                                                   # Cetuximab ^89^Zr
        ("DCM",         "126517"): ("DCM",        "126517", "| cG250-F(ab')(2) ^89^Zr |"),                                                             # cG250-F(ab')(2) ^89^Zr
        ("DCM",         "126703"): ("DCM",        "126703", "| Choline C^11^ |"),                                                                      # Choline C^11^
        ("DCM",         "126715"): ("DCM",        "126715", "| CLR1404 I^124^ |"),                                                                     # CLR1404 I^124^
        ("DCM",         "126716"): ("DCM",        "126716", "| CLR1404 I^131^ |"),                                                                     # CLR1404 I^131^
        ("DCM",         "126746"): ("DCM",        "126746", "| cMAb U36 ^89^Zr |"),                                                                    # cMAb U36 ^89^Zr
        ("DCM",         "126515"): ("DCM",        "126515", "| cU36 ^89^Zr |"),                                                                        # cU36 ^89^Zr
        ("MSH",        "C412822"): ("MSH",       "C412822", "| 3-amino-4-(2-dimethylaminomethylphenylsulfanyl)benzonitrile |"),                        # DASB C^11^
        ("NCIt",        "C96234"): ("NCIt",       "C96234", "| Fluorine F 18 DCFBC |"),                                                                # DCFBC F^18^
        ("DCM",         "126762"): ("DCM",        "126762", "| Df-[FK](2) ^89^Zr |"),                                                                  # Df-[FK](2) ^89^Zr
        ("DCM",         "126763"): ("DCM",        "126763", "| Df-[FK](2)-3PEG(4) ^89^Zr |"),                                                          # Df-[FK](2)-3PEG(4) ^89^Zr
        ("DCM",         "126520"): ("DCM",        "126520", "| Df-CD45 ^89^Zr |"),                                                                     # Df-CD45 ^89^Zr
        ("DCM",         "126760"): ("DCM",        "126760", "| Df-FK ^89^Zr |"),                                                                       # Df-FK ^89^Zr
        ("DCM",         "126761"): ("DCM",        "126761", "| Df-FK-PEG(3) ^89^Zr |"),                                                                # Df-FK-PEG(3) ^89^Zr
        ("DCM",         "126747"): ("DCM",        "126747", "| DN30 ^89^Zr |"),                                                                        # DN30 ^89^Zr
        ("SCT",      "724025002"): ("SNOMED",  "724025002", "| Gallium (68-Ga) dotatate (substance) |"),                                               # Dotatate Ga^68^
        ("DCM",         "126765"): ("DCM",        "126765", "| DPA-713 ^11^C |"),                                                                      # DPA-713 ^11^C
        ("DCM",         "126766"): ("DCM",        "126766", "| DPA-714 ^18^F |"),                                                                      # DPA-714 ^18^F
        ("DCM",         "126519"): ("DCM",        "126519", "| E4G10 ^89^Zr |"),                                                                       # E4G10 ^89^Zr
        ("DCM",         "126732"): ("DCM",        "126732", "| Ecromeximab ^89^Zr |"),                                                                 # Ecromeximab ^89^Zr
        ("UMLS",      "C2713594"): ("SNOMED", "1371422008", "| Gallium (Ga-68) labeled edotreotide (substance) |"),                                    # Edotreotide Ga^68^                       # Replaced DICOM code UMLS C2713594 | gallium-68 DOTATOC | by the specific SNOMED CT concept (new in the International Edition after 2025-02)
        ("SCT",      "423498000"): ("SNOMED",  "424729005", "| Gallium (68-Ga) ethylenediamine tetra-acetate (substance) |"),                          # EDTA Ga^68^                              # Replaced DICOM code 423498000 | Product containing gallium (68-Ga) ethylenediamine tetra-acetate (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("DCM",         "126704"): ("DCM",        "126704", "| Fallypride C^11^ |"),                                                                   # Fallypride C^11^
        ("DCM",         "126705"): ("DCM",        "126705", "| Fallypride F^18^ |"),                                                                   # Fallypride F^18^
        ("DCM",         "126706"): ("DCM",        "126706", "| FLB 457 C^11^ |"),                                                                      # FLB 457 C^11^
        ("SCT",      "712736002"): ("SNOMED",  "712736002", "| Florbetaben (18-F) (substance) |"),                                                     # Florbetaben F^18^
        ("SCT",      "456995000"): ("SNOMED",  "456995000", "| Florbetapir (18-F) (substance) |"),                                                     # Florbetapir F^18^
        ("SCT",      "879808000"): ("SNOMED",  "879808000", "| Flortaucipir (18-F) (substance) |"),                                                    # Flortaucipir F^18^
        ("DCM",         "126503"): ("DCM",        "126503", "| Flubatine F^18^ |"),                                                                    # Flubatine F^18^
        ("SCT",      "456999006"): ("SNOMED",  "456999006", "| Fluciclatide (18-F) (substance) |"),                                                    # Fluciclatide F^18^
        ("SCT",      "457000009"): ("SNOMED",  "457000009", "| Fluciclovine (18-F) (substance) |"),                                                    # Fluciclovine F^18^
        ("SCT",      "423543007"): ("SNOMED",  "424554007", "| Carbon (11-C) flumazenil (substance) |"),                                               # Flumazenil C^11^                         # Replaced DICOM code 423543007 | Product containing carbon (11-C) flumazenil (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("SCT",      "422975006"): ("SNOMED",  "423577002", "| Flumazenil (18-F) (substance) |"),                                                      # Flumazenil F^18^                         # Replaced DICOM code 422975006 | Product containing flumazenil (18-F) (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("SCT",      "424708001"): ("SNOMED",  "423388007", "| Fluorethyltyrosine (18-F) (substance) |"),                                              # Fluorethyltyrosin F^18^                  # Replaced DICOM code 424708001 | Product containing fluorethyltyrosine (18-F) (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("NCIt",        "C62520"): ("NCIt",       "C62520", "| Fluorine F 18-fluoroazomycin Arabinoside |"),                                           # Fluoroazomycin arabinoside F^18^
        ("SCT",      "423546004"): ("SNOMED",  "423061008", "| Fluorobenzothiazole (18-F) (substance) |"),                                             # Fluorobenzothiazole F^18^                # Replaced DICOM code 423546004 | Product containing fluorobenzothiazole (18-F) (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("SCT",      "456992002"): ("SNOMED",  "456992002", "| Fluorocholine (18-F) (substance) |"),                                                   # Fluorocholine F^18^
        ("SCT",       "35321007"): ("SNOMED",   "35321007", "| Fluorodeoxyglucose (18-F) (substance) |"),                                              # Fluorodeoxyglucose F^18^
        ("SCT",      "926372005"): ("SNOMED",  "926372005", "| Fluoroestradiol (18-F) (substance) |"),                                                 # Fluoroestradiol F^18^
        ("UMLS",      "C1541539"): ("UMLS",     "C1541539", "| Fluorine F 18 EF5 |"),                                                                  # Fluoroetanidazole F^18^
        ("SCT",  "5811000122108"): ("SNOMED", "5811000122108", "| Fluorodopa (18-F) (substance) |"),                                                   # Fluoro-L-dopa F^18^
        ("SCT",      "422763008"): ("SNOMED",  "423071005", "| Fluoromethane (18-F) (substance) |"),                                                   # Fluoromethane F^18^                      # Replaced DICOM code 422763008 | Product containing fluoromethane (18-F) (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("SCT",      "422598008"): ("SNOMED",  "423795001", "| Fluoromisonidazole (18-F) (substance) |"),                                              # Fluoromisonidazole F^18^                 # Replaced DICOM code 422598008 | Product containing fluoromisonidazole (18-F) (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("UMLS",      "C2934038"): ("SNOMED",   "25205007", "| Fluorine radioisotope (substance) |"),                                                  # Fluoropropyl-dihydrotetrabenazine F^18^  # No specific SNOMED CT concept: replaced the DICOM code UMLS C2934038 | Fluoropropyl-dihydrotetrabenazine F^18^ | (AV-133, retired in the NCI Metathesaurus) by its parent class
        ("SCT",      "764937002"): ("SNOMED",  "764937002", "| Fluorothymidine (18-F) (substance) |"),                                                 # Fluorothymidine F^18^
        ("DCM",         "126707"): ("DCM",        "126707", "| Fluorotriopride F^18^ |"),                                                              # Fluorotriopride F^18^
        ("SCT",      "425236000"): ("SNOMED",  "423373002", "| Fluorouracil (18-F) (substance) |"),                                                    # Fluorouracil F^18^                       # Replaced DICOM code 425236000 | Product containing fluorouracil (18-F) (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("DCM",         "126718"): ("DCM",        "126718", "| Flurpiridaz F^18^ |"),                                                                  # Flurpiridaz F^18^
        ("SCT",      "456997008"): ("SNOMED",  "456997008", "| Flutemetamol (18-F) (substance) |"),                                                    # Flutemetamol F^18^
        ("DCM",         "126748"): ("DCM",        "126748", "| Fresolimumab ^89^Zr |"),                                                                # Fresolimumab ^89^Zr
        ("DCM",         "126731"): ("DCM",        "126731", "| GA201 ^89^Zr |"),                                                                       # GA201 ^89^Zr
        ("SCT",       "53315004"): ("SNOMED",   "53315004", "| Germanium-68 (substance) |"),                                                           # Germanium Ge^68^
        ("DCM",         "126724"): ("DCM",        "126724", "| Glembatumumab vedotin ^89^Zr |"),                                                       # Glembatumumab vedotin ^89^Zr
        ("DCM",         "126521"): ("DCM",        "126521", "| Glucose C^11^ |"),                                                                      # Glucose C^11^
        ("SCT",      "129509006"): ("SNOMED",  "129509006", "| Glutamate (13-N) (substance) |"),                                                       # Glutamate N^13^
        ("DCM",         "126709"): ("DCM",        "126709", "| Glutamine C^11^ |"),                                                                    # Glutamine C^11^
        ("DCM",         "126710"): ("DCM",        "126710", "| Glutamine C^14^ |"),                                                                    # Glutamine C^14^
        ("DCM",         "126711"): ("DCM",        "126711", "| Glutamine F^18^ |"),                                                                    # Glutamine F^18^
        ("UMLS",      "C2981788"): ("UMLS",     "C2981788", "| ISO-1 F^18^ |"),                                                                        # ISO-1 F^18^                              # UMLS CUI not found in the NCI Metathesaurus (the UMLS API needs a license key), DICOM Code Meaning used as description
        ("DCM",         "126514"): ("DCM",        "126514", "| J591 ^89^Zr |"),                                                                        # J591 ^89^Zr
        ("DCM",         "126740"): ("DCM",        "126740", "| Margetuximab ^89^Zr |"),                                                                # Margetuximab ^89^Zr
        ("DCM",         "126730"): ("DCM",        "126730", "| MEDI-551 ^89^Zr |"),                                                                    # MEDI-551 ^89^Zr
        ("SCT",      "424789007"): ("SNOMED",  "423450009", "| Carbon (11-C) mespiperone (substance) |"),                                              # Mespiperone C^11^                        # Replaced DICOM code 424789007 | Product containing carbon (11-C) mespiperone (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("SCT",      "129510001"): ("SNOMED",  "129510001", "| Carbon (11-C) methionine (substance) |"),                                               # Methionine C^11^
        ("UMLS",      "C4506764"): ("UMLS",     "C4506764", "| MK-6240 F^18^ |"),                                                                      # MK-6240 F^18^                            # UMLS CUI not found in the NCI Metathesaurus (the UMLS API needs a license key), DICOM Code Meaning used as description
        ("DCM",         "126738"): ("DCM",        "126738", "| Mogamulizumab ^89^Zr |"),                                                               # Mogamulizumab ^89^Zr
        ("DCM",         "126510"): ("DCM",        "126510", "| Monoclonal Antibody ^64^Cu |"),                                                         # Monoclonal Antibody ^64^Cu
        ("DCM",         "126511"): ("DCM",        "126511", "| Monoclonal Antibody ^89^Zr |"),                                                         # Monoclonal Antibody ^89^Zr
        ("SCT",      "423249007"): ("SNOMED",  "423249007", "| Iodine (124-I) labeled monoclonal antibody (substance) |"),                             # Monoclonal antibody I^124^
        ("DCM",         "126753"): ("DCM",        "126753", "| Nanocolloidal albumin ^89^Zr |"),                                                       # Nanocolloidal albumin ^89^Zr
        ("DCM",         "126714"): ("DCM",        "126714", "| Nifene F^18^ |"),                                                                       # Nifene F^18^
        ("DCM",         "126721"): ("DCM",        "126721", "| Obinituzimab ^89^Zr |"),                                                                # Obinituzimab ^89^Zr
        ("DCM",         "126723"): ("DCM",        "126723", "| Ocaratuzumab ^89^Zr |"),                                                                # Ocaratuzumab ^89^Zr
        ("SCT",      "129504001"): ("SNOMED",  "129504001", "| Oxygen-15 (substance) |"),                                                              # Oxygen O^15^
        ("SCT",      "129505000"): ("SNOMED",  "129505000", "| Oxygen (15-O) water (substance) |"),                                                    # Oxygen-water O^15^
        ("SCT",      "129514005"): ("SNOMED",  "129514005", "| Carbon (11-C) palmitate (substance) |"),                                                # Palmitate C^11^
        ("DCM",         "126736"): ("DCM",        "126736", "| Panitumumab ^89^Zr |"),                                                                 # Panitumumab ^89^Zr
        ("DCM",         "126728"): ("DCM",        "126728", "| Pegdinetanib ^89^Zr |"),                                                                # Pegdinetanib ^89^Zr
        ("NCIt",       "C148167"): ("NCIt",      "C148167", "| Zirconium Zr 89 Pembrolizumab |"),                                                      # Pembrolizumab ^89^Zr
        ("UMLS",      "C5433257"): ("UMLS",     "C5433257", "| PI-2620 F^18^ |"),                                                                      # PI-2620 F^18^                            # UMLS CUI not found in the NCI Metathesaurus (the UMLS API needs a license key), DICOM Code Meaning used as description
        ("NCIt",       "C116352"): ("SNOMED", "1351593009", "| Piflufolastat (18F) (substance) |"),                                                    # Piflufolastat F^18^                      # Replaced DICOM code NCIt C116352 | Fluorine F 18 Piflufolastat | by the specific SNOMED CT concept
        ("DCM",         "126725"): ("DCM",        "126725", "| Pinatuzumab vedotin ^89^Zr |"),                                                         # Pinatuzumab vedotin ^89^Zr
        ("DCM",         "126500"): ("DCM",        "126500", "| Pittsburgh compound B C^11^ |"),                                                        # Pittsburgh compound B C^11^
        ("UMLS",      "C1609883"): ("UMLS",     "C1609883", "| (R)-(11C)1-(2-chlorophenyl)-N-methyl-N-(1-methylpropyl)-3-isoquinolinecarboxamide |"),  # PK11195 ^11^C
        ("DCM",         "126726"): ("DCM",        "126726", "| Polatuzumab vedotin ^89^Zr |"),                                                         # Polatuzumab vedotin ^89^Zr
        ("DCM",         "126758"): ("DCM",        "126758", "| PSMA-1007 F^18^ |"),                                                                    # PSMA-1007 F^18^
        ("NCIt",       "C118961"): ("SNOMED", "1371531005", "| Gallium (Ga-68) labeled gozetotide (substance) |"),                                     # PSMA-11 Ga^68^                           # Replaced DICOM code NCIt C118961 | Gallium Ga 68 Gozetotide | by the specific SNOMED CT concept (new in the International Edition after 2025-02)
        ("DCM",         "126759"): ("DCM",        "126759", "| PSMA-617 Ga^68^ |"),                                                                    # PSMA-617 Ga^68^
        ("SCT",      "422789008"): ("SNOMED",  "423809007", "| Copper (62-Cu) pyruvaldehyde-bis N-(4)-methyl-thiosemicarbazone (substance) |"),        # PTSM Cu^62^                              # Replaced DICOM code 422789008 | Product containing copper (62-Cu) pyruvaldehyde-bis N-(4)-methyl-thiosemicarbazone (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("DCM",         "126518"): ("DCM",        "126518", "| R1507 ^89^Zr |"),                                                                       # R1507 ^89^Zr
        ("SCT",      "129512009"): ("SNOMED",  "129512009", "| Carbon (11-C) raclopride (substance) |"),                                               # Raclopride C^11^
        ("DCM",         "126742"): ("DCM",        "126742", "| Ranibizumab ^89^Zr |"),                                                                 # Ranibizumab ^89^Zr
        ("DCM",         "126737"): ("DCM",        "126737", "| Rituximab ^89^Zr |"),                                                                   # Rituximab ^89^Zr
        ("DCM",         "126755"): ("DCM",        "126755", "| RO5323441 ^89^Zr |"),                                                                   # RO5323441 ^89^Zr
        ("DCM",         "126756"): ("DCM",        "126756", "| RO542908 ^89^Zr |"),                                                                    # RO542908 ^89^Zr
        ("DCM",         "126719"): ("DCM",        "126719", "| RO6924963 ^11^C |"),                                                                    # RO6924963 ^11^C
        ("DCM",         "126720"): ("DCM",        "126720", "| RO6931643 ^11^C |"),                                                                    # RO6931643 ^11^C
        ("DCM",         "126757"): ("DCM",        "126757", "| RO6958948 ^18^F |"),                                                                    # RO6958948 ^18^F
        ("DCM",         "126733"): ("DCM",        "126733", "| Roledumab ^89^Zr |"),                                                                   # Roledumab ^89^Zr
        ("SCT",      "129503007"): ("SNOMED",  "129503007", "| Rubidium (82-Rb) chloride (substance) |"),                                              # Rubidium chloride Rb^82^
        ("DCM",         "126741"): ("DCM",        "126741", "| SAR3419 ^89^Zr |"),                                                                     # SAR3419 ^89^Zr
        ("NCIt",       "C122684"): ("NCIt",      "C122684", "| Carbon C 11 Sarcosine |"),                                                              # Sarcosine C^11^
        ("SCT",      "129501009"): ("SNOMED",  "129501009", "| Sodium fluoride (18-F) (substance) |"),                                                 # Sodium fluoride F^18^
        ("SCT",      "422980002"): ("SNOMED",  "423638007", "| Sodium iodide (124-I) (substance) |"),                                                  # Sodium iodide I^124^                     # Replaced DICOM code 422980002 | Product containing sodium iodide (124-I) (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("SCT",       "71633006"): ("SNOMED",   "71633006", "| Sodium-22 (substance) |"),                                                              # Sodium Na^22^
        ("SCT",      "129499001"): ("SNOMED",  "129499001", "| Spiperone (18-F) (substance) |"),                                                       # Spiperone F^18^
        ("DCM",         "126502"): ("DCM",        "126502", "| T807 F^18^ |"),                                                                         # T807 F^18^
        ("UMLS",      "C4550127"): ("UMLS",     "C4550127", "| THK5317 F^18^ |"),                                                                      # THK5317 F^18^                            # UMLS CUI not found in the NCI Metathesaurus (the UMLS API needs a license key), DICOM Code Meaning used as description
        ("UMLS",      "C4279748"): ("UMLS",     "C4279748", "| 18F-THK5351 |"),                                                                        # THK5351 F^18^
        ("DCM",         "126512"): ("DCM",        "126512", "| Trastuzumab ^89^Zr |"),                                                                 # Trastuzumab ^89^Zr
        ("DCM",         "126749"): ("DCM",        "126749", "| TRC105 ^89^Zr |"),                                                                      # TRC105 ^89^Zr
        ("DCM",         "126739"): ("DCM",        "126739", "| Ublituximab ^89^Zr |"),                                                                 # Ublituximab ^89^Zr
        ("UMLS",      "C4506788"): ("UMLS",     "C4506788", "| UCB-J C^11^ |"),                                                                        # UCB-J C^11^                              # UMLS CUI not found in the NCI Metathesaurus (the UMLS API needs a license key), DICOM Code Meaning used as description
        ("DCM",         "126734"): ("DCM",        "126734", "| XmAb5574 ^89^Zr |"),                                                                    # XmAb5574 ^89^Zr
    }

    # Dictionary mapping the DICOM PET radionuclide names to regex patterns
    # Key: Code Meaning of the radionuclide in DICOM CID 4020 (e.g.: "^18^Fluorine")
    # Value: Regex pattern to match the radionuclide in a DICOM string, e.g.: "F18", "F-18", "18F", "[18F]", "^18^F", "Fluorine-18"
    # Note(s):
    #  - The patterns are intended to be compiled with re.IGNORECASE.
    #  - A radionuclide is also found in most radiopharmaceutical strings, e.g. "18F-FDG" matches both "^18^Fluorine" here
    #    and "Fluorodeoxyglucose F^18^" in pet_radiopharmaceutical_names_2_patterns.
    #    A radiopharmaceutical match should therefore take priority, the radionuclide is the fallback.
    #  - "^15^Oxygen", "^22^Sodium" and "^68^Germanium" have the same SNOMED code as "Oxygen O^15^", "Sodium Na^22^" and
    #    "Germanium Ge^68^" in pet_radiopharmaceutical_names_2_patterns.
    #  - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4020.html
    pet_radionuclide_names_2_patterns: ClassVar[Mapping[str, str]] = {

        "^11^Carbon":                               rf"(?<![a-z0-9])({_rp_iso_C11})(?![a-z0-9])",
        "^13^Nitrogen":                             rf"(?<![a-z0-9])({_rp_iso_N13})(?![a-z0-9])",
        "^14^Oxygen":                               rf"(?<![a-z0-9])({_rp_iso_O14})(?![a-z0-9])",
        "^15^Oxygen":                               rf"(?<![a-z0-9])({_rp_iso_O15})(?![a-z0-9])",
        "^18^Fluorine":                             rf"(?<![a-z0-9])({_rp_iso_F18})(?![a-z0-9])",
        "^22^Sodium":                               rf"(?<![a-z0-9])({_rp_iso_Na22})(?![a-z0-9])",
        "^38^Potassium":                            rf"(?<![a-z0-9])({_rp_iso_K38})(?![a-z0-9])",
        "^43^Scandium":                             rf"(?<![a-z0-9])({_rp_iso_Sc43})(?![a-z0-9])",
        "^44^Scandium":                             rf"(?<![a-z0-9])({_rp_iso_Sc44})(?![a-z0-9])",
        "^45^Titanium":                             rf"(?<![a-z0-9])({_rp_iso_Ti45})(?![a-z0-9])",
        "^51^Manganese":                            rf"(?<![a-z0-9])({_rp_iso_Mn51})(?![a-z0-9])",
        "^52^Iron":                                 rf"(?<![a-z0-9])({_rp_iso_Fe52})(?![a-z0-9])",
        "^52^Manganese":                            rf"(?<![a-z0-9])({_rp_iso_Mn52})(?![a-z0-9])",
        "^52m^Manganese":                           rf"(?<![a-z0-9])({_rp_iso_Mn52m})(?![a-z0-9])",
        "^60^Copper":                               rf"(?<![a-z0-9])({_rp_iso_Cu60})(?![a-z0-9])",
        "^61^Copper":                               rf"(?<![a-z0-9])({_rp_iso_Cu61})(?![a-z0-9])",
        "^62^Copper":                               rf"(?<![a-z0-9])({_rp_iso_Cu62})(?![a-z0-9])",
        "^62^Zinc":                                 rf"(?<![a-z0-9])({_rp_iso_Zn62})(?![a-z0-9])",
        "^64^Copper":                               rf"(?<![a-z0-9])({_rp_iso_Cu64})(?![a-z0-9])",
        "^66^Gallium":                              rf"(?<![a-z0-9])({_rp_iso_Ga66})(?![a-z0-9])",
        "^68^Gallium":                              rf"(?<![a-z0-9])({_rp_iso_Ga68})(?![a-z0-9])",
        "^68^Germanium":                            rf"(?<![a-z0-9])({_rp_iso_Ge68})(?![a-z0-9])",
        "^70^Arsenic":                              rf"(?<![a-z0-9])({_rp_iso_As70})(?![a-z0-9])",
        "^72^Arsenic":                              rf"(?<![a-z0-9])({_rp_iso_As72})(?![a-z0-9])",
        "^73^Selenium":                             rf"(?<![a-z0-9])({_rp_iso_Se73})(?![a-z0-9])",
        "^75^Bromine":                              rf"(?<![a-z0-9])({_rp_iso_Br75})(?![a-z0-9])",
        "^76^Bromine":                              rf"(?<![a-z0-9])({_rp_iso_Br76})(?![a-z0-9])",
        "^77^Bromine":                              rf"(?<![a-z0-9])({_rp_iso_Br77})(?![a-z0-9])",
        "^82^Rubidium":                             rf"(?<![a-z0-9])({_rp_iso_Rb82})(?![a-z0-9])",
        "^86^Yttrium":                              rf"(?<![a-z0-9])({_rp_iso_Y86})(?![a-z0-9])",
        "^89^Zirconium":                            rf"(?<![a-z0-9])({_rp_iso_Zr89})(?![a-z0-9])",
        "^90^Niobium":                              rf"(?<![a-z0-9])({_rp_iso_Nb90})(?![a-z0-9])",
        "^90^Yttrium":                              rf"(?<![a-z0-9])({_rp_iso_Y90})(?![a-z0-9])",
        "^94m^Technetium":                          rf"(?<![a-z0-9])({_rp_iso_Tc94m})(?![a-z0-9])",
        "^124^Iodine":                              rf"(?<![a-z0-9])({_rp_iso_I124})(?![a-z0-9])",
        "^152^Terbium":                             rf"(?<![a-z0-9])({_rp_iso_Tb152})(?![a-z0-9])",
    }

    # Dictionary mapping the DICOM PET radionuclide names to their codes
    # Key: Code Meaning of the radionuclide in DICOM CID 4020 (the same keys as in pet_radionuclide_names_2_patterns)
    # Value: Tuple with the Coding Scheme Designator and Code Value of DICOM CID 4020, and the description of the coding scheme:
    #   - SNOMED: SNOMED CT Fully Specified Name (International Edition)
    #   - DCM:  DICOM Code Meaning (DICOM is the coding scheme itself)
    # Note(s):
    #  - The SNOMED CT codes are checked to be a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |,
    #    if not, a comment is added at the end of the line.
    #  - The Coding Scheme Designators are those of DICOM, except "SNOMED" (as used for SPHN) instead of "SCT" for SNOMED CT.
    #  - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4020.html
    pet_radionuclide_name_2_code: ClassVar[Mapping[str, tuple[str, str, str]]] = {

        "^11^Carbon":                               ("SNOMED",  "40565003", "| Carbon-11 (substance) |"),
        "^13^Nitrogen":                             ("SNOMED",  "21576001", "| Nitrogen-13 (substance) |"),
        "^14^Oxygen":                               ("SNOMED", "424875009", "| Oxygen-14 (substance) |"),
        "^15^Oxygen":                               ("SNOMED", "129504001", "| Oxygen-15 (substance) |"),
        "^18^Fluorine":                             ("SNOMED",  "77004003", "| Fluorine-18 (substance) |"),
        "^22^Sodium":                               ("SNOMED",  "71633006", "| Sodium-22 (substance) |"),
        "^38^Potassium":                            ("SNOMED", "423764008", "| Potassium-38 (substance) |"),
        "^43^Scandium":                             ("DCM",       "126605", "| ^43^Scandium |"),
        "^44^Scandium":                             ("DCM",       "126600", "| ^44^Scandium |"),
        "^45^Titanium":                             ("SNOMED",  "75696008", "| Titanium-45 (substance) |"),
        "^51^Manganese":                            ("DCM",       "126601", "| ^51^Manganese |"),
        "^52^Iron":                                 ("SNOMED",  "69089000", "| Iron-52 (substance) |"),
        "^52^Manganese":                            ("SNOMED",  "37225000", "| Manganese-52 (substance) |"),
        "^52m^Manganese":                           ("DCM",       "126607", "| ^52m^Manganese |"),
        "^60^Copper":                               ("SNOMED", "425364008", "| Copper-60 (substance) |"),
        "^61^Copper":                               ("SNOMED",  "71425003", "| Copper-61 (substance) |"),
        "^62^Copper":                               ("SNOMED", "422934004", "| Copper-62 (substance) |"),
        "^62^Zinc":                                 ("SNOMED",  "65054007", "| Zinc-62 (substance) |"),
        "^64^Copper":                               ("SNOMED",   "3932008", "| Copper-64 (substance) |"),
        "^66^Gallium":                              ("SNOMED",  "79477007", "| Gallium-66 (substance) |"),
        "^68^Gallium":                              ("SNOMED",  "35337001", "| Gallium-68 (substance) |"),
        "^68^Germanium":                            ("SNOMED",  "53315004", "| Germanium-68 (substance) |"),
        "^70^Arsenic":                              ("DCM",       "126602", "| ^70^Arsenic |"),
        "^72^Arsenic":                              ("SNOMED",   "2705002", "| Arsenic-72 (substance) |"),
        "^73^Selenium":                             ("SNOMED",  "87437000", "| Selenium-73 (substance) |"),
        "^75^Bromine":                              ("SNOMED",  "17910003", "| Bromine-75 (substance) |"),
        "^76^Bromine":                              ("SNOMED",  "79523006", "| Bromine-76 (substance) |"),
        "^77^Bromine":                              ("SNOMED",  "86521004", "| Bromine-77 (substance) |"),
        "^82^Rubidium":                             ("SNOMED",  "79197006", "| Rubidium-82 (substance) |"),
        "^86^Yttrium":                              ("SNOMED",  "10738001", "| Yttrium-86 (substance) |"),
        "^89^Zirconium":                            ("SNOMED",  "63360001", "| Zirconium-89 (substance) |"),
        "^90^Niobium":                              ("DCM",       "126603", "| ^90^Niobium |"),
        "^90^Yttrium":                              ("SNOMED",  "14691008", "| Yttrium-90 (substance) |"),
        "^94m^Technetium":                          ("SNOMED", "424079002", "| Technetium-94m (substance) |"),
        "^124^Iodine":                              ("SNOMED",  "40937006", "| Iodine-124 (substance) |"),
        "^152^Terbium":                             ("DCM",       "126606", "| ^152^Terbium |"),
    }

    # Dictionary mapping the DICOM CID 4020 "PET Radionuclide" codes to the (new) codes used in pet_radionuclide_name_2_code
    # Key: Tuple with:
    #   - coding scheme designator (e.g.: "SCT")
    #   - code value
    # Value: Tuple with:
    #   - coding scheme designator (e.g.: "SNOMED")
    #   - code value
    #   - human-readable description (e.g.: "| ... (substance) |")
    # Note(s):
    #   - The DICOM Code Meaning is the first comment at the end of the line, the second comment explains a changed code.
    #   - The "coding scheme designator" in DICOM CID 4020 has "SCT" for SNOMED CT codes, which is "SNOMED" for SPHN.
    #   - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_4020.html
    dicom_pet_radionuclides_coded_2_sphn_coded: ClassVar[Mapping[tuple[str, str], tuple[str, str, str]]] = {
        ("SCT",   "40565003"): ("SNOMED",   "40565003", "| Carbon-11 (substance) |"),       # ^11^Carbon
        ("SCT",   "21576001"): ("SNOMED",   "21576001", "| Nitrogen-13 (substance) |"),     # ^13^Nitrogen
        ("SCT",  "424875009"): ("SNOMED",  "424875009", "| Oxygen-14 (substance) |"),       # ^14^Oxygen
        ("SCT",  "129504001"): ("SNOMED",  "129504001", "| Oxygen-15 (substance) |"),       # ^15^Oxygen
        ("SCT",   "77004003"): ("SNOMED",   "77004003", "| Fluorine-18 (substance) |"),     # ^18^Fluorine
        ("SCT",   "71633006"): ("SNOMED",   "71633006", "| Sodium-22 (substance) |"),       # ^22^Sodium
        ("SCT",  "423764008"): ("SNOMED",  "423764008", "| Potassium-38 (substance) |"),    # ^38^Potassium
        ("DCM",     "126605"): ("DCM",        "126605", "| ^43^Scandium |"),                # ^43^Scandium
        ("DCM",     "126600"): ("DCM",        "126600", "| ^44^Scandium |"),                # ^44^Scandium
        ("SCT",   "75696008"): ("SNOMED",   "75696008", "| Titanium-45 (substance) |"),     # ^45^Titanium
        ("DCM",     "126601"): ("DCM",        "126601", "| ^51^Manganese |"),               # ^51^Manganese
        ("SCT",   "69089000"): ("SNOMED",   "69089000", "| Iron-52 (substance) |"),         # ^52^Iron
        ("SCT",   "37225000"): ("SNOMED",   "37225000", "| Manganese-52 (substance) |"),    # ^52^Manganese
        ("DCM",     "126607"): ("DCM",        "126607", "| ^52m^Manganese |"),              # ^52m^Manganese
        ("SCT",  "425364008"): ("SNOMED",  "425364008", "| Copper-60 (substance) |"),       # ^60^Copper
        ("SCT",   "71425003"): ("SNOMED",   "71425003", "| Copper-61 (substance) |"),       # ^61^Copper
        ("SCT",  "422934004"): ("SNOMED",  "422934004", "| Copper-62 (substance) |"),       # ^62^Copper
        ("SCT",   "65054007"): ("SNOMED",   "65054007", "| Zinc-62 (substance) |"),         # ^62^Zinc
        ("SCT",    "3932008"): ("SNOMED",    "3932008", "| Copper-64 (substance) |"),       # ^64^Copper
        ("SCT",   "79477007"): ("SNOMED",   "79477007", "| Gallium-66 (substance) |"),      # ^66^Gallium
        ("SCT",   "35337001"): ("SNOMED",   "35337001", "| Gallium-68 (substance) |"),      # ^68^Gallium
        ("SCT",   "53315004"): ("SNOMED",   "53315004", "| Germanium-68 (substance) |"),    # ^68^Germanium
        ("DCM",     "126602"): ("DCM",        "126602", "| ^70^Arsenic |"),                 # ^70^Arsenic
        ("SCT",    "2705002"): ("SNOMED",    "2705002", "| Arsenic-72 (substance) |"),      # ^72^Arsenic
        ("SCT",   "87437000"): ("SNOMED",   "87437000", "| Selenium-73 (substance) |"),     # ^73^Selenium
        ("SCT",   "17910003"): ("SNOMED",   "17910003", "| Bromine-75 (substance) |"),      # ^75^Bromine
        ("SCT",   "79523006"): ("SNOMED",   "79523006", "| Bromine-76 (substance) |"),      # ^76^Bromine
        ("SCT",   "86521004"): ("SNOMED",   "86521004", "| Bromine-77 (substance) |"),      # ^77^Bromine
        ("SCT",   "79197006"): ("SNOMED",   "79197006", "| Rubidium-82 (substance) |"),     # ^82^Rubidium
        ("SCT",   "10738001"): ("SNOMED",   "10738001", "| Yttrium-86 (substance) |"),      # ^86^Yttrium
        ("SCT",   "63360001"): ("SNOMED",   "63360001", "| Zirconium-89 (substance) |"),    # ^89^Zirconium
        ("DCM",     "126603"): ("DCM",        "126603", "| ^90^Niobium |"),                 # ^90^Niobium
        ("SCT",   "14691008"): ("SNOMED",   "14691008", "| Yttrium-90 (substance) |"),      # ^90^Yttrium
        ("SCT",  "424079002"): ("SNOMED",  "424079002", "| Technetium-94m (substance) |"),  # ^94m^Technetium
        ("SCT",   "40937006"): ("SNOMED",   "40937006", "| Iodine-124 (substance) |"),      # ^124^Iodine
        ("DCM",     "126606"): ("DCM",        "126606", "| ^152^Terbium |"),                # ^152^Terbium
    }

    # Dictionary mapping the codes of the PET radionuclides of DICOM CID 4020 to their half-life and positron fraction
    # Key: Tuple with the coding scheme designator and code value as used in pet_radionuclide_name_2_code (e.g.: ("SNOMED", "77004003"))
    # Value: Tuple with:
    #   - half-life in seconds, as in DICOM Radionuclide Half Life (0018,1075)
    #   - positron fraction (0..1), as in DICOM Radionuclide Positron Fraction (0018,1076): the sum of the beta+ intensities per decay
    #     (positron emission only, e.g. 0.0 for Y-90, whose positrons come from internal pair production (about 3.2e-5))
    # Note(s):
    #  - Source: IAEA Nuclear Data Section, LiveChart of Nuclides (evaluated ENSDF data), https://nds.iaea.org/relnsd/v1/data
    #  - For the metastable radionuclides (e.g. "^99m^Technetium") the values are those of the lowest long-lived isomeric state.
    #  - The comment at the end of the line gives the DICOM Code Meaning, the half-life in its common unit, and the decay mode(s).
    pet_radionuclide_coded_2_half_life_and_positron_fraction: ClassVar[Mapping[tuple[str, str], tuple[float, float]]] = {
        ("SNOMED",    "40565003"): (1221.84, 0.997669),    # ^11^Carbon 20.364 min (EC+B+ 100%)
        ("SNOMED",    "21576001"): (597.504, 0.99803),     # ^13^Nitrogen 9.9584 min (EC+B+ 100%)
        ("SNOMED",   "424875009"): (70.606, 0.99878),      # ^14^Oxygen 70.606 s (EC+B+ 100%)
        ("SNOMED",   "129504001"): (122.24, 0.999003),     # ^15^Oxygen 122.24 s (EC+B+ 100%)
        ("SNOMED",    "77004003"): (6586.2, 0.9673),       # ^18^Fluorine 109.77 min (EC+B+ 100%)
        ("SNOMED",    "71633006"): (82104810.0, 0.89955),  # ^22^Sodium 2.6018 y (EC+B+ 100%)
        ("SNOMED",   "423764008"): (459.06, 0.996002),     # ^38^Potassium 7.651 min (EC+B+ 100%)
        ("DCM",         "126605"): (14007.6, 0.881),       # ^43^Scandium 3.891 h (EC+B+ 100%)
        ("DCM",         "126600"): (14551.2, 0.94278),     # ^44^Scandium 4.0420 h (EC+B+ 100%)
        ("SNOMED",    "75696008"): (11088.0, 0.84819),     # ^45^Titanium 184.8 min (EC+B+ 100%)
        ("DCM",         "126601"): (2772.0, 0.97089),      # ^51^Manganese 46.2 min (EC+B+ 100%)
        ("SNOMED",    "69089000"): (29790.0, 0.5549),      # ^52^Iron 8.275 h (EC+B+ 100%)
        ("SNOMED",    "37225000"): (483062.4, 0.294012),   # ^52^Manganese 5.591 d (EC+B+ 100%)
        ("DCM",         "126607"): (1266.0, 0.966117),     # ^52m^Manganese 21.1 min (EC+B+ 98.22%, IT 1.78%)
        ("SNOMED",   "425364008"): (1422.0, 0.925967),     # ^60^Copper 23.7 min (EC+B+ 100%)
        ("SNOMED",    "71425003"): (12020.4, 0.61433),     # ^61^Copper 3.339 h (EC+B+ 100%)
        ("SNOMED",   "422934004"): (580.32, 0.97781),      # ^62^Copper 9.672 min (EC+B+ 100%)
        ("SNOMED",    "65054007"): (33109.2, 0.084),       # ^62^Zinc 9.197 h (EC+B+ 100%)
        ("SNOMED",     "3932008"): (45722.16, 0.1749),     # ^64^Copper 12.7006 h (EC+B+ 61.5%, B- 38.5%)
        ("SNOMED",    "79477007"): (34164.0, 0.568078),    # ^66^Gallium 9.49 h (EC+B+ 100%)
        ("SNOMED",    "35337001"): (4062.6, 0.889103),     # ^68^Gallium 67.71 min (EC+B+ 100%)
        ("SNOMED",    "53315004"): (23408352.0, 0.0),      # ^68^Germanium 270.93 d (EC 100%)
        ("DCM",         "126602"): (3156.0, 0.90792),      # ^70^Arsenic 52.6 min (EC+B+ 100%)
        ("SNOMED",     "2705002"): (93600.0, 0.878512),    # ^72^Arsenic 26.0 h (EC+B+ 100%)
        ("SNOMED",    "87437000"): (25740.0, 0.645852),    # ^73^Selenium 7.15 h (EC+B+ 100%)
        ("SNOMED",    "17910003"): (5802.0, 0.74618),      # ^75^Bromine 96.7 min (EC+B+ 100%)
        ("SNOMED",    "79523006"): (58104.0, 0.470017),    # ^76^Bromine 16.14 h (EC+B+ 100%)
        ("SNOMED",    "86521004"): (205344.0, 0.007318),   # ^77^Bromine 57.04 h (EC+B+ 100%)
        ("SNOMED",    "79197006"): (75.45, 0.953619),      # ^82^Rubidium 1.2575 min (EC+B+ 100%)
        ("SNOMED",    "10738001"): (53064.0, 0.282196),    # ^86^Yttrium 14.74 h (EC+B+ 100%)
        ("SNOMED",    "63360001"): (282276.0, 0.2274),     # ^89^Zirconium 78.41 h (EC+B+ 100%)
        ("DCM",         "126603"): (52560.0, 0.550547),    # ^90^Niobium 14.60 h (EC+B+ 100%)
        ("SNOMED",    "14691008"): (230580.0, 0.0),        # ^90^Yttrium 64.05 h (B- 100%)
        ("SNOMED",   "424079002"): (3120.0, 0.701527),     # ^94m^Technetium 52.0 min (EC+B+ 100%, IT 0.1%)
        ("SNOMED",    "40937006"): (360806.4, 0.226938),   # ^124^Iodine 4.1760 d (EC+B+ 100%)
        ("DCM",         "126606"): (63000.0, 0.202739),    # ^152^Terbium 17.5 h (EC+B+ 100%, A 0.0000007%)
    }

    # Dictionary mapping the DICOM NM/SPECT radiopharmaceutical names to regex patterns
    # Key: Code Meaning of the radiopharmaceutical in DICOM CID 25 (e.g.: "Technetium Tc^99m^ sestamibi")
    # Value: Regex pattern to match the "Code Meaning" and the "Trade name" in a DICOM string (e.g. Radiopharmaceutical (0018,0031))
    # Note(s):
    #  - The patterns are intended to be compiled with re.IGNORECASE.
    #  - The radionuclide is required next to the name (before or after it), when the name is not specific for one
    #    radiopharmaceutical, e.g. "Indium^111^ pentetate", "Indium^113m^ pentetate", "Technetium Tc^99m^ pentetate".
    #    Otherwise, the name alone is sufficient, e.g. "Technetium Tc^99m^ sestamibi".
    #  - Names marked "additional" are not listed in DICOM CID 25 but are common names, abbreviations or trade names.
    #  - DICOM CID 25 also contains two PET radiopharmaceuticals: "Fluorodeoxyglucose F^18^" and "Sodium fluoride F^18^".
    #  - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_25.html
    nm_spect_radiopharmaceutical_names_2_patterns: ClassVar[Mapping[str, str]] = {

        "Carbon^14^ D-xylose":                      rf"(?<![a-z0-9])({_rp_iso_C14}{_rp_sep}(?:(?:d[-\s]?)?xylose)|(?:(?:d[-\s]?)?xylose){_rp_sep}{_rp_iso_C14})(?![a-z0-9])",
        "Carbon^14^ triolein":                      rf"(?<![a-z0-9])({_rp_iso_C14}{_rp_sep}(?:triolein)|(?:triolein){_rp_sep}{_rp_iso_C14})(?![a-z0-9])",
        "Chromic phosphate P^32^":                  rf"(?<![a-z0-9])({_rp_iso_P32}{_rp_sep}(?:chromic[-\s]?phosphate)|(?:chromic[-\s]?phosphate){_rp_sep}{_rp_iso_P32})(?![a-z0-9])",
        "Chromium^51^ albumin":                     rf"(?<![a-z0-9])({_rp_iso_Cr51}{_rp_sep}(?:(?:(?:human[-\s]?)?serum[-\s]?)?albumin)|(?:(?:(?:human[-\s]?)?serum[-\s]?)?albumin){_rp_sep}{_rp_iso_Cr51})(?![a-z0-9])",
        "Chromium^51^ chloride":                    rf"(?<![a-z0-9])({_rp_iso_Cr51}{_rp_sep}(?:(?:chrom(?:ic|ium)[-\s]?)?chloride)|(?:(?:chrom(?:ic|ium)[-\s]?)?chloride){_rp_sep}{_rp_iso_Cr51})(?![a-z0-9])",
        "Copper^64^ acetate":                       rf"(?<![a-z0-9])({_rp_iso_Cu64}{_rp_sep}(?:(?:copper[-\s]?)?acetate)|(?:(?:copper[-\s]?)?acetate){_rp_sep}{_rp_iso_Cu64})(?![a-z0-9])",
        "Copper^64^ versenate":                     rf"(?<![a-z0-9])({_rp_iso_Cu64}{_rp_sep}(?:(?:copper[-\s]?)?(?:versenate|edta))|(?:(?:copper[-\s]?)?(?:versenate|edta)){_rp_sep}{_rp_iso_Cu64})(?![a-z0-9])",
        "Copper^67^ ceruloplasmin":                 rf"(?<![a-z0-9])({_rp_iso_Cu67}{_rp_sep}(?:ceruloplasmin)|(?:ceruloplasmin){_rp_sep}{_rp_iso_Cu67})(?![a-z0-9])",
        "Cyanocobalamin Co^57^":                    rf"(?<![a-z0-9])({_rp_iso_Co57}{_rp_sep}(?:cyanocobalamin|vitamin[-\s]?b[-\s]?12)|(?:cyanocobalamin|vitamin[-\s]?b[-\s]?12){_rp_sep}{_rp_iso_Co57})(?![a-z0-9])",
        "Cyanocobalamin Co^58^":                    rf"(?<![a-z0-9])({_rp_iso_Co58}{_rp_sep}(?:cyanocobalamin|vitamin[-\s]?b[-\s]?12)|(?:cyanocobalamin|vitamin[-\s]?b[-\s]?12){_rp_sep}{_rp_iso_Co58})(?![a-z0-9])",
        "Cyanocobalamin Co^60^":                    rf"(?<![a-z0-9])({_rp_iso_Co60}{_rp_sep}(?:cyanocobalamin|vitamin[-\s]?b[-\s]?12)|(?:cyanocobalamin|vitamin[-\s]?b[-\s]?12){_rp_sep}{_rp_iso_Co60})(?![a-z0-9])",
        "Diagnostic radioisotope":                  r"(?<![a-z0-9])(diagnostic[-\s]?radio[-\s]?(?:isotope|nuclide|pharmaceutical)s?)(?![a-z0-9])",
        "Ferrous chloride Fe^59^":                  rf"(?<![a-z0-9])({_rp_iso_Fe59}{_rp_sep}(?:ferrous[-\s]?chloride)|(?:ferrous[-\s]?chloride){_rp_sep}{_rp_iso_Fe59})(?![a-z0-9])",
        "Ferrous citrate Fe^59^":                   rf"(?<![a-z0-9])({_rp_iso_Fe59}{_rp_sep}(?:ferrous[-\s]?citrate)|(?:ferrous[-\s]?citrate){_rp_sep}{_rp_iso_Fe59})(?![a-z0-9])",
        "Ferrous sulfate Fe^59^":                   rf"(?<![a-z0-9])({_rp_iso_Fe59}{_rp_sep}(?:ferrous[-\s]?sul(?:ph|f)ate)|(?:ferrous[-\s]?sul(?:ph|f)ate){_rp_sep}{_rp_iso_Fe59})(?![a-z0-9])",
        "Fibrinogen I^123^":                        rf"(?<![a-z0-9])({_rp_iso_I123}{_rp_sep}(?:fibrinogen)|(?:fibrinogen){_rp_sep}{_rp_iso_I123})(?![a-z0-9])",
        "Fluorodeoxyglucose F^18^":                 rf"(?<![a-z0-9])(fluoro[-\s]?(?:2[-\s]?)?deoxy[-\s]?(?:d[-\s]?)?glucose|(?:2[-\s]?)?deoxy[-\s]?(?:2[-\s]?)?(?:{_rp_iso_F18}[-\s]?)?fluoro[-\s]?(?:d[-\s]?)?glucose|fludeoxyglucose|(?:18[-\s]?)?fdg)(?![a-z0-9])",  # fludeoxyglucose (INN), fdg: additional
        "Gallium^67^ citrate":                      rf"(?<![a-z0-9])({_rp_iso_Ga67}{_rp_sep}(?:(?:gallium[-\s]?)?citrate)|(?:(?:gallium[-\s]?)?citrate){_rp_sep}{_rp_iso_Ga67})(?![a-z0-9])",
        "Indium^111^-Fe(OH) >3<":                   rf"(?<![a-z0-9])({_rp_iso_In111}{_rp_sep}(?:fe[-\s]?\(oh\)[-\s]?>?3<?|iron[-\s]?hydroxide)|(?:fe[-\s]?\(oh\)[-\s]?>?3<?|iron[-\s]?hydroxide){_rp_sep}{_rp_iso_In111})(?![a-z0-9])",
        "Indium^111^oxyquinoline":                  rf"(?<![a-z0-9])({_rp_iso_In111}{_rp_sep}(?:oxy[-\s]?quinoline|oxine|8[-\s]?hydroxy[-\s]?quinoline)|(?:oxy[-\s]?quinoline|oxine|8[-\s]?hydroxy[-\s]?quinoline){_rp_sep}{_rp_iso_In111})(?![a-z0-9])",  # oxine: additional
        "Indium^111^ pentetate":                    rf"(?<![a-z0-9])({_rp_iso_In111}{_rp_sep}(?:pentetate|dtpa(?![-\s]?octreotide))|(?:pentetate|dtpa(?![-\s]?octreotide)){_rp_sep}{_rp_iso_In111})(?![a-z0-9])",
        "Indium^111^ red cell label":               rf"(?<![a-z0-9])({_rp_iso_In111}{_rp_sep}(?:(?:labell?ed[-\s]?)?(?:red[-\s]?(?:blood[-\s]?)?cells?|rbcs?)(?:[-\s]?label(?:l?ed|l?ing)?)?)|(?:(?:labell?ed[-\s]?)?(?:red[-\s]?(?:blood[-\s]?)?cells?|rbcs?)(?:[-\s]?label(?:l?ed|l?ing)?)?){_rp_sep}{_rp_iso_In111})(?![a-z0-9])",
        "Indium^111^ transferrin":                  rf"(?<![a-z0-9])({_rp_iso_In111}{_rp_sep}(?:transferrin)|(?:transferrin){_rp_sep}{_rp_iso_In111})(?![a-z0-9])",
        "Indium^111 Capromab Pendetide":            r"(?<![a-z0-9])(capromab(?:[-\s]?pendetide)?|prosta[-\s]?scint)(?![a-z0-9])",
        "Indium^111 Chloride":                      rf"(?<![a-z0-9])({_rp_iso_In111}{_rp_sep}(?:(?:indium[-\s]?)?chloride)|(?:(?:indium[-\s]?)?chloride){_rp_sep}{_rp_iso_In111})(?![a-z0-9])",  # Zevalin (trade name in CID 25) not used, as it is also the Y-90 therapy
        "Indium^111 Pentetreotide":                 r"(?<![a-z0-9])(pentetreotide|octreoscan|dtpa[-\s]?octreotide)(?![a-z0-9])",  # dtpa-octreotide: additional
        "Indium^113m^ bleomycin":                   rf"(?<![a-z0-9])({_rp_iso_In113m}{_rp_sep}(?:bleomycin)|(?:bleomycin){_rp_sep}{_rp_iso_In113m})(?![a-z0-9])",
        "Indium^113m^ chloride":                    rf"(?<![a-z0-9])({_rp_iso_In113m}{_rp_sep}(?:(?:indium[-\s]?)?chloride)|(?:(?:indium[-\s]?)?chloride){_rp_sep}{_rp_iso_In113m})(?![a-z0-9])",
        "Indium^113m^ pentetate":                   rf"(?<![a-z0-9])({_rp_iso_In113m}{_rp_sep}(?:pentetate|dtpa(?![-\s]?octreotide))|(?:pentetate|dtpa(?![-\s]?octreotide)){_rp_sep}{_rp_iso_In113m})(?![a-z0-9])",
        "Iodinated I^125^ albumin":                 rf"(?<![a-z0-9])({_rp_iso_I125}{_rp_sep}(?:(?<!serum[-\s])(?<!aggregated[-\s])(?:iodinated[-\s]?)?albumin)|(?:(?<!serum[-\s])(?<!aggregated[-\s])(?:iodinated[-\s]?)?albumin){_rp_sep}{_rp_iso_I125})(?![a-z0-9])",
        "Iodinated I^125^ DPA-713":                 rf"(?<![a-z0-9])({_rp_iso_I125}{_rp_sep}(?:dpa[-\s]?713)|(?:dpa[-\s]?713){_rp_sep}{_rp_iso_I125})(?![a-z0-9])",
        "Iodinated I^125^ human serum albumin":     rf"(?<![a-z0-9])({_rp_iso_I125}{_rp_sep}(?:(?:iodinated[-\s]?)?(?:human[-\s]?)?serum[-\s]?albumin|i?hsa)|(?:(?:iodinated[-\s]?)?(?:human[-\s]?)?serum[-\s]?albumin|i?hsa){_rp_sep}{_rp_iso_I125})(?![a-z0-9])",
        "Iodinated I^125^ povidone":                rf"(?<![a-z0-9])({_rp_iso_I125}{_rp_sep}(?:povidone|polyvinyl[-\s]?pyrrolidone|pvp)|(?:povidone|polyvinyl[-\s]?pyrrolidone|pvp){_rp_sep}{_rp_iso_I125})(?![a-z0-9])",
        "Iodinated I^125^ sodium iodine":           rf"(?<![a-z0-9])({_rp_iso_I125}{_rp_sep}(?:sodium[-\s]?iod(?:ine|ide)|nai)|(?:sodium[-\s]?iod(?:ine|ide)|nai){_rp_sep}{_rp_iso_I125})(?![a-z0-9])",
        "Iodinated I^131^ aggregated albumin":      rf"(?<![a-z0-9])({_rp_iso_I131}{_rp_sep}(?:(?<!micro)(?<!micro[-\s])(?:macro[-\s]?)?aggregated[-\s]?albumin|maa)|(?:(?<!micro)(?<!micro[-\s])(?:macro[-\s]?)?aggregated[-\s]?albumin|maa){_rp_sep}{_rp_iso_I131})(?![a-z0-9])",
        "Iodinated I^131^ albumin":                 rf"(?<![a-z0-9])({_rp_iso_I131}{_rp_sep}(?:(?<!aggregated[-\s])(?:iodinated[-\s]?)?(?:(?:human[-\s]?)?serum[-\s]?)?albumin|i?hsa)|(?:(?<!aggregated[-\s])(?:iodinated[-\s]?)?(?:(?:human[-\s]?)?serum[-\s]?)?albumin|i?hsa){_rp_sep}{_rp_iso_I131})(?![a-z0-9])",
        "Iodinated I^131^ gamma globulin":          rf"(?<![a-z0-9])({_rp_iso_I131}{_rp_sep}(?:gamma[-\s]?globulin)|(?:gamma[-\s]?globulin){_rp_sep}{_rp_iso_I131})(?![a-z0-9])",
        "Iodine^123 15-(4-Iodophenyl)-3(R,S)-Methylpentadecanoic Acid":r"(?<![a-z0-9])(bmipp|cardiodine|15[-\s]?\((?:4|p)[-\s]?iodophenyl\)[-\s]?3[-\s]?\(r,\s?s\)[-\s]?methyl[-\s]?pentadecanoic[-\s]?acid)(?![a-z0-9])",  # bmipp: additional
        "Iodine^123 3-Iodobenzylguanidine MIBG":    rf"(?<![a-z0-9])({_rp_iso_I123}{_rp_sep}(?:(?:3[-\s]?|meta[-\s]?|m[-\s]?)?iodo[-\s]?benzyl[-\s]?guanidine(?:[-\s]?\(?mibg\)?)?|mibg|iobenguane)|(?:(?:3[-\s]?|meta[-\s]?|m[-\s]?)?iodo[-\s]?benzyl[-\s]?guanidine(?:[-\s]?\(?mibg\)?)?|mibg|iobenguane){_rp_sep}{_rp_iso_I123}|adreview)(?![a-z0-9])",  # iobenguane (INN), adreview: additional
        "Iodine^131^ polyvinylpyrrolidone":         rf"(?<![a-z0-9])({_rp_iso_I131}{_rp_sep}(?:polyvinyl[-\s]?pyrrolidone|povidone|pvp)|(?:polyvinyl[-\s]?pyrrolidone|povidone|pvp){_rp_sep}{_rp_iso_I131})(?![a-z0-9])",
        "Iodine^131 3-Iodobenzylguanidine MIBG":    rf"(?<![a-z0-9])({_rp_iso_I131}{_rp_sep}(?:(?:3[-\s]?|meta[-\s]?|m[-\s]?)?iodo[-\s]?benzyl[-\s]?guanidine(?:[-\s]?\(?mibg\)?)?|mibg|iobenguane)|(?:(?:3[-\s]?|meta[-\s]?|m[-\s]?)?iodo[-\s]?benzyl[-\s]?guanidine(?:[-\s]?\(?mibg\)?)?|mibg|iobenguane){_rp_sep}{_rp_iso_I131})(?![a-z0-9])",  # iobenguane (INN): additional
        "Iodocholesterol I^131^":                   rf"(?<![a-z0-9])({_rp_iso_I131}{_rp_sep}(?:(?:19[-\s]?)?iodo[-\s]?cholesterol)|(?:(?:19[-\s]?)?iodo[-\s]?cholesterol){_rp_sep}{_rp_iso_I131})(?![a-z0-9])",
        "Iodohippurate I^123^ sodium":              rf"(?<![a-z0-9])({_rp_iso_I123}{_rp_sep}(?:(?:sodium[-\s]?)?(?:ortho[-\s]?|o[-\s]?)?iodo[-\s]?hippurate(?:[-\s]?sodium)?|oih)|(?:(?:sodium[-\s]?)?(?:ortho[-\s]?|o[-\s]?)?iodo[-\s]?hippurate(?:[-\s]?sodium)?|oih){_rp_sep}{_rp_iso_I123})(?![a-z0-9])",  # oih: additional
        "Iodohippurate I^125^ sodium":              rf"(?<![a-z0-9])({_rp_iso_I125}{_rp_sep}(?:(?:sodium[-\s]?)?(?:ortho[-\s]?|o[-\s]?)?iodo[-\s]?hippurate(?:[-\s]?sodium)?|oih)|(?:(?:sodium[-\s]?)?(?:ortho[-\s]?|o[-\s]?)?iodo[-\s]?hippurate(?:[-\s]?sodium)?|oih){_rp_sep}{_rp_iso_I125})(?![a-z0-9])",  # oih: additional
        "Iodohippurate I^131^ sodium":              rf"(?<![a-z0-9])({_rp_iso_I131}{_rp_sep}(?:(?:sodium[-\s]?)?(?:ortho[-\s]?|o[-\s]?)?iodo[-\s]?hippurate(?:[-\s]?sodium)?|oih)|(?:(?:sodium[-\s]?)?(?:ortho[-\s]?|o[-\s]?)?iodo[-\s]?hippurate(?:[-\s]?sodium)?|oih){_rp_sep}{_rp_iso_I131})(?![a-z0-9])",  # oih: additional
        "Iofetamine I^123^ hydrochloride":          r"(?<![a-z0-9])(iofetamine(?:[-\s]?hydrochloride)?)(?![a-z0-9])",
        "Ioflupane I^123^":                         rf"(?<![a-z0-9])(ioflupane|dat[-\s]?scan|{_rp_iso_I123}{_rp_sep}(?:fp[-\s]?cit)|(?:fp[-\s]?cit){_rp_sep}{_rp_iso_I123})(?![a-z0-9])",  # fp-cit (with I-123 only, as there is also F-18 FP-CIT): additional
        "Iothalamate sodium I^125^":                rf"(?<![a-z0-9])({_rp_iso_I125}{_rp_sep}(?:(?:sodium[-\s]?)?io?thalamate(?:[-\s]?sodium)?)|(?:(?:sodium[-\s]?)?io?thalamate(?:[-\s]?sodium)?){_rp_sep}{_rp_iso_I125}|glofil)(?![a-z0-9])",  # glofil: additional
        "Iron Fe^59^ labeled dextran":              rf"(?<![a-z0-9])({_rp_iso_Fe59}{_rp_sep}(?:(?:iron[-\s]?)?(?:labell?ed[-\s]?)?dextran)|(?:(?:iron[-\s]?)?(?:labell?ed[-\s]?)?dextran){_rp_sep}{_rp_iso_Fe59})(?![a-z0-9])",
        "Krypton^81m":                              rf"(?<![a-z0-9])({_rp_iso_Kr81m}(?:{_rp_sep}(?:krypton[-\s]?)?gas)?)(?![a-z0-9])",
        "Lutetium^177^ DOTATATE":                   rf"(?<![a-z0-9])({_rp_iso_Lu177}{_rp_sep}(?:(?:lu[-\s]?)?dota[-\s]?tate|oxodotreotide)|(?:(?:lu[-\s]?)?dota[-\s]?tate|oxodotreotide){_rp_sep}{_rp_iso_Lu177}|lutathera)(?![a-z0-9])",  # oxodotreotide (INN), lutathera: additional
        "Lutetium^177^ n-acetylaspartylglutamate":  rf"(?<![a-z0-9])({_rp_iso_Lu177}{_rp_sep}(?:n[-\s]?acetyl[-\s]?aspartyl[-\s]?glutamate|naag)|(?:n[-\s]?acetyl[-\s]?aspartyl[-\s]?glutamate|naag){_rp_sep}{_rp_iso_Lu177})(?![a-z0-9])",
        "Lutetium^177^ vipivotide tetraxetan":      rf"(?<![a-z0-9])(vipivotide(?:[-\s]?tetraxetan)?|pluvicto|{_rp_iso_Lu177}{_rp_sep}(?:(?:lu[-\s]?)?psma[-\s]?617)|(?:(?:lu[-\s]?)?psma[-\s]?617){_rp_sep}{_rp_iso_Lu177})(?![a-z0-9])",  # psma-617 (with Lu-177 only): additional
        "Oleic acid I^125^":                        rf"(?<![a-z0-9])({_rp_iso_I125}{_rp_sep}(?:oleic[-\s]?acid|oleate)|(?:oleic[-\s]?acid|oleate){_rp_sep}{_rp_iso_I125})(?![a-z0-9])",
        "Pentetate calcium trisodium Yb^169^":      rf"(?<![a-z0-9])({_rp_iso_Yb169}{_rp_sep}(?:pentetate[-\s]?calcium[-\s]?trisodium|calcium[-\s]?trisodium[-\s]?pentetate)|(?:pentetate[-\s]?calcium[-\s]?trisodium|calcium[-\s]?trisodium[-\s]?pentetate){_rp_sep}{_rp_iso_Yb169})(?![a-z0-9])",
        "Potassium carbonate K^42^":                rf"(?<![a-z0-9])({_rp_iso_K42}{_rp_sep}(?:(?:potassium[-\s]?)?carbonate)|(?:(?:potassium[-\s]?)?carbonate){_rp_sep}{_rp_iso_K42})(?![a-z0-9])",
        "Potassium chloride K^42^":                 rf"(?<![a-z0-9])({_rp_iso_K42}{_rp_sep}(?:(?:potassium[-\s]?)?chloride|kcl)|(?:(?:potassium[-\s]?)?chloride|kcl){_rp_sep}{_rp_iso_K42})(?![a-z0-9])",
        "Potassium chloride K^43^":                 rf"(?<![a-z0-9])({_rp_iso_K43}{_rp_sep}(?:(?:potassium[-\s]?)?chloride|kcl)|(?:(?:potassium[-\s]?)?chloride|kcl){_rp_sep}{_rp_iso_K43})(?![a-z0-9])",
        "Radium^223^ dichloride":                   rf"(?<![a-z0-9])({_rp_iso_Ra223}(?:{_rp_sep}(?:radium[-\s]?)?(?:di)?chloride)?|radium[-\s]?(?:di)?chloride|xofigo)(?![a-z0-9])",  # xofigo: additional
        "Rose Bengal sodium I^131^":                r"(?<![a-z0-9])(rose[-\s]?bengal(?:[-\s]?sodium)?)(?![a-z0-9])",
        "Selenium^75^ HCAT":                        r"(?<![a-z0-9])((?:se[-\s]?)?hcat|tauroselcholic[-\s]?acid)(?![a-z0-9])",  # sehcat, tauroselcholic acid: additional
        "Selenomethionione Se^75^":                 r"(?<![a-z0-9])(seleno[-\s]?methion(?:i?one|ine))(?![a-z0-9])",
        "Sodium chloride Na^22^":                   rf"(?<![a-z0-9])({_rp_iso_Na22}{_rp_sep}(?:sodium[-\s]?chloride|nacl)|(?:sodium[-\s]?chloride|nacl){_rp_sep}{_rp_iso_Na22})(?![a-z0-9])",
        "Sodium chloride Na^24^":                   rf"(?<![a-z0-9])({_rp_iso_Na24}{_rp_sep}(?:sodium[-\s]?chloride|nacl)|(?:sodium[-\s]?chloride|nacl){_rp_sep}{_rp_iso_Na24})(?![a-z0-9])",
        "Sodium chromate Cr^51^":                   rf"(?<![a-z0-9])({_rp_iso_Cr51}{_rp_sep}(?:(?:sodium[-\s]?)?chromate)|(?:(?:sodium[-\s]?)?chromate){_rp_sep}{_rp_iso_Cr51})(?![a-z0-9])",
        "Sodium fluoride F^18^":                    r"(?<![a-z0-9])(sodium[-\s]?fluoride|naf|na[\[(]?18[-\s^]*f[\])]?)(?![a-z0-9])",  # naf, na18f: additional
        "Sodium iodide I^123^":                     rf"(?<![a-z0-9])({_rp_iso_I123}{_rp_sep}(?:sodium[-\s]?iodide|nai)|(?:sodium[-\s]?iodide|nai){_rp_sep}{_rp_iso_I123}|na[\[(]?123[-\s^]*i[\])]?)(?![a-z0-9])",
        "Sodium iodide I^131^":                     rf"(?<![a-z0-9])({_rp_iso_I131}{_rp_sep}(?:sodium[-\s]?iodide|nai)|(?:sodium[-\s]?iodide|nai){_rp_sep}{_rp_iso_I131}|na[\[(]?131[-\s^]*i[\])]?)(?![a-z0-9])",
        "Sodium pertechnetate Tc^99m^":             r"(?<![a-z0-9])((?:sodium[-\s]?)?pertechnetate)(?![a-z0-9])",
        "Sodium phosphate P^32^":                   rf"(?<![a-z0-9])({_rp_iso_P32}{_rp_sep}(?:sodium[-\s]?phosphate)|(?:sodium[-\s]?phosphate){_rp_sep}{_rp_iso_P32})(?![a-z0-9])",
        "Strontium chloride Sr^85^":                rf"(?<![a-z0-9])({_rp_iso_Sr85}{_rp_sep}(?:(?:strontium[-\s]?)?chloride)|(?:(?:strontium[-\s]?)?chloride){_rp_sep}{_rp_iso_Sr85})(?![a-z0-9])",
        "Strontium chloride Sr^87^":                rf"(?<![a-z0-9])({_rp_iso_Sr87m}{_rp_sep}(?:(?:strontium[-\s]?)?chloride)|(?:(?:strontium[-\s]?)?chloride){_rp_sep}{_rp_iso_Sr87m})(?![a-z0-9])",
        "Strontium chloride Sr^89^":                rf"(?<![a-z0-9])({_rp_iso_Sr89}{_rp_sep}(?:(?:strontium[-\s]?)?chloride)|(?:(?:strontium[-\s]?)?chloride){_rp_sep}{_rp_iso_Sr89}|metastron)(?![a-z0-9])",  # metastron: additional
        "Strontium nitrate Sr^85^":                 rf"(?<![a-z0-9])({_rp_iso_Sr85}{_rp_sep}(?:(?:strontium[-\s]?)?nitrate)|(?:(?:strontium[-\s]?)?nitrate){_rp_sep}{_rp_iso_Sr85})(?![a-z0-9])",
        "Strontium nitrate Sr^87^":                 rf"(?<![a-z0-9])({_rp_iso_Sr87m}{_rp_sep}(?:(?:strontium[-\s]?)?nitrate)|(?:(?:strontium[-\s]?)?nitrate){_rp_sep}{_rp_iso_Sr87m})(?![a-z0-9])",
        "Technetium^99m^ TRODAT-1":                 r"(?<![a-z0-9])(trodat(?:[-\s]?1)?)(?![a-z0-9])",
        "Technetium^99m Galactosyl Human Serum Albumin Diethylenetriamine":r"(?<![a-z0-9])(galactosyl[-\s]?human[-\s]?serum[-\s]?albumin(?:[-\s]?diethylene[-\s]?triamine(?:[-\s]?penta[-\s]?acetic[-\s]?acid)?)?|gsa|asialoscinti)(?![a-z0-9])",  # gsa: additional
        "Technetium^99m labeled carbon":            rf"(?<![a-z0-9])(technegas|{_rp_iso_Tc99m}{_rp_sep}(?:labell?ed[-\s]?)?carbon|technetium[-\s]?labell?ed[-\s]?carbon)(?![a-z0-9])",
        "Technetium^99m Mercaptoacetyl triglycine MAG3":r"(?<![a-z0-9])(mag[-\s]?3|mercapto[-\s]?acetyl[-\s]?(?:tri)?glycine|mertiatide|magscinti)(?![a-z0-9])",  # mertiatide (INN): additional
        "Technetium^99m N-pyridoxyl-5-methyltryptophan":r"(?<![a-z0-9])(n[-\s]?pyridoxyl[-\s]?5[-\s]?methyl[-\s]?tryptophan|hepatimage)(?![a-z0-9])",
        "Technetium^99m Phytate":                   r"(?<![a-z0-9])(phytate|phytic[-\s]?acid)(?![a-z0-9])",
        "Technetium^99m Stannous Colloid":          r"(?<![a-z0-9])((?:stannous|tin)[-\s]?colloid)(?![a-z0-9])",
        "Technetium^99m Trofolastat":               r"(?<![a-z0-9])(trofolastat|mip[-\s]?1404)(?![a-z0-9])",
        "Technetium Tc^99c^ albumin microspheres":  r"(?<![a-z0-9])((?:human[-\s]?)?albumin[-\s]?micro[-\s]?spheres?)(?![a-z0-9])",
        "Technetium Tc^99m^ aggregated albumin":    rf"(?<![a-z0-9])({_rp_iso_Tc99m}{_rp_sep}(?:(?<!micro)(?<!micro[-\s])(?:macro[-\s]?)?aggregated[-\s]?albumin|maa)|(?:(?<!micro)(?<!micro[-\s])(?:macro[-\s]?)?aggregated[-\s]?albumin|maa){_rp_sep}{_rp_iso_Tc99m})(?![a-z0-9])",
        "Technetium Tc^99m^ depreotide":            r"(?<![a-z0-9])(depreotide|neotect|neospect)(?![a-z0-9])",  # neotect, neospect: additional
        "Technetium Tc^99m^ disofenin":             r"(?<![a-z0-9])(disofenin|hepatolite)(?![a-z0-9])",  # hepatolite: additional
        "Technetium Tc^99m^ bicisate":              r"(?<![a-z0-9])(bicisate|ecd|neurolite)(?![a-z0-9])",  # ecd: additional
        "Technetium Tc^99m^ exametazime":           r"(?<![a-z0-9])(exametazime|hm[-\s]?pao|ceretec)(?![a-z0-9])",  # hmpao, ceretec: additional
        "Technetium Tc^99m^ iron ascorbate":        rf"(?<![a-z0-9])({_rp_iso_Tc99m}{_rp_sep}(?:iron[-\s]?ascorbate)|(?:iron[-\s]?ascorbate){_rp_sep}{_rp_iso_Tc99m})(?![a-z0-9])",
        "Technetium Tc^99m^ lidofenin":             r"(?<![a-z0-9])(lidofenin)(?![a-z0-9])",
        "Technetium Tc^99m^ mebrofenin":            r"(?<![a-z0-9])(mebrofenin|bromida|choletec)(?![a-z0-9])",  # bromida, choletec: additional
        "Technetium Tc^99m^ medronate":             r"(?<![a-z0-9])(medronate|mdp|methylene[-\s]?di[-\s]?phosphonate)(?![a-z0-9])",  # mdp: additional
        "Technetium Tc^99m^ microaggregated albumin":rf"(?<![a-z0-9])({_rp_iso_Tc99m}{_rp_sep}(?:micro[-\s]?aggregated[-\s]?albumin)|(?:micro[-\s]?aggregated[-\s]?albumin){_rp_sep}{_rp_iso_Tc99m})(?![a-z0-9])",
        "Technetium Tc^99m^ N-substituted iminodiacetate":r"(?<![a-z0-9])((?:n[-\s]?substituted[-\s]?)?imino[-\s]?diacet(?:ate|ic[-\s]?acid)|hida)(?![a-z0-9])",  # hida: additional
        "Technetium Tc^99m^ oxidronate":            r"(?<![a-z0-9])(oxidronate|h(?:m)?dp|hydroxy[-\s]?methylene[-\s]?di[-\s]?phosphonate)(?![a-z0-9])",  # hdp, hmdp: additional
        "Technetium Tc^99m^ pentetate":             rf"(?<![a-z0-9])({_rp_iso_Tc99m}{_rp_sep}(?:pentetate|dtpa(?![-\s]?octreotide))|(?:pentetate|dtpa(?![-\s]?octreotide)){_rp_sep}{_rp_iso_Tc99m})(?![a-z0-9])",
        "Technetium Tc^99m^ pyrophosphate":         r"(?<![a-z0-9])(pyrophosphate|pyp)(?![a-z0-9])",  # pyp: additional
        "Technetium Tc^99m^ serum albumin":         rf"(?<![a-z0-9])({_rp_iso_Tc99m}{_rp_sep}(?:(?:human[-\s]?)?serum[-\s]?albumin|hsa)|(?:(?:human[-\s]?)?serum[-\s]?albumin|hsa){_rp_sep}{_rp_iso_Tc99m})(?![a-z0-9])",
        "Technetium Tc^99m^ sestamibi":             r"(?<![a-z0-9])(sestamibi|mibi|cardiolite|miraluma)(?![a-z0-9])",  # mibi, cardiolite, miraluma: additional
        "Technetium Tc^99m^ sodium glucoheptonate": r"(?<![a-z0-9])((?:sodium[-\s]?)?gluco[-\s]?heptonate)(?![a-z0-9])",
        "Technetium Tc^99m^ stannous etidronate":   r"(?<![a-z0-9])((?:stannous[-\s]?)?etidronate)(?![a-z0-9])",
        "Technetium Tc^99m^ succimer":              r"(?<![a-z0-9])(succimer|dmsa)(?![a-z0-9])",  # dmsa: additional
        "Technetium Tc^99m^ sulfur colloid":        r"(?<![a-z0-9])(sul(?:ph|f)ur[-\s]?colloid)(?![a-z0-9])",
        "Technetium Tc^99m^ tagged red cells":      rf"(?<![a-z0-9])({_rp_iso_Tc99m}{_rp_sep}(?:(?:(?:tagged|labell?ed)[-\s]?)?(?:red[-\s]?(?:blood[-\s]?)?cells?|rbcs?))|(?:(?:(?:tagged|labell?ed)[-\s]?)?(?:red[-\s]?(?:blood[-\s]?)?cells?|rbcs?)){_rp_sep}{_rp_iso_Tc99m}|ultratag)(?![a-z0-9])",  # ultratag: additional
        "Technetium Tc^99m^Teboroxime":             r"(?<![a-z0-9])(teboroxime|cardiotec)(?![a-z0-9])",  # cardiotec: additional
        "Technetium Tc^99m^Tetrofosmin":            r"(?<![a-z0-9])(tetrofosmin|myoview)(?![a-z0-9])",  # myoview: additional
        "Thallous chloride Tl^201^":                rf"(?<![a-z0-9])(thallous[-\s]?chloride|thallium(?:[-\s]?chloride)?(?:{_rp_sep}{_rp_iso_Tl201})?|{_rp_iso_Tl201}(?:{_rp_sep}(?:thallous[-\s]?)?chloride)?)(?![a-z0-9])",
        "Therapeutic radioisotope":                 r"(?<![a-z0-9])(therapeutic[-\s]?radio[-\s]?(?:isotope|nuclide|pharmaceutical)s?)(?![a-z0-9])",
        "Xenon^133^ gas":                           rf"(?<![a-z0-9])({_rp_iso_Xe133}(?:{_rp_sep}(?:xenon[-\s]?)?gas)?|xeneisol)(?![a-z0-9])",
        "Yb^169^-DTPA - pentetate":                 rf"(?<![a-z0-9])({_rp_iso_Yb169}{_rp_sep}(?:(?:dtpa|pentetate)(?![-\s]?calcium))|(?:(?:dtpa|pentetate)(?![-\s]?calcium)){_rp_sep}{_rp_iso_Yb169})(?![a-z0-9])",
        "Yttrium^90^ microspheres":                 rf"(?<![a-z0-9])({_rp_iso_Y90}{_rp_sep}(?:(?:glass[-\s]?|resin[-\s]?)?micro[-\s]?spheres?)|(?:(?:glass[-\s]?|resin[-\s]?)?micro[-\s]?spheres?){_rp_sep}{_rp_iso_Y90}|therasphere|sir[-\s]?spheres?)(?![a-z0-9])",  # therasphere, sir-spheres: additional
    }

    # Dictionary mapping the DICOM NM/SPECT radiopharmaceutical names to their codes
    # Key: Code Meaning of the radiopharmaceutical in DICOM CID 25 (the same keys as in nm_spect_radiopharmaceutical_names_2_patterns)
    # Value: Tuple with the Coding Scheme Designator and Code Value of DICOM CID 25, and the description of the coding scheme:
    #   - SNOMED: SNOMED CT Fully Specified Name (International Edition)
    #   - DCM:    DICOM Code Meaning (DICOM is the coding scheme itself)
    #   - NCIt:   NCI Thesaurus preferred name
    #   - MSH:    MeSH supplementary concept name
    # Note(s):
    #  - The SNOMED CT codes are checked to be a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |.
    #    DICOM codes that are not ("Product containing ... (medicinal product)" concepts) are replaced by their
    #    radioactive isotope substance (the active ingredient of the product), the DICOM code is kept in the comment at the end of the line.
    #    Inactive DICOM codes without replacement are kept, with a comment at the end of the line.
    #  - The Coding Scheme Designators are those of DICOM, except "SNOMED" (as used for SPHN) instead of "SCT" for SNOMED CT.
    #  - "Pentetate calcium trisodium Yb^169^" and "Yb^169^-DTPA - pentetate" have the same code in DICOM CID 25.
    #  - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_25.html
    nm_spect_radiopharmaceutical_name_2_code: ClassVar[Mapping[str, tuple[str, str, str]]] = {

        "Carbon^14^ D-xylose":                      ("SNOMED",        "2942001", "| Carbon (14-C) xylose (substance) |"),
        "Carbon^14^ triolein":                      ("SNOMED",       "42417005", "| Carbon (14-C) triolein (substance) |"),
        "Chromic phosphate P^32^":                  ("SNOMED",       "17069007", "| Chromic phosphate (32-P) (substance) |"),
        "Chromium^51^ albumin":                     ("SNOMED",        "4693006", "| Chromium (51-Cr) albumin (substance) |"),
        "Chromium^51^ chloride":                    ("SNOMED",        "6973004", "| Chromium (51-Cr) chloride (substance) |"),
        "Copper^64^ acetate":                       ("SNOMED",       "78686003", "| Copper (64-Cu) acetate (substance) |"),
        "Copper^64^ versenate":                     ("SNOMED",       "88166005", "| Copper (64-Cu) versenate (substance) |"),
        "Copper^67^ ceruloplasmin":                 ("SNOMED",       "29460005", "| Copper (67-Cu) ceruloplasmin (substance) |"),
        "Cyanocobalamin Co^57^":                    ("SNOMED",         "187006", "| Cyanocobalamin (57-Co) (substance) |"),
        "Cyanocobalamin Co^58^":                    ("SNOMED",        "5692007", "| Cyanocobalamin (58-Co) (substance) |"),
        "Cyanocobalamin Co^60^":                    ("SNOMED",       "72159005", "| Cyanocobalamin (60-Co) (substance) |"),
        "Diagnostic radioisotope":                  ("SNOMED",       "17600005", "| Diagnostic radioisotope (product) |"),  # DICOM code is inactive in SNOMED CT without replacement, so it is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "Ferrous chloride Fe^59^":                  ("SNOMED",       "31192007", "| Ferrous (59-Fe) chloride (substance) |"),
        "Ferrous citrate Fe^59^":                   ("SNOMED",       "87958003", "| Ferrous (59-Fe) citrate (substance) |"),
        "Ferrous sulfate Fe^59^":                   ("SNOMED",         "125001", "| Ferrous (59-Fe) sulfate (substance) |"),
        "Fibrinogen I^123^":                        ("SNOMED",       "71636003", "| Fibrinogen (123-I) (substance) |"),
        "Fluorodeoxyglucose F^18^":                 ("SNOMED",       "35321007", "| Fluorodeoxyglucose (18-F) (substance) |"),
        "Gallium^67^ citrate":                      ("SNOMED",       "73065000", "| Gallium (67-Ga) citrate (substance) |"),
        "Indium^111^-Fe(OH) >3<":                   ("SNOMED",        "6516008", "| Indium (111-In) ferric hydroxide (substance) |"),
        "Indium^111^oxyquinoline":                  ("SNOMED",      "395747004", "| Indium (111-In) oxine (substance) |"),  # Replaced DICOM code 424570009 | Product containing indium (111-In) oxine (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "Indium^111^ pentetate":                    ("SNOMED",       "29218008", "| Indium (111-In) pentetate (substance) |"),
        "Indium^111^ red cell label":               ("SNOMED",       "81621007", "| Indium (111-In) labeled erythrocyte (substance) |"),
        "Indium^111^ transferrin":                  ("SNOMED",       "78570003", "| Indium (111-In) transferrin (substance) |"),
        "Indium^111 Capromab Pendetide":            ("SNOMED",      "446871009", "| Indium (111-In) capromab pendetide (substance) |"),
        "Indium^111 Chloride":                      ("SNOMED",      "395742005", "| Indium (111-In) chloride (substance) |"),
        "Indium^111 Pentetreotide":                 ("SNOMED",      "446800006", "| Indium (111-In) pentetreotide (substance) |"),
        "Indium^113m^ bleomycin":                   ("SNOMED",       "90617008", "| Indium (113-In) bleomycin (substance) |"),
        "Indium^113m^ chloride":                    ("SNOMED",      "767418009", "| Indium (113-In) chloride (substance) |"),
        "Indium^113m^ pentetate":                   ("SNOMED",       "42728008", "| Indium (113-In) pentetate (substance) |"),
        "Iodinated I^125^ albumin":                 ("SNOMED",       "72015003", "| Iodinated (125-I) albumin (substance) |"),
        "Iodinated I^125^ DPA-713":                 ("DCM",         "126764", "| Iodinated I^125^ DPA-713 |"),
        "Iodinated I^125^ human serum albumin":     ("SNOMED",       "64488003", "| Iodinated (125-I) human serum albumin (substance) |"),
        "Iodinated I^125^ povidone":                ("SNOMED",       "69839009", "| Povidone iodine (125-I) (substance) |"),
        "Iodinated I^125^ sodium iodine":           ("SNOMED",       "70154008", "| Sodium iodide (125-I) (substance) |"),
        "Iodinated I^131^ aggregated albumin":      ("SNOMED",       "55814006", "| Iodinated (131-I) aggregated albumin (substance) |"),
        "Iodinated I^131^ albumin":                 ("SNOMED",       "39200002", "| Iodinated (131-I) albumin (substance) |"),
        "Iodinated I^131^ gamma globulin":          ("SNOMED",       "52408003", "| Iodinated (131-I) gamma globulin (substance) |"),
        "Iodine^123 15-(4-Iodophenyl)-3(R,S)-Methylpentadecanoic Acid":("SNOMED",      "447134003", "| Iodofiltic acid (123-I) (substance) |"),
        "Iodine^123 3-Iodobenzylguanidine MIBG":    ("SNOMED",      "395787009", "| Iobenguane (123-I) (substance) |"),
        "Iodine^131^ polyvinylpyrrolidone":         ("SNOMED",       "35884005", "| Povidone iodine (131-I) (substance) |"),
        "Iodine^131 3-Iodobenzylguanidine MIBG":    ("SNOMED",      "395789007", "| Iobenguane (131-I) (substance) |"),
        "Iodocholesterol I^131^":                   ("SNOMED",       "68967007", "| Iodocholesterol (131-I) (substance) |"),
        "Iodohippurate I^123^ sodium":              ("SNOMED",       "33785000", "| Iodine (125-I) liothyronine (substance) |"),
        "Iodohippurate I^125^ sodium":              ("SNOMED",       "36900006", "| Sodium Iodohippurate (125-I) (substance) |"),
        "Iodohippurate I^131^ sodium":              ("SNOMED",       "33271006", "| Iodohippurate (131-I) sodium (substance) |"),
        "Iofetamine I^123^ hydrochloride":          ("SNOMED",       "78481003", "| Iofetamine (123-I) hydrochloride (substance) |"),
        "Ioflupane I^123^":                         ("SNOMED",      "428122004", "| Ioflupane (123-I) (substance) |"),  # Replaced DICOM code 429296007 | Product containing ioflupane (123-I) (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "Iothalamate sodium I^125^":                ("SNOMED",      "395879003", "| Sodium iothalamate (125-I) (substance) |"),  # Replaced DICOM code 55673009 | Product containing sodium iothalamate (125-I) (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "Iron Fe^59^ labeled dextran":              ("SNOMED",       "60459006", "| Iron (59-Fe) dextran (substance) |"),
        "Krypton^81m":                              ("SNOMED",       "61716009", "| Krypton-81m (substance) |"),
        "Lutetium^177^ DOTATATE":                   ("SNOMED",      "781259000", "| Lutetium (177-Lu) dotatate (substance) |"),
        "Lutetium^177^ n-acetylaspartylglutamate":  ("DCM",         "126509", "| Lutetium^177^ n-acetylaspartylglutamate |"),
        "Lutetium^177^ vipivotide tetraxetan":      ("SNOMED",     "1263794005", "| Lutetium (177-Lu) vipivotide tetraxetan (substance) |"),
        "Oleic acid I^125^":                        ("SNOMED",       "22979004", "| Oleic acid (125-I) (substance) |"),
        "Pentetate calcium trisodium Yb^169^":      ("SNOMED",       "29348008", "| Ytterbium (169-Yb) pentetate calcium trisodium (substance) |"),
        "Potassium carbonate K^42^":                ("SNOMED",      "111161000", "| Potassium (K-42) carbonate (substance) |"),
        "Potassium chloride K^42^":                 ("SNOMED",       "36641004", "| Potassium (K-42) chloride (substance) |"),
        "Potassium chloride K^43^":                 ("SNOMED",       "47729008", "| Potassium (K-43) chloride (substance) |"),
        "Radium^223^ dichloride":                   ("SNOMED",      "724024003", "| Radium (223-Ra) dichloride (substance) |"),
        "Rose Bengal sodium I^131^":                ("SNOMED",      "111159009", "| Rose bengal (131-I) sodium (substance) |"),
        "Selenium^75^ HCAT":                        ("SNOMED",      "395894004", "| Tauroselcholic acid (75-Se) (substance) |"),
        "Selenomethionione Se^75^":                 ("SNOMED",       "88473009", "| Selenomethionine (75-Se) (substance) |"),
        "Sodium chloride Na^22^":                   ("SNOMED",        "6257000", "| Sodium (22-Na) chloride (substance) |"),
        "Sodium chloride Na^24^":                   ("SNOMED",       "31527000", "| Sodium (24-Na) chloride (substance) |"),
        "Sodium chromate Cr^51^":                   ("SNOMED",       "62517004", "| Sodium chromate (51-Cr) (substance) |"),
        "Sodium fluoride F^18^":                    ("SNOMED",      "129501009", "| Sodium fluoride (18-F) (substance) |"),
        "Sodium iodide I^123^":                     ("SNOMED",       "67690002", "| Sodium iodide (123-I) (substance) |"),
        "Sodium iodide I^131^":                     ("SNOMED",      "111160004", "| Sodium iodide (131-I) (substance) |"),
        "Sodium pertechnetate Tc^99m^":             ("SNOMED",       "19495007", "| Technetium (99m-Tc) sodium pertechnetate (substance) |"),
        "Sodium phosphate P^32^":                   ("SNOMED",       "10781003", "| Sodium phosphate (32-P) (substance) |"),
        "Strontium chloride Sr^85^":                ("SNOMED",       "69076006", "| Strontium (85-Sr) chloride (substance) |"),
        "Strontium chloride Sr^87^":                ("SNOMED",       "38424001", "| Strontium (87-Sr) chloride (substance) |"),
        "Strontium chloride Sr^89^":                ("SNOMED",      "125701003", "| Strontium (89-Sr) chloride (substance) |"),
        "Strontium nitrate Sr^85^":                 ("SNOMED",        "8858006", "| Strontium (85-Sr) nitrate (substance) |"),
        "Strontium nitrate Sr^87^":                 ("SNOMED",       "31953001", "| Strontium (87-Sr) nitrate (substance) |"),
        "Technetium^99m^ TRODAT-1":                 ("MSH",        "C104196", "| technetium Tc 99m TRODAT-1 |"),
        "Technetium^99m Galactosyl Human Serum Albumin Diethylenetriamine":("SNOMED",      "446534003", "| Technetium (99m-Tc) galactosyl human serum albumin diethylenetriamine pentaacetic acid (substance) |"),
        "Technetium^99m labeled carbon":            ("SNOMED",      "447125008", "| Technetium (99m-Tc) labeled carbon (substance) |"),
        "Technetium^99m Mercaptoacetyl triglycine MAG3":("SNOMED",      "446536001", "| Technetium (99m-Tc) tiatide (substance) |"),
        "Technetium^99m N-pyridoxyl-5-methyltryptophan":("SNOMED",      "447126009", "| Technetium (99m-Tc) N-pyridoxyl-5-methyltryptophan (substance) |"),
        "Technetium^99m Phytate":                   ("SNOMED",      "447127000", "| Technetium (99m-Tc) phytate (substance) |"),
        "Technetium^99m Stannous Colloid":          ("SNOMED",      "447128005", "| Technetium (99m-Tc) stannous colloid (substance) |"),
        "Technetium^99m Trofolastat":               ("NCIt",        "C116887", "| Technetium Tc 99m Trofolastat |"),
        "Technetium Tc^99c^ albumin microspheres":  ("SNOMED",       "55494003", "| Technetium (99m-Tc) albumin microspheres (substance) |"),
        "Technetium Tc^99m^ aggregated albumin":    ("SNOMED",       "85693008", "| Technetium (99m-Tc) aggregated albumin (substance) |"),
        "Technetium Tc^99m^ depreotide":            ("SNOMED",      "415704007", "| Technetium (99m-Tc) depreotide (substance) |"),
        "Technetium Tc^99m^ disofenin":             ("SNOMED",        "3040004", "| Technetium (99m-Tc) disofenin (substance) |"),
        "Technetium Tc^99m^ bicisate":              ("SNOMED",      "766886003", "| Technetium (99m-Tc) bicisate (substance) |"),
        "Technetium Tc^99m^ exametazime":           ("SNOMED",       "77313009", "| Technetium (99m-Tc) exametazime (substance) |"),
        "Technetium Tc^99m^ iron ascorbate":        ("SNOMED",       "87853006", "| Technetium (99m-Tc) iron ascorbate (substance) |"),
        "Technetium Tc^99m^ lidofenin":             ("SNOMED",        "7281000", "| Technetium (99m-Tc) lidofenin (substance) |"),
        "Technetium Tc^99m^ mebrofenin":            ("SNOMED",        "4832001", "| Technetium (99m-Tc) mebrofenin (substance) |"),
        "Technetium Tc^99m^ medronate":             ("SNOMED",       "96390006", "| Technetium (99m-Tc) medronate (substance) |"),
        "Technetium Tc^99m^ microaggregated albumin":("SNOMED",       "81761004", "| Technetium (99m-Tc) microaggregated albumin (substance) |"),
        "Technetium Tc^99m^ N-substituted iminodiacetate":("SNOMED",       "87410002", "| Technetium (99-Tc) lidofenin (substance) |"),  # DICOM code is inactive in the SNOMED CT International Edition 2026-06 (still active in 2025-02), without replacement; SNOMED CT has no concept for the N-substituted iminodiacetates, Tc-99m lidofenin is 7281000
        "Technetium Tc^99m^ oxidronate":            ("SNOMED",       "53951001", "| Technetium (99m-Tc) oxidronate (substance) |"),
        "Technetium Tc^99m^ pentetate":             ("SNOMED",      "430276001", "| Technetium (99m-Tc) pentetate (substance) |"),
        "Technetium Tc^99m^ pyrophosphate":         ("SNOMED",      "764821009", "| Technetium (99m-Tc) pyrophosphate (substance) |"),
        "Technetium Tc^99m^ serum albumin":         ("SNOMED",       "79610008", "| Technetium (99m-Tc) albumin (substance) |"),
        "Technetium Tc^99m^ sestamibi":             ("SNOMED",      "424299003", "| Technetium (99m-Tc) sestamibi (substance) |"),
        "Technetium Tc^99m^ sodium glucoheptonate": ("SNOMED",       "45849009", "| Technetium (99m-Tc) sodium glucoheptonate (substance) |"),
        "Technetium Tc^99m^ stannous etidronate":   ("SNOMED",      "111162007", "| Technetium (99m-Tc) stannous etidronate (substance) |"),
        "Technetium Tc^99m^ succimer":              ("SNOMED",       "24511001", "| Technetium (99m-Tc) succimer (substance) |"),
        "Technetium Tc^99m^ sulfur colloid":        ("SNOMED",        "5931004", "| Technetium (99m-Tc) sulfur colloid (substance) |"),
        "Technetium Tc^99m^ tagged red cells":      ("SNOMED",       "89818005", "| Technetium (99-Tc) labeled red blood cells (substance) |"),
        "Technetium Tc^99m^Teboroxime":             ("SNOMED",      "424318009", "| Technetium (99m-Tc) teboroxime (substance) |"),
        "Technetium Tc^99m^Tetrofosmin":            ("SNOMED",      "424118002", "| Technetium (99m-Tc) tetrofosmin (substance) |"),
        "Thallous chloride Tl^201^":                ("SNOMED",       "73685002", "| Thallous (201-Tl) chloride (substance) |"),
        "Therapeutic radioisotope":                 ("SNOMED",         "439007", "| Therapeutic radioisotope (product) |"),  # DICOM code is inactive in SNOMED CT without replacement, so it is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "Xenon^133^ gas":                           ("SNOMED",       "80751004", "| Xenon-133 (substance) |"),  # Replaced DICOM code 780783002 | Product containing only xenon-133 in pulmonary dose form (medicinal product form) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        "Yb^169^-DTPA - pentetate":                 ("SNOMED",       "29348008", "| Ytterbium (169-Yb) pentetate calcium trisodium (substance) |"),
        "Yttrium^90^ microspheres":                 ("SNOMED",      "764678003", "| Yttrium (90-Y) labeled microspheres (substance) |"),
    }

    # Dictionary mapping the DICOM CID 25 "Radiopharmaceuticals" codes to the (new) codes used in nm_spect_radiopharmaceutical_name_2_code
    # Key: Tuple with:
    #   - coding scheme designator (e.g.: "SCT")
    #   - code value
    # Value: Tuple with:
    #   - coding scheme designator (e.g.: "SNOMED")
    #   - code value
    #   - human-readable description (e.g.: "| ... (substance) |")
    # Note(s):
    #   - The DICOM Code Meaning is the first comment at the end of the line, the second comment explains a changed code.
    #   - The "coding scheme designator" in DICOM CID 25 has "SCT" for SNOMED CT codes, which is "SNOMED" for SPHN.
    #   - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_25.html
    dicom_nm_spect_radiopharmaceuticals_coded_2_sphn_coded: ClassVar[Mapping[tuple[str, str], tuple[str, str, str]]] = {
        ("SCT",     "2942001"): ("SNOMED",    "2942001", "| Carbon (14-C) xylose (substance) |"),                                                                    # Carbon^14^ D-xylose
        ("SCT",    "42417005"): ("SNOMED",   "42417005", "| Carbon (14-C) triolein (substance) |"),                                                                  # Carbon^14^ triolein
        ("SCT",    "17069007"): ("SNOMED",   "17069007", "| Chromic phosphate (32-P) (substance) |"),                                                                # Chromic phosphate P^32^
        ("SCT",     "4693006"): ("SNOMED",    "4693006", "| Chromium (51-Cr) albumin (substance) |"),                                                                # Chromium^51^ albumin
        ("SCT",     "6973004"): ("SNOMED",    "6973004", "| Chromium (51-Cr) chloride (substance) |"),                                                               # Chromium^51^ chloride
        ("SCT",    "78686003"): ("SNOMED",   "78686003", "| Copper (64-Cu) acetate (substance) |"),                                                                  # Copper^64^ acetate
        ("SCT",    "88166005"): ("SNOMED",   "88166005", "| Copper (64-Cu) versenate (substance) |"),                                                                # Copper^64^ versenate
        ("SCT",    "29460005"): ("SNOMED",   "29460005", "| Copper (67-Cu) ceruloplasmin (substance) |"),                                                            # Copper^67^ ceruloplasmin
        ("SCT",      "187006"): ("SNOMED",     "187006", "| Cyanocobalamin (57-Co) (substance) |"),                                                                  # Cyanocobalamin Co^57^
        ("SCT",     "5692007"): ("SNOMED",    "5692007", "| Cyanocobalamin (58-Co) (substance) |"),                                                                  # Cyanocobalamin Co^58^
        ("SCT",    "72159005"): ("SNOMED",   "72159005", "| Cyanocobalamin (60-Co) (substance) |"),                                                                  # Cyanocobalamin Co^60^
        ("SCT",    "17600005"): ("SNOMED",   "17600005", "| Diagnostic radioisotope (product) |"),                                                                   # Diagnostic radioisotope                          # DICOM code is inactive in SNOMED CT without replacement, so it is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("SCT",    "31192007"): ("SNOMED",   "31192007", "| Ferrous (59-Fe) chloride (substance) |"),                                                                # Ferrous chloride Fe^59^
        ("SCT",    "87958003"): ("SNOMED",   "87958003", "| Ferrous (59-Fe) citrate (substance) |"),                                                                 # Ferrous citrate Fe^59^
        ("SCT",      "125001"): ("SNOMED",     "125001", "| Ferrous (59-Fe) sulfate (substance) |"),                                                                 # Ferrous sulfate Fe^59^
        ("SCT",    "71636003"): ("SNOMED",   "71636003", "| Fibrinogen (123-I) (substance) |"),                                                                      # Fibrinogen I^123^
        ("SCT",    "35321007"): ("SNOMED",   "35321007", "| Fluorodeoxyglucose (18-F) (substance) |"),                                                               # Fluorodeoxyglucose F^18^
        ("SCT",    "73065000"): ("SNOMED",   "73065000", "| Gallium (67-Ga) citrate (substance) |"),                                                                 # Gallium^67^ citrate
        ("SCT",     "6516008"): ("SNOMED",    "6516008", "| Indium (111-In) ferric hydroxide (substance) |"),                                                        # Indium^111^-Fe(OH) >3<
        ("SCT",   "424570009"): ("SNOMED",  "395747004", "| Indium (111-In) oxine (substance) |"),                                                                   # Indium^111^oxyquinoline                          # Replaced DICOM code 424570009 | Product containing indium (111-In) oxine (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("SCT",    "29218008"): ("SNOMED",   "29218008", "| Indium (111-In) pentetate (substance) |"),                                                               # Indium^111^ pentetate
        ("SCT",    "81621007"): ("SNOMED",   "81621007", "| Indium (111-In) labeled erythrocyte (substance) |"),                                                     # Indium^111^ red cell label
        ("SCT",    "78570003"): ("SNOMED",   "78570003", "| Indium (111-In) transferrin (substance) |"),                                                             # Indium^111^ transferrin
        ("SCT",   "446871009"): ("SNOMED",  "446871009", "| Indium (111-In) capromab pendetide (substance) |"),                                                      # Indium^111 Capromab Pendetide
        ("SCT",   "395742005"): ("SNOMED",  "395742005", "| Indium (111-In) chloride (substance) |"),                                                                # Indium^111 Chloride
        ("SCT",   "446800006"): ("SNOMED",  "446800006", "| Indium (111-In) pentetreotide (substance) |"),                                                           # Indium^111 Pentetreotide
        ("SCT",    "90617008"): ("SNOMED",   "90617008", "| Indium (113-In) bleomycin (substance) |"),                                                               # Indium^113m^ bleomycin
        ("SCT",   "767418009"): ("SNOMED",  "767418009", "| Indium (113-In) chloride (substance) |"),                                                                # Indium^113m^ chloride
        ("SCT",    "42728008"): ("SNOMED",   "42728008", "| Indium (113-In) pentetate (substance) |"),                                                               # Indium^113m^ pentetate
        ("SCT",    "72015003"): ("SNOMED",   "72015003", "| Iodinated (125-I) albumin (substance) |"),                                                               # Iodinated I^125^ albumin
        ("DCM",      "126764"): ("DCM",        "126764", "| Iodinated I^125^ DPA-713 |"),                                                                            # Iodinated I^125^ DPA-713
        ("SCT",    "64488003"): ("SNOMED",   "64488003", "| Iodinated (125-I) human serum albumin (substance) |"),                                                   # Iodinated I^125^ human serum albumin
        ("SCT",    "69839009"): ("SNOMED",   "69839009", "| Povidone iodine (125-I) (substance) |"),                                                                 # Iodinated I^125^ povidone
        ("SCT",    "70154008"): ("SNOMED",   "70154008", "| Sodium iodide (125-I) (substance) |"),                                                                   # Iodinated I^125^ sodium iodine
        ("SCT",    "55814006"): ("SNOMED",   "55814006", "| Iodinated (131-I) aggregated albumin (substance) |"),                                                    # Iodinated I^131^ aggregated albumin
        ("SCT",    "39200002"): ("SNOMED",   "39200002", "| Iodinated (131-I) albumin (substance) |"),                                                               # Iodinated I^131^ albumin
        ("SCT",    "52408003"): ("SNOMED",   "52408003", "| Iodinated (131-I) gamma globulin (substance) |"),                                                        # Iodinated I^131^ gamma globulin
        ("SCT",   "447134003"): ("SNOMED",  "447134003", "| Iodofiltic acid (123-I) (substance) |"),                                                                 # Iodine^123 15-(4-Iodophenyl)-3(R,S)-Methylpentadecanoic Acid
        ("SCT",   "395787009"): ("SNOMED",  "395787009", "| Iobenguane (123-I) (substance) |"),                                                                      # Iodine^123 3-Iodobenzylguanidine MIBG
        ("SCT",    "35884005"): ("SNOMED",   "35884005", "| Povidone iodine (131-I) (substance) |"),                                                                 # Iodine^131^ polyvinylpyrrolidone
        ("SCT",   "395789007"): ("SNOMED",  "395789007", "| Iobenguane (131-I) (substance) |"),                                                                      # Iodine^131 3-Iodobenzylguanidine MIBG
        ("SCT",    "68967007"): ("SNOMED",   "68967007", "| Iodocholesterol (131-I) (substance) |"),                                                                 # Iodocholesterol I^131^
        ("SCT",    "33785000"): ("SNOMED",   "33785000", "| Iodine (125-I) liothyronine (substance) |"),                                                             # Iodohippurate I^123^ sodium
        ("SCT",    "36900006"): ("SNOMED",   "36900006", "| Sodium Iodohippurate (125-I) (substance) |"),                                                            # Iodohippurate I^125^ sodium
        ("SCT",    "33271006"): ("SNOMED",   "33271006", "| Iodohippurate (131-I) sodium (substance) |"),                                                            # Iodohippurate I^131^ sodium
        ("SCT",    "78481003"): ("SNOMED",   "78481003", "| Iofetamine (123-I) hydrochloride (substance) |"),                                                        # Iofetamine I^123^ hydrochloride
        ("SCT",   "429296007"): ("SNOMED",  "428122004", "| Ioflupane (123-I) (substance) |"),                                                                       # Ioflupane I^123^                                 # Replaced DICOM code 429296007 | Product containing ioflupane (123-I) (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("SCT",    "55673009"): ("SNOMED",  "395879003", "| Sodium iothalamate (125-I) (substance) |"),                                                              # Iothalamate sodium I^125^                        # Replaced DICOM code 55673009 | Product containing sodium iothalamate (125-I) (medicinal product) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("SCT",    "60459006"): ("SNOMED",   "60459006", "| Iron (59-Fe) dextran (substance) |"),                                                                    # Iron Fe^59^ labeled dextran
        ("SCT",    "61716009"): ("SNOMED",   "61716009", "| Krypton-81m (substance) |"),                                                                             # Krypton^81m
        ("SCT",   "781259000"): ("SNOMED",  "781259000", "| Lutetium (177-Lu) dotatate (substance) |"),                                                              # Lutetium^177^ DOTATATE
        ("DCM",      "126509"): ("DCM",        "126509", "| Lutetium^177^ n-acetylaspartylglutamate |"),                                                             # Lutetium^177^ n-acetylaspartylglutamate
        ("SCT",  "1263794005"): ("SNOMED", "1263794005", "| Lutetium (177-Lu) vipivotide tetraxetan (substance) |"),                                                 # Lutetium^177^ vipivotide tetraxetan
        ("SCT",    "22979004"): ("SNOMED",   "22979004", "| Oleic acid (125-I) (substance) |"),                                                                      # Oleic acid I^125^
        ("SCT",    "29348008"): ("SNOMED",   "29348008", "| Ytterbium (169-Yb) pentetate calcium trisodium (substance) |"),                                          # Pentetate calcium trisodium Yb^169^ + Yb^169^-DTPA - pentetate
        ("SCT",   "111161000"): ("SNOMED",  "111161000", "| Potassium (K-42) carbonate (substance) |"),                                                              # Potassium carbonate K^42^
        ("SCT",    "36641004"): ("SNOMED",   "36641004", "| Potassium (K-42) chloride (substance) |"),                                                               # Potassium chloride K^42^
        ("SCT",    "47729008"): ("SNOMED",   "47729008", "| Potassium (K-43) chloride (substance) |"),                                                               # Potassium chloride K^43^
        ("SCT",   "724024003"): ("SNOMED",  "724024003", "| Radium (223-Ra) dichloride (substance) |"),                                                              # Radium^223^ dichloride
        ("SCT",   "111159009"): ("SNOMED",  "111159009", "| Rose bengal (131-I) sodium (substance) |"),                                                              # Rose Bengal sodium I^131^
        ("SCT",   "395894004"): ("SNOMED",  "395894004", "| Tauroselcholic acid (75-Se) (substance) |"),                                                             # Selenium^75^ HCAT
        ("SCT",    "88473009"): ("SNOMED",   "88473009", "| Selenomethionine (75-Se) (substance) |"),                                                                # Selenomethionione Se^75^
        ("SCT",     "6257000"): ("SNOMED",    "6257000", "| Sodium (22-Na) chloride (substance) |"),                                                                 # Sodium chloride Na^22^
        ("SCT",    "31527000"): ("SNOMED",   "31527000", "| Sodium (24-Na) chloride (substance) |"),                                                                 # Sodium chloride Na^24^
        ("SCT",    "62517004"): ("SNOMED",   "62517004", "| Sodium chromate (51-Cr) (substance) |"),                                                                 # Sodium chromate Cr^51^
        ("SCT",   "129501009"): ("SNOMED",  "129501009", "| Sodium fluoride (18-F) (substance) |"),                                                                  # Sodium fluoride F^18^
        ("SCT",    "67690002"): ("SNOMED",   "67690002", "| Sodium iodide (123-I) (substance) |"),                                                                   # Sodium iodide I^123^
        ("SCT",   "111160004"): ("SNOMED",  "111160004", "| Sodium iodide (131-I) (substance) |"),                                                                   # Sodium iodide I^131^
        ("SCT",    "19495007"): ("SNOMED",   "19495007", "| Technetium (99m-Tc) sodium pertechnetate (substance) |"),                                                # Sodium pertechnetate Tc^99m^
        ("SCT",    "10781003"): ("SNOMED",   "10781003", "| Sodium phosphate (32-P) (substance) |"),                                                                 # Sodium phosphate P^32^
        ("SCT",    "69076006"): ("SNOMED",   "69076006", "| Strontium (85-Sr) chloride (substance) |"),                                                              # Strontium chloride Sr^85^
        ("SCT",    "38424001"): ("SNOMED",   "38424001", "| Strontium (87-Sr) chloride (substance) |"),                                                              # Strontium chloride Sr^87^
        ("SCT",   "125701003"): ("SNOMED",  "125701003", "| Strontium (89-Sr) chloride (substance) |"),                                                              # Strontium chloride Sr^89^
        ("SCT",     "8858006"): ("SNOMED",    "8858006", "| Strontium (85-Sr) nitrate (substance) |"),                                                               # Strontium nitrate Sr^85^
        ("SCT",    "31953001"): ("SNOMED",   "31953001", "| Strontium (87-Sr) nitrate (substance) |"),                                                               # Strontium nitrate Sr^87^
        ("MSH",     "C104196"): ("MSH",       "C104196", "| technetium Tc 99m TRODAT-1 |"),                                                                          # Technetium^99m^ TRODAT-1
        ("SCT",   "446534003"): ("SNOMED",  "446534003", "| Technetium (99m-Tc) galactosyl human serum albumin diethylenetriamine pentaacetic acid (substance) |"),  # Technetium^99m Galactosyl Human Serum Albumin Diethylenetriamine
        ("SCT",   "447125008"): ("SNOMED",  "447125008", "| Technetium (99m-Tc) labeled carbon (substance) |"),                                                      # Technetium^99m labeled carbon
        ("SCT",   "446536001"): ("SNOMED",  "446536001", "| Technetium (99m-Tc) tiatide (substance) |"),                                                             # Technetium^99m Mercaptoacetyl triglycine MAG3
        ("SCT",   "447126009"): ("SNOMED",  "447126009", "| Technetium (99m-Tc) N-pyridoxyl-5-methyltryptophan (substance) |"),                                      # Technetium^99m N-pyridoxyl-5-methyltryptophan
        ("SCT",   "447127000"): ("SNOMED",  "447127000", "| Technetium (99m-Tc) phytate (substance) |"),                                                             # Technetium^99m Phytate
        ("SCT",   "447128005"): ("SNOMED",  "447128005", "| Technetium (99m-Tc) stannous colloid (substance) |"),                                                    # Technetium^99m Stannous Colloid
        ("NCIt",    "C116887"): ("NCIt",      "C116887", "| Technetium Tc 99m Trofolastat |"),                                                                       # Technetium^99m Trofolastat
        ("SCT",    "55494003"): ("SNOMED",   "55494003", "| Technetium (99m-Tc) albumin microspheres (substance) |"),                                                # Technetium Tc^99c^ albumin microspheres
        ("SCT",    "85693008"): ("SNOMED",   "85693008", "| Technetium (99m-Tc) aggregated albumin (substance) |"),                                                  # Technetium Tc^99m^ aggregated albumin
        ("SCT",   "415704007"): ("SNOMED",  "415704007", "| Technetium (99m-Tc) depreotide (substance) |"),                                                          # Technetium Tc^99m^ depreotide
        ("SCT",     "3040004"): ("SNOMED",    "3040004", "| Technetium (99m-Tc) disofenin (substance) |"),                                                           # Technetium Tc^99m^ disofenin
        ("SCT",   "766886003"): ("SNOMED",  "766886003", "| Technetium (99m-Tc) bicisate (substance) |"),                                                            # Technetium Tc^99m^ bicisate
        ("SCT",    "77313009"): ("SNOMED",   "77313009", "| Technetium (99m-Tc) exametazime (substance) |"),                                                         # Technetium Tc^99m^ exametazime
        ("SCT",    "87853006"): ("SNOMED",   "87853006", "| Technetium (99m-Tc) iron ascorbate (substance) |"),                                                      # Technetium Tc^99m^ iron ascorbate
        ("SCT",     "7281000"): ("SNOMED",    "7281000", "| Technetium (99m-Tc) lidofenin (substance) |"),                                                           # Technetium Tc^99m^ lidofenin
        ("SCT",     "4832001"): ("SNOMED",    "4832001", "| Technetium (99m-Tc) mebrofenin (substance) |"),                                                          # Technetium Tc^99m^ mebrofenin
        ("SCT",    "96390006"): ("SNOMED",   "96390006", "| Technetium (99m-Tc) medronate (substance) |"),                                                           # Technetium Tc^99m^ medronate
        ("SCT",    "81761004"): ("SNOMED",   "81761004", "| Technetium (99m-Tc) microaggregated albumin (substance) |"),                                             # Technetium Tc^99m^ microaggregated albumin
        ("SCT",    "87410002"): ("SNOMED",   "87410002", "| Technetium (99-Tc) lidofenin (substance) |"),                                                            # Technetium Tc^99m^ N-substituted iminodiacetate  # DICOM code is inactive in the SNOMED CT International Edition 2026-06 (still active in 2025-02), without replacement; SNOMED CT has no concept for the N-substituted iminodiacetates, Tc-99m lidofenin is 7281000
        ("SCT",    "53951001"): ("SNOMED",   "53951001", "| Technetium (99m-Tc) oxidronate (substance) |"),                                                          # Technetium Tc^99m^ oxidronate
        ("SCT",   "430276001"): ("SNOMED",  "430276001", "| Technetium (99m-Tc) pentetate (substance) |"),                                                           # Technetium Tc^99m^ pentetate
        ("SCT",   "764821009"): ("SNOMED",  "764821009", "| Technetium (99m-Tc) pyrophosphate (substance) |"),                                                       # Technetium Tc^99m^ pyrophosphate
        ("SCT",    "79610008"): ("SNOMED",   "79610008", "| Technetium (99m-Tc) albumin (substance) |"),                                                             # Technetium Tc^99m^ serum albumin
        ("SCT",   "424299003"): ("SNOMED",  "424299003", "| Technetium (99m-Tc) sestamibi (substance) |"),                                                           # Technetium Tc^99m^ sestamibi
        ("SCT",    "45849009"): ("SNOMED",   "45849009", "| Technetium (99m-Tc) sodium glucoheptonate (substance) |"),                                               # Technetium Tc^99m^ sodium glucoheptonate
        ("SCT",   "111162007"): ("SNOMED",  "111162007", "| Technetium (99m-Tc) stannous etidronate (substance) |"),                                                 # Technetium Tc^99m^ stannous etidronate
        ("SCT",    "24511001"): ("SNOMED",   "24511001", "| Technetium (99m-Tc) succimer (substance) |"),                                                            # Technetium Tc^99m^ succimer
        ("SCT",     "5931004"): ("SNOMED",    "5931004", "| Technetium (99m-Tc) sulfur colloid (substance) |"),                                                      # Technetium Tc^99m^ sulfur colloid
        ("SCT",    "89818005"): ("SNOMED",   "89818005", "| Technetium (99-Tc) labeled red blood cells (substance) |"),                                              # Technetium Tc^99m^ tagged red cells
        ("SCT",   "424318009"): ("SNOMED",  "424318009", "| Technetium (99m-Tc) teboroxime (substance) |"),                                                          # Technetium Tc^99m^Teboroxime
        ("SCT",   "424118002"): ("SNOMED",  "424118002", "| Technetium (99m-Tc) tetrofosmin (substance) |"),                                                         # Technetium Tc^99m^Tetrofosmin
        ("SCT",    "73685002"): ("SNOMED",   "73685002", "| Thallous (201-Tl) chloride (substance) |"),                                                              # Thallous chloride Tl^201^
        ("SCT",      "439007"): ("SNOMED",     "439007", "| Therapeutic radioisotope (product) |"),                                                                  # Therapeutic radioisotope                         # DICOM code is inactive in SNOMED CT without replacement, so it is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("SCT",   "780783002"): ("SNOMED",   "80751004", "| Xenon-133 (substance) |"),                                                                               # Xenon^133^ gas                                   # Replaced DICOM code 780783002 | Product containing only xenon-133 in pulmonary dose form (medicinal product form) |, which is not a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) |
        ("SCT",   "764678003"): ("SNOMED",  "764678003", "| Yttrium (90-Y) labeled microspheres (substance) |"),                                                     # Yttrium^90^ microspheres
    }

    # Dictionary mapping the DICOM NM/SPECT radionuclide names to regex patterns
    # Key: Code Meaning of the radionuclide in DICOM CID 18 (e.g.: "^99m^Technetium")
    # Value: Regex pattern to match the radionuclide in a DICOM string, e.g.: "Tc99m", "Tc-99m", "99mTc", "[99mTc]", "Technetium-99m"
    # Note(s):
    #  - The patterns are intended to be compiled with re.IGNORECASE.
    #  - For the metastable radionuclides (e.g. "^99m^Technetium") the "m" is optional, as e.g. "Tc-99" is often written for "Tc-99m".
    #  - A radionuclide is also found in most radiopharmaceutical strings, e.g. "Tc-99m sestamibi" matches both "^99m^Technetium" here
    #    and "Technetium Tc^99m^ sestamibi" in nm_spect_radiopharmaceutical_names_2_patterns.
    #    A radiopharmaceutical match should therefore take priority, the radionuclide is the fallback.
    #  - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_18.html
    nm_spect_radionuclide_names_2_patterns: ClassVar[Mapping[str, str]] = {

        "^14^Carbon":                               rf"(?<![a-z0-9])({_rp_iso_C14})(?![a-z0-9])",
        "^18^Fluorine":                             rf"(?<![a-z0-9])({_rp_iso_F18})(?![a-z0-9])",
        "^22^Sodium":                               rf"(?<![a-z0-9])({_rp_iso_Na22})(?![a-z0-9])",
        "^24^Sodium":                               rf"(?<![a-z0-9])({_rp_iso_Na24})(?![a-z0-9])",
        "^32^Phosphorus":                           rf"(?<![a-z0-9])({_rp_iso_P32})(?![a-z0-9])",
        "^42^Potassium":                            rf"(?<![a-z0-9])({_rp_iso_K42})(?![a-z0-9])",
        "^43^Potassium":                            rf"(?<![a-z0-9])({_rp_iso_K43})(?![a-z0-9])",
        "^47^Scandium":                             rf"(?<![a-z0-9])({_rp_iso_Sc47})(?![a-z0-9])",
        "^51^Chromium":                             rf"(?<![a-z0-9])({_rp_iso_Cr51})(?![a-z0-9])",
        "^57^Cobalt":                               rf"(?<![a-z0-9])({_rp_iso_Co57})(?![a-z0-9])",
        "^58^Cobalt":                               rf"(?<![a-z0-9])({_rp_iso_Co58})(?![a-z0-9])",
        "^59^Iron":                                 rf"(?<![a-z0-9])({_rp_iso_Fe59})(?![a-z0-9])",
        "^60^Cobalt":                               rf"(?<![a-z0-9])({_rp_iso_Co60})(?![a-z0-9])",
        "^64^Copper":                               rf"(?<![a-z0-9])({_rp_iso_Cu64})(?![a-z0-9])",
        "^67^Copper":                               rf"(?<![a-z0-9])({_rp_iso_Cu67})(?![a-z0-9])",
        "^67^Gallium":                              rf"(?<![a-z0-9])({_rp_iso_Ga67})(?![a-z0-9])",
        "^75^Selenium":                             rf"(?<![a-z0-9])({_rp_iso_Se75})(?![a-z0-9])",
        "^81m^Krypton":                             rf"(?<![a-z0-9])({_rp_iso_Kr81m})(?![a-z0-9])",
        "^85^Krypton":                              rf"(?<![a-z0-9])({_rp_iso_Kr85})(?![a-z0-9])",
        "^85^Strontium":                            rf"(?<![a-z0-9])({_rp_iso_Sr85})(?![a-z0-9])",
        "^87m^Strontium":                           rf"(?<![a-z0-9])({_rp_iso_Sr87m})(?![a-z0-9])",
        "^89^Strontium":                            rf"(?<![a-z0-9])({_rp_iso_Sr89})(?![a-z0-9])",
        "^90^Yttrium":                              rf"(?<![a-z0-9])({_rp_iso_Y90})(?![a-z0-9])",
        "^97^Ruthenium":                            rf"(?<![a-z0-9])({_rp_iso_Ru97})(?![a-z0-9])",
        "^99m^Technetium":                          rf"(?<![a-z0-9])({_rp_iso_Tc99m})(?![a-z0-9])",
        "^111^Indium":                              rf"(?<![a-z0-9])({_rp_iso_In111})(?![a-z0-9])",
        "^113m^Indium":                             rf"(?<![a-z0-9])({_rp_iso_In113m})(?![a-z0-9])",
        "^122^Iodine":                              rf"(?<![a-z0-9])({_rp_iso_I122})(?![a-z0-9])",
        "^123^Iodine":                              rf"(?<![a-z0-9])({_rp_iso_I123})(?![a-z0-9])",
        "^123^Xenon":                               rf"(?<![a-z0-9])({_rp_iso_Xe123})(?![a-z0-9])",
        "^125^Iodine":                              rf"(?<![a-z0-9])({_rp_iso_I125})(?![a-z0-9])",
        "^127^Xenon":                               rf"(?<![a-z0-9])({_rp_iso_Xe127})(?![a-z0-9])",
        "^131^Iodine":                              rf"(?<![a-z0-9])({_rp_iso_I131})(?![a-z0-9])",
        "^133^Barium":                              rf"(?<![a-z0-9])({_rp_iso_Ba133})(?![a-z0-9])",
        "^133^Xenon":                               rf"(?<![a-z0-9])({_rp_iso_Xe133})(?![a-z0-9])",
        "^149^Terbium":                             rf"(?<![a-z0-9])({_rp_iso_Tb149})(?![a-z0-9])",
        "^153^Gadolinium":                          rf"(?<![a-z0-9])({_rp_iso_Gd153})(?![a-z0-9])",
        "^153^Samarium":                            rf"(?<![a-z0-9])({_rp_iso_Sm153})(?![a-z0-9])",
        "^161^Terbium":                             rf"(?<![a-z0-9])({_rp_iso_Tb161})(?![a-z0-9])",
        "^166^Holmium":                             rf"(?<![a-z0-9])({_rp_iso_Ho166})(?![a-z0-9])",
        "^169^Ytterbium":                           rf"(?<![a-z0-9])({_rp_iso_Yb169})(?![a-z0-9])",
        "^177^Lutetium":                            rf"(?<![a-z0-9])({_rp_iso_Lu177})(?![a-z0-9])",
        "^178^Tantalum":                            rf"(?<![a-z0-9])({_rp_iso_Ta178})(?![a-z0-9])",
        "^186^Rhenium":                             rf"(?<![a-z0-9])({_rp_iso_Re186})(?![a-z0-9])",
        "^188^Rhenium":                             rf"(?<![a-z0-9])({_rp_iso_Re188})(?![a-z0-9])",
        "^191m^Iridium":                            rf"(?<![a-z0-9])({_rp_iso_Ir191m})(?![a-z0-9])",
        "^198^Gold":                                rf"(?<![a-z0-9])({_rp_iso_Au198})(?![a-z0-9])",
        "^199^Gold":                                rf"(?<![a-z0-9])({_rp_iso_Au199})(?![a-z0-9])",
        "^201^Thallium":                            rf"(?<![a-z0-9])({_rp_iso_Tl201})(?![a-z0-9])",
        "^203^Lead":                                rf"(?<![a-z0-9])({_rp_iso_Pb203})(?![a-z0-9])",
        "^211^Astatine":                            rf"(?<![a-z0-9])({_rp_iso_At211})(?![a-z0-9])",
        "^212^Lead":                                rf"(?<![a-z0-9])({_rp_iso_Pb212})(?![a-z0-9])",
        "^213^Bismuth":                             rf"(?<![a-z0-9])({_rp_iso_Bi213})(?![a-z0-9])",
        "^223^Radium":                              rf"(?<![a-z0-9])({_rp_iso_Ra223})(?![a-z0-9])",
        "^225^Actinium":                            rf"(?<![a-z0-9])({_rp_iso_Ac225})(?![a-z0-9])",
    }

    # Dictionary mapping the DICOM NM/SPECT radionuclide names to their codes
    # Key: Code Meaning of the radionuclide in DICOM CID 18 (the same keys as in nm_spect_radionuclide_names_2_patterns)
    # Value: Tuple with the Coding Scheme Designator and Code Value of DICOM CID 18, and the description of the coding scheme:
    #   - SNOMED: SNOMED CT Fully Specified Name (International Edition)
    #   - DCM:    DICOM Code Meaning (DICOM is the coding scheme itself)
    #   - NCIt:   NCI Thesaurus preferred name
    #   - MSH:    MeSH supplementary concept name
    # Note(s):
    #  - The SNOMED CT codes are checked to be a subclass of SNOMED-CT 89457008 | Radioactive isotope (substance) | (all are).
    #  - The Coding Scheme Designators are those of DICOM, except "SNOMED" (as used for SPHN) instead of "SCT" for SNOMED CT.
    #  - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_18.html
    nm_spect_radionuclide_name_2_code: ClassVar[Mapping[str, tuple[str, str, str]]] = {

        "^14^Carbon":                               ("SNOMED",       "71647005", "| Carbon-14 (substance) |"),
        "^18^Fluorine":                             ("SNOMED",       "77004003", "| Fluorine-18 (substance) |"),
        "^22^Sodium":                               ("SNOMED",       "71633006", "| Sodium-22 (substance) |"),
        "^24^Sodium":                               ("SNOMED",       "58541008", "| Sodium-24 (substance) |"),
        "^32^Phosphorus":                           ("SNOMED",       "32505007", "| Phosphorus-32 (substance) |"),
        "^42^Potassium":                            ("SNOMED",       "59844004", "| Potassium-42 (substance) |"),
        "^43^Potassium":                            ("SNOMED",        "8202008", "| Potassium-43 (substance) |"),
        "^47^Scandium":                             ("MSH",     "C000615359", "| Scandium-47 |"),
        "^51^Chromium":                             ("SNOMED",       "52745005", "| Chromium-51 (substance) |"),
        "^57^Cobalt":                               ("SNOMED",       "27054007", "| Cobalt-57 (substance) |"),
        "^58^Cobalt":                               ("SNOMED",       "89272005", "| Cobalt-58 (substance) |"),
        "^59^Iron":                                 ("SNOMED",       "68580003", "| Iron-59 (substance) |"),
        "^60^Cobalt":                               ("SNOMED",        "5405008", "| Cobalt-60 (substance) |"),
        "^64^Copper":                               ("SNOMED",        "3932008", "| Copper-64 (substance) |"),
        "^67^Copper":                               ("SNOMED",       "53700003", "| Copper-67 (substance) |"),
        "^67^Gallium":                              ("SNOMED",        "2008008", "| Gallium-67 (substance) |"),
        "^75^Selenium":                             ("SNOMED",       "43239002", "| Selenium-75 (substance) |"),
        "^81m^Krypton":                             ("SNOMED",       "61716009", "| Krypton-81m (substance) |"),
        "^85^Krypton":                              ("SNOMED",       "34127007", "| Krypton-85 (substance) |"),
        "^85^Strontium":                            ("SNOMED",      "111084009", "| Strontium-85 (substance) |"),
        "^87m^Strontium":                           ("SNOMED",       "78023008", "| Strontium-87m (substance) |"),
        "^89^Strontium":                            ("SNOMED",        "7770004", "| Strontium-89 (substance) |"),
        "^90^Yttrium":                              ("SNOMED",       "14691008", "| Yttrium-90 (substance) |"),
        "^97^Ruthenium":                            ("SNOMED",       "23788009", "| Ruthenium-97 (substance) |"),
        "^99m^Technetium":                          ("SNOMED",       "72454006", "| Technetium-99m (substance) |"),
        "^111^Indium":                              ("SNOMED",       "56609000", "| Indium-111 (substance) |"),
        "^113m^Indium":                             ("SNOMED",       "48895003", "| Indium-113m (substance) |"),
        "^122^Iodine":                              ("SNOMED",       "66956003", "| Iodine-122 (substance) |"),
        "^123^Iodine":                              ("SNOMED",       "21572004", "| Iodine-123 (substance) |"),
        "^123^Xenon":                               ("SNOMED",       "68153002", "| Xenon-123 (substance) |"),
        "^125^Iodine":                              ("SNOMED",       "68630002", "| Iodine-125 (substance) |"),
        "^127^Xenon":                               ("SNOMED",       "27081007", "| Xenon-127 (substance) |"),
        "^131^Iodine":                              ("SNOMED",        "1368003", "| Iodine-131 (substance) |"),
        "^133^Barium":                              ("SNOMED",        "3027009", "| Barium-133 (substance) |"),
        "^133^Xenon":                               ("SNOMED",       "80751004", "| Xenon-133 (substance) |"),
        "^149^Terbium":                             ("MSH",     "C000615034", "| Terbium-149 |"),
        "^153^Gadolinium":                          ("SNOMED",       "14529005", "| Gadolinium-153 (substance) |"),
        "^153^Samarium":                            ("SNOMED",      "419804008", "| Samarium-153 (substance) |"),
        "^161^Terbium":                             ("MSH",     "C000615038", "| Terbium-161 |"),
        "^166^Holmium":                             ("NCIt",          "C1943", "| Holmium Ho-166 |"),
        "^169^Ytterbium":                           ("SNOMED",       "41758004", "| Ytterbium-169 (substance) |"),
        "^177^Lutetium":                            ("SNOMED",      "447553000", "| Lutetium-177 (substance) |"),
        "^178^Tantalum":                            ("SNOMED",        "6301006", "| Tantalum-178 (substance) |"),
        "^186^Rhenium":                             ("SNOMED",      "395865006", "| Rhenium-186 (substance) |"),
        "^188^Rhenium":                             ("SNOMED",      "423578007", "| Rhenium-188 (substance) |"),
        "^191m^Iridium":                            ("DCM",         "126604", "| ^191m^Iridium |"),
        "^198^Gold":                                ("SNOMED",       "24301009", "| Gold-198 (substance) |"),
        "^199^Gold":                                ("SNOMED",       "70544003", "| Gold-199 (substance) |"),
        "^201^Thallium":                            ("SNOMED",       "60057003", "| Thallium-201 (substance) |"),
        "^203^Lead":                                ("SNOMED",       "47588004", "| Lead-203 (substance) |"),
        "^211^Astatine":                            ("MSH",     "C000615146", "| Astatine-211 |"),
        "^212^Lead":                                ("SNOMED",       "87401005", "| Lead-212 (substance) |"),
        "^213^Bismuth":                             ("MSH",     "C000615137", "| Bismuth-213 |"),
        "^223^Radium":                              ("SNOMED",       "24853006", "| Radium-223 (substance) |"),
        "^225^Actinium":                            ("SNOMED",       "32059002", "| Actinium-225 (substance) |"),
    }

    # Dictionary mapping the DICOM CID 18 "Isotopes in Radiopharmaceuticals" codes to the (new) codes used in nm_spect_radionuclide_name_2_code
    # Key: Tuple with:
    #   - coding scheme designator (e.g.: "SCT")
    #   - code value
    # Value: Tuple with:
    #   - coding scheme designator (e.g.: "SNOMED")
    #   - code value
    #   - human-readable description (e.g.: "| ... (substance) |")
    # Note(s):
    #   - The DICOM Code Meaning is the first comment at the end of the line, the second comment explains a changed code.
    #   - The "coding scheme designator" in DICOM CID 18 has "SCT" for SNOMED CT codes, which is "SNOMED" for SPHN.
    #   - See also: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_18.html
    dicom_nm_spect_radionuclides_coded_2_sphn_coded: ClassVar[Mapping[tuple[str, str], tuple[str, str, str]]] = {
        ("SCT",    "71647005"): ("SNOMED",   "71647005", "| Carbon-14 (substance) |"),       # ^14^Carbon
        ("SCT",    "77004003"): ("SNOMED",   "77004003", "| Fluorine-18 (substance) |"),     # ^18^Fluorine
        ("SCT",    "71633006"): ("SNOMED",   "71633006", "| Sodium-22 (substance) |"),       # ^22^Sodium
        ("SCT",    "58541008"): ("SNOMED",   "58541008", "| Sodium-24 (substance) |"),       # ^24^Sodium
        ("SCT",    "32505007"): ("SNOMED",   "32505007", "| Phosphorus-32 (substance) |"),   # ^32^Phosphorus
        ("SCT",    "59844004"): ("SNOMED",   "59844004", "| Potassium-42 (substance) |"),    # ^42^Potassium
        ("SCT",     "8202008"): ("SNOMED",    "8202008", "| Potassium-43 (substance) |"),    # ^43^Potassium
        ("MSH",  "C000615359"): ("MSH",    "C000615359", "| Scandium-47 |"),                 # ^47^Scandium
        ("SCT",    "52745005"): ("SNOMED",   "52745005", "| Chromium-51 (substance) |"),     # ^51^Chromium
        ("SCT",    "27054007"): ("SNOMED",   "27054007", "| Cobalt-57 (substance) |"),       # ^57^Cobalt
        ("SCT",    "89272005"): ("SNOMED",   "89272005", "| Cobalt-58 (substance) |"),       # ^58^Cobalt
        ("SCT",    "68580003"): ("SNOMED",   "68580003", "| Iron-59 (substance) |"),         # ^59^Iron
        ("SCT",     "5405008"): ("SNOMED",    "5405008", "| Cobalt-60 (substance) |"),       # ^60^Cobalt
        ("SCT",     "3932008"): ("SNOMED",    "3932008", "| Copper-64 (substance) |"),       # ^64^Copper
        ("SCT",    "53700003"): ("SNOMED",   "53700003", "| Copper-67 (substance) |"),       # ^67^Copper
        ("SCT",     "2008008"): ("SNOMED",    "2008008", "| Gallium-67 (substance) |"),      # ^67^Gallium
        ("SCT",    "43239002"): ("SNOMED",   "43239002", "| Selenium-75 (substance) |"),     # ^75^Selenium
        ("SCT",    "61716009"): ("SNOMED",   "61716009", "| Krypton-81m (substance) |"),     # ^81m^Krypton
        ("SCT",    "34127007"): ("SNOMED",   "34127007", "| Krypton-85 (substance) |"),      # ^85^Krypton
        ("SCT",   "111084009"): ("SNOMED",  "111084009", "| Strontium-85 (substance) |"),    # ^85^Strontium
        ("SCT",    "78023008"): ("SNOMED",   "78023008", "| Strontium-87m (substance) |"),   # ^87m^Strontium
        ("SCT",     "7770004"): ("SNOMED",    "7770004", "| Strontium-89 (substance) |"),    # ^89^Strontium
        ("SCT",    "14691008"): ("SNOMED",   "14691008", "| Yttrium-90 (substance) |"),      # ^90^Yttrium
        ("SCT",    "23788009"): ("SNOMED",   "23788009", "| Ruthenium-97 (substance) |"),    # ^97^Ruthenium
        ("SCT",    "72454006"): ("SNOMED",   "72454006", "| Technetium-99m (substance) |"),  # ^99m^Technetium
        ("SCT",    "56609000"): ("SNOMED",   "56609000", "| Indium-111 (substance) |"),      # ^111^Indium
        ("SCT",    "48895003"): ("SNOMED",   "48895003", "| Indium-113m (substance) |"),     # ^113m^Indium
        ("SCT",    "66956003"): ("SNOMED",   "66956003", "| Iodine-122 (substance) |"),      # ^122^Iodine
        ("SCT",    "21572004"): ("SNOMED",   "21572004", "| Iodine-123 (substance) |"),      # ^123^Iodine
        ("SCT",    "68153002"): ("SNOMED",   "68153002", "| Xenon-123 (substance) |"),       # ^123^Xenon
        ("SCT",    "68630002"): ("SNOMED",   "68630002", "| Iodine-125 (substance) |"),      # ^125^Iodine
        ("SCT",    "27081007"): ("SNOMED",   "27081007", "| Xenon-127 (substance) |"),       # ^127^Xenon
        ("SCT",     "1368003"): ("SNOMED",    "1368003", "| Iodine-131 (substance) |"),      # ^131^Iodine
        ("SCT",     "3027009"): ("SNOMED",    "3027009", "| Barium-133 (substance) |"),      # ^133^Barium
        ("SCT",    "80751004"): ("SNOMED",   "80751004", "| Xenon-133 (substance) |"),       # ^133^Xenon
        ("MSH",  "C000615034"): ("MSH",    "C000615034", "| Terbium-149 |"),                 # ^149^Terbium
        ("SCT",    "14529005"): ("SNOMED",   "14529005", "| Gadolinium-153 (substance) |"),  # ^153^Gadolinium
        ("SCT",   "419804008"): ("SNOMED",  "419804008", "| Samarium-153 (substance) |"),    # ^153^Samarium
        ("MSH",  "C000615038"): ("MSH",    "C000615038", "| Terbium-161 |"),                 # ^161^Terbium
        ("NCIt",      "C1943"): ("NCIt",        "C1943", "| Holmium Ho-166 |"),              # ^166^Holmium
        ("SCT",    "41758004"): ("SNOMED",   "41758004", "| Ytterbium-169 (substance) |"),   # ^169^Ytterbium
        ("SCT",   "447553000"): ("SNOMED",  "447553000", "| Lutetium-177 (substance) |"),    # ^177^Lutetium
        ("SCT",     "6301006"): ("SNOMED",    "6301006", "| Tantalum-178 (substance) |"),    # ^178^Tantalum
        ("SCT",   "395865006"): ("SNOMED",  "395865006", "| Rhenium-186 (substance) |"),     # ^186^Rhenium
        ("SCT",   "423578007"): ("SNOMED",  "423578007", "| Rhenium-188 (substance) |"),     # ^188^Rhenium
        ("DCM",      "126604"): ("DCM",        "126604", "| ^191m^Iridium |"),               # ^191m^Iridium
        ("SCT",    "24301009"): ("SNOMED",   "24301009", "| Gold-198 (substance) |"),        # ^198^Gold
        ("SCT",    "70544003"): ("SNOMED",   "70544003", "| Gold-199 (substance) |"),        # ^199^Gold
        ("SCT",    "60057003"): ("SNOMED",   "60057003", "| Thallium-201 (substance) |"),    # ^201^Thallium
        ("SCT",    "47588004"): ("SNOMED",   "47588004", "| Lead-203 (substance) |"),        # ^203^Lead
        ("MSH",  "C000615146"): ("MSH",    "C000615146", "| Astatine-211 |"),                # ^211^Astatine
        ("SCT",    "87401005"): ("SNOMED",   "87401005", "| Lead-212 (substance) |"),        # ^212^Lead
        ("MSH",  "C000615137"): ("MSH",    "C000615137", "| Bismuth-213 |"),                 # ^213^Bismuth
        ("SCT",    "24853006"): ("SNOMED",   "24853006", "| Radium-223 (substance) |"),      # ^223^Radium
        ("SCT",    "32059002"): ("SNOMED",   "32059002", "| Actinium-225 (substance) |"),    # ^225^Actinium
    }

    # Dictionary mapping the codes of the NM/SPECT radionuclides of DICOM CID 18 to their half-life
    # Key: Tuple with the coding scheme designator and code value as used in nm_spect_radionuclide_name_2_code (e.g.: ("SNOMED", "77004003"))
    # Value: Tuple with:
    #   - half-life in seconds, as in DICOM Radionuclide Half Life (0018,1075)
    # Note(s):
    #  - Source: IAEA Nuclear Data Section, LiveChart of Nuclides (evaluated ENSDF data), https://nds.iaea.org/relnsd/v1/data
    #  - For the metastable radionuclides (e.g. "^99m^Technetium") the values are those of the lowest long-lived isomeric state.
    #  - The comment at the end of the line gives the DICOM Code Meaning, the half-life in its common unit, and the decay mode(s).
    nm_spect_radionuclide_coded_2_half_life: ClassVar[Mapping[tuple[str, str], tuple[float]]] = {
        ("SNOMED",    "71647005"): (179874478100.0,),  # ^14^Carbon 5700 y (B- 100%)
        ("SNOMED",    "77004003"): (6586.2,),          # ^18^Fluorine 109.77 min (EC+B+ 100%)
        ("SNOMED",    "71633006"): (82104810.0,),      # ^22^Sodium 2.6018 y (EC+B+ 100%)
        ("SNOMED",    "58541008"): (53841.6,),         # ^24^Sodium 14.956 h (B- 100%)
        ("SNOMED",    "32505007"): (1232582.4,),       # ^32^Phosphorus 14.266 d (B- 100%)
        ("SNOMED",    "59844004"): (44478.0,),         # ^42^Potassium 12.355 h (B- 100%)
        ("SNOMED",     "8202008"): (80280.0,),         # ^43^Potassium 22.3 h (B- 100%)
        ("MSH",     "C000615359"): (289370.88,),       # ^47^Scandium 3.3492 d (B- 100%)
        ("SNOMED",    "52745005"): (2393625.6,),       # ^51^Chromium 27.704 d (EC 100%)
        ("SNOMED",    "27054007"): (23478336.0,),      # ^57^Cobalt 271.74 d (EC 100%)
        ("SNOMED",    "89272005"): (6122304.0,),       # ^58^Cobalt 70.86 d (EC+B+ 100%)
        ("SNOMED",    "68580003"): (3843936.0,),       # ^59^Iron 44.490 d (B- 100%)
        ("SNOMED",     "5405008"): (166344192.0,),     # ^60^Cobalt 1925.28 d (B- 100%)
        ("SNOMED",     "3932008"): (45722.16,),        # ^64^Copper 12.7006 h (EC+B+ 61.5%, B- 38.5%)
        ("SNOMED",    "53700003"): (222588.0,),        # ^67^Copper 61.83 h (B- 100%)
        ("SNOMED",     "2008008"): (281810.88,),       # ^67^Gallium 3.2617 d (EC 100%)
        ("SNOMED",    "43239002"): (10348992.0,),      # ^75^Selenium 119.78 d (EC 100%)
        ("SNOMED",    "61716009"): (13.1,),            # ^81m^Krypton 13.10 s (IT 99.9975%, EC 0.0025%)
        ("SNOMED",    "34127007"): (338889828.0,),     # ^85^Krypton 10.739 y (B- 100%)
        ("SNOMED",   "111084009"): (5602953.6,),       # ^85^Strontium 64.849 d (EC 100%)
        ("SNOMED",    "78023008"): (10134.0,),         # ^87m^Strontium 2.815 h (IT 99.7%, EC 0.3%)
        ("SNOMED",     "7770004"): (4368643.2,),       # ^89^Strontium 50.563 d (B- 100%)
        ("SNOMED",    "14691008"): (230580.0,),        # ^90^Yttrium 64.05 h (B- 100%)
        ("SNOMED",    "23788009"): (244512.0,),        # ^97^Ruthenium 2.83 d (EC+B+ 100%)
        ("SNOMED",    "72454006"): (21625.92,),        # ^99m^Technetium 6.0072 h (IT 99.9963%, B- 0.0037%)
        ("SNOMED",    "56609000"): (242326.08,),       # ^111^Indium 2.8047 d (EC 100%)
        ("SNOMED",    "48895003"): (5968.56,),         # ^113m^Indium 99.476 min (IT 100%)
        ("SNOMED",    "66956003"): (217.8,),           # ^122^Iodine 3.63 min (EC+B+ 100%)
        ("SNOMED",    "21572004"): (47602.8,),         # ^123^Iodine 13.2230 h (EC+B+ 100%)
        ("SNOMED",    "68153002"): (7380.0,),          # ^123^Xenon 2.050 h (EC+B+ 100%)
        ("SNOMED",    "68630002"): (5132764.8,),       # ^125^Iodine 59.407 d (EC 100%)
        ("SNOMED",    "27081007"): (3140294.4,),       # ^127^Xenon 36.346 d (EC 100%)
        ("SNOMED",     "1368003"): (693377.28,),       # ^131^Iodine 8.0252 d (B- 100%)
        ("SNOMED",     "3027009"): (332957126.0,),     # ^133^Barium 10.551 y (EC 100%)
        ("SNOMED",    "80751004"): (453384.0,),        # ^133^Xenon 5.2475 d (B- 100%)
        ("MSH",     "C000615034"): (14832.0,),         # ^149^Terbium 4.12 h (EC+B+ 83.3%, A 16.7%)
        ("SNOMED",    "14529005"): (20770560.0,),      # ^153^Gadolinium 240.4 d (EC 100%)
        ("SNOMED",   "419804008"): (166622.4,),        # ^153^Samarium 46.284 h (B- 100%)
        ("MSH",     "C000615038"): (595296.0,),        # ^161^Terbium 6.89 d (B- 100%)
        ("NCIt",         "C1943"): (96566.4,),         # ^166^Holmium 26.824 h (B- 100%)
        ("SNOMED",    "41758004"): (2766182.4,),       # ^169^Ytterbium 32.016 d (EC 100%)
        ("SNOMED",   "447553000"): (574067.52,),       # ^177^Lutetium 6.6443 d (B- 100%)
        ("SNOMED",     "6301006"): (8496.0,),          # ^178^Tantalum 2.36 h (EC+B+ 100%)
        ("SNOMED",   "395865006"): (321278.4,),        # ^186^Rhenium 3.7185 d (B- 92.5%, EC 7.5%)
        ("SNOMED",   "423578007"): (61218.0,),         # ^188^Rhenium 17.005 h (B- 100%)
        ("DCM",         "126604"): (4.899,),           # ^191m^Iridium 4.899 s (IT 100%)
        ("SNOMED",    "24301009"): (232770.24,),       # ^198^Gold 2.6941 d (B- 100%)
        ("SNOMED",    "70544003"): (271209.6,),        # ^199^Gold 3.139 d (B- 100%)
        ("SNOMED",    "60057003"): (262828.8,),        # ^201^Thallium 3.0420 d (EC 100%)
        ("SNOMED",    "47588004"): (186912.0,),        # ^203^Lead 51.92 h (EC 100%)
        ("MSH",     "C000615146"): (25970.4,),         # ^211^Astatine 7.214 h (EC 58.2%, A 41.8%)
        ("SNOMED",    "87401005"): (38239.2,),         # ^212^Lead 10.622 h (B- 100%)
        ("MSH",     "C000615137"): (2735.4,),          # ^213^Bismuth 45.59 min (B- 97.86%, A 2.14%)
        ("SNOMED",    "24853006"): (987552.0,),        # ^223^Radium 11.43 d (A 100%, 14C 0.000000089%)
        ("SNOMED",    "32059002"): (857088.0,),        # ^225^Actinium 9.920 d (A 100%, 14C 0.00000000053%)
    }




