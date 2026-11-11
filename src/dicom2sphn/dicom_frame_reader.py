"""
dicom_instance_reader.py: 
    Part of the example dicom2sphn package.
    It contains functions for reading DICOM Instance metadata for the SPHN ImagingFrame concept.
"""

import itertools

import numpy as np
import pydicom
from pydicom import Dataset
from pydicom.sequence import Sequence

from .context import Context
from .data_converter import DataConverter
from .dicom_contrast_bolus_module_reader import process_dicom_contrast_information
from .sphn_concepts.sphn_body_site import SPHNBodySite
from .sphn_concepts.sphn_code import SPHNCode
from .sphn_concepts.sphn_data_compression_algorithm import SPHNDataCompressionAlgorithm
from .sphn_concepts.sphn_image_dimensions import SPHNImageDimensions
from .sphn_concepts.sphn_pixel_dimensions import SPHNPixelDimensions
from .sphn_concepts.sphn_quantity import SPHNQuantity
from .sphn_concepts.sphn_unit import SPHNUnit
from .tools import (
    combine_dicom_date_and_time,
    complete_dicom_datetime,
    get_dicom_timezone,
    is_clean_string,
    is_valid_string,
)

type SPHN_ImagingFrame_type_ValueSet_Member = str
type SPHN_ImageFrame_content_qualification_ValueSet_Member = str
type UnitCode = tuple[str,str,str]  # (coding_scheme_designator, code_value, code_meaning)

type UnitUCUMCode = str  # UCUM unit code as a string
type PixelSizeRow = tuple[float, UnitCode]  # (value, unit_ucum_code)
type PixelSizeColumn = tuple[float, UnitCode]  # (value, unit_ucum_code)
type PixelSize = tuple[PixelSizeRow, PixelSizeColumn]  # ((row_value, row_unit_code), (column_value, column_unit_code))

type NumOfRows = tuple[float, UnitUCUMCode]  # (value, unit_ucum_code)
type NumOfColumns = tuple[float, UnitUCUMCode]  # (value, unit_ucum_code)
type SliceSpacing = tuple[float, UnitUCUMCode]  # (value, unit_ucum_code)
type SliceThickness = tuple[float, UnitUCUMCode]  # (value, unit_ucum_code)
type NumOfSamples =  tuple[int, UnitUCUMCode]  # (value, unit_ucum_code)
type SnomedCTCode = str  # SNOMED-CT code as a string
type ImagePosition = tuple[tuple[float, float, float], str]  # ((x, y, z), unit)
type ImageOrientation = tuple[tuple[float, float, float], tuple[float, float, float]]  # ((row_x, row_y, row_z), (column_x, column_y, column_z))

type CodeValue = str  # Code value as a string
type CodingSchemeDesignator = str  # Code scheme designator as a string
type CodingSchemeVersion = str  # Coding scheme version as a string
type CodeMeaning = str  # Code meaning as a string
type LongCodeValue = str  # Long code value as a string
type URNCodeValue = str  # URN code value as a string

