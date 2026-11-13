"""
dicom_pet_isotope_module_reader.py:
    Part of the example dicom2sphn package.
    It contains functions for reading DICOM PET isotope (radiopharmaceutical and radionuclide) tags.
"""
import re
from datetime import datetime, tzinfo

from pydicom import Dataset
from pydicom.sequence import Sequence

from .context import Context
from .data_converter import DataConverter
from .dicom_code_sequence_tags_reader import (
    get_code_meaning_from_dicom,
    get_code_value_from_dicom,
    get_coding_scheme_designator_from_dicom,
)
from .sphn_concepts.sphn_code import CodingSystemList, SPHNCode
from .sphn_concepts.sphn_quantity import SPHNQuantity
from .sphn_concepts.sphn_radioactivity import SPHNRadioactivity
from .sphn_concepts.sphn_radionuclide import SPHNRadionuclide
from .sphn_concepts.sphn_radiopharmaceutical import SPHNRadiopharmaceutical
from .sphn_concepts.sphn_radiopharmaceutical_administration_event import (
    SPHNRadiopharmaceuticalAdministrationEvent,
)
from .sphn_concepts.sphn_substance import SPHNSubstance
from .sphn_concepts.sphn_unit import SPHNUnit
from .tools import (
    combine_dicom_time_with_reference_datetime,
    complete_dicom_datetime,
    complete_dicom_time,
    extract_administration_routes_from_text,
    get_dicom_timezone,
    get_lookup_coding_scheme_designator,
    is_valid_string,
)

type CodeTuple = tuple[str, str, str]  # (coding scheme designator, code value, description) as used in the DataConverter dictionaries

#
# DICOM defines two modules for PET isotope (radiopharmaceutical and radionuclide) information:
#
# - The "PET Isotope" module
#   - Used by legacy (single-frame) PET images.
#   - Table C.8-61. PET Isotope Module Attributes
#   - Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.8.9.2.html
#
# - The "Enhanced PET Isotope" module
#   - Used by enhanced (multi-frame) PET images.
#   - Table C.8.22-9. Enhanced PET Isotope Module Attributes
#   - Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.8.22.4.html
#
# - Checking for the presence of a "PET Isotope" or an "Enhanced PET Isotope" module in the DICOM dataset
#   - Both modules have a "Radiopharmaceutical Information Sequence Attribute (0054,0016)" tag.
#   - The legacy (single-frame) PET Isotope module:
#       - has the sequence as Type 2 (required, but may be empty), its items have no "Radiopharmaceutical Agent Number Attribute (0018,9729)" tag.
#       - may contain free text tags: "Radiopharmaceutical Attribute (0018,0031)" and "Radiopharmaceutical Route Attribute (0018,1070)",
#         and time only tags: "Radiopharmaceutical Start Time Attribute (0018,1072)" and "Radiopharmaceutical Stop Time Attribute (0018,1073)".
#   - The enhanced (multi-frame) PET Isotope module:
#       - has the sequence as Type 1, each item has a mandatory "Radiopharmaceutical Agent Number Attribute (0018,9729)" tag.
#       - has only coded information and DateTime tags, no free text or time only tags.
#
# - The "Intervention Drug Information Sequence Attribute (0018,0026)" in the legacy PET Isotope module is not processed.
#
# - Mapping of the DICOM PET isotope information to the SPHN schema:
#   - SPHN Radiopharmaceutical Administration Event
#       - has start datetime:           Radiopharmaceutical Start DateTime (0018,1078) or Start Time (0018,1072)
#       - has end datetime:             Radiopharmaceutical Stop DateTime (0018,1079) or Stop Time (0018,1073)
#       - has administration route code: Administration Route Code Sequence (0054,0302) or Radiopharmaceutical Route (0018,1070)
#       - has drug: SPHN Radiopharmaceutical
#           - has active ingredient:    Radiopharmaceutical Code Sequence (0054,0304) or Radiopharmaceutical (0018,0031)
#           - has quantity:             Radiopharmaceutical Volume (0018,1071) [mL]
#           - has radionuclide: SPHN Radionuclide
#               - has code:             Radionuclide Code Sequence (0054,0300), or derived from the radiopharmaceutical
#               - has half life:        Radionuclide Half Life (0018,1075) [s]
#               - has positron fraction: Radionuclide Positron Fraction (0018,1076) [{fraction}]
#               - has radioactivity: SPHN Radioactivity
#                   - has quantity:     Radionuclide Total Dose (0018,1074) [Bq in DICOM, MBq in SPHN]
#                   - has datetime:     the radiopharmaceutical start datetime (DICOM: the dose is measured at the start time)
#   - Not mapped to SPHN (only read and logged): Radiopharmaceutical Specific Activity (0018,1077),
#     Radiopharmaceutical Administration Event UID (0008,3012) and Radiopharmaceutical Agent Number (0018,9729).

# ---------------------------------------------------------------------------------------------------------------------
# Functions for processing the Legacy/Enhanced "PET Isotope" module
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-11-13
#
def process_dicom_pet_isotope_information(dataset: Dataset, context: Context, indent: int=0) -> None:
    """
    Processes the DICOM PET Isotope information, either legacy (single-frame) or enhanced (multi-frame),
    and stores radiopharmaceutical administration events in the data_store.
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Check if the dataset contains the legacy (single-frame) PET Isotope module or the enhanced (multi-frame) PET Isotope module
    radiopharmaceutical_information_sequence = dataset.get("RadiopharmaceuticalInformationSequence", None)

    if radiopharmaceutical_information_sequence is None:
        logger.debug(" "*(indent+0) + "No DICOM (legacy or enhanced) PET Isotope module found in the dataset.")
        return

    assert isinstance(radiopharmaceutical_information_sequence, Sequence)

    has_enhanced_pet_isotope_module = len(radiopharmaceutical_information_sequence) > 0 \
        and all(hasattr(item, "RadiopharmaceuticalAgentNumber") for item in radiopharmaceutical_information_sequence)
    has_legacy_pet_isotope_module = not has_enhanced_pet_isotope_module

    # DICOM dates and times are local times: get the timezone (TimezoneOffsetFromUTC or the configured local timezone)
    # The TimezoneOffsetFromUTC tag is at the top level of the dataset, not in the sequence items
    assert context.local_timezone is not None
    dicom_timezone = get_dicom_timezone(dataset, context.local_timezone, logger, indent=indent+2)

    if has_legacy_pet_isotope_module:
        logger.debug(" "*(indent+0) + "Found DICOM legacy (single-frame) PET Isotope module.")
        process_legacy_pet_isotope_module_from_dicom(dataset, dicom_timezone, context, indent=indent+2)

    else:
        logger.debug(" "*(indent+0) + "Found DICOM enhanced (multi-frame) PET Isotope module.")
        process_enhanced_pet_isotope_module_from_dicom(dataset, dicom_timezone, context, indent=indent+2)


# ---------------------------------------------------------------------------------------------------------------------
# Functions for processing the Legacy (single-frame) "PET Isotope" module
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-11-13
#
def process_legacy_pet_isotope_module_from_dicom(dataset: Dataset, dicom_timezone: tzinfo, context: Context, indent: int=0) -> None:
    """
    Processes the DICOM legacy (single-frame) PET Isotope Module information
    and stores radiopharmaceutical administration events in the data_store.
    Parameters:
        - dataset: The DICOM Dataset containing the legacy (single-frame) PET Isotope Module
        - dicom_timezone: The timezone of the DICOM dates and times (see get_dicom_timezone())
        - context: The Context object that holds the data_store, logger, and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(dicom_timezone, tzinfo)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger
    data_store = context.data_store

    #
    # 1. Get the Radiopharmaceutical Information Sequence
    #

    radiopharmaceutical_information_sequence = get_radiopharmaceutical_information_sequence_from_dicom(dataset, context, indent=indent+2)

    if radiopharmaceutical_information_sequence is None:
        logger.debug(" "*(indent+0) + "DICOM RadiopharmaceuticalInformationSequence not found or empty in the dataset")
        return

    assert isinstance(radiopharmaceutical_information_sequence, Sequence)

    logger.debug(" "*(indent+0) + f"DICOM RadiopharmaceuticalInformationSequence found with {len(radiopharmaceutical_information_sequence)} item(s)")

    #
    # 2. Process the items in the Radiopharmaceutical Information Sequence
    #

    for i, item in enumerate(radiopharmaceutical_information_sequence, start=1):

        assert isinstance(item, Dataset)

        logger.debug(" "*(indent+2) + f"Processing item {i} of {len(radiopharmaceutical_information_sequence)} in DICOM RadiopharmaceuticalInformationSequence")

        sphn_radiopharmaceutical_administration_event = process_legacy_radiopharmaceutical_information_sequence_item(item, dicom_timezone, context, indent=indent+4)

        # Store the SPHN radiopharmaceutical administration event in the data store
        if sphn_radiopharmaceutical_administration_event is not None:
            data_store.add_sphn_radiopharmaceutical_administration_event_to_list(
                sphn_radiopharmaceutical_administration_event=sphn_radiopharmaceutical_administration_event,
                logger=logger,
                indent=indent+4
            )
        else:
            logger.debug(" "*(indent+4) + "No SPHN Radiopharmaceutical Administration Event object to store in the data store")


