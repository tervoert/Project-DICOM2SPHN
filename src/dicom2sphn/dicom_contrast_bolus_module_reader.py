"""
dicom_contrast_bolus_module_reader.py:
    Part of the example dicom2sphn package.
    It contains functions for reading DICOM contrast bolus tags.
"""
from collections.abc import Callable
from datetime import datetime

from pydicom import Dataset
from pydicom.multival import MultiValue
from pydicom.sequence import Sequence

from .context import Context
from .data_converter import DataConverter
from .dicom_code_sequence_tags_reader import (
    get_code_meaning_from_dicom,
    get_code_value_from_dicom,
    get_coding_scheme_designator_from_dicom,
)
from .extract_contrast_agents import extract_contrast_agents
from .sphn_concepts.sphn_code import SPHNCode
from .sphn_concepts.sphn_contrast_agent import SPHNContrastAgent
from .sphn_concepts.sphn_contrast_agent_active_ingredient import (
    SPHNContrastAgentActiveIngredient,
)
from .sphn_concepts.sphn_contrast_agent_administration_event import (
    SPHNContrastAgentAdministrationEvent,
)
from .sphn_concepts.sphn_drug_article import SPHNDrugArticle
from .sphn_concepts.sphn_flow_profile_interval import SPHNFlowProfileInterval
from .sphn_concepts.sphn_quantity import SPHNQuantity
from .sphn_concepts.sphn_unit import SPHNUnit
from .tools import (
    combine_dicom_time_with_reference_datetime,
    complete_dicom_time,
    extract_administration_routes_from_text,
    get_lookup_coding_scheme_designator,
    is_valid_string,
)

type CodeTuple = tuple[str, str, str]  # (coding scheme designator, code value, description) as used in the DataConverter dictionaries

# The general SNOMED CT code used when contrast agent was administered, but the contrast agent itself is unknown
CONTRAST_MEDIA_CODE: CodeTuple = ("SNOMED", "385420005", "| Contrast media (substance) |")

#
# DICOM defines two modules for contrast bolus information:
#
# - The "Contrast/Bolus" module
#   - Used by legacy (single-frame) DICOM objects, such as CT, MR, and XA images.
#   - Table C.7-12. Contrast/Bolus Module Attributes
#   - Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.4.html#table_C.7-12
#
# - The "Enhanced Contrast/Bolus" module
#   - Used by enhanced (multi-frame) DICOM objects, such as Enhanced CT, Enhanced MR, and Enhanced XA images.
#   - Table C.7-12b. Enhanced Contrast/Bolus Module Attributes
#   - Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.4b.html#table_C.7-12b
#
# - Checking for the presence of a "Contrast/Bolus" or an "Enhanced Contrast/Bolus" module in the DICOM dataset
#   - The legacy (single-frame) Contrast/Bolus module:
#       - has a mandatory "Contrast/Bolus Agent Attribute (0018,0010)" tag in case contrast agent was present. The tag can be empty however.
#       - describes a single contrast bolus at the top level of the dataset, with free text tags and time only tags.
#   - The enhanced (multi-frame) Contrast/Bolus module:
#       - has a mandatory "Contrast/Bolus Agent Number Attribute (0018,9337)" tag in each item of the "Contrast/Bolus Agent Sequence Attribute (0018,0012)".
#       - doesn't have the "Contrast/Bolus Agent Attribute (0018,0010)" tag.
#       - describes each contrast agent in its own item of the Contrast/Bolus Agent Sequence, with only coded information.
#
# - Mapping of the DICOM contrast/bolus information to the SPHN schema:
#   - SPHN Contrast Agent Administration Event
#       - has start datetime:               Contrast/Bolus Start Time (0018,1042), completed with the acquisition/series/study date
#                                           (enhanced: the earliest start time in the Contrast Administration Profile Sequence (0018,9340))
#       - has end datetime:                 Contrast/Bolus Stop Time (0018,1043), completed in the same way
#                                           (enhanced: the latest stop time in the Contrast Administration Profile Sequence (0018,9340))
#       - has administration route code:    Contrast/Bolus Administration Route Sequence (0018,0014) or Contrast/Bolus Route (0018,1040)
#       - has flow profile interval:        legacy: the Contrast Flow Rate (0018,1046) and Contrast Flow Duration (0018,1047) values
#                                           enhanced: the items of the Contrast Administration Profile Sequence (0018,9340)
#       - has drug: SPHN Contrast Agent
#           - has active ingredient:        Contrast/Bolus Agent Sequence (0018,0012) or Contrast/Bolus Agent (0018,0010),
#                                           Contrast/Bolus Ingredient (0018,1048) or Contrast/Bolus Ingredient Code Sequence (0018,9338)
#               - has quantity:             Contrast/Bolus Total Dose (0018,1044) [mL undiluted] (legacy only)
#               - has concentration:        Contrast/Bolus Ingredient Concentration (0018,1049) [mg/mL]
#               - has volume percentage:    Contrast/Bolus Ingredient Percent by Volume (0052,0001) [%] (enhanced only)
#           - has article:                  the trade name in the Contrast/Bolus Agent (0018,0010) free text, e.g. "Omnipaque-300 100ml"
#           - has quantity:                 Contrast/Bolus Volume (0018,1041) [mL diluted]
#   - Not mapped to SPHN (only read and logged): Contrast/Bolus Agent Number (0018,9337),
#     Contrast/Bolus Ingredient Opaque (0018,9425) and Contrast/Bolus T1 Relaxivity (0018,0013).

# ---------------------------------------------------------------------------------------------------------------------
# Functions for processing the Legacy/Enhanced "Contrast/Bolus" module
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-11-11
#
def process_dicom_contrast_information(dataset: Dataset, context: Context, indent: int=0) -> None:
    """
    Processes the DICOM Contrast/Bolus information, either legacy (single-frame) or enhanced (multi-frame),
    and stores contrast agent administration events in the data_store.
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

    # Check if the dataset contains the legacy (single-frame) Contrast/Bolus module or the enhanced (multi-frame) Contrast/Bolus module
    has_legacy_contrast_bolus_module = hasattr(dataset, "ContrastBolusAgent")

    contrast_bolus_agent_sequence = dataset.get("ContrastBolusAgentSequence", None)
    assert contrast_bolus_agent_sequence is None or isinstance(contrast_bolus_agent_sequence, Sequence)
    has_enhanced_contrast_bolus_module = contrast_bolus_agent_sequence is not None \
        and all(hasattr(item, "ContrastBolusAgentNumber") for item in contrast_bolus_agent_sequence)

    if not has_legacy_contrast_bolus_module and not has_enhanced_contrast_bolus_module:
        logger.debug(" "*(indent+0) + "No DICOM (legacy or enhanced) Contrast/Bolus module found in the dataset.")
        return

    elif has_legacy_contrast_bolus_module and not has_enhanced_contrast_bolus_module:
        logger.debug(" "*(indent+0) + "Found DICOM legacy (single-frame) Contrast/Bolus module.")
        process_legacy_contrast_bolus_module_from_dicom(dataset, context, indent=indent+2)

    elif has_enhanced_contrast_bolus_module and not has_legacy_contrast_bolus_module:
        logger.debug(" "*(indent+0) + "Found DICOM enhanced (multi-frame) Contrast/Bolus module.")
        process_enhanced_contrast_bolus_module_from_dicom(dataset, context, indent=indent+2)

    else:
        raise ValueError("This should not happen: Found both DICOM legacy (single-frame) and enhanced (multi-frame) Contrast/Bolus modules.")


# ---------------------------------------------------------------------------------------------------------------------
# Functions for processing the Legacy (single-frame) "Contrast/Bolus" module
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-11-13
#
def process_legacy_contrast_bolus_module_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> None:
    """
    Processes the DICOM legacy (single-frame) Contrast/Bolus Module information
    and stores contrast agent administration events in the data_store.
    The legacy module describes a single contrast bolus, which may contain one or more contrast agents:
        - With one contrast agent, all information is added to its administration event.
        - With multiple contrast agents, an administration event is created for each contrast agent, with only the start and stop datetimes,
          as it is unknown to which contrast agent the other information (route, volume, dose and flow) belongs.
        - Without a contrast agent, but with an administration route and a start datetime, an administration event is created
          for a general "Contrast media" contrast agent.
    Parameters:
        - dataset: The DICOM Dataset containing the legacy (single-frame) Contrast/Bolus Module
        - context: The Context object that holds the data_store, logger, and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger
    data_store = context.data_store

    #
    # 1. The contrast agents: first the coded information, then the free text
    #

    logger.debug(" "*(indent+0) + "Start processing the DICOM contrast agent information.")

    sphn_contrast_agent_list = process_legacy_contrast_bolus_agents(dataset, context, indent=indent+2)

    logger.debug(" "*(indent+0) + f"Done processing the DICOM contrast agent information. Found: '{len(sphn_contrast_agent_list)}' SPHN Contrast Agent object(s)")

    #
    # 2. The contrast ingredient (free text) and its concentration
    #

    logger.debug(" "*(indent+0) + "Start processing the DICOM contrast ingredient information.")

    sphn_contrast_agent_list = process_legacy_contrast_bolus_ingredient(dataset, sphn_contrast_agent_list, context, indent=indent+2)

    logger.debug(" "*(indent+0) + "Done processing the DICOM contrast ingredient information.")

    #
    # 3. The administration route: first the coded information, then the free text
    #

    logger.debug(" "*(indent+0) + "Start processing the DICOM administration route information.")

    sphn_administration_route_code = process_contrast_bolus_administration_route(dataset, use_free_text=True, context=context, indent=indent+2)

    logger.debug(" "*(indent+0) + "Done processing the DICOM administration route information.")

    #
    # 4. The start and stop datetimes: the time only tags, completed with the acquisition, series or study date
    #

    logger.debug(" "*(indent+0) + "Start processing the DICOM contrast/bolus start and stop datetimes.")

    start_datetime = process_contrast_bolus_time(get_contrast_bolus_start_time_from_dicom(dataset, context, indent=indent+2), context, indent=indent+2)

    if start_datetime is None:
        logger.debug(" "*(indent+2) + "Contrast/bolus start datetime is not available, trying fallback datetimes.")
        # ToDo: Edwin: Search other hospital databases for contrast/bolus start time information.
        start_datetime = get_contrast_bolus_datetime_fallback(context, indent=indent+4)

    if start_datetime is None:
        logger.debug(" "*(indent+0) + "No contrast/bolus start datetime available. No SPHN Contrast Agent Administration Event is created.")
        return

    end_datetime = process_contrast_bolus_time(get_contrast_bolus_stop_time_from_dicom(dataset, context, indent=indent+2), context, indent=indent+2)

    if end_datetime is not None and end_datetime < start_datetime:
        logger.warning(" "*(indent+2) + f"Contrast/bolus stop datetime '{end_datetime!s}' is before the start datetime '{start_datetime!s}', it is not used.")
        end_datetime = None

    logger.debug(" "*(indent+0) + f"Done processing the DICOM contrast/bolus datetimes: start '{start_datetime!s}', stop '{end_datetime!s}'")

    #
    # 5. Create the SPHN Contrast Agent Administration Event(s)
    #

    sphn_contrast_agent_administration_event_list: list[SPHNContrastAgentAdministrationEvent] = []

    # 5.1. No contrast agent: only with an administration route and a start datetime that is not the configured fallback datetime,
    #      for a general "Contrast media" contrast agent (the SPHN schema requires a contrast agent)
    if len(sphn_contrast_agent_list) == 0:

        if sphn_administration_route_code is None or start_datetime == data_store.fallback_contrast_agent_datetime:
            logger.debug(" "*(indent+0) + "No contrast agent found. No SPHN Contrast Agent Administration Event is created.")
            return

        logger.debug(" "*(indent+0) + "No contrast agent found, but an administration route and a start datetime. Using a general 'Contrast media' contrast agent.")

        sphn_contrast_agent = create_sphn_contrast_agent(
            active_ingredient_list=[create_sphn_contrast_agent_active_ingredient(CONTRAST_MEDIA_CODE, context, indent=indent+2)],
            article=None,
            context=context,
            indent=indent+2
        )

        sphn_contrast_agent_administration_event_list.append(create_sphn_contrast_agent_administration_event(
            sphn_contrast_agent=sphn_contrast_agent,
            sphn_administration_route_code=sphn_administration_route_code,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            sphn_flow_profile_interval_list=None,
            context=context,
            indent=indent+2
        ))

    # 5.2. A single contrast agent: add the volume, the total dose and the flow profile
    elif len(sphn_contrast_agent_list) == 1:

        logger.debug(" "*(indent+0) + "Single contrast agent found.")

        sphn_contrast_agent = sphn_contrast_agent_list[0]

        process_legacy_contrast_bolus_volume_and_total_dose(dataset, sphn_contrast_agent, context, indent=indent+2)

        sphn_flow_profile_interval_list = process_legacy_contrast_flow_profile(dataset, context, indent=indent+2)

        sphn_contrast_agent_administration_event_list.append(create_sphn_contrast_agent_administration_event(
            sphn_contrast_agent=sphn_contrast_agent,
            sphn_administration_route_code=sphn_administration_route_code,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            sphn_flow_profile_interval_list=sphn_flow_profile_interval_list,
            context=context,
            indent=indent+2
        ))

    # 5.3. Multiple contrast agents: an administration event for each contrast agent, with only the start and stop datetimes
    else:

        logger.debug(" "*(indent+0) + f"Multiple contrast agents found: '{len(sphn_contrast_agent_list)}'. The route, volume, total dose and flow are not used.")

        for sphn_contrast_agent in sphn_contrast_agent_list:
            sphn_contrast_agent_administration_event_list.append(create_sphn_contrast_agent_administration_event(
                sphn_contrast_agent=sphn_contrast_agent,
                sphn_administration_route_code=None,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                sphn_flow_profile_interval_list=None,
                context=context,
                indent=indent+2
            ))

    #
    # 6. Store the SPHN Contrast Agent Administration Event(s) in the data store
    #

    for sphn_contrast_agent_administration_event in sphn_contrast_agent_administration_event_list:
        data_store.add_sphn_contrast_agent_administration_event_to_list(
            sphn_contrast_agent_administration_event=sphn_contrast_agent_administration_event,
            logger=logger,
            indent=indent+2
        )


