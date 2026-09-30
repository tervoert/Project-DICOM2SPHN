"""
dicom_contrast_bolus_tags_reader.py:
    Part of the example dicom2sphn package.
    It contains functions for reading DICOM contrast bolus tags.
"""

from datetime import datetime

from pydicom import Dataset
from pydicom.multival import MultiValue
from pydicom.sequence import Sequence
from pydicom.valuerep import DSdecimal, DSfloat

from dicom2sphn.sphn_concepts.sphn_contrast_agent_administration_event import (
    SPHNContrastAgentAdministrationEvent,
)

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
from .sphn_concepts.sphn_drug_article import SPHNDrugArticle
from .sphn_concepts.sphn_quantity import SPHNQuantity
from .sphn_concepts.sphn_source_system import SPHNSourceSystem
from .sphn_concepts.sphn_substance import SPHNSubstance
from .sphn_concepts.sphn_unit import SPHNUnit
from .tools import already_in_list, is_valid_string

#
# DICOM defines two modules for contrast bolus information: 
#
# - the "Contrast/Bolus" module
#   - Used by legacy (single-frame) DICOM objects, such as CT, MR, and XA images.
#   - Table C.7-12. Contrast/Bolus Module Attributes
#   - Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.4.html#table_C.7-12
#
# - the "Enhanced Contrast/Bolus" module.
#   - Used by enhanced (multi-frame) DICOM objects, such as Enhanced CT, Enhanced MR, and Enhanced XA images.
#   - Table C.7-12b. Enhanced Contrast/Bolus Module Attributes
#   - Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.4b.html#table_C.7-12b

    # ToDo: Edwin 2026-09-24 - Implement processing for Contrast / Bolus concentration and administration route
    # ToDo: Edwin 2026-09-24 - Implement processing for Enhanced Contrast / Bolus module



# ---------------------------------------------------------------------------------------------------------------------
# Functions for reading DICOM tags in the Contrast/Bolus module
# ---------------------------------------------------------------------------------------------------------------------