#
# Edwin 2026-08-09
# 
def get_frame_metadata_from_dicom(dataset: Dataset, frame_number: int, context: Context, indent: int=0) -> None:
    """
    Get the metadata related to SPHN ImagingFrame from the dataset
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - frame_number: The frame number (1-based index) for single- and multi-frame DICOM instances
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Checks
    assert isinstance(dataset, Dataset)
    assert isinstance(frame_number, int) and frame_number>0
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent>=0

    logger = context.logger
    data_store = context.data_store
    sphn_schema = data_store.sphn_schema

    # -------------------------------------------------------------------------------------------------------------

    #
    # Timezone
    #

    # DICOM dates and times are local times: get the timezone (TimezoneOffsetFromUTC or the configured local timezone)
    assert context.local_timezone is not None
    dicom_timezone = get_dicom_timezone(dataset, context.local_timezone, logger, indent=indent+2)

    #
    # AcquisitionDateTime
    #

    if data_store.acquisition_start_datetime is None:

        acquisition_datetime_str = get_acquisition_datetime_from_dicom(dataset, context, indent=indent+2)
        
        if acquisition_datetime_str is not None:

            assert isinstance(acquisition_datetime_str, str)

            logger.debug(" "*(indent+0) + f"AcquisitionDateTime string from DICOM: '{acquisition_datetime_str}'")

            # Convert the AcquisitionDateTime string into a complete DICOM datetime (DT) object
            # - acquisition datetime is completed by filling in missing components for Month, Day, Hour, Minute, Second
            acquisition_datetime_obj = complete_dicom_datetime(acquisition_datetime_str, dicom_timezone, logger=logger, indent=indent+2)

            if acquisition_datetime_obj is not None:
                # Set the acquisition start datetime in the data store
                data_store.acquisition_start_datetime = acquisition_datetime_obj

                logger.debug(" "*(indent+2) + f"AcquisitionDateTime: '{acquisition_datetime_obj!s}'")
            else:
                logger.debug(" "*(indent+2) + "AcquisitionDateTime could not be created")
        else:
            logger.debug(" "*(indent+0) + "AcquisitionDateTime not found")

    # 
    # AcquisitionDate and AcquisitionTime
    #
    
    if data_store.acquisition_start_datetime is None:

        # Date
        acquisition_date = get_acquisition_date_from_dicom(dataset, context, indent=indent+2)
        
        if acquisition_date is not None:
            assert isinstance(acquisition_date, str)
            logger.debug(" "*(indent+0) + f"AcquisitionDate string from DICOM: '{acquisition_date}'")
        else:
            logger.debug(" "*(indent+0) + "AcquisitionDate not found")

        # Time
        acquisition_time = get_acquisition_time_from_dicom(dataset, context, indent=indent+2)
        
        if acquisition_time is not None:
            assert isinstance(acquisition_time, str)
            logger.debug(" "*(indent+0) + f"AcquisitionTime string from DICOM: '{acquisition_time}'")
        else:
            logger.debug(" "*(indent+0) + "AcquisitionTime not found")

        # Combine AcquisitionDate and AcquisitionTime
        acquisition_start_datetime_obj = None
        if acquisition_date and acquisition_time:

            # Combine the AcquisitionDate and AcquisitionTime strings into a single complete DICOM datetime (DT) object
            # - acquisition datetime is completed by filling in missing components for Month, Day, Hour, Minute, Second
            acquisition_start_datetime_obj = combine_dicom_date_and_time(acquisition_date, acquisition_time, dicom_timezone, logger, indent=indent+2)
        
        elif acquisition_date and not acquisition_time:

            # Combine the AcquisitionDate and a missing or empty AcquisitionTime strings into a single complete DICOM datetime (DT) object
            # - acquisition datetime is completed by filling in missing components for Month, Day, Hour, Minute, Second
            acquisition_start_datetime_obj = combine_dicom_date_and_time(acquisition_date, "", dicom_timezone, logger, indent=indent+2)
        else:
            logger.debug(" "*(indent+0) + "Could not combine AcquisitionDate and AcquisitionTime: Acquisition Date not defined")
        
        if acquisition_start_datetime_obj is not None:
            # Set the acquisition start datetime in the data store
            data_store.acquisition_start_datetime = acquisition_start_datetime_obj

            logger.debug(" "*(indent+0) + f"Combined Acquisition Date and Time: '{acquisition_start_datetime_obj!s}'")
        else:
            logger.debug(" "*(indent+0) + "Could not combine AcquisitionDate and AcquisitionTime")

    # -------------------------------------------------------------------------------------------------------------

    # 
    # FrameAcquisitionDateTime
    #

    # ToDo by Edwin:

    # frame_acquisition_datetime_str = self.get_frame_acquisition_datetime_from_dicom_instance(file_dataset, indent=indent)

    # if frame_acquisition_datetime_str is not None:
    #     # Log
    #     logger.debug(" "*(indent+0) + f"FrameAcquisitionDateTime: '{frame_acquisition_datetime_str}'")
    #     logger.debug("")
    # else:
    #     # Log
    #     logger.debug(" "*(indent+0) + f"FrameAcquisitionDateTime not defined")
    #     logger.debug("")

    # -------------------------------------------------------------------------------------------------------------

    # 
    # FrameType
    #

    # ToDo by Edwin:

    # frame_type_list = self.get_frame_type_from_dicom_instance(file_dataset, indent=indent)

    # if frame_type_list is not None:
    #     # Log
    #     logger.debug(" "*(indent+0) + f"FrameType valueset value: '{frame_type_list}'")
    #     logger.debug("")
    # else:
    #     # Log
    #     logger.debug(" "*(indent+0) + f"FrameType not defined")
    #     logger.debug("")

    # 
    # ImageType
    #

    type_list = get_image_type_list_from_dicom(dataset, context, indent=indent+2)

    if type_list is not None:

        assert len(type_list) > 0
        
        logger.debug(" "*(indent+0) + f"Found SPHN ImageFrame_type ValueSet Member list: '{type_list}'")

        if data_store.sphn_imagingframe_type_valueset_member_list is None:
            data_store.sphn_imagingframe_type_valueset_member_list = type_list
            n = len(type_list)
        else:
            n = 0
            for type_item in type_list:
                if type_item not in data_store.sphn_imagingframe_type_valueset_member_list:
                    data_store.sphn_imagingframe_type_valueset_member_list.append(type_item)
                    n += 1
        logger.debug(" "*(indent+0) + f"Added {n} ImageType ValueSet member(s) to the data_store.")


    # -------------------------------------------------------------------------------------------------------------

    # 
    # PixelSpacing
    #

    # sphn_pixel_dimensions will be used later to create the SPHN ImageDimensions instance
    sphn_pixel_dimensions = None

    if data_store.sphn_pixel_dimensions is None:

        pixel_size = get_pixel_spacing_from_dicom(dataset, context, indent=indent+2)
        
        if pixel_size is not None:

            assert isinstance(pixel_size, tuple) \
                and len(pixel_size) == 2 \
                and isinstance(pixel_size[0], float) \
                and isinstance(pixel_size[1], float)

            logger.debug(" "*(indent+0) + f"PixelSpacing row: '{pixel_size[0]}' mm")
            logger.debug(" "*(indent+0) + f"PixelSpacing column: '{pixel_size[1]}' mm")

            sphn_pixel_dimensions = create_sphn_pixel_dimensions(pixel_size, context, indent=indent+2)

            # Store the SPHN PixelDimensions in the data_store
            data_store.sphn_pixel_dimensions = sphn_pixel_dimensions

            logger.debug(" "*(indent+0) + "SPHN PixelDimensions created and added to the data_store")

    # -------------------------------------------------------------------------------------------------------------
    

    # Will be used later to create the SPHN ImageDimensions instance
    sphn_quantity_rows = None
    sphn_quantity_columns = None
    sphn_quantity_slice_spacing = None
    sphn_quantity_slice_thickness = None
    sphn_quantity_samples_per_pixel = None

    if data_store.sphn_image_dimensions is None:

        # 
        # Rows
        #

        num_of_rows = get_rows_from_dicom(dataset, context, indent=indent+2) 

        if num_of_rows is not None:

            assert isinstance(num_of_rows, int)

            logger.debug(" "*(indent+0) + f"Number of rows: '{num_of_rows}'")

            sphn_quantity_rows = create_sphn_quantity_for_number_of_items(num_of_rows, context, indent=indent+2)

            logger.debug(" "*(indent+0) + "SPHN Quantity for number of rows created")

        # 
        # Columns
        #

        num_of_columns = get_columns_from_dicom(dataset, context, indent=indent+2) 

        if num_of_columns is not None:

            assert isinstance(num_of_columns, int)

            logger.debug(" "*(indent+0) + f"Number of columns: '{num_of_columns}'")

            sphn_quantity_columns = create_sphn_quantity_for_number_of_items(num_of_columns, context, indent=indent+2)

            logger.debug(" "*(indent+0) + "SPHN Quantity for number of columns created")

    
        # 
        # SpacingBetweenSlices
        #

        slice_spacing = get_spacing_between_slices_from_dicom(dataset, context, indent=indent+2)

        if slice_spacing is not None:

            logger.debug(" "*(indent+0) + f"Spacing between center of slices: '{slice_spacing}'")

            sphn_quantity_slice_spacing = create_sphn_quantity_for_distance_in_mm(slice_spacing, context, indent=indent+2)

            logger.debug(" "*(indent+0) + "SPHN Quantity for spacing between center of slices created")

        # 
        # SliceThickness
        #

        thickness = get_slice_thickness_from_dicom(dataset, context, indent=indent+2)

        if thickness is not None:
            
            logger.debug(" "*(indent+0) + f"Slice thickness: '{thickness}'")

            sphn_quantity_slice_thickness = create_sphn_quantity_for_distance_in_mm(thickness, context, indent=indent+2)

            logger.debug(" "*(indent+0) + "SPHN Quantity for slice thickness created")

        # 
        # SamplesPerPixel
        #

        samples_per_pixel = get_samples_per_pixel_from_dicom(dataset, context,indent=indent+2)

        if samples_per_pixel is not None:

            logger.debug(" "*(indent+0) + f"Samples per pixel: '{samples_per_pixel}'")

            sphn_quantity_samples_per_pixel = create_sphn_quantity_for_number_of_items(samples_per_pixel, context, indent=indent+2)

            logger.debug(" "*(indent+0) + "SPHN Quantity for samples per pixel created")

        # 
        # SPHN ImageDimensions 
        #

        if sphn_pixel_dimensions is not None \
            or sphn_quantity_rows is not None \
            or sphn_quantity_columns is not None \
            or sphn_quantity_slice_spacing is not None \
            or sphn_quantity_slice_thickness is not None:
            # ToDo: Edwin, or sphn_quantity_samples_per_pixel is not None: (not an SPHN property yet)
            
            sphn_image_dimensions = SPHNImageDimensions(
                sphn_schema=sphn_schema,
                has_number_of_rows=sphn_quantity_rows,
                has_number_of_columns=sphn_quantity_columns,
                has_number_of_slices=None,
                has_slice_spacing=sphn_quantity_slice_spacing,
                has_slice_thickness=sphn_quantity_slice_thickness,
                has_pixel_dimensions=sphn_pixel_dimensions,
                has_number_of_samples_per_pixel=sphn_quantity_samples_per_pixel
            )

            data_store.sphn_image_dimensions = sphn_image_dimensions
            logger.debug(" "*(indent+0) + "SPHN ImageDimensions created and added to the data_store")

        else:
            logger.debug(" "*(indent+0) + "No SPHN ImageDimensions metadata found")

    # -------------------------------------------------------------------------------------------------------------

    # 
    # BodyPartExamined
    # 
    
    body_part_examined_term = get_body_part_examined_from_dicom(dataset, context, indent=indent+2)

    if body_part_examined_term is not None:
        logger.debug(" "*(indent+0) + f"BodyPartExamined term: '{body_part_examined_term}'")

        sphn_body_site = create_sphn_body_site_for_body_part_examined_term(body_part_examined_term, context, indent=indent+2)

        if sphn_body_site is None:
            logger.debug(" "*(indent+0) + "SPHN BodySite could not be created for the given BodyPartExamined term")
        else:
            logger.debug(" "*(indent+0) + "SPHN BodySite created for the given BodyPartExamined term")
            data_store.add_sphn_body_site_to_list(sphn_body_site, logger, indent=indent+2)
            
    
    #
    # Anatomic Region Sequence
    #

    # ToDo by Edwin:
    #  - Not implemented yet
    #  - Adds to the self.body_site_list

    #
    # Primary Anatomic Structure Sequence
    #

    # ToDo by Edwin:
    #  - Not implemented yet
    #  - Adds to the self.body_site_list

    # -------------------------------------------------------------------------------------------------------------

    # 
    # LossyImageCompression
    #

    has_lossy_compression = get_lossy_image_compression_from_dicom(dataset, context, indent=indent+2) 

    if has_lossy_compression is not None:
        logger.debug(" "*(indent+0) + f"LossyImageCompression: '{has_lossy_compression}'")
    else:
        logger.debug(" "*(indent+0) + "LossyImageCompression not found")

    # 
    # LossyImageCompressionMethod
    #

    lossy_compression_method_list = get_lossy_image_compression_method_list_from_dicom(dataset, context, indent=indent+2) 

    if lossy_compression_method_list is not None:
        logger.debug(" "*(indent+0) + f"LossyImageCompressionMethod list: '{lossy_compression_method_list}'")
    else:
        logger.debug(" "*(indent+0) + "LossyImageCompressionMethod not found")

    # 
    # LossyImageCompressionRatio
    #

    lossy_compression_ratio_list = get_lossy_image_compression_ratio_list_from_dicom(dataset, context, indent=indent+2) 

    if lossy_compression_ratio_list is not None:
        logger.debug(" "*(indent+0) + f"LossyImageCompressionRatio list: '{lossy_compression_ratio_list}'")
    else:
        logger.debug(" "*(indent+0) + "LossyImageCompressionRatio not found")

    # 
    # Convert LossyImageCompression data to a list of SPHN DataCompressionAlgorithm
    #

    image_compression_algorithm_list = convert_to_data_compression_algorithm_list(has_lossy_compression, lossy_compression_method_list, lossy_compression_ratio_list, context, indent=indent+2)

    if image_compression_algorithm_list is not None:

        assert len(image_compression_algorithm_list) > 0

        if data_store.sphn_data_compression_algorithm_list is None:
            data_store.sphn_data_compression_algorithm_list = image_compression_algorithm_list
            n = len(image_compression_algorithm_list)
        else:
            n = 0
            for image_compression_algorithm in image_compression_algorithm_list:
                # Add if not similar to a previous SPHN ImagingFrame in the list (to avoid duplicates)
                if image_compression_algorithm not in data_store.sphn_data_compression_algorithm_list:
                    data_store.sphn_data_compression_algorithm_list.append(image_compression_algorithm)
                    n += 1
                else:
                    logger.debug(" "*(indent+2) + "SPHN DataCompressionAlgorithm is already in the list")

        logger.debug(" "*(indent+0) + f"Added {n} SPHN DataCompressionAlgorithm instances to the data_store.")
    else:
        logger.debug(" "*(indent+0) + "No SPHN DataCompressionAlgorithm metadatafound.")


    # -------------------------------------------------------------------------------------------------------------

    # 
    # ContentQualification
    #

    if data_store.sphn_imagingframe_content_qualification_valueset_member is None:

        content_qualification = get_content_qualification_from_dicom(dataset, context, indent=indent+2)

        if content_qualification is not None:
            logger.debug(" "*(indent+0) + f"SPHN ImagingFrame ContentQualification ValueSet member: '{content_qualification}'")
            data_store.sphn_imagingframe_content_qualification_valueset_member = content_qualification
        else:
            logger.debug(" "*(indent+0) + "No SPHN ImagingFrame ContentQualification metadata found")


    # -------------------------------------------------------------------------------------------------------------

    #
    # SPHN PhysicalQuantity
    #

    # Not implemented

    # -------------------------------------------------------------------------------------------------------------

    #
    # SPHN Anatomical Projection
    #

    # Not implemented

    # -------------------------------------------------------------------------------------------------------------

    # 
    # Image Position (Patient)
    #

    # Note:
    #   Not available in CR, DX
    #   Available in CT, MR, PT, enhanced CT, enhanced MR, enhanced PT

    image_position = get_image_position_from_dicom(dataset, context, indent=indent+2) 

    if image_position is not None:

        # Create a NumPy array
        image_position_np = np.array([image_position[0][0], image_position[0][1], image_position[0][2]])

        # The image_position_np will be used later to calculate the slice location

        logger.debug(" "*(indent+0) + f"ImagePositionPatient vector: '[{image_position[0][0]}, {image_position[0][1]}, {image_position[0][2]}]', Unit UCUM code: '{image_position[1]}'")
    else:
        logger.debug(" "*(indent+0) + "ImagePositionPatient not found")

    # 
    # Image Orientation (Patient)
    #

    # Note:
    #   Not available in CR, DX
    #   Available in CT, MR, PT, enhanced CT, enhanced MR, enhanced PT

    image_orientation = get_image_orientation_from_dicom(dataset, context, indent=indent+2) 

    if image_orientation is not None:
    
        # Create NumPy arrays
        image_orientation_row_np = np.array([image_orientation[0][0], image_orientation[0][1], image_orientation[0][2]])
        image_orientation_column_np = np.array([image_orientation[1][0], image_orientation[1][1], image_orientation[1][2]])

        # The image_orientation_row_np and image_orientation_column_np will be used later to calculate the slice location

        logger.debug(" "*(indent+0) + f"ImageOrientationPatient row vector:    '[{image_orientation[0][0]}, {image_orientation[0][1]}, {image_orientation[0][2]}]'")
        logger.debug(" "*(indent+0) + f"ImageOrientationPatient column vector: '[{image_orientation[1][0]}, {image_orientation[1][1]}, {image_orientation[1][2]}]'")
    else:
        logger.debug(" "*(indent+0) + "ImageOrientationPatient not defined")

    # 
    # Calculate the Normal and slice location to be able to sort the image slices in a 3D image volume
    #

    # Set initial value
    image_orientation_normal_np = None
    slice_location = None

    if image_position is not None and image_orientation is not None:
        
        # Check
        assert isinstance(image_position_np, np.ndarray)
        assert isinstance(image_orientation_row_np, np.ndarray)
        assert isinstance(image_orientation_column_np, np.ndarray)

        # Caluculate the normal to the imaging plane
        image_orientation_normal_np = np.cross(image_orientation_row_np, image_orientation_column_np)

        # Calculate the projection. The projection gives the ‘distance’ of each slice along the normal imaging axis. Also known as the slice location
        slice_location = np.dot(image_position_np, image_orientation_normal_np)

        logger.debug(" "*(indent+0) + f"SliceLocation (calculated): '{slice_location}'")

    else:
        logger.debug(" "*(indent+0) + "SliceLocation could not be calculated")

    # -------------------------------------------------------------------------------------------------------------

    #
    # Real World Value Mapping Sequence
    #

    # result = get_real_world_value_mapping_sequence_from_dicom(dataset, context, indent=indent)

    # -------------------------------------------------------------------------------------------------------------

    #
    # Contrast/Bolus
    #
    
    logger.debug(" "*(indent+0) + "Start processing Contrast/Bolus information from DICOM dataset")

    process_dicom_contrast_information(dataset, context, indent=indent+2)

    if data_store.sphn_contrast_agent_administration_event_list is not None:
        logger.debug(" "*(indent+0) + f"SPHN Contrast Agent Administration Event list in the data_store contains {len(data_store.sphn_contrast_agent_administration_event_list)} event(s)")
    else:
        logger.debug(" "*(indent+0) + "No SPHN Contrast Agent Administration Event metadata found")


# -----------------------------------------------------------------------------------------------------------------
# Create SPHN objects from DICOM data
# -----------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-11-11
#
def create_sphn_pixel_dimensions(dicom_pixel_spacing: tuple[float,float], context: Context, indent: int=0) -> SPHNPixelDimensions:
    """
    Creates SPHN Pixel Dimensions object
    Parameters:
        - dicom_pixel_spacing: The DICOM PixelSpacing values as a tuple of two floats [row_spacing, column_spacing]
        - context: The Context object that contains the logger and other relevant information
        - indent: The indentation level for logging messages (default is 0)
    """
    assert isinstance(dicom_pixel_spacing, tuple)
    assert len(dicom_pixel_spacing) == 2 \
        and isinstance(dicom_pixel_spacing[0], float) \
        and isinstance(dicom_pixel_spacing[1], float)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    sphn_schema = context.sphn_schema

    # Set unit using UCUM annotation for row and column spacing
    row_unit_code = ("UCUM", "mm", "millimeter")    # The DICOM unit for PixelSpacing is always "mm"
    column_unit_code = ("UCUM", "mm", "millimeter") # The DICOM unit for PixelSpacing is always "mm"

    sphn_code_row = SPHNCode(
        sphn_schema=sphn_schema,
        has_coding_system_and_version=row_unit_code[0],
        has_identifier=row_unit_code[1],
        has_name=row_unit_code[2]
        )
    sphn_code_col = SPHNCode(
        sphn_schema = sphn_schema,
        has_coding_system_and_version = column_unit_code[0],
        has_identifier = column_unit_code[1],
        has_name = column_unit_code[2]
        )
    sphn_unit_row = SPHNUnit(
        sphn_schema = sphn_schema,
        has_code = sphn_code_row
        )
    sphn_unit_col = SPHNUnit(
        sphn_schema = sphn_schema,
        has_code = sphn_code_col
        )
    sphn_quantity_row = SPHNQuantity(
        sphn_schema = sphn_schema,
        has_value = dicom_pixel_spacing[0],
        has_unit = sphn_unit_row
        )
    sphn_quantity_col = SPHNQuantity(
        sphn_schema = sphn_schema,
        has_value = dicom_pixel_spacing[1],
        has_unit = sphn_unit_col
        )
    sphn_pixel_dimensions = SPHNPixelDimensions(
        sphn_schema = sphn_schema,
        has_row_spacing = sphn_quantity_row,
        has_column_spacing = sphn_quantity_col
        )

    return sphn_pixel_dimensions


#
# Edwin 2026-10-22
#
def create_sphn_quantity_for_number_of_items(number_of_items: int, context: Context, indent: int=0) -> SPHNQuantity:
    """
    Creates SPHN Quantity object for the number of items
    Parameters:
        - number_of_items: The number of items as an integer
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """
    assert isinstance(number_of_items, int)
    assert number_of_items >= 0
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    sphn_schema = context.sphn_schema

    # Set unit using UCUM annotation
    unit_code = ("UCUM", "cblnbcbr", "{#}") # SPHN UCUM unit code, label: "{#}", comment: "number"

    sphn_code = SPHNCode( 
        sphn_schema = sphn_schema,
        has_coding_system_and_version = unit_code[0],
        has_identifier = unit_code[1],
        has_name = unit_code[2]
        )
    sphn_unit = SPHNUnit(
        sphn_schema = sphn_schema,
        has_code = sphn_code
        )
    sphn_quantity = SPHNQuantity(
        sphn_schema = sphn_schema,
        has_value = number_of_items,
        has_unit = sphn_unit
        )

    return sphn_quantity

#
# Edwin 2026-10-22
#
def create_sphn_quantity_for_distance_in_mm(distance: float, context: Context, indent: int=0) -> SPHNQuantity:
    """
    Creates SPHN Quantity object for the distance in millimeters
    Parameters:
        - distance: The distance in millimeters as a float
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """
    assert isinstance(distance, (int, float))
    assert distance >= 0
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    sphn_schema = context.sphn_schema

    # Set unit using UCUM annotation
    unit_code = ("UCUM", "mm", "mm") # SPHN UCUM unit code, label: "mm", comment: "millimeters"

    sphn_code = SPHNCode( 
        sphn_schema = sphn_schema,
        has_coding_system_and_version = unit_code[0],
        has_identifier = unit_code[1],
        has_name = unit_code[2]
        )
    sphn_unit = SPHNUnit(
        sphn_schema = sphn_schema,
        has_code = sphn_code
        )
    sphn_quantity = SPHNQuantity(
        sphn_schema = sphn_schema,
        has_value = distance,
        has_unit = sphn_unit
        )

    return sphn_quantity


#
#  Edwin 2026-10-22
#
def create_sphn_body_site_for_body_part_examined_term(body_part_examined_term: str, context: Context, indent: int=0) -> SPHNBodySite|None:
    """
    Returns an SPHN BodySite object with the corresponding SNOMED-CT code for the given BodyPartExamined term
    Parameters:
        - body_part_examined_term: The term obtained from the DICOM BodyPartExamined tag
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    assert is_valid_string(body_part_examined_term)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    sphn_schema = context.sphn_schema
    logger = context.logger

    # Check if it is in the dictionary and convert to a corresponding SNOMED-CT code
    result = DataConverter.dicom_body_part_examined_terms_dict.get(body_part_examined_term.upper(), None)

    if result is None:
        logger.warning(" "*(indent+0) + f"DICOM BodyPartExamined Term: '{body_part_examined_term}' could not be converted to a corresponding code")
        return None

    # Check if conversion is ok
    assert isinstance(result, tuple) and len(result) == 3
    assert all(is_valid_string(item) for item in result)
    # ToDo: Check if it is a valid SNOMED-CT code

    coding_scheme_designator = result[0]
    code_value = result[1]
    code_descr = result[2]

    sphn_code = SPHNCode(
        sphn_schema=sphn_schema,
        has_coding_system_and_version=coding_scheme_designator,
        has_identifier=code_value,
        has_name=code_descr
    )

    # Laterality is not implemented

    sphn_body_site = SPHNBodySite(
        sphn_schema=sphn_schema,
        has_code=sphn_code,
        has_laterality=None
        )

    return sphn_body_site