#
# Edwin 2026-11-13
#
def process_legacy_contrast_bolus_agents(dataset: Dataset, context: Context, indent: int=0) -> list[SPHNContrastAgent]:
    """
    Returns the list of SPHN Contrast Agent objects (without duplicates) in the DICOM legacy (single-frame) Contrast/Bolus module:
        - first from the coded information: each item of the DICOM ContrastBolusAgentSequence is a contrast agent,
        - then, if no contrast agent was found, from the free text in the DICOM ContrastBolusAgent tag.
    Parameters:
        - dataset: The DICOM Dataset containing the legacy (single-frame) Contrast/Bolus Module
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger
    data_store = context.data_store

    sphn_contrast_agent_list: list[SPHNContrastAgent] = []

    #
    # 1. The DICOM ContrastBolusAgentSequence (coded info)
    #

    contrast_bolus_agent_sequence = get_contrast_bolus_agent_sequence_from_dicom(dataset, context, indent=indent+2)

    if contrast_bolus_agent_sequence is not None:

        logger.debug(" "*(indent+0) + f"Found DICOM ContrastBolusAgentSequence (coded info) with {len(contrast_bolus_agent_sequence)} item(s)")

        for i, item in enumerate(contrast_bolus_agent_sequence, start=1):

            assert isinstance(item, Dataset)

            logger.debug(" "*(indent+2) + f"Processing item {i} of {len(contrast_bolus_agent_sequence)} in DICOM ContrastBolusAgentSequence")

            sphn_contrast_agent_active_ingredient = process_contrast_bolus_agent_code(item, context, indent=indent+4)

            if sphn_contrast_agent_active_ingredient is None:
                continue

            sphn_contrast_agent = create_sphn_contrast_agent(
                active_ingredient_list=[sphn_contrast_agent_active_ingredient],
                article=None,
                context=context,
                indent=indent+4
            )
            add_sphn_contrast_agent_to_list(sphn_contrast_agent, sphn_contrast_agent_list, context, indent=indent+4)

    #
    # 2. The DICOM ContrastBolusAgent (free text info), if no contrast agent was found in the coded info
    #

    if len(sphn_contrast_agent_list) == 0:

        contrast_bolus_agent_str = get_contrast_bolus_agent_from_dicom(dataset, context, indent=indent+2)

        if contrast_bolus_agent_str is not None:

            logger.debug(" "*(indent+0) + f"Found DICOM ContrastBolusAgent (free text info) with value: '{contrast_bolus_agent_str}'")

            # Add the free text contrast agent to the data store for statistical purposes
            data_store.add_contrast_bolus_agent_to_dict(contrast_bolus_agent_str)

            # ToDo: Edwin: Add a call to an AI model to predict the DICOM contrast agent code(s) based on the text in the contrast_bolus_agent string

            # Find the contrast agent trade names, active ingredient names and active element (or functional group) names in the free text
            contrast_agent_dict_list = extract_contrast_agents(contrast_bolus_agent_str, context, indent=indent+2)

            logger.debug(" "*(indent+0) + f"Extracted: '{len(contrast_agent_dict_list)}' contrast agent(s) from the free text")

            for i, contrast_agent_dict in enumerate(contrast_agent_dict_list, start=1):

                logger.debug(" "*(indent+2) + f"Processing contrast agent {i} of {len(contrast_agent_dict_list)}: '{contrast_agent_dict}'")

                sphn_contrast_agent = process_contrast_bolus_agent_dict(contrast_agent_dict, context, indent=indent+4)
                add_sphn_contrast_agent_to_list(sphn_contrast_agent, sphn_contrast_agent_list, context, indent=indent+4)

    return sphn_contrast_agent_list


#
# Edwin 2026-11-13
#
def process_legacy_contrast_bolus_ingredient(
        dataset: Dataset,
        sphn_contrast_agent_list: list[SPHNContrastAgent],
        context: Context,
        indent: int=0
    ) -> list[SPHNContrastAgent]:
    """
    Processes the DICOM ContrastBolusIngredient (e.g. "IODINE") and ContrastBolusIngredientConcentration tags,
    and returns the (updated) list of SPHN Contrast Agent objects:
        - Without a contrast agent, a new contrast agent is created with the ingredient.
        - With a single contrast agent, the ingredient is added to it.
        - With multiple contrast agents, the ingredient is not used, as it is unknown to which contrast agent it belongs.
    The concentration is added to the ingredient, if the ingredient is used.
    Parameters:
        - dataset: The DICOM Dataset containing the legacy (single-frame) Contrast/Bolus Module
        - sphn_contrast_agent_list: The list of SPHN Contrast Agent objects found so far
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(sphn_contrast_agent_list, list) and all(isinstance(item, SPHNContrastAgent) for item in sphn_contrast_agent_list)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger

    #
    # 1. The DICOM ContrastBolusIngredient (a defined term)
    #

    contrast_bolus_ingredient_str = get_contrast_bolus_ingredient_from_dicom(dataset, context, indent=indent+2)

    if contrast_bolus_ingredient_str is None:
        return sphn_contrast_agent_list

    logger.debug(" "*(indent+0) + f"Found DICOM ContrastBolusIngredient with value: '{contrast_bolus_ingredient_str}'")

    sphn_contrast_agent_active_ingredient = process_contrast_bolus_ingredient(contrast_bolus_ingredient_str, context, indent=indent+2)

    if sphn_contrast_agent_active_ingredient is None:
        return sphn_contrast_agent_list

    if len(sphn_contrast_agent_list) > 1:
        logger.debug(" "*(indent+0) + "Multiple SPHN Contrast Agents found. The SPHN Contrast Agent Active Ingredient cannot be added to a specific SPHN Contrast Agent.")
        return sphn_contrast_agent_list

    #
    # 2. Add the ingredient to the single contrast agent, or create a new contrast agent with the ingredient
    #

    if len(sphn_contrast_agent_list) == 1:
        sphn_contrast_agent = sphn_contrast_agent_list[0]

        # Use the ingredient of the contrast agent with the same code, if any (e.g. from the ContrastBolusAgentSequence)
        existing_ingredient = next((item for item in sphn_contrast_agent.has_active_ingredient_list or [] if item.has_code == sphn_contrast_agent_active_ingredient.has_code), None)

        if existing_ingredient is not None:
            sphn_contrast_agent_active_ingredient = existing_ingredient
            logger.debug(" "*(indent+0) + "The SPHN Contrast Agent already has this SPHN Contrast Agent Active Ingredient.")
        else:
            sphn_contrast_agent.add_sphn_contrast_agent_active_ingredient(sphn_contrast_agent_active_ingredient)
            logger.debug(" "*(indent+0) + "Added the SPHN Contrast Agent Active Ingredient to the existing SPHN Contrast Agent.")

    else:
        sphn_contrast_agent_list = [create_sphn_contrast_agent(
            active_ingredient_list=[sphn_contrast_agent_active_ingredient],
            article=None,
            context=context,
            indent=indent+2
        )]
        logger.debug(" "*(indent+0) + "Created a new SPHN Contrast Agent with the SPHN Contrast Agent Active Ingredient.")

    #
    # 3. The DICOM ContrastBolusIngredientConcentration [mg/mL]
    #

    concentration = get_contrast_bolus_ingredient_concentration_from_dicom(dataset, context, indent=indent+2)

    if concentration is not None:
        sphn_contrast_agent_active_ingredient.has_concentration = create_sphn_quantity_for_concentration(concentration, context, indent=indent+2)
        logger.debug(" "*(indent+0) + f"Added the concentration: '{concentration}' mg/mL to the SPHN Contrast Agent Active Ingredient.")

    return sphn_contrast_agent_list