#
#  Edwin 2026-09-29
#
def get_contrast_bolus_module_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> list[SPHNContrastAgentAdministrationEvent]|None:
    """
    Returns a list of SPHN Contrast Agent Administration Event objects corresponding to the contrast bolus module information in the DICOM dataset.
    Parameters:
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context is the Context object that holds the data_store, logger and other relevant information
        - indent is the indentation level for logging messages
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger
    data_store = context.data_store
    sphn_schema = context.sphn_schema

    
    # contrast_bolus_route = get_contrast_bolus_route_from_dicom(dataset, context, indent=indent+2)
    # contrast_bolus_volume = get_contrast_bolus_volume_from_dicom(dataset, context, indent=indent+2)
    # contrast_bolus_start_time = get_contrast_bolus_start_time_from_dicom(dataset, context, indent=indent+2)
    # contrast_bolus_stop_time = get_contrast_bolus_stop_time_from_dicom(dataset, context, indent=indent+2)
    # contrast_bolus_total_dose = get_contrast_bolus_total_dose_from_dicom(dataset, context, indent=indent+2)
    # contrast_flow_rate_list = get_contrast_flow_rate_list_from_dicom(dataset, context, indent=indent+2)
    # contrast_flow_duration_list = get_contrast_flow_duration_list_from_dicom(dataset, context, indent=indent+2)
    # contrast_bolus_ingredient_concentration = get_contrast_bolus_ingredient_concentration_from_dicom(dataset, context, indent=indent+2)

    sphn_contrast_agent_administration_event_list = []
    sphn_contrast_agent_list = []
    sphn_administration_route_code = None
    

    # 
    # 1. Check if there is coded information in the ContrastBolusAgentSequence
    #

    contrast_bolus_agent_sequence = get_contrast_bolus_agent_sequence_from_dicom(dataset, context, indent=indent+2)

    if contrast_bolus_agent_sequence is not None:

        assert isinstance(contrast_bolus_agent_sequence, Sequence)

        logger.debug(" "*(indent+0) + f"DICOM ContrastBolusAgentSequence (coded info) found with {len(contrast_bolus_agent_sequence)} item(s)")

        sphn_contrast_agent = process_contrast_bolus_agent_sequence(contrast_bolus_agent_sequence, context, indent+4)

        if sphn_contrast_agent is not None:
            if not already_in_list(sphn_contrast_agent, sphn_contrast_agent_list):
                sphn_contrast_agent_list.append(sphn_contrast_agent)
                logger.debug(" "*(indent+2) + "Added SPHN Contrast Agent")
            else:
                logger.debug(" "*(indent+2) + "SPHN Contrast Agent is already in the list")
        else:            
            logger.debug(" "*(indent+2) + "Failed to create an SPHN Contrast Agent object from DICOM ContrastBolusAgentSequence (coded info).")

    else:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAgentSequence (coded info) is missing or empty.")

    #
    # 2. Check if there is free text information in the ContrastBolusAgent tag
    #

    contrast_bolus_agent = get_contrast_bolus_agent_from_dicom(dataset, context, indent=indent+2)

    if contrast_bolus_agent is not None:

        assert is_valid_string(contrast_bolus_agent)

        logger.debug(" "*(indent+0) + f"DICOM ContrastBolusAgent (free text info) found with value: '{contrast_bolus_agent}'")

        # Add the free text contrast agent to the data store for statistical purposes
        data_store.add_contrast_bolus_agent_to_dict(contrast_bolus_agent)

        # ToDo: Edwin: Add a call to an AI model to predict the DICOM contrast agent code(s) based on the text in the contrast_bolus_agent string

        # 
        # 2.1 Check if a DICOM contrast agent (trade) name, or active ingredient name is found in the contrast_bolus_agent free text string
        #
        contrast_agents_dict_list = extract_contrast_agents(contrast_bolus_agent, context, indent=indent+2)

        for contrast_agent_dict in contrast_agents_dict_list:
            logger.debug(" "*(indent+2) + f"Extracted contrast agent info: {contrast_agent_dict}")

            sphn_contrast_agent = process_contrast_bolus_agent_dict(contrast_agent_dict, context, indent=indent+2)

            if sphn_contrast_agent is not None:
                if not already_in_list(sphn_contrast_agent, sphn_contrast_agent_list):
                    sphn_contrast_agent_list.append(sphn_contrast_agent)
                    logger.debug(" "*(indent+2) + "Added SPHN Contrast Agent")
                else:
                    logger.debug(" "*(indent+2) + "SPHN Contrast Agent is already in the list")

            else:            
                logger.debug(" "*(indent+2) + "Failed to create an SPHN Contrast Agent object from DICOM ContrastBolusAgent (free text info).")

    else:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAgent (free text info) is missing or empty.")


    #
    # 3. Check if there is a DICOM term in the ContrastBolusIngredient tag
    #
    
    contrast_bolus_ingredient = get_contrast_bolus_ingredient_from_dicom(dataset, context, indent=indent+2)

    if contrast_bolus_ingredient is not None:

        logger.debug(" "*(indent+0) + f"DICOM ContrastBolusIngredient found: '{contrast_bolus_ingredient}'")

        # Add the DICOM contrast bolus ingredient to the data store for statistical purposes
        data_store.add_contrast_bolus_ingredient_to_dict(contrast_bolus_agent)

        sphn_contrast_agent = process_contrast_bolus_ingredient(contrast_bolus_ingredient, context, indent+4)

        if sphn_contrast_agent is not None:
            if not already_in_list(sphn_contrast_agent, sphn_contrast_agent_list):
                sphn_contrast_agent_list.append(sphn_contrast_agent)
                logger.debug(" "*(indent+2) + "Added SPHN Contrast Agent")
            else:
                logger.debug(" "*(indent+2) + "SPHN Contrast Agent is already in the list")

        else:            
            logger.debug(" "*(indent+2) + "Failed to create an SPHN Contrast Agent object from DICOM ContrastBolusIngredient (DICOM Term).")

    else:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusIngredient (DICOM Term) is missing or empty.")

    #
    # Done with the Contrast Agent names
    #
    logger.debug(" "*(indent+0) + "Done processing DICOM ContrastBolusAgentSequence, ContrastBolusAgent and ContrastBolusIngredient tags." + 
                 f" Found: '{len(sphn_contrast_agent_list)}' SPHN Contrast Agent object(s)")

    #
    # 4. Check if there is a administration route sequence in the DICOM dataset
    #

    contrast_bolus_administration_route_sequence = get_contrast_bolus_administration_route_sequence_from_dicom(dataset, context, indent=indent+2)

    if contrast_bolus_administration_route_sequence is not None:
        
        assert isinstance(contrast_bolus_administration_route_sequence, Sequence)

        if len(contrast_bolus_administration_route_sequence) == 1:

            result = process_contrast_bolus_administration_route_sequence(contrast_bolus_administration_route_sequence, context, indent+4)

            if result is not None:
                sphn_administration_route_code = result
            else:
                logger.debug(" "*(indent+2) + "Failed to create an SPHN Administration Route Code object from DICOM ContrastBolusAdministrationRouteSequence (coded info).")

        elif len(contrast_bolus_administration_route_sequence) == 0:
            logger.debug(" "*(indent+2) + "DICOM ContrastBolusAdministrationRouteSequence is empty.")

        else:
            raise ValueError(f"Expected zero or one item in DICOM ContrastBolusAdministrationRouteSequence, but found {len(contrast_bolus_administration_route_sequence)}.")
        
    else:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAdministrationRouteSequence (coded info) is missing or empty.")
        

    #
    # 5. Collect more information for the SPHN Contrast Agent Administration Event object
    #

    # ToDo: Edwin: HERE
    # For test purposes:
    start_date_time_dummy = data_store.fallback_study_date_time

    #
    # 8. Create SPHN Contrast Agent Administration Event object(s) with the collected information
    #

    if len(sphn_contrast_agent_list) > 1:
        # Multiple contrast agent case, create administration events for each. 
        # We cannot use the other information as we donn't know which contrast agent it belongs to.

        logger.debug(" "*(indent+2) + f"Multiple contrast agents found: '{len(sphn_contrast_agent_list)}'.")

        for index, sphn_contrast_agent in enumerate(sphn_contrast_agent_list):
            
            logger.debug(" "*(indent+2) + f"Start creating SPHN Contrast Agent Administration Event object {index}/{len(sphn_contrast_agent_list)}")

            sphn_contrast_agent_administration_event = create_sphn_contrast_agent_administration_event(
                sphn_contrast_agent=sphn_contrast_agent,
                sphn_administration_route_code=sphn_administration_route_code,
                start_date_time=start_date_time_dummy,
                context=context,
                indent=indent+2
            )

            if sphn_contrast_agent_administration_event is None:
                logger.debug(" "*(indent+2) + "Failed to create SPHN Contrast Agent Administration Event object.")
                continue

            logger.debug(" "*(indent+2) + "Done  creating SPHN Contrast Agent Administration Event object.")

            # Add to the list if not already in it
            if not already_in_list(sphn_contrast_agent_administration_event, sphn_contrast_agent_administration_event_list):
                sphn_contrast_agent_administration_event_list.append(sphn_contrast_agent_administration_event)
                logger.debug(" "*(indent+2) + "Added SPHN Contrast Agent Administration Event object to the list.")
            else:
                logger.debug(" "*(indent+2) + "SPHN Contrast Agent Administration Event object is already in the list.")

    if len(sphn_contrast_agent_list) == 1:
        # Single contrast agent case, create an administration event for it.

        logger.debug(" "*(indent+2) + "Single contrast agent found.")

        sphn_contrast_agent = sphn_contrast_agent_list[0]

        sphn_contrast_agent_administration_event = create_sphn_contrast_agent_administration_event(
            sphn_contrast_agent=sphn_contrast_agent,
            sphn_administration_route_code=sphn_administration_route_code,
            start_date_time=start_date_time_dummy,
            context=context,
            indent=indent+2
        )
        
        if sphn_contrast_agent_administration_event is None:
            logger.debug(" "*(indent+2) + "Failed to create SPHN Contrast Agent Administration Event object.")
        else:
            logger.debug(" "*(indent+2) + "Done  creating SPHN Contrast Agent Administration Event object.")
            # Add to the list if not already in it
            if not already_in_list(sphn_contrast_agent_administration_event, sphn_contrast_agent_administration_event_list):
                sphn_contrast_agent_administration_event_list.append(sphn_contrast_agent_administration_event)
                logger.debug(" "*(indent+2) + "Added SPHN Contrast Agent Administration Event object to the list.")
            else:
                logger.debug(" "*(indent+2) + "SPHN Contrast Agent Administration Event object is already in the list.")


    if len(sphn_contrast_agent_list) == 0 and sphn_administration_route_code is not None:
        # No contrast agent case but there is other information available
        # The SPHN schema requires at least one contrast agent
        # Creating a contrast agent object with a placeholder active ingredient

        logger.debug(" "*(indent+2) + "No contrast agent found. Creating a contrast agent with a general 'Contrast Media' active ingredient.")
        sphn_contrast_agent_active_ingredient = create_sphn_contrast_agent_active_ingredient("SNOMED","385420005","| Contrast media (substance) |", context, indent=indent+2)

        sphn_contrast_agent = SPHNContrastAgent(
            sphn_schema = sphn_schema,
            has_active_ingredient=sphn_contrast_agent_active_ingredient,
            has_source_system_list=[data_store.sphn_source_system]
        )

        # We now have one contrast agent and can create a single administration event
        logger.debug(" "*(indent+2) + "Start creating SPHN Contrast Agent Administration Event object")

        sphn_contrast_agent_administration_event = create_sphn_contrast_agent_administration_event(
            sphn_contrast_agent=sphn_contrast_agent,
            sphn_administration_route_code=sphn_administration_route_code,
            start_date_time=start_date_time_dummy,
            context=context,
            indent=indent+2
        )

        if sphn_contrast_agent_administration_event is None:
            logger.debug(" "*(indent+2) + "Failed to create SPHN Contrast Agent Administration Event object.")
        else:
            logger.debug(" "*(indent+2) + "Done  creating SPHN Contrast Agent Administration Event object.")
            # Add to the list if not already in it
            if not already_in_list(sphn_contrast_agent_administration_event, sphn_contrast_agent_administration_event_list):
                sphn_contrast_agent_administration_event_list.append(sphn_contrast_agent_administration_event)
                logger.debug(" "*(indent+2) + "Added SPHN Contrast Agent Administration Event object to the list.")
            else:
                logger.debug(" "*(indent+2) + "SPHN Contrast Agent Administration Event object is already in the list.")

    # 
    # 9. Check if any SPHN Contrast Agent Administration Event objects were successfully created
    #

    return sphn_contrast_agent_administration_event_list if len(sphn_contrast_agent_administration_event_list) > 0 else None


#
# Edwin 2026-09-29
#
def create_sphn_contrast_agent_administration_event(
    sphn_contrast_agent:SPHNContrastAgent,
    sphn_administration_route_code:SPHNCode|None,
    start_date_time:datetime,
    context: Context,
    indent:int=0
) -> SPHNContrastAgentAdministrationEvent:
    """
    Create an SPHN Contrast Agent Administration Event object with the provided information.
    Parameters:
        - sphn_contrast_agent: SPHNContrastAgent object.
        - sphn_administration_route_code: The administration route code.
        - start_date_time: The start date and time of the administration event.
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    Returns:
        - SPHNContrastAgentAdministrationEvent: The created SPHN Contrast Agent Administration Event object.
    """

    assert isinstance(sphn_contrast_agent, SPHNContrastAgent)
    assert sphn_administration_route_code is None or isinstance(sphn_administration_route_code, SPHNCode)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger
    data_store = context.data_store
    sphn_schema = context.sphn_schema

    logger.debug(" "*(indent+0) + "Start creating an SPHN Contrast Agent Administration Event object...")

    sphn_contrast_agent_administration_event = SPHNContrastAgentAdministrationEvent(
        sphn_schema = sphn_schema,
        has_start_date_time=start_date_time,
        has_drug=sphn_contrast_agent,
        sphn_administration_route_code=sphn_administration_route_code,
        has_subject_pseudo_identifier = data_store.sphn_subject_pseudo_identifier,
        has_source_system_list = [data_store.sphn_source_system]
    )

    logger.debug(" "*(indent+0) + "Done  creating SPHN Contrast Agent Administration Event object.")

    return sphn_contrast_agent_administration_event


#
#  Edwin 2026-09-20
#
def process_contrast_bolus_agent_sequence(contrast_bolus_agent_sequence:Sequence, context: Context, indent:int=0) -> SPHNContrastAgent|None:
    """
    Process the DICOM ContrastBolusAgentSequence and return an SPHNContrastAgent object, if any.
    Parameters:
        - contrast_bolus_agent_sequence (Sequence): The DICOM ContrastBolusAgentSequence.
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(contrast_bolus_agent_sequence, Sequence)
    assert isinstance(context, Context)
    assert isinstance(indent, int)

    logger = context.logger
    data_store = context.data_store
    sphn_schema = context.sphn_schema
    
    sphn_contrast_agent_active_ingredient_list = []

    for index, dataset_item in enumerate(contrast_bolus_agent_sequence, start=1):

        logger.debug(" "*(indent+2) + f"Processing DICOM ContrastBolusAgentSequence item {index}/{len(contrast_bolus_agent_sequence)}")

        assert isinstance(dataset_item, Dataset)

        code_value = get_code_value_from_dicom(dataset_item, context, indent=indent+2)
        coding_scheme_designator = get_coding_scheme_designator_from_dicom(dataset_item, context, indent=indent+2)
        #coding_scheme_version = get_coding_scheme_version_from_dicom(dataset_item, context, indent=indent+2)
        code_meaning = get_code_meaning_from_dicom(dataset_item, context, indent=indent+2)
        #code_value_long = get_long_code_value_from_dicom(dataset_item, context, indent=indent+2)
        #urn_code_value = get_urn_code_value_from_dicom(dataset_item, context, indent=indent+2)

        # Add the contrast bolus agent code to the data store dictionary for statistical purposes
        data_store.add_contrast_bolus_agent_sequence_code_to_dict(coding_scheme_designator, code_value, code_meaning)

        if code_value is not None and coding_scheme_designator is not None:

            logger.debug(" "*(indent+4) + f"DICOM ContrastBolusAgentSequence has coding scheme designator '{coding_scheme_designator}' and code value '{code_value}' with meaning '{code_meaning}'")

            # Create the SPHN Contrast Agent Active Ingredient object
            sphn_contrast_agent_active_ingredient = create_sphn_contrast_agent_active_ingredient(
                coding_scheme_designator=coding_scheme_designator,
                code_value=code_value,
                code_meaning=code_meaning,
                context=context,
                indent=indent+6
            )

            # It is possible that the creation of the SPHN Contrast Agent Active Ingredient object failed
            # in case the DICOM code could not be mapped to a valid SPHN SNOMED-CT code
            if sphn_contrast_agent_active_ingredient is not None:

                # Add to the list if it is not already in the list
                if not already_in_list(sphn_contrast_agent_active_ingredient, sphn_contrast_agent_active_ingredient_list):
                    sphn_contrast_agent_active_ingredient_list.append(sphn_contrast_agent_active_ingredient)
                else:
                    logger.debug(" "*(indent+4) + "SPHN Contrast Agent Active Ingredient is already in the list of SPHN Contrast Agent Active Ingredients")

            else:
                logger.debug(" "*(indent+4) + f"DICOM ContrastBolusAgentSequence item {index} could not be converted to a SPHN Contrast Agent Active Ingredient object")
        else:
            logger.debug(" "*(indent+4) + f"DICOM ContrastBolusAgentSequence item {index} has no coding scheme designator or code value")
            data_store.add_unknown_contrast_bolus_agent_sequence_code_to_dict(coding_scheme_designator, code_value, code_meaning)

    if len(sphn_contrast_agent_active_ingredient_list) == 0:
        logger.debug(" "*(indent+4) + "No valid SPHN Contrast Agent Active Ingredients could be created from the DICOM ContrastBolusAgentSequence")
        return None

    # Create the SPHN Contrast Agent object
    # ToDo Edwin Note: Multiple active ingredients can not be included yet, update this once the SPHN schema supports it
    sphn_contrast_agent = SPHNContrastAgent(
        sphn_schema = sphn_schema,
        has_active_ingredient=sphn_contrast_agent_active_ingredient_list[0],
        has_source_system_list=[data_store.sphn_source_system]
    )

    return sphn_contrast_agent