#
# Edwin 2026-11-13
#
def process_legacy_radiopharmaceutical_information_sequence_item(dataset: Dataset, dicom_timezone: tzinfo, context: Context, indent: int=0) -> SPHNRadiopharmaceuticalAdministrationEvent|None:
    """
    Process the DICOM legacy (single-frame) RadiopharmaceuticalInformationSequence item (Dataset)
    and return an SPHNRadiopharmaceuticalAdministrationEvent object, if any.
    The coded information is used first, the free text and time only tags are used when there is no coded or DateTime information.
    Parameters:
        - dataset: The DICOM legacy (single-frame) RadiopharmaceuticalInformationSequence item (Dataset)
        - dicom_timezone: The timezone of the DICOM dates and times (see get_dicom_timezone())
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(dicom_timezone, tzinfo)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    return process_radiopharmaceutical_information_sequence_item(dataset, dicom_timezone, use_free_text=True, context=context, indent=indent)


# ---------------------------------------------------------------------------------------------------------------------
# Functions for processing the Enhanced (multi-frame) "PET Isotope" module
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-11-13
#
def process_enhanced_pet_isotope_module_from_dicom(dataset: Dataset, dicom_timezone: tzinfo, context: Context, indent: int=0) -> None:
    """
    Processes the DICOM enhanced (multi-frame) PET Isotope Module information
    and stores radiopharmaceutical administration events in the data_store.
    Parameters:
        - dataset: The DICOM Dataset containing the enhanced (multi-frame) PET Isotope Module
        - dicom_timezone: The timezone of the DICOM dates and times (see get_dicom_timezone())
        - context: The Context object that holds the data_store, logger, and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(dicom_timezone, tzinfo)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger
    data_store = context.data_store

    #
    # 1. Get the Radiopharmaceutical Information Sequence
    #

    radiopharmaceutical_information_sequence = get_radiopharmaceutical_information_sequence_from_dicom(dataset, context, indent=indent+2)

    if radiopharmaceutical_information_sequence is None:
        logger.debug(" "*(indent+0) + "DICOM RadiopharmaceuticalInformationSequence not found or empty in the dataset")
        return

    assert isinstance(radiopharmaceutical_information_sequence, Sequence)

    logger.debug(" "*(indent+0) + f"DICOM RadiopharmaceuticalInformationSequence found with {len(radiopharmaceutical_information_sequence)} item(s)")

    #
    # 2. Process the items in the Radiopharmaceutical Information Sequence
    #

    for i, item in enumerate(radiopharmaceutical_information_sequence, start=1):

        assert isinstance(item, Dataset)

        logger.debug(" "*(indent+2) + f"Processing item {i} of {len(radiopharmaceutical_information_sequence)} in DICOM RadiopharmaceuticalInformationSequence")

        sphn_radiopharmaceutical_administration_event = process_enhanced_radiopharmaceutical_information_sequence_item(item, dicom_timezone, context, indent=indent+4)

        # Store the SPHN radiopharmaceutical administration event in the data store
        if sphn_radiopharmaceutical_administration_event is not None:
            data_store.add_sphn_radiopharmaceutical_administration_event_to_list(
                sphn_radiopharmaceutical_administration_event=sphn_radiopharmaceutical_administration_event,
                logger=logger,
                indent=indent+4
            )
        else:
            logger.debug(" "*(indent+4) + "No SPHN Radiopharmaceutical Administration Event object to store in the data store")