#
# Edwin 2026-11-13
#
def process_legacy_contrast_bolus_volume_and_total_dose(dataset: Dataset, sphn_contrast_agent: SPHNContrastAgent, context: Context, indent: int=0) -> None:
    """
    Adds the DICOM ContrastBolusVolume (the total administered volume of diluted contrast agent) to the SPHN Contrast Agent,
    and the DICOM ContrastBolusTotalDose (the total administered volume of undiluted contrast agent) to its active ingredient,
    if it has a single active ingredient.
    Parameters:
        - dataset: The DICOM Dataset containing the legacy (single-frame) Contrast/Bolus Module
        - sphn_contrast_agent: The (single) SPHN Contrast Agent object of the contrast bolus
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(sphn_contrast_agent, SPHNContrastAgent)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger

    # 1. The DICOM ContrastBolusVolume [mL diluted]
    volume = get_contrast_bolus_volume_from_dicom(dataset, context, indent=indent+2)

    if volume is not None:
        sphn_contrast_agent.has_quantity = create_sphn_quantity_for_volume(volume, context, indent=indent+2)
        logger.debug(" "*(indent+0) + f"Added the total administered (diluted) volume: '{volume}' mL to the SPHN Contrast Agent.")

    # 2. The DICOM ContrastBolusTotalDose [mL undiluted]
    total_dose = get_contrast_bolus_total_dose_from_dicom(dataset, context, indent=indent+2)

    if total_dose is not None:
        active_ingredient_list = sphn_contrast_agent.has_active_ingredient_list
        if active_ingredient_list is not None and len(active_ingredient_list) == 1:
            active_ingredient_list[0].has_quantity = create_sphn_quantity_for_volume(total_dose, context, indent=indent+2)
            logger.debug(" "*(indent+0) + f"Added the total administered (undiluted) dose: '{total_dose}' mL to the SPHN Contrast Agent Active Ingredient.")
        else:
            logger.debug(" "*(indent+0) + "The total administered (undiluted) dose is only used for a single SPHN Contrast Agent Active Ingredient.")


#
# Edwin 2026-11-13
#
def process_legacy_contrast_flow_profile(dataset: Dataset, context: Context, indent: int=0) -> list[SPHNFlowProfileInterval]|None:
    """
    Returns the list of SPHN Flow Profile Interval objects for the DICOM ContrastFlowRate and ContrastFlowDuration tags, if any.
    Both tags may have multiple values: the n-th flow rate belongs to the n-th flow duration.
    When only one of the tags is present, its values are used without the other.
    Parameters:
        - dataset: The DICOM Dataset containing the legacy (single-frame) Contrast/Bolus Module
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger

    flow_rate_list = get_contrast_flow_rate_from_dicom(dataset, context, indent=indent+2)
    flow_duration_list = get_contrast_flow_duration_from_dicom(dataset, context, indent=indent+2)

    if flow_rate_list is None and flow_duration_list is None:
        return None

    if flow_rate_list is not None and flow_duration_list is not None and len(flow_rate_list) != len(flow_duration_list):
        logger.debug(" "*(indent+0) + f"Mismatch between the number of flow rates: '{len(flow_rate_list)}' and flow durations: '{len(flow_duration_list)}'. They are not used.")
        return None

    number_of_intervals = len(flow_rate_list) if flow_rate_list is not None else len(flow_duration_list)  # type: ignore[arg-type]
    flow_rate_list = flow_rate_list or [None] * number_of_intervals
    flow_duration_list = flow_duration_list or [None] * number_of_intervals

    sphn_flow_profile_interval_list: list[SPHNFlowProfileInterval] = []

    for flow_rate, flow_duration in zip(flow_rate_list, flow_duration_list):

        sphn_flow_profile_interval = create_sphn_flow_profile_interval(
            start_datetime=None,
            end_datetime=None,
            volume=None,
            flow_rate=flow_rate,
            flow_duration=flow_duration,
            context=context,
            indent=indent+2
        )

        # Add the SPHN Flow Profile Interval to the list, even duplicates
        if sphn_flow_profile_interval is not None:
            sphn_flow_profile_interval_list.append(sphn_flow_profile_interval)

    logger.debug(" "*(indent+0) + f"Created '{len(sphn_flow_profile_interval_list)}' SPHN Flow Profile Interval object(s).")

    return sphn_flow_profile_interval_list if len(sphn_flow_profile_interval_list) > 0 else None


# ---------------------------------------------------------------------------------------------------------------------
# Functions for processing the Enhanced (multi-frame) "Contrast/Bolus" module
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-10-12
#
def process_enhanced_contrast_bolus_module_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> None:
    """
    Processes the DICOM enhanced (multi-frame) Contrast/Bolus Module information
    and stores contrast agent administration events in the data_store.
    Parameters:
        - dataset: The DICOM Dataset containing the enhanced (multi-frame) Contrast/Bolus Module
        - context: The Context object that holds the data_store, logger, and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger
    data_store = context.data_store

    #
    # 1. Get the Contrast/Bolus Agent Sequence
    #

    contrast_bolus_agent_sequence = get_contrast_bolus_agent_sequence_from_dicom(dataset, context, indent=indent+2)

    if contrast_bolus_agent_sequence is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAgentSequence not found or empty in the dataset")
        return

    logger.debug(" "*(indent+0) + f"DICOM ContrastBolusAgentSequence found with {len(contrast_bolus_agent_sequence)} item(s)")

    #
    # 2. Process the items in the Contrast/Bolus Agent Sequence: each item is a contrast agent
    #

    for i, item in enumerate(contrast_bolus_agent_sequence, start=1):

        assert isinstance(item, Dataset)

        logger.debug(" "*(indent+2) + f"Processing item {i} of {len(contrast_bolus_agent_sequence)} in DICOM ContrastBolusAgentSequence")

        sphn_contrast_agent_administration_event = process_enhanced_contrast_bolus_agent_sequence_item(item, context, indent=indent+4)

        # Store the SPHN contrast agent administration event in the data store
        if sphn_contrast_agent_administration_event is not None:
            data_store.add_sphn_contrast_agent_administration_event_to_list(
                sphn_contrast_agent_administration_event=sphn_contrast_agent_administration_event,
                logger=logger,
                indent=indent+4
            )
        else:
            logger.debug(" "*(indent+4) + "No SPHN Contrast Agent Administration Event object to store in the data store")


#
# Edwin 2026-11-13
#
def process_enhanced_contrast_bolus_agent_sequence_item(dataset: Dataset, context: Context, indent: int=0) -> SPHNContrastAgentAdministrationEvent|None:
    """
    Process the DICOM enhanced (multi-frame) ContrastBolusAgentSequence item (Dataset), which describes a single contrast agent,
    and return an SPHNContrastAgentAdministrationEvent object, if any.
    Parameters:
        - dataset: The DICOM enhanced (multi-frame) ContrastBolusAgentSequence item (Dataset)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger

    # Not mapped to SPHN, only logged
    agent_number = get_contrast_bolus_agent_number_from_dicom(dataset, context, indent=indent+2)
    t1_relaxivity = get_contrast_bolus_t1_relaxivity_from_dicom(dataset, context, indent=indent+2)
    ingredient_opaque = get_contrast_bolus_ingredient_opaque_from_dicom(dataset, context, indent=indent+2)
    logger.debug(" "*(indent+0) + f"Not mapped to SPHN: DICOM ContrastBolusAgentNumber: '{agent_number}', ContrastBolusT1Relaxivity: '{t1_relaxivity}', ContrastBolusIngredientOpaque: '{ingredient_opaque}'")

    #
    # 1. The contrast agent: the code of the item itself, and the codes in the ContrastBolusIngredientCodeSequence
    #

    logger.debug(" "*(indent+0) + "Start processing the DICOM contrast agent information.")

    # 1.1. The code of the ContrastBolusAgentSequence item
    sphn_contrast_agent_active_ingredient = process_contrast_bolus_agent_code(dataset, context, indent=indent+2)

    # 1.2. The codes in the ContrastBolusIngredientCodeSequence, with the concentration and percent by volume (only for a single ingredient)
    ingredient_list = process_enhanced_contrast_bolus_ingredients(dataset, context, indent=indent+2)

    # The code of the item first, without duplicates
    active_ingredient_list: list[SPHNContrastAgentActiveIngredient] = []
    for ingredient in ([sphn_contrast_agent_active_ingredient] if sphn_contrast_agent_active_ingredient is not None else []) + ingredient_list:
        if ingredient not in active_ingredient_list:
            active_ingredient_list.append(ingredient)

    sphn_contrast_agent = create_sphn_contrast_agent(
        active_ingredient_list=active_ingredient_list,
        article=None,
        context=context,
        indent=indent+2
    )

    # 1.3. The DICOM ContrastBolusVolume [mL diluted]
    volume = get_contrast_bolus_volume_from_dicom(dataset, context, indent=indent+2)

    if volume is not None:
        sphn_contrast_agent.has_quantity = create_sphn_quantity_for_volume(volume, context, indent=indent+2)
        logger.debug(" "*(indent+2) + f"Added the total administered (diluted) volume: '{volume}' mL to the SPHN Contrast Agent.")

    logger.debug(" "*(indent+0) + f"Done processing the DICOM contrast agent information: '{len(active_ingredient_list)}' active ingredient(s)")

    #
    # 2. The administration route: only coded information in the enhanced module
    #

    logger.debug(" "*(indent+0) + "Start processing the DICOM administration route information.")

    sphn_administration_route_code = process_contrast_bolus_administration_route(dataset, use_free_text=False, context=context, indent=indent+2)

    logger.debug(" "*(indent+0) + "Done processing the DICOM administration route information.")

    #
    # 3. The flow profile, with the start and stop datetimes: the earliest start and the latest stop of the profile intervals
    #

    logger.debug(" "*(indent+0) + "Start processing the DICOM contrast administration profile.")

    sphn_flow_profile_interval_list = process_enhanced_contrast_administration_profile(dataset, context, indent=indent+2)

    start_datetime = min((item.has_start_datetime for item in sphn_flow_profile_interval_list or [] if item.has_start_datetime is not None), default=None)
    end_datetime = max((item.has_end_datetime for item in sphn_flow_profile_interval_list or [] if item.has_end_datetime is not None), default=None)

    if start_datetime is None:
        logger.debug(" "*(indent+2) + "Contrast/bolus start datetime is not available, trying fallback datetimes.")
        # ToDo: Edwin: Search other hospital databases for contrast/bolus start time information.
        start_datetime = get_contrast_bolus_datetime_fallback(context, indent=indent+4)

    if start_datetime is None:
        logger.debug(" "*(indent+0) + "No contrast/bolus start datetime available. No SPHN Contrast Agent Administration Event is created.")
        return None

    if end_datetime is not None and end_datetime < start_datetime:
        logger.warning(" "*(indent+2) + f"Contrast/bolus stop datetime '{end_datetime!s}' is before the start datetime '{start_datetime!s}', it is not used.")
        end_datetime = None

    logger.debug(" "*(indent+0) + f"Done processing the DICOM contrast administration profile: start '{start_datetime!s}', stop '{end_datetime!s}'")

    #
    # 4. Create the SPHN Contrast Agent Administration Event
    #

    return create_sphn_contrast_agent_administration_event(
        sphn_contrast_agent=sphn_contrast_agent,
        sphn_administration_route_code=sphn_administration_route_code,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        sphn_flow_profile_interval_list=sphn_flow_profile_interval_list,
        context=context,
        indent=indent+2
    )