#
#  Edwin 2026-09-20
#
def create_sphn_contrast_agent_active_ingredient(coding_scheme_designator: str, code_value: str, code_meaning: str|None, context: Context, indent: int=0) -> SPHNContrastAgentActiveIngredient|None:
    """
    Converts the DICOM Contrast Agent component defined by the coding scheme designator and code value to a SPHN Contrast Agent Active Ingredient object.
    Parameters:
        - coding_scheme_designator: The coding scheme designator for the contrast agent component, as listed in DICOM
        - code_value: The code value for the contrast agent component, as listed in DICOM
        - code_meaning: The code meaning for the contrast agent component, as listed in DICOM
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert is_valid_string(coding_scheme_designator)
    assert is_valid_string(code_value)
    assert code_meaning is None or is_valid_string(code_meaning)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger
    data_store = context.data_store
    sphn_schema = context.sphn_schema

    # Check if it is a known DICOM contrast agent code, otherwise check if it is a DICOM contrast ingredient code instead

    # Try to convert the DICOM coding scheme designator and code value, mostly SNOMED-CT code ("medicinal product") to the corresponding SPHN SNOMED-CT code ("substance")
    result = DataConverter.dicom_contrast_agent_code_to_sphn_active_ingredient_snomed_code_dict.get((coding_scheme_designator.upper(), code_value), None)

    # If the result is None, try again using the contrast ingredient code dict
    if result is None:
        result = DataConverter.dicom_contrast_ingredient_code_to_sphn_active_ingredient_snomed_code_dict.get((coding_scheme_designator.upper(), code_value), None)

    # Check again
    if result is None:
        logger.debug(" "*(indent+0) + f"The DICOM coding scheme designator: '{coding_scheme_designator}' and code value: '{code_value}' has no corresponding SPHN SNOMED-CT code in the DataConverter")
        data_store.add_unknown_contrast_bolus_agent_sequence_code_to_dict(context, coding_scheme_designator, code_value, code_meaning, indent=indent)
        # ToDo: Edwin: Perhaps add a generic SPHN code for unknown contrast agents
        return None

    assert isinstance(result, tuple) and len(result) == 3
    assert all(is_valid_string(item) for item in result)

    active_ingredient_coding_scheme_designator = result[0]
    active_ingredient_code_value = result[1]
    active_ingredient_code_descr = result[2]

    sphn_code = SPHNCode( 
        sphn_schema = sphn_schema,
        has_coding_system_and_version = active_ingredient_coding_scheme_designator,
        has_identifier = active_ingredient_code_value,
        has_name = active_ingredient_code_descr
        )
    sphn_contrast_agent_active_ingredient = SPHNContrastAgentActiveIngredient(
        sphn_schema = sphn_schema,
        has_code = sphn_code,
        has_source_system_list = [data_store.sphn_source_system]
        )

    logger.debug(" "*(indent+0) + f"The DICOM coding scheme designator: '{coding_scheme_designator}' and code value: '{code_value}'" + 
                f" with meaning '{code_meaning}' was successfully converted to an SPHN Contrast Agent Active Ingredient object" +
                f" with coding scheme designator '{active_ingredient_coding_scheme_designator}' and code value '{active_ingredient_code_value}'" +
                f" and code meaning '{active_ingredient_code_descr}'")

    return sphn_contrast_agent_active_ingredient


#
#  Edwin 2026-09-29
#
def process_contrast_bolus_agent_dict(contrast_agent_dict: dict, context: Context, indent: int=0) -> SPHNContrastAgent|None:
    """
    Process the DICOM Contrast Agent component defined in the contrast_agent_dict and return an SPHNContrastAgent object, if any.
    Parameters:
        - contrast_agent_dict: A dictionary containing the extracted contrast agent information from the DICOM data (see below)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)

    contrast_agent_dict is a dictionary representing an extracted contrast agent:
        {   
            "agent": "agent name",
            "concentration": integer|None,
            "dose": {
                "value": int|float|None,
                "unit": "ml"|"mg"|None
            }
        }
    """

    # Check
    assert isinstance(contrast_agent_dict, dict)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger
    data_store = context.data_store
    sphn_schema = context.sphn_schema

    trade_name = None

    # Get the concentration as part of the name of the contrast agent from the dictionary
    concentration = contrast_agent_dict.get("concentration", None)
    if concentration is not None:
        assert isinstance(concentration, int)

    # Get the name of the contrast agent from the dictionary
    agent_name = contrast_agent_dict.get("agent", None)
    if agent_name is None:
        logger.debug(" "*(indent+0) + "Contrast agent name is missing in the provided dictionary")
        return None
    
    assert is_valid_string(agent_name)

    # Check if the agent_name is a trade name
    # Note: Case-sensitive lookup in the DICOM contrast agent trade name dictionary. 
    #       It should not be a problem as the "extract_contrast_agents" function already normalizes the trade names
    #       to match the case used in the dictionary (in case it is a trade name).
    if agent_name in DataConverter.dicom_contrast_agent_trade_name_dict:
        logger.debug(" "*(indent+0) + f"Contrast agent '{agent_name}' is identified as a trade name")
        trade_name = agent_name

        sphn_contrast_agent = process_contrast_bolus_agent_trade_name(trade_name, concentration, context, indent=indent+2)
        if sphn_contrast_agent is None:
            raise ValueError("This should never happen as the trade name was found in the table.")

    # Check if the agent_name is a dicom contrast agent name
    # Note: Case-sensitive lookup in the DICOM contrast agent name dictionary. 
    #       It should not be a problem as the "extract_contrast_agents" function already normalizes the dicom contrast agent names
    #       to match the case used in the dictionary (in case it is a dicom contrast agent name).
    # Note: In case there are multiple generic names, they are added as separate contrast agents, but could potentially have originated from the same article.
    elif agent_name in DataConverter.dicom_contrast_agent_generic_name_dict:
        logger.debug(" "*(indent+0) + f"Contrast agent '{agent_name}' is identified as a generic DICOM contrast agent name")
        generic_name = agent_name

        sphn_contrast_agent = process_contrast_bolus_agent_generic_name(generic_name, context, indent=indent+2)
        if sphn_contrast_agent is None:
            raise ValueError("This should never happen as the generic DICOM contrast agent name was found in the table.")

    # Check if the agent_name is an DICOM active ingredient name
    # Note: Case-sensitive lookup in the DICOM contrast agent active ingredient dictionary. 
    #       It should not be a problem as the "extract_contrast_agents" function already normalizes the active ingredient names
    #       to match the case used in the dictionary (in case it is an active ingredient name).
    # Note: In case there are multiple ingredient names, they are added as separate contrast agents, but could potentially have originated from the same article.    
    elif agent_name in DataConverter.dicom_contrast_ingredient_name_dict:
        logger.debug(" "*(indent+0) + f"Contrast agent '{agent_name}' is identified as a DICOM active ingredient name")
        active_ingredient_name = agent_name

        sphn_contrast_agent = process_contrast_bolus_agent_active_ingredient_name(active_ingredient_name, context=context, indent=indent+2)
        if sphn_contrast_agent is None:
            raise ValueError("This should never happen as the DICOM active ingredient name was found in the table.")

    else:
        raise ValueError("This should never happen as the contrast agent name was originally obtained from one of the dictionaries by the extract_contrast_agents function.")

    # ToDo: Edwin 2026-09-23: Below, the dose

    # Get the dose of the contrast agent from the dictionary
    dose_dict = contrast_agent_dict.get("dose", None)
    dose_value = None
    dose_unit = None
    if dose_dict is not None:
        assert isinstance(dose_dict, dict)
        dose_value = dose_dict.get("value", None)
        if dose_value is not None:
            assert isinstance(dose_value, (int, float))
        dose_unit = dose_dict.get("unit", None)
        if dose_unit is not None:
            assert dose_unit in ["ml", "mg"]

    return sphn_contrast_agent


#
#  Edwin 2026-09-21
#
def process_contrast_bolus_agent_trade_name(trade_name:str, concentration: int|None, context: Context, indent:int=0) -> SPHNContrastAgent:
    """
    Process the DICOM contrast agent trade name and return a SPHNContrastAgent object
    Parameters:
        - trade_name: The DICOM contrast agent trade name in lower case.
        - concentration: The concentration of the contrast agent as part of the name (can be None if not available)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert is_valid_string(trade_name)
    assert concentration is None or isinstance(concentration, int)
    assert isinstance(context, Context)
    assert isinstance(indent, int)
    assert trade_name in DataConverter.dicom_contrast_agent_trade_name_dict

    logger = context.logger
    data_store = context.data_store
    sphn_schema = context.sphn_schema

    sphn_contrast_agent_active_ingredient_list = []

    # Get the DICOM contrast agent code list
    # Note: Case-sensitive lookup in the DICOM contrast agent trade name dictionary. 
    #       It should not be a problem as the "extract_contrast_agents" function already normalizes the trade names
    #       to match the case used in the dictionary.
    result = DataConverter.dicom_contrast_agent_trade_name_dict.get(trade_name, None)

    # Check the format of the result
    assert isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], list)

    # Get the corresponding DICOM contrast agent code(s) for the trade name from the data_converter
    dicom_contrast_agent_code_list = result[1]

    logger.debug(" "*(indent+2) + f"DICOM contrast agent found with {len(dicom_contrast_agent_code_list)} item(s)")

    for index, dicom_contrast_agent in enumerate(dicom_contrast_agent_code_list, start=1):

        logger.debug(" "*(indent+4) + f"Processing DICOM contrast agent code {index}/{len(dicom_contrast_agent_code_list)}")

        # Check the format of the dicom_contrast_agent entry
        assert isinstance(dicom_contrast_agent, tuple) and len(dicom_contrast_agent) == 3
        assert all(is_valid_string(item) for item in dicom_contrast_agent)

        coding_scheme_designator = dicom_contrast_agent[0]
        code_value = dicom_contrast_agent[1]
        code_descr = dicom_contrast_agent[2]

        # Create the SPHN Contrast Agent Active Ingredient object
        sphn_contrast_agent_active_ingredient = create_sphn_contrast_agent_active_ingredient(
            coding_scheme_designator=coding_scheme_designator,
            code_value=code_value,
            code_meaning=code_descr,
            context=context,
            indent=indent+2
        )

        # The creation of the SPHN Contrast Agent Active Ingredient object should not have failed
        # as the DICOM code should always be mappable to a valid SPHN SNOMED-CT code
        assert sphn_contrast_agent_active_ingredient is not None 

        # Add to the list if it is not already in the list
        if not already_in_list(sphn_contrast_agent_active_ingredient, sphn_contrast_agent_active_ingredient_list):
            sphn_contrast_agent_active_ingredient_list.append(sphn_contrast_agent_active_ingredient)
        else:
            logger.debug(" "*(indent+4) + "SPHN Contrast Agent Active Ingredient is already in the list of SPHN Contrast Agent Active Ingredients")

    # Create the SPHN Drug Article object with the trade name and concentration (if available)
    if concentration is not None:
        sphn_drug_article = SPHNDrugArticle(
            sphn_schema = sphn_schema,
            has_name=f"{trade_name}-{concentration}",
            has_source_system_list=[data_store.sphn_source_system]
        )
    else:
        sphn_drug_article = SPHNDrugArticle(
            sphn_schema = sphn_schema,
            has_name=trade_name,
            has_source_system_list=[data_store.sphn_source_system]
        )

    # Create the SPHN Contrast Agent object
    # ToDo Edwin Note: Multiple active ingredients can not be included yet, update this once the SPHN schema supports it
    sphn_contrast_agent = SPHNContrastAgent(
        sphn_schema = sphn_schema,
        has_active_ingredient=sphn_contrast_agent_active_ingredient_list[0],
        has_article=sphn_drug_article,
        has_source_system_list=[data_store.sphn_source_system]
    )

    return sphn_contrast_agent


