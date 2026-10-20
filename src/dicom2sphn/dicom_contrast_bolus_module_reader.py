"""
dicom_contrast_bolus_tags_reader.py:
    Part of the example dicom2sphn package.
    It contains functions for reading DICOM contrast bolus tags.
"""

from datetime import datetime, time, timedelta

from pydicom import Dataset
from pydicom.multival import MultiValue
from pydicom.sequence import Sequence
from pydicom.valuerep import DA, DT, TM, DSdecimal, DSfloat

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
from .sphn_concepts.sphn_source_system import SPHNSourceSystem
from .sphn_concepts.sphn_substance import SPHNSubstance
from .sphn_concepts.sphn_unit import SPHNUnit
from .tools import complete_dicom_time, is_valid_string

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

    # ToDo: Edwin 2026-10-09 - Implement processing for Contrast / Bolus module
    # ToDo: Edwin 2026-10-09 - Implement processing for Enhanced Contrast / Bolus module

# ---------------------------------------------------------------------------------------------------------------------
# Functions for reading DICOM tags in the "Contrast/Bolus" module
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
    # contrast_bolus_end_time = get_contrast_bolus_stop_time_from_dicom(dataset, context, indent=indent+2)
    # contrast_bolus_total_dose = get_contrast_bolus_total_dose_from_dicom(dataset, context, indent=indent+2)
    # contrast_flow_rate_list = get_contrast_flow_rate_list_from_dicom(dataset, context, indent=indent+2)
    # contrast_flow_duration_list = get_contrast_flow_duration_list_from_dicom(dataset, context, indent=indent+2)
    # contrast_bolus_ingredient_concentration = get_contrast_bolus_ingredient_concentration_from_dicom(dataset, context, indent=indent+2)

    sphn_contrast_agent_administration_event_list = []
    sphn_contrast_agent_list = []
    sphn_administration_route_code: SPHNCode|None = None
    

    # 
    # 1. Check if there is coded information in the ContrastBolusAgentSequence
    #

    contrast_bolus_agent_sequence = get_contrast_bolus_agent_sequence_from_dicom(dataset, context, indent=indent+2)

    if contrast_bolus_agent_sequence is not None:

        assert isinstance(contrast_bolus_agent_sequence, Sequence)

        logger.debug(" "*(indent+0) + f"DICOM ContrastBolusAgentSequence (coded info) found with {len(contrast_bolus_agent_sequence)} item(s)")

        sphn_contrast_agent = process_contrast_bolus_agent_sequence(contrast_bolus_agent_sequence, context, indent+4)

        if sphn_contrast_agent is not None:
            if sphn_contrast_agent not in sphn_contrast_agent_list:
                sphn_contrast_agent_list.append(sphn_contrast_agent)
                logger.debug(" "*(indent+2) + "Added SPHN Contrast Agent")
            else:
                logger.debug(" "*(indent+2) + "SPHN Contrast Agent is already in the list")
        else:            
            logger.debug(" "*(indent+2) + "Failed to create an SPHN Contrast Agent object from DICOM ContrastBolusAgentSequence (coded info).")

    else:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAgentSequence (coded info) was not found or empty.")

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
                if sphn_contrast_agent not in sphn_contrast_agent_list:
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
            if sphn_contrast_agent not in sphn_contrast_agent_list:
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
    # 4. Extract the Contrast/Bolus Administration Route Sequence from the DICOM dataset
    #    and create a SPHN Contrast Agent Administration Route Code object if possible
    # 

    contrast_bolus_administration_route_sequence = get_contrast_bolus_administration_route_sequence_from_dicom(dataset, context, indent=indent+2)

    if contrast_bolus_administration_route_sequence is not None:
        
        assert isinstance(contrast_bolus_administration_route_sequence, Sequence)

        logger.debug(" "*(indent+2) + f"DICOM ContrastBolusAdministrationRouteSequence (coded info) found with {len(contrast_bolus_administration_route_sequence)} item(s)")

        #
        # 4.1. Process each item in the sequence
        #

        # There should be exactly zero or one item(s) in the Contrast/Bolus Administration Route Sequence
        if len(contrast_bolus_administration_route_sequence) == 1:

            sphn_administration_route_code = process_contrast_bolus_administration_route_sequence_item(contrast_bolus_administration_route_sequence[0], context, indent+4)

            if sphn_administration_route_code is None:
                logger.debug(" "*(indent+2) + "Failed to create an SPHN Administration Route Code object from DICOM ContrastBolusAdministrationRouteSequence (coded info).")

        elif len(contrast_bolus_administration_route_sequence) == 0:
            logger.debug(" "*(indent+2) + "No items found in ContrastBolusAdministrationRouteSequence")

        else:
            raise ValueError("Unexpected number of items in ContrastBolusAdministrationRouteSequence")
        
    else:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAdministrationRouteSequence (coded info) is missing or empty.")

    #
    # 5. 
    #        

    #
    # 5. Collect more information for the SPHN Contrast Agent Administration Event object
    #

    # ToDo: Edwin: HERE
    # For test purposes:
    start_datetime_dummy = data_store.fallback_study_datetime

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
                start_datetime=start_datetime_dummy,
                context=context,
                indent=indent+2
            )

            if sphn_contrast_agent_administration_event is None:
                logger.debug(" "*(indent+2) + "Failed to create SPHN Contrast Agent Administration Event object.")
                continue

            logger.debug(" "*(indent+2) + "Done  creating SPHN Contrast Agent Administration Event object.")

            # Add to the list if not already in it
            if sphn_contrast_agent_administration_event not in sphn_contrast_agent_administration_event_list:
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
            start_datetime=start_datetime_dummy,
            context=context,
            indent=indent+2
        )
        
        if sphn_contrast_agent_administration_event is None:
            logger.debug(" "*(indent+2) + "Failed to create SPHN Contrast Agent Administration Event object.")
        else:
            logger.debug(" "*(indent+2) + "Done  creating SPHN Contrast Agent Administration Event object.")
            # Add to the list if not already in it
            if sphn_contrast_agent_administration_event not in sphn_contrast_agent_administration_event_list:
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

        sphn_contrast_agent = create_sphn_contrast_agent(
            active_ingredient_list=[sphn_contrast_agent_active_ingredient],
            article=None,
            context=context,
            indent=indent+2
        )

        # We now have one contrast agent and can create a single administration event
        logger.debug(" "*(indent+2) + "Start creating SPHN Contrast Agent Administration Event object")

        sphn_contrast_agent_administration_event = create_sphn_contrast_agent_administration_event(
            sphn_contrast_agent=sphn_contrast_agent,
            sphn_administration_route_code=sphn_administration_route_code,
            start_datetime=start_datetime_dummy,
            context=context,
            indent=indent+2
        )

        if sphn_contrast_agent_administration_event is None:
            logger.debug(" "*(indent+2) + "Failed to create SPHN Contrast Agent Administration Event object.")
        else:
            logger.debug(" "*(indent+2) + "Done  creating SPHN Contrast Agent Administration Event object.")
            # Add to the list if not already in it
            if sphn_contrast_agent_administration_event not in sphn_contrast_agent_administration_event_list:
                sphn_contrast_agent_administration_event_list.append(sphn_contrast_agent_administration_event)
                logger.debug(" "*(indent+2) + "Added SPHN Contrast Agent Administration Event object to the list.")
            else:
                logger.debug(" "*(indent+2) + "SPHN Contrast Agent Administration Event object is already in the list.")

    # 
    # 9. Check if any SPHN Contrast Agent Administration Event objects were successfully created
    #

    return sphn_contrast_agent_administration_event_list if len(sphn_contrast_agent_administration_event_list) > 0 else None




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
        data_store.add_known_contrast_bolus_agent_sequence_code_to_dict(coding_scheme_designator, code_value, code_meaning)

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
                if sphn_contrast_agent_active_ingredient not in sphn_contrast_agent_active_ingredient_list:
                    sphn_contrast_agent_active_ingredient_list.append(sphn_contrast_agent_active_ingredient)
                else:
                    logger.debug(" "*(indent+4) + "SPHN Contrast Agent Active Ingredient is already in the list")

            else:
                logger.debug(" "*(indent+4) + f"DICOM ContrastBolusAgentSequence item {index} could not be converted to a SPHN Contrast Agent Active Ingredient object")
        else:
            logger.debug(" "*(indent+4) + f"DICOM ContrastBolusAgentSequence item {index} has no coding scheme designator or code value")
            data_store.add_unknown_contrast_bolus_agent_sequence_code_to_dict(coding_scheme_designator, code_value, code_meaning)

    if len(sphn_contrast_agent_active_ingredient_list) == 0:
        logger.debug(" "*(indent+4) + "No valid SPHN Contrast Agent Active Ingredients could be created from the DICOM ContrastBolusAgentSequence")
        return None

    # Create the SPHN Contrast Agent object
    sphn_contrast_agent = create_sphn_contrast_agent(
        active_ingredient_list=sphn_contrast_agent_active_ingredient_list,
        article=None,
        context=context,
        indent=indent+2
    )

    return sphn_contrast_agent




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
        if sphn_contrast_agent_active_ingredient not in sphn_contrast_agent_active_ingredient_list:
            sphn_contrast_agent_active_ingredient_list.append(sphn_contrast_agent_active_ingredient)
        else:
            logger.debug(" "*(indent+4) + "SPHN Contrast Agent Active Ingredient is already in the list")

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
    sphn_contrast_agent = create_sphn_contrast_agent(
        active_ingredient_list=sphn_contrast_agent_active_ingredient_list,
        article=sphn_drug_article,
        context=context,
        indent=indent+2
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
    
    logger.debug(" "*(indent+0) + "DICOM contrast agent code found.")

    coding_scheme_designator = result[0]
    code_value = result[1]
    code_descr = generic_name

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

    # Add to the list (There should only be one active ingredient)
    sphn_contrast_agent_active_ingredient_list = [sphn_contrast_agent_active_ingredient]

    # Create the SPHN Contrast Agent object
    sphn_contrast_agent = create_sphn_contrast_agent(
        active_ingredient_list=sphn_contrast_agent_active_ingredient_list,
        article=None,
        context=context,
        indent=indent+2
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

    logger.debug(" "*(indent+0) + "DICOM contrast agent ingredient code found.")

    coding_scheme_designator = result[0]
    code_value = result[1]
    code_descr = ingredient_name

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

    # Add to the list (There should only be one active ingredient)
    sphn_contrast_agent_active_ingredient_list = [sphn_contrast_agent_active_ingredient]

    # Create the SPHN Contrast Agent object
    sphn_contrast_agent = create_sphn_contrast_agent(
        active_ingredient_list=sphn_contrast_agent_active_ingredient_list,
        article=None,
        context=context,
        indent=indent+2
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
        logger.debug(" "*(indent+0) + f"DICOM contrast ingredient term '{ingredient_term}' is not in the list of known DICOM contrast ingredient terms")
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
        indent=indent+2
    )

    # The creation of the SPHN Contrast Agent Active Ingredient object should not have failed
    # as the DICOM code should always be mappable to a valid SPHN SNOMED-CT code
    assert sphn_contrast_agent_active_ingredient is not None 

    # Add to the list (There should only be one active ingredient)
    sphn_contrast_agent_active_ingredient_list = [sphn_contrast_agent_active_ingredient]

    # Create the SPHN Contrast Agent object
    sphn_contrast_agent = create_sphn_contrast_agent(
        active_ingredient_list=sphn_contrast_agent_active_ingredient_list,
        article=None,
        context=context,
        indent=indent+2
    )

    return sphn_contrast_agent



# ---------------------------------------------------------------------------------------------------------------------
# Functions for reading the "Enhanced Contrast/Bolus" module 
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-10-12
# New
def process_enhanced_contrast_bolus_module_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> None:
    """
    Processes the DICOM Enhanced Contrast/Bolus Module information and stores contrast agent administration events in the data_store.
    Parameters:
        - dataset: The DICOM Dataset containing the Enhanced Contrast/Bolus Module
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
    # 1. Check if there is coded information in the ContrastBolusAgentSequence
    #

    contrast_bolus_agent_sequence = get_contrast_bolus_agent_sequence_from_dicom(dataset, context, indent=indent+2)

    if contrast_bolus_agent_sequence is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAgentSequence not found in the dataset")
        return

    assert isinstance(contrast_bolus_agent_sequence, Sequence)

    logger.debug(" "*(indent+0) + f"DICOM ContrastBolusAgentSequence (coded info) found with {len(contrast_bolus_agent_sequence)} item(s)")

    #
    # 2. Process each item in the sequence
    #

    # Process each item in the ContrastBolusAgentSequence
    for i, item in enumerate(contrast_bolus_agent_sequence):
        
        assert isinstance(item, Dataset)

        logger.debug(" "*(indent+2) + f"Processing item {i+1} of {len(contrast_bolus_agent_sequence)} in ContrastBolusAgentSequence")
        
        sphn_contrast_agent_administration_event = process_contrast_bolus_agent_sequence_item(item, context, indent+4)

        # Store the collected SPHN contrast agent administration event in the data store
        if sphn_contrast_agent_administration_event is not None:
            if data_store.sphn_contrast_agent_administration_event_list is None:
                data_store.sphn_contrast_agent_administration_event_list = [sphn_contrast_agent_administration_event]
            else:
                if sphn_contrast_agent_administration_event not in data_store.sphn_contrast_agent_administration_event_list:
                    data_store.sphn_contrast_agent_administration_event_list.append(sphn_contrast_agent_administration_event)
                else:
                    logger.debug(" "*(indent+4) + "SPHN Contrast Agent Administration Event object already in the list")
        else:
            logger.debug(" "*(indent+4) + "No SPHN Contrast Agent Administration Event object to store in the data store")


#
# Edwin 2026-10-12
# New
def process_contrast_bolus_agent_sequence_item(dataset:Dataset, context: Context, indent:int=0) -> SPHNContrastAgentAdministrationEvent|None:
    """
    Process the DICOM ContrastBolusAgentSequence item (Dataset) and return an SPHNContrastAgentAdministrationEvent object, if any.
    Parameters:
        - dataset: The DICOM ContrastBolusAgentSequence item (Dataset).
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int)

    logger = context.logger
    data_store = context.data_store
    sphn_schema = context.sphn_schema

    sphn_contrast_agent_active_ingredient: SPHNContrastAgentActiveIngredient|None = None
    ingredient_list: list[SPHNContrastAgentActiveIngredient] = []
    sphn_contrast_agent: SPHNContrastAgent|None = None
    sphn_administration_route_code: SPHNCode|None = None
    flow_profile_list: list[SPHNFlowProfileInterval] = []

    #
    # 1. Extract the coding scheme designator, code value, and code meaning from the DICOM sequence item (dataset)
    #    and create the SPHN Contrast Agent Active Ingredient object if possible
    #

    coding_scheme_designator = get_coding_scheme_designator_from_dicom(dataset, context, indent=indent+2)
    code_value = get_code_value_from_dicom(dataset, context, indent=indent+2)
    code_descr = get_code_meaning_from_dicom(dataset, context, indent=indent+2)

    if code_value is not None and coding_scheme_designator is not None:

        logger.debug(" "*(indent+0) + f"DICOM ContrastBolusAgentSequence item has coding scheme designator '{coding_scheme_designator}' and code value '{code_value}' with description '{code_descr}'")

        # Create the SPHN Contrast Agent Active Ingredient object
        sphn_contrast_agent_active_ingredient = create_sphn_contrast_agent_active_ingredient(
            coding_scheme_designator=coding_scheme_designator,
            code_value=code_value,
            code_meaning=code_descr,
            context=context,
            indent=indent+2
        )

        # Check if the SPHN Contrast Agent Active Ingredient object was successfully created
        if sphn_contrast_agent_active_ingredient is not None:
            # Add the contrast bolus agent code to the data store dictionary for statistical purposes
            data_store.add_known_contrast_bolus_agent_sequence_code_to_dict(coding_scheme_designator, code_value, code_descr)
        else:
            logger.debug(" "*(indent+2) + "DICOM ContrastBolusAgentSequence item could not be converted to a SPHN Contrast Agent Active Ingredient object")
            data_store.add_unknown_contrast_bolus_agent_sequence_code_to_dict(coding_scheme_designator, code_value, code_descr)
    else:
        logger.debug(" "*(indent+2) + "DICOM ContrastBolusAgentSequence item has no coding scheme designator or code value")
        data_store.add_unknown_contrast_bolus_agent_sequence_code_to_dict(coding_scheme_designator, code_value, code_descr)


    #
    # 2. Extract the Contrast/Bolus Ingredient Code Sequence from the DICOM sequence item (dataset)
    #    and create a list of SPHN Contrast Agent Active Ingredient objects if possible
    #

    contrast_bolus_ingredient_code_sequence = get_contrast_bolus_ingredient_code_sequence_from_dicom(dataset, context, indent=indent+2)

    if contrast_bolus_ingredient_code_sequence is not None:

        assert isinstance(contrast_bolus_ingredient_code_sequence, Sequence)

        logger.debug(" "*(indent+0) + f"DICOM ContrastBolusIngredientCodeSequence (coded info) found with {len(contrast_bolus_ingredient_code_sequence)} item(s)")

        #
        # 2.1. Process each item in the sequence
        #

        # Process each item in the ContrastBolusIngredientCodeSequence
        for i, item in enumerate(contrast_bolus_ingredient_code_sequence):
            
            assert isinstance(item, Dataset)

            logger.debug(" "*(indent+2) + f"Processing item {i+1} of {len(contrast_bolus_ingredient_code_sequence)} in ContrastBolusIngredientCodeSequence")
            
            ingredient = process_contrast_bolus_ingredient_code_sequence_item(item, context, indent+4)

            if ingredient:
                if ingredient not in ingredient_list:
                    ingredient_list.append(ingredient)
                else:
                    logger.debug(" "*(indent+4) + "Ingredient is already in the list")
            else:
                logger.debug(" "*(indent+4) + "Failed to process Ingredient from item")

    else:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusIngredientCodeSequence not found in the dataset")

    #
    # 2.2. Process the ingredient concentration
    # 

    contrast_bolus_ingredient_concentration = get_contrast_bolus_ingredient_concentration_from_dicom(dataset, context, indent=indent+2)

    if contrast_bolus_ingredient_concentration is not None:
        logger.debug(" "*(indent+2) + f"ContrastBolusIngredientConcentration found: {contrast_bolus_ingredient_concentration} mg/ml")

        # Convert the concentration to a SPHNQuantity object
        sphn_code_mg_per_ml = SPHNCode( 
            sphn_schema = sphn_schema,
            has_identifier = "mgpermL",  # Label:"mg/ml", the UCUM unit code for milligrams per milliliter
            has_coding_system_and_version = "UCUM"
        )
        sphn_unit_mg_per_ml = SPHNUnit(
            sphn_schema = sphn_schema,
            has_code = sphn_code_mg_per_ml
        )
        sphn_quantity_concentration = SPHNQuantity(
            sphn_schema = sphn_schema,
            has_value = float(contrast_bolus_ingredient_concentration),
            has_unit = sphn_unit_mg_per_ml
        )

        #
        # 2.2.1. Add the concentration to the ingredient if available
        #
        if len(ingredient_list) == 1:
            ingredient_list[-1].has_concentration = sphn_quantity_concentration
            logger.debug(" "*(indent+4) + "Added concentration to ingredient")
        else:
            logger.debug(" "*(indent+4) + "Could not add concentration to ingredient, either no ingredient or multiple ingredients present")

    else:
        logger.debug(" "*(indent+2) + "ContrastBolusIngredientConcentration not found")


    #
    # 2.3. Process the ingredient percent by volume
    # 

    contrast_bolus_ingredient_percent_by_volume = get_contrast_bolus_ingredient_percent_by_volume_from_dicom(dataset, context, indent=indent+2)

    if contrast_bolus_ingredient_percent_by_volume is not None:
        logger.debug(" "*(indent+2) + f"ContrastBolusIngredientPercentByVolume found: {contrast_bolus_ingredient_percent_by_volume} %")

        assert isinstance(contrast_bolus_ingredient_percent_by_volume, float)

        # Convert the percent by volume to a SPHNQuantity object
        sphn_code_percent = SPHNCode( 
            sphn_schema = sphn_schema,
            has_identifier = "percent",  # Label:"%", the UCUM unit code for percent
            has_coding_system_and_version = "UCUM"
        )
        sphn_unit_percent = SPHNUnit(
            sphn_schema = sphn_schema,
            has_code = sphn_code_percent
        )
        sphn_quantity_volume_percentage = SPHNQuantity(
            sphn_schema = sphn_schema,
            has_value = contrast_bolus_ingredient_percent_by_volume,
            has_unit = sphn_unit_percent
        )

        #
        # 2.3.1. Add the volume percentage to the ingredient if available
        #
        if len(ingredient_list) == 1:
            ingredient_list[-1].has_volume_percentage = sphn_quantity_volume_percentage
            logger.debug(" "*(indent+4) + "Added volume percentage to ingredient")
        else:
            logger.debug(" "*(indent+4) + "Could not add volume percentage to ingredient, either no ingredient or multiple ingredients present")

    else:
        logger.debug(" "*(indent+2) + "ContrastBolusIngredientPercentByVolume not found")

    #
    # 2.4. Process the ingredient Opaque
    # 
    # Opaque is not a propery of SPHN Contrast Agent Active Ingredient. Skipping...

    #
    # 3. Create the SPHN Contrast Agent object
    #

    # Add the sphn_contrast_agent_active_ingredient in front of the list and avoid duplicates
    if sphn_contrast_agent_active_ingredient is not None:
        new_ingredient_list = [sphn_contrast_agent_active_ingredient]
        for ingredient in ingredient_list:  
            if ingredient not in new_ingredient_list:
                new_ingredient_list.append(ingredient)
            else:
                logger.debug(" "*(indent+4) + "Ingredient is already in the list")
    else:
        new_ingredient_list = ingredient_list

    sphn_contrast_agent = create_sphn_contrast_agent(
        active_ingredient_list=new_ingredient_list if new_ingredient_list else None,
        article=None,
        context=context,
        indent=indent+2
    )

    logger.debug(" "*(indent+2) + "Created an SPHN Contrast Agent object")

    #
    # 4. Extract the Contrast/Bolus Administration Route Sequence from the DICOM sequence item (dataset)
    #    and create a SPHN Contrast Agent Administration Route Code object if possible
    # 
    
    contrast_bolus_administration_route_sequence = get_contrast_bolus_administration_route_sequence_from_dicom(dataset, context, indent=indent+2)

    if contrast_bolus_administration_route_sequence is not None:
        
        assert isinstance(contrast_bolus_administration_route_sequence, Sequence)

        logger.debug(" "*(indent+2) + f"DICOM ContrastBolusAdministrationRouteSequence (coded info) found with {len(contrast_bolus_administration_route_sequence)} item(s)")

        #
        # 4.1. Process each item in the sequence
        #

        # There should be exactly zero or one item(s) in the Contrast/Bolus Administration Route Sequence
        if len(contrast_bolus_administration_route_sequence) == 1:
            
            sphn_administration_route_code = process_contrast_bolus_administration_route_sequence_item(contrast_bolus_administration_route_sequence[0], context, indent+4)
            
            if sphn_administration_route_code is None:
                logger.debug(" "*(indent+2) + "Failed to create an SPHN Administration Route Code object from DICOM ContrastBolusAdministrationRouteSequence (coded info).")

        elif len(contrast_bolus_administration_route_sequence) == 0:
            logger.debug(" "*(indent+2) + "No items found in ContrastBolusAdministrationRouteSequence")

        else:
            raise ValueError("Unexpected number of items in ContrastBolusAdministrationRouteSequence")

    else:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAdministrationRouteSequence (coded info) is missing or empty.")

    #
    # 5. Process the Contrast/Bolus T1 Relaxivity
    #

    # T1 Relaxivity is not a propery of SPHN Contrast Agent. Skipping...

    #
    # 6. Process the Contrast/Bolus Volume (Total volume administered in milliliters of diluted contrast agent)
    # 

    sphn_quantity_volume = None

    volume = get_contrast_bolus_volume_from_dicom(dataset, context, indent=indent+2)

    if volume is not None:
        # Process the volume information here
        sphn_quantity_volume = create_sphn_quantity_for_volume(volume, logger, indent=indent+2)

    if sphn_quantity_volume is not None:
        # Assign the volume to the SPHN contrast agent object
        sphn_contrast_agent.has_quantity = sphn_quantity_volume
        logger.debug(" "*(indent+0) +f"Added contrast/bolus total administered (diluted) volume: '{volume} ml' to SPHN contrast agent object.")
    else:
        logger.debug(" "*(indent+0) +"Failed to determine contrast/bolus total administered (diluted) volume.")

    #
    # 7. Extract the Contrast Administration Profile Sequence from the DICOM sequence item (dataset)
    #

    # Also record the earliest start and latest end times
    contrast_bolus_start_datetime = None
    contrast_bolus_end_datetime = None

    contrast_administration_profile_sequence = get_contrast_administration_profile_sequence_from_dicom(dataset, context, indent=indent+2)

    if contrast_administration_profile_sequence is not None:
        
        assert isinstance(contrast_administration_profile_sequence, Sequence)

        logger.debug(" "*(indent+2) + f"DICOM ContrastAdministrationProfileSequence (coded info) found with {len(contrast_administration_profile_sequence)} item(s)")

        #
        # 7.1. Process each item in the sequence
        #

        # Process each item in the ContrastAdministrationProfileSequence
        for i, item in enumerate(contrast_administration_profile_sequence):
            
            assert isinstance(item, Dataset)

            logger.debug(" "*(indent+2) + f"Processing item {i+1} of {len(contrast_administration_profile_sequence)} in ContrastAdministrationProfileSequence")
            
            sphn_flow_profile_interval = process_contrast_administration_profile_sequence_item(item, context, indent+4)

            if sphn_flow_profile_interval:
                if sphn_flow_profile_interval not in flow_profile_list:
                    flow_profile_list.append(sphn_flow_profile_interval)

                    # Update the earliest start and latest end times
                    if sphn_flow_profile_interval.has_start_datetime and (contrast_bolus_start_datetime is None or sphn_flow_profile_interval.has_start_datetime < contrast_bolus_start_datetime):
                        contrast_bolus_start_datetime = sphn_flow_profile_interval.has_start_datetime
                    if sphn_flow_profile_interval.has_end_datetime and (contrast_bolus_end_datetime is None or sphn_flow_profile_interval.has_end_datetime > contrast_bolus_end_datetime):
                        contrast_bolus_end_datetime = sphn_flow_profile_interval.has_end_datetime

                else:
                    logger.debug(" "*(indent+4) + "SPHN Flow Profile Intervalis is already in the list")
            else:
                logger.debug(" "*(indent+4) + "Failed to process Profile from item")

    else:
        logger.debug(" "*(indent+0) + "DICOM ContrastAdministrationProfileSequence not found in the dataset")


    # 
    # 8. Determine the SPHNContrastAdministrationEvent start datetime
    #

    # If the contrast bolus start time is unknown, use the fallback studydate
    if contrast_bolus_start_datetime is None:

        assert data_store.fallback_study_datetime is not None and isinstance(data_store.fallback_study_datetime, datetime)

        # Create a fallback contrast bolus start time using the DICOM time completion function
        contrast_bolus_start_time = complete_dicom_time(
            str(data_store.fallback_study_datetime.time()), 
            logger, 
            indent=indent+2)

        # Get the complete contrast/bolus start datetime by combining the start time with the fallback date.
        contrast_bolus_start_datetime = get_contrast_bolus_datetime(
            contrast_bolus_time=contrast_bolus_start_time, 
            acquisition_datetime=None, 
            series_datetime=None,
            study_datetime=data_store.fallback_study_datetime,
            context=context, 
            indent=indent+2
        )
        logger.debug(" "*(indent+2) + f"Created a fallback contrast bolus start datetime: {contrast_bolus_start_datetime!s}")
    else:
        logger.debug(" "*(indent+2) + f"Using contrast bolus start datetime: {contrast_bolus_start_datetime!s}")

    if contrast_bolus_end_datetime is None:
        logger.debug(" "*(indent+2) + "Contrast bolus end datetime is not defined")
    else:
        logger.debug(" "*(indent+2) + f"Using contrast bolus end datetime: {contrast_bolus_end_datetime!s}")

    if contrast_bolus_start_datetime > contrast_bolus_end_datetime:
        logger.debug(" "*(indent+2) + "Warning: Contrast bolus start datetime is after the end datetime")

    #
    # 9. Create the SPHN Contrast Agent Administration Event
    #

    sphn_contrast_agent_administration_event = create_sphn_contrast_agent_administration_event(
        sphn_contrast_agent=sphn_contrast_agent,
        sphn_administration_route_code=sphn_administration_route_code,
        start_datetime=contrast_bolus_start_datetime,
        context=context,
        indent=indent+2
    )

    if sphn_contrast_agent_administration_event is None:
        logger.debug(" "*(indent+2) + "Failed to create SPHN Contrast Agent Administration Event")
        return None
    else:
        logger.debug(" "*(indent+2) + "Successfully created SPHN Contrast Agent Administration Event")
    
    return sphn_contrast_agent_administration_event

# ---------------------------------------------------------------------------------------------------------------------
# Functions for Processing
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-10-12
# New
def process_contrast_bolus_ingredient_code_sequence_item(dataset:Dataset, context: Context, indent:int=0) -> SPHNContrastAgentActiveIngredient|None:
    """
    Process the DICOM ContrastBolusIngredientCodeSequence item (Dataset) and return an SPHNContrastAgentActiveIngredient object, if any.
    Parameters:
        - dataset: The DICOM ContrastBolusIngredientCodeSequence item (Dataset).
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int)

    logger = context.logger
    data_store = context.data_store

    sphn_contrast_agent_active_ingredient: SPHNContrastAgentActiveIngredient|None = None

    #
    # 1. Extract the coding scheme designator, code value, and code meaning from the DICOM sequence item (dataset)
    #    and create the SPHN Contrast Agent Active Ingredient object if possible
    #

    coding_scheme_designator = get_coding_scheme_designator_from_dicom(dataset, context, indent=indent+2)
    code_value = get_code_value_from_dicom(dataset, context, indent=indent+2)
    code_descr = get_code_meaning_from_dicom(dataset, context, indent=indent+2)

    if code_value is None or coding_scheme_designator is None:
        logger.debug(" "*(indent+2) + "DICOM ContrastBolusIngredientCodeSequence item has no coding scheme designator or code value")
        data_store.add_unknown_contrast_bolus_agent_sequence_code_to_dict(coding_scheme_designator, code_value, code_descr)
        return None

    logger.debug(" "*(indent+0) + f"DICOM ContrastBolusIngredientCodeSequence item has coding scheme designator '{coding_scheme_designator}' and code value '{code_value}' with description '{code_descr}'")

    # Create the SPHN Contrast Agent Active Ingredient object
    sphn_contrast_agent_active_ingredient = create_sphn_contrast_agent_active_ingredient(
        coding_scheme_designator=coding_scheme_designator,
        code_value=code_value,
        code_meaning=code_descr,
        context=context,
        indent=indent+2
    )

    # Check if the SPHN Contrast Agent Active Ingredient object was successfully created
    if sphn_contrast_agent_active_ingredient is None:
        logger.debug(" "*(indent+2) + "DICOM ContrastBolusIngredientCodeSequence item could not be converted to a SPHN Contrast Agent Active Ingredient object")
        data_store.add_unknown_contrast_bolus_agent_sequence_code_to_dict(coding_scheme_designator, code_value, code_descr)
        return None

    # Add the contrast bolus ingredient code to the data store dictionary for statistical purposes
    data_store.add_known_contrast_bolus_agent_sequence_code_to_dict(coding_scheme_designator, code_value, code_descr)

    return sphn_contrast_agent_active_ingredient


#
# Edwin 2026-10-12
# New
def process_contrast_bolus_administration_route_sequence_item(dataset:Dataset, context: Context, indent:int=0) -> SPHNCode|None:
    """
    Process the DICOM ContrastBolusAdministrationRouteSequence item and return an SPHN Code object for the SPHN hasAdministrationRouteCode, if any.
    Parameters:
        - dataset: The DICOM dataset containing the ContrastBolusAdministrationRouteSequence item (Dataset)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int)

    logger = context.logger
    data_store = context.data_store
    sphn_schema = context.sphn_schema
    
    # Get the coded info from DICOM
    coding_scheme_designator = get_coding_scheme_designator_from_dicom(dataset, context, indent=indent+2)
    code_value = get_code_value_from_dicom(dataset, context, indent=indent+2)
    code_descr = get_code_meaning_from_dicom(dataset, context, indent=indent+2)

    if coding_scheme_designator is None or code_value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAdministrationRouteSequence item has no coding scheme designator or code value")
        data_store.add_unknown_contrast_bolus_administration_route_sequence_code_to_dict(context, coding_scheme_designator, code_value, code_descr, indent=indent)
        return None

    logger.debug(" "*(indent+4) + f"DICOM ContrastBolusAdministrationRouteSequence item has coding scheme designator '{coding_scheme_designator}' and code value '{code_value}' with description '{code_descr}'")

    # Try to convert the DICOM coding scheme designator and code value to a SPHN administration route SNOMED-CT code
    result = DataConverter.administration_routes_list.get((coding_scheme_designator, code_value), None)

    # Check if the route is known
    if result is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAdministrationRouteSequence item could not be mapped to a known SPHN Administrative Route code")
        data_store.add_unknown_contrast_bolus_administration_route_sequence_code_to_dict(context, coding_scheme_designator, code_value, code_descr, indent=indent)
        return None
    
    # Add the administration route to the data store dictionary for statistical purposes
    data_store.add_known_contrast_bolus_administration_route_sequence_code_to_dict(coding_scheme_designator, code_value, code_descr)

    assert isinstance(result, tuple) and len(result) == 3
    assert all(is_valid_string(item) for item in result)

    route_coding_scheme_designator = result[0]
    route_code_value = result[1]
    route_code_descr = result[2]

    sphn_code_route = SPHNCode( 
        sphn_schema = sphn_schema,
        has_coding_system_and_version = route_coding_scheme_designator,
        has_identifier = route_code_value,
        has_name = route_code_descr
        )

    logger.debug(" "*(indent+0) + f"The DICOM coding scheme designator: '{coding_scheme_designator}' and code value: '{code_value}'" + 
                f" with description '{code_descr}' was successfully converted to an SPHN Contrast Bolus Administration Route" +
                f" with coding scheme designator '{route_coding_scheme_designator}' and code value '{route_code_value}'" +
                f" and code description '{route_code_descr}'")

    return sphn_code_route

