"""
dw_instance_processor.py:
    Part of the example dicom2sphn package.
    It processes the DICOM(web) Instance level data.
"""
from datetime import timedelta
from time import time

import pydicom
from pydicom import Dataset
from pydicom.uid import UID
from pynetdicom import sop_class

from .context import Context
from .dicom_imaging_device_reader import get_imaging_device_metadata_from_dicom
from .dicom_series_reader import get_series_metadata_from_dicom
from .dicom_study_reader import get_study_metadata_from_dicom
from .dw_frame_processor import DWFrameProcessor
from .sphn_concepts.sphn_code import SPHNCode
from .sphn_concepts.sphn_computed_tomography_imaging_series import (
    SPHNComputedTomographyImagingSeries,
)
from .sphn_concepts.sphn_imaging_device import SPHNImagingDevice
from .sphn_concepts.sphn_imaging_procedure import SPHNImagingProcedure
from .sphn_concepts.sphn_imaging_series import SPHNImagingSeries
from .sphn_concepts.sphn_magnetic_resonance_imaging_series import (
    SPHNMagneticResonanceImagingSeries,
)
from .sphn_concepts.sphn_positron_emission_tomography_imaging_series import (
    SPHNPositronEmissionTomographyImagingSeries,
)
from .sphn_concepts.sphn_subject_pseudo_identifier import SPHNSubjectPseudoIdentifier
from .sphn_concepts.sphn_xray_imaging_series import SPHNXRayImagingSeries
from .tools import already_in_list, is_valid_string