#
# Edwin 2026-11-13
#
def process_enhanced_radiopharmaceutical_information_sequence_item(dataset: Dataset, dicom_timezone: tzinfo, context: Context, indent: int=0) -> SPHNRadiopharmaceuticalAdministrationEvent|None:
    """
    Process the DICOM enhanced (multi-frame) RadiopharmaceuticalInformationSequence item (Dataset)
    and return an SPHNRadiopharmaceuticalAdministrationEvent object, if any.
    The enhanced module has only coded information and DateTime tags (no free text or time only tags).
    Parameters:
        - dataset: The DICOM enhanced (multi-frame) RadiopharmaceuticalInformationSequence item (Dataset)
        - dicom_timezone: The timezone of the DICOM dates and times (see get_dicom_timezone())
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(dicom_timezone, tzinfo)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger

    # The Radiopharmaceutical Agent Number identifies the item, it is not mapped to SPHN
    radiopharmaceutical_agent_number = get_radiopharmaceutical_agent_number_from_dicom(dataset, context, indent=indent+2)
    logger.debug(" "*(indent+0) + f"DICOM RadiopharmaceuticalAgentNumber: '{radiopharmaceutical_agent_number}'")

    return process_radiopharmaceutical_information_sequence_item(dataset, dicom_timezone, use_free_text=False, context=context, indent=indent)


# ---------------------------------------------------------------------------------------------------------------------
# Functions for processing the Radiopharmaceutical Information Sequence items (legacy and enhanced)
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-11-13
#
def process_radiopharmaceutical_information_sequence_item(
        dataset: Dataset,
        dicom_timezone: tzinfo,
        use_free_text: bool,
        context: Context,
        indent: int=0
    ) -> SPHNRadiopharmaceuticalAdministrationEvent|None:
    """
    Process a DICOM RadiopharmaceuticalInformationSequence item (Dataset), of the legacy or enhanced PET Isotope module,
    and return an SPHNRadiopharmaceuticalAdministrationEvent object, if any.
    Parameters:
        - dataset: The DICOM RadiopharmaceuticalInformationSequence item (Dataset)
        - dicom_timezone: The timezone of the DICOM dates and times (see get_dicom_timezone())
        - use_free_text: Use the free text and time only tags (legacy module) when there is no coded or DateTime information
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(dicom_timezone, tzinfo)
    assert isinstance(use_free_text, bool)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger

    radiopharmaceutical_code: CodeTuple|None = None
    radiopharmaceutical_name: str|None = None
    radionuclide_code: CodeTuple|None = None

    # The free text radiopharmaceutical (legacy module only)
    radiopharmaceutical_str = get_radiopharmaceutical_from_dicom(dataset, context, indent=indent+2) if use_free_text else None

    #
    # 1. The radiopharmaceutical: first the coded information, then the free text
    #

    logger.debug(" "*(indent+0) + "Start processing the DICOM radiopharmaceutical information.")

    # 1.1. The DICOM RadiopharmaceuticalCodeSequence (coded info)
    radiopharmaceutical_code_sequence = get_radiopharmaceutical_code_sequence_from_dicom(dataset, context, indent=indent+2)

    if radiopharmaceutical_code_sequence is not None:
        radiopharmaceutical_code = process_radiopharmaceutical_code_sequence_item(radiopharmaceutical_code_sequence[0], context, indent=indent+2)

    # 1.2. The DICOM Radiopharmaceutical (free text info)
    if radiopharmaceutical_code is None and radiopharmaceutical_str is not None:
        logger.debug(" "*(indent+2) + f"Found DICOM Radiopharmaceutical (free text info) with value: '{radiopharmaceutical_str}'")
        result = process_radiopharmaceutical_free_text(radiopharmaceutical_str, context, indent=indent+2)
        if result is not None:
            radiopharmaceutical_name, radiopharmaceutical_code = result

    # The name (DICOM CID 4021 Code Meaning) of a coded radiopharmaceutical, used to derive the radionuclide if needed
    if radiopharmaceutical_code is not None and radiopharmaceutical_name is None:
        radiopharmaceutical_name = get_pet_radiopharmaceutical_name_from_code(radiopharmaceutical_code)

    logger.debug(" "*(indent+0) + f"Done processing the DICOM radiopharmaceutical information: '{radiopharmaceutical_code}'")

    #
    # 2. The radionuclide: first the coded information, then the free text radiopharmaceutical, then derived from the radiopharmaceutical
    #

    logger.debug(" "*(indent+0) + "Start processing the DICOM radionuclide information.")

    # 2.1. The DICOM RadionuclideCodeSequence (coded info)
    radionuclide_code_sequence = get_radionuclide_code_sequence_from_dicom(dataset, context, indent=indent+2)

    if radionuclide_code_sequence is not None:
        radionuclide_code = process_radionuclide_code_sequence_item(radionuclide_code_sequence[0], context, indent=indent+2)

    # 2.2. The radionuclide in the DICOM Radiopharmaceutical (free text info), e.g. "18F-FDG"
    if radionuclide_code is None and radiopharmaceutical_str is not None:
        radionuclide_code = process_radionuclide_free_text(radiopharmaceutical_str, context, indent=indent+2)

    # 2.3. The radionuclide of the radiopharmaceutical, e.g. "Fluorodeoxyglucose F^18^"
    if radionuclide_code is None and radiopharmaceutical_name is not None:
        logger.debug(" "*(indent+2) + f"Deriving the radionuclide from the radiopharmaceutical: '{radiopharmaceutical_name}'")
        radionuclide_code = process_radionuclide_free_text(normalize_dicom_isotope_notation(radiopharmaceutical_name), context, indent=indent+2)

    logger.debug(" "*(indent+0) + f"Done processing the DICOM radionuclide information: '{radionuclide_code}'")

    if radiopharmaceutical_code is None and radionuclide_code is None:
        logger.debug(" "*(indent+0) + "No radiopharmaceutical and no radionuclide found. No SPHN Radiopharmaceutical Administration Event is created.")
        return None

    #
    # 3. The administration route: first the coded information, then the free text
    #

    logger.debug(" "*(indent+0) + "Start processing the DICOM administration route information.")

    sphn_administration_route_codes: list[SPHNCode] = []

    # 3.1. The DICOM AdministrationRouteCodeSequence (coded info)
    administration_route_code_sequence = get_administration_route_code_sequence_from_dicom(dataset, context, indent=indent+2)

    if administration_route_code_sequence is not None:
        sphn_administration_route_code = process_administration_route_code_sequence_item(administration_route_code_sequence[0], context, indent=indent+2)
        if sphn_administration_route_code is not None:
            sphn_administration_route_codes.append(sphn_administration_route_code)

    # 3.2. The DICOM RadiopharmaceuticalRoute (free text info, legacy module only)
    if len(sphn_administration_route_codes) == 0 and use_free_text:
        route_str = get_radiopharmaceutical_route_from_dicom(dataset, context, indent=indent+2)
        if route_str is not None:
            logger.debug(" "*(indent+2) + f"Found DICOM RadiopharmaceuticalRoute (free text info) with value: '{route_str}'")
            sphn_administration_route_codes = process_radiopharmaceutical_route(route_str, context, indent=indent+2)

    # Only a single administration route can be added to the SPHN Radiopharmaceutical Administration Event
    sphn_administration_route_code_checked: SPHNCode|None = None
    if len(sphn_administration_route_codes) == 1:
        sphn_administration_route_code_checked = sphn_administration_route_codes[0]
    elif len(sphn_administration_route_codes) > 1:
        logger.debug(" "*(indent+2) + f"Multiple administration routes found: '{len(sphn_administration_route_codes)}'. None is used.")

    logger.debug(" "*(indent+0) + "Done processing the DICOM administration route information.")

    #
    # 4. The start and stop datetimes: first the DateTime tags, then the Time only tags (legacy module only)
    #

    logger.debug(" "*(indent+0) + "Start processing the DICOM radiopharmaceutical start and stop datetimes.")

    start_datetime = process_radiopharmaceutical_datetime(
        datetime_str=get_radiopharmaceutical_start_datetime_from_dicom(dataset, context, indent=indent+2),
        time_str=get_radiopharmaceutical_start_time_from_dicom(dataset, context, indent=indent+2) if use_free_text else None,
        dicom_timezone=dicom_timezone,
        context=context,
        indent=indent+2
    )
    start_datetime_from_dicom = start_datetime is not None

    if start_datetime is None:
        logger.debug(" "*(indent+2) + "Radiopharmaceutical start datetime is not available, trying fallback datetimes.")
        start_datetime = get_radiopharmaceutical_datetime_fallback(context, indent=indent+4)

    if start_datetime is None:
        logger.debug(" "*(indent+0) + "No radiopharmaceutical start datetime available. No SPHN Radiopharmaceutical Administration Event is created.")
        return None

    end_datetime = process_radiopharmaceutical_datetime(
        datetime_str=get_radiopharmaceutical_stop_datetime_from_dicom(dataset, context, indent=indent+2),
        time_str=get_radiopharmaceutical_stop_time_from_dicom(dataset, context, indent=indent+2) if use_free_text else None,
        dicom_timezone=dicom_timezone,
        context=context,
        indent=indent+2
    )

    if end_datetime is not None and end_datetime < start_datetime:
        logger.warning(" "*(indent+2) + f"Radiopharmaceutical stop datetime '{end_datetime!s}' is before the start datetime '{start_datetime!s}', it is not used.")
        end_datetime = None

    logger.debug(" "*(indent+0) + f"Done processing the DICOM radiopharmaceutical datetimes: start '{start_datetime!s}', stop '{end_datetime!s}'")

    #
    # 5. The quantities: volume, total dose, half-life and positron fraction
    #

    volume = get_radiopharmaceutical_volume_from_dicom(dataset, context, indent=indent+2)
    total_dose = get_radionuclide_total_dose_from_dicom(dataset, context, indent=indent+2)
    half_life = get_radionuclide_half_life_from_dicom(dataset, context, indent=indent+2)
    positron_fraction = get_radionuclide_positron_fraction_from_dicom(dataset, context, indent=indent+2)

    # Use the half-life and positron fraction of the radionuclide (IAEA/ENSDF data) when not available in DICOM
    if radionuclide_code is not None:
        half_life, positron_fraction = complete_radionuclide_half_life_and_positron_fraction(radionuclide_code, half_life, positron_fraction, context, indent=indent+2)

    # Not mapped to SPHN, only logged
    specific_activity = get_radiopharmaceutical_specific_activity_from_dicom(dataset, context, indent=indent+2)
    administration_event_uid = get_radiopharmaceutical_administration_event_uid_from_dicom(dataset, context, indent=indent+2)
    logger.debug(" "*(indent+0) + f"Not mapped to SPHN: DICOM RadiopharmaceuticalSpecificActivity: '{specific_activity}' Bq/micromole, RadiopharmaceuticalAdministrationEventUID: '{administration_event_uid}'")

    #
    # 6. Create the SPHN objects
    #

    sphn_radionuclide: SPHNRadionuclide|None = None
    if radionuclide_code is not None:
        sphn_radionuclide = create_sphn_radionuclide(
            radionuclide_code=radionuclide_code,
            half_life=half_life,
            positron_fraction=positron_fraction,
            total_dose=total_dose,
            total_dose_datetime=start_datetime if start_datetime_from_dicom else None,
            context=context,
            indent=indent+2
        )

    sphn_radiopharmaceutical = create_sphn_radiopharmaceutical(
        radiopharmaceutical_code=radiopharmaceutical_code,
        sphn_radionuclide=sphn_radionuclide,
        volume=volume,
        context=context,
        indent=indent+2
    )

    if sphn_radiopharmaceutical is None:
        logger.debug(" "*(indent+0) + "Failed to create an SPHN Radiopharmaceutical object. No SPHN Radiopharmaceutical Administration Event is created.")
        return None

    sphn_radiopharmaceutical_administration_event = create_sphn_radiopharmaceutical_administration_event(
        sphn_radiopharmaceutical=sphn_radiopharmaceutical,
        sphn_administration_route_code=sphn_administration_route_code_checked,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        context=context,
        indent=indent+2
    )

    return sphn_radiopharmaceutical_administration_event