#
# Edwin 2026-10-16
# New
def process_contrast_administration_profile_sequence_item(dataset:Dataset, context: Context, indent:int=0) -> SPHNFlowProfileInterval|None:
    """
    Process the DICOM ContrastAdministrationProfileSequence item and return an SPHN Flow Profile Interval object, if any.
    Parameters:
        - dataset: The DICOM dataset containing the ContrastAdministrationProfileSequence item (Dataset)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int)

    logger = context.logger
    data_store = context.data_store
    sphn_schema = context.sphn_schema

    #
    # 1. Process the start time and combine it with a relevant date to get the complete start datetime.
    #

    contrast_bolus_start_datetime = None

    start_time = get_contrast_bolus_start_time_from_dicom(dataset, context, indent=indent+2)

    if start_time is not None:

        # Complete the DICOM contrast/bolus start time to ensure it has all necessary components (hours, minutes, seconds) 
        # and return it as a TM object (or type datetime.time).
        contrast_bolus_start_time = complete_dicom_time(start_time, logger, indent=indent+2)

        if contrast_bolus_start_time is not None:
            # Get the complete contrast/bolus start datetime by combining the start time with the relevant acquisition/series/study date.
            contrast_bolus_start_datetime = get_contrast_bolus_datetime(
                contrast_bolus_time=contrast_bolus_start_time, 
                acquisition_datetime=data_store.acquisition_datetime, 
                series_datetime=data_store.series_datetime,
                study_datetime=data_store.study_datetime,
                context=context, 
                indent=indent+2
            )

    if contrast_bolus_start_datetime is not None:
        logger.debug(" "*(indent+0) +f"Determined contrast/bolus start datetime: {contrast_bolus_start_datetime!s}")
    else:
        logger.debug(" "*(indent+0) +"Failed to determine contrast/bolus start datetime.")


    #
    # 2. Process the end time and combine it with a relevant date to get the complete end datetime.
    #

    contrast_bolus_end_datetime = None

    end_time = get_contrast_bolus_stop_time_from_dicom(dataset, context, indent=indent+2)

    if end_time is not None:

        # Complete the DICOM contrast/bolus stop time to ensure it has all necessary components (hours, minutes, seconds) 
        # and return it as a TM object (or type datetime.time).
        contrast_bolus_end_time = complete_dicom_time(end_time, logger, indent=indent+2)

        if contrast_bolus_end_time is not None:
            # Get the complete contrast/bolus end datetime by combining the end time with the relevant acquisition/series/study date.
            contrast_bolus_end_datetime = get_contrast_bolus_datetime(
                contrast_bolus_time=contrast_bolus_end_time, 
                acquisition_datetime=data_store.acquisition_datetime, 
                series_datetime=data_store.series_datetime,
                study_datetime=data_store.study_datetime,
                context=context, 
                indent=indent+2
            )

    if contrast_bolus_end_datetime is not None:
        logger.debug(" "*(indent+0) +f"Determined contrast/bolus end datetime: {contrast_bolus_end_datetime!s}")
    else:
        logger.debug(" "*(indent+0) +"Failed to determine contrast/bolus end datetime.")

    #
    #  3. Process the volume, if available.
    #

    sphn_quantity_volume = None

    volume = get_contrast_bolus_volume_from_dicom(dataset, context, indent=indent+2)

    if volume is not None:
        # Process the volume information here
        sphn_quantity_volume = create_sphn_quantity_for_volume(volume, logger, indent=indent+2)

    if sphn_quantity_volume is not None:
        logger.debug(" "*(indent+0) +f"Determined contrast/bolus volume: {volume} ml")
    else:
        logger.debug(" "*(indent+0) +"Failed to determine contrast/bolus volume.")

    #
    #  4. Process the flow rate, if available.
    #

    sphn_quantity_flow_rate = None

    flow_rate = get_contrast_flow_rate_from_dicom(dataset, context, indent=indent+2)

    if flow_rate is not None:
        # Process the flow rate information here
        sphn_quantity_flow_rate = create_sphn_quantity_for_flow_rate(flow_rate, logger, indent=indent+2)

    if sphn_quantity_flow_rate is not None:
        logger.debug(" "*(indent+0) +f"Determined contrast/bolus flow rate: {flow_rate} ml/s")
    else:
        logger.debug(" "*(indent+0) +"Failed to determine contrast/bolus flow rate.")

    #
    #  5. Process the flow duration, if available.
    #

    sphn_quantity_flow_duration = None

    flow_duration = get_contrast_flow_duration_from_dicom(dataset, context, indent=indent+2)

    if flow_duration is not None:
        # Process the flow duration information here
        sphn_quantity_flow_duration = create_sphn_quantity_for_flow_duration(flow_duration, logger, indent=indent+2)

    if sphn_quantity_flow_duration is not None:
        logger.debug(" "*(indent+0) +f"Determined contrast/bolus flow duration: {flow_duration} s")
    else:
        logger.debug(" "*(indent+0) +"Failed to determine contrast/bolus flow duration.")

    #
    #  6. Create the SPHNFlowProfileInterval object with the processed information.
    #

    sphn_flow_profile_interval = None

    #  Check if any of the processed information is available before creating the SPHNFlowProfileInterval object.
    if contrast_bolus_start_datetime is not None \
        or contrast_bolus_end_datetime is not None \
        or sphn_quantity_volume is not None \
        or sphn_quantity_flow_rate is not None \
        or sphn_quantity_flow_duration is not None:

        sphn_flow_profile_interval = SPHNFlowProfileInterval(
            sphn_schema = sphn_schema,
            has_start_datetime = contrast_bolus_start_datetime,
            has_end_datetime = contrast_bolus_end_datetime,
            has_volume = sphn_quantity_volume,
            has_volumetric_flow_rate = sphn_quantity_flow_rate,
            has_duration = sphn_quantity_flow_duration
            )

    if sphn_flow_profile_interval is not None:
        logger.debug(" "*(indent+0) +"Successfully created SPHNFlowProfileInterval object.")
    else:
        logger.debug(" "*(indent+0) +"Failed to create SPHNFlowProfileInterval object.")

    return sphn_flow_profile_interval


# ---------------------------------------------------------------------------------------------------------------------
# Functions for Creating
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-10-12
# New
def create_sphn_contrast_agent_active_ingredient(
        coding_scheme_designator: str, 
        code_value: str, 
        code_meaning: str|None, 
        context: Context, 
        indent: int=0
    ) -> SPHNContrastAgentActiveIngredient|None:
    """
    Creates a SPHN Contrast Agent Active Ingredient object. The given DICOM coding scheme designator and code value 
    are converted to the corresponding SPHN SNOMED-CT code if available.
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

    # If the result is None, try again using the SPHN SNOMED-CT codes

    # Check again
    if result is None:
        logger.debug(" "*(indent+0) + f"The DICOM coding scheme designator: '{coding_scheme_designator}' and code value: '{code_value}' has no corresponding SPHN SNOMED-CT code in the DataConverter")
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
# Edwin 2026-10-12
# New
def create_sphn_contrast_agent(
        active_ingredient_list:list[SPHNContrastAgentActiveIngredient]|None,
        article: SPHNDrugArticle,
        context: Context,
        indent:int=0
    ) -> SPHNContrastAgent:
    """
    Creates an SPHN Contrast Agent object with the provided information.
    Parameters:
        - active_ingredient_list: A list of SPHN Contrast Agent Active Ingredient objects.
        - article: The SPHN Drug Article object associated with the contrast agent.
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    assert active_ingredient_list is None or (isinstance(active_ingredient_list, list) and all(isinstance(i, SPHNContrastAgentActiveIngredient) for i in active_ingredient_list))
    assert isinstance(article, SPHNDrugArticle)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger
    data_store = context.data_store
    sphn_schema = context.sphn_schema

    logger.debug(" "*(indent+0) + "Start creating an SPHN Contrast Agent object...")

    # ToDo Edwin Note: Multiple active ingredients can not be included yet, update this once the SPHN schema supports it

    sphn_contrast_agent = SPHNContrastAgent(
        sphn_schema = sphn_schema,
        has_active_ingredient=None if active_ingredient_list is None or len(active_ingredient_list) == 0 else active_ingredient_list[0],  # Currently only supports a single active ingredient
        has_source_system_list=[data_store.sphn_source_system]
    )

    logger.debug(" "*(indent+0) + "Done  creating SPHN Contrast Agent object.")

    return sphn_contrast_agent


#
# Edwin 2026-10-12
# New
def create_sphn_contrast_agent_administration_event(
        sphn_contrast_agent:SPHNContrastAgent,
        sphn_administration_route_code:SPHNCode|None,
        start_datetime:datetime,
        context: Context,
        indent:int=0
    ) -> SPHNContrastAgentAdministrationEvent:
    """
    Creates an SPHN Contrast Agent Administration Event object with the provided information.
    Parameters:
        - sphn_contrast_agent: SPHN Contrast Agent object.
        - sphn_administration_route_code: The SPHN administration route code.
        - start_datetime: The start date and time of the administration event.
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
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
        has_start_datetime=start_datetime,
        has_drug=sphn_contrast_agent,
        has_administration_route_code=sphn_administration_route_code,
        has_subject_pseudo_identifier = data_store.sphn_subject_pseudo_identifier,
        has_source_system_list = [data_store.sphn_source_system]
    )

    logger.debug(" "*(indent+0) + "Done  creating SPHN Contrast Agent Administration Event object.")

    return sphn_contrast_agent_administration_event