#
#  Edwin 2026-09-23
#
def process_contrast_bolus_agent_generic_name(generic_name:str, context: Context, indent:int=0) -> SPHNContrastAgent:
    """
    Process the DICOM contrast agent generic name and return a SPHNContrastAgent object
    Parameters:
        - generic_name: The DICOM contrast agent generic name
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert is_valid_string(generic_name)
    assert isinstance(context, Context)
    assert isinstance(indent, int)
    assert generic_name in DataConverter.dicom_contrast_agent_generic_name_dict

    logger = context.logger
    data_store = context.data_store
    sphn_schema = context.sphn_schema

    sphn_contrast_agent_active_ingredient_list = []

    # Get the DICOM contrast agent code list
    # Note: Case-sensitive lookup in the DICOM contrast agent generic name dictionary. 
    #       It should not be a problem as the "extract_contrast_agents" function already normalizes the generic names
    #       to match the case used in the dictionary.
    result = DataConverter.dicom_contrast_agent_generic_name_dict.get(generic_name, None)

    # Check the format of the result
    assert isinstance(result, tuple) and len(result) == 2
    assert all(is_valid_string(item) for item in result)
    
    logger.debug(" "*(indent+2) + "DICOM contrast agent code found.")

    coding_scheme_designator = result[0]
    code_value = result[1]
    code_descr = generic_name

    # Create the SPHN Contrast Agent Active Ingredient object
    sphn_contrast_agent_active_ingredient = create_sphn_contrast_agent_active_ingredient(
        coding_scheme_designator=coding_scheme_designator,
        code_value=code_value,
        code_meaning=code_descr,
        context=context,
        indent=indent+4
    )

    # The creation of the SPHN Contrast Agent Active Ingredient object should not have failed
    # as the DICOM code should always be mappable to a valid SPHN SNOMED-CT code
    assert sphn_contrast_agent_active_ingredient is not None 

    # Add to the list (There should only be one active ingredient)
    sphn_contrast_agent_active_ingredient_list = [sphn_contrast_agent_active_ingredient]

    # Create the SPHN Contrast Agent object
    # ToDo Edwin Note: Multiple active ingredients can not be included yet, update this once the SPHN schema supports it
    sphn_contrast_agent = SPHNContrastAgent(
        sphn_schema = sphn_schema,
        has_active_ingredient=sphn_contrast_agent_active_ingredient_list[0],
        has_source_system_list=[data_store.sphn_source_system]
    )

    return sphn_contrast_agent

#
#  Edwin 2026-09-23
#
def process_contrast_bolus_agent_active_ingredient_name(ingredient_name:str, context: Context, indent:int=0) -> SPHNContrastAgent:
    """
    Process the DICOM contrast agent active ingredient name and return a SPHNContrastAgent object
    Parameters:
        - ingredient_name: The DICOM contrast agent active ingredient name
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert is_valid_string(ingredient_name)
    assert isinstance(context, Context)
    assert isinstance(indent, int)
    assert ingredient_name in DataConverter.dicom_contrast_ingredient_name_dict

    logger = context.logger
    data_store = context.data_store
    sphn_schema = context.sphn_schema

    sphn_contrast_agent_active_ingredient_list = []

    # Get the DICOM contrast agent code list
    # Note: Case-sensitive lookup in the DICOM contrast agent active ingredient name dictionary. 
    #       It should not be a problem as the "extract_contrast_agents" function already normalizes the ingredient names
    #       to match the case used in the dictionary.
    result = DataConverter.dicom_contrast_ingredient_name_dict.get(ingredient_name, None)

    # Check the format of the result
    assert isinstance(result, tuple) and len(result) == 2
    assert all(is_valid_string(item) for item in result)

    logger.debug(" "*(indent+2) + "DICOM contrast agent ingredient code found.")

    coding_scheme_designator = result[0]
    code_value = result[1]
    code_descr = ingredient_name

    # Create the SPHN Contrast Agent Active Ingredient object
    sphn_contrast_agent_active_ingredient = create_sphn_contrast_agent_active_ingredient(
        coding_scheme_designator=coding_scheme_designator,
        code_value=code_value,
        code_meaning=code_descr,
        context=context,
        indent=indent+4
    )

    # The creation of the SPHN Contrast Agent Active Ingredient object should not have failed
    # as the DICOM code should always be mappable to a valid SPHN SNOMED-CT code
    assert sphn_contrast_agent_active_ingredient is not None 

    # Add to the list (There should only be one active ingredient)
    sphn_contrast_agent_active_ingredient_list = [sphn_contrast_agent_active_ingredient]

    # Create the SPHN Contrast Agent object
    # ToDo Edwin Note: Multiple active ingredients can not be included yet, update this once the SPHN schema supports it
    sphn_contrast_agent = SPHNContrastAgent(
        sphn_schema = sphn_schema,
        has_active_ingredient=sphn_contrast_agent_active_ingredient_list[0],
        has_source_system_list=[data_store.sphn_source_system]
    )

    return sphn_contrast_agent


