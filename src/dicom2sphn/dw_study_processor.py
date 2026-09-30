"""
dw_study_processor.py:
    Part of the example dicom2sphn package.
    It processes the DICOM(web) Study level data.
"""
from datetime import timedelta
from time import time

import pydicom
from pydicom import Dataset

from .context import Context
from .data_converter import DataConverter
from .dw_series_processor import DWSeriesProcessor
from .sphn_concepts.sphn_code import SPHNCode
from .sphn_concepts.sphn_quantity import SPHNQuantity
from .sphn_concepts.sphn_unit import SPHNUnit
from .tools import already_in_list, is_valid_string


class DWStudyProcessor:

    def __init__(self):
        """ 
        Initializes the instance
        """

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    def process(self, study_search_response_item_ds: Dataset, current_study_number: int, context: Context, indent: int=0) -> None:
        """
        Processes the Study level data by traversing the DICOM Patient - Study - Series - Instance hierarchical tree using 
        the DICOMweb API and collecting the metadata related to the SPHN ImagingStudy and its related SPHN concepts.
        """

        # Checks
        assert isinstance(study_search_response_item_ds, Dataset)
        assert isinstance(current_study_number, int) and current_study_number > 0
        assert isinstance(context, Context)
        assert isinstance(indent,int) and indent>=0

        # Get the logger, data_store, and dw_client from the context
        logger = context.logger
        data_store = context.data_store
        dw_client = context.dw_client

        logger.debug(" "*(indent+0) + "StudyProcessor: Start processing...")
        start_time_t1 = time()

        # Update the DataStore
        data_store.current_study_number = current_study_number

        # -------------------------------------------------------------------------------------------------------------
        # Start collecting metadata from the response
        # -------------------------------------------------------------------------------------------------------------

        # Log
        logger.debug(" "*(indent+2) + "Start collecting DICOM metadata from study_search_response")

        #
        # StudyInstanceUID
        #

        # Get the StudyInstanceUID
        study_instance_uid = self.get_study_instance_uid_from_dicomweb_response(study_search_response_item_ds, context, indent=indent+4)

        if study_instance_uid is not None:
            data_store.study_instance_uid = study_instance_uid
            logger.debug(" "*(indent+4) + f"StudyInstanceUID: '{data_store.study_instance_uid}'")
        else:
            logger.debug(" "*(indent+4) + "StudyInstanceUID is not defined")
            data_store.increment_dicom_studies_skipped_counter()
            return

        #
        # NumberOfStudyRelatedSeries
        #

        # Get the NumberOfStudyRelatedSeries
        number_of_study_related_series = self.get_number_of_study_related_series_from_dicomweb_response(study_search_response_item_ds, context, indent=indent+4)

        if number_of_study_related_series is not None:

            if number_of_study_related_series > 0:
                data_store.number_of_study_related_series = number_of_study_related_series
                logger.debug(" "*(indent+4) + f"NumberOfStudyRelatedSeries: '{data_store.number_of_study_related_series}'")
            else:
                logger.warning(" "*(indent+4) + "No DICOM Series defined")
                data_store.increment_dicom_studies_skipped_counter()
                return
            
        else:
            logger.debug(" "*(indent+4) + "NumberOfStudyRelatedSeries is not defined")

        #
        # NumberOfStudyRelatedInstances
        #

        # Get the NumberOfStudyRelatedInstances
        number_of_study_related_instances = self.get_number_of_study_related_instances_from_dicomweb_response(study_search_response_item_ds, context, indent=indent+4)

        if number_of_study_related_instances is not None:

            if number_of_study_related_instances > 0:
                data_store.number_of_study_related_instances = number_of_study_related_instances
                logger.debug(" "*(indent+4) + f"NumberOfStudyRelatedInstances: '{data_store.number_of_study_related_instances}'")
            else:
                logger.warning(" "*(indent+4) + "No DICOM Instances defined")
                data_store.increment_dicom_studies_skipped_counter()
                return
            
        else:
            logger.debug(" "*(indent+4) + "NumberOfStudyRelatedInstances is not defined")

        #
        # ModalitiesInStudy DCM code(s)
        #

        # Not used

        # Get the ModalitiesInStudy DCM code(s)
        modalities_in_study_code_list = self.get_modalities_in_study_from_dicomweb_response(study_search_response_item_ds, context, indent=indent+4)

        if modalities_in_study_code_list is not None:

            assert isinstance(modalities_in_study_code_list, list) and len(modalities_in_study_code_list) > 0

            data_store.modalities_in_study_code_list = modalities_in_study_code_list
            logger.debug(" "*(indent+4) + f"ModalitiesInStudy code(s): '{data_store.modalities_in_study_code_list}'")

        else:
            logger.debug(" "*(indent+4) + "ModalitiesInStudy codes are not defined")


        #
        # Imaging Procedure SNOMED-CT code(s) based on ModalitiesInStudy DICOM terms
        #

        # Get the modality-based Imaging Procedure SNOMED-CT code(s)
        modality_based_imaging_procedure_code_list = self.get_modality_based_imaging_procedure_codes_from_dicomweb_response(study_search_response_item_ds, context, indent=indent+4)

        if modality_based_imaging_procedure_code_list is not None:
            
            assert isinstance(modality_based_imaging_procedure_code_list, list) and len(modality_based_imaging_procedure_code_list) > 0

            data_store.modality_based_imaging_procedure_code_list = modality_based_imaging_procedure_code_list
            logger.debug(" "*(indent+4) + f"Modality-based Imaging Procedure code(s): '{data_store.modality_based_imaging_procedure_code_list}'")
        
        else:
            logger.debug(" "*(indent+4) + "Modality-based Imaging Procedure codes are not defined")

        # 
        # Done
        #
        logger.debug(" "*(indent+2) + "Done  collecting DICOM metadata from study_search_response")

        # -------------------------------------------------------------------------------------------------------------
        # Done  collecting metadata from the response
        # -------------------------------------------------------------------------------------------------------------

        # Check
        assert is_valid_string(data_store.study_instance_uid)
        assert data_store.number_of_study_related_series is None \
                or (isinstance(data_store.number_of_study_related_series, int) and data_store.number_of_study_related_series>0) 

        assert data_store.number_of_study_related_instances is None \
                or (isinstance(data_store.number_of_study_related_instances, int) and data_store.number_of_study_related_instances>0) 

        assert data_store.modalities_in_study_code_list is None \
                or (isinstance(data_store.modalities_in_study_code_list, list) \
                    and len(data_store.modalities_in_study_code_list)>0 \
                    and all(is_valid_string(item) for code_tuple in data_store.modalities_in_study_code_list for item in code_tuple))

        # -------------------------------------------------------------------------------------------------------------
        # Find all DICOM Series belonging to the DICOM Study on the DICOMweb server
        # -------------------------------------------------------------------------------------------------------------

        logger.debug(" "*(indent+2) + "Start querying DICOMweb server for DICOM Series" + 
                     " related to the DICOM Study")
        # Set timing
        start_time_t99 = time()

        # Run Query
        # The series_search_response_json is the DICOMweb API "Series Resource Search Response Payload" 
        #  - For more info see: https://dicom.nema.org/medical/dicom/current/output/html/part18.html#table_10.6.3-4
        # The parameters "offset" and "limit" seems to be not implemented, hence get_remaining is set to False
        series_search_response_json = dw_client.search_for_series(
            study_instance_uid = data_store.study_instance_uid,
            get_remaining = False
        )

        # Set timing
        stop_time_t99 = time()
        logger.debug(" "*(indent+2) + "Done  querying DICOMweb server for DICOM Series" + 
                     " related to the DICOM Study" +
                     " in: " + str(timedelta(seconds=(stop_time_t99 - start_time_t99)))
        )

        # Get number of series in current study
        number_of_series_in_current_study = len(series_search_response_json)


        # Check if there is any DICOM Series defined in the current DICOM Study
        if number_of_series_in_current_study == 0:
            logger.warning(" "*(indent+2) + "No DICOM Series found" +
                            f" in study number : '{current_study_number}'" +
                            f" with DICOM StudyInstanceUID: '{data_store.study_instance_uid}'"
            )
            # Nothing to do, return
            data_store.increment_dicom_studies_skipped_counter()
            return

        # -------------------------------------------------------------------------------------------------------------
        # For every DICOM Series
        # -------------------------------------------------------------------------------------------------------------

        for current_series_number, series_search_response_item_json in enumerate(series_search_response_json, start=1):
    
            logger.info(" "*(indent+2) + f"Start processing DICOM Series number: '{current_series_number}'" + 
                        f" of '{number_of_series_in_current_study}'" +
                        f" in study number : '{data_store.current_study_number}'" +
                        f" for patient with PatientID: '{data_store.patient_id}'"
            )
            start_time_t2 = time()

            # Reset any previous DICOM Series level information in the data_store
            data_store.reset_imaging_series_level()

            # Converting JSON to DICOM Dataset
            series_search_response_item_ds = Dataset.from_json(series_search_response_item_json)

            # Create a SeriesProcessor instance to process the DICOM Series
            dw_series_processor = DWSeriesProcessor()

            # Start processing the next level
            dw_series_processor.process(series_search_response_item_ds, current_series_number, context, indent=indent+4)

            # ---------------------------------------------------------------------------------------------------------
            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            # Add the number of frames in series to the SPHN Imaging Series
            # ---------------------------------------------------------------------------------------------------------

            if data_store.sphn_imaging_series is not None:

                assert data_store.number_of_frames_in_series > 0

                # Add number of frames to the SPHN ImagingSeries as a SPHN Quantity
                sphn_code_num_of_frames = SPHNCode( 
                    sphn_schema = data_store.sphn_schema,
                    has_identifier = "cblnbcbr", # UCUM | {#} |
                    has_coding_system_and_version = "UCUM"
                )
                sphn_unit_num_of_frames = SPHNUnit(
                    sphn_schema = data_store.sphn_schema,
                    has_code = sphn_code_num_of_frames
                )
                sphn_quantity_num_of_frames = SPHNQuantity(
                    sphn_schema = data_store.sphn_schema,
                    has_value = data_store.number_of_frames_in_series,
                    has_unit = sphn_unit_num_of_frames
                )
                data_store.sphn_imaging_series.has_number_of_frames = sphn_quantity_num_of_frames

                logger.debug(" "*(indent+0) + f"Added SPHN ImagingSeries has_number_of_frames value: '{data_store.number_of_frames_in_series}', unit UCUM code:'cblnbcbr'")

            # ---------------------------------------------------------------------------------------------------------
            # Add the SPHN ImagingSeries to the SPHN ImagingProcedure in the data_store
            # ---------------------------------------------------------------------------------------------------------

            # toDo: Edwin - 2025-07-27 - Check if the SPHN ImagingSeries is having any data

            # Add the SPHN ImagingSeries to the SPHN ImagingProcedure in the data_store
            if data_store.sphn_imaging_series is not None:

                assert isinstance(data_store.sphn_imaging_series_list, list)
                assert data_store.sphn_imaging_procedure is not None

                if data_store.sphn_imaging_procedure.has_imaging_series_list is None:
                    data_store.sphn_imaging_procedure.has_imaging_series_list = [data_store.sphn_imaging_series]
                    logger.debug(" "*(indent+2) + "Added the SPHN ImagingSeries to the SPHN ImagingProcedure in the data_store")
                    data_store.increment_sphn_imaging_series_added_to_sphn_imaging_procedure_counter()
                else:

                    assert isinstance(data_store.sphn_imaging_procedure.has_imaging_series_list, list)

                    # Add if not similar to a previous SPHN ImagingSeries in the list (to avoid duplicates)
                    if context.ALWAYS_ADD_SPHN_IMAGING_SERIES \
                        or not already_in_list(data_store.sphn_imaging_series, data_store.sphn_imaging_procedure.has_imaging_series_list):
                        data_store.sphn_imaging_procedure.has_imaging_series_list.append(data_store.sphn_imaging_series)
                        logger.debug(" "*(indent+2) + "Added the SPHN ImagingSeries to the SPHN ImagingProcedure in the data_store")
                        data_store.increment_sphn_imaging_series_added_to_sphn_imaging_procedure_counter()
                    else:
                        logger.debug(" "*(indent+2) + "SPHN ImagingSeries not added to the SPHN ImagingProcedure" + 
                                    " in the data_store as a similar SPHN ImagingSeries already existed." +
                                    f" Series number: '{data_store.current_series_number}'" +
                                    f" in study number : '{data_store.current_study_number}'" +
                                    f" for patient with PatientID: '{data_store.patient_id}'"
                        )


            else:
                logger.debug(" "*(indent+2) + "SPHN ImagingSeries not added to the SPHN ImagingProcedure" + 
                            " in the data_store as the SPHN ImagingSeries was not created." +
                            f" Series number: '{data_store.current_series_number}'" +
                            f" in study number : '{data_store.current_study_number}'" +
                            f" for patient with PatientID: '{data_store.patient_id}'"
                )

            # ---------------------------------------------------------------------------------------------------------

            # Reset any previous DICOM Series level information in the data_store
            data_store.reset_imaging_series_level()

            stop_time_t2 = time()
            logger.info(" "*(indent+2) + f"Done  processing DICOM Series number: '{current_series_number}'" + 
                        f" of '{number_of_series_in_current_study}'" +
                        f" in study number : '{current_study_number}'" +
                        f" for patient with PatientID: '{data_store.patient_id}'" +
                        " in: " + str(timedelta(seconds=(stop_time_t2 - start_time_t2)))
            )
            logger.info("")

            #break  # ToDo: Edwin - 2026-08-06 - Remove this break after testing the first DICOM Series
        # -------------------------------------------------------------------------------------------------------------
        # Done processing all DICOM Series in the current DICOM Study

        # Add the SPHN ImagingSeries list to the SPHN ImagingProcedure
        # if data_store.sphn_imaging_procedure is not None:

        #     assert isinstance(data_store.sphn_imaging_series_list, list)
        #     if len(data_store.sphn_imaging_series_list) > 0:
        #         data_store.sphn_imaging_procedure.has_imaging_series_list = data_store.sphn_imaging_series_list
        #         logger.debug(" "*(indent+2) + "Added the SPHN ImagingSeries list to the SPHN ImagingProcedure")
        #     else:
        #         logger.debug(" "*(indent+2) + "SPHN ImagingSeries list was not added to the SPHN ImagingProcedure" + 
        #                     " as it was empty." +
        #                     f" In study number : '{data_store.current_study_number}'" +
        #                     f" for patient with PatientID: '{data_store.patient_id}'"
        #         )
        # else:
        #     logger.debug(" "*(indent+2) + "SPHN ImagingSeries list was not added to the SPHN ImagingProcedure" + 
        #                 " as the SPHN ImagingProcedure was not created." +
        #                 f" In study number : '{data_store.current_study_number}'" +
        #                 f" for patient with PatientID: '{data_store.patient_id}'"
        #     )
        # logger.debug("")

        stop_time_t1 = time()
        logger.debug(" "*(indent+0) + "StudyProcessor: Done processing..." +
                    " in: " + str(timedelta(seconds=(stop_time_t1 - start_time_t1)))
        )
        logger.debug("")

        # Statistics
        data_store.increment_dicom_studies_processed_counter()

        logger.debug(" "*(indent+0) + f"Processed {data_store.number_of_dicom_series_processed} DICOM Series")
        logger.debug(" "*(indent+0) + f"Skipped {data_store.number_of_dicom_series_skipped} DICOM Series")

        logger.debug(" "*(indent+0) + f"Added {data_store.number_of_sphn_imaging_series_added_to_sphn_imaging_procedure} SPHN ImagingSeries to the SPHN ImagingProcedure in the data_store.")
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

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions - related to processing the DICOMweb API "Study Resource Search Response Payload"
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-07-24
    #
    # Not Used as PatientID is already provided
    #
    def get_patient_id_from_dicomweb_response(self, dataset: Dataset, context: Context, indent: int=0) -> str|None:
        """
        Returns the value corresponding to the value of the DICOM PatientID tag
        Parameters:
            - dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)
            - context: The Context object that holds the data_store, logger and other relevant information
            - indent: The indentation level for logging (default is 0)
        
        Note: The DICOM PatientID tag is part of the DICOMweb API "Study Resource Search 
              Response Payload". It's type is '[R]equired'
              For more info see: 
              https://dicom.nema.org/medical/dicom/current/output/html/part18.html#table_10.6.3-3
        """

        # Keyword:              PatientID
        # Value Representation: PatientID
        # Type:	                Required, Empty if Unknown (2)
        # Value Multiplicity:   1

        # Check
        assert isinstance(dataset, Dataset)
        assert isinstance(context, Context)
        assert isinstance(indent,int) and indent>=0

        logger = context.logger

        if "PatientID" not in dataset:
            logger.warning(" "*(indent+0) + "DICOM PatientID tag was not found")
            return None

        # Get the DataElement
        data_element = dataset["PatientID"]

        # Get the value
        value = data_element.value
            
        # Get the Value Multiplicity
        value_multiplicity = data_element.VM
            
        # Check if it is empty
        if value_multiplicity == 0 or value is None:
            logger.warning(" "*(indent+0) + "DICOM PatientID tag value was not provided")
            return None

        # It should be a single-valued tag, a string            
        if value_multiplicity != 1 or not isinstance(value, str):
            logger.warning(" "*(indent+0) + "DICOM PatientID tag has an unknown format")
            return None
            
        # Remove whitespace
        patient_id_str = value.strip()

        # Check if value is not empty
        if len(patient_id_str) == 0:
            logger.warning(" "*(indent+0) + "DICOM PatientID tag contains only whitespace")
            return None

        return patient_id_str


    #
    # Edwin 2026-07-24
    #
    def get_study_instance_uid_from_dicomweb_response(self, dataset: Dataset, context: Context, indent: int=0) -> str|None:
        """
        Returns the value corresponding to the value of the DICOM StudyInstanceUID tag
          - dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)

        Note: The DICOM StudyInstanceUID tag is part of the DICOMweb API "Study Resource Search 
              Response Payload". It's type is '[U]nique and Required'
              For more info see: 
              https://dicom.nema.org/medical/dicom/current/output/html/part18.html#table_10.6.3-3
        """

        # Keyword:              StudyInstanceUID
        # Value Representation: Unique Identifier (UI)
        # Type:	                Required (1)
        # Value Multiplicity:   1

        # Check
        assert isinstance(dataset, Dataset)
        assert isinstance(context, Context)
        assert isinstance(indent,int) and indent>=0

        logger = context.logger

        if "StudyInstanceUID" not in dataset:
            logger.warning(" "*(indent+0) + "DICOM StudyInstanceUID tag was not found")
            return None

        # Get the DataElement
        data_element = dataset["StudyInstanceUID"]

        # Get the value
        value = data_element.value
            
        # Get the Value Multiplicity
        value_multiplicity = data_element.VM
            
        # Check if it is empty
        if value_multiplicity == 0 or value is None:
            logger.warning(" "*(indent+0) + "DICOM StudyInstanceUID tag value was not provided")
            return None

        # It should be a single-valued tag, a string            
        if value_multiplicity != 1 or not isinstance(value, str):
            logger.warning(" "*(indent+0) + "DICOM StudyInstanceUID tag has an unknown format")
            return None
            
        # Remove whitespace
        study_instance_uid_str = value.strip()

        # Check if value is not empty
        if len(study_instance_uid_str) == 0:
            logger.warning(" "*(indent+0) + "DICOM StudyInstanceUID tag contains only whitespace")
            return None

        return study_instance_uid_str
    
    #
    # Edwin 2026-07-24
    #
    def get_number_of_study_related_series_from_dicomweb_response(self, dataset: Dataset, context: Context, indent: int=0) -> int|None:
        """
        Returns the value corresponding to the value of the DICOM NumberOfStudyRelatedSeries tag
          - dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)

        Note: The DICOM NumberOfStudyRelatedSeries tag is part of the DICOMweb API "Study Resource Search 
              Response Payload". It's type is '[R]equired'
              For more info see: 
              https://dicom.nema.org/medical/dicom/current/output/html/part18.html#table_10.6.3-3
        """

        # Keyword:              NumberOfStudyRelatedSeries
        # Value Representation: Integer String (IS)
        # Type:	                Required, Empty if Unknown (2)
        # Value Multiplicity:   1

        # Check
        assert isinstance(dataset, Dataset)
        assert isinstance(context, Context)
        assert isinstance(indent,int) and indent>=0

        logger = context.logger

        if "NumberOfStudyRelatedSeries" not in dataset:
            logger.warning(" "*(indent+0) + "DICOM NumberOfStudyRelatedSeries tag was not found")  
            return None

        # Get the DataElement
        data_element = dataset["NumberOfStudyRelatedSeries"]

        # Get the value
        value = data_element.value
        
        # Get the Value Multiplicity
        value_multiplicity = data_element.VM
        
        # Check if it is empty
        if value_multiplicity == 0 or value is None:
            logger.debug(" "*(indent+0) + "DICOM NumberOfStudyRelatedSeries tag value was not provided")
            return None
        
        # It should be a single-valued tag, an integer
        if value_multiplicity != 1 or not isinstance(value, pydicom.valuerep.IS):
            logger.warning(" "*(indent+0) + "DICOM NumberOfStudyRelatedSeries tag has an unknown format")
            return None

        # Try to convert IS to int
        try:
            number_of_study_related_series = int(value)
        except (TypeError, ValueError):
            logger.warning(" "*(indent+0) + "DICOM NumberOfStudyRelatedSeries value could not be converted to an int value.")
            return None

        if number_of_study_related_series < 0:
            logger.warning(" "*(indent+0) + f"DICOM NumberOfStudyRelatedSeries tag value: '{number_of_study_related_series}' is likely not a valid value")

        return number_of_study_related_series
    
    #
    # Edwin 2026-07-24
    #
    def get_number_of_study_related_instances_from_dicomweb_response(self, dataset: Dataset, context: Context, indent: int=0) -> int|None:
        """
        Returns the value corresponding to the value of the DICOM NumberOfStudyRelatedInstances tag
          - dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)

        Note: The DICOM NumberOfStudyRelatedInstances tag is part of the DICOMweb API "Study Resource Search 
              Response Payload". It's type is '[R]equired'
              For more info see: 
              https://dicom.nema.org/medical/dicom/current/output/html/part18.html#table_10.6.3-3
        """

        # Keyword:              NumberOfStudyRelatedInstances
        # Value Representation: Integer String (IS)
        # Type:	                Required, Empty if Unknown (2)
        # Value Multiplicity:   1

        # Check
        assert isinstance(dataset, Dataset)
        assert isinstance(context, Context)
        assert isinstance(indent,int) and indent>=0

        logger = context.logger

        if "NumberOfStudyRelatedInstances" not in dataset:
            logger.warning(" "*(indent+0) + "DICOM NumberOfStudyRelatedInstances tag was not found")  
            return None

        # Get the DataElement
        data_element = dataset["NumberOfStudyRelatedInstances"]

        # Get the value
        value = data_element.value
        
        # Get the Value Multiplicity
        value_multiplicity = data_element.VM
        
        # Check if it is empty
        if value_multiplicity == 0 or value is None:
            logger.debug(" "*(indent+0) + "DICOM NumberOfStudyRelatedInstances tag value was not provided")
            return None
        
        # It should be a single-valued tag, an integer
        if value_multiplicity != 1 or not isinstance(value, pydicom.valuerep.IS):
            logger.warning(" "*(indent+0) + "DICOM NumberOfStudyRelatedInstances tag has an unknown format")
            return None

        # Try to convert IS to int
        try:
            number_of_study_related_instances = int(value)
        except (TypeError, ValueError):
            logger.warning(" "*(indent+0) + "DICOM NumberOfStudyRelatedInstances value could not be converted to an int value.")
            return None

        if number_of_study_related_instances < 0:
            logger.warning(" "*(indent+0) + f"DICOM NumberOfStudyRelatedInstances tag value: '{number_of_study_related_instances}' is likely not a valid value")

        return number_of_study_related_instances

    #
    # Edwin 2026-09-28
    #
    def get_modalities_in_study_from_dicomweb_response(self, dataset: Dataset, context: Context, indent: int=0) -> list[tuple[str,str,str]]|None:
        """
        Returns a list with DCM codes corresponding to the values of the DICOM ModalitiesInStudy tag
        Parameters:
            - dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)
            - context: The Context object that holds the data_store, logger and other relevant information
            - indent: The indentation level for logging (default is 0)

        Note 1: DICOM codes not having a corresponding DCM code will be skipped.
        Note 2: The DICOM ModalitiesInStudy tag is part of the DICOMweb API "Study Resource Search 
                Response Payload". It's type is '[R]equired'
                For more info see: 
                https://dicom.nema.org/medical/dicom/current/output/html/part18.html#table_10.6.3-3
        """

        # Keyword:              ModalitiesInStudy
        # Value Representation: Code String (CS)
        # Type:	                Required, Empty if Unknown (2)
        # Value Multiplicity:   1-n

        # Check
        assert isinstance(dataset, Dataset)
        assert isinstance(context, Context)
        assert isinstance(indent,int) and indent>=0

        logger = context.logger

        # Set initial value
        modality_code_list = []

        if "ModalitiesInStudy" not in dataset:
            logger.warning(" "*(indent+0) + "DICOM ModalitiesInStudy tag was not found")  
            return None

        # Get the DataElement
        data_element = dataset["ModalitiesInStudy"]

        # Get the value
        value = data_element.value
        
        # Get the Value Multiplicity
        value_multiplicity = data_element.VM
        
        # Check if it is empty
        if value_multiplicity == 0 or value is None:
            logger.debug(" "*(indent+0) + "DICOM ModalitiesInStudy tag value was not provided")
            return None

        # It could be a multi-valued tag
        if value_multiplicity >= 1 and isinstance(value, pydicom.multival.MultiValue):

            # For each value in the multi-value list
            for value_item in value:

                if not isinstance(value_item, str):
                    logger.warning(" "*(indent+0) + "DICOM ModalitiesInStudy tag value-item has an unknown format")
                    continue

                # Remove whitespace
                modality_code_str = value_item.strip()

                # Check if value is not empty
                if len(modality_code_str) == 0:
                    logger.debug(" "*(indent+0) + "DICOM ModalitiesInStudy tag value-item contains only whitespace")
                    continue

                # Convert the value to a corresponding DCM code
                result = DataConverter.dicom_modality_code_dict.get(modality_code_str.upper(), None)

                # Check if it is a know DICOM modality code
                if result is None:
                    logger.warning(" "*(indent+0) + f"DICOM ModalitiesInStudy tag value-item: '{modality_code_str}' is unknown")
                    continue

                assert isinstance(result, tuple) and len(result) == 2
                assert isinstance(result[0], tuple) and len(result[0]) == 3
                assert isinstance(result[0][0], str)
                assert isinstance(result[0][1], str)
                assert isinstance(result[0][2], str)

                modality_coding_scheme_designator = result[0][0]
                modality_code_value = result[0][1]
                modality_code_descr = result[0][2]

                # Check if the corresponding DCM code and description exists
                if modality_coding_scheme_designator == "" or modality_code_value == "" or modality_code_descr == "":
                    logger.warning(" "*(indent+0) + f"DICOM ModalitiesInStudy tag value-item: '{modality_code_str}' could not be converted to a Modality code")
                    continue

                # Check conversion is ok
                assert is_valid_string(modality_coding_scheme_designator)
                assert is_valid_string(modality_code_value)
                assert is_valid_string(modality_code_descr)

                # Add to the list, ensuring no duplicates
                if (modality_coding_scheme_designator, modality_code_value, modality_code_descr) not in modality_code_list:
                    modality_code_list.append((modality_coding_scheme_designator, modality_code_value, modality_code_descr))

        # It could be a single-valued tag, a string
        elif value_multiplicity == 1 and isinstance(value, str):

            # Remove whitespace
            modality_code_str = value.strip()

            # Check if value is not empty
            if len(modality_code_str) == 0:
                logger.debug(" "*(indent+0) + "DICOM ModalitiesInStudy tag value contains only whitespace")
                return None
            
            # Convert the value to a corresponding DCM code
            result = DataConverter.dicom_modality_code_dict.get(modality_code_str.upper(), None)

            # Check if it is a know DICOM modality code
            if result is None:
                logger.warning(" "*(indent+0) + f"DICOM ModalitiesInStudy tag value: '{modality_code_str}' is unknown")
                return None

            assert isinstance(result, tuple) and len(result) == 2
            assert isinstance(result[0], tuple) and len(result[0]) == 3
            assert isinstance(result[0][0], str)
            assert isinstance(result[0][1], str)
            assert isinstance(result[0][2], str)

            modality_coding_scheme_designator = result[0][0]
            modality_code_value = result[0][1]
            modality_code_descr = result[0][2]

            # Check if the corresponding DCM code and description exists
            if modality_coding_scheme_designator == "" or modality_code_value == "" or modality_code_descr == "":
                logger.warning(" "*(indent+0) + f"DICOM ModalitiesInStudy tag value: '{modality_code_str}' could not be converted to a Modality code")
                return None
    
            # Check conversion is ok
            assert is_valid_string(modality_coding_scheme_designator)
            assert is_valid_string(modality_code_value)
            assert is_valid_string(modality_code_descr)

            # Add to the list, ensuring no duplicates
            modality_code_list = [(modality_coding_scheme_designator, modality_code_value, modality_code_descr)]

        else:
            logger.warning(" "*(indent+0) + "DICOM ModalitiesInStudy tag has an unknown format")
            return None

        return modality_code_list if len(modality_code_list)>0 else None


    #
    # Edwin 2026-09-28
    #
    def get_modality_based_imaging_procedure_codes_from_dicomweb_response(self, dataset: Dataset, context: Context, indent: int=0) -> list[tuple[str, str, str]]|None:
        """
        Returns a list with SNOMED-CT codes corresponding to the values of the DICOM ModalitiesInStudy tag
        Parameters:
            - dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)
            - context: The Context object that holds the data_store, logger and other relevant information
            - indent: The indentation level for logging (default is 0)

        Note 1: DICOM codes not having a corresponding Imaging Procedure SNOMED-CT code will be skipped.
        Note 2: The DICOM ModalitiesInStudy tag is part of the DICOMweb API "Study Resource Search 
                Response Payload". It's type is '[R]equired'
                For more info see: 
                https://dicom.nema.org/medical/dicom/current/output/html/part18.html#table_10.6.3-3
        """

        # Keyword:              ModalitiesInStudy
        # Value Representation: Code String (CS)
        # Type:	                Required, Empty if Unknown (2)
        # Value Multiplicity:   1-n

        # Check
        assert isinstance(dataset, Dataset)
        assert isinstance(context, Context)
        assert isinstance(indent,int) and indent>=0

        logger = context.logger

        # Set initial value
        imaging_procedure_code_list = []

        if "ModalitiesInStudy" not in dataset:
            logger.warning(" "*(indent+0) + "DICOM ModalitiesInStudy tag was not found")  
            return None

        # Get the DataElement
        data_element = dataset["ModalitiesInStudy"]

        # Get the value
        value = data_element.value
        
        # Get the Value Multiplicity
        value_multiplicity = data_element.VM
        
        # Check if it is empty
        if value_multiplicity == 0 or value is None:
            logger.debug(" "*(indent+0) + "DICOM ModalitiesInStudy tag value was not provided")
            return None

        # It could be a multi-valued tag
        if value_multiplicity >= 1 and isinstance(value, pydicom.multival.MultiValue):

            # For each value in the multi-value list
            for value_item in value:

                if not isinstance(value_item, str):
                    logger.warning(" "*(indent+0) + "DICOM ModalitiesInStudy tag value-item has an unknown format")
                    continue

                # Remove whitespace
                modality_code_str = value_item.strip()

                # Check if value is not empty
                if len(modality_code_str) == 0:
                    logger.debug(" "*(indent+0) + "DICOM ModalitiesInStudy tag value-item contains only whitespace")
                    continue

                # Convert the value to a corresponding SNOMED CT code
                result = DataConverter.dicom_modality_code_dict.get(modality_code_str.upper(), None)

                # Check if it is a know SNOMED-CT code
                if result is None:
                    logger.warning(" "*(indent+0) + f"DICOM ModalitiesInStudy tag value-item: '{modality_code_str}' is unknown")
                    continue

                assert isinstance(result, tuple) and len(result) == 2
                assert isinstance(result[1], tuple) and len(result[1]) == 3
                assert isinstance(result[1][0], str)
                assert isinstance(result[1][1], str)
                assert isinstance(result[1][2], str)

                # Convert the value to a corresponding Imaging Procedure SNOMED-CT code
                imaging_procedure_coding_scheme_designator = result[1][0]
                imaging_procedure_code_value = result[1][1]
                imaging_procedure_code_descr = result[1][2]

                if imaging_procedure_coding_scheme_designator == "" or imaging_procedure_code_value == "" or imaging_procedure_code_descr == "":
                    logger.warning(" "*(indent+0) + f"DICOM ModalitiesInStudy tag value-item: '{modality_code_str}' could not be converted to a corresponding Imaging Procedure code")
                    continue

                # Check conversion is ok
                assert is_valid_string(imaging_procedure_coding_scheme_designator)
                assert is_valid_string(imaging_procedure_code_value)
                assert is_valid_string(imaging_procedure_code_descr)

                # Add to the list, ensuring no duplicates
                if (imaging_procedure_coding_scheme_designator, imaging_procedure_code_value, imaging_procedure_code_descr) not in imaging_procedure_code_list:
                    imaging_procedure_code_list.append((imaging_procedure_coding_scheme_designator, imaging_procedure_code_value, imaging_procedure_code_descr))

        # It could be a single-valued tag, a string
        elif value_multiplicity == 1 and isinstance(value, str):

            # Remove whitespace
            modality_code_str = value.strip()

            # Check if value is not empty
            if len(modality_code_str) == 0:
                logger.debug(" "*(indent+0) + "DICOM ModalitiesInStudy tag value contains only whitespace")
                return None

            # Convert the value to a corresponding SNOMED CT code
            result = DataConverter.dicom_modality_code_dict.get(modality_code_str.upper(), None)

            # Check if it is a know SNOMED-CT code
            if result is None:
                logger.warning(" "*(indent+0) + f"DICOM ModalitiesInStudy tag value: '{modality_code_str}' is unknown")
                return None

            assert isinstance(result, tuple) and len(result) == 2
            assert isinstance(result[1], tuple) and len(result[1]) == 3
            assert isinstance(result[1][0], str)
            assert isinstance(result[1][1], str)
            assert isinstance(result[1][2], str)

            # Convert the value to a corresponding Imaging Procedure SNOMED-CT code
            imaging_procedure_coding_scheme_designator = result[1][0]
            imaging_procedure_code_value = result[1][1]
            imaging_procedure_code_descr = result[1][2]

            if imaging_procedure_coding_scheme_designator == "" or imaging_procedure_code_value == "" or imaging_procedure_code_descr == "":
                logger.warning(" "*(indent+0) + f"DICOM ModalitiesInStudy tag value: '{modality_code_str}' could not be converted to a corresponding Imaging Procedure code")
                return None

            # Check conversion is ok
            assert is_valid_string(imaging_procedure_coding_scheme_designator)
            assert is_valid_string(imaging_procedure_code_value)
            assert is_valid_string(imaging_procedure_code_descr)

            # Add to the list, ensuring no duplicates
            imaging_procedure_code_list = [(imaging_procedure_coding_scheme_designator, imaging_procedure_code_value, imaging_procedure_code_descr)]

        else:
            logger.warning(" "*(indent+0) + "DICOM ModalitiesInStudy tag has an unknown format")
            return None

        return imaging_procedure_code_list if len(imaging_procedure_code_list)>0 else None