# -----------------------------------------------------------------------------------------------------------------
# DICOM tag reading functions for SPHN ImagingFrame metadata
# -----------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-07-30
#
def get_image_type_list_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> list[SPHN_ImagingFrame_type_ValueSet_Member]|None:
    """
    Returns a list with SPHN ImagingFrame_type ValueSet members corresponding to the values of the DICOM ImageType tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context is the Context object that contains the logger and other relevant information
        - indent is the indentation level for logging messages
    """

    # Keyword:              ImageType
    # Value Representation: Code String (CS)
    # Type:	                Optional (3)
    # Value Multiplicity:   2-n

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger
    data_store = context.data_store
    sphn_schema = context.sphn_schema

    # Set initial value
    type_value_set_member_list = []

    if "ImageType" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM ImageType tag was not found")  
        return None

    # Get the DataElement
    data_element = dataset["ImageType"]

    # Get the value
    value = data_element.value
    
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
    
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM ImageType tag value was not provided")
        return None
    
    # It should be a multi-valued tag
    if value_multiplicity < 2 or not isinstance(value, pydicom.multival.MultiValue):
        logger.warning(" "*(indent+0) + "DICOM ImageType tag has an unknown format")
        return None
    
    # For each value in the multi-value list
    for value_item in value:

        if not isinstance(value_item, str):
            logger.warning(" "*(indent+0) + "DICOM ImageType tag value-item has an unknown format")
            continue

        # Remove whitespace
        image_type_item = value_item.strip()

        # Check if not empty
        if len(image_type_item) == 0:
            logger.debug(" "*(indent+0) + "DICOM ImageType tag value-item contains only whitespace")
            continue

        # Convert to SPHN ImagingFrame_type ValueSet member (using lower case key)
        type_value_set_member = DataConverter.dicom_image_and_frame_type_dict_lower_case_key.get(image_type_item.lower(), None)

        if type_value_set_member is None:
            logger.debug(" "*(indent+0) + f"DICOM ImageType tag value-item: '{image_type_item}' could not be converted to a corresponding SPHN ImagingFrame_type ValueSet member.")
            data_store.add_skipped_frame_type_to_dict(image_type_item)
            continue

        # Check if it is a valid SPHN ImagingFrame_type ValueSet member
        assert is_clean_string(type_value_set_member)
        assert sphn_schema.is_sphn_imaging_frame_type_value_set_member(type_value_set_member)

        # Add to the list
        if type_value_set_member not in type_value_set_member_list:
            type_value_set_member_list.append(type_value_set_member)

    return type_value_set_member_list if len(type_value_set_member_list)>0 else None



