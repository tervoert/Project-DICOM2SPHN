# Supported DICOM SOP Classes

This table lists the DICOM SOP Classes that DICOM2SPHN can process. It contains all SOP Classes from [Table B.5-1 "Standard SOP Classes"](https://dicom.nema.org/medical/dicom/current/output/chtml/part04/sect_b.5.html) of DICOM PS3.4 (edition 2026d) whose IOD contains image data.

SOP Classes without image data are not listed, for example structured reports, presentation states, waveforms, encapsulated documents, measurements, spatial registrations and the RT objects without images. *MR Spectroscopy Storage* is an exception: it has no image data, but it is listed.

## Columns

| Column | Meaning |
|---|---|
| Supported | `Yes` if the SOP Class is in `allowed_sop_classes` in [config-example.toml](config-example.toml) |
| SOP Class | Name of the SOP Class in DICOM PS3.4 |
| SOP Class UID | The SOP Class UID, as used in `allowed_sop_classes` |
| Modality | Value of the DICOM Modality (0008,0060) attribute, as required by the IOD in DICOM PS3.3. `any` means that the IOD allows any modality |
| IOD | The Information Object Definition (DICOM PS3.3) |
| pydicom | The [pydicom UID](https://pydicom.github.io/pydicom/stable/reference/uid.html) constant. Empty if pydicom has no constant for this UID |
| SPHN ImagingSeries / ImagingFrame | The SPHN concepts that DICOM2SPHN creates: for example *X-Ray* creates an `XRayImagingSeries` and an `XRayImagingFrame`. *General* creates an `ImagingSeries` and an `ImagingFrame` |

## Table

| Supported | SOP Class | SOP Class UID | Modality | IOD | pydicom | SPHN ImagingSeries / ImagingFrame |
|---|---|---|---|---|---|---|
| Yes | Computed Radiography Image Storage | `1.2.840.10008.5.1.4.1.1.1` | CR | Computed Radiography Image IOD | `pydicom.uid.ComputedRadiographyImageStorage` | X-Ray |
| Yes | Digital X-Ray Image Storage - For Presentation | `1.2.840.10008.5.1.4.1.1.1.1` | DX | Digital X-Ray Image IOD | `pydicom.uid.DigitalXRayImageStorageForPresentation` | X-Ray |
| Yes | Digital X-Ray Image Storage - For Processing | `1.2.840.10008.5.1.4.1.1.1.1.1` | DX | Digital X-Ray Image IOD | `pydicom.uid.DigitalXRayImageStorageForProcessing` | X-Ray |
| Yes | Digital Mammography X-Ray Image Storage - For Presentation | `1.2.840.10008.5.1.4.1.1.1.2` | MG | Digital Mammography X-Ray Image IOD | `pydicom.uid.DigitalMammographyXRayImageStorageForPresentation` | X-Ray |
| Yes | Digital Mammography X-Ray Image Storage - For Processing | `1.2.840.10008.5.1.4.1.1.1.2.1` | MG | Digital Mammography X-Ray Image IOD | `pydicom.uid.DigitalMammographyXRayImageStorageForProcessing` | X-Ray |
| Yes | Digital Intra-Oral X-Ray Image Storage - For Presentation | `1.2.840.10008.5.1.4.1.1.1.3` | IO | Digital Intra-Oral X-Ray Image IOD | `pydicom.uid.DigitalIntraOralXRayImageStorageForPresentation` | X-Ray |
| Yes | Digital Intra-Oral X-Ray Image Storage - For Processing | `1.2.840.10008.5.1.4.1.1.1.3.1` | IO | Digital Intra-Oral X-Ray Image IOD | `pydicom.uid.DigitalIntraOralXRayImageStorageForProcessing` | X-Ray |
| Yes | CT Image Storage | `1.2.840.10008.5.1.4.1.1.2` | CT | CT Image IOD | `pydicom.uid.CTImageStorage` | Computed Tomography |
| Yes | Enhanced CT Image Storage | `1.2.840.10008.5.1.4.1.1.2.1` | CT | Enhanced CT Image IOD | `pydicom.uid.EnhancedCTImageStorage` | Computed Tomography |
| Yes | Legacy Converted Enhanced CT Image Storage | `1.2.840.10008.5.1.4.1.1.2.2` | CT | Legacy Converted Enhanced CT Image IOD | `pydicom.uid.LegacyConvertedEnhancedCTImageStorage` | Computed Tomography |
| No | CT Image Storage - For Processing | `1.2.840.10008.5.1.4.1.1.2.3` | CT | CT Image IOD |  | General |
| No | Enhanced CT Image Storage - For Processing | `1.2.840.10008.5.1.4.1.1.2.4` | CT | Enhanced CT Image IOD |  | General |
| No | Legacy Converted Enhanced CT Image Storage - For Processing | `1.2.840.10008.5.1.4.1.1.2.5` | CT | Legacy Converted Enhanced CT Image IOD |  | General |
| Yes | Ultrasound Multi-frame Image Storage | `1.2.840.10008.5.1.4.1.1.3.1` | US | Ultrasound Multi-frame Image IOD | `pydicom.uid.UltrasoundMultiFrameImageStorage` | General |
| Yes | MR Image Storage | `1.2.840.10008.5.1.4.1.1.4` | MR | MR Image IOD | `pydicom.uid.MRImageStorage` | Magnetic Resonance |
| Yes | Enhanced MR Image Storage | `1.2.840.10008.5.1.4.1.1.4.1` | MR | Enhanced MR Image IOD | `pydicom.uid.EnhancedMRImageStorage` | Magnetic Resonance |
| Yes | MR Spectroscopy Storage | `1.2.840.10008.5.1.4.1.1.4.2` | MR | MR Spectroscopy IOD | `pydicom.uid.MRSpectroscopyStorage` | General |
| Yes | Enhanced MR Color Image Storage | `1.2.840.10008.5.1.4.1.1.4.3` | MR | Enhanced MR Color Image IOD | `pydicom.uid.EnhancedMRColorImageStorage` | Magnetic Resonance |
| Yes | Legacy Converted Enhanced MR Image Storage | `1.2.840.10008.5.1.4.1.1.4.4` | MR | Legacy Converted Enhanced MR Image IOD | `pydicom.uid.LegacyConvertedEnhancedMRImageStorage` | Magnetic Resonance |
| Yes | Ultrasound Image Storage | `1.2.840.10008.5.1.4.1.1.6.1` | US | Ultrasound Image IOD | `pydicom.uid.UltrasoundImageStorage` | General |
| Yes | Enhanced US Volume Storage | `1.2.840.10008.5.1.4.1.1.6.2` | US/IVUS | Enhanced US Volume IOD | `pydicom.uid.EnhancedUSVolumeStorage` | General |
| Yes | Photoacoustic Image Storage | `1.2.840.10008.5.1.4.1.1.6.3` | PA | Photoacoustic Image IOD | `pydicom.uid.PhotoacousticImageStorage` | General |
| Yes | Secondary Capture Image Storage | `1.2.840.10008.5.1.4.1.1.7` | any | Secondary Capture Image IOD | `pydicom.uid.SecondaryCaptureImageStorage` | General |
| Yes | Multi-frame Single Bit Secondary Capture Image Storage | `1.2.840.10008.5.1.4.1.1.7.1` | any | Multi-frame Single Bit Secondary Capture Image IOD | `pydicom.uid.MultiFrameSingleBitSecondaryCaptureImageStorage` | General |
| Yes | Multi-frame Grayscale Byte Secondary Capture Image Storage | `1.2.840.10008.5.1.4.1.1.7.2` | any | Multi-frame Grayscale Byte Secondary Capture Image IOD | `pydicom.uid.MultiFrameGrayscaleByteSecondaryCaptureImageStorage` | General |
| Yes | Multi-frame Grayscale Word Secondary Capture Image Storage | `1.2.840.10008.5.1.4.1.1.7.3` | any | Multi-frame Grayscale Word Secondary Capture Image IOD | `pydicom.uid.MultiFrameGrayscaleWordSecondaryCaptureImageStorage` | General |
| Yes | Multi-frame True Color Secondary Capture Image Storage | `1.2.840.10008.5.1.4.1.1.7.4` | any | Multi-frame True Color Secondary Capture Image IOD | `pydicom.uid.MultiFrameTrueColorSecondaryCaptureImageStorage` | General |
| Yes | X-Ray Angiographic Image Storage | `1.2.840.10008.5.1.4.1.1.12.1` | XA | X-Ray Angiographic Image IOD | `pydicom.uid.XRayAngiographicImageStorage` | X-Ray |
| Yes | Enhanced XA Image Storage | `1.2.840.10008.5.1.4.1.1.12.1.1` | XA | Enhanced XA Image IOD | `pydicom.uid.EnhancedXAImageStorage` | X-Ray |
| Yes | X-Ray Radiofluoroscopic Image Storage | `1.2.840.10008.5.1.4.1.1.12.2` | RF | X-Ray Radiofluoroscopic Image IOD | `pydicom.uid.XRayRadiofluoroscopicImageStorage` | X-Ray |
| Yes | Enhanced XRF Image Storage | `1.2.840.10008.5.1.4.1.1.12.2.1` | RF | Enhanced XRF Image IOD | `pydicom.uid.EnhancedXRFImageStorage` | X-Ray |
| Yes | X-Ray 3D Angiographic Image Storage | `1.2.840.10008.5.1.4.1.1.13.1.1` | XA | X-Ray 3D Angiographic Image IOD | `pydicom.uid.XRay3DAngiographicImageStorage` | X-Ray |
| Yes | X-Ray 3D Craniofacial Image Storage | `1.2.840.10008.5.1.4.1.1.13.1.2` | DX | X-Ray 3D Craniofacial Image IOD | `pydicom.uid.XRay3DCraniofacialImageStorage` | X-Ray |
| Yes | Breast Tomosynthesis Image Storage | `1.2.840.10008.5.1.4.1.1.13.1.3` | MG | Breast Tomosynthesis Image IOD | `pydicom.uid.BreastTomosynthesisImageStorage` | X-Ray |
| Yes | Breast Projection X-Ray Image Storage - For Presentation | `1.2.840.10008.5.1.4.1.1.13.1.4` | MG | Breast Projection X-Ray Image IOD | `pydicom.uid.BreastProjectionXRayImageStorageForPresentation` | X-Ray |
| Yes | Breast Projection X-Ray Image Storage - For Processing | `1.2.840.10008.5.1.4.1.1.13.1.5` | MG | Breast Projection X-Ray Image IOD | `pydicom.uid.BreastProjectionXRayImageStorageForProcessing` | X-Ray |
| Yes | Intravascular Optical Coherence Tomography Image Storage - For Presentation | `1.2.840.10008.5.1.4.1.1.14.1` | IVOCT | Intravascular Optical Coherence Tomography Image IOD | `pydicom.uid.IntravascularOpticalCoherenceTomographyImageStorageForPresentation` | General |
| Yes | Intravascular Optical Coherence Tomography Image Storage - For Processing | `1.2.840.10008.5.1.4.1.1.14.2` | IVOCT | Intravascular Optical Coherence Tomography Image IOD | `pydicom.uid.IntravascularOpticalCoherenceTomographyImageStorageForProcessing` | General |
| Yes | Nuclear Medicine Image Storage | `1.2.840.10008.5.1.4.1.1.20` | NM | Nuclear Medicine Image IOD | `pydicom.uid.NuclearMedicineImageStorage` | General |
| Yes | Parametric Map Storage | `1.2.840.10008.5.1.4.1.1.30` | any | Parametric Map IOD | `pydicom.uid.ParametricMapStorage` | General |
| Yes | Segmentation Storage | `1.2.840.10008.5.1.4.1.1.66.4` | SEG | Segmentation IOD | `pydicom.uid.SegmentationStorage` | General |
| Yes | Label Map Segmentation Storage | `1.2.840.10008.5.1.4.1.1.66.7` | SEG | Segmentation IOD | `pydicom.uid.LabelMapSegmentationStorage` | General |
| Yes | Height Map Segmentation Storage | `1.2.840.10008.5.1.4.1.1.66.8` | SEG | Height Map Segmentation IOD | `pydicom.uid.HeightMapSegmentationStorage` | General |
| Yes | VL Endoscopic Image Storage | `1.2.840.10008.5.1.4.1.1.77.1.1` | ES | VL Endoscopic Image IOD | `pydicom.uid.VLEndoscopicImageStorage` | General |
| Yes | Video Endoscopic Image Storage | `1.2.840.10008.5.1.4.1.1.77.1.1.1` | ES | Video Endoscopic Image IOD | `pydicom.uid.VideoEndoscopicImageStorage` | General |
| Yes | VL Microscopic Image Storage | `1.2.840.10008.5.1.4.1.1.77.1.2` | GM | VL Microscopic Image IOD | `pydicom.uid.VLMicroscopicImageStorage` | General |
| Yes | Video Microscopic Image Storage | `1.2.840.10008.5.1.4.1.1.77.1.2.1` | GM | Video Microscopic Image IOD | `pydicom.uid.VideoMicroscopicImageStorage` | General |
| Yes | VL Slide-Coordinates Microscopic Image Storage | `1.2.840.10008.5.1.4.1.1.77.1.3` | SM | VL Slide-Coordinates Microscopic Image IOD | `pydicom.uid.VLSlideCoordinatesMicroscopicImageStorage` | General |
| Yes | VL Photographic Image Storage | `1.2.840.10008.5.1.4.1.1.77.1.4` | XC | VL Photographic Image IOD | `pydicom.uid.VLPhotographicImageStorage` | General |
| Yes | Video Photographic Image Storage | `1.2.840.10008.5.1.4.1.1.77.1.4.1` | XC | Video Photographic Image IOD | `pydicom.uid.VideoPhotographicImageStorage` | General |
| Yes | Ophthalmic Photography 8 Bit Image Storage | `1.2.840.10008.5.1.4.1.1.77.1.5.1` | OP | Ophthalmic Photography 8 Bit Image IOD | `pydicom.uid.OphthalmicPhotography8BitImageStorage` | General |
| Yes | Ophthalmic Photography 16 Bit Image Storage | `1.2.840.10008.5.1.4.1.1.77.1.5.2` | OP | Ophthalmic Photography 16 Bit Image IOD | `pydicom.uid.OphthalmicPhotography16BitImageStorage` | General |
| Yes | Ophthalmic Tomography Image Storage | `1.2.840.10008.5.1.4.1.1.77.1.5.4` | OPT | Ophthalmic Tomography Image IOD | `pydicom.uid.OphthalmicTomographyImageStorage` | General |
| Yes | Wide Field Ophthalmic Photography Stereographic Projection Image Storage | `1.2.840.10008.5.1.4.1.1.77.1.5.5` | OP | Wide Field Ophthalmic Photography Stereographic Projection Image IOD | `pydicom.uid.WideFieldOphthalmicPhotographyStereographicProjectionImageStorage` | General |
| Yes | Wide Field Ophthalmic Photography 3D Coordinates Image Storage | `1.2.840.10008.5.1.4.1.1.77.1.5.6` | OP | Wide Field Ophthalmic Photography 3D Coordinates Image IOD | `pydicom.uid.WideFieldOphthalmicPhotography3DCoordinatesImageStorage` | General |
| Yes | Ophthalmic Optical Coherence Tomography En Face Image Storage | `1.2.840.10008.5.1.4.1.1.77.1.5.7` | OPTENF | Ophthalmic Optical Coherence Tomography En Face Image IOD | `pydicom.uid.OphthalmicOpticalCoherenceTomographyEnFaceImageStorage` | General |
| Yes | Ophthalmic Optical Coherence Tomography B-scan Volume Analysis Storage | `1.2.840.10008.5.1.4.1.1.77.1.5.8` | OPTBSV | Ophthalmic Optical Coherence Tomography B-scan Volume Analysis IOD | `pydicom.uid.OphthalmicOpticalCoherenceTomographyBscanVolumeAnalysisStorage` | General |
| Yes | VL Whole Slide Microscopy Image Storage | `1.2.840.10008.5.1.4.1.1.77.1.6` | SM | VL Whole Slide Microscopy Image IOD | `pydicom.uid.VLWholeSlideMicroscopyImageStorage` | General |
| Yes | Dermoscopic Photography Image Storage | `1.2.840.10008.5.1.4.1.1.77.1.7` | DMS | Dermoscopic Photography Image IOD | `pydicom.uid.DermoscopicPhotographyImageStorage` | General |
| Yes | Confocal Microscopy Image Storage | `1.2.840.10008.5.1.4.1.1.77.1.8` | CFM | Confocal Microscopy Image IOD | `pydicom.uid.ConfocalMicroscopyImageStorage` | General |
| Yes | Confocal Microscopy Tiled Pyramidal Image Storage | `1.2.840.10008.5.1.4.1.1.77.1.9` | CFM | Confocal Microscopy Tiled Pyramidal Image IOD | `pydicom.uid.ConfocalMicroscopyTiledPyramidalImageStorage` | General |
| Yes | Ophthalmic Thickness Map Storage | `1.2.840.10008.5.1.4.1.1.81.1` | OPM | Ophthalmic Thickness Map IOD | `pydicom.uid.OphthalmicThicknessMapStorage` | General |
| Yes | Corneal Topography Map Storage | `1.2.840.10008.5.1.4.1.1.82.1` | OPM | Corneal Topography Map IOD | `pydicom.uid.CornealTopographyMapStorage` | General |
| Yes | Positron Emission Tomography Image Storage | `1.2.840.10008.5.1.4.1.1.128` | PT | Positron Emission Tomography Image IOD | `pydicom.uid.PositronEmissionTomographyImageStorage` | Positron Emission Tomography |
| Yes | Legacy Converted Enhanced PET Image Storage | `1.2.840.10008.5.1.4.1.1.128.1` | PT | Legacy Converted Enhanced PET Image IOD | `pydicom.uid.LegacyConvertedEnhancedPETImageStorage` | Positron Emission Tomography |
| Yes | Enhanced PET Image Storage | `1.2.840.10008.5.1.4.1.1.130` | PT | Enhanced PET Image IOD | `pydicom.uid.EnhancedPETImageStorage` | Positron Emission Tomography |
| Yes | RT Image Storage | `1.2.840.10008.5.1.4.1.1.481.1` | RTIMAGE | RT Image IOD | `pydicom.uid.RTImageStorage` | General |
| Yes | RT Dose Storage | `1.2.840.10008.5.1.4.1.1.481.2` | RTDOSE | RT Dose IOD | `pydicom.uid.RTDoseStorage` | General |
| Yes | Enhanced RT Image Storage | `1.2.840.10008.5.1.4.1.1.481.23` | RTIMAGE | Enhanced RT Image IOD | `pydicom.uid.EnhancedRTImageStorage` | General |
| Yes | Enhanced Continuous RT Image Storage | `1.2.840.10008.5.1.4.1.1.481.24` | RTIMAGE | Enhanced Continuous RT Image IOD | `pydicom.uid.EnhancedContinuousRTImageStorage` | General |

## Notes

- The three CT *For Processing* SOP Classes (`1.2.840.10008.5.1.4.1.1.2.3`, `.2.4` and `.2.5`) are not supported yet. pynetdicom 3.0.4 does not know them as Storage SOP Classes, so the configuration check would reject them. They are commented out in `allowed_sop_classes`.
- `pydicom.uid.LabelMapSegmentationStorage` and `pydicom.uid.HeightMapSegmentationStorage` are on the main branch of pydicom, but not yet in a released version (the latest release is pydicom 3.0.2).
- The mapping to the SPHN ImagingSeries and ImagingFrame is done in `dw_instance_processor.py` and `dw_frame_processor.py`.
- A SOP Class with *Supported* `Yes` is accepted by the configuration.

## Modalities without a SNOMED CT imaging procedure code

The SPHN `ImagingProcedure` gets a SNOMED CT code (a descendant of `363679005 |Imaging (procedure)|`) from `dicom_modality_code_dict` in `data_converter.py`. The codes are determined per DICOM study, from all modalities in the DICOM ModalitiesInStudy (0008,0061) attribute. A modality without a code is skipped (with a warning). If none of the modalities of a study has a code, no `ImagingProcedure` is created and the DICOM instances of that study are skipped. For example, a study with CT and SEG series gets the CT procedure code and both series are processed, but a study with only SEG series is skipped.

The following modalities in the table have no SNOMED CT imaging procedure code, because no suitable descendant of `363679005 |Imaging (procedure)|` exists in SNOMED CT (International edition 2026-07-01):

| Modality | SOP Classes |
|---|---|
| PA (Photoacoustic) | Photoacoustic Image Storage |
| ES (Endoscopy) | VL Endoscopic Image Storage, Video Endoscopic Image Storage |
| OPM (Ophthalmic Mapping) | Ophthalmic Thickness Map Storage, Corneal Topography Map Storage |
| RTDOSE (Radiotherapy Dose) | RT Dose Storage |

The modalities SEG (Segmentation), RTIMAGE (RT Image), GM (General Microscopy), SM (Slide Microscopy) and CFM (Confocal Microscopy) have no specific SNOMED CT code either, but get the general code `363679005 |Imaging (procedure)|`, so that their DICOM studies are not skipped.

The SOP Classes with modality `any` (the Secondary Capture SOP Classes and Parametric Map Storage) get the code of the modality in their DICOM dataset. For example, a Parametric Map with modality `MR` gets the MR procedure code, but a Secondary Capture with modality `OT` (Other) gets no code.