#
# Edwin 2026-10-16
# New 
def create_sphn_quantity_for_volume(volume: float, context: Context, indent:int=0) -> SPHNQuantity|None:
    """
    Creates the SPHN Quantity object for the contrast/bolus volume and returns it.
    Parameters:
        - volume: The contrast/bolus volume value
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """
    assert isinstance(volume, float)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    sphn_schema = context.sphn_schema   

    sphn_code_ucum = SPHNCode( 
        sphn_schema = sphn_schema,
        has_identifier = "mL",  # UCUM unit code for ml
        has_coding_system_and_version = "UCUM"
        )
    sphn_unit = SPHNUnit(
        sphn_schema = sphn_schema,
        has_code = sphn_code_ucum
        )
    sphn_quantity_volume = SPHNQuantity(
        sphn_schema = sphn_schema,
        has_value = volume,
        has_unit = sphn_unit
        )

    return sphn_quantity_volume


#
# Edwin 2026-10-16
# New 
def create_sphn_quantity_for_flow_rate(flow_rate: float, context: Context, indent:int=0) -> SPHNQuantity|None:
    """
    Creates the SPHN Quantity object for the contrast/bolus flow rate and returns it.
    Parameters:
        - flow_rate: The contrast/bolus flow rate value
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """
    assert isinstance(flow_rate, float)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    sphn_schema = context.sphn_schema   

    sphn_code_ucum = SPHNCode( 
        sphn_schema = sphn_schema,
        has_identifier = "mL/s",  # UCUM unit code for ml per second
        has_coding_system_and_version = "UCUM"
        )
    sphn_unit = SPHNUnit(
        sphn_schema = sphn_schema,
        has_code = sphn_code_ucum
        )
    sphn_quantity_flow_rate = SPHNQuantity(
        sphn_schema = sphn_schema,
        has_value = flow_rate,
        has_unit = sphn_unit
        )

    return sphn_quantity_flow_rate