#
# Edwin 2026-11-13
#
def process_enhanced_contrast_bolus_ingredients(dataset: Dataset, context: Context, indent: int=0) -> list[SPHNContrastAgentActiveIngredient]:
    """
    Returns the list of SPHN Contrast Agent Active Ingredient objects (without duplicates) for the items of the
    DICOM ContrastBolusIngredientCodeSequence in a DICOM enhanced (multi-frame) ContrastBolusAgentSequence item.
    The DICOM ContrastBolusIngredientConcentration and ContrastBolusIngredientPercentByVolume are added to the ingredient,
    if there is a single ingredient.
    Parameters:
        - dataset: The DICOM enhanced (multi-frame) ContrastBolusAgentSequence item (Dataset)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger

    ingredient_list: list[SPHNContrastAgentActiveIngredient] = []

    #
    # 1. The DICOM ContrastBolusIngredientCodeSequence (coded info)
    #

    ingredient_code_sequence = get_contrast_bolus_ingredient_code_sequence_from_dicom(dataset, context, indent=indent+2)

    if ingredient_code_sequence is not None:

        logger.debug(" "*(indent+0) + f"Found DICOM ContrastBolusIngredientCodeSequence (coded info) with {len(ingredient_code_sequence)} item(s)")

        for i, item in enumerate(ingredient_code_sequence, start=1):

            assert isinstance(item, Dataset)

            logger.debug(" "*(indent+2) + f"Processing item {i} of {len(ingredient_code_sequence)} in DICOM ContrastBolusIngredientCodeSequence")

            ingredient = process_contrast_bolus_agent_code(item, context, indent=indent+4)

            if ingredient is not None and ingredient not in ingredient_list:
                ingredient_list.append(ingredient)

    #
    # 2. The DICOM ContrastBolusIngredientConcentration [mg/mL] and ContrastBolusIngredientPercentByVolume [%]
    #

    concentration = get_contrast_bolus_ingredient_concentration_from_dicom(dataset, context, indent=indent+2)
    percent_by_volume = get_contrast_bolus_ingredient_percent_by_volume_from_dicom(dataset, context, indent=indent+2)

    if concentration is None and percent_by_volume is None:
        return ingredient_list

    if len(ingredient_list) != 1:
        logger.debug(" "*(indent+0) + f"The concentration and percent by volume are only used for a single ingredient, found: '{len(ingredient_list)}'")
        return ingredient_list

    if concentration is not None:
        ingredient_list[0].has_concentration = create_sphn_quantity_for_concentration(concentration, context, indent=indent+2)
        logger.debug(" "*(indent+0) + f"Added the concentration: '{concentration}' mg/mL to the SPHN Contrast Agent Active Ingredient.")

    if percent_by_volume is not None:
        ingredient_list[0].has_volume_percentage = create_sphn_quantity_for_percent_by_volume(percent_by_volume, context, indent=indent+2)
        logger.debug(" "*(indent+0) + f"Added the percent by volume: '{percent_by_volume}' % to the SPHN Contrast Agent Active Ingredient.")

    return ingredient_list


#
# Edwin 2026-11-13
#
def process_enhanced_contrast_administration_profile(dataset: Dataset, context: Context, indent: int=0) -> list[SPHNFlowProfileInterval]|None:
    """
    Returns the list of SPHN Flow Profile Interval objects for the items of the DICOM ContrastAdministrationProfileSequence
    in a DICOM enhanced (multi-frame) ContrastBolusAgentSequence item, if any.
    Parameters:
        - dataset: The DICOM enhanced (multi-frame) ContrastBolusAgentSequence item (Dataset)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger

    contrast_administration_profile_sequence = get_contrast_administration_profile_sequence_from_dicom(dataset, context, indent=indent+2)

    if contrast_administration_profile_sequence is None:
        return None

    logger.debug(" "*(indent+0) + f"Found DICOM ContrastAdministrationProfileSequence with {len(contrast_administration_profile_sequence)} item(s)")

    sphn_flow_profile_interval_list: list[SPHNFlowProfileInterval] = []

    for i, item in enumerate(contrast_administration_profile_sequence, start=1):

        assert isinstance(item, Dataset)

        logger.debug(" "*(indent+2) + f"Processing item {i} of {len(contrast_administration_profile_sequence)} in DICOM ContrastAdministrationProfileSequence")

        sphn_flow_profile_interval = process_contrast_administration_profile_sequence_item(item, context, indent=indent+4)

        # Add the SPHN Flow Profile Interval to the list, even duplicates
        if sphn_flow_profile_interval is not None:
            sphn_flow_profile_interval_list.append(sphn_flow_profile_interval)

    return sphn_flow_profile_interval_list if len(sphn_flow_profile_interval_list) > 0 else None


#
# Edwin 2026-11-13
#
def process_contrast_administration_profile_sequence_item(dataset: Dataset, context: Context, indent: int=0) -> SPHNFlowProfileInterval|None:
    """
    Process the DICOM ContrastAdministrationProfileSequence item (Dataset) and return an SPHN Flow Profile Interval object, if any.
    Parameters:
        - dataset: The DICOM ContrastAdministrationProfileSequence item (Dataset)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    # The enhanced Contrast/Bolus module allows only one flow rate and one flow duration value per profile item
    flow_rate_list = get_contrast_flow_rate_from_dicom(dataset, context, indent=indent+2)
    flow_duration_list = get_contrast_flow_duration_from_dicom(dataset, context, indent=indent+2)

    return create_sphn_flow_profile_interval(
        start_datetime=process_contrast_bolus_time(get_contrast_bolus_start_time_from_dicom(dataset, context, indent=indent+2), context, indent=indent+2),
        end_datetime=process_contrast_bolus_time(get_contrast_bolus_stop_time_from_dicom(dataset, context, indent=indent+2), context, indent=indent+2),
        volume=get_contrast_bolus_volume_from_dicom(dataset, context, indent=indent+2),
        flow_rate=flow_rate_list[0] if flow_rate_list is not None and len(flow_rate_list) == 1 else None,
        flow_duration=flow_duration_list[0] if flow_duration_list is not None and len(flow_duration_list) == 1 else None,
        context=context,
        indent=indent+2
    )


# ---------------------------------------------------------------------------------------------------------------------
# Functions for processing the contrast agents, ingredients, routes and times (legacy and enhanced)
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-11-13
#
def process_contrast_bolus_agent_code(dataset: Dataset, context: Context, indent: int=0) -> SPHNContrastAgentActiveIngredient|None:
    """
    Process the coded information in a DICOM ContrastBolusAgentSequence item (legacy and enhanced) or a
    DICOM ContrastBolusIngredientCodeSequence item (enhanced), and return an SPHN Contrast Agent Active Ingredient object, if any.
    The DICOM code (DICOM CID 12 and CID 13) is mapped with DataConverter.dicom_contrast_agents_coded_2_sphn_snomed_coded.
    Parameters:
        - dataset: The DICOM code sequence item (Dataset)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    data_store = context.data_store

    code = process_coded_item(
        dataset=dataset,
        mapping=DataConverter.dicom_contrast_agents_coded_2_sphn_snomed_coded,
        sequence_name="ContrastBolusAgentSequence",
        add_known_code_to_dict=data_store.add_known_contrast_bolus_agent_sequence_code_to_dict,
        add_unknown_code_to_dict=data_store.add_unknown_contrast_bolus_agent_sequence_code_to_dict,
        context=context,
        indent=indent
    )

    if code is None:
        return None

    return create_sphn_contrast_agent_active_ingredient(code, context, indent=indent)