#
# Edwin 2026-11-13
#
def process_radiopharmaceutical_code_sequence_item(dataset: Dataset, context: Context, indent: int=0) -> CodeTuple|None:
    """
    Process the DICOM RadiopharmaceuticalCodeSequence item (Dataset) and return the SPHN compatible code tuple, if any.
    The DICOM code (DICOM CID 4021) is mapped with DataConverter.dicom_pet_radiopharmaceuticals_coded_2_sphn_coded.
    Parameters:
        - dataset: The DICOM RadiopharmaceuticalCodeSequence item (Dataset)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    return process_coded_item(dataset, DataConverter.dicom_pet_radiopharmaceuticals_coded_2_sphn_coded, "RadiopharmaceuticalCodeSequence", context, indent=indent)


#
# Edwin 2026-11-13
#
def process_radionuclide_code_sequence_item(dataset: Dataset, context: Context, indent: int=0) -> CodeTuple|None:
    """
    Process the DICOM RadionuclideCodeSequence item (Dataset) and return the SPHN compatible code tuple, if any.
    The DICOM code (DICOM CID 4020) is mapped with DataConverter.dicom_pet_radionuclides_coded_2_sphn_coded.
    Parameters:
        - dataset: The DICOM RadionuclideCodeSequence item (Dataset)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    return process_coded_item(dataset, DataConverter.dicom_pet_radionuclides_coded_2_sphn_coded, "RadionuclideCodeSequence", context, indent=indent)


#
# Edwin 2026-11-13
#
def process_coded_item(dataset: Dataset, mapping: dict[tuple[str, str], CodeTuple], sequence_name: str, context: Context, indent: int=0) -> CodeTuple|None:
    """
    Read the coding scheme designator, code value and code meaning in a DICOM code sequence item (Dataset)
    and map them to an SPHN compatible code tuple with the given mapping dictionary.
    Parameters:
        - dataset: The DICOM code sequence item (Dataset)
        - mapping: The mapping dictionary: (DICOM coding scheme designator, code value) -> (coding scheme designator, code value, description)
        - sequence_name: The name of the DICOM code sequence (for logging)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(mapping, dict)
    assert is_valid_string(sequence_name)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger

    # Get the coded info from DICOM
    coding_scheme_designator = get_coding_scheme_designator_from_dicom(dataset, context, indent=indent+2)
    code_value = get_code_value_from_dicom(dataset, context, indent=indent+2)
    code_descr = get_code_meaning_from_dicom(dataset, context, indent=indent+2)

    if coding_scheme_designator is None or code_value is None:
        logger.debug(" "*(indent+0) + f"DICOM {sequence_name} item has no coding scheme designator or code value")
        return None

    logger.debug(" "*(indent+0) + f"DICOM {sequence_name} item has coding scheme designator '{coding_scheme_designator}' and code value '{code_value}' with description '{code_descr}'")

    # Map the DICOM code to the SPHN compatible code (older DICOM data may use the retired designator "SNM3" instead of "SRT")
    result = mapping.get((get_lookup_coding_scheme_designator(coding_scheme_designator), code_value), None)

    if result is None:
        logger.debug(" "*(indent+0) + f"DICOM {sequence_name} item code '{(coding_scheme_designator, code_value, code_descr)}' could not be mapped to a known code")
        return None

    assert isinstance(result, tuple) and len(result) == 3 and all(is_valid_string(item) for item in result)

    logger.debug(" "*(indent+0) + f"Successfully mapped the DICOM coding: '{(coding_scheme_designator, code_value, code_descr)}' to the coding: '{result}'")

    return result


#
# Edwin 2026-11-13
#
def process_radiopharmaceutical_free_text(radiopharmaceutical_str: str, context: Context, indent: int=0) -> tuple[str, CodeTuple]|None:
    """
    Find the radiopharmaceutical in the DICOM Radiopharmaceutical (free text) string, e.g. "18F-FDG",
    with DataConverter.pet_radiopharmaceutical_names_2_patterns, and return its name and code tuple
    (DataConverter.pet_radiopharmaceutical_name_2_code), if exactly one radiopharmaceutical is found.
    Parameters:
        - radiopharmaceutical_str: The DICOM Radiopharmaceutical (free text) string
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert is_valid_string(radiopharmaceutical_str)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger

    names = find_names_in_free_text(radiopharmaceutical_str, DataConverter.pet_radiopharmaceutical_names_2_patterns)

    if len(names) == 0:
        logger.debug(" "*(indent+0) + f"No radiopharmaceutical found in the free text: '{radiopharmaceutical_str}'")
        return None

    if len(names) > 1:
        logger.debug(" "*(indent+0) + f"Multiple radiopharmaceuticals found in the free text: '{radiopharmaceutical_str}': '{names}'. None is used.")
        return None

    name = names[0]
    code = DataConverter.pet_radiopharmaceutical_name_2_code.get(name, None)
    assert code is not None, f"Radiopharmaceutical '{name}' has no code in DataConverter.pet_radiopharmaceutical_name_2_code"

    logger.debug(" "*(indent+0) + f"Found radiopharmaceutical '{name}' with code '{code}' in the free text: '{radiopharmaceutical_str}'")

    return name, code


#
# Edwin 2026-11-13
#
def process_radionuclide_free_text(text: str, context: Context, indent: int=0) -> CodeTuple|None:
    """
    Find the radionuclide in a (free text) string, e.g. "18F-FDG", with DataConverter.pet_radionuclide_names_2_patterns,
    and return its code tuple (DataConverter.pet_radionuclide_name_2_code), if exactly one radionuclide is found.
    Parameters:
        - text: The (free text) string
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert is_valid_string(text)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger

    names = find_names_in_free_text(text, DataConverter.pet_radionuclide_names_2_patterns)

    if len(names) == 0:
        logger.debug(" "*(indent+0) + f"No radionuclide found in the text: '{text}'")
        return None

    if len(names) > 1:
        logger.debug(" "*(indent+0) + f"Multiple radionuclides found in the text: '{text}': '{names}'. None is used.")
        return None

    name = names[0]
    code = DataConverter.pet_radionuclide_name_2_code.get(name, None)
    assert code is not None, f"Radionuclide '{name}' has no code in DataConverter.pet_radionuclide_name_2_code"

    logger.debug(" "*(indent+0) + f"Found radionuclide '{name}' with code '{code}' in the text: '{text}'")

    return code


#
# Edwin 2026-11-13
#
def process_administration_route_code_sequence_item(dataset: Dataset, context: Context, indent: int=0) -> SPHNCode|None:
    """
    Process the DICOM AdministrationRouteCodeSequence item (Dataset) and return an SPHN Code object for the SPHN hasAdministrationRouteCode, if any.
    The DICOM route code (DICOM CID 11) is mapped with DataConverter.administration_routes_list.
    Parameters:
        - dataset: The DICOM AdministrationRouteCodeSequence item (Dataset)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    route_code = process_coded_item(dataset, DataConverter.administration_routes_list, "AdministrationRouteCodeSequence", context, indent=indent)

    if route_code is None:
        return None

    return create_sphn_code(route_code, context, indent=indent)