#
# Edwin 2026-10-16
# New
def create_sphn_quantity_for_flow_duration(flow_duration: float, context: Context, indent:int=0) -> SPHNQuantity|None:
    """
    Creates the SPHN Quantity object for the contrast/bolus flow duration and returns it.
    Parameters:
        - flow_duration: The contrast/bolus flow duration value
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """
    assert isinstance(flow_duration, float)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    sphn_schema = context.sphn_schema   

    sphn_code_ucum = SPHNCode( 
        sphn_schema = sphn_schema,
        has_identifier = "s",  # UCUM unit code for seconds
        has_coding_system_and_version = "UCUM"
        )
    sphn_unit = SPHNUnit(
        sphn_schema = sphn_schema,
        has_code = sphn_code_ucum
        )
    sphn_quantity_flow_duration = SPHNQuantity(
        sphn_schema = sphn_schema,
        has_value = flow_duration,
        has_unit = sphn_unit
        )

    return sphn_quantity_flow_duration

# ---------------------------------------------------------------------------------------------------------------------
# Functions for reading DICOM tags in the (Enhanced) Contrast/Bolus module
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-10-12
# New
def get_contrast_bolus_agent_sequence_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence (list of Datasets) in the DICOM ContrastBolusAgentSequence tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Keyword:              ContrastBolusAgentSequence
    # Tag:                  (0018,0012)
    # Value Representation: Sequence (SQ)
    # Type:	                Optional (3) / Required (1)
    # Value Multiplicity:   1

    # Note: The Type is:
    # - Optional (3) for Legacy single-frame images and 
    # - Required (1) for Enhanced multi-frame images

    # Note: The Value Multiplicity (VM) of the ContrastBolusAgentSequence is 1, meaning:
    # - The ContrastBolusAgentSequence 'block' itself can only be provided once, but
    # - may contain 0, 1, or multiple nested data blocks, each representing a coded contrast agent.

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
# Edwin 2026-10-12
# New
def get_contrast_bolus_administration_route_sequence_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence / the list of Datasets in the DICOM ContrastBolusAdministrationRouteSequence tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
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
# Edwin 2026-10-12
# New
def get_contrast_bolus_ingredient_code_sequence_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence (list of Datasets) in the DICOM ContrastBolusIngredientCodeSequence tag
    Parameters:
        - dataset: the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: the Context object that holds the data_store, logger and other relevant information
        - indent: the indentation level for logging (default is 0)
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
# Edwin 2026-10-12
# New
def get_contrast_bolus_ingredient_concentration_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> DSfloat|DSdecimal|None:
    """
    Returns the value corresponding to the value of the DICOM ContrastBolusIngredientConcentration tag
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
# Edwin 2026-10-12
# New
def get_contrast_bolus_ingredient_percent_by_volume_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the float corresponding to the value of the DICOM ContrastBolusIngredientPercentByVolume tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
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


#
# Edwin 2026-10-15
# New
def get_contrast_administration_profile_sequence_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> Sequence[Dataset]|None:
    """
    Returns the Sequence / the list of Datasets in the DICOM ContrastAdministrationProfileSequence tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
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

    # Get the value of the DICOM CContrastAdministrationProfileSequence tag
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
# Edwin 2026-10-15
# New
def get_contrast_bolus_volume_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the float corresponding to the value of the DICOM ContrastBolusVolume tag
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

    try:
        contrast_bolus_volume = float(value)
    except (TypeError, ValueError):
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusVolume tag value could not be converted to float")
        return None
    
    if contrast_bolus_volume < 0:
        logger.warning(" "*(indent+0) + f"DICOM ContrastBolusVolume: '{contrast_bolus_volume}' is probably not a valid value.")
        return None

    return contrast_bolus_volume