#
# Edwin 2026-11-13
#
def process_contrast_bolus_agent_dict(contrast_agent_dict: dict, context: Context, indent: int=0) -> SPHNContrastAgent:
    """
    Process a contrast agent found in the DICOM ContrastBolusAgent (free text) by the "extract_contrast_agents" function,
    and return an SPHN Contrast Agent object. The contrast agent name is either:
        - a trade name: all its active ingredients are added to the contrast agent, with a drug article (e.g. "Omnipaque-300 100ml"),
        - an active ingredient name, or
        - an active element (or functional group) name.
    Parameters:
        - contrast_agent_dict: A dictionary with the contrast agent found in the free text:
            {
                "agent": "agent name",
                "concentration": int|None,
                "dose": {
                    "value": int|float|None,
                    "unit": "ml"|"mg"|None
                }
            }
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(contrast_agent_dict, dict)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    agent_name = contrast_agent_dict.get("agent", None)
    concentration = contrast_agent_dict.get("concentration", None)
    dose_dict = contrast_agent_dict.get("dose", None) or {}
    dose_value = dose_dict.get("value", None)
    dose_unit = dose_dict.get("unit", None)

    assert is_valid_string(agent_name)
    assert concentration is None or isinstance(concentration, int)
    assert dose_value is None or isinstance(dose_value, (int, float))
    assert dose_unit is None or dose_unit in ["ml", "mg"]

    # Note: Case-sensitive lookup in the dictionaries, as the "extract_contrast_agents" function
    #       already normalizes the names to match the case used in the dictionaries.

    article_name: str|None = None

    # 1. A trade name: all its active ingredients, and the trade name with the concentration and dose as drug article
    if agent_name in DataConverter.contrast_agent_trade_name_2_manufacturer_and_ingredient_name:
        logger.debug(" "*(indent+0) + f"DICOM contrast agent '{agent_name}' is identified as a trade name")

        _manufacturer, ingredient_name_list, _inactive_ingredient_name_list = DataConverter.contrast_agent_trade_name_2_manufacturer_and_ingredient_name[agent_name]
        assert len(ingredient_name_list) > 0
        code_list = [DataConverter.contrast_agent_active_ingredient_name_2_snomed_code[name] for name in ingredient_name_list]

        article_name = agent_name
        if concentration is not None:
            article_name = f"{article_name}-{concentration}"
        if dose_value is not None and dose_unit is not None:
            article_name = f"{article_name} {dose_value}{dose_unit}"

    # 2. An active ingredient name
    elif agent_name in DataConverter.contrast_agent_active_ingredient_name_2_snomed_code:
        logger.debug(" "*(indent+0) + f"DICOM contrast agent '{agent_name}' is identified as a contrast agent active ingredient name")
        code_list = [DataConverter.contrast_agent_active_ingredient_name_2_snomed_code[agent_name]]

    # 3. An active element (or functional group) name
    elif agent_name.title() in DataConverter.contrast_agent_active_element_names_2_snomed_code:
        logger.debug(" "*(indent+0) + f"DICOM contrast agent '{agent_name}' is identified as a contrast agent active element (or functional group) name")
        code_list = [DataConverter.contrast_agent_active_element_names_2_snomed_code[agent_name.title()]]

    else:
        raise ValueError(f"This should never happen. Contrast agent '{agent_name}' found by the extract_contrast_agents function is not in one of the mapping dictionaries.")

    # Create the SPHN Contrast Agent Active Ingredients (without duplicates) and the SPHN Contrast Agent
    active_ingredient_list: list[SPHNContrastAgentActiveIngredient] = []
    for code in code_list:
        ingredient = create_sphn_contrast_agent_active_ingredient(code, context, indent=indent+2)
        if ingredient not in active_ingredient_list:
            active_ingredient_list.append(ingredient)

    return create_sphn_contrast_agent(
        active_ingredient_list=active_ingredient_list,
        article=create_sphn_drug_article(article_name, context, indent=indent+2) if article_name is not None else None,
        context=context,
        indent=indent+2
    )


#
# Edwin 2026-11-13
#
def process_contrast_bolus_ingredient(ingredient_term: str, context: Context, indent: int=0) -> SPHNContrastAgentActiveIngredient|None:
    """
    Process the DICOM ContrastBolusIngredient defined term (e.g. "IODINE", "GADOLINIUM", "CARBON DIOXIDE", "BARIUM")
    and return an SPHN Contrast Agent Active Ingredient object, if any.
    The term is mapped with DataConverter.contrast_agent_active_element_names_2_snomed_code.
    Parameters:
        - ingredient_term: The DICOM ContrastBolusIngredient defined term
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert is_valid_string(ingredient_term)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger
    data_store = context.data_store

    # The dictionary uses title case names, e.g. "Carbon Dioxide"
    code = DataConverter.contrast_agent_active_element_names_2_snomed_code.get(ingredient_term.title(), None)

    if code is None:
        logger.debug(" "*(indent+0) + f"DICOM ContrastBolusIngredient '{ingredient_term}' could not be mapped to a known code")
        data_store.add_unknown_contrast_bolus_ingredient_to_dict(ingredient_term)
        return None

    logger.debug(" "*(indent+0) + f"Successfully mapped the DICOM ContrastBolusIngredient '{ingredient_term}' to the coding: '{code}'")
    data_store.add_known_contrast_bolus_ingredient_to_dict(ingredient_term)

    return create_sphn_contrast_agent_active_ingredient(code, context, indent=indent)


#
# Edwin 2026-11-13
#
def process_contrast_bolus_administration_route(dataset: Dataset, use_free_text: bool, context: Context, indent: int=0) -> SPHNCode|None:
    """
    Returns the SPHN Code object for the administration route of the contrast bolus, if exactly one route is found:
        - first from the DICOM ContrastBolusAdministrationRouteSequence (coded info),
        - then from the DICOM ContrastBolusRoute (free text info, legacy module only), e.g. "IV".
    Parameters:
        - dataset: The DICOM Dataset with the legacy module, or the DICOM enhanced ContrastBolusAgentSequence item (Dataset)
        - use_free_text: Use the free text DICOM ContrastBolusRoute tag (legacy module) when there is no coded information
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(use_free_text, bool)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger

    sphn_administration_route_codes: list[SPHNCode] = []

    # 1. The DICOM ContrastBolusAdministrationRouteSequence (coded info)
    route_sequence = get_contrast_bolus_administration_route_sequence_from_dicom(dataset, context, indent=indent+2)

    if route_sequence is not None:
        sphn_administration_route_code = process_contrast_bolus_administration_route_sequence_item(route_sequence[0], context, indent=indent+2)
        if sphn_administration_route_code is not None:
            sphn_administration_route_codes.append(sphn_administration_route_code)

    # 2. The DICOM ContrastBolusRoute (free text info, legacy module only)
    if len(sphn_administration_route_codes) == 0 and use_free_text:
        route_str = get_contrast_bolus_route_from_dicom(dataset, context, indent=indent+2)
        if route_str is not None:
            logger.debug(" "*(indent+0) + f"Found DICOM ContrastBolusRoute (free text info) with value: '{route_str}'")
            sphn_administration_route_codes = process_contrast_bolus_route(route_str, context, indent=indent+2)

    # Only a single administration route can be added to the SPHN Contrast Agent Administration Event
    if len(sphn_administration_route_codes) == 1:
        return sphn_administration_route_codes[0]

    if len(sphn_administration_route_codes) > 1:
        logger.debug(" "*(indent+0) + f"Multiple administration routes found: '{len(sphn_administration_route_codes)}'. None is used.")

    return None


#
# Edwin 2026-11-13
#
def process_contrast_bolus_administration_route_sequence_item(dataset: Dataset, context: Context, indent: int=0) -> SPHNCode|None:
    """
    Process the DICOM ContrastBolusAdministrationRouteSequence item (Dataset) and return an SPHN Code object for the SPHN hasAdministrationRouteCode, if any.
    The DICOM route code (DICOM CID 11) is mapped with DataConverter.administration_routes_list.
    Parameters:
        - dataset: The DICOM ContrastBolusAdministrationRouteSequence item (Dataset)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    data_store = context.data_store

    route_code = process_coded_item(
        dataset=dataset,
        mapping=DataConverter.administration_routes_list,
        sequence_name="ContrastBolusAdministrationRouteSequence",
        add_known_code_to_dict=data_store.add_known_contrast_bolus_administration_route_sequence_code_to_dict,
        add_unknown_code_to_dict=data_store.add_unknown_contrast_bolus_administration_route_sequence_code_to_dict,
        context=context,
        indent=indent
    )

    if route_code is None:
        return None

    return create_sphn_code(route_code, context, indent=indent)


#
# Edwin 2026-11-13
#
def process_contrast_bolus_route(route_str: str, context: Context, indent: int=0) -> list[SPHNCode]:
    """
    Process the DICOM ContrastBolusRoute (free text) string and return a list of matched SPHN administration route codes.
    The routes are matched with DataConverter.route_patterns and DataConverter.sphn_route_codes.
    Parameters:
        - route_str: The DICOM ContrastBolusRoute (free text) string
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert is_valid_string(route_str)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger
    data_store = context.data_store

    sphn_code_list: list[SPHNCode] = []
    routes_found: list[str] = []

    for item_dict in extract_administration_routes_from_text(route_str, logger, indent=indent):

        sphn_code_route = create_sphn_code(item_dict["Code"], context, indent=indent)
        if sphn_code_route not in sphn_code_list:
            sphn_code_list.append(sphn_code_route)

        # For statistics, keep track of the routes found
        data_store.add_known_contrast_bolus_route_to_dict(item_dict["Route"])
        routes_found.append(item_dict["Route"])

    if len(sphn_code_list) == 0:
        logger.debug(" "*(indent+0) + f"No administration route found in the free text: '{route_str}'")
        data_store.add_unknown_contrast_bolus_route_to_dict(route_str)

    # For statistics, add the route string and the routes found
    data_store.add_contrast_bolus_route_to_dict(route_str, routes_found)

    return sphn_code_list


#
# Edwin 2026-11-13
#
def process_contrast_bolus_time(time_str: str|None, context: Context, indent: int=0) -> datetime|None:
    """
    Returns the contrast/bolus (start or stop) datetime for the DICOM Time (TM) string, e.g. Contrast/Bolus Start Time (0018,1042),
    completed with the date of the acquisition, series or study datetime, if any.
    Parameters:
        - time_str: The DICOM Time (TM) string, if any
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert time_str is None or is_valid_string(time_str)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger
    data_store = context.data_store

    if time_str is None:
        return None

    # Complete the DICOM time to ensure it has all components (hours, minutes, seconds)
    dicom_time = complete_dicom_time(time_str, logger, indent=indent+2)

    if dicom_time is None:
        logger.debug(" "*(indent+0) + f"Failed to complete the DICOM Time: '{time_str}'")
        return None

    # Combine the time with the date of the acquisition, series or study datetime
    result = combine_dicom_time_with_reference_datetime(
        dicom_time=dicom_time,
        acquisition_datetime=data_store.acquisition_start_datetime,
        series_datetime=data_store.series_start_datetime,
        study_datetime=data_store.study_start_datetime,
        logger=logger,
        indent=indent+2
    )

    if result is not None:
        logger.debug(" "*(indent+0) + f"Contrast/bolus datetime from the DICOM Time tag and the acquisition/series/study date: '{result!s}'")
    else:
        logger.debug(" "*(indent+0) + f"Failed to combine the DICOM Time: '{time_str}' with an acquisition/series/study date")

    return result