#
#  Edwin 2026-09-23
#
def process_contrast_bolus_ingredient(ingredient_term:str, context: Context, indent:int=0) -> SPHNContrastAgent|None:
    """
    Process the DICOM contrast ingredient term and return an SPHNContrastAgent object, if any.
    Parameters:
        - ingredient_term: The DICOM contrast ingredient term.
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert is_valid_string(ingredient_term)
    assert isinstance(context, Context)
    assert isinstance(indent, int)
    
    logger = context.logger
    data_store = context.data_store
    sphn_schema = context.sphn_schema

    sphn_contrast_agent_active_ingredient_list = []

    term_upper_case = ingredient_term.upper()

    # Get the DICOM contrast ingredient code
    result = DataConverter.dicom_contrast_ingredient_term_dict.get(term_upper_case, None)

    # Check if the ingredient term is known
    if result is None:
        logger.debug(" "*(indent+2) + f"DICOM contrast ingredient term '{ingredient_term}' is not in the list of known DICOM contrast ingredient terms")
        return None
    
    # Check the format of the result
    assert isinstance(result, tuple) and len(result) == 3
    assert all(is_valid_string(item) for item in result)

    coding_scheme_designator = result[0]
    code_value = result[1]
    code_descr = result[2]

    # Create the SPHN Contrast Agent Active Ingredient object
    sphn_contrast_agent_active_ingredient = create_sphn_contrast_agent_active_ingredient(
        coding_scheme_designator=coding_scheme_designator,
        code_value=code_value,
        code_meaning=code_descr,
        context=context,
        indent=indent+4
    )

    # The creation of the SPHN Contrast Agent Active Ingredient object should not have failed
    # as the DICOM code should always be mappable to a valid SPHN SNOMED-CT code
    assert sphn_contrast_agent_active_ingredient is not None 

    # Add to the list (There should only be one active ingredient)
    sphn_contrast_agent_active_ingredient_list = [sphn_contrast_agent_active_ingredient]

    # Create the SPHN Contrast Agent object
    # ToDo Edwin Note: Multiple active ingredients can not be included yet, update this once the SPHN schema supports it
    sphn_contrast_agent = SPHNContrastAgent(
        sphn_schema = sphn_schema,
        has_active_ingredient=sphn_contrast_agent_active_ingredient_list[0],
        has_source_system_list=[data_store.sphn_source_system]
    )

    return sphn_contrast_agent


#
#  Edwin 2026-09-29
#
def process_contrast_bolus_administration_route_sequence(contrast_bolus_administration_route_sequence:Sequence, context: Context, indent:int=0) -> SPHNCode|None:
    """
    Process the DICOM ContrastBolusAdministrationRouteSequence and return an SPHNcode object for the SPHN hasAdministrationRouteCode, if any.
    Parameters:
        - contrast_bolus_administration_route_sequence (Sequence): The DICOM ContrastBolusAdministrationRouteSequence.
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(contrast_bolus_administration_route_sequence, Sequence)
    assert isinstance(context, Context)
    assert isinstance(indent, int)

    logger = context.logger
    data_store = context.data_store
    sphn_schema = context.sphn_schema
    
    # There should only be one item in the ContrastBolusAdministrationRouteSequence
    
    assert len(contrast_bolus_administration_route_sequence) == 1

    dataset_item = contrast_bolus_administration_route_sequence[0]

    assert isinstance(dataset_item, Dataset)

    # Get the coded info from DICOM
    coding_scheme_designator = get_coding_scheme_designator_from_dicom(dataset_item, context, indent=indent+2)
    code_value = get_code_value_from_dicom(dataset_item, context, indent=indent+2)
    code_descr = get_code_meaning_from_dicom(dataset_item, context, indent=indent+2)

    # Add the administration route to the data store dictionary for statistical purposes
    data_store.add_contrast_bolus_administration_route_sequence_code_to_dict(coding_scheme_designator, code_value, code_descr)

    if coding_scheme_designator is None or code_value is None:
        logger.debug(" "*(indent+0) + f"DICOM ContrastBolusAdministrationRouteSequence has incomplete coding information: coding scheme designator '{coding_scheme_designator}', code value '{code_value}'")
        data_store.add_unknown_contrast_bolus_administration_route_sequence_code_to_dict(context, coding_scheme_designator, code_value, code_descr, indent=indent)
        return None

    logger.debug(" "*(indent+4) + f"DICOM ContrastBolusAdministrationRouteSequence has coding scheme designator '{coding_scheme_designator}' and code value '{code_value}' with description '{code_descr}'")

    # Try to convert the DICOM coding scheme designator and code value to a SPHN administration route SNOMED-CT code
    result = DataConverter.administration_routes_list.get((coding_scheme_designator, code_value), None)

    # Check if the route is known
    if result is None:
        logger.debug(" "*(indent+0) + f"The coding scheme designator: '{coding_scheme_designator}' and code value: '{code_value}' has no corresponding code in the DataConverter")
        data_store.add_unknown_contrast_bolus_administration_route_sequence_code_to_dict(context, coding_scheme_designator, code_value, code_descr, indent=indent)
        return None

    assert isinstance(result, tuple) and len(result) == 3
    assert all(is_valid_string(item) for item in result)

    administration_route_coding_scheme_designator = result[0]
    administration_route_code_value = result[1]
    administration_route_code_descr = result[2]

    sphn_code = SPHNCode( 
        sphn_schema = sphn_schema,
        has_coding_system_and_version = administration_route_coding_scheme_designator,
        has_identifier = administration_route_code_value,
        has_name = administration_route_code_descr
        )

    logger.debug(" "*(indent+0) + f"The DICOM coding scheme designator: '{coding_scheme_designator}' and code value: '{code_value}'" + 
                f" with meaning '{code_descr}' was successfully converted to an SPHN Contrast Bolus Administration Route" +
                f" with coding scheme designator '{administration_route_coding_scheme_designator}' and code value '{administration_route_code_value}'" +
                f" and code description '{administration_route_code_descr}'")

    return sphn_code


