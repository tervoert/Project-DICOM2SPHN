"""
dw_series_processor.py:
    Part of the example dicom2sphn package.
    It processes the DICOM(web) Series level data.
"""
from datetime import timedelta
from time import time

import pydicom
from pydicom import Dataset

from .context import Context
from .data_converter import DataConverter
from .dw_instance_processor import DWInstanceProcessor
from .tools import already_in_list, is_valid_string


class DWSeriesProcessor:

    def __init__(self):
        """ 
        Initializes the instance
        """

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    def process(self, series_search_response_item_ds: Dataset, current_series_number: int, context: Context, indent: int=0) -> None:
        """
        Processes the Series level data by traversing the DICOM Patient - Study - Series - Instance hierarchical tree using 
        the DICOMweb API and collecting the metadata related to the SPHN ImagingSeries and its related SPHN concepts.
        """

        # Checks
        assert isinstance(series_search_response_item_ds, Dataset)
        assert isinstance(current_series_number, int) and current_series_number > 0
        assert isinstance(context, Context)
        assert isinstance(indent,int) and indent>=0

        # Get the logger, data_store, and dw_client from the context
        logger = context.logger
        data_store = context.data_store
        dw_client = context.dw_client

        logger.debug(" "*(indent+0) + "SeriesProcessor: Start processing...")
        start_time_t1 = time()

        # Update the DataStore
        data_store.current_series_number = current_series_number    

        # -------------------------------------------------------------------------------------------------------------
        # Start collecting metadata from the response
        # -------------------------------------------------------------------------------------------------------------

        logger.debug(" "*(indent+2) + "Start collecting DICOM metadata from series_search_response")

        #
        # SeriesInstanceUID
        #

        # Get the SeriesInstanceUID
        series_instance_uid = self.get_series_instance_uid_from_dicomweb_response(series_search_response_item_ds, context, indent=indent+4)

        if series_instance_uid is not None:
            data_store.series_instance_uid = series_instance_uid
            logger.debug(" "*(indent+4) + f"SeriesInstanceUID: '{data_store.series_instance_uid}'")
        else:
            logger.debug(" "*(indent+4) + "SeriesInstanceUID not defined")
            data_store.increment_dicom_series_skipped_counter()
            return

        #
        # NumberOfSeriesRelatedInstances
        #

        # Get the NumberOfSeriesRelatedInstances
        number_of_series_related_instances = self.get_number_of_series_related_instances_from_dicomweb_response(series_search_response_item_ds, context, indent=indent+4)

        if number_of_series_related_instances is not None:
            if number_of_series_related_instances > 0:
                data_store.number_of_series_related_instances = number_of_series_related_instances
                logger.debug(" "*(indent+4) + f"NumberOfSeriesRelatedInstances: '{data_store.number_of_series_related_instances}'")
            else:
                logger.warning(" "*(indent+4) + "No DICOM Instances defined")
                data_store.increment_dicom_series_skipped_counter()
                return
        else:
            logger.debug(" "*(indent+4) + "NumberOfSeriesRelatedInstances is not defined")

        # 
        # Modality
        #

        # Get the Modality
        result = self.get_modality_from_dicomweb_response(series_search_response_item_ds, context, indent=indent+4)

        if result is not None:
            
            assert isinstance(result, tuple) and len(result) == 3

            modality_coding_scheme_designator, modality_dcm_code, modality_dcm_description = result
            data_store.modality_coding_scheme_designator = modality_coding_scheme_designator
            data_store.modality_dcm_code = modality_dcm_code
            data_store.modality_dcm_description = modality_dcm_description
            logger.debug(" "*(indent+4) + f"Modality coding scheme designator: '{modality_coding_scheme_designator}', code: '{data_store.modality_dcm_code}', description: '{data_store.modality_dcm_description}'")
        
        else:
            logger.debug(" "*(indent+4) + "Modality not defined")

        # 
        # Done
        #
        logger.debug(" "*(indent+2) + "Done  collecting DICOM metadata from series_search_response")

        # -------------------------------------------------------------------------------------------------------------
        # Done collecting metadata from the response
        # -------------------------------------------------------------------------------------------------------------

        # Check
        assert is_valid_string(data_store.series_instance_uid)
        assert data_store.modality_dcm_code is None or is_valid_string(data_store.modality_dcm_code)

        # -------------------------------------------------------------------------------------------------------------
        # Find all DICOM SOP Instances belonging to the DICOM Series on the DICOMweb server
        # -------------------------------------------------------------------------------------------------------------

        logger.debug(" "*(indent+2) + "Start querying DICOMweb server for DICOM Instances" +
                     " related to the DICOM Series in the DICOM Study"
        )
        start_time_t99 = time()

        # Run Query
        # The instance_search_response_json is the DICOMweb API "Instance Resource Search Response Payload" 
        #  - For more info see: https://dicom.nema.org/medical/dicom/current/output/html/part18.html#table_10.6.3-5
        # The parameters "offset" and "limit" seems to be not implemented, hence get_remaining is set to False
        instance_search_response_json = dw_client.search_for_instances(
            study_instance_uid = data_store.study_instance_uid,
            series_instance_uid = data_store.series_instance_uid,
            get_remaining = False
        )

        stop_time_t99 = time()
        logger.debug(" "*(indent+2) + "Done  querying DICOMweb server for DICOM Instances" +
                     " related to the DICOM Series in the DICOM Study" +
                     " in: " + str(timedelta(seconds=(stop_time_t99 - start_time_t99)))
        )

        # Get number of instances in the current series
        number_of_instances_in_current_series = len(instance_search_response_json)

        # Check if there is any instance defined in the current series
        if number_of_instances_in_current_series == 0:
            logger.warning(" "*(indent+2) + "No DICOM Instances found" +
                           f" in series number : '{data_store.series_instance_number}'" +
                           f" with DICOM SeriesInstanceUID: '{data_store.series_instance_uid}'" +
                           f" in study number : '{data_store.study_instance_number}'" +
                           f" with DICOM StudyInstanceUID: '{data_store.study_instance_uid}'"
            )
            data_store.increment_dicom_series_skipped_counter()
            return

        # -------------------------------------------------------------------------------------------------------------
        # For every DICOM Instance
        # -------------------------------------------------------------------------------------------------------------

        for current_instance_number, instance_search_response_item_json in enumerate(instance_search_response_json, start=1):
    
            logger.debug(" "*(indent+2) + f"Start processing DICOM Instance number: '{current_instance_number}'" + 
                        f" of '{number_of_instances_in_current_series}'" +
                        f" in series number : '{current_series_number}'" +
                        f" in study number : '{data_store.current_study_number}'" +
                        f" for patient with PatientID: '{data_store.patient_id}'"
            )
            start_time_t2 = time()

            # Reset any previous DICOM Instance level information in the data_store
            data_store.reset_imaging_instance_level()

            # Converting JSON to DICOM Dataset
            instance_search_response_item_ds = Dataset.from_json(instance_search_response_item_json)

            # Create an InstanceProcessor instance to process the DICOM Instance
            dw_instance_processor = DWInstanceProcessor()

            # Start processing the next level
            dw_instance_processor.process(instance_search_response_item_ds, current_instance_number, context, indent=indent+4)

            # ---------------------------------------------------------------------------------------------------------
            # ---------------------------------------------------------------------------------------------------------

            # ToDo: Edwin - 2026-08-14 - Add the SPHN ImagingFrame directly to the SPHN ImagingSeries in the data_store

            # ---------------------------------------------------------------------------------------------------------
            # Add the number of frames in the instance to the number of frames in the series 
            # ---------------------------------------------------------------------------------------------------------
            data_store.number_of_frames_in_series += data_store.number_of_frames_in_instance
            
            # ---------------------------------------------------------------------------------------------------------
            # Add the SPHN ImagingDevice to the SPHN ImagingSeries
            # ---------------------------------------------------------------------------------------------------------

            # Add the SPHN ImagingDevice to the SPHN ImagingSeries
            if data_store.sphn_imaging_series is not None:
                if data_store.sphn_imaging_series.has_medical_device is None:
                    if data_store.sphn_imaging_device is not None:
                        data_store.sphn_imaging_series.has_medical_device = data_store.sphn_imaging_device
                        logger.debug(" "*(indent+2) + "Added the SPHN ImagingDevice to the SPHN ImagingSeries")
                    else:
                        logger.debug(" "*(indent+2) + "SPHN ImagingDevice was not added to the SPHN ImagingSeries" + 
                                    " as the SPHN ImagingDevice was not created." +
                                    f" Series number: '{data_store.current_series_number}'" +
                                    f" in study number : '{data_store.current_study_number}'" +
                                    f" for patient with PatientID: '{data_store.patient_id}'"
                        )
                else:
                    logger.debug(" "*(indent+2) + "SPHN ImagingDevice was already added to the SPHN ImagingSeries")
            else:
                logger.debug(" "*(indent+2) + "SPHN ImagingDevice was not added to the SPHN ImagingSeries" + 
                            " as the SPHN ImagingSeries was not created." +
                            f" Series number: '{data_store.current_series_number}'" +
                            f" in study number : '{data_store.current_study_number}'" +
                            f" for patient with PatientID: '{data_store.patient_id}'"
                )

            # ---------------------------------------------------------------------------------------------------------

            # Reset any previous DICOM Instance level information in the data_store
            data_store.reset_imaging_instance_level()

            stop_time_t2 = time()
            logger.debug(" "*(indent+2) + f"Done  processing DICOM Instance number: '{current_instance_number}'" + 
                        f" of '{number_of_instances_in_current_series}'" +
                        f" in series number : '{current_series_number}'" +
                        f" in study number : '{data_store.current_study_number}'" +
                        f" for patient with PatientID: '{data_store.patient_id}'"
                         " in: " + str(timedelta(seconds=(stop_time_t2 - start_time_t2)))
            )
            logger.debug("")

            #break  # ToDo: Edwin - 2026-08-06 - Remove this break after testing the first DICOM Instance
        # -------------------------------------------------------------------------------------------------------------
        # Done processing all DICOM Instances in the current DICOM Series

        stop_time_t1 = time()
        logger.debug(" "*(indent+0) + "SeriesProcessor: Done processing..." +
                    " in: " + str(timedelta(seconds=(stop_time_t1 - start_time_t1)))
        )

        # Statistics
        data_store.increment_dicom_series_processed_counter()

        logger.debug("")        
        logger.debug(" "*(indent+0) + f"Processed {data_store.number_of_dicom_instances_processed} DICOM Instance(s)")
        logger.debug(" "*(indent+0) + f"Skipped {data_store.number_of_dicom_instances_skipped} DICOM Instance(s)")

        if data_store.sphn_imaging_series is not None and data_store.sphn_imaging_series.has_imaging_frame_list is not None:
            data_store.number_of_sphn_imaging_frames_stored = len(data_store.sphn_imaging_series.has_imaging_frame_list)
        else:
            data_store.number_of_sphn_imaging_frames_stored = 0
        
        data_store.total_number_of_sphn_imaging_frames_stored += data_store.number_of_sphn_imaging_frames_stored
        logger.debug(" "*(indent+0) + f"Added {data_store.number_of_sphn_imaging_frames_stored} SPHN ImagingFrame(s) to the SPHN ImagingSeries.")

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
    # Private functions - related to processing the DICOMweb API "Series Resource Search Response Payload"
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-07-20
    #
    def get_number_of_series_related_instances_from_dicomweb_response(self, dataset: Dataset, context: Context, indent: int=0) -> int|None:
        """
        Returns the value corresponding to the value of the DICOM NumberOfSeriesRelatedInstances tag
          - dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)

        Note: The DICOM NumberOfSeriesRelatedInstances tag is part of the DICOMweb API "Series Resource Search 
              Response Payload". It's type is '[R]equired'
              For more info see: 
              https://dicom.nema.org/medical/dicom/current/output/html/part18.html#table_10.6.3-4
        """
        
        # Tag:                  (0020,1209)
        # Keyword:              NumberOfSeriesRelatedInstances
        # Value Representation: Integer String (IS)
        # Type:	                Required, Empty if Unknown (2)
        # Value Multiplicity:   1

        # Check
        assert isinstance(dataset, Dataset)
        assert isinstance(context, Context)
        assert isinstance(indent,int) and indent>=0

        logger = context.logger

        if "NumberOfSeriesRelatedInstances" not in dataset:
            logger.warning(" "*(indent+0) + "DICOM NumberOfSeriesRelatedInstances tag was not found")  
            return None

        # Get the DataElement
        data_element = dataset["NumberOfSeriesRelatedInstances"]

        # Get the value
        value = data_element.value
        
        # Get the Value Multiplicity
        value_multiplicity = data_element.VM
        
        # Check if it is empty
        if value_multiplicity == 0 or value is None:
            logger.debug(" "*(indent+0) + "DICOM NumberOfSeriesRelatedInstances tag value was not provided")
            return None
        
        # It should be a single-valued tag, an integer
        if value_multiplicity != 1 or not isinstance(value, pydicom.valuerep.IS):
            logger.warning(" "*(indent+0) + "DICOM NumberOfSeriesRelatedInstances tag has an unknown format")
            return None

        # Try to convert IS to int
        try:
            number_of_series_related_instances = int(value)
        except (TypeError, ValueError):
            logger.warning(" "*(indent+0) + "DICOM NumberOfSeriesRelatedInstances value could not be converted to an int value.")
            return None

        if number_of_series_related_instances < 0:
            logger.warning(" "*(indent+0) + f"DICOM NumberOfSeriesRelatedInstances tag value: '{number_of_series_related_instances}' is likely not a valid value")

        return number_of_series_related_instances
    

    #
    # Edwin 2026-07-20
    #
    def get_series_instance_uid_from_dicomweb_response(self, dataset: Dataset, context: Context, indent: int=0) -> str|None:
        """
        Returns the value corresponding to the value of the DICOM SeriesInstanceUID tag
          - dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)

        Note: The DICOM SeriesInstanceUID tag is part of the DICOMweb API "Series Resource Search 
              Response Payload". It's type is '[R]equired'
              For more info see: 
              https://dicom.nema.org/medical/dicom/current/output/html/part18.html#table_10.6.3-4
        """

        # Keyword:              SeriesInstanceUID
        # Value Representation: Unique Identifier (UI)
        # Type:	                Required (1)
        # Value Multiplicity:   1

        # Check
        assert isinstance(dataset, Dataset)
        assert isinstance(context, Context)
        assert isinstance(indent, int) and indent>=0

        logger = context.logger

        if "SeriesInstanceUID" not in dataset:
            logger.warning(" "*(indent+0) + "DICOM SeriesInstanceUID tag was not found")
            return None

        # Get the DataElement
        data_element = dataset["SeriesInstanceUID"]

        # Get the value
        value = data_element.value
            
        # Get the Value Multiplicity
        value_multiplicity = data_element.VM
            
        # Check if it is empty
        if value_multiplicity == 0 or value is None:
            logger.warning(" "*(indent+0) + "DICOM SeriesInstanceUID tag value was not provided")
            return None

        # It should be a single-valued tag, a string            
        if value_multiplicity != 1 or not isinstance(value, str):
            logger.warning(" "*(indent+0) + "DICOM SeriesInstanceUID tag has an unknown format")
            return None
            
        # Remove whitespace
        series_instance_uid_str = value.strip()

        # Check if value is not empty
        if len(series_instance_uid_str) == 0:
            logger.warning(" "*(indent+0) + "DICOM SeriesInstanceUID tag contains only whitespace")
            return None

        return series_instance_uid_str

    #
    # Edwin 2026-07-20
    #
    def get_modality_from_dicomweb_response(self, dataset: Dataset, context: Context, indent: int=0) -> tuple[str, str, str]|None:
        """
        Returns the DCM code corresponding to the value of the DICOM Modality tag
        Parameters:
            - dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)
            - context: The Context object that holds the data_store, logger and other relevant information
            - indent: The indentation level for logging (default is 0)

        Note: The DICOM Modality tag is part of the DICOMweb API "Series Resource Search 
              Response Payload". It's type is '[R]equired'
              For more info see: 
              https://dicom.nema.org/medical/dicom/current/output/html/part18.html#table_10.6.3-4
        """

        # Keyword:              Modality
        # Value Representation: Code String (CS)
        # Type:	                Required (1)
        # Value Multiplicity:   1

        # Note:
        #   Available in CR, DX, CT, MR, PT, enhanced CT, enhanced MR, enhanced PT

        # Check
        assert isinstance(dataset, Dataset)
        assert isinstance(context, Context)
        assert isinstance(indent, int) and indent>=0

        logger = context.logger

        if "Modality" not in dataset:
            logger.warning(" "*(indent+0) + "DICOM Modality tag was not found")  
            return None

        # Get the DataElement
        data_element = dataset["Modality"]

        # Get the value
        value = data_element.value
        
        # Get the Value Multiplicity
        value_multiplicity = data_element.VM
        
        # Check if it is empty
        if value_multiplicity == 0 or value is None:
            logger.warning(" "*(indent+0) + "DICOM Modality tag value was not provided")
            return None

        # It should be a single-valued tag, a string
        if value_multiplicity != 1 or not isinstance(value, str):
            logger.warning(" "*(indent+0) + "DICOM Modality tag has an unknown format")
            return None
        
        # Remove whitespace
        modality_code_str = value.strip()

        # Check if value is not empty
        if len(modality_code_str) == 0:
            logger.warning(" "*(indent+0) + "DICOM Modality tag contains only whitespace")
            return None
        
        # Convert the value to a corresponding DCM code
        result = DataConverter.dicom_modality_code_dict.get(modality_code_str.upper(), None)

        # Check if it is a know DICOM modality code
        if result is None:
            logger.warning(" "*(indent+0) + f"DICOM Modality tag value: '{modality_code_str}' is unknown")
            return None

        assert isinstance(result, tuple) and len(result) == 2
        assert isinstance(result[0], tuple) and len(result[0]) == 3
        assert isinstance(result[0][0], str)
        assert isinstance(result[0][1], str)
        assert isinstance(result[0][2], str)

        dcm_coding_scheme_designator = result[0][0]
        dcm_code_value = result[0][1]
        dcm_code_descr = result[0][2]

        # Check if the corresponding DCM code and description exists
        if dcm_coding_scheme_designator == "" or dcm_code_value == "" or dcm_code_descr == "":
            logger.warning(" "*(indent+0) + f"DICOM Modality tag value: '{modality_code_str}' could not be converted to a DCM code")
            return None

        # Check conversion is ok
        assert is_valid_string(dcm_coding_scheme_designator)
        assert is_valid_string(dcm_code_value)
        assert is_valid_string(dcm_code_descr)

        return (dcm_coding_scheme_designator, dcm_code_value, dcm_code_descr)