#
# Edwin 2026-11-13
#
def process_radiopharmaceutical_route(route_str: str, context: Context, indent: int=0) -> list[SPHNCode]:
    """
    Process the DICOM RadiopharmaceuticalRoute (free text) string and return a list of matched SPHN administration route codes.
    The routes are matched with DataConverter.route_patterns and DataConverter.sphn_route_codes.
    Parameters:
        - route_str: The DICOM RadiopharmaceuticalRoute (free text) string
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert is_valid_string(route_str)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger

    sphn_code_list: list[SPHNCode] = []

    for item_dict in extract_administration_routes_from_text(route_str, logger, indent=indent):
        sphn_code_route = create_sphn_code(item_dict["Code"], context, indent=indent)
        if sphn_code_route is not None and sphn_code_route not in sphn_code_list:
            sphn_code_list.append(sphn_code_route)

    if len(sphn_code_list) == 0:
        logger.debug(" "*(indent+0) + f"No administration route found in the free text: '{route_str}'")

    return sphn_code_list


#
# Edwin 2026-11-13
#
def process_radiopharmaceutical_datetime(
        datetime_str: str|None,
        time_str: str|None,
        dicom_timezone: tzinfo,
        context: Context,
        indent: int=0
    ) -> datetime|None:
    """
    Returns the radiopharmaceutical (start or stop) datetime:
        - first from the DICOM DateTime (DT) tag, e.g. Radiopharmaceutical Start DateTime (0018,1078),
          in the timezone of the DICOM DateTime value if specified, otherwise in the given DICOM timezone,
        - then from the DICOM Time (TM) tag, e.g. Radiopharmaceutical Start Time (0018,1072), completed with the date
          of the acquisition, series or study datetime (in the same way as for the contrast/bolus start and stop times).
    Parameters:
        - datetime_str: The DICOM DateTime (DT) string, if any
        - time_str: The DICOM Time (TM) string, if any
        - dicom_timezone: The timezone of the DICOM dates and times (see get_dicom_timezone())
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert datetime_str is None or is_valid_string(datetime_str)
    assert time_str is None or is_valid_string(time_str)
    assert isinstance(dicom_timezone, tzinfo)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger
    data_store = context.data_store

    # 1. The DICOM DateTime (DT) tag
    if datetime_str is not None:
        result = complete_dicom_datetime(datetime_str, dicom_timezone, logger, indent=indent+2)
        if result is not None:
            logger.debug(" "*(indent+0) + f"Radiopharmaceutical datetime from the DICOM DateTime tag: '{result!s}'")
            return result
        logger.debug(" "*(indent+0) + f"Failed to complete the DICOM DateTime: '{datetime_str}'")

    # 2. The DICOM Time (TM) tag, completed with the date of the acquisition, series or study datetime
    if time_str is not None:
        dicom_time = complete_dicom_time(time_str, logger, indent=indent+2)
        if dicom_time is None:
            logger.debug(" "*(indent+0) + f"Failed to complete the DICOM Time: '{time_str}'")
            return None

        result = combine_dicom_time_with_reference_datetime(
            dicom_time=dicom_time,
            acquisition_datetime=data_store.acquisition_start_datetime,
            series_datetime=data_store.series_start_datetime,
            study_datetime=data_store.study_start_datetime,
            logger=logger,
            indent=indent+2
        )
        if result is not None:
            logger.debug(" "*(indent+0) + f"Radiopharmaceutical datetime from the DICOM Time tag and the acquisition/series/study date: '{result!s}'")
        return result

    return None


#
# Edwin 2026-11-13
#
def get_radiopharmaceutical_datetime_fallback(context: Context, indent: int=0) -> datetime|None:
    """
    Tries to determine a fallback datetime for the radiopharmaceutical start, based on the available Series, Acquisition or Study datetimes.
    Parameters:
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    data_store = context.data_store
    logger = context.logger

    radiopharmaceutical_start_datetime = None

    if data_store.series_start_datetime is not None:
        radiopharmaceutical_start_datetime = data_store.series_start_datetime
        logger.debug(" "*(indent+0) + f"Using DICOM Series start datetime as fallback: {radiopharmaceutical_start_datetime!s}")

    elif data_store.acquisition_start_datetime is not None:
        radiopharmaceutical_start_datetime = data_store.acquisition_start_datetime
        logger.debug(" "*(indent+0) + f"Using DICOM Acquisition start datetime as fallback: {radiopharmaceutical_start_datetime!s}")

    elif data_store.study_start_datetime is not None:
        radiopharmaceutical_start_datetime = data_store.study_start_datetime
        logger.debug(" "*(indent+0) + f"Using DICOM Study start datetime as fallback: {radiopharmaceutical_start_datetime!s}")

    else:
        logger.debug(" "*(indent+0) + "No fallback datetime available for the radiopharmaceutical start.")

    return radiopharmaceutical_start_datetime


#
# Edwin 2026-11-13
#
def complete_radionuclide_half_life_and_positron_fraction(
        radionuclide_code: CodeTuple,
        half_life: float|None,
        positron_fraction: float|None,
        context: Context,
        indent: int=0
    ) -> tuple[float|None, float|None]:
    """
    Returns the half-life and positron fraction of the radionuclide: the DICOM values, if available,
    otherwise those of DataConverter.pet_radionuclide_coded_2_half_life_and_positron_fraction (IAEA/ENSDF data).
    Parameters:
        - radionuclide_code: The code tuple of the radionuclide
        - half_life: The DICOM Radionuclide Half Life [s], if any
        - positron_fraction: The DICOM Radionuclide Positron Fraction, if any
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(radionuclide_code, tuple) and len(radionuclide_code) == 3
    assert half_life is None or isinstance(half_life, float)
    assert positron_fraction is None or isinstance(positron_fraction, float)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger

    reference = DataConverter.pet_radionuclide_coded_2_half_life_and_positron_fraction.get(radionuclide_code[:2], None)

    if reference is None:
        logger.debug(" "*(indent+0) + f"No reference half-life and positron fraction for radionuclide: '{radionuclide_code}'")
        return half_life, positron_fraction

    reference_half_life, reference_positron_fraction = reference

    if half_life is None:
        half_life = reference_half_life
        logger.debug(" "*(indent+0) + f"Using the reference half-life of the radionuclide: '{half_life}' s")
    elif abs(half_life / reference_half_life - 1) > 0.01:
        logger.warning(" "*(indent+0) + f"DICOM RadionuclideHalfLife '{half_life}' s differs more than 1% from the reference value '{reference_half_life}' s for radionuclide: '{radionuclide_code}'")

    if positron_fraction is None:
        positron_fraction = reference_positron_fraction
        logger.debug(" "*(indent+0) + f"Using the reference positron fraction of the radionuclide: '{positron_fraction}'")
    elif abs(positron_fraction - reference_positron_fraction) > 0.01:
        logger.warning(" "*(indent+0) + f"DICOM RadionuclidePositronFraction '{positron_fraction}' differs more than 0.01 from the reference value '{reference_positron_fraction}' for radionuclide: '{radionuclide_code}'")

    return half_life, positron_fraction


# ---------------------------------------------------------------------------------------------------------------------
# Functions for creating SPHN objects
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-11-13
#
def create_sphn_code(code: CodeTuple, context: Context, indent: int=0) -> SPHNCode|None:
    """
    Creates an SPHN Code object from a code tuple (coding scheme designator, code value, description),
    if the coding scheme is implemented in SPHNCode (e.g. not for NCIt, UMLS or MSH codes).
    Parameters:
        - code: The code tuple
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(code, tuple) and len(code) == 3 and all(is_valid_string(item) for item in code)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger

    coding_scheme_designator, code_value, code_descr = code

    if coding_scheme_designator not in CodingSystemList:
        logger.debug(" "*(indent+0) + f"The coding scheme '{coding_scheme_designator}' of code '{code}' is not implemented in SPHN Code, the code is not used.")
        return None

    return SPHNCode(
        sphn_schema = context.sphn_schema,
        has_coding_system_and_version = coding_scheme_designator,
        has_identifier = code_value,
        has_name = code_descr
    )


#
# Edwin 2026-11-13
#
def create_sphn_radionuclide(
        radionuclide_code: CodeTuple,
        half_life: float|None,
        positron_fraction: float|None,
        total_dose: float|None,
        total_dose_datetime: datetime|None,
        context: Context,
        indent: int=0
    ) -> SPHNRadionuclide|None:
    """
    Creates an SPHN Radionuclide object with the provided information.
    Parameters:
        - radionuclide_code: The code tuple of the radionuclide
        - half_life: The half-life [s], if any
        - positron_fraction: The positron fraction [0..1], if any
        - total_dose: The DICOM Radionuclide Total Dose [Bq], if any
        - total_dose_datetime: The datetime of the total dose (the radiopharmaceutical start datetime), if any
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(radionuclide_code, tuple) and len(radionuclide_code) == 3
    assert half_life is None or isinstance(half_life, float)
    assert positron_fraction is None or isinstance(positron_fraction, float)
    assert total_dose is None or isinstance(total_dose, float)
    assert total_dose_datetime is None or isinstance(total_dose_datetime, datetime)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger
    data_store = context.data_store

    sphn_code_radionuclide = create_sphn_code(radionuclide_code, context, indent=indent+2)

    if sphn_code_radionuclide is None:
        logger.debug(" "*(indent+0) + f"Failed to create an SPHN Code for radionuclide: '{radionuclide_code}'")
        return None

    sphn_radioactivity = None
    if total_dose is not None:
        sphn_radioactivity = SPHNRadioactivity(
            sphn_schema = context.sphn_schema,
            has_quantity = create_sphn_quantity_for_radioactivity(total_dose, context, indent=indent+2),
            has_datetime = total_dose_datetime
        )

    sphn_radionuclide = SPHNRadionuclide(
        sphn_schema = context.sphn_schema,
        has_code = sphn_code_radionuclide,
        has_half_life = create_sphn_quantity_for_half_life(half_life, context, indent=indent+2) if half_life is not None else None,
        has_positron_fraction = create_sphn_quantity_for_positron_fraction(positron_fraction, context, indent=indent+2) if positron_fraction is not None else None,
        has_radioactivity = sphn_radioactivity,
        has_source_system_list = [data_store.sphn_source_system]
    )

    logger.debug(" "*(indent+0) + f"Successfully created an SPHN Radionuclide object for: '{radionuclide_code}'")

    return sphn_radionuclide