#
# Edwin 2026-11-11
#
def get_pixel_spacing_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> tuple[float,float]|None:
    """
    Returns the value corresponding to the value of the DICOM PixelSpacing tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0028,0030)
    # Keyword:              PixelSpacing
    # Value Representation: Decimal String (DS)
    # Type:	                Required (1) / Conditionally Required (1C)
    # Value Multiplicity:   2

    # Note:
    #   Maybe available in CR, DX
    #   Available in CT, MR, PT, enhanced CT, enhanced MR, enhanced PT

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM PixelSpacing tag
    value = dataset.get("PixelSpacing", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM PixelSpacing tag was not found or empty")
        return None

    if not isinstance(value, pydicom.multival.MultiValue) \
       or len(value) != 2:
        logger.warning(" "*(indent+0) + "DICOM PixelSpacing tag has invalid format")
        return None

    try:
        pixel_spacing = (float(value[0]), float(value[1]))
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM PixelSpacing values could not be converted to float values")
        return None
    
    if pixel_spacing[0] < 0.0 or pixel_spacing[1] < 0.0:
        logger.warning(" "*(indent+0) + f"DICOM PixelSpacing values: '{pixel_spacing}' are likely not valid")
        return None

    return pixel_spacing

#
# Edwin 2026-10-22
#
def get_rows_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> int|None:
    """
    Returns the number of rows corresponding to the value of the DICOM Rows tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0028,0010)
    # Keyword:              Rows
    # Value Representation: Unsigned Short (US)
    # Type:	                Required (1)
    # Value Multiplicity:   1

    # Note:
    #   Available in CR, DX, CT, MR, PT, enhanced CT, enhanced MR, enhanced PT

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    value = dataset.get("Rows", None)
    if value is None:
        logger.debug(" "*(indent+0) + "DICOM Rows tag was not found or empty")
        return None

    if not isinstance(value, int):
        logger.warning(" "*(indent+0) + "DICOM Rows tag has invalid format")
        return None

    # Should already be int
    number_of_rows = value

    if number_of_rows < 0:
        logger.warning(" "*(indent+0) + f"DICOM Rows tag value: '{number_of_rows}' is likely not a valid value")
        return None

    return number_of_rows


