"""
dw_frame_processor.py:
    Part of the example dicom2sphn package.
    It processes the DICOM(web) Frame level data.
"""
from datetime import timedelta
from time import time

from pydicom import Dataset
from pynetdicom import sop_class

from .context import Context
from .dicom_frame_reader import get_frame_metadata_from_dicom
from .sphn_concepts.sphn_computed_tomography_imaging_frame import (
    SPHNComputedTomographyImagingFrame,
)
from .sphn_concepts.sphn_imaging_frame import SPHNImagingFrame
from .sphn_concepts.sphn_magnetic_resonance_imaging_frame import (
    SPHNMagneticResonanceImagingFrame,
)
from .sphn_concepts.sphn_positron_emission_tomography_imaging_frame import (
    SPHNPositronEmissionTomographyImagingFrame,
)
from .sphn_concepts.sphn_xray_imaging_frame import SPHNXRayImagingFrame


class DWFrameProcessor:

    def __init__(self):
        """ 
        Initializes the instance
        """

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    def process(self, instance_ds: Dataset, current_frame_number: int, context: Context, indent: int=0) -> None:
        """
        Processes the Instance level data by traversing the DICOM Patient - Study - Series - Instance hierarchical tree using 
        the DICOMweb API and collecting the metadata related to the SPHN ImagingFrame and its related SPHN concepts.
        """

        # Checks
        assert isinstance(instance_ds, Dataset)
        assert isinstance(current_frame_number, int) and current_frame_number > 0
        assert isinstance(context, Context)
        assert isinstance(indent,int) and indent>=0

        # Get the logger, data_store, and dw_client from the context
        logger = context.logger
        data_store = context.data_store
        sop_class_uid = data_store.sop_class_uid

        logger.debug(" "*(indent+0) + "FrameProcessor: Start processing...")
        start_time_t1 = time()

        # Update the DataStore
        data_store.current_frame_number = current_frame_number

        # -------------------------------------------------------------------------------------------------------------
        # Start collecting metadata from the entire DICOM Instance dataset for the current SPHN ImagingFrame
        # -------------------------------------------------------------------------------------------------------------

        logger.debug(" "*(indent+2) + "Start collecting more DICOM metadata from instance_ds for the current ImagingFrame")

        # Get SPHN ImagingFrame metadata from the entire DICOM SOP Instance Header
        get_frame_metadata_from_dicom(instance_ds, current_frame_number, context, indent=indent+4)

        logger.debug(" "*(indent+2) + "Done  collecting more DICOM metadata from instance_ds for the current ImagingFrame")

        # -------------------------------------------------------------------------------------------------------------
        # Done  collecting metadata from the entire DICOM Instance dataset for the current SPHN ImagingFrame
        # -------------------------------------------------------------------------------------------------------------

        # ---------------------------------------------------------------------------------------------------------
        # Creating the SPHN ImagingFrame
        # ---------------------------------------------------------------------------------------------------------

        logger.debug(" "*(indent+2) + "Start creating the SPHN ImagingFrame")

        assert data_store.sphn_imaging_frame is None
        assert data_store.sphn_schema is not None
        assert sop_class_uid is not None

        # -------------------------------------------------------------------------------------------------------------

        # Supported DICOM SOP Classes by the dcm2sphn example:
        # +-----------+-------------------------------------------------------------+--------------------------------+----------+-----------------------------------------+-------------------------------------------------------------+
        # | Supported | SOP Class                                                   | SOP Class UID                  | Modality | IOD                                     |                                                             |
        # +-----------+-------------------------------------------------------------+--------------------------------+----------+-----------------------------------------+-------------------------------------------------------------+      
        # | No        | Computed Radiography Image Storage                          | 1.2.840.10008.5.1.4.1.1.1      | CR       | Computed Radiography Image IOD          | sop_class.ComputedRadiographyImageStorage                   |
        # | No        | Digital X-Ray Image Storage – For Presentation              | 1.2.840.10008.5.1.4.1.1.1.1    | DX       | Digital X-Ray Image IOD                 | sop_class.DigitalXRayImageStorageForPresentation            |
        # | No        | Digital X-Ray Image Storage – For Processing                | 1.2.840.10008.5.1.4.1.1.1.1.1  | DX       | Digital X-Ray Image IOD                 | sop_class.DigitalXRayImageStorageForProcessing              |
        # | No        | Digital Mammography X-Ray Image Storage – For Presentation  | 1.2.840.10008.5.1.4.1.1.1.2    | MG       | Digital Mammography X-Ray Image IOD     | sop_class.DigitalMammographyXRayImageStorageForPresentation |
        # | No        | Digital Mammography X-Ray Image Storage – For Processing    | 1.2.840.10008.5.1.4.1.1.1.2.1  | MG       | Digital Mammography X-Ray Image IOD     | sop_class.DigitalMammographyXRayImageStorageForProcessing   |
        # | No        | Digital Intra-Oral X-Ray Image Storage - For Presentation   | 1.2.840.10008.5.1.4.1.1.1.3    | IO       | Digital Intra-Oral X-Ray Image IOD      | sop_class.DigitalIntraOralXRayImageStorageForPresentation   |
        # | No        | Digital Intra-Oral X-Ray Image Storage - For Processing     | 1.2.840.10008.5.1.4.1.1.1.3.1  | IO       | Digital Intra-Oral X-Ray Image IOD      | sop_class.DigitalIntraOralXRayImageStorageForProcessing     |
        # | Yes       | CT Image Storage                                            | 1.2.840.10008.5.1.4.1.1.2      | CT       | CT Image IOD                            | sop_class.CTImageStorage                                    |
        # | No        | Enhanced CT Image Storage                                   | 1.2.840.10008.5.1.4.1.1.2.1    | CT       | Enhanced CT Image IOD                   | sop_class.EnhancedCTImageStorage                            |
        # | No        | Legacy Converted Enhanced CT Image Storage                  | 1.2.840.10008.5.1.4.1.1.2.2    | CT       | Legacy Converted Enhanced CT Image IOD  | sop_class.LegacyConvertedEnhancedCTImageStorage             |
        # | No        | CT Image Storage - For Processsing                          | 1.2.840.10008.5.1.4.1.1.2.3    | CT       | CT Image IOD                            | < new >                                                     |
        # | No        | Enhanced CT Image Storage - For Processing                  | 1.2.840.10008.5.1.4.1.1.2.4    | CT       | Enhanced CT Image IOD                   | < new >                                                     |
        # | No        | Legacy Converted Enhanced CT Image Storage - For Processing | 1.2.840.10008.5.1.4.1.1.2.5    | CT       | Legacy Converted Enhanced CT Image IOD  | < new >                                                     |
        # | No        | Ultrasound Multi-frame Image Storage                        | 1.2.840.10008.5.1.4.1.1.3.1    | US       | Ultrasound Multi-frame Image IOD        | sop_class.UltrasoundMultiFrameImageStorage                  |
        # | Yes       | MR Image Storage                                            | 1.2.840.10008.5.1.4.1.1.4      | MR       | MR Image IOD                            | sop_class.MRImageStorage                                    |
        # | No        | Enhanced MR Image Storage                                   | 1.2.840.10008.5.1.4.1.1.4.1    | MR       | Enhanced MR Image IOD                   | sop_class.EnhancedMRImageStorage                            |
        # | No        | MR Spectroscopy Storage                                     | 1.2.840.10008.5.1.4.1.1.4.2    | MR       | MR Spectroscopy IOD                     | sop_class.MRSpectroscopyStorage                             |
        # | No        | Enhanced MR Color Image Storage                             | 1.2.840.10008.5.1.4.1.1.4.3    | MR       | Enhanced MR Color Image IOD             | sop_class.EnhancedMRColorImageStorage                       |
        # | No        | Legacy Converted Enhanced MR Image Storage                  | 1.2.840.10008.5.1.4.1.1.4.4    | MR       | Legacy Converted Enhanced MR Image IOD  | sop_class.LegacyConvertedEnhancedMRImageStorage             |
        # | No        | Ultrasound Image Storage                                    | 1.2.840.10008.5.1.4.1.1.6.1    | US       | Ultrasound Image IOD                    | sop_class.UltrasoundImageStorage                            |
        # | No        | Enhanced US Volume Storage                                  | 1.2.840.10008.5.1.4.1.1.6.2    | US       | Enhanced US Volume IOD                  | sop_class.EnhancedUSVolumeStorage                           |
        # | No        | Photoacoustic Image Storage                                 | 1.2.840.10008.5.1.4.1.1.6.3    | PA       | Photoacoustic Image IOD                 | sop_class.PhotoacousticImageStorage                         |
        # | No        | X-Ray Angiographic Image Storage                            | 1.2.840.10008.5.1.4.1.1.12.1   | XA       | X-Ray Angiographic Image IOD            | sop_class.XRayAngiographicImageStorage                      |
        # | No        | Enhanced XA Image Storage                                   | 1.2.840.10008.5.1.4.1.1.12.1.1 | XA       | Enhanced XA Image IOD                   | sop_class.EnhancedXAImageStorage                            |
        # | No        | X-Ray Radiofluoroscopic Image Storage                       | 1.2.840.10008.5.1.4.1.1.12.2   | RF       | X-Ray Radiofluoroscopic Image IOD       | sop_class.XRayRadiofluoroscopicImageStorage                 |
        # | No        | Enhanced XRF Image Storage                                  | 1.2.840.10008.5.1.4.1.1.12.2.1 | RF       | Enhanced XRF Image IOD                  | sop_class.EnhancedXRFImageStorage                           |
        # | No        | X-Ray 3D Angiographic Image Storage                         | 1.2.840.10008.5.1.4.1.1.13.1.1 | XA       | X-Ray 3D Angiographic Image IOD         | sop_class.XRay3DAngiographicImageStorage                    |
        # | No        | X-Ray 3D Craniofacial Image Storage                         | 1.2.840.10008.5.1.4.1.1.13.1.2 |          | X-Ray 3D Craniofacial Image IOD         | sop_class.XRay3DCraniofacialImageStorage                    |
        # | No        | Breast Tomosynthesis Image Storage                          | 1.2.840.10008.5.1.4.1.1.13.1.3 |          | Breast Tomosynthesis Image IOD          | sop_class.BreastTomosynthesisImageStorage                   |
        # | No        | Breast Projection X-Ray Image Storage – For Presentation    | 1.2.840.10008.5.1.4.1.1.13.1.4 |          | Breast Projection X-Ray Image IOD       | sop_class.BreastProjectionXRayImageStorageForPresentation   |
        # | No        | Breast Projection X-Ray Image Storage – For Processing      | 1.2.840.10008.5.1.4.1.1.13.1.5 |          | Breast Projection X-Ray Image IOD       | sop_class.BreastProjectionXRayImageStorageForProcessing     |
        # | No        | Nuclear Medicine Image Storage                              | 1.2.840.10008.5.1.4.1.1.20     | NM       | Nuclear Medicine Image IOD              | sop_class.NuclearMedicineImageStorage                       |
        # | No        | Segmentation Storage                                        | 1.2.840.10008.5.1.4.1.1.66.4   | SEG      | Segmentation IOD                        | sop_class.SegmentationStorage                               |
        # | No        | VL Whole Slide Microscopy Image Storage                     | 1.2.840.10008.5.1.4.1.1.77.1.6 | SM       | VL Whole Slide Microscopy Image IOD     | sop_class.VLWholeSlideMicroscopyImageStorage                |
        # | Yes       | Positron Emission Tomography Image Storage                  | 1.2.840.10008.5.1.4.1.1.128    | PT       | Positron Emission Tomography Image IOD  | sop_class.PositronEmissionTomographyImageStorage            |
        # | No        | Legacy Converted Enhanced PET Image Storage                 | 1.2.840.10008.5.1.4.1.1.128.1  | PT       | Legacy Converted Enhanced PET Image IOD | sop_class.LegacyConvertedEnhancedPETImageStorage            |
        # | No        | Enhanced PET Image Storage                                  | 1.2.840.10008.5.1.4.1.1.130    | PT       | Enhanced PET Image IOD                  | sop_class.EnhancedPETImageStorage                           |
        # +-----------+-------------------------------------------------------------+--------------------------------+----------+-----------------------------------------+-------------------------------------------------------------+
        # For DICOM standard SOP classes see: https://dicom.nema.org/medical/dicom/current/output/html/part04.html#sect_B.5
        # For the pydicom / pynetdicom SOP classes see: https://pydicom.github.io/pynetdicom/stable/reference/sop_classes.html

        # -------------------------------------------------------------------------------------------------------------

        # Selecting the general or one of the specific SPHN ImagingFrames based on the SOP Class UID of the DICOM Instance dataset
        if sop_class_uid in [sop_class.CTImageStorage]:
            # Create a specific SPHN ComputedTomographyImagingFrame
            logger.debug(" "*(indent+4) + "Creating an SPHN CT-ImagingFrame")
            sphn_imaging_frame = SPHNComputedTomographyImagingFrame(
                sphn_schema = data_store.sphn_schema,
                has_start_datetime = None,
                has_end_datetime = None,
                has_type_list = data_store.sphn_imagingframe_type_valueset_member_list,
                has_image_dimensions = data_store.sphn_image_dimensions,
                has_body_site_list = data_store.sphn_body_site_list,
                has_algorithm_list = data_store.sphn_data_compression_algorithm_list,
                has_content_qualification = data_store.sphn_imagingframe_content_qualification_valueset_member,
                has_imaging_metric = None,
                has_anatomical_projection = None
            )
        elif sop_class_uid in [sop_class.MRImageStorage]:
            # Create a specific SPHN MagneticResonanceImagingFrame
            logger.debug(" "*(indent+4) + "Creating an SPHN MR-ImagingFrame")
            sphn_imaging_frame = SPHNMagneticResonanceImagingFrame(
                sphn_schema = data_store.sphn_schema,
                has_start_datetime = None,
                has_end_datetime = None,
                has_type_list = data_store.sphn_imagingframe_type_valueset_member_list,
                has_image_dimensions = data_store.sphn_image_dimensions,
                has_body_site_list = data_store.sphn_body_site_list,
                has_algorithm_list = data_store.sphn_data_compression_algorithm_list,
                has_content_qualification = data_store.sphn_imagingframe_content_qualification_valueset_member,
                has_imaging_metric = None,
                has_anatomical_projection = None
            )
        elif sop_class_uid in [sop_class.PositronEmissionTomographyImageStorage]:
            # Create a specific SPHN PositronEmissionTomographyImagingFrame
            logger.debug(" "*(indent+4) + "Creating an SPHN PET-ImagingFrame")
            sphn_imaging_frame = SPHNPositronEmissionTomographyImagingFrame(
                sphn_schema = data_store.sphn_schema,
                has_start_datetime = None,
                has_end_datetime = None,
                has_type_list = data_store.sphn_imagingframe_type_valueset_member_list,
                has_image_dimensions = data_store.sphn_image_dimensions,
                has_body_site_list = data_store.sphn_body_site_list,
                has_algorithm_list = data_store.sphn_data_compression_algorithm_list,
                has_content_qualification = data_store.sphn_imagingframe_content_qualification_valueset_member,
                has_imaging_metric = None,
                has_anatomical_projection = None
            )
        elif sop_class_uid in ['empty_for_now']:
            # Create a specific SPHN XRayImagingFrame
            logger.debug(" "*(indent+4) + "Creating an SPHN XRay-ImagingFrame")
            sphn_imaging_frame = SPHNXRayImagingFrame(
                sphn_schema = data_store.sphn_schema,
                has_start_datetime = None,
                has_end_datetime = None,
                has_type_list = data_store.sphn_imagingframe_type_valueset_member_list,
                has_image_dimensions = data_store.sphn_image_dimensions,
                has_body_site_list = data_store.sphn_body_site_list,
                has_algorithm_list = data_store.sphn_data_compression_algorithm_list,
                has_content_qualification = data_store.sphn_imagingframe_content_qualification_valueset_member,
                has_imaging_metric = None,
                has_anatomical_projection = None
            )
        else:
            # Create a general SPHN ImagingFrame
            logger.debug(" "*(indent+4) + "Creating a general SPHN ImagingFrame")
            sphn_imaging_frame = SPHNImagingFrame(
                sphn_schema = data_store.sphn_schema,
                has_start_datetime = None,
                has_end_datetime = None,
                has_type_list = data_store.sphn_imagingframe_type_valueset_member_list,
                has_image_dimensions = data_store.sphn_image_dimensions,
                has_body_site_list = data_store.sphn_body_site_list,
                has_algorithm_list = data_store.sphn_data_compression_algorithm_list,
                has_content_qualification = data_store.sphn_imagingframe_content_qualification_valueset_member,
                has_imaging_metric = None,
                has_anatomical_projection = None
            )

        # Add the SPHN ImagingFrame to the DataStore
        data_store.sphn_imaging_frame = sphn_imaging_frame

        logger.debug(" "*(indent+2) + "Done  creating the SPHN ImagingFrame")


        # ---------------------------------------------------------------------------------------------------------
        # ---------------------------------------------------------------------------------------------------------

        stop_time_t1 = time()
        logger.debug(" "*(indent+0) + "FrameProcessor: Done processing..." +
                    " in: " + str(timedelta(seconds=(stop_time_t1 - start_time_t1)))
        )
        logger.debug("")

        # Statistics
        data_store.increment_dicom_frames_processed_counter()

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions - related to processing the DICOM Instance dataset and collecting the metadata related to the SPHN ImagingFrame and its related SPHN concepts
    # -----------------------------------------------------------------------------------------------------------------