#
# Edwin 2026-11-08
#
def get_contrast_bolus_datetime_fallback(context: Context, indent: int=0) -> datetime|None:
    """
    Tries to determine a fallback datetime for the contrast/bolus start, based on the available Series, Acquisition or Study datetimes,
    or the configured fallback contrast agent datetime.
    Parameters:
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    data_store = context.data_store
    logger = context.logger

    contrast_bolus_start_datetime = None

    if data_store.series_start_datetime is not None:
        contrast_bolus_start_datetime = data_store.series_start_datetime
        logger.debug(" "*(indent+0) + f"Using DICOM Series start datetime as fallback: {contrast_bolus_start_datetime!s}")

    elif data_store.acquisition_start_datetime is not None:
        contrast_bolus_start_datetime = data_store.acquisition_start_datetime
        logger.debug(" "*(indent+0) + f"Using DICOM Acquisition start datetime as fallback: {contrast_bolus_start_datetime!s}")

    elif data_store.study_start_datetime is not None:
        contrast_bolus_start_datetime = data_store.study_start_datetime
        logger.debug(" "*(indent+0) + f"Using DICOM Study start datetime as fallback: {contrast_bolus_start_datetime!s}")

    elif data_store.fallback_contrast_agent_datetime is not None:
        contrast_bolus_start_datetime = data_store.fallback_contrast_agent_datetime
        logger.debug(" "*(indent+0) + f"Using the configured fallback contrast agent datetime: {contrast_bolus_start_datetime!s}")

    else:
        logger.debug(" "*(indent+0) + "No fallback datetime available for the contrast/bolus start.")

    return contrast_bolus_start_datetime


#
# Edwin 2026-11-13
#
def process_coded_item(
        dataset: Dataset,
        mapping: dict[tuple[str, str], CodeTuple],
        sequence_name: str,
        add_known_code_to_dict: Callable[[str|None, str|None, str|None], None],
        add_unknown_code_to_dict: Callable[[str|None, str|None, str|None], None],
        context: Context,
        indent: int=0
    ) -> CodeTuple|None:
    """
    Read the coding scheme designator, code value and code meaning in a DICOM code sequence item (Dataset)
    and map them to an SPHN compatible code tuple with the given mapping dictionary.
    The DICOM code is added to the known or unknown codes dictionary of the data store, for statistical purposes.
    Parameters:
        - dataset: The DICOM code sequence item (Dataset)
        - mapping: The mapping dictionary: (DICOM coding scheme designator, code value) -> (coding scheme designator, code value, description)
        - sequence_name: The name of the DICOM code sequence (for logging)
        - add_known_code_to_dict: The data store method for adding a mapped DICOM code to its statistics dictionary
        - add_unknown_code_to_dict: The data store method for adding an unmapped DICOM code to its statistics dictionary
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(mapping, dict)
    assert is_valid_string(sequence_name)
    assert callable(add_known_code_to_dict) and callable(add_unknown_code_to_dict)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger

    # Get the coded info from DICOM
    coding_scheme_designator = get_coding_scheme_designator_from_dicom(dataset, context, indent=indent+2)
    code_value = get_code_value_from_dicom(dataset, context, indent=indent+2)
    code_descr = get_code_meaning_from_dicom(dataset, context, indent=indent+2)

    if coding_scheme_designator is None or code_value is None:
        logger.debug(" "*(indent+0) + f"DICOM {sequence_name} item has no coding scheme designator or code value")
        add_unknown_code_to_dict(coding_scheme_designator, code_value, code_descr)
        return None

    logger.debug(" "*(indent+0) + f"DICOM {sequence_name} item has coding scheme designator '{coding_scheme_designator}' and code value '{code_value}' with description '{code_descr}'")

    # Map the DICOM code to the SPHN compatible code
    # (the designators in the contrast agent and route mappings are upper case, and older DICOM data may use "SNM3" instead of "SRT")
    result = mapping.get((get_lookup_coding_scheme_designator(coding_scheme_designator.upper()), code_value), None)

    if result is None:
        logger.warning(" "*(indent+0) + f"DICOM {sequence_name} item code '{(coding_scheme_designator, code_value, code_descr)}' could not be mapped to a known code")
        add_unknown_code_to_dict(coding_scheme_designator, code_value, code_descr)
        return None

    assert isinstance(result, tuple) and len(result) == 3 and all(is_valid_string(item) for item in result)

    logger.debug(" "*(indent+0) + f"Successfully mapped the DICOM coding: '{(coding_scheme_designator, code_value, code_descr)}' to the coding: '{result}'")
    add_known_code_to_dict(coding_scheme_designator, code_value, code_descr)

    return result


#
# Edwin 2026-11-13
#
def add_sphn_contrast_agent_to_list(sphn_contrast_agent: SPHNContrastAgent, sphn_contrast_agent_list: list[SPHNContrastAgent], context: Context, indent: int=0) -> None:
    """
    Adds the SPHN Contrast Agent object to the list, if it is not already in the list.
    Parameters:
        - sphn_contrast_agent: The SPHN Contrast Agent object
        - sphn_contrast_agent_list: The list of SPHN Contrast Agent objects
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(sphn_contrast_agent, SPHNContrastAgent)
    assert isinstance(sphn_contrast_agent_list, list)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    if sphn_contrast_agent in sphn_contrast_agent_list:
        context.logger.debug(" "*(indent+0) + "SPHN Contrast Agent is already in the list")
        return

    sphn_contrast_agent_list.append(sphn_contrast_agent)
    context.logger.debug(" "*(indent+0) + "SPHN Contrast Agent added to the list")


# ---------------------------------------------------------------------------------------------------------------------
# Functions for creating SPHN objects
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-11-13
#
def create_sphn_code(code: CodeTuple, context: Context, indent: int=0) -> SPHNCode:
    """
    Creates an SPHN Code object from a code tuple (coding scheme designator, code value, description).
    Parameters:
        - code: The code tuple
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(code, tuple) and len(code) == 3 and all(is_valid_string(item) for item in code)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    coding_scheme_designator, code_value, code_descr = code

    return SPHNCode(
        sphn_schema = context.sphn_schema,
        has_coding_system_and_version = coding_scheme_designator,
        has_identifier = code_value,
        has_name = code_descr
    )


#
# Edwin 2026-10-12
#
def create_sphn_contrast_agent_active_ingredient(code: CodeTuple, context: Context, indent: int=0) -> SPHNContrastAgentActiveIngredient:
    """
    Creates an SPHN Contrast Agent Active Ingredient object for the (SPHN SNOMED CT) code tuple.
    Parameters:
        - code: The code tuple (coding scheme designator, code value, description) of the active ingredient
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(code, tuple) and len(code) == 3 and all(is_valid_string(item) for item in code)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    context.logger.debug(" "*(indent+0) + f"Creating an SPHN Contrast Agent Active Ingredient object for: '{code}'")

    return SPHNContrastAgentActiveIngredient(
        sphn_schema = context.sphn_schema,
        has_code = create_sphn_code(code, context, indent=indent+2),
        has_source_system_list = [context.data_store.sphn_source_system]
    )


#
# Edwin 2026-10-12
#
def create_sphn_contrast_agent(
        active_ingredient_list: list[SPHNContrastAgentActiveIngredient]|None,
        article: SPHNDrugArticle|None,
        context: Context,
        indent: int=0
    ) -> SPHNContrastAgent:
    """
    Creates an SPHN Contrast Agent object with the provided information.
    Parameters:
        - active_ingredient_list: A list of SPHN Contrast Agent Active Ingredient objects, if any
        - article: The SPHN Drug Article object associated with the contrast agent, if any
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert active_ingredient_list is None \
        or (isinstance(active_ingredient_list, list) \
            and all(isinstance(item, SPHNContrastAgentActiveIngredient) for item in active_ingredient_list))
    assert article is None or isinstance(article, SPHNDrugArticle)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    context.logger.debug(" "*(indent+0) + f"Creating an SPHN Contrast Agent object with '{len(active_ingredient_list or [])}' active ingredient(s)")

    return SPHNContrastAgent(
        sphn_schema = context.sphn_schema,
        has_active_ingredient_list = active_ingredient_list if active_ingredient_list else None,
        has_article = article,
        has_source_system_list = [context.data_store.sphn_source_system]
    )


#
# Edwin 2026-11-13
#
def create_sphn_drug_article(name: str, context: Context, indent: int=0) -> SPHNDrugArticle:
    """
    Creates an SPHN Drug Article object with the name, e.g. the trade name with concentration and dose: "Omnipaque-300 100ml".
    Parameters:
        - name: The name of the drug article
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert is_valid_string(name)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    context.logger.debug(" "*(indent+0) + f"Creating an SPHN Drug Article object: '{name}'")

    return SPHNDrugArticle(
        sphn_schema = context.sphn_schema,
        has_name = name,
        has_source_system_list = [context.data_store.sphn_source_system]
    )


#
# Edwin 2026-10-12
#
def create_sphn_contrast_agent_administration_event(
        sphn_contrast_agent: SPHNContrastAgent,
        sphn_administration_route_code: SPHNCode|None,
        start_datetime: datetime,
        end_datetime: datetime|None,
        sphn_flow_profile_interval_list: list[SPHNFlowProfileInterval]|None,
        context: Context,
        indent: int=0
    ) -> SPHNContrastAgentAdministrationEvent:
    """
    Creates an SPHN Contrast Agent Administration Event object with the provided information.
    Parameters:
        - sphn_contrast_agent: The SPHN Contrast Agent object
        - sphn_administration_route_code: The SPHN administration route code, if any
        - start_datetime: The start date and time of the administration event
        - end_datetime: The end date and time of the administration event, if any
        - sphn_flow_profile_interval_list: The list of SPHN Flow Profile Interval objects, if any (an empty list is not allowed by SPHN)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(sphn_contrast_agent, SPHNContrastAgent)
    assert sphn_administration_route_code is None or isinstance(sphn_administration_route_code, SPHNCode)
    assert isinstance(start_datetime, datetime)
    assert end_datetime is None or isinstance(end_datetime, datetime)
    assert sphn_flow_profile_interval_list is None \
           or (isinstance(sphn_flow_profile_interval_list, list) \
               and all(isinstance(item, SPHNFlowProfileInterval) for item in sphn_flow_profile_interval_list))
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger
    data_store = context.data_store

    logger.debug(" "*(indent+0) + "Start creating an SPHN Contrast Agent Administration Event object...")

    sphn_contrast_agent_administration_event = SPHNContrastAgentAdministrationEvent(
        sphn_schema = context.sphn_schema,
        has_start_datetime = start_datetime,
        has_end_datetime = end_datetime,
        has_drug = sphn_contrast_agent,
        has_administration_route_code = sphn_administration_route_code,
        has_subject_pseudo_identifier = data_store.sphn_subject_pseudo_identifier,
        has_source_system_list = [data_store.sphn_source_system],
        has_flow_profile_interval_list = sphn_flow_profile_interval_list if sphn_flow_profile_interval_list else None
    )

    logger.debug(" "*(indent+0) + "Done  creating SPHN Contrast Agent Administration Event object.")

    return sphn_contrast_agent_administration_event


