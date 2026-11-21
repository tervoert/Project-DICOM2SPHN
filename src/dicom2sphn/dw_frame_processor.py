"""
dw_frame_processor.py:
    Part of the example dicom2sphn package.
    It processes the DICOM(web) Frame level data.
"""
import time
from datetime import timedelta

import pydicom
from pydicom import Dataset

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
        start_time_t1 = time.perf_counter()

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


        # ToDo: Edwin: Currently SPHN only allows one contrast agent administration event per imaging frame, change with the new SPHN schema version
        # Reference for DICOM UIDs: https://pydicom.github.io/pydicom/stable/reference/uid.html

        # Selecting the general or one of the specific SPHN ImagingFrames based on the SOP Class UID of the DICOM Instance dataset
        if sop_class_uid in [
            pydicom.uid.CTImageStorage, 
            pydicom.uid.EnhancedCTImageStorage,
            pydicom.uid.LegacyConvertedEnhancedCTImageStorage
            ]:
            # Create a specific SPHN ComputedTomographyImagingFrame
            logger.debug(" "*(indent+4) + "Creating an SPHN CT-ImagingFrame")
            sphn_imaging_frame = SPHNComputedTomographyImagingFrame(
                sphn_schema = data_store.sphn_schema,
                has_start_datetime = None,
                has_end_datetime = None,
                has_type_list = data_store.sphn_imagingframe_type_valueset_member_list,
                has_image_dimensions = data_store.sphn_image_dimensions,
                has_body_site_list = data_store.sphn_body_site_list_frame,
                has_algorithm_list = data_store.sphn_data_compression_algorithm_list,
                has_content_qualification = data_store.sphn_imagingframe_content_qualification_valueset_member,
                has_imaging_metric = None,
                has_anatomical_projection = None,
                has_contrast_agent_administration_event = data_store.sphn_contrast_agent_administration_event_list[0] \
                    if data_store.sphn_contrast_agent_administration_event_list is not None \
                        and len(data_store.sphn_contrast_agent_administration_event_list) > 0 else None
            )
        elif sop_class_uid in [
            pydicom.uid.MRImageStorage,
            pydicom.uid.EnhancedMRImageStorage,
            pydicom.uid.EnhancedMRColorImageStorage,
            pydicom.uid.LegacyConvertedEnhancedMRImageStorage
            ]:
            # Create a specific SPHN MagneticResonanceImagingFrame
            logger.debug(" "*(indent+4) + "Creating an SPHN MR-ImagingFrame")
            sphn_imaging_frame = SPHNMagneticResonanceImagingFrame(
                sphn_schema = data_store.sphn_schema,
                has_start_datetime = None,
                has_end_datetime = None,
                has_type_list = data_store.sphn_imagingframe_type_valueset_member_list,
                has_image_dimensions = data_store.sphn_image_dimensions,
                has_body_site_list = data_store.sphn_body_site_list_frame,
                has_algorithm_list = data_store.sphn_data_compression_algorithm_list,
                has_content_qualification = data_store.sphn_imagingframe_content_qualification_valueset_member,
                has_imaging_metric = None,
                has_anatomical_projection = None,
                has_contrast_agent_administration_event = data_store.sphn_contrast_agent_administration_event_list[0] \
                    if data_store.sphn_contrast_agent_administration_event_list is not None \
                        and len(data_store.sphn_contrast_agent_administration_event_list) > 0 else None
            )
        elif sop_class_uid in [
            pydicom.uid.PositronEmissionTomographyImageStorage,
            pydicom.uid.LegacyConvertedEnhancedPETImageStorage,
            pydicom.uid.EnhancedPETImageStorage
            ]:
            # Create a specific SPHN PositronEmissionTomographyImagingFrame
            logger.debug(" "*(indent+4) + "Creating an SPHN PET-ImagingFrame")
            sphn_imaging_frame = SPHNPositronEmissionTomographyImagingFrame(
                sphn_schema = data_store.sphn_schema,
                has_start_datetime = None,
                has_end_datetime = None,
                has_type_list = data_store.sphn_imagingframe_type_valueset_member_list,
                has_image_dimensions = data_store.sphn_image_dimensions,
                has_body_site_list = data_store.sphn_body_site_list_frame,
                has_algorithm_list = data_store.sphn_data_compression_algorithm_list,
                has_content_qualification = data_store.sphn_imagingframe_content_qualification_valueset_member,
                has_imaging_metric = None,
                has_anatomical_projection = None,
                has_radiopharmaceutical_administration_event = data_store.sphn_radiopharmaceutical_administration_event_list[0] \
                    if data_store.sphn_radiopharmaceutical_administration_event_list is not None \
                        and len(data_store.sphn_radiopharmaceutical_administration_event_list) > 0 else None
            )
        elif sop_class_uid in [
            pydicom.uid.ComputedRadiographyImageStorage,
            pydicom.uid.DigitalXRayImageStorageForPresentation,
            pydicom.uid.DigitalXRayImageStorageForProcessing,
            pydicom.uid.DigitalMammographyXRayImageStorageForPresentation,
            pydicom.uid.DigitalMammographyXRayImageStorageForProcessing,
            pydicom.uid.DigitalIntraOralXRayImageStorageForPresentation,
            pydicom.uid.DigitalIntraOralXRayImageStorageForProcessing,
            pydicom.uid.XRayAngiographicImageStorage,
            pydicom.uid.EnhancedXAImageStorage,
            pydicom.uid.XRayRadiofluoroscopicImageStorage,
            pydicom.uid.EnhancedXRFImageStorage,
            pydicom.uid.XRay3DAngiographicImageStorage,
            pydicom.uid.XRay3DCraniofacialImageStorage,
            pydicom.uid.BreastTomosynthesisImageStorage,
            pydicom.uid.BreastProjectionXRayImageStorageForPresentation,
            pydicom.uid.BreastProjectionXRayImageStorageForProcessing,
            ]:
            # Create a specific SPHN XRayImagingFrame
            logger.debug(" "*(indent+4) + "Creating an SPHN XRay-ImagingFrame")
            sphn_imaging_frame = SPHNXRayImagingFrame(
                sphn_schema = data_store.sphn_schema,
                has_start_datetime = None,
                has_end_datetime = None,
                has_type_list = data_store.sphn_imagingframe_type_valueset_member_list,
                has_image_dimensions = data_store.sphn_image_dimensions,
                has_body_site_list = data_store.sphn_body_site_list_frame,
                has_algorithm_list = data_store.sphn_data_compression_algorithm_list,
                has_content_qualification = data_store.sphn_imagingframe_content_qualification_valueset_member,
                has_imaging_metric = None,
                has_anatomical_projection = None,
                has_contrast_agent_administration_event = data_store.sphn_contrast_agent_administration_event_list[0] \
                    if data_store.sphn_contrast_agent_administration_event_list is not None \
                        and len(data_store.sphn_contrast_agent_administration_event_list) > 0 else None
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
                has_body_site_list = data_store.sphn_body_site_list_frame,
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

        stop_time_t1 = time.perf_counter()
        logger.debug(" "*(indent+0) + "FrameProcessor: Done processing..." +
                    f" in '{stop_time_t1 - start_time_t1:.2f}' seconds" +
                    f" ({timedelta(seconds=(stop_time_t1 - start_time_t1))!s})"
        )
        logger.debug("")

        # Statistics
        data_store.increment_dicom_frames_processed_counter()

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions - related to processing the DICOM Instance dataset and collecting the metadata related to the SPHN ImagingFrame and its related SPHN concepts
    # -----------------------------------------------------------------------------------------------------------------
