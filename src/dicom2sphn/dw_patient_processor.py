"""
dw_patient_processor.py:
    Part of the example dicom2sphn package.
    It processes the DICOM(web) Patient level data.
"""

from datetime import timedelta
from time import time

from pydicom import Dataset

from .context import Context
from .dw_study_processor import DWStudyProcessor
from .tools import already_in_list, is_valid_string


class DWPatientProcessor:

    def __init__(self):
        """ 
        Initializes the instance
        """

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    def process(self, patient_id: str, context: Context, indent: int=0) -> None:
        """
        Processes the Patient level data by traversing the DICOM Patient - Study - Series - Instance hierarchical tree using 
        the DICOMweb API and collecting the metadata related to the SPHN ImagingProcedure and its related SPHN concepts.
        """

        # Checks
        assert is_valid_string(patient_id)
        assert isinstance(context, Context)
        assert isinstance(indent,int) and indent>=0

        # Get the logger, data_store, and dw_client from the context
        logger = context.logger
        data_store = context.data_store
        dw_client = context.dw_client

        logger.debug(" "*(indent+0) + "PatientProcessor: Start processing...")
        start_time_t1 = time()

        # Update the DataStore
        data_store.patient_id = patient_id

        # -------------------------------------------------------------------------------------------------------------
        # Start collecting metadata
        # -------------------------------------------------------------------------------------------------------------
        

        # -------------------------------------------------------------------------------------------------------------
        # Done  collecting metadata
        # -------------------------------------------------------------------------------------------------------------

        # ---------------------------------------------------------------------------------------------------------
        # Find all DICOM Studies with patientID on the DICOM server using DICOMweb API
        # ---------------------------------------------------------------------------------------------------------

        logger.debug(" "*(indent+2) + "Start querying DICOMweb server for DICOM Studies" +
                    f" with DICOM PatientID: '{data_store.patient_id}'"
        )
        start_time_t99 = time()

        # Run Query
        # The study_search_response_json is the DICOMweb API "Study Resource Search Response Payload" 
        #  - For more info see: https://dicom.nema.org/medical/dicom/current/output/html/part18.html#table_10.6.3-3
        # The parameters "offset" and "limit" seems to be not implemented, hence get_remaining is set to False
        study_search_response_json = dw_client.search_for_studies(
            search_filters={'PatientID': data_store.patient_id}, 
            get_remaining=False
        ) 

        stop_time_t99 = time()
        logger.debug(" "*(indent+2) + "Done  querying DICOMweb server for DICOM Studies" + 
                    f" with DICOM PatientID: '{data_store.patient_id}'" +
                    " in: " + str(timedelta(seconds=(stop_time_t99 - start_time_t99)))
        )

        # Get number of studies in current patient dataset
        number_of_studies_in_current_patient_dataset = len(study_search_response_json)

        # Check if there is any DICOM Study defined
        if number_of_studies_in_current_patient_dataset == 0:
            logger.warning(" "*(indent+2) + "No DICOM Studies found" +
                        f" for patient with PatientID: '{data_store.patient_id}'"
            )
            # Nothing to do, return
            return

        # -------------------------------------------------------------------------------------------------------------
        # For every DICOM Study
        # -------------------------------------------------------------------------------------------------------------

        for current_study_number, study_search_response_item_json in enumerate(study_search_response_json, start=1):

            logger.info(" "*(indent+2) + f"Start processing DICOM Study number: '{current_study_number}'" + 
                        f" of '{number_of_studies_in_current_patient_dataset}'" +
                        f" for patient with PatientID: '{data_store.patient_id}'"
            )
            start_time_t2 = time()

            # Reset any previous DICOM Study level information in the data_store
            data_store.reset_imaging_study_level()

            # Converting JSON to DICOM Dataset
            study_search_response_item_ds = Dataset.from_json(study_search_response_item_json)

            # Create a StudyProcessor instance to process the DICOM Study
            dw_study_processor = DWStudyProcessor()

            # Start processing the next level
            dw_study_processor.process(study_search_response_item_ds, current_study_number, context, indent=indent+4)

            # ---------------------------------------------------------------------------------------------------------
            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            # Add the SPHN ImagingProcedure to the list
            # ---------------------------------------------------------------------------------------------------------

            # toDo: Edwin - 2025-07-27 - Check if the SPHN ImagingProcedure is having any data

            # Add the SPHN ImagingProcedure to the SPHN ImagingProcedure list in the data_store
            if data_store.sphn_imaging_procedure is not None:

                assert isinstance(data_store.sphn_imaging_procedure_list, list)

                # Add if not similar to a previous SPHN ImagingProcedure in the list (to avoid duplicates)
                if context.ALWAYS_ADD_SPHN_IMAGING_PROCEDURE \
                    or not already_in_list(data_store.sphn_imaging_procedure, data_store.sphn_imaging_procedure_list):
                    data_store.sphn_imaging_procedure_list.append(data_store.sphn_imaging_procedure)
                    logger.debug(" "*(indent+2) + "Added the SPHN ImagingProcedure to the list in the data_store")
                else:
                    logger.debug(" "*(indent+2) + "SPHN ImagingProcedure not added to the list" + 
                                " in the data_store as a similar SPHN ImagingProcedure already existed." +
                                f" in study number : '{data_store.current_study_number}'" +
                                f" for patient with PatientID: '{data_store.patient_id}'"
                    )
            else:
                logger.debug(" "*(indent+2) + "SPHN ImagingProcedure not added to the list" + 
                            " in the data_store as it was not created." +
                            f" in study number : '{data_store.current_study_number}'" +
                            f" for patient with PatientID: '{data_store.patient_id}'"
                )

            # ---------------------------------------------------------------------------------------------------------

            # Reset any previous DICOM Study level information in the data_store
            data_store.reset_imaging_study_level()

            # Set timing
            stop_time_t2 = time()
            logger.info(" "*(indent+2) + f"Done  processing DICOM Study number: '{current_study_number}'" + 
                        f" of '{number_of_studies_in_current_patient_dataset}'" +
                        f" for patient with PatientID: '{data_store.patient_id}'" +
                        " in: " + str(timedelta(seconds=(stop_time_t2 - start_time_t2)))
            )
            logger.info("")

            n_procedures, n_series, n_frames = data_store.get_number_of_sphn_procedures_series_frames_stored()
            logger.info(" "*(indent+0) + f"Total number of SPHN ImagingProcedures stored so far: {n_procedures}")
            logger.info(" "*(indent+0) + f"Total number of SPHN ImagingSeries stored so far: {n_series}")
            logger.info(" "*(indent+0) + f"Total number of SPHN ImagingFrames stored so far: {n_frames}")
            logger.info("")

            # break  # ToDo: Edwin - 2026-08-06 - Remove this break after testing the first DICOM Study

        # -------------------------------------------------------------------------------------------------------------
        # Done processing all DICOM Studies for the current DICOM Patient

        stop_time_t1 = time()
        logger.debug(" "*(indent+0) + "PatientProcessor: Done processing..." +
                    " in: " + str(timedelta(seconds=(stop_time_t1 - start_time_t1)))
        )
        logger.debug("")

        # Statistics
        logger.debug(" "*(indent+0) + f"Processed {data_store.number_of_dicom_studies_processed} DICOM Studies")
        logger.debug(" "*(indent+0) + f"Skipped {data_store.number_of_dicom_studies_skipped} DICOM Studies")
        logger.debug("")

        n = len(data_store.sphn_imaging_procedure_list)
        logger.debug(" "*(indent+0) + f"Added {n} SPHN ImagingProcedure(s) to the DataStore.")
        logger.debug("")

        logger.debug(" "*(indent+0) + f"Total number of DICOM Studies processed so far: {data_store.total_number_of_dicom_studies_processed}")
        logger.debug(" "*(indent+0) + f"Total number of DICOM Series processed so far: {data_store.total_number_of_dicom_series_processed}")
        logger.debug(" "*(indent+0) + f"Total number of DICOM Instances processed so far: {data_store.total_number_of_dicom_instances_processed}")
        logger.debug(" "*(indent+0) + f"Total number of DICOM Frames processed so far: {data_store.total_number_of_dicom_frames_processed}")
        logger.debug("")
        logger.debug(" "*(indent+0) + f"Total number of DICOM Studies skipped so far: {data_store.total_number_of_dicom_studies_skipped}")
        logger.debug(" "*(indent+0) + f"Total number of DICOM Series skipped so far: {data_store.total_number_of_dicom_series_skipped}")
        logger.debug(" "*(indent+0) + f"Total number of DICOM Instances skipped so far: {data_store.total_number_of_dicom_instances_skipped}")
        logger.debug("")

        n_procedures, n_series, n_frames = data_store.get_number_of_sphn_procedures_series_frames_stored()
        logger.debug(" "*(indent+0) + f"Total number of SPHN ImagingProcedures stored so far: {n_procedures}")
        logger.debug(" "*(indent+0) + f"Total number of SPHN ImagingSeries stored so far: {n_series}")
        logger.debug(" "*(indent+0) + f"Total number of SPHN ImagingFrames stored so far: {n_frames}")
        logger.debug("")
        
    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------
