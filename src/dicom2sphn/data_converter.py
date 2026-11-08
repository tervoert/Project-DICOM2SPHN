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