#
# Edwin 2026-10-22
#
def get_columns_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> int|None:
    """
    Returns the number of columns corresponding to the value of the DICOM Columns tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0028,0011)
    # Keyword:              Columns
    # Value Representation: Unsigned Short (US)
    # Type:	                Required (1)
    # Value Multiplicity:   1

    # Note:
    #   Available in CR, DX, CT, MR, PT, enhanced CT, enhanced MR, enhanced PT

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    value = dataset.get("Columns", None)
    if value is None:
        logger.debug(" "*(indent+0) + "DICOM Columns tag was not found or empty")
        return None

    if not isinstance(value, int):
        logger.warning(" "*(indent+0) + "DICOM Columns tag has invalid format")
        return None

    # Should already be int
    number_of_columns = value

    if number_of_columns < 0:
        logger.warning(" "*(indent+0) + f"DICOM Columns tag value: '{number_of_columns}' is likely not a valid value")
        return None

    return number_of_columns


#
# Edwin 2026-07-30
#
def get_spacing_between_slices_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the spacing corresponding to the value of the DICOM SpacingBetweenSlices tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,0088) 
    # Keyword:              SpacingBetweenSlices
    # Value Representation: Decimal String (DS)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    value = dataset.get("SpacingBetweenSlices", None)
    if value is None:
        logger.debug(" "*(indent+0) + "DICOM SpacingBetweenSlices tag was not found or empty")  
        return None
    
    if not isinstance(value, pydicom.valuerep.DSfloat):
        logger.warning(" "*(indent+0) + "DICOM SpacingBetweenSlices tag has an unknown format")
        return None
    
    # Try to convert DSfloat to float
    try:
        spacing_between_slices = float(value)
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM SpacingBetweenSlices tag value could not be converted to a float value")
        return None

    if spacing_between_slices < 0:
        # A negative value is allowed in some IODs (e.g. the NM Reconstruction Module, PS3.3 C.8.4.15),
        # where the sign gives the stacking direction relative to the first slice. SPHN stores the spacing
        # as a distance, so only the magnitude is kept.
        logger.debug(" "*(indent+0) + f"DICOM SpacingBetweenSlices tag value '{spacing_between_slices}' is negative (stacking direction); using its absolute value")
        spacing_between_slices = abs(spacing_between_slices)

    if spacing_between_slices == 0:
        logger.warning(" "*(indent+0) + "DICOM SpacingBetweenSlices tag value is 0 and therefore ignored")
        return None

    return spacing_between_slices


#
# Edwin 2026-10-22
#
def get_slice_thickness_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the slice thicknes corresponding to the value of the DICOM SliceThickness tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,0050) 
    # Keyword:              SliceThickness
    # Value Representation: Decimal String (DS)
    # Type:	                Required, Empty if Unknown (2)
    # Value Multiplicity:   1

    # Note:
    #   Not available in CR, DX
    #   Available in CT, MR, PT, enhanced CT, enhanced MR, enhanced PT

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    value = dataset.get("SliceThickness", None)
    if value is None:
        logger.debug(" "*(indent+0) + "DICOM SliceThickness tag was not found or empty")  
        return None

    if not isinstance(value, pydicom.valuerep.DSfloat):
        logger.warning(" "*(indent+0) + "DICOM SliceThickness tag has an unknown format")
        return None
    
    # Try to convert DSfloat to float
    try:
        slice_thickness = float(value)
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM SliceThickness tag value could not be converted to a float value")
        return None

    if slice_thickness < 0:
        logger.warning(" "*(indent+0) + f"DICOM SliceThickness tag value: '{slice_thickness}' may not be a valid value")
        return None

    return slice_thickness


#
# Edwin 2026-10-22
#
def get_samples_per_pixel_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> int|None:
    """
    Returns the number of samples per pixel corresponding to the value of the DICOM SamplesPerPixel tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0028,0002)
    # Keyword:              SamplesPerPixel
    # Value Representation: Unsigned Short (US)
    # Type:	                Required (1)
    # Value Multiplicity:   1

    # Note:
    #   Available in CR, DX, CT, MR, PT, enhanced CT, enhanced MR, enhanced PT

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    value = dataset.get("SamplesPerPixel", None)
    if value is None:
        logger.debug(" "*(indent+0) + "DICOM SamplesPerPixel tag was not found or empty")  
        return None

    if not isinstance(value, int):
        logger.warning(" "*(indent+0) + "DICOM SamplesPerPixel tag has an unknown format")
        return None
            
    # Should already be int
    samples_per_pixel = value

    if samples_per_pixel < 0:
        logger.warning(" "*(indent+0) + f"DICOM SamplesPerPixel tag value: '{samples_per_pixel}' is likely not a valid value")
        return None

    return samples_per_pixel


#
#  Edwin 2026-10-22
#
def get_body_part_examined_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the DICOM Term corresponding to the value of the DICOM BodyPartExamined tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,0015)
    # Keyword:              BodyPartExamined
    # Value Representation: Code String (CS)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    value = dataset.get("BodyPartExamined", None)
    if value is None:
        logger.debug(" "*(indent+0) + "DICOM BodyPartExamined tag was not found or empty")  
        return None
    
    # It should be a string
    if not isinstance(value, str):
        logger.warning(" "*(indent+0) + "DICOM BodyPartExamined tag has an unknown format")
        return None

    # Remove whitespace and convert to uppercase
    body_part_examined_term = value.strip().upper()

    # Check if value is not empty
    if len(body_part_examined_term) == 0:
        logger.debug(" "*(indent+0) + "DICOM BodyPartExamined tag value contains only whitespace")
        return None

    assert is_valid_string(body_part_examined_term)

    return body_part_examined_term