# ---------------------------------------------------------------------------------------------------------------------
# Functions for reading DICOM tags in the Enhanced Contrast/Bolus module
# ---------------------------------------------------------------------------------------------------------------------

#
#  Edwin 2026-09-02
#
def get_enhanced_contrast_bolus_module_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> None:
    """
    Sets the enhanced contrast bolus module information in the data_store.
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger
    data_store = context.data_store


# ---------------------------------------------------------------------------------------------------------------------
# Functions for reading DICOM tags related to contrast bolus information
# ---------------------------------------------------------------------------------------------------------------------

#
#  Edwin 2026-09-20
#
def get_contrast_bolus_agent_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM ContrastBolusAgent tag
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

    # Get the value of the DICOM ContrastBolusAgent tag
    value = dataset.get("ContrastBolusAgent", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAgent tag was not found")  
        return None

    assert isinstance(value, str)

    # Remove whitespace
    contrast_bolus_agent = value.strip()

    # Check if value is not empty
    if len(contrast_bolus_agent) == 0:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAgent tag value contains only whitespace")
        return None

    assert is_valid_string(contrast_bolus_agent)

    return contrast_bolus_agent


#
# Edwin 2026-08-31
#
def get_contrast_bolus_agent_sequence_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence (list of Datasets) in the DICOM ContrastBolusAgentSequence tag
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

    # Get the value of the DICOM ContrastBolusAgentSequence tag
    value = dataset.get("ContrastBolusAgentSequence", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAgentSequence tag was not found")
        return None

    assert isinstance(value, Sequence)

    if len(value) == 0:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAgentSequence tag is empty")
        return None

    return value


#
#  Edwin 2026-09-02
#
def get_contrast_bolus_t1_relaxivity_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the float corresponding to the value of the DICOM ContrastBolusT1Relaxivity tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,0013)
    # Type:	                Optional (3)
    # Keyword:	            ContrastBolusT1Relaxivity
    # Value Multiplicity	1
    # Value Representation:	Single (FL)
    
    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM ContrastBolusT1Relaxivity tag
    value = dataset.get("ContrastBolusT1Relaxivity", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusT1Relaxivity tag was not found")  
        return None

    assert isinstance(value, float)

    contrast_bolus_t1_relaxivity = value

    if contrast_bolus_t1_relaxivity < 0:
        logger.warning(" "*(indent+0) + f"DICOM ContrastBolusT1Relaxivity: '{contrast_bolus_t1_relaxivity}' is probably not a valid value.")
        return None

    return contrast_bolus_t1_relaxivity


#
# Edwin 2026-08-31
#
def get_contrast_bolus_administration_route_sequence_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence / the list of Datasets in the DICOM ContrastBolusAdministrationRouteSequence tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Keyword:              ContrastBolusAdministrationRouteSequence
    # Tag:                  (0018,0014)
    # Value Representation: Sequence (SQ)
    # Type:	                Optional (3)
    # Value Multiplicity:   1


    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM ContrastBolusAdministrationRouteSequence tag
    value = dataset.get("ContrastBolusAdministrationRouteSequence", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAdministrationRouteSequence tag was not found")
        return None

    assert isinstance(value, Sequence)

    if len(value) == 0:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAdministrationRouteSequence tag is empty")
        return None

    return value


#
#  Edwin 2026-08-31
#
def get_contrast_bolus_route_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM ContrastBolusRoute tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1040)
    # Type:	                Optional (3)
    # Keyword:	            ContrastBolusRoute
    # Value Multiplicity	1
    # Value Representation:	Long String (LO)
    
    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM ContrastBolusRoute tag
    value = dataset.get("ContrastBolusRoute", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusRoute tag was not found")  
        return None

    assert isinstance(value, str)

    # Remove whitespace
    contrast_bolus_route = value.strip()

    # Check if value is not empty
    if len(contrast_bolus_route) == 0:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusRoute tag value contains only whitespace")
        return None

    assert is_valid_string(contrast_bolus_route)

    return contrast_bolus_route


#
#  Edwin 2026-08-31
#
def get_contrast_bolus_volume_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> DSfloat|DSdecimal|None:
    """
    Returns the float corresponding to the value of the DICOM ContrastBolusVolume tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1041)
    # Type:	                Optional (3)
    # Keyword:	            ContrastBolusVolume
    # Value Multiplicity	1
    # Value Representation:	Decimal String (DS)
    
    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM ContrastBolusVolume tag
    value = dataset.get("ContrastBolusVolume", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusVolume tag was not found")  
        return None

    assert isinstance(value, (DSfloat, DSdecimal))

    contrast_bolus_volume = value

    if contrast_bolus_volume < 0:
        logger.warning(" "*(indent+0) + f"DICOM ContrastBolusVolume: '{contrast_bolus_volume}' is probably not a valid value.")
        return None

    return contrast_bolus_volume


#
# Edwin 2026-08-31
#
def get_contrast_bolus_start_time_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM ContrastBolusStartTime tag
        - dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1042)
    # Type:	                Optional (3)
    # Keyword:              ContrastBolusStartTime
    # Value Multiplicity:   1
    # Value Representation: Time (TM)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM ContrastBolusStartTime tag
    value = dataset.get("ContrastBolusStartTime", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusStartTime tag was not found")  
        return None

    assert isinstance(value, str)

    contrast_bolus_start_time = value.strip()

    if len(contrast_bolus_start_time) == 0:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusStartTime tag contains only whitespace")
        return None

    assert is_valid_string(contrast_bolus_start_time)

    return contrast_bolus_start_time


#
# Edwin 2026-08-31
#
def get_contrast_bolus_stop_time_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM ContrastBolusStopTime tag
        - dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1043)
    # Type:	                Optional (3)
    # Keyword:              ContrastBolusStopTime
    # Value Multiplicity:   1
    # Value Representation: Time (TM)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM ContrastBolusStopTime tag
    value = dataset.get("ContrastBolusStopTime", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusStopTime tag was not found")  
        return None

    assert isinstance(value, str)

    # Remove whitespace
    contrast_bolus_stop_time = value.strip()

    # Check if value is not empty
    if len(contrast_bolus_stop_time) == 0:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusStopTime tag contains only whitespace")
        return None

    assert is_valid_string(contrast_bolus_stop_time)

    return contrast_bolus_stop_time


#
#  Edwin 2026-08-31
#
def get_contrast_bolus_total_dose_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> DSfloat|DSdecimal|None:
    """
    Returns the float corresponding to the value of the DICOM ContrastBolusTotalDose tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1044)
    # Type:	                Optional (3)
    # Keyword:	            ContrastBolusTotalDose
    # Value Multiplicity	1
    # Value Representation:	Decimal String (DS)
    
    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM ContrastBolusTotalDose tag
    value = dataset.get("ContrastBolusTotalDose", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusTotalDose tag was not found")  
        return None

    assert isinstance(value, (DSfloat, DSdecimal))

    contrast_bolus_total_dose = value

    if contrast_bolus_total_dose < 0:
        logger.warning(" "*(indent+0) + f"DICOM ContrastBolusTotalDose: '{contrast_bolus_total_dose}' is probablynot a valid value.")
        return None

    return contrast_bolus_total_dose


#
# Edwin 2026-08-31
#
def get_contrast_flow_rate_list_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> list[DSfloat|DSdecimal|None]|None:
    """
    Returns a list of values corresponding to the DICOM ContrastFlowRate tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    Note: The output list with values can have a corresponding list with Flow Duration. Therefore, 
        the order of values in this list should correspond to the order of Flow Duration in the other list
    """

    # Tag:                  (0018,1046)
    # Type:	                Optional (3)
    # Keyword:              ContrastFlowRate
    # Value Multiplicity:   1-n
    # Value Representation: Decimal String (DS)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Create an empty list to store the values of the DICOM ContrastFlowRate tag
    contrast_flow_rate_float_list = []

    # Get the value of the DICOM ContrastFlowRate tag
    value = dataset.get("ContrastFlowRate", None)

    # Check if the value is None
    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastFlowRate tag was not found")
        return None

    # It could be a multi-valued tag, a list of DSfloat or DSdecimal
    elif isinstance(value, MultiValue):

        for value_item in value:
            if isinstance(value_item, (DSfloat, DSdecimal)):
                # Add value_item to the list
                contrast_flow_rate_float_list.append(value_item)
            elif value_item is None:
                # Add None to the list, to keep the same order
                contrast_flow_rate_float_list.append(None)
            else:
                logger.warning(" "*(indent+0) + "DICOM ContrastFlowRate tag value-item has an unknown format")
                # Add None to the list, to keep the same order
                contrast_flow_rate_float_list.append(None)

    # It could be a single-valued tag, a DSfloat or DSdecimal
    elif isinstance(value, (DSfloat, DSdecimal)):
        # Add value to the list
        contrast_flow_rate_float_list.append(value)

    # Warning otherwise
    else:
        logger.warning(" "*(indent+0) + "DICOM ContrastFlowRate tag value has an unknown format")
        return None

    return contrast_flow_rate_float_list if len(contrast_flow_rate_float_list)>0 else None


#
# Edwin 2026-08-31
#
def get_contrast_flow_duration_list_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> list[DSfloat|DSdecimal|None]|None:
    """
    Returns a list of values corresponding to the DICOM ContrastFlowDuration tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    Note: The output list with values can have a corresponding list with Contrast Flow Rate. Therefore, 
        the order of values in this list should correspond to the order of Contrast Flow Rate in the other list
    """

    # Tag:                  (0018,1047)
    # Type:	                Optional (3)
    # Keyword:              ContrastFlowDuration
    # Value Multiplicity:   1-n
    # Value Representation: Decimal String (DS)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Create an empty list to store the values of the DICOM ContrastFlowDuration tag    
    contrast_flow_duration_float_list = []

    # Get the value of the DICOM ContrastFlowDuration tag
    value = dataset.get("ContrastFlowDuration", None)

    # Check if the value is None
    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastFlowDuration tag was not found")
        return None

    # It could be a multi-valued tag, a list of DSfloat or DSdecimal
    elif isinstance(value, MultiValue):

        for value_item in value:
            if isinstance(value_item, (DSfloat, DSdecimal)):
                # Add value_item to the list
                contrast_flow_duration_float_list.append(value_item)
            elif value_item is None:
                # Add None to the list, to keep the same order
                contrast_flow_duration_float_list.append(None)
            else:
                logger.warning(" "*(indent+0) + "DICOM ContrastFlowDuration tag value-item has an unknown format")
                # Add None to the list, to keep the same order
                contrast_flow_duration_float_list.append(None)

    # It could be a single-valued tag, a DSfloat or DSdecimal
    elif isinstance(value, (DSfloat, DSdecimal)):
        # Add value to the list
        contrast_flow_duration_float_list.append(value)

    # Warning otherwise
    else:
        logger.warning(" "*(indent+0) + "DICOM ContrastFlowDuration tag value has an unknown format")
        return None

    return contrast_flow_duration_float_list if len(contrast_flow_duration_float_list)>0 else None


#
# Edwin 2026-08-31
#
def get_contrast_bolus_ingredient_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM ContrastBolusIngredient tag
        - dataset is a DICOM dataset (DICOM header) that contains DICOM DataElements (tags)
        - context is the Context object that holds the data_store, logger and other relevant information
        - indent is the indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1048)
    # Type:	                Optional (3)
    # Keyword:              ContrastBolusIngredient
    # Value Multiplicity:   1
    # Value Representation: Code String (CS)

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM ContrastBolusIngredient tag
    value = dataset.get("ContrastBolusIngredient", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusIngredient tag was not found")  
        return None
    
    assert isinstance(value, str)
    
    # Remove whitespace
    contrast_bolus_ingredient = value.strip()

    # Check if value is not empty
    if len(contrast_bolus_ingredient) == 0:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusIngredient tag contains only whitespace")
        return None

    assert is_valid_string(contrast_bolus_ingredient)

    return contrast_bolus_ingredient


#
#  Edwin 2026-08-31
#
def get_contrast_bolus_ingredient_concentration_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> DSfloat|DSdecimal|None:
    """
    Returns the value corresponding to the value of the DICOM ContrastBolusIngredientConcentration tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context is the Context object that holds the data_store, logger and other relevant information
        - indent is the indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1049)
    # Type:	                Optional (3)
    # Keyword:	            ContrastBolusIngredientConcentration
    # Value Multiplicity	1
    # Value Representation:	Decimal String (DS)
    
    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM ContrastBolusIngredientConcentration tag
    value = dataset.get("ContrastBolusIngredientConcentration", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusIngredientConcentration tag was not found")  
        return None

    assert isinstance(value, (DSfloat, DSdecimal))

    contrast_bolus_ingredient_concentration = value

    if contrast_bolus_ingredient_concentration < 0:
        logger.warning(" "*(indent+0) + f"DICOM ContrastBolusIngredientConcentration: '{contrast_bolus_ingredient_concentration}' is not a valid value.")
        return None

    return contrast_bolus_ingredient_concentration



#
#  Edwin 2026-09-02
#
def get_contrast_bolus_agent_number_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> int|None:
    """
    Returns the value corresponding to the value of the DICOM ContrastBolusAgentNumber tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context is the Context object that holds the data_store, logger and other relevant information
        - indent is the indentation level for logging (default is 0)
    """

    # Tag:                  (0018,9337)
    # Type:	                Required (1)
    # Keyword:	            ContrastBolusAgentNumber
    # Value Multiplicity	1
    # Value Representation:	Unsigned Short (US)
    
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

    assert isinstance(value, int)

    contrast_bolus_agent_number = value

    if contrast_bolus_agent_number <= 0:
        logger.warning(" "*(indent+0) + f"DICOM ContrastBolusAgentNumber: '{contrast_bolus_agent_number}' is not a valid value.")
        return None

    return contrast_bolus_agent_number


#
# Edwin 2026-09-02
#
def get_contrast_bolus_ingredient_code_sequence_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence / list of Datasets in the DICOM ContrastBolusIngredientCodeSequence tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context is the Context object that holds the data_store, logger and other relevant information
        - indent is the indentation level for logging (default is 0)
    """

    # Keyword:              ContrastBolusIngredientCodeSequence
    # Tag:                  (0018,9338)
    # Value Representation: Sequence (SQ)
    # Type:	                Required, Empty if Unknown (2)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM ContrastBolusIngredientCodeSequence tag
    value = dataset.get("ContrastBolusIngredientCodeSequence", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusIngredientCodeSequence tag was not found")
        return None

    assert isinstance(value, Sequence)

    if len(value) == 0:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusIngredientCodeSequence tag is empty")
        return None

    return value


#
# Edwin 2026-09-02
#
def get_contrast_administration_profile_sequence_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence / list of Datasets in the DICOM ContrastAdministrationProfileSequence tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context is the Context object that holds the data_store, logger and other relevant information
        - indent is the indentation level for logging (default is 0)
    """

    # Keyword:              ContrastAdministrationProfileSequence
    # Tag:                  (0018,9340)
    # Value Representation: Sequence (SQ)
    # Type:	                Optional (3)
    # Value Multiplicity:   1

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM ContrastAdministrationProfileSequence tag
    value = dataset.get("ContrastAdministrationProfileSequence", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastAdministrationProfileSequence tag was not found")
        return None

    assert isinstance(value, Sequence)

    if len(value) == 0:
        logger.debug(" "*(indent+0) + "DICOM ContrastAdministrationProfileSequence tag is empty")
        return None

    return value


#
#  Edwin 2026-09-02
#
def get_contrast_bolus_ingredient_opaque_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM ContrastBolusIngredientOpaque tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context is the Context object that holds the data_store, logger and other relevant information
        - indent is the indentation level for logging (default is 0)
    """

    # Tag:                  (0018,9425)
    # Type:	                Optional (3)
    # Keyword:	            ContrastBolusIngredientOpaque
    # Value Multiplicity	1
    # Value Representation:	Code String (CS)
    
    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM ContrastBolusIngredientOpaque tag
    value = dataset.get("ContrastBolusIngredientOpaque", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusIngredientOpaque tag was not found")  
        return None

    assert isinstance(value, str)

    contrast_bolus_ingredient_opaque = value

    if not contrast_bolus_ingredient_opaque:
        logger.warning(" "*(indent+0) + f"DICOM ContrastBolusIngredientOpaque: '{contrast_bolus_ingredient_opaque}' is not a valid value.")
        return None

    return contrast_bolus_ingredient_opaque


#
#  Edwin 2026-09-02
#
def get_contrast_bolus_ingredient_percent_by_volume_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the float corresponding to the value of the DICOM ContrastBolusIngredientPercentByVolume tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context is the Context object that holds the data_store, logger and other relevant information
        - indent is the indentation level for logging (default is 0)
    """

    # Tag:                  (0052,0001)
    # Type:	                Optional (3)
    # Keyword:	            ContrastBolusIngredientPercentByVolume
    # Value Multiplicity	1
    # Value Representation:	Single (FL)
    
    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM ContrastBolusIngredientPercentByVolume tag
    value = dataset.get("ContrastBolusIngredientPercentByVolume", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusIngredientPercentByVolume tag was not found")  
        return None

    assert isinstance(value, float)

    contrast_bolus_ingredient_percent_by_volume = value

    if contrast_bolus_ingredient_percent_by_volume < 0:
        logger.warning(" "*(indent+0) + f"DICOM ContrastBolusIngredientPercentByVolume: '{contrast_bolus_ingredient_percent_by_volume}' is probably not a valid value.")
        return None

    return contrast_bolus_ingredient_percent_by_volume