#
# Edwin 2026-11-13
#
def create_sphn_radiopharmaceutical(
        radiopharmaceutical_code: CodeTuple|None,
        sphn_radionuclide: SPHNRadionuclide|None,
        volume: float|None,
        context: Context,
        indent: int=0
    ) -> SPHNRadiopharmaceutical|None:
    """
    Creates an SPHN Radiopharmaceutical object with the provided information.
    The radiopharmaceutical code is added as active ingredient (SPHN Substance).
    Parameters:
        - radiopharmaceutical_code: The code tuple of the radiopharmaceutical, if any
        - sphn_radionuclide: The SPHN Radionuclide object, if any
        - volume: The DICOM Radiopharmaceutical Volume [mL], if any
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert radiopharmaceutical_code is None or (isinstance(radiopharmaceutical_code, tuple) and len(radiopharmaceutical_code) == 3)
    assert sphn_radionuclide is None or isinstance(sphn_radionuclide, SPHNRadionuclide)
    assert volume is None or isinstance(volume, float)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger
    data_store = context.data_store

    sphn_active_ingredient_list: list[SPHNSubstance]|None = None

    if radiopharmaceutical_code is not None:
        sphn_code_radiopharmaceutical = create_sphn_code(radiopharmaceutical_code, context, indent=indent+2)
        if sphn_code_radiopharmaceutical is not None:
            sphn_active_ingredient_list = [SPHNSubstance(
                sphn_schema = context.sphn_schema,
                has_code = sphn_code_radiopharmaceutical,
                has_source_system_list = [data_store.sphn_source_system]
            )]

    if sphn_active_ingredient_list is None and sphn_radionuclide is None:
        logger.debug(" "*(indent+0) + "No active ingredient and no radionuclide available for the SPHN Radiopharmaceutical object")
        return None

    sphn_radiopharmaceutical = SPHNRadiopharmaceutical(
        sphn_schema = context.sphn_schema,
        has_active_ingredient_list = sphn_active_ingredient_list,
        has_radionuclide = sphn_radionuclide,
        has_quantity = create_sphn_quantity_for_volume(volume, context, indent=indent+2) if volume is not None else None,
        has_source_system_list = [data_store.sphn_source_system]
    )

    logger.debug(" "*(indent+0) + "Successfully created an SPHN Radiopharmaceutical object")

    return sphn_radiopharmaceutical


#
# Edwin 2026-11-13
#
def create_sphn_radiopharmaceutical_administration_event(
        sphn_radiopharmaceutical: SPHNRadiopharmaceutical,
        sphn_administration_route_code: SPHNCode|None,
        start_datetime: datetime,
        end_datetime: datetime|None,
        context: Context,
        indent: int=0
    ) -> SPHNRadiopharmaceuticalAdministrationEvent:
    """
    Creates an SPHN Radiopharmaceutical Administration Event object with the provided information.
    Parameters:
        - sphn_radiopharmaceutical: The SPHN Radiopharmaceutical object
        - sphn_administration_route_code: The SPHN administration route code, if any
        - start_datetime: The start date and time of the administration event
        - end_datetime: The end date and time of the administration event, if any
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(sphn_radiopharmaceutical, SPHNRadiopharmaceutical)
    assert sphn_administration_route_code is None or isinstance(sphn_administration_route_code, SPHNCode)
    assert isinstance(start_datetime, datetime)
    assert end_datetime is None or isinstance(end_datetime, datetime)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger
    data_store = context.data_store

    logger.debug(" "*(indent+0) + "Start creating an SPHN Radiopharmaceutical Administration Event object...")

    sphn_radiopharmaceutical_administration_event = SPHNRadiopharmaceuticalAdministrationEvent(
        sphn_schema = context.sphn_schema,
        has_start_datetime = start_datetime,
        has_end_datetime = end_datetime,
        has_drug = sphn_radiopharmaceutical,
        has_administration_route_code = sphn_administration_route_code,
        has_subject_pseudo_identifier = data_store.sphn_subject_pseudo_identifier,
        has_source_system_list = [data_store.sphn_source_system]
    )

    logger.debug(" "*(indent+0) + "Done  creating SPHN Radiopharmaceutical Administration Event object.")

    return sphn_radiopharmaceutical_administration_event


#
# Edwin 2026-11-13
#
def create_sphn_quantity(value: float, ucum_code: str, context: Context) -> SPHNQuantity:
    """
    Creates an SPHN Quantity object with the value and the SPHN UCUM unit code.
    Parameters:
        - value: The value
        - ucum_code: The SPHN UCUM unit code, e.g. "s", "MBq", "mL", "cblfractioncbr" (for "{fraction}")
        - context: The Context object that holds the data_store, logger and other relevant information
    """

    # Check
    assert isinstance(value, float)
    assert is_valid_string(ucum_code)
    assert isinstance(context, Context)

    sphn_schema = context.sphn_schema

    sphn_code_ucum = SPHNCode(
        sphn_schema = sphn_schema,
        has_identifier = ucum_code,
        has_coding_system_and_version = "UCUM"
    )
    sphn_unit = SPHNUnit(
        sphn_schema = sphn_schema,
        has_code = sphn_code_ucum
    )
    return SPHNQuantity(
        sphn_schema = sphn_schema,
        has_value = value,
        has_unit = sphn_unit
    )


#
# Edwin 2026-11-13
#
def create_sphn_quantity_for_half_life(half_life: float, context: Context, indent: int=0) -> SPHNQuantity:
    """
    Creates the SPHN Quantity object for the radionuclide half-life [s] and returns it.
    Parameters:
        - half_life: The half-life in seconds
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """
    assert isinstance(half_life, float)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    return create_sphn_quantity(half_life, "s", context)  # SPHN UCUM unit code, label: "s", comment: "second"


#
# Edwin 2026-11-13
#
def create_sphn_quantity_for_positron_fraction(positron_fraction: float, context: Context, indent: int=0) -> SPHNQuantity:
    """
    Creates the SPHN Quantity object for the radionuclide positron fraction [0..1] and returns it.
    Parameters:
        - positron_fraction: The positron fraction
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """
    assert isinstance(positron_fraction, float)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    return create_sphn_quantity(positron_fraction, "cblfractioncbr", context)  # SPHN UCUM unit code, label: "{fraction}"


#
# Edwin 2026-11-13
#
def create_sphn_quantity_for_radioactivity(total_dose: float, context: Context, indent: int=0) -> SPHNQuantity:
    """
    Creates the SPHN Quantity object for the radioactivity [MBq] and returns it.
    Parameters:
        - total_dose: The DICOM Radionuclide Total Dose in Bq (converted to MBq)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """
    assert isinstance(total_dose, float)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    return create_sphn_quantity(total_dose / 1e6, "MBq", context)  # SPHN UCUM unit code, label: "MBq", comment: "megabecquerel"