#
# Edwin 2026-07-31
#
def get_lossy_image_compression_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> bool | None:
    """
    Returns the boolean value corresponding to the value of the DICOM LossyImageCompression tag
    Parameters:
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Keyword:              LossyImageCompression
    # Value Representation: Code String (CS)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    if "LossyImageCompression" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM LossyImageCompression tag was not found")
        return None

    # Get the DataElement
    data_element = dataset["LossyImageCompression"]

    # Get the value
    value = data_element.value
    
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
    
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM LossyImageCompression tag value was not provided")
        return None
    
    # It should be a single-valued tag, a string
    if value_multiplicity != 1 or not isinstance(value, str):
        logger.warning(" "*(indent+0) + "DICOM LossyImageCompression tag has an unknown format")
        return None

    # Remove whitespace
    lossy_image_compression_code = value.strip()

    # Check if value is not empty
    if len(lossy_image_compression_code) == 0:
        logger.debug(" "*(indent+0) + "DICOM LossyImageCompression tag value contains only whitespace")
        return None

    # Check if it is a know DICOM code and convert to a corresponding boolean value
    has_lossy_image_compression = DataConverter.dicom_lossy_image_compression_code_dict.get(lossy_image_compression_code, None)

    if has_lossy_image_compression is None:
        logger.warning(" "*(indent+0) + f"DICOM LossyImageCompression tag value: '{lossy_image_compression_code}' could not be converted to a corresponding boolean value")
        return None
    
    # Check conversion is ok
    assert isinstance(has_lossy_image_compression, bool)

    return has_lossy_image_compression

#
# Edwin 2026-07-31
#
def get_lossy_image_compression_method_list_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> list[str|None] | None:
    """
    Returns a list with method strings corresponding to the values of the DICOM LossyImageCompressionMethod tag
    Parameters:
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    Note: The output list with methods can have a corresponding list with ratios. Therefore, 
          the order of methods in this list should correspond to the order of ratios in the other list
    """

    # Keyword:              LossyImageCompressionMethod
    # Value Representation: Code String (CS)
    # Type:	                Optional (3)
    # Value Multiplicity:   1-n

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Set initial value
    method_str_list = []

    if "LossyImageCompressionMethod" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM LossyImageCompressionMethod tag was not found")  
        return None

    # Get the DataElement
    data_element = dataset["LossyImageCompressionMethod"]

    # Get the value
    value = data_element.value
    
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
    
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM LossyImageCompressionMethod tag value was not provided")
        return None
    
    # It could be a multi-valued tag
    if value_multiplicity >= 1 and isinstance(value, pydicom.multival.MultiValue):

        # For each value in the multi-value list
        for value_item in value:

            if not isinstance(value_item, str):
                logger.warning(" "*(indent+0) + "DICOM LossyImageCompressionMethod tag value-item has an unknown format")
                
                # Add None to the list, to keep the same order
                method_str_list.append(None)
                continue

            # Remove whitespace
            compression_method = value_item.strip()

            # Check if value is not empty
            if len(compression_method) == 0:
                logger.debug(" "*(indent+0) + "DICOM LossyImageCompressionMethod tag value-item contains only whitespace")
                
                # Add None to the list, to keep the same order
                method_str_list.append(None)
                continue

            # Add to the list
            method_str_list.append(compression_method)

    # It could be a single-valued tag, a string
    elif value_multiplicity == 1 and isinstance(value, str):

        # Remove whitespace
        compression_method = value.strip()

        # Check if value is not empty
        if len(compression_method) == 0:
            logger.debug(" "*(indent+0) + "DICOM LossyImageCompressionMethod tag value contains only whitespace")
            return None
        
        # Add as single item to the list
        method_str_list=[compression_method]

    else:
        logger.warning(" "*(indent+0) + "DICOM LossyImageCompressionMethod tag has an unknown format")
        return None

    return method_str_list if len(method_str_list)>0 else None

#
# Edwin 2026-07-31
#
def get_lossy_image_compression_ratio_list_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> list[float|None] | None:
    """
    Returns a list of ratios corresponding to the values of the DICOM LossyImageCompressionRatio tag
    Parameters:
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    Note: The output list with ratios can have a corresponding list with methods. Therefore, 
          the order of ratios in this list should correspond to the order of methods in the other list
    """

    # Keyword:              LossyImageCompressionRatio
    # Value Representation: Decimal String (DS)
    # Type:	                Optional (3)
    # Value Multiplicity:   1-n

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Set initial value
    ratio_float_list = []

    if "LossyImageCompressionRatio" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM LossyImageCompressionRatio tag was not found")
        return None

    # Get the DataElement
    data_element = dataset["LossyImageCompressionRatio"]

    # Get the value
    value = data_element.value
    
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
    
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM LossyImageCompressionRatio tag value was not provided")
        return None
    
    # It could be a multi-valued tag
    if value_multiplicity > 1 and isinstance(value, pydicom.multival.MultiValue):

        # For each value in the multi-value list
        for value_item in value:
            
            if not isinstance(value_item, pydicom.valuerep.DSfloat):
                logger.warning(" "*(indent+0) + "DICOM LossyImageCompressionRatio tag value-item has an unknown format")
                
                # Add None to the list, to keep the same order
                ratio_float_list.append(None)
                continue

            # Try to convert DSfloat to float
            try:
                algorithm_ratio = float(value_item)
            except (ValueError, TypeError):
                logger.warning(" "*(indent+0) + "DICOM LossyImageCompressionRatio tag value_item could not be converted to a float value")

                # Add None to the list, to keep the same order
                ratio_float_list.append(None)
                continue

            # Add to the list
            ratio_float_list.append(algorithm_ratio)

    # It could be a single-valued tag, a DSfloat
    elif value_multiplicity == 1 and isinstance(value, pydicom.valuerep.DSfloat):

        # Try to convert DSfloat to float
        try:
            algorithm_ratio = float(value)
        except (ValueError, TypeError):
            logger.warning(" "*(indent+0) + "DICOM LossyImageCompressionRatio tag value could not be converted to a float value")
            return None

        # Add single value to a list
        ratio_float_list.append(algorithm_ratio)

    else:
        logger.warning(" "*(indent+0) + "DICOM LossyImageCompressionRatio tag has an unknown format")
        return None

    return ratio_float_list if len(ratio_float_list)>0 else None

#
# Edwin 2026-08-01
#
def convert_to_data_compression_algorithm_list(
        has_lossy_compression: bool|None, 
        lossy_compression_method_list: list|None, 
        lossy_compression_ratio_list: list|None,
        context: Context,
        indent: int=0
    ) -> list[SPHNDataCompressionAlgorithm]|None:
    
    """
    Returns a list with unique SPHN DataCompressionAlgorithm instances corresponding to the values of the DICOM LossyImageCompression, LossyImageCompressionMethod and LossyImageCompressionRatio tags
    Parameters:
        - has_lossy_compression is a boolean value corresponding to the DICOM LossyImageCompression tag
        - lossy_compression_method_list is a list of strings corresponding to the DICOM LossyImageCompressionMethod tag
        - lossy_compression_ratio_list is a list of floats corresponding to the DICOM LossyImageCompressionRatio tag
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Checks
    assert has_lossy_compression is None or isinstance(has_lossy_compression,bool)
    assert lossy_compression_method_list is None or isinstance(lossy_compression_method_list,list)
    assert lossy_compression_ratio_list is None or isinstance(lossy_compression_ratio_list,list)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent>=0

    logger = context.logger
    sphn_schema = context.sphn_schema

    image_compression_algorithm_list = []

    # Check if there is any usefull info
    if has_lossy_compression is not None \
        or lossy_compression_method_list is not None \
        or lossy_compression_ratio_list is not None:

        # Create empty list when None
        if lossy_compression_method_list is None:
            method_list = []
        else:
            method_list = lossy_compression_method_list

        if lossy_compression_ratio_list is None:
            ratio_list = []
        else:
            ratio_list = lossy_compression_ratio_list

        # Zipping with zip_longest and filling with 'None'
        zipped_list = list(itertools.zip_longest(method_list, ratio_list, fillvalue=None))

        for method, ratio in zipped_list:

            has_method = None
            has_type = None
            has_ratio = None

            # Check if method is a string or None
            if method is not None:

                assert isinstance(method, str)

                result = DataConverter.dicom_data_compression_method_dict.get(method.upper(), None)

                if result is not None:

                    assert len(result) == 3

                    if is_clean_string(result[0]):

                        assert sphn_schema.is_sphn_data_compression_algorithm_method_value_set_member(result[0])

                        has_method = result[0]
                        logger.debug(" "*(indent+0) + f"DICOM LossyImageCompressionMethod tag value-item: '{method}' was converted to"+
                                     f" a corresponding SPHN DataCompressionAlgorithm_method ValueSet member: '{has_method}'")
                    else:
                        logger.warning(" "*(indent+0) + "Expected a clean string for DICOM LossyImageCompressionMethod tag" +
                                       f" value-item: '{method}' but found: '{result[0]}' in conversion table")

                    if is_valid_string(result[1]):

                        assert sphn_schema.is_sphn_data_compression_algorithm_type_value_set_member(result[1])

                        has_type = result[1]
                        logger.debug(" "*(indent+0) + f"DICOM LossyImageCompressionMethod tag value-item: '{method}' was converted to"+
                                     f" a corresponding SPHN DataCompressionAlgorithm_type ValueSet member: '{has_type}'")
                    else:
                        logger.warning(" "*(indent+0) + "Expected a valid string for DICOM LossyImageCompressionMethod tag" +
                                       f" value-item: '{method}' but found: '{result[1]}' in conversion table")
                else:
                    logger.warning(" "*(indent+0) + f"DICOM LossyImageCompressionMethod tag value-item: '{method}'" +
                                   " could not be converted to a corresponding SPHN DataCompressionAlgorithm_method ValueSet member" +
                                   " and SPHN DataCompressionAlgorithm_type ValueSet member")
            if ratio is not None:

                assert isinstance(ratio, float)

                if ratio > 0.00:

                    sphn_code_ratio = SPHNCode( 
                        sphn_schema = sphn_schema,
                        has_identifier = "cblratiocbr",  # SPHN UCUM unit code, label: "{ratio}", comment: "ratio"
                        has_coding_system_and_version = "UCUM"
                        )
                    sphn_unit_ratio = SPHNUnit(
                        sphn_schema = sphn_schema,
                        has_code = sphn_code_ratio
                        )
                    sphn_quantity_ratio = SPHNQuantity(
                        sphn_schema = sphn_schema,
                        has_value = ratio,
                        has_unit = sphn_unit_ratio
                        )

                    has_ratio = sphn_quantity_ratio

                    logger.debug(" "*(indent+0) + f"DICOM LossyImageCompressionRatio tag value-item: '{ratio}'")
                else:
                    logger.warning(" "*(indent+0) + f"Expected a positive float for DICOM LossyImageCompressionRatio tag but found: '{ratio}'")


            # Check if values comply with each other
            if not has_lossy_compression and method is not None:
                logger.warning(" "*(indent+0) + f"DICOM LossyImageCompressionMethod tag has '{method}' indicated, while DICOM LossyImageCompression was set to '{has_lossy_compression}'.")

            # Check if values comply with each other
            if not has_lossy_compression and ratio is not None:
                logger.warning(" "*(indent+0) + f"DICOM LossyImageCompressionRatio tag has '{ratio}' indicated, while DICOM LossyImageCompression was set to '{has_lossy_compression}'.")

            # Check if there is any usefull info to create an SPHN DataCompressionAlgorithm instance
            if has_lossy_compression is not None or has_method is not None or has_type is not None or has_ratio is not None:

                sphn_data_compression_algorithm = SPHNDataCompressionAlgorithm(
                    sphn_schema=sphn_schema,
                    has_name = None,
                    has_version = None,
                    has_description = None,
                    has_uniform_resource_locator = None,
                    has_type=has_type,
                    has_method=has_method,
                    has_ratio=has_ratio
                )

                # Check if it is already in the list
                if sphn_data_compression_algorithm not in image_compression_algorithm_list:
                    image_compression_algorithm_list.append(sphn_data_compression_algorithm)
                else:
                    logger.debug(" "*(indent+2) + "SPHN DataCompressionAlgorithm is already in the list")

    return image_compression_algorithm_list if len(image_compression_algorithm_list)>0 else None