#
# Edwin 2026-11-13
#
def create_sphn_flow_profile_interval(
        start_datetime: datetime|None,
        end_datetime: datetime|None,
        volume: float|None,
        flow_rate: float|None,
        flow_duration: float|None,
        context: Context,
        indent: int=0
    ) -> SPHNFlowProfileInterval|None:
    """
    Creates an SPHN Flow Profile Interval object with the provided information, if any information is available.
    Parameters:
        - start_datetime: The start date and time of the interval, if any
        - end_datetime: The end date and time of the interval, if any
        - volume: The volume [mL], if any
        - flow_rate: The flow rate [mL/s], if any
        - flow_duration: The flow duration [s], if any
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert start_datetime is None or isinstance(start_datetime, datetime)
    assert end_datetime is None or isinstance(end_datetime, datetime)
    assert volume is None or isinstance(volume, float)
    assert flow_rate is None or isinstance(flow_rate, float)
    assert flow_duration is None or isinstance(flow_duration, float)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger

    if all(item is None for item in (start_datetime, end_datetime, volume, flow_rate, flow_duration)):
        logger.debug(" "*(indent+0) + "No information available for an SPHN Flow Profile Interval object.")
        return None

    logger.debug(" "*(indent+0) + f"Creating an SPHN Flow Profile Interval object: start '{start_datetime!s}', stop '{end_datetime!s}', "
                 + f"volume '{volume}' mL, flow rate '{flow_rate}' mL/s, duration '{flow_duration}' s")

    return SPHNFlowProfileInterval(
        sphn_schema = context.sphn_schema,
        has_start_datetime = start_datetime,
        has_end_datetime = end_datetime,
        has_volume = create_sphn_quantity_for_volume(volume, context, indent=indent+2) if volume is not None else None,
        has_volumetric_flow_rate = create_sphn_quantity_for_flow_rate(flow_rate, context, indent=indent+2) if flow_rate is not None else None,
        has_duration = create_sphn_quantity_for_flow_duration(flow_duration, context, indent=indent+2) if flow_duration is not None else None
    )


#
# Edwin 2026-11-13
#
def create_sphn_quantity(value: float, ucum_code: str, context: Context) -> SPHNQuantity:
    """
    Creates an SPHN Quantity object with the value and the SPHN UCUM unit code.
    Parameters:
        - value: The value
        - ucum_code: The SPHN UCUM unit code, e.g. "mL", "mgpermL", "mLpers", "s", "percent"
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
# Edwin 2026-10-16
#
def create_sphn_quantity_for_volume(volume: float, context: Context, indent: int=0) -> SPHNQuantity:
    """
    Creates the SPHN Quantity object for a contrast/bolus volume [mL] and returns it.
    Parameters:
        - volume: The volume in mL
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """
    assert isinstance(volume, float)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    return create_sphn_quantity(volume, "mL", context)  # SPHN UCUM unit code, label: "mL", comment: "milliliter"


#
# Edwin 2026-10-16
#
def create_sphn_quantity_for_flow_rate(flow_rate: float, context: Context, indent: int=0) -> SPHNQuantity:
    """
    Creates the SPHN Quantity object for the contrast/bolus flow rate [mL/s] and returns it.
    Parameters:
        - flow_rate: The flow rate in mL/s
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """
    assert isinstance(flow_rate, float)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    return create_sphn_quantity(flow_rate, "mLpers", context)  # SPHN UCUM unit code, label: "mL/s", comment: "milliliter per second"


#
# Edwin 2026-10-16
#
def create_sphn_quantity_for_flow_duration(flow_duration: float, context: Context, indent: int=0) -> SPHNQuantity:
    """
    Creates the SPHN Quantity object for the contrast/bolus flow duration [s] and returns it.
    Parameters:
        - flow_duration: The flow duration in seconds
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """
    assert isinstance(flow_duration, float)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    return create_sphn_quantity(flow_duration, "s", context)  # SPHN UCUM unit code, label: "s", comment: "second"


#
# Edwin 2026-11-13
#
def create_sphn_quantity_for_concentration(concentration: float, context: Context, indent: int=0) -> SPHNQuantity:
    """
    Creates the SPHN Quantity object for the contrast/bolus ingredient concentration [mg/mL] and returns it.
    Parameters:
        - concentration: The concentration in mg/mL
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """
    assert isinstance(concentration, float)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    return create_sphn_quantity(concentration, "mgpermL", context)  # SPHN UCUM unit code, label: "mg/mL", comment: "milligram per milliliter"


#
# Edwin 2026-11-13
#
def create_sphn_quantity_for_percent_by_volume(percent_by_volume: float, context: Context, indent: int=0) -> SPHNQuantity:
    """
    Creates the SPHN Quantity object for the contrast/bolus ingredient percent by volume [%] and returns it.
    Parameters:
        - percent_by_volume: The percent by volume
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """
    assert isinstance(percent_by_volume, float)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    return create_sphn_quantity(percent_by_volume, "percent", context)  # SPHN UCUM unit code, label: "%", comment: "percent"


# ---------------------------------------------------------------------------------------------------------------------
# Functions for reading DICOM tags in the Legacy (single-frame) and Enhanced (multi-frame) Contrast/Bolus module
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-10-12
#
def get_contrast_bolus_agent_sequence_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence (list of Datasets) in the DICOM ContrastBolusAgentSequence tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,0012)
    # Type:	                Optional (3) / Required (1)
    # Keyword:	            ContrastBolusAgentSequence
    # Value Multiplicity	1
    # Value Representation:	Sequence (SQ)

    # Note: The Type is Optional (3) in the legacy and Required (1) in the enhanced Contrast/Bolus module.
    # The sequence may contain multiple items, each representing a coded contrast agent (DICOM CID 12 "Imaging Contrast Agent").

    return get_sequence_from_dicom(dataset, "ContrastBolusAgentSequence", context, indent=indent)


#
# Edwin 2026-10-20
#
def get_contrast_bolus_agent_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM ContrastBolusAgent tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,0010)
    # Type:	                Required, Empty if Unknown (2)
    # Keyword:	            ContrastBolusAgent
    # Value Multiplicity	1
    # Value Representation:	Long String (LO)

    # Note: Only in the legacy (single-frame) Contrast/Bolus module

    return get_string_from_dicom(dataset, "ContrastBolusAgent", context, indent=indent)


#
# Edwin 2026-10-22
#
def get_contrast_bolus_ingredient_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM ContrastBolusIngredient tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1048)
    # Type:	                Optional (3)
    # Keyword:              ContrastBolusIngredient
    # Value Multiplicity:   1
    # Value Representation: Code String (CS)

    # Note: Only in the legacy (single-frame) Contrast/Bolus module.
    # Defined terms: IODINE, GADOLINIUM, CARBON DIOXIDE, BARIUM

    return get_string_from_dicom(dataset, "ContrastBolusIngredient", context, indent=indent)


#
# Edwin 2026-10-27
#
def get_contrast_bolus_route_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM ContrastBolusRoute tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1040)
    # Type:	                Optional (3)
    # Keyword:	            ContrastBolusRoute
    # Value Multiplicity	1
    # Value Representation:	Long String (LO)

    # Note: Only in the legacy (single-frame) Contrast/Bolus module

    return get_string_from_dicom(dataset, "ContrastBolusRoute", context, indent=indent)


#
# Edwin 2026-10-12
#
def get_contrast_bolus_administration_route_sequence_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence (list of Datasets) in the DICOM ContrastBolusAdministrationRouteSequence tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,0014)
    # Type:	                Optional (3)
    # Keyword:	            ContrastBolusAdministrationRouteSequence
    # Value Multiplicity	1
    # Value Representation:	Sequence (SQ)

    # Note: Only a single item shall be included in this sequence (DICOM CID 11 "Route of Administration")

    return get_code_sequence_from_dicom(dataset, "ContrastBolusAdministrationRouteSequence", context, indent=indent)


#
# Edwin 2026-10-12
#
def get_contrast_bolus_ingredient_code_sequence_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence (list of Datasets) in the DICOM ContrastBolusIngredientCodeSequence tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,9338)
    # Type:	                Required, Empty if Unknown (2)
    # Keyword:	            ContrastBolusIngredientCodeSequence
    # Value Multiplicity	1
    # Value Representation:	Sequence (SQ)

    # Note: Only in the enhanced (multi-frame) Contrast/Bolus module.
    # One or more items are permitted in this sequence (DICOM CID 13 "Imaging Contrast Agent Ingredient")

    return get_sequence_from_dicom(dataset, "ContrastBolusIngredientCodeSequence", context, indent=indent)


#
# Edwin 2026-10-12
#
def get_contrast_bolus_ingredient_concentration_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the float corresponding to the value of the DICOM ContrastBolusIngredientConcentration tag [mg/mL]
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1049)
    # Type:	                Optional (3)
    # Keyword:	            ContrastBolusIngredientConcentration
    # Value Multiplicity	1
    # Value Representation:	Decimal String (DS)
    # Unit:                 milligrams per milliliter (mg/mL)

    return get_positive_float_from_dicom(dataset, "ContrastBolusIngredientConcentration", context, indent=indent)


#
# Edwin 2026-10-12
#
def get_contrast_bolus_ingredient_percent_by_volume_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the float corresponding to the value of the DICOM ContrastBolusIngredientPercentByVolume tag [%]
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0052,0001)
    # Type:	                Optional (3)
    # Keyword:	            ContrastBolusIngredientPercentByVolume
    # Value Multiplicity	1
    # Value Representation:	Floating Point Single (FL)
    # Unit:                 percent (%)

    # Note: Only in the enhanced (multi-frame) Contrast/Bolus module

    return get_positive_float_from_dicom(dataset, "ContrastBolusIngredientPercentByVolume", context, indent=indent)