#
# Edwin 2026-11-13
#
def create_sphn_quantity_for_volume(volume: float, context: Context, indent: int=0) -> SPHNQuantity:
    """
    Creates the SPHN Quantity object for the radiopharmaceutical volume [mL] and returns it.
    Parameters:
        - volume: The DICOM Radiopharmaceutical Volume in mL
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """
    assert isinstance(volume, float)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    return create_sphn_quantity(volume, "mL", context)  # SPHN UCUM unit code, label: "mL", comment: "milliliter"


# ---------------------------------------------------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-11-13
#
def find_names_in_free_text(text: str, names_2_patterns: dict[str, str]) -> list[str]:
    """
    Returns the names (keys) of the regex patterns (compiled with re.IGNORECASE) that match the (free) text.
    Parameters:
        - text: The (free) text
        - names_2_patterns: The dictionary mapping the names to regex patterns, e.g. DataConverter.pet_radiopharmaceutical_names_2_patterns
    """

    # Check
    assert isinstance(text, str)
    assert isinstance(names_2_patterns, dict)

    return [name for name, pattern in names_2_patterns.items() if re.search(pattern, text, re.IGNORECASE)]


#
# Edwin 2026-11-13
#
def normalize_dicom_isotope_notation(text: str) -> str:
    """
    Converts the DICOM isotope notation in a Code Meaning to a common notation, e.g.:
        - "Fluorodeoxyglucose F^18^" -> "Fluorodeoxyglucose F-18"
        - "DPA-713 ^11^C" -> "DPA-713 11C"
    Parameters:
        - text: The text with DICOM isotope notation(s)
    """

    # Check
    assert isinstance(text, str)

    text = re.sub(r"\^(\d+m?)\^([A-Z][a-z]?)", r"\1\2", text)  # "^11^C" -> "11C"
    text = re.sub(r"([A-Z][a-z]?)\^(\d+m?)\^", r"\1-\2", text)  # "F^18^" -> "F-18"
    return text


#
# Edwin 2026-11-13
#
def get_pet_radiopharmaceutical_name_from_code(radiopharmaceutical_code: CodeTuple) -> str|None:
    """
    Returns the name (DICOM CID 4021 Code Meaning) of the radiopharmaceutical with the given code tuple
    in DataConverter.pet_radiopharmaceutical_name_2_code, if any.
    Parameters:
        - radiopharmaceutical_code: The code tuple of the radiopharmaceutical
    """

    # Check
    assert isinstance(radiopharmaceutical_code, tuple) and len(radiopharmaceutical_code) == 3

    for name, code in DataConverter.pet_radiopharmaceutical_name_2_code.items():
        if code == radiopharmaceutical_code:
            return name
    return None


# ---------------------------------------------------------------------------------------------------------------------
# Functions for reading DICOM tags in the Legacy (single-frame) and Enhanced (multi-frame) PET Isotope module
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-11-13
#
def get_radiopharmaceutical_information_sequence_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence (list of Datasets) in the DICOM RadiopharmaceuticalInformationSequence tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0054,0016)
    # Type:	                Required, Empty if Unknown (2) / Required (1)
    # Keyword:	            RadiopharmaceuticalInformationSequence
    # Value Multiplicity	1
    # Value Representation:	Sequence (SQ)

    # Note: The Type is:
    # - Required, Empty if Unknown (2) for the legacy (single-frame) PET Isotope module and
    # - Required (1) for the enhanced (multi-frame) PET Isotope module

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM RadiopharmaceuticalInformationSequence tag
    value = dataset.get("RadiopharmaceuticalInformationSequence", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM RadiopharmaceuticalInformationSequence tag was not found")
        return None

    assert isinstance(value, Sequence)

    if len(value) == 0:
        logger.debug(" "*(indent+0) + "DICOM RadiopharmaceuticalInformationSequence tag is empty")
        return None

    return value


#
# Edwin 2026-11-13
#
def get_radiopharmaceutical_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM Radiopharmaceutical tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,0031)
    # Type:	                Optional (3)
    # Keyword:	            Radiopharmaceutical
    # Value Multiplicity	1
    # Value Representation:	Long String (LO)

    # Note: Only in the legacy (single-frame) PET Isotope module

    return get_string_from_dicom(dataset, "Radiopharmaceutical", context, indent=indent)


#
# Edwin 2026-11-13
#
def get_radiopharmaceutical_route_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM RadiopharmaceuticalRoute tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1070)
    # Type:	                Optional (3)
    # Keyword:	            RadiopharmaceuticalRoute
    # Value Multiplicity	1
    # Value Representation:	Long String (LO)

    # Note: Only in the legacy (single-frame) PET Isotope module

    return get_string_from_dicom(dataset, "RadiopharmaceuticalRoute", context, indent=indent)


#
# Edwin 2026-11-13
#
def get_radiopharmaceutical_start_time_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM RadiopharmaceuticalStartTime tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1072)
    # Type:	                Optional (3)
    # Keyword:	            RadiopharmaceuticalStartTime
    # Value Multiplicity	1
    # Value Representation:	Time (TM)

    # Note: Only in the legacy (single-frame) PET Isotope module.
    # The DICOM time format is specified in the DICOM standard as Time (TM) in:
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part05/sect_6.2.html

    return get_string_from_dicom(dataset, "RadiopharmaceuticalStartTime", context, indent=indent)


#
# Edwin 2026-11-13
#
def get_radiopharmaceutical_stop_time_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM RadiopharmaceuticalStopTime tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1073)
    # Type:	                Optional (3)
    # Keyword:	            RadiopharmaceuticalStopTime
    # Value Multiplicity	1
    # Value Representation:	Time (TM)

    # Note: Only in the legacy (single-frame) PET Isotope module

    return get_string_from_dicom(dataset, "RadiopharmaceuticalStopTime", context, indent=indent)


#
# Edwin 2026-11-13
#
def get_radiopharmaceutical_start_datetime_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM RadiopharmaceuticalStartDateTime tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1078)
    # Type:	                Optional (3) / Required (1)
    # Keyword:	            RadiopharmaceuticalStartDateTime
    # Value Multiplicity	1
    # Value Representation:	Date Time (DT)

    # Note: The Type is Optional (3) in the legacy and Required (1) in the enhanced PET Isotope module.
    # The DICOM datetime format is specified in the DICOM standard as Date Time (DT) in:
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part05/sect_6.2.html

    return get_string_from_dicom(dataset, "RadiopharmaceuticalStartDateTime", context, indent=indent)


#
# Edwin 2026-11-13
#
def get_radiopharmaceutical_stop_datetime_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM RadiopharmaceuticalStopDateTime tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1079)
    # Type:	                Optional (3)
    # Keyword:	            RadiopharmaceuticalStopDateTime
    # Value Multiplicity	1
    # Value Representation:	Date Time (DT)

    return get_string_from_dicom(dataset, "RadiopharmaceuticalStopDateTime", context, indent=indent)


#
# Edwin 2026-11-13
#
def get_radiopharmaceutical_administration_event_uid_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM RadiopharmaceuticalAdministrationEventUID tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0008,3012)
    # Type:	                Optional (3)
    # Keyword:	            RadiopharmaceuticalAdministrationEventUID
    # Value Multiplicity	1
    # Value Representation:	Unique Identifier (UI)

    return get_string_from_dicom(dataset, "RadiopharmaceuticalAdministrationEventUID", context, indent=indent)


#
# Edwin 2026-11-13
#
def get_radiopharmaceutical_volume_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the float corresponding to the value of the DICOM RadiopharmaceuticalVolume tag [mL]
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1071)
    # Type:	                Optional (3)
    # Keyword:	            RadiopharmaceuticalVolume
    # Value Multiplicity	1
    # Value Representation:	Decimal String (DS)
    # Unit:                 milliliter (mL)

    return get_positive_float_from_dicom(dataset, "RadiopharmaceuticalVolume", context, indent=indent)