#
# Edwin 2026-08-02
#
def get_content_qualification_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> SPHN_ImageFrame_content_qualification_ValueSet_Member | None:
    """
    Returns the SPHN ImagingSeries_contentQualification ValueSet member corresponding to 
        the value of the DICOM ContentQualification tag
    Parameters:
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Keyword:              ContentQualification
    # Value Representation: Code String (CS)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger
    sphn_schema = context.sphn_schema

    if "ContentQualification" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM ContentQualification tag was not found")  
        return None

    # Get the DataElement
    data_element = dataset["ContentQualification"]

    # Get the value
    value = data_element.value
    
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
    
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM ContentQualification tag value was not provided")
        return None
    
    # It should be a single-valued tag, a string
    if value_multiplicity != 1 or not isinstance(value, str):
        logger.warning(" "*(indent+0) + "DICOM ContentQualification tag has an unknown format")
        return None

    # Remove whitespace
    content_qualification_str = value.strip()

    # Check if value is not empty
    if len(content_qualification_str) == 0:
        logger.debug(" "*(indent+0) + "DICOM ContentQualification tag contains only whitespace")
        return None

    # Check if it is a known DICOM term and convert to a corresponding SPHN ImagingSeries_contentQualification ValueSet member
    content_qualification_valueset_member = DataConverter.dicom_content_qualification_dict_lower_case_key.get(content_qualification_str.lower(), None)

    if content_qualification_valueset_member is None:
        logger.warning(" "*(indent+0) + f"DICOM ContentQualification tag value: '{content_qualification_str}' could not be converted to a corresponding SPHN ImagingSeries_contentQualification ValueSet member")
        return None
    
    # Check conversion is ok
    assert is_valid_string(content_qualification_valueset_member)
    assert sphn_schema is not None
    assert sphn_schema.is_sphn_imaging_frame_content_qualification_value_set_member(content_qualification_valueset_member)

    return content_qualification_valueset_member


#
# Edwin 2026-08-02
#
def get_image_position_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> ImagePosition | None:
    """
    Returns the values corresponding to the values of the DICOM ImagePositionPatient tag,
        it specifies the x, y, and z coordinates of the upper left hand corner of the image; it is the center of the first voxel transmitted,
    Parameters:
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Keyword:              ImagePositionPatient
    # Value Representation: Decimal String (DS)
    # Type:	                Required (1)
    # Value Multiplicity:   3

    # Note:
    #   Not available in CR, DX
    #   Available in CT, MR, PT, enhanced CT, enhanced MR, enhanced PT

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Set initial value
    ucum_unit = "mm"    # The DICOM unit for ImagePositionPatient is always "mm"

    if "ImagePositionPatient" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM ImagePositionPatient tag was not found")
        return None

    # Get the DataElement
    data_element = dataset["ImagePositionPatient"]

    # Get the value
    value = data_element.value
    
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM

    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM ImagePositionPatient tag value was not provided")
        return None
    
    # It should be a multi-valued tag
    if value_multiplicity != 3 or not isinstance(value, pydicom.multival.MultiValue) or \
        not isinstance(value[0], pydicom.valuerep.DSfloat) or \
        not isinstance(value[1], pydicom.valuerep.DSfloat) or \
        not isinstance(value[2], pydicom.valuerep.DSfloat):
        logger.warning(" "*(indent+0) + "DICOM ImagePositionPatient tag has an unknown format")
        return None
            
    # Try to convert DSfloat to float
    try:
        x_value = float(value[0])
        y_value = float(value[1])
        z_value = float(value[2])
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM ImagePositionPatient values could not be converted to float values")
        return None

    return ((x_value, y_value, z_value), ucum_unit)


#
# Edwin 2026-08-02
#
def get_image_orientation_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> ImageOrientation | None:
    """
    Returns the values corresponding to the values of the DICOM ImageOrientationPatient tag,
        specifies the direction cosines of the first row and the first column with respect to the patient,
    Parameters:
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Keyword:              ImageOrientationPatient
    # Value Representation: Decimal String (DS)
    # Type:	                Required (1)
    # Value Multiplicity:   6

    # Note:
    #   Not available in CR, DX
    #   Available in CT, MR, PT, enhanced CT, enhanced MR, enhanced PT

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    if "ImageOrientationPatient" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM ImageOrientationPatient tag was not found")
        return None
    
    # Get the DataElement
    data_element = dataset["ImageOrientationPatient"]

    # Get the value
    value = data_element.value
    
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM

    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM ImageOrientationPatient tag value was not provided")
        return None
    
    # It should be a multi-valued tag
    if value_multiplicity != 6 or not isinstance(value, pydicom.multival.MultiValue) or \
        not isinstance(value[0], pydicom.valuerep.DSfloat) or \
        not isinstance(value[1], pydicom.valuerep.DSfloat) or \
        not isinstance(value[2], pydicom.valuerep.DSfloat) or \
        not isinstance(value[3], pydicom.valuerep.DSfloat) or \
        not isinstance(value[4], pydicom.valuerep.DSfloat) or \
        not isinstance(value[5], pydicom.valuerep.DSfloat):
        logger.warning(" "*(indent+0) + "DICOM ImageOrientationPatient tag has an unknown format")
        return None
            
    # Try to convert DSfloat to float
    try:
        row_x_value = float(value[0])
        row_y_value = float(value[1])
        row_z_value = float(value[2])
        column_x_value = float(value[3])
        column_y_value = float(value[4])
        column_z_value = float(value[5])
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM ImageOrientationPatient tag values could not be converted to float values")
        return None

    return ((row_x_value, row_y_value, row_z_value), (column_x_value, column_y_value, column_z_value))


#
# Edwin 2026-10-13
#
def get_acquisition_date_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM AcquisitionDate tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0008,0022)
    # Type:	                Optional (3)
    # Keyword:              AcquisitionDate
    # Value Multiplicity:   1
    # Value Representation: Date (DA)

    # Note:
    # The DICOM date format is specified in the DICOM standard as Date (DA) in:
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part05/sect_6.2.html

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM AcquisitionDate tag
    aq_date = dataset.get("AcquisitionDate", None)

    if aq_date is None:
        logger.debug(" "*(indent+0) + "DICOM AcquisitionDate tag was not found or empty")  
        return None

    # Convert a possible DICOM DA object to a string representation
    aq_date_str = str(aq_date)

    return aq_date_str


#
# Edwin 2026-10-13
#
def get_acquisition_time_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM AcquisitionTime tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Keyword:              AcquisitionTime
    # Tag:                  (0008,0032)
    # Value Representation: Time (TM)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Note:
    # The DICOM time format is specified in the DICOM standard as Time (TM) in:
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part05/sect_6.2.html

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM AcquisitionTime tag
    aq_time = dataset.get("AcquisitionTime", None)

    if aq_time is None:
        logger.debug(" "*(indent+0) + "DICOM AcquisitionTime tag was not found or empty")  
        return None

    # Convert a possible DICOM TM object to a string representation
    aq_time_str = str(aq_time)

    # The string could be in various DICOM TM formats such as HHMMSS.frac, HHMMSS, HHMM, or HH
    # if len(aq_time_str)<6:
    #     logger.debug(" "*(indent+0) + f"DICOM AcquisitionTime string shorter than expected (6 char) HHMMSS format: '{aq_time_str}'. Padding with zeros.")
    #     aq_time_str = aq_time_str.ljust(6, '0')

    return aq_time_str


#
# Edwin 2026-10-13
#
def get_acquisition_datetime_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM AcquisitionDateTime tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Keyword:              AcquisitionDateTime
    # Tag:                  (0008,002A)
    # Value Representation: DateTime (DT)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Note:
    # The DICOM datetime format is specified in the DICOM standard as Date Time (DT) in:
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part05/sect_6.2.html

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM AcquisitionDateTime tag
    dt_obj = dataset.get("AcquisitionDateTime", None)

    if dt_obj is None:
        logger.debug(" "*(indent+0) + "DICOM AcquisitionDateTime tag was not found or empty")  
        return None

    # Convert a possible DICOM DT object to a string representation
    dt_str = str(dt_obj)

    return dt_str

# ---------------------------------------------------------------------------------------------------------------------
# Old and/or unused functions
# ---------------------------------------------------------------------------------------------------------------------

#
#  Edwin 2026-07-31
#  Old
def get_contrast_bolus_agent_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str | None:
    """
    Returns the string corresponding to the value of the DICOM ContrastBolusAgent tag
    Parameters:
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,0010)
    # Type:	                Required, Empty if Unknown (2)
    # Keyword:	            ContrastBolusAgent
    # Value Multiplicity	1
    # Value Representation:	Long String (LO)
    
    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    if "ContrastBolusAgent" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAgent tag was not found")  
        return None

    # Get the DataElement
    data_element = dataset["ContrastBolusAgent"]

    # Get the value
    value = data_element.value
    
    # Get the Value Multiplicity
    value_multiplicity = data_element.VM
    
    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAgent tag value was not provided")
        return None

    # It should be a single-valued tag, a string
    if value_multiplicity != 1 or not isinstance(value, str):
        logger.warning(" "*(indent+0) + "DICOM ContrastBolusAgent tag has an unknown format")
        return None

    # Remove whitespace
    contrast_bolus_agent = value.strip()

    # Check if value is not empty
    if len(contrast_bolus_agent) == 0:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAgent tag value contains only whitespace")
        return None

    return contrast_bolus_agent