#
# Edwin 2026-10-15
# New
def get_contrast_flow_rate_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the float corresponding to the value of the DICOM ContrastFlowRate tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1046)
    # Type:	                Optional (3)
    # Keyword:	            ContrastFlowRate
    # Value Multiplicity	1-n
    # Value Representation:	Decimal String (DS)
    
    # Only a single value allowed for the Enhanced Contrast/Bolus Module

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM ContrastFlowRate tag
    value = dataset.get("ContrastFlowRate", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastFlowRate tag was not found")  
        return None

    try:
        contrast_flow_rate = float(value)
    except (TypeError, ValueError):
        logger.debug(" "*(indent+0) + "DICOM ContrastFlowRate tag value could not be converted to float")
        return None
    
    if contrast_flow_rate < 0:
        logger.warning(" "*(indent+0) + f"DICOM ContrastFlowRate: '{contrast_flow_rate}' is probably not a valid value.")
        return None

    return contrast_flow_rate


#
# Edwin 2026-10-15
# New
def get_contrast_flow_duration_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
    """
    Returns the float corresponding to the value of the DICOM ContrastFlowDuration tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1047)
    # Type:	                Optional (3)
    # Keyword:	            ContrastFlowDuration
    # Value Multiplicity	1-n
    # Value Representation:	Decimal String (DS)
    
    # Only a single value allowed for the Enhanced Contrast/Bolus Module

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM ContrastFlowDuration tag
    value = dataset.get("ContrastFlowDuration", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastFlowDuration tag was not found")  
        return None

    try:
        contrast_flow_duration = float(value)
    except (TypeError, ValueError):
        logger.debug(" "*(indent+0) + "DICOM ContrastFlowDuration tag value could not be converted to float")
        return None
    
    if contrast_flow_duration < 0:
        logger.warning(" "*(indent+0) + f"DICOM ContrastFlowDuration: '{contrast_flow_duration}' is probably not a valid value.")
        return None

    return contrast_flow_duration


#
# Edwin 2026-10-15
# New
def get_contrast_bolus_start_time_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM ContrastBolusStartTime tag
    Parameters:
        - dataset: The DICOM dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Tag:                  (0018,1042)
    # Type:	                Optional (3)
    # Keyword:              ContrastBolusStartTime
    # Value Multiplicity:   1
    # Value Representation: Time (TM)

    # Note:
    # The DICOM time format is specified in the DICOM standard as Time (TM) in:
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part05/sect_6.2.html

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

    # Convert a possible DICOM TM object to a string representation
    contrast_bolus_start_time = str(value)

    return contrast_bolus_start_time


#
# Edwin 2026-10-15
# New
def get_contrast_bolus_stop_time_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM ContrastBolusStopTime tag
    Parameters:
        - dataset: The DICOM dataset (DICOM header) that contains DICOM DataElements (tags)
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

    # Convert a possible DICOM TM object to a string representation
    contrast_bolus_stop_time = str(value)

    return contrast_bolus_stop_time


# ---------------------------------------------------------------------------------------------------------------------
# Not yet used functions
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-10-12
# New, Not Yet Used
def get_contrast_bolus_ingredient_opaque_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM ContrastBolusIngredientOpaque tag
    Parameters:
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

    # Remove whitespace
    contrast_bolus_ingredient_opaque = value.strip()

    if not contrast_bolus_ingredient_opaque:
        logger.warning(" "*(indent+0) + f"DICOM ContrastBolusIngredientOpaque: '{contrast_bolus_ingredient_opaque}' is not a valid value.")
        return None

    return contrast_bolus_ingredient_opaque


#
# Edwin 2026-10-12
# New, Not Yet Used
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


# ---------------------------------------------------------------------------------------------------------------------
# Older or not yet used functions
# ---------------------------------------------------------------------------------------------------------------------


#
#  Edwin 2026-10-09
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
#  Edwin 2026-10-09
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
#  Edwin 2026-10-09
#
def get_contrast_bolus_total_dose_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> DSfloat|DSdecimal|None:
    """
    Returns the float corresponding to the value of the DICOM ContrastBolusTotalDose tag
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
        logger.warning(" "*(indent+0) + f"DICOM ContrastBolusTotalDose: '{contrast_bolus_total_dose}' is probably not a valid value.")
        return None

    return contrast_bolus_total_dose


#
# Edwin 2026-10-09
#
def get_contrast_flow_rate_list_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> list[DSfloat|DSdecimal|None]|None:
    """
    Returns a list of values corresponding to the DICOM ContrastFlowRate tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
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
# Edwin 2026-10-09
#
def get_contrast_flow_duration_list_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> list[DSfloat|DSdecimal|None]|None:
    """
    Returns a list of values corresponding to the DICOM ContrastFlowDuration tag
    Parameters:
        - dataset: The DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
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
# Edwin 2026-10-09
#
def get_contrast_bolus_ingredient_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the value corresponding to the value of the DICOM ContrastBolusIngredient tag
    Parameters:
        - dataset: The DICOM dataset (DICOM header) that contains DICOM DataElements (tags)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
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
#  Edwin 2026-10-09
#
def get_contrast_bolus_agent_number_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> int|None:
    """
    Returns the value corresponding to the value of the DICOM ContrastBolusAgentNumber tag
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


# ---------------------------------------------------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------------------------------------------------


#
# Edwin 2026-10-16
# New
def get_contrast_bolus_datetime(
        contrast_bolus_time: time, 
        acquisition_datetime: datetime|None, 
        series_datetime: datetime|None,
        study_datetime: datetime|None,
        context: Context, 
        indent: int=0
    ) -> datetime:
    """
    Returns the estimated datetime of the contrast/bolus, adjusted for potential midnight boundary crossings.
    Parameters:
        contrast_bolus_time (datetime.time): The time of the contrast/bolus injection.
        acquisition_datetime (datetime|None): The datetime of the acquisition.
        series_datetime (datetime|None): The datetime of the series.
        study_datetime (datetime|None): The datetime of the study.
        context (Context): The context object containing logger and other information.
        indent (int): The indentation level for logging.
    
    Returns:
        datetime: The estimated datetime of the contrast/bolus, adjusted for potential midnight boundary crossings.

    Note: At least one of acquisition_datetime, series_datetime, or study_datetime must be provided.
    """
    assert isinstance(contrast_bolus_time, time)
    assert acquisition_datetime is None or isinstance(acquisition_datetime, datetime)
    assert series_datetime is None or isinstance(series_datetime, datetime)
    assert study_datetime is None or isinstance(study_datetime, datetime)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    # 1. Validate input parameters and ensure at least one datetime is provided
    if acquisition_datetime is None and series_datetime is None and study_datetime is None:
        raise ValueError("At least one of acquisition_datetime, series_datetime, or study_datetime must be provided.")
    
    # 2. Safely retrieve required tags with logical fallbacks
    acq_date = acquisition_datetime.strftime("%Y%m%d") if acquisition_datetime else series_datetime.strftime("%Y%m%d") if series_datetime else study_datetime.strftime("%Y%m%d")
    acq_time = acquisition_datetime.strftime("%H%M%S") if acquisition_datetime else series_datetime.strftime("%H%M%S") if series_datetime else study_datetime.strftime("%H%M%S")
    contrast_time = contrast_bolus_time.strftime("%H%M%S")
    
    if not all([acq_date, acq_time, contrast_time]):
        raise ValueError("Required date/time values are missing.")
    
    # 3. Strip fractional seconds/microseconds to ensure uniform string parsing
    acq_time_clean = acq_time.split('.')[0]
    contrast_time_clean = contrast_time.split('.')[0]
    
    # Pad strings with trailing zeros if they lack seconds (e.g., '1430' -> '143000')
    acq_time_clean = acq_time_clean.ljust(6, '0')
    contrast_time_clean = contrast_time_clean.ljust(6, '0')
   
    # 4. Generate baseline datetime objects assuming they share the same date initially
    acq_dt = datetime.strptime(f"{acq_date}{acq_time_clean}", "%Y%m%d%H%M%S")
    contrast_dt = datetime.strptime(f"{acq_date}{contrast_time_clean}", "%Y%m%d%H%M%S")

    # 5. Handle Both Midnight Scenarios (Forward and Reverse Crossings)
    time_difference = contrast_dt - acq_dt

    # Scenario A: Contrast looks like it happened 23+ hours BEFORE the scan
    # (Real world: Contrast happened right BEFORE midnight, Scan happened right AFTER midnight)
    if time_difference.total_seconds() > 82800:
        contrast_dt = contrast_dt - timedelta(days=1)

    # Scenario B: Contrast looks like it happened 23+ hours AFTER the scan
    # (Real world: Scan started right BEFORE midnight, Contrast injected right AFTER midnight)
    elif time_difference.total_seconds() < -82800:
        contrast_dt = contrast_dt + timedelta(days=1)

    # Scenario C: Normal daytime workflow or same-day post-midnight operations
    # No adjustments needed, the calendar date matches perfectly.
            
    return contrast_dt