#
# Edwin 2026-11-13
#
def get_radionuclide_total_dose_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the float corresponding to the value of the DICOM RadionuclideTotalDose tag [Bq]
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1074)
    # Type:	                Optional (3) / Required, Empty if Unknown (2)
    # Keyword:	            RadionuclideTotalDose
    # Value Multiplicity	1
    # Value Representation:	Decimal String (DS)
    # Unit:                 becquerel (Bq), measured at the Radiopharmaceutical Start (Date)Time

    logger = context.logger

    total_dose = get_positive_float_from_dicom(dataset, "RadionuclideTotalDose", context, indent=indent)

    # Some systems store the dose in MBq instead of Bq: a value below 100 kBq is not a realistic PET dose in Bq
    if total_dose is not None and total_dose < 1e5:
        logger.warning(" "*(indent+0) + f"DICOM RadionuclideTotalDose: '{total_dose}' Bq is not a realistic value (probably not in Bq), it is not used.")
        return None

    return total_dose


#
# Edwin 2026-11-13
#
def get_radionuclide_half_life_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the float corresponding to the value of the DICOM RadionuclideHalfLife tag [s]
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1075)
    # Type:	                Optional (3) / Required (1)
    # Keyword:	            RadionuclideHalfLife
    # Value Multiplicity	1
    # Value Representation:	Decimal String (DS)
    # Unit:                 seconds (s)

    return get_positive_float_from_dicom(dataset, "RadionuclideHalfLife", context, indent=indent, allow_zero=False)


#
# Edwin 2026-11-13
#
def get_radionuclide_positron_fraction_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the float corresponding to the value of the DICOM RadionuclidePositronFraction tag [0..1]
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1076)
    # Type:	                Optional (3) / Required (1)
    # Keyword:	            RadionuclidePositronFraction
    # Value Multiplicity	1
    # Value Representation:	Decimal String (DS)
    # Unit:                 fraction (0..1)

    logger = context.logger

    positron_fraction = get_positive_float_from_dicom(dataset, "RadionuclidePositronFraction", context, indent=indent)

    if positron_fraction is not None and positron_fraction > 1:
        logger.warning(" "*(indent+0) + f"DICOM RadionuclidePositronFraction: '{positron_fraction}' is not a fraction (0..1), it is not used.")
        return None

    return positron_fraction


#
# Edwin 2026-11-13
#
def get_radiopharmaceutical_specific_activity_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the float corresponding to the value of the DICOM RadiopharmaceuticalSpecificActivity tag [Bq/micromole]
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1077)
    # Type:	                Optional (3)
    # Keyword:	            RadiopharmaceuticalSpecificActivity
    # Value Multiplicity	1
    # Value Representation:	Decimal String (DS)
    # Unit:                 becquerel per micromole (Bq/micromole)

    return get_positive_float_from_dicom(dataset, "RadiopharmaceuticalSpecificActivity", context, indent=indent)


#
# Edwin 2026-11-13
#
def get_radiopharmaceutical_agent_number_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> int|None:
    """
    Returns the value corresponding to the value of the DICOM RadiopharmaceuticalAgentNumber tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,9729)
    # Type:	                Required (1)
    # Keyword:	            RadiopharmaceuticalAgentNumber
    # Value Multiplicity	1
    # Value Representation:	Unsigned Short (US)

    # Note: Only in the enhanced (multi-frame) PET Isotope module

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM RadiopharmaceuticalAgentNumber tag
    value = dataset.get("RadiopharmaceuticalAgentNumber", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM RadiopharmaceuticalAgentNumber tag was not found")
        return None

    # Convert value to int
    try:
        value_int = int(value)
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM RadiopharmaceuticalAgentNumber tag value could not be converted to int")
        return None

    if value_int <= 0:
        logger.warning(" "*(indent+0) + f"DICOM RadiopharmaceuticalAgentNumber: '{value_int}' is not a valid value.")
        return None

    return value_int


#
# Edwin 2026-11-13
#
def get_radionuclide_code_sequence_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence (list of Datasets) in the DICOM RadionuclideCodeSequence tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0054,0300)
    # Type:	                Required, Empty if Unknown (2) / Required (1)
    # Keyword:	            RadionuclideCodeSequence
    # Value Multiplicity	1
    # Value Representation:	Sequence (SQ)

    # Note: Only a single item shall be included in this sequence (DICOM CID 4020 "PET Radionuclide")

    return get_code_sequence_from_dicom(dataset, "RadionuclideCodeSequence", context, indent=indent)


#
# Edwin 2026-11-13
#
def get_administration_route_code_sequence_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence (list of Datasets) in the DICOM AdministrationRouteCodeSequence tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0054,0302)
    # Type:	                Optional (3) / Required (1)
    # Keyword:	            AdministrationRouteCodeSequence
    # Value Multiplicity	1
    # Value Representation:	Sequence (SQ)

    # Note: Only a single item shall be included in this sequence (DICOM CID 11 "Route of Administration")

    return get_code_sequence_from_dicom(dataset, "AdministrationRouteCodeSequence", context, indent=indent)


#
# Edwin 2026-11-13
#
def get_radiopharmaceutical_code_sequence_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence (list of Datasets) in the DICOM RadiopharmaceuticalCodeSequence tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0054,0304)
    # Type:	                Optional (3) / Required (1)
    # Keyword:	            RadiopharmaceuticalCodeSequence
    # Value Multiplicity	1
    # Value Representation:	Sequence (SQ)

    # Note: Only a single item shall be included in this sequence (DICOM CID 4021 "PET Radiopharmaceutical")

    return get_code_sequence_from_dicom(dataset, "RadiopharmaceuticalCodeSequence", context, indent=indent)


# ---------------------------------------------------------------------------------------------------------------------
# Generic functions for reading DICOM tags
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-11-13
#
def get_string_from_dicom(dataset: Dataset, keyword: str, context: Context, indent: int=0) -> str|None:
    """
    Returns the (stripped, non-empty) string corresponding to the value of the DICOM tag with the given keyword
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - keyword: The DICOM keyword of the tag, e.g. "Radiopharmaceutical"
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert is_valid_string(keyword)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM tag
    value = dataset.get(keyword, None)

    if value is None:
        logger.debug(" "*(indent+0) + f"DICOM {keyword} tag was not found")
        return None

    # Convert a possible DICOM TM/DT/UID object to a string representation and remove leading/trailing whitespace
    value_str = str(value).strip()

    # Check if value is not empty
    if len(value_str) == 0:
        logger.debug(" "*(indent+0) + f"DICOM {keyword} tag value contains only whitespace")
        return None

    assert is_valid_string(value_str)

    return value_str


#
# Edwin 2026-11-13
#
def get_positive_float_from_dicom(dataset: Dataset, keyword: str, context: Context, indent: int=0, allow_zero: bool=True) -> float|None:
    """
    Returns the (non-negative) float corresponding to the value of the DICOM Decimal String (DS) tag with the given keyword
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - keyword: The DICOM keyword of the tag, e.g. "RadionuclideTotalDose"
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
        - allow_zero: Whether a value of zero is valid (default is True)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert is_valid_string(keyword)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0
    assert isinstance(allow_zero, bool)

    logger = context.logger

    # Get the value of the DICOM tag
    value = dataset.get(keyword, None)

    if value is None or str(value).strip() == "":
        logger.debug(" "*(indent+0) + f"DICOM {keyword} tag was not found or empty")
        return None

    # Convert value to float
    try:
        value_float = float(value)
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + f"DICOM {keyword} tag value could not be converted to float")
        return None

    if value_float < 0 or (value_float == 0 and not allow_zero):
        logger.warning(" "*(indent+0) + f"DICOM {keyword}: '{value_float}' is probably not a valid value.")
        return None

    return value_float


#
# Edwin 2026-11-13
#
def get_code_sequence_from_dicom(dataset: Dataset, keyword: str, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence (list of Datasets) in the DICOM code sequence tag with the given keyword, if it is not empty.
    These code sequences shall contain only a single item: when there are more, a warning is logged.
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - keyword: The DICOM keyword of the code sequence tag, e.g. "RadionuclideCodeSequence"
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert is_valid_string(keyword)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM code sequence tag
    value = dataset.get(keyword, None)

    if value is None:
        logger.debug(" "*(indent+0) + f"DICOM {keyword} tag was not found")
        return None

    assert isinstance(value, Sequence)

    if len(value) == 0:
        logger.debug(" "*(indent+0) + f"DICOM {keyword} tag is empty")
        return None

    if len(value) > 1:
        logger.warning(" "*(indent+0) + f"DICOM {keyword} tag has '{len(value)}' items, only a single item is allowed. Only the first item is used.")

    return value