class DWInstanceProcessor:

    def __init__(self):
        """ 
        Initializes the instance
        """

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    def process(self, instance_search_response_item_ds: Dataset, current_instance_number: int, context: Context, indent: int=0) -> None:
        """
        Processes the Instance level data by traversing the DICOM Patient - Study - Series - Instance hierarchical tree using 
        the DICOMweb API and collecting the metadata related to the SPHN ImagingFrame and its related SPHN concepts.
        """

        # Checks
        assert isinstance(instance_search_response_item_ds, Dataset)
        assert isinstance(current_instance_number, int) and current_instance_number > 0
        assert isinstance(context, Context)
        assert isinstance(indent,int) and indent>=0

        # Get the logger, data_store, and dw_client from the context
        logger = context.logger
        data_store = context.data_store
        dw_client = context.dw_client

        logger.debug(" "*(indent+0) + "InstanceProcessor: Start processing...")
        start_time_t1 = time()

        # Update the DataStore
        data_store.current_instance_number = current_instance_number

        # -------------------------------------------------------------------------------------------------------------
        # Start collecting metadata from the response
        # -------------------------------------------------------------------------------------------------------------

        logger.debug(" "*(indent+2) + "Start collecting DICOM metadata from instance_search_response")

        #
        # SOPInstanceUID
        #

        # Get the SOPInstanceUID
        sop_instance_uid = self.get_sop_instance_uid_from_dicomweb_response(instance_search_response_item_ds, context, indent=indent+4)

        if sop_instance_uid is not None:
            data_store.sop_instance_uid = sop_instance_uid
            logger.debug(" "*(indent+4) + f"SOPInstanceUID: '{data_store.sop_instance_uid}'")
        else:
            logger.debug(" "*(indent+4) + "SOPInstanceUID not defined")
            data_store.increment_dicom_instances_skipped_counter()
            return

        #
        # SOPClassUID
        #

        # Get the SOPClassUID
        sop_class_uid = self.get_sop_class_uid_from_dicomweb_response(instance_search_response_item_ds, context, indent=indent+4)

        if sop_class_uid is not None:
            sop_class_uid_name = UID(sop_class_uid).name
        else:
            sop_class_uid_name = None
            
        if sop_class_uid is not None and sop_class_uid_name is not None:
            data_store.sop_class_uid = sop_class_uid
            data_store.sop_class_uid_name = sop_class_uid_name
            logger.debug(" "*(indent+4) + f"SOPClassUID: '{data_store.sop_class_uid}' having name: '{data_store.sop_class_uid_name}'")
        else:
            logger.debug(" "*(indent+4) + "SOPClassUID not defined")
            data_store.increment_dicom_instances_skipped_counter()
            return

        # 
        # NumberOfFrames
        #

        # Note: DICOM NumberOfFrames tag is only available in Multi-Frame DICOM, not in legacy Single-Frame DICOM

        # Get number of frames
        number_of_frames = self.get_number_of_frames_from_dicomweb_response(instance_search_response_item_ds, context, indent=indent+4)

        if number_of_frames is not None:
            data_store.number_of_frames_in_instance = number_of_frames
            logger.debug(" "*(indent+4) + f"NumberOfFrames: '{data_store.number_of_frames_in_instance}'")
        else:
            logger.debug(" "*(indent+4) + "NumberOfFrames not defined")

        # 
        # Done
        #
        logger.debug(" "*(indent+2) + "Done  collecting DICOM metadata from instance_search_response")

        # -------------------------------------------------------------------------------------------------------------
        # Done  collecting metadata from the response
        # -------------------------------------------------------------------------------------------------------------

        # Check
        assert is_valid_string(data_store.sop_instance_uid)
        assert is_valid_string(data_store.sop_class_uid)
        assert is_valid_string(data_store.sop_class_uid_name)

        # -------------------------------------------------------------------------------------------------------------
        # Check if the SOPClassUID is supported in this example
        # -------------------------------------------------------------------------------------------------------------

        if sop_class_uid not in data_store.valid_sop_classes:
            logger.warning(" "*(indent+2) + "This instance is not (yet) supported," +
                           f" according to its DICOM 'SOPClassUID' tag value: '{sop_class_uid}'," +
                           f" and name: '{sop_class_uid_name}'" +
                           f" in sop instance number : '{current_instance_number}'" +
                           f" in series number : '{data_store.current_series_number}'" +
                           f" in study number : '{data_store.current_study_number}'"
            )
            # Add unsupported SOPClassUID to dictionary for statistics
            data_store.add_skipped_sop_class_uid_to_dict(sop_class_uid, sop_class_uid_name)
            data_store.increment_dicom_instances_skipped_counter()
            return

        # -------------------------------------------------------------------------------------------------------------
        # Get the entire DICOM header (metadata) belonging to the DICOM SOP Instance 
        # from the DICOMweb server (WADO-RS RetrieveMetadata)
        # -------------------------------------------------------------------------------------------------------------

        logger.debug(" "*(indent+2) + "Start querying DICOMweb server for the metadata of this DICOM Instance" + 
                     " related to the DICOM Series and DICOM Study"
        )
        start_time_t99 = time()

        # Run Query
        # Get all SOP Instance metadata (Entire DICOM Header)
        instance_metadata_json = dw_client.retrieve_instance_metadata(
            study_instance_uid=data_store.study_instance_uid,
            series_instance_uid=data_store.series_instance_uid,
            sop_instance_uid=data_store.sop_instance_uid
        )
        
        stop_time_t99 = time()
        logger.debug(" "*(indent+2) + "Done  querying DICOMweb server for the metadata of this DICOM Instance" + 
                     " related to the DICOM Series and DICOM Study" +
                     " in: " + str(timedelta(seconds=(stop_time_t99 - start_time_t99)))
        )

        # Check if there is any metadata defined (There should always be metadata)
        if len(instance_metadata_json) == 0:
            logger.warning(" "*(indent+2) + "No DICOM header (metadata) defined" +
                           f" in sop instance number : '{data_store.sop_instance_number}'" +
                           f" in series number : '{data_store.series_instance_number}'" +
                           f" in study number : '{data_store.study_instance_number}'"
            )
            data_store.increment_dicom_instances_skipped_counter()
            return

        # Converting JSON to DICOM Dataset
        instance_ds = Dataset.from_json(instance_metadata_json)
        
        # Store the data in the data_store
        data_store.instance_ds = instance_ds

        # -------------------------------------------------------------------------------------------------------------
        # Creating the SPHN SubjectPseudoIdentifier (if it does not exist yet)
        # -------------------------------------------------------------------------------------------------------------

        if data_store.sphn_subject_pseudo_identifier is None:

            logger.debug(" "*(indent+2) + "Start creating the SPHN SubjectPseudoIdentifier")

            assert data_store.patient_id is not None
            assert data_store.sphn_data_provider is not None
            assert data_store.sphn_schema is not None

            # Create a new SPHN SubjectPseudoIdentifier and add it to the data_store
            sphn_subject_pseudo_identifier=SPHNSubjectPseudoIdentifier(
                has_identifier = data_store.patient_id,
                has_data_provider = data_store.sphn_data_provider,
                sphn_schema = data_store.sphn_schema
            )
            data_store.sphn_subject_pseudo_identifier = sphn_subject_pseudo_identifier

            logger.debug(" "*(indent+2) + "Done  creating the SPHN SubjectPseudoIdentifier")
        else:
            logger.debug(" "*(indent+2) + "SPHN SubjectPseudoIdentifier already exists, not creating it again")

        # -------------------------------------------------------------------------------------------------------------
        # Creating the SPHN ImagingProcedure (if it does not exist yet)
        # -------------------------------------------------------------------------------------------------------------

        if data_store.sphn_imaging_procedure is None:

            logger.debug(" "*(indent+2) + "Start creating the SPHN ImagingProcedure")

            assert data_store.sphn_source_system is not None
            assert data_store.sphn_subject_pseudo_identifier is not None
            assert data_store.sphn_schema is not None

            # The SPHN ImagingProcedure requires a has_code that indicates the imaging procedure. 
            # In DICOM there is a Procedure Code Sequence Attribute (0008,1032), but the Procedure Codes are not always provided. 
            # However, the modalities found by the dw_study_processor in the DICOMweb API "Study Resource Search Response Payload" 
            # can possibly be used to determine a procedure code. They are stored in the data_store in modality_based_imaging_procedure_code_dict

            if data_store.modality_based_imaging_procedure_codes_dict is not None:

                assert isinstance(data_store.modality_based_imaging_procedure_codes_dict, dict) and len(data_store.modality_based_imaging_procedure_codes_dict) > 0

                sphn_code_list = []
                for imaging_procedure_snomed_ct_code, imaging_procedure_snomed_ct_description in data_store.modality_based_imaging_procedure_codes_dict.items():

                    assert is_valid_string(imaging_procedure_snomed_ct_code)
                    assert imaging_procedure_snomed_ct_description == "" or is_valid_string(imaging_procedure_snomed_ct_description)

                    # Create an instance of SPHN Code
                    sphn_code = SPHNCode(
                        sphn_schema = data_store.sphn_schema,
                        has_coding_system_and_version = "SNOMED",
                        has_identifier = imaging_procedure_snomed_ct_code,
                        has_name = imaging_procedure_snomed_ct_description
                    )
                    sphn_code_list.append(sphn_code)


                sphn_imaging_procedure = SPHNImagingProcedure(
                    sphn_schema = data_store.sphn_schema,
                    has_code_list= sphn_code_list,
                    has_subject_pseudo_identifier = data_store.sphn_subject_pseudo_identifier,
                    has_source_system_list = [data_store.sphn_source_system]
                )
                data_store.sphn_imaging_procedure = sphn_imaging_procedure

                # ToDo: Edwin - 2026-07-24
                # Get other SPHN ImagingProcedure metadata from the entire DICOM SOP Instance Header
                #sphn_imaging_procedure.get_metadata_from_dicom(metadata_ds, indent=indent+4)

            else:
                logger.warning(" "*(indent+2) + "SPHN ImagingProcedure not created, because no modality-based imaging procedure codes are defined")
                data_store.increment_dicom_instances_skipped_counter()
                return

            logger.debug(" "*(indent+2) + "Done  creating the SPHN ImagingProcedure")

        else:
            logger.debug(" "*(indent+2) + "SPHN ImagingProcedure already exists, not creating it again")

        # -------------------------------------------------------------------------------------------------------------
        # Creating the SPHN ImagingSeries (if it does not exist yet)
        # -------------------------------------------------------------------------------------------------------------
        
        if data_store.sphn_imaging_series is None:

            logger.debug(" "*(indent+2) + "Start creating the SPHN ImagingSeries")

            assert data_store.sphn_source_system is not None
            assert data_store.sphn_subject_pseudo_identifier is not None
            assert data_store.sphn_schema is not None
            assert data_store.modality_dcm_code is not None
            assert data_store.modality_dcm_description is not None
            assert sop_class_uid is not None

            # Create an instance of SPHN Code for the imaging modality
            imaging_modality_code = SPHNCode(
                sphn_schema = data_store.sphn_schema,
                has_coding_system_and_version = "DCM",
                has_identifier = data_store.modality_dcm_code,
                has_name = data_store.modality_dcm_description
            )

            # Selecting the general or one of the specific SPHN ImagingSeries
            if sop_class_uid in [sop_class.CTImageStorage]:
                # Create a specific SPHN ComputedTomographyImagingSeries
                logger.debug(" "*(indent+4) + "Creating an SPHN CT-ImagingSeries")
                sphn_imaging_series = SPHNComputedTomographyImagingSeries(
                    sphn_schema = data_store.sphn_schema,
                    has_subject_pseudo_identifier = data_store.sphn_subject_pseudo_identifier,
                    has_source_system_list = [data_store.sphn_source_system],
                    has_imaging_modality_code = imaging_modality_code
                )
            elif sop_class_uid in [sop_class.MRImageStorage]:
                # Create a specific SPHN MagneticResonanceImagingSeries
                logger.debug(" "*(indent+4) + "Creating an SPHN MR-ImagingSeries")
                sphn_imaging_series = SPHNMagneticResonanceImagingSeries(
                    sphn_schema = data_store.sphn_schema,
                    has_subject_pseudo_identifier = data_store.sphn_subject_pseudo_identifier,
                    has_source_system_list = [data_store.sphn_source_system],
                    has_imaging_modality_code = imaging_modality_code
                )
            elif sop_class_uid in [sop_class.PositronEmissionTomographyImageStorage]:
                # Create a specific SPHN PositronEmissionTomographyImagingSeries
                logger.debug(" "*(indent+4) + "Creating an SPHN PET-ImagingSeries")
                sphn_imaging_series = SPHNPositronEmissionTomographyImagingSeries(
                    sphn_schema = data_store.sphn_schema,
                    has_subject_pseudo_identifier = data_store.sphn_subject_pseudo_identifier,
                    has_source_system_list = [data_store.sphn_source_system],
                    has_imaging_modality_code = imaging_modality_code
                )
            elif sop_class_uid in ['empty_for_now']:
                # Create a specific SPHN XRayImagingSeries
                logger.debug(" "*(indent+4) + "Creating an SPHN XRay-ImagingSeries")
                sphn_imaging_series = SPHNXRayImagingSeries(
                    sphn_schema = data_store.sphn_schema,
                    has_subject_pseudo_identifier = data_store.sphn_subject_pseudo_identifier,
                    has_source_system_list = [data_store.sphn_source_system],
                    has_imaging_modality_code = imaging_modality_code
                )
            else:
                # Create a general SPHN ImagingSeries
                logger.debug(" "*(indent+4) + "Creating a general SPHN ImagingSeries")
                sphn_imaging_series = SPHNImagingSeries(
                    sphn_schema = data_store.sphn_schema,
                    has_subject_pseudo_identifier = data_store.sphn_subject_pseudo_identifier,
                    has_source_system_list = [data_store.sphn_source_system],
                    has_imaging_modality_code = imaging_modality_code
                )

            # Add the SPHN ImagingSeries to the DataStore
            data_store.sphn_imaging_series = sphn_imaging_series

            # ToDo: Edwin - 2026-07-24
            # Get other SPHN ImagingSeries metadata from the entire DICOM SOP Instance Header
            #sphn_imaging_series.get_metadata_from_dicom(metadata_ds, indent=indent+4)

            logger.debug(" "*(indent+2) + "Done  creating the SPHN ImagingSeries")

        else:
            logger.debug(" "*(indent+2) + "SPHN ImagingSeries already exists, not creating it again")

        # -------------------------------------------------------------------------------------------------------------
        # Creating the SPHN ImagingDevice
        # -------------------------------------------------------------------------------------------------------------

        if data_store.sphn_imaging_device is None:

            logger.debug(" "*(indent+2) + "Start creating the SPHN ImagingDevice")

            # Collect the SPHN ImagingDevice metadata from the entire DICOM SOP Instance Header
            get_imaging_device_metadata_from_dicom(instance_ds, context, indent=indent+4)

            # Check if there is any SPHN ImagingDevice metadata defined
            if data_store.manufacturer_name is not None \
                or data_store.manufacturer_model_name is not None \
                or data_store.device_serial_number is not None \
                or (data_store.software_list is not None \
                    and len(data_store.software_list) > 0):

                # Create the SPHN ImagingDevice
                sphn_imaging_device = SPHNImagingDevice(
                    sphn_schema = data_store.sphn_schema,
                    has_manufacturer_name = data_store.manufacturer_name,
                    has_model_name = data_store.manufacturer_model_name,
                    has_serial_number = data_store.device_serial_number,
                    has_software_list = data_store.software_list,
                )

                # Add the SPHN ImagingDevice to the DataStore
                data_store.sphn_imaging_device = sphn_imaging_device

                logger.debug(" "*(indent+2) + "Done  creating the SPHN ImagingDevice")

            else:
                logger.debug(" "*(indent+2) + "SPHN ImagingDevice not created, because no SPHN ImagingDevice metadata is defined")

        else:
            logger.debug(" "*(indent+2) + "SPHN ImagingDevice already exists, not creating it again")

        # -------------------------------------------------------------------------------------------------------------
        # Getting number of frames again, but now from the entire DICOM Instance metadata
        # -------------------------------------------------------------------------------------------------------------

        # 
        # NumberOfFrames
        #

        # Note: DICOM NumberOfFrames tag is only available in Multi-Frame DICOM, not in legacy Single-Frame DICOM

        # Only if it was not obtained before from the DICOMweb response
        if number_of_frames is None:
            # Get number of frames from instance Dataset.
            # Using the same function as used for the DICOMweb response
            number_of_frames = self.get_number_of_frames_from_dicomweb_response(instance_ds, context, indent=indent+2)

            if number_of_frames is not None:
                # Set the property
                data_store.number_of_frames_in_instance = number_of_frames

                logger.debug(" "*(indent+2) + f"NumberOfFrames: '{number_of_frames}'")

            else:
                logger.debug(" "*(indent+2) + "NumberOfFrames not defined")

        # In case DICOM NumberOfFrames was not defined, assume legacy Single-Frame DICOM
        if number_of_frames is None:

            assert data_store.number_of_frames_in_instance == 0

            data_store.number_of_frames_in_instance = 1

            # Log
            logger.debug(" "*(indent+2) + "Note: Assuming legacy, Single-Frame DICOM SOP Instances")
            logger.debug(" "*(indent+2) + f"NumberOfFrames: '{data_store.number_of_frames_in_instance}'")

        assert data_store.number_of_frames_in_instance > 0

        # -------------------------------------------------------------------------------------------------------------
        # Start collecting metadata from the entire DICOM Instance dataset for the current ImagingStudy and ImagingSeries
        # -------------------------------------------------------------------------------------------------------------

        logger.debug(" "*(indent+2) + "Start collecting more DICOM metadata from instance_ds for the current ImagingStudy and ImagingSeries")

        # Get SPHN ImagingStudy metadata from the entire DICOM SOP Instance Header
        get_study_metadata_from_dicom(instance_ds, context, indent=indent+4)

        # Get SPHN ImagingSeries metadata from the entire DICOM SOP Instance Header
        get_series_metadata_from_dicom(instance_ds, context, indent=indent+4)

        logger.debug(" "*(indent+2) + "Done  collecting more DICOM metadata from instance_ds for the current ImagingStudy and ImagingSeries")

        # -------------------------------------------------------------------------------------------------------------
        # Done  collecting metadata from the entire DICOM Instance dataset for the current ImagingStudy and ImagingSeries
        # -------------------------------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------------------------------
        # For every DICOM Frame
        # -------------------------------------------------------------------------------------------------------------

        for current_frame_number, current_frame_index in enumerate(range(data_store.number_of_frames_in_instance), start=1):

            logger.debug(" "*(indent+2) + f"Start processing DICOM Frame number: '{current_frame_number}'" +
                        f" of '{data_store.number_of_frames_in_instance}'"
                        f" in instance number : '{data_store.current_instance_number}'" +
                        f" in series number : '{data_store.current_series_number}'" +
                        f" in study number : '{data_store.current_study_number}'" +
                        f" for patient with PatientID: '{data_store.patient_id}'"
            )
            start_time_t2 = time()

            # Reset any previous DICOM Frame level information in the data_store
            data_store.reset_imaging_frame_level()

            # Create an InstanceProcessor instance to process the DICOM Instance
            dw_frame_processor = DWFrameProcessor()

            # Start processing the next level
            dw_frame_processor.process(instance_ds, current_frame_number, context, indent=indent+4)

            # ---------------------------------------------------------------------------------------------------------
            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            # Add the SPHN ImagingFrame to the data_store
            # ---------------------------------------------------------------------------------------------------------

            # Add the SPHN ImagingFrame to the SPHN ImagingSeries in the data_store
            if data_store.sphn_imaging_frame is not None:

                # toDo: Edwin - 2025-07-27 - Check if the SPHN ImagingFrame is having any data

                assert data_store.sphn_imaging_series is not None

                if data_store.sphn_imaging_series.has_imaging_frame_list is None:
                    data_store.sphn_imaging_series.has_imaging_frame_list = [data_store.sphn_imaging_frame]
                    logger.debug(" "*(indent+2) + "Added the SPHN ImagingFrame to the SPHN ImagingSeries in the data_store")
                    data_store.increment_sphn_imaging_frames_added_to_sphn_imaging_series_counter()
                else:
                    assert isinstance(data_store.sphn_imaging_series.has_imaging_frame_list, list)

                    # Add if not similar to a previous SPHN ImagingFrame in the list (to avoid duplicates)
                    if context.ALWAYS_ADD_SPHN_IMAGING_FRAME \
                        or not already_in_list(data_store.sphn_imaging_frame, data_store.sphn_imaging_series.has_imaging_frame_list):
                        data_store.sphn_imaging_series.has_imaging_frame_list.append(data_store.sphn_imaging_frame)
                        logger.debug(" "*(indent+2) + "Added the SPHN ImagingFrame to the SPHN ImagingSeries in the data_store")
                        data_store.increment_sphn_imaging_frames_added_to_sphn_imaging_series_counter()
                    else:
                        logger.debug(" "*(indent+2) + "SPHN ImagingFrame not added to the SPHN ImagingSeries" + 
                                    " in the data_store as a similar SPHN ImagingFrame already existed." +
                                    f" Frame number: '{current_frame_number}' of '{data_store.number_of_frames_in_instance}'" +
                                    f" in instance number : '{data_store.current_instance_number}'" +
                                    f" in series number : '{data_store.current_series_number}'" +
                                    f" in study number : '{data_store.current_study_number}'"
                        )

            else:
                logger.debug(" "*(indent+2) + "SPHN ImagingFrame not added to the SPHN ImagingSeries" + 
                            " in the data_store as the SPHN ImagingFrame was not created." +
                            f" Frame number: '{current_frame_number}' of '{data_store.number_of_frames_in_instance}'" +
                            f" in instance number : '{data_store.current_instance_number}'" +
                            f" in series number : '{data_store.current_series_number}'" +
                            f" in study number : '{data_store.current_study_number}'"
                )

            # ---------------------------------------------------------------------------------------------------------

            # Reset any previous DICOM Frame level information in the data_store
            data_store.reset_imaging_frame_level()

            stop_time_t2 = time()
            logger.debug(" "*(indent+2) + f"Done  processing DICOM frame number: '{current_frame_number}'" + 
                        f" of '{data_store.number_of_frames_in_instance}'" +
                        f" in instance number : '{data_store.current_instance_number}'" +
                        f" in series number : '{data_store.current_series_number}'" +
                        f" in study number : '{data_store.current_study_number}'" +
                        f" for patient with PatientID: '{data_store.patient_id}'"
                         " in: " + str(timedelta(seconds=(stop_time_t2 - start_time_t2)))
            )

        # -------------------------------------------------------------------------------------------------------------
        # Done processing all DICOM Frames in this DICOM Instance
        logger.debug("")
        stop_time_t1 = time()
        logger.debug(" "*(indent+0) + "InstanceProcessor: Done processing..." +
                    " in: " + str(timedelta(seconds=(stop_time_t1 - start_time_t1)))
        )

        # Statistics
        data_store.increment_dicom_instances_processed_counter()
        logger.debug("")
        logger.debug(" "*(indent+0) + f"Processed {data_store.number_of_dicom_frames_processed} DICOM Frame(s) in this DICOM Instance")
        logger.debug(" "*(indent+0) + f"Added {data_store.number_of_sphn_imaging_frames_added_to_sphn_imaging_series} SPHN ImagingFrame(s) to the SPHN ImagingSeries in the data_store.")
        logger.debug(" "*(indent+0) + f"A total of: {len(data_store.sphn_imaging_series.has_imaging_frame_list)} SPHN ImagingFrame(s) in the SPHN ImagingSeries in the data_store.")
        logger.debug("")

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions - related to processing the DICOMweb API "Instance Resource Search Response Payload"
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin - 2026-07-24
    #
    def get_sop_instance_uid_from_dicomweb_response(self, dataset: Dataset, context: Context, indent: int=0) -> str|None:
        """
        Returns the value corresponding to the value of the DICOM SOPInstanceUID tag
          - dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)

        Note: The DICOM SOPInstanceUID tag is part of the DICOMweb API "Instance Resource Search 
              Response Payload". It's type is '[U]nique and Required'
              For more info see: 
              https://dicom.nema.org/medical/dicom/current/output/html/part18.html#table_10.6.3-5
        """

        # Keyword:              SOPInstanceUID
        # Value Representation: Unique Identifier (UI)
        # Type:	                Required (1)
        # Value Multiplicity:   1

        # Check
        assert isinstance(dataset, Dataset)
        assert isinstance(context, Context)
        assert isinstance(indent,int) and indent>=0

        logger = context.logger

        if "SOPInstanceUID" not in dataset:
            logger.warning(" "*(indent+0) + "DICOM SOPInstanceUID tag was not found")
            return None

        # Get the DataElement
        data_element = dataset["SOPInstanceUID"]

        # Get the value
        value = data_element.value
            
        # Get the Value Multiplicity
        value_multiplicity = data_element.VM
            
        # Check if it is empty
        if value_multiplicity == 0 or value is None:
            logger.warning(" "*(indent+0) + "DICOM SOPInstanceUID tag value was not provided")
            return None

        # It should be a single-valued tag, a string            
        if value_multiplicity != 1 or not isinstance(value, str):
            logger.warning(" "*(indent+0) + "DICOM SOPInstanceUID tag has an unknown format")
            return None
            
        # Remove whitespace
        sop_instance_uid_str = value.strip()

        # Check if value is not empty
        if len(sop_instance_uid_str) == 0:
            logger.warning(" "*(indent+0) + "DICOM SOPInstanceUID tag value contains only whitespace")
            return None

        return sop_instance_uid_str

    #
    # Edwin - 2026-07-24
    #
    def get_sop_class_uid_from_dicomweb_response(self, dataset: Dataset, context: Context, indent: int=0) -> str|None:
        """
        Returns the value corresponding to the value of the DICOM SOPClassUID tag
          - dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)

        Note: The DICOM SOPClassUID tag is part of the DICOMweb API "Instance Resource Search 
              Response Payload". It's type is '[R]equired'
              For more info see: 
              https://dicom.nema.org/medical/dicom/current/output/html/part18.html#table_10.6.3-5
        """

        # Keyword:              SOPClassUID
        # Value Representation: Unique Identifier (UI)
        # Type:	                Required (1)
        # Value Multiplicity:   1

        # Check
        assert isinstance(dataset, Dataset)
        assert isinstance(context, Context)
        assert isinstance(indent,int) and indent>=0

        logger = context.logger

        if "SOPClassUID" not in dataset:
            logger.warning(" "*(indent+0) + "DICOM SOPClassUID tag was not found")
            return None

        # Get the DataElement
        data_element = dataset["SOPClassUID"]

        # Get the value
        value = data_element.value
            
        # Get the Value Multiplicity
        value_multiplicity = data_element.VM
            
        # Check if it is empty
        if value_multiplicity == 0 or value is None:
            logger.warning(" "*(indent+0) + "DICOM SOPClassUID tag value was not provided")
            return None

        # It should be a single-valued tag, a string            
        if value_multiplicity != 1 or not isinstance(value, str):
            logger.warning(" "*(indent+0) + "DICOM SOPClassUID tag has an unknown format")
            return None
            
        # Remove whitespace
        sop_class_uid_str = value.strip()

        # Check if value is not empty
        if len(sop_class_uid_str) == 0:
            logger.warning(" "*(indent+0) + "DICOM SOPClassUID tag value contains only whitespace")
            return None

        return sop_class_uid_str
    
    # 
    # Edwin - 2026-07-24
    #
    def get_number_of_frames_from_dicomweb_response(self, dataset: Dataset, context: Context, indent: int=0) -> int|None:
        """
        Returns the value corresponding to the value of the DICOM NumberOfFrames tag
          - dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)

        Note: The DICOM NumberOfFrames tag is part of the DICOMweb API "Instance Resource Search 
              Response Payload". It's type is '[C]onditional' "Shall be present if known"
              For more info see: 
              https://dicom.nema.org/medical/dicom/current/output/html/part18.html#table_10.6.3-5
        """

        # Keyword:              NumberOfFrames
        # Value Representation: Integer String (IS)
        # Type:	                Required (1)
        # Value Multiplicity:   1

        # Note: DICOM NumberOfFrames tag is only available in Multi-Frame DICOM, not in legacy Single-Frame DICOM

        # Check
        assert isinstance(dataset, Dataset)
        assert isinstance(context, Context)
        assert isinstance(indent,int) and indent>=0

        logger = context.logger

        if "NumberOfFrames" not in dataset:
            logger.debug(" "*(indent+0) + "DICOM NumberOfFrames tag was not found")  
            return None

        # Get the DataElement
        data_element = dataset["NumberOfFrames"]

        # Get the value
        value = data_element.value
        
        # Get the Value Multiplicity
        value_multiplicity = data_element.VM
        
        # Check if it is empty
        if value_multiplicity == 0 or value is None:
            logger.warning(" "*(indent+0) + "DICOM NumberOfFrames tag value was not provided")
            return None
        
        # It should be a single-valued tag, an integer
        if value_multiplicity != 1 or not isinstance(value, pydicom.valuerep.IS):
            logger.warning(" "*(indent+0) + "DICOM NumberOfFrames tag has an unknown format")
            return None
        
        # Try to convert IS to int
        try:
            number_of_frames = int(value)
        except (TypeError, ValueError):
            logger.warning(" "*(indent+0) + "DICOM NumberOfFrames value could not be converted to an int value.")
            return None

        if number_of_frames <= 0:
            logger.warning(" "*(indent+0) + f"DICOM NumberOfFrames: '{number_of_frames}' is not a valid value.")
            return None

        return number_of_frames

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions - other
    # -----------------------------------------------------------------------------------------------------------------