#
# Edwin 2026-08-27
# Old
def get_contrast_bolus_agent_sequence_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Sequence|None:
    """
    Returns the list of Datasets in the DICOM ContrastBolusAgentSequence tag
    Parameters:
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Keyword:              ContrastBolusAgentSequence
    # Tag:                  (0018,0012)
    # Value Representation: Sequence (SQ)
    # Type:	                Optional (3)
    # Value Multiplicity:   1


    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    if "ContrastBolusAgentSequence" not in dataset:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAgentSequence tag was not found")  
        return None

    # Get the DataElement
    data_element = dataset["ContrastBolusAgentSequence"]

    if data_element is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAgentSequence tag was not found")
        return None

    # Get the Value Multiplicity
    value_multiplicity = data_element.VM

    # Get the Value Representation
    value_representation = data_element.VR

    # Get the value
    value = data_element.value

    # Check if it is empty
    if value_multiplicity == 0 or value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAgentSequence tag value was not provided")
        return None
    
    # It should be a single-valued tag, a Sequence
    if value_multiplicity != 1 or not isinstance(value, Sequence) or value_representation != "SQ":
        logger.warning(" "*(indent+0) + "DICOM ContrastBolusAgentSequence tag has an unknown format")
        return None

    assert isinstance(value, Sequence)

    return value


#
# Edwin 2026-08-11
# ToDo: Not finished yet
def get_real_world_value_mapping_sequence_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Sequence|None:
    """
    Returns the list of Datasets in the DICOM Real World Value Mapping Sequence tag
    Parameters:
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Keyword:              RealWorldValueMappingSequence
    # Tag:                  (0040,9096)
    # Value Representation: Sequence (SQ)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    # logger = context.logger

    # # Get the DataElement
    # sequence = dataset.get("DeidentificationMethodCodeSequence", None)
    # data_element = dataset["DeidentificationMethodCodeSequence"]

    # if data_element is None:
    #     logger.debug(" "*(indent+0) + "DICOM RealWorldValueMappingSequence tag was not found")
    #     return None

    # # Get the Value Multiplicity
    # value_multiplicity = data_element.VM

    # # Get the Value Representation
    # value_representation = data_element.VR

    # # Get the value
    # value = data_element.value

    # # Check if it is empty
    # if value_multiplicity == 0 or value is None:
    #     logger.debug(" "*(indent+0) + "DICOM RealWorldValueMappingSequence tag value was not provided")
    #     return None
    
    # # It should be a single-valued tag, a Sequence
    # if value_multiplicity != 1 or not isinstance(value, Sequence) or value_representation != "SQ":
    #     logger.warning(" "*(indent+0) + "DICOM RealWorldValueMappingSequence tag has an unknown format")
    #     return None

    # return value


# -----------------------------------------------------------------------------------------------------------------
# Unused Functions
# -----------------------------------------------------------------------------------------------------------------

# 
# Edwin 2025-05-13: Not Used
#
# ToDo by Edwin:
#  - Doesn't work as it is in a sequence
#
# def to_do_get_frame_acquisition_datetime_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str | None:
#     """
#     Returns the value of the DICOM FrameAcquisitionDateTime tag
#         dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
#     """

#     # Keyword:              FrameAcquisitionDateTime
#     # Value Representation: Date Time (DT)
#     # Type:	                Conditionally Required (1C)
#     # Value Multiplicity:   1

#     # Check
#     assert isinstance(dataset, Dataset)
#     assert isinstance(context, Context)
#     assert isinstance(indent,int) and indent>=0

#     logger = context.logger

#     # Set initial value
#     frame_acquisition_datetime_str = None

#     if "FrameAcquisitionDateTime" in dataset:

#         # Get the DataElement
#         data_element = dataset["FrameAcquisitionDateTime"]

#         # Get the value
#         value = data_element.value
        
#         # Get the Value Multiplicity
#         value_multiplicity = data_element.VM
        
#         # Check if it is empty
#         if value_multiplicity == 0 or value is None:
#             logger.debug(" "*(indent+0) + "DICOM FrameAcquisitionDateTime tag value is not provided")
        
#         # It should be a single-valued tag, a string
#         elif value_multiplicity == 1 and isinstance(value, str):

#             # Should already be str and remove whitespace
#             frame_acquisition_datetime_str = value.strip()

#             # Check if value is not empty
#             if len(frame_acquisition_datetime_str) == 0:
#                 logger.debug(" "*(indent+0) + "DICOM FrameAcquisitionDateTime tag contains only whitespace.")
#                 frame_acquisition_datetime_str = None

#         else:
#             logger.error(" "*(indent+0) + "DICOM FrameAcquisitionDateTime tag has unknown format")
#             raise ValueError("DICOM FrameAcquisitionDateTime tag has unknown format")

#     return frame_acquisition_datetime_str

# 
# Edwin 2025-05-13: Not Used
#
# ToDo by Edwin:
#  - Doesn't work as it is in a sequence
#
# def to_do_get_frame_type_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> list | None:
#     """
#     Returns a list with value_set values corresponding to values of the DICOM FrameType tag
#         dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
#     """

#     # Keyword:              FrameType
#     # Value Representation: Code String (CS)
#     # Type:	                Required (1)
#     # Value Multiplicity:   4-5

#     # Check
#     assert isinstance(dataset, Dataset)
#     assert isinstance(context, Context)
#     assert isinstance(indent,int) and indent>=0

#     logger = context.logger

#     # Set initial value
#     frame_type_list = None

#     if "FrameType" in dataset:

#         # Get the DataElement
#         data_element = dataset["FrameType"]

#         # Get the value
#         value = data_element.value
        
#         # Get the Value Multiplicity
#         value_multiplicity = data_element.VM
        
#         # Check if it is empty
#         if value_multiplicity == 0 or value is None:
#             logger.debug(" "*(indent+0) + "DICOM FrameType tag value is not provided")

#         # It should be a multi-valued tag
#         elif value_multiplicity >= 4 and isinstance(value, pydicom.multival.MultiValue):

#             # Set initial value
#             frame_type_list = []

#             # For each value in the multi-value list
#             for value_item in value:

#                 # Set initial value
#                 valueset_value_str = None

#                 if isinstance(value_item, str):

#                     # Should already be a string, remove whitespace
#                     frame_type_str = value_item.strip()

#                     # Check if value is not empty
#                     if len(frame_type_str) > 0:

#                         # Convert to upper case
#                         frame_type_str_upper_case = frame_type_str.upper()

#                         # Check if it is a know SPHN ImagingSeries_type
#                         if frame_type_str_upper_case in Omniscient.sphn_imaging_frame_type_value_set_dict:

#                             # Get the ValueSet value
#                             valueset_value_str = Omniscient.sphn_imaging_frame_type_value_set_dict[frame_type_str_upper_case]

#                         else:
#                             logger.debug(" "*(indent+0) + f"DICOM FrameType tag value: '{frame_type_str}' not in the SPHN ImagingSeries_type list (ValueSet).")
#                             # raise ValueError(f"DICOM FrameType tag value: '{image_type_str}' not in the SPHN ImagingSeries_type list (ValueSet).")
#                     else:
#                         logger.debug(" "*(indent+0) + "DICOM FrameType tag contains values that are only whitespace.")
#                 else:
#                     logger.error(" "*(indent+0) + "DICOM FrameType tag has unknown format")
#                     raise TypeError("DICOM FrameType tag has unknown format")
                
#                 # Add to the list
#                 frame_type_list.append(valueset_value_str)

#         else:
#             logger.error(" "*(indent+0) + "DICOM FrameType tag has unknown format")
#             raise TypeError("DICOM FrameType tag has unknown format")

#     else:
#         logger.error(" "*(indent+0) + "DICOM FrameType tag is Required (1), but not found")
#         raise ValueError("DICOM FrameType tag value is Required (1), but not found")

#     return frame_type_list