#
# Edwin 2026-10-15
#
def get_contrast_administration_profile_sequence_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence (list of Datasets) in the DICOM ContrastAdministrationProfileSequence tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,9340)
    # Type:	                Optional (3)
    # Keyword:	            ContrastAdministrationProfileSequence
    # Value Multiplicity	1
    # Value Representation:	Sequence (SQ)

    # Note: Only in the enhanced (multi-frame) Contrast/Bolus module.
    # One or more items are permitted in this sequence, each describing a phase of the contrast administration.

    return get_sequence_from_dicom(dataset, "ContrastAdministrationProfileSequence", context, indent=indent)


#
# Edwin 2026-10-15
#
def get_contrast_bolus_volume_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the float corresponding to the value of the DICOM ContrastBolusVolume tag [mL]
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1041)
    # Type:	                Optional (3)
    # Keyword:	            ContrastBolusVolume
    # Value Multiplicity	1
    # Value Representation:	Decimal String (DS)
    # Unit:                 milliliter (mL) of diluted contrast agent

    # Note: In the legacy module and the enhanced Contrast/Bolus Agent Sequence item: the total volume administered,
    # in the enhanced Contrast Administration Profile Sequence item: the volume administered during this phase.

    return get_positive_float_from_dicom(dataset, "ContrastBolusVolume", context, indent=indent)


#
# Edwin 2026-10-29
#
def get_contrast_bolus_total_dose_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the float corresponding to the value of the DICOM ContrastBolusTotalDose tag [mL]
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1044)
    # Type:	                Optional (3)
    # Keyword:	            ContrastBolusTotalDose
    # Value Multiplicity	1
    # Value Representation:	Decimal String (DS)
    # Unit:                 milliliter (mL) of undiluted contrast agent

    # Note: Only in the legacy (single-frame) Contrast/Bolus module

    return get_positive_float_from_dicom(dataset, "ContrastBolusTotalDose", context, indent=indent)


#
# Edwin 2026-10-28
#
def get_contrast_flow_rate_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> list[float|None]|None:
    """
    Returns the list of floats corresponding to the values of the DICOM ContrastFlowRate tag [mL/s]
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    Note: The n-th value belongs to the n-th value of the DICOM ContrastFlowDuration tag.
    """

    # Tag:                  (0018,1046)
    # Type:	                Optional (3)
    # Keyword:	            ContrastFlowRate
    # Value Multiplicity	1-n (only 1 in the enhanced Contrast/Bolus module)
    # Value Representation:	Decimal String (DS)
    # Unit:                 milliliter per second (mL/s)

    return get_positive_float_list_from_dicom(dataset, "ContrastFlowRate", context, indent=indent)


#
# Edwin 2026-10-28
#
def get_contrast_flow_duration_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> list[float|None]|None:
    """
    Returns the list of floats corresponding to the values of the DICOM ContrastFlowDuration tag [s]
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    Note: The n-th value belongs to the n-th value of the DICOM ContrastFlowRate tag.
    """

    # Tag:                  (0018,1047)
    # Type:	                Optional (3)
    # Keyword:	            ContrastFlowDuration
    # Value Multiplicity	1-n (only 1 in the enhanced Contrast/Bolus module)
    # Value Representation:	Decimal String (DS)
    # Unit:                 seconds (s)

    return get_positive_float_list_from_dicom(dataset, "ContrastFlowDuration", context, indent=indent)


#
# Edwin 2026-10-15
#
def get_contrast_bolus_start_time_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM ContrastBolusStartTime tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1042)
    # Type:	                Optional (3)
    # Keyword:	            ContrastBolusStartTime
    # Value Multiplicity	1
    # Value Representation:	Time (TM)

    # Note: The DICOM time format is specified in the DICOM standard as Time (TM) in:
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part05/sect_6.2.html

    return get_string_from_dicom(dataset, "ContrastBolusStartTime", context, indent=indent)


#
# Edwin 2026-10-15
#
def get_contrast_bolus_stop_time_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM ContrastBolusStopTime tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1043)
    # Type:	                Optional (3)
    # Keyword:	            ContrastBolusStopTime
    # Value Multiplicity	1
    # Value Representation:	Time (TM)

    return get_string_from_dicom(dataset, "ContrastBolusStopTime", context, indent=indent)


#
# Edwin 2026-10-09
#
def get_contrast_bolus_agent_number_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> int|None:
    """
    Returns the integer corresponding to the value of the DICOM ContrastBolusAgentNumber tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,9337)
    # Type:	                Required (1)
    # Keyword:	            ContrastBolusAgentNumber
    # Value Multiplicity	1
    # Value Representation:	Unsigned Short (US)

    # Note: Only in the enhanced (multi-frame) Contrast/Bolus module, it identifies the ContrastBolusAgentSequence item

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM ContrastBolusAgentNumber tag
    value = dataset.get("ContrastBolusAgentNumber", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAgentNumber tag was not found")
        return None

    # Convert value to int
    try:
        value_int = int(value)
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM ContrastBolusAgentNumber tag value could not be converted to int")
        return None

    if value_int <= 0:
        logger.warning(" "*(indent+0) + f"DICOM ContrastBolusAgentNumber: '{value_int}' is not a valid value.")
        return None

    return value_int


#
# Edwin 2026-10-12
#
def get_contrast_bolus_ingredient_opaque_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM ContrastBolusIngredientOpaque tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,9425)
    # Type:	                Optional (3)
    # Keyword:	            ContrastBolusIngredientOpaque
    # Value Multiplicity	1
    # Value Representation:	Code String (CS)

    # Note: Only in the enhanced (multi-frame) Contrast/Bolus module. Enumerated values: YES, NO.
    # Not a property of the SPHN Contrast Agent Active Ingredient.

    return get_string_from_dicom(dataset, "ContrastBolusIngredientOpaque", context, indent=indent)


#
# Edwin 2026-10-12
#
def get_contrast_bolus_t1_relaxivity_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the float corresponding to the value of the DICOM ContrastBolusT1Relaxivity tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,0013)
    # Type:	                Optional (3)
    # Keyword:	            ContrastBolusT1Relaxivity
    # Value Multiplicity	1
    # Value Representation:	Floating Point Single (FL)

    # Note: Only in the enhanced (multi-frame) Contrast/Bolus module.
    # Not a property of the SPHN Contrast Agent.

    return get_positive_float_from_dicom(dataset, "ContrastBolusT1Relaxivity", context, indent=indent)


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
        - keyword: The DICOM keyword of the tag, e.g. "ContrastBolusAgent"
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

    # Convert a possible DICOM TM object to a string representation and remove leading/trailing whitespace
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
def get_positive_float_from_dicom(dataset: Dataset, keyword: str, context: Context, indent: int=0) -> float|None:
    """
    Returns the (non-negative) float corresponding to the value of the DICOM Decimal String (DS) or Floating Point (FL) tag with the given keyword
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - keyword: The DICOM keyword of the tag, e.g. "ContrastBolusVolume"
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

    if value is None or str(value).strip() == "":
        logger.debug(" "*(indent+0) + f"DICOM {keyword} tag was not found or empty")
        return None

    # Convert value to float
    try:
        value_float = float(value)
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + f"DICOM {keyword} tag value could not be converted to float")
        return None

    if value_float < 0:
        logger.warning(" "*(indent+0) + f"DICOM {keyword}: '{value_float}' is probably not a valid value.")
        return None

    return value_float


#
# Edwin 2026-11-13
#
def get_positive_float_list_from_dicom(dataset: Dataset, keyword: str, context: Context, indent: int=0) -> list[float|None]|None:
    """
    Returns the list of (non-negative) floats corresponding to the values of the multi-valued DICOM Decimal String (DS) tag
    with the given keyword. A value that cannot be converted is None in the list, to keep the order of the values.
    When a value is negative, None is returned.
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - keyword: The DICOM keyword of the tag, e.g. "ContrastFlowRate"
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

    if value is None or str(value).strip() == "":
        logger.debug(" "*(indent+0) + f"DICOM {keyword} tag was not found or empty")
        return None

    # A multi-valued tag is a MultiValue (list) of DSfloat or DSdecimal values, a single-valued tag a single DSfloat or DSdecimal value
    values = list(value) if isinstance(value, MultiValue) else [value]

    value_float_list: list[float|None] = []

    for value_item in values:
        try:
            value_float_list.append(float(value_item) if value_item is not None and str(value_item).strip() != "" else None)
        except (ValueError, TypeError):
            logger.warning(" "*(indent+0) + f"DICOM {keyword} tag value '{value_item}' could not be converted to float")
            value_float_list.append(None)

    if any(value_float is not None and value_float < 0 for value_float in value_float_list):
        logger.warning(" "*(indent+0) + f"DICOM {keyword} tag contains negative values: '{value_float_list}'")
        return None

    return value_float_list if len(value_float_list) > 0 else None


#
# Edwin 2026-11-13
#
def get_sequence_from_dicom(dataset: Dataset, keyword: str, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence (list of Datasets) in the DICOM sequence tag with the given keyword, if it is not empty.
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - keyword: The DICOM keyword of the sequence tag, e.g. "ContrastBolusAgentSequence"
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert is_valid_string(keyword)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM sequence tag
    value = dataset.get(keyword, None)

    if value is None:
        logger.debug(" "*(indent+0) + f"DICOM {keyword} tag was not found")
        return None

    assert isinstance(value, Sequence)

    if len(value) == 0:
        logger.debug(" "*(indent+0) + f"DICOM {keyword} tag is empty")
        return None

    return value


#
# Edwin 2026-11-13
#
def get_code_sequence_from_dicom(dataset: Dataset, keyword: str, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence (list of Datasets) in the DICOM code sequence tag with the given keyword, if it is not empty.
    These code sequences shall contain only a single item: when there are more, a warning is logged.
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - keyword: The DICOM keyword of the code sequence tag, e.g. "ContrastBolusAdministrationRouteSequence"
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert is_valid_string(keyword)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    value = get_sequence_from_dicom(dataset, keyword, context, indent=indent)

    if value is not None and len(value) > 1:
        context.logger.warning(" "*(indent+0) + f"DICOM {keyword} tag has '{len(value)}' items, only a single item is allowed. Only the first item is used.")

    return value
