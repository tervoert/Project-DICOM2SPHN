"""
dicom_contrast_bolus_tags_reader.py:
    Part of the example dicom2sphn package.
    It contains functions for reading DICOM contrast bolus tags.
"""
import re
from datetime import datetime, time, timedelta

from pydicom import Dataset
from pydicom.multival import MultiValue
from pydicom.sequence import Sequence
from pydicom.valuerep import DSdecimal, DSfloat

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
from .tools import complete_dicom_time, is_valid_string

#
# DICOM defines two modules for contrast bolus information: 
#
# - The "Contrast/Bolus" module
#   - Used by legacy (single-frame) DICOM objects, such as CT, MR, and XA images.
#   - Table C.7-12. Contrast/Bolus Module Attributes
#   - Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.4.html#table_C.7-12
#
# - The "Enhanced Contrast/Bolus" module.
#   - Used by enhanced (multi-frame) DICOM objects, such as Enhanced CT, Enhanced MR, and Enhanced XA images.
#   - Table C.7-12b. Enhanced Contrast/Bolus Module Attributes
#   - Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.4b.html#table_C.7-12b

# - Checking for the presence of a "Contrast/Bolus" or an "Enhanced Contrast/Bolus" module in the DICOM dataset
#   - The legacy (single-frame) Contrast/Bolus module:
#       - has a mandatory "Contrast/Bolus Agent Attribute (0018,0010)" tag in case contrast agent was present. The tag can be empty however.
#   - The enhanced (multi-frame) Contrast/Bolus module:
#       - has a mandatory "Contrast/Bolus Agent Number Attribute (0018,9337)" tag in the "Contrast/Bolus Agent Sequence Attribute (0018,0012)" tag in case contrast agent was present.
#       - doesn't have the "Contrast/Bolus Agent Attribute (0018,0010)" tag.

    # ToDo: Edwin 2026-10-09 - Implement processing for Contrast / Bolus module
    # ToDo: Edwin 2026-10-09 - Implement processing for Enhanced Contrast / Bolus module

# ---------------------------------------------------------------------------------------------------------------------
# Functions for processing the Legacy (single-frame) "Contrast/Bolus" module
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-11-08
#
def process_dicom_contrast_information(dataset: Dataset, context: Context, indent: int=0) -> None:
    """
    Processes the DICOM Contrast/Bolus information, either legacy (single-frame) or enhanced (multi-frame),
    and stores contrast agent administration events in the data_store.
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
    has_enhanced_contrast_bolus_module = contrast_bolus_agent_sequence is not None and all(hasattr(item, "ContrastBolusAgentNumber") for item in contrast_bolus_agent_sequence)

    if not has_legacy_contrast_bolus_module and not has_enhanced_contrast_bolus_module:
        logger.debug(" "*(indent+0) + "No DICOM (legacy or enhanced) Contrast/Bolus module found in the dataset.")
        return

    elif has_legacy_contrast_bolus_module and not has_enhanced_contrast_bolus_module:
        logger.debug(" "*(indent+0) + "Found DICOM legacy (single-frame) Contrast/Bolus module.")
        process_contrast_bolus_module_from_dicom(dataset, context, indent=indent+2)

    elif has_enhanced_contrast_bolus_module and not has_legacy_contrast_bolus_module:
        logger.debug(" "*(indent+0) + "Found DICOM enhanced (multi-frame) Contrast/Bolus module.")
        process_enhanced_contrast_bolus_module_from_dicom(dataset, context, indent=indent+2)

    else:
        raise ValueError("This should not happen: Found both DICOM legacy (single-frame) and enhanced (multi-frame) Contrast/Bolus modules.")


#
# Edwin 2026-11-08
#
def process_contrast_bolus_module_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> None:
    """
    Processes the DICOM legacy (single-frame) Contrast/Bolus Module information 
    and stores contrast agent administration events in the data_store.
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
    sphn_schema = context.sphn_schema

    sphn_contrast_agent_list: list[SPHNContrastAgent] = []
    sphn_administration_route_code: SPHNCode | None = None
    sphn_administration_route_codes: list[SPHNCode] = []

    #
    # Start with the Contrast Agent names
    #
    logger.debug(" "*(indent+0) + "Start processing DICOM ContrastBolusAgentSequence and ContrastBolusAgent tags.")

    # 
    # 1. Check if there is coded information in the ContrastBolusAgentSequence
    #

    logger.debug(" "*(indent+2) + "Checking for a DICOM ContrastBolusAgentSequence tag")

    contrast_bolus_agent_sequence = get_contrast_bolus_agent_sequence_from_dicom(dataset, context, indent=indent+4)

    if contrast_bolus_agent_sequence is not None:

        assert isinstance(contrast_bolus_agent_sequence, Sequence)

        logger.debug(" "*(indent+2) + f"Found DICOM ContrastBolusAgentSequence (coded info) with {len(contrast_bolus_agent_sequence)} item(s)")

        #
        # 1.1. Process the items in the ContrastBolusAgentSequence (coded info)
        #

        # Process each item in the ContrastBolusAgentSequence
        for i, item in enumerate(contrast_bolus_agent_sequence, start=1):
        
            assert isinstance(item, Dataset)

            logger.debug(" "*(indent+4) + f"Processing item {i} of {len(contrast_bolus_agent_sequence)} in DICOM ContrastBolusAgentSequence tag")
        
            sphn_contrast_agent = process_legacy_contrast_bolus_agent_sequence_item(item, context, indent+6)

            if sphn_contrast_agent is not None:
                if sphn_contrast_agent not in sphn_contrast_agent_list:
                    sphn_contrast_agent_list.append(sphn_contrast_agent)
                    logger.debug(" "*(indent+6) + "SPHN Contrast Agent added to the list")
                else:
                    logger.debug(" "*(indent+6) + "SPHN Contrast Agent is already in the list")

    #
    # 2. In case there was no SPHN Contrast Agent created before,
    #    check if there is free text information in the Contrast/Bolus Agent tag in the DICOM dataset
    #    and create SPHN Contrast Agent objects from it if possible
    #

    if len(sphn_contrast_agent_list) == 0:

        logger.debug(" "*(indent+2) + "Checking for a DICOM ContrastBolusAgent (free text info) tag")

        contrast_bolus_agent_str = get_contrast_bolus_agent_from_dicom(dataset, context, indent=indent+4)

        if contrast_bolus_agent_str is not None:

            assert isinstance(contrast_bolus_agent_str, str)

            logger.debug(" "*(indent+2) + f"Found DICOM ContrastBolusAgent (free text info) with value: '{contrast_bolus_agent_str}'")

            # Add the free text contrast agent to the data store for statistical purposes
            data_store.add_contrast_bolus_agent_to_dict(contrast_bolus_agent_str)

            # ToDo: Edwin: Add a call to an AI model to predict the DICOM contrast agent code(s) based on the text in the contrast_bolus_agent string

            # 
            # 2.1 Check if a contrast agent trade name, or a contrast agent active ingredient or an active element (or functional group) name
            #     can be found in the contrast_bolus_agent free text string
            #

            contrast_agents_dict_list = extract_contrast_agents(contrast_bolus_agent_str, context, indent=indent+4)

            logger.debug(" "*(indent+2) + f"Extracted: '{len(contrast_agents_dict_list)}' contrast agent(s) from free text")

            for i, contrast_agent_dict in enumerate(contrast_agents_dict_list):
                
                logger.debug(" "*(indent+4) + f"Processing contrast agent info: ({i+1}/{len(contrast_agents_dict_list)})")

                sphn_contrast_agent = process_contrast_bolus_agent_dict(contrast_agent_dict, context, indent=indent+6)

                if sphn_contrast_agent is not None:
                    if sphn_contrast_agent not in sphn_contrast_agent_list:
                        sphn_contrast_agent_list.append(sphn_contrast_agent)
                        logger.debug(" "*(indent+4) + "Added SPHN Contrast Agent to the list")
                    else:
                        logger.debug(" "*(indent+4) + "SPHN Contrast Agent is already in the list")

                else:            
                    logger.debug(" "*(indent+4) + "Failed to create an SPHN Contrast Agent object from DICOM ContrastBolusAgent (free text info).")

    logger.debug(" "*(indent+0) + "Done processing DICOM ContrastBolusAgentSequence and ContrastBolusAgent tags." + 
                 f" Found: '{len(sphn_contrast_agent_list)}' SPHN Contrast Agent object(s)")

    logger.debug(" "*(indent+0) + "Start processing other ContrastBolus tags.")

    #
    # 3. Check if there is a DICOM term in the ContrastBolusIngredient tag in the DICOM dataset
    #

    sphn_contrast_agent_active_ingredient: SPHNContrastAgentActiveIngredient | None = None

    contrast_bolus_ingredient_str = get_contrast_bolus_ingredient_from_dicom(dataset, context, indent=indent+2)

    if contrast_bolus_ingredient_str is not None:

        assert isinstance(contrast_bolus_ingredient_str, str)

        logger.debug(" "*(indent+2) + f"DICOM ContrastBolusIngredient found: '{contrast_bolus_ingredient_str}'")

        sphn_contrast_agent_active_ingredient = process_contrast_bolus_ingredient(contrast_bolus_ingredient_str, context, indent+4)

        if sphn_contrast_agent_active_ingredient is None:
            logger.debug(" "*(indent+4) + "Failed to create an SPHN Contrast Agent Active Ingredient from DICOM ContrastBolusIngredient Term.")
            # Add the DICOM contrast bolus ingredient to the data store for statistical purposes
            data_store.add_unknown_contrast_bolus_ingredient_to_dict(contrast_bolus_ingredient_str)

        else:
            # Add the DICOM contrast bolus ingredient to the data store for statistical purposes
            data_store.add_known_contrast_bolus_ingredient_to_dict(contrast_bolus_ingredient_str)

            #
            # 3.1. In case there was no SPHN Contrast Agent created before, 
            #      create a new SPHN Contrast Agent object and add the SPHN Contrast Agent Active Ingredient to it
            #

            if len(sphn_contrast_agent_list) == 0:
                sphn_contrast_agent = create_sphn_contrast_agent(
                    active_ingredient_list=[sphn_contrast_agent_active_ingredient],
                    article=None,
                    context=context,
                    indent=indent+4
                )
                logger.debug(" "*(indent+4) + "Created new SPHN Contrast Agent and added the SPHN Contrast Agent Active Ingredient.")

                sphn_contrast_agent_list.append(sphn_contrast_agent)
                logger.debug(" "*(indent+4) + "Added the new SPHN Contrast Agent to the list.")

            #
            # 3.2. In case there is only one SPHN Contrast Agent found, 
            #      add the SPHN Contrast Agent Active Ingredient to it
            #

            if len(sphn_contrast_agent_list) == 1:
                sphn_contrast_agent = sphn_contrast_agent_list[0]
                sphn_contrast_agent.add_sphn_contrast_agent_active_ingredient(sphn_contrast_agent_active_ingredient)
                logger.debug(" "*(indent+4) + "Added SPHN Contrast Agent Active Ingredient to the existing SPHN Contrast Agent.")

            #
            # 3.3. In case there are multiple SPHN Contrast Agents found, 
            #      do not add the SPHN Contrast Agent Active Ingredient to any SPHN Contrast Agent object
            #
            if len(sphn_contrast_agent_list) > 1:
                sphn_contrast_agent_active_ingredient = None
                logger.debug(" "*(indent+4) + "Multiple SPHN Contrast Agents found. Cannot add the SPHN Contrast Agent Active Ingredient to a specific SPHN Contrast Agent object.")

    #
    # 4. Check if the ingredient concentration is available and process it
    #    but only if the SPHN Contrast Agent Active Ingredient obtained in the previous steps is also present
    # 

    if sphn_contrast_agent_active_ingredient is not None:

        contrast_bolus_ingredient_concentration = get_contrast_bolus_ingredient_concentration_from_dicom(dataset, context, indent=indent+2)

        if contrast_bolus_ingredient_concentration is not None:

            assert isinstance(contrast_bolus_ingredient_concentration, float)

            logger.debug(" "*(indent+2) + f"ContrastBolusIngredientConcentration found: {contrast_bolus_ingredient_concentration} mg/ml")

            # Create an SPHNQuantity object
            sphn_code_mg_per_ml = SPHNCode( 
                sphn_schema = sphn_schema,
                has_identifier = "mgpermL",  # SPHN UCUM unit code, label: "mg/ml", comment: "milligrams per milliliter"
                has_coding_system_and_version = "UCUM"
            )
            sphn_unit_mg_per_ml = SPHNUnit(
                sphn_schema = sphn_schema,
                has_code = sphn_code_mg_per_ml
            )
            sphn_quantity_concentration = SPHNQuantity(
                sphn_schema = sphn_schema,
                has_value = contrast_bolus_ingredient_concentration,
                has_unit = sphn_unit_mg_per_ml
            )

            #
            # 4.1. Add the concentration to the ingredient
            #
            sphn_contrast_agent_active_ingredient.has_concentration = sphn_quantity_concentration
            logger.debug(" "*(indent+4) + "Added concentration to ingredient")

    #
    # The Route of Administration, the Volume, the Total Dose, the Flow Rate and Flow Duration 
    # will only be used in case there is one contrast agent defined. 
    #
    if len(sphn_contrast_agent_list) == 1:

        #
        # 5. Check if there is a Contrast/Bolus Administration Route Sequence (coded information) in the DICOM dataset
        # 
        
        contrast_bolus_administration_route_sequence = get_contrast_bolus_administration_route_sequence_from_dicom(dataset, context, indent=indent+2)

        if contrast_bolus_administration_route_sequence is not None:
            
            assert isinstance(contrast_bolus_administration_route_sequence, Sequence)

            logger.debug(" "*(indent+2) + f"DICOM ContrastBolusAdministrationRouteSequence (coded info) found with {len(contrast_bolus_administration_route_sequence)} item(s)")

            #
            # 5.1. Process each item in the sequence
            #

            # There should be exactly zero or one item(s) in the Contrast/Bolus Administration Route Sequence
            if len(contrast_bolus_administration_route_sequence) == 0:
                logger.debug(" "*(indent+4) + "No items found in ContrastBolusAdministrationRouteSequence")

            elif len(contrast_bolus_administration_route_sequence) == 1:

                sphn_administration_route_code = process_contrast_bolus_administration_route_sequence_item(contrast_bolus_administration_route_sequence[0], context, indent+4)

                if sphn_administration_route_code is None:
                    logger.debug(" "*(indent+4) + "Failed to create an SPHN Administration Route Code object from DICOM ContrastBolusAdministrationRouteSequence (coded info).")
                else:
                    if sphn_administration_route_code not in sphn_administration_route_codes:
                        sphn_administration_route_codes.append(sphn_administration_route_code)

            else:
                raise ValueError("Unexpected number of items in ContrastBolusAdministrationRouteSequence")

        #
        # 6. Check if there is a Contrast/Bolus Route (free text) in the DICOM dataset
        # 

        route_string = get_contrast_bolus_route_from_dicom(dataset, context, indent=indent+2)

        if route_string is not None:

            assert is_valid_string(route_string)

            logger.debug(" "*(indent+2) + f"Found DICOM Contrast/Bolus Route (free text): {route_string}")

            sphn_administration_route_codes_extracted = process_contrast_bolus_route(route_string, context, indent=indent+4)

            if sphn_administration_route_codes_extracted:
                logger.debug(" "*(indent+2) + f"Successfully processed DICOM Contrast/Bolus Route (free text) and created '{len(sphn_administration_route_codes_extracted)}' SPHN Code object(s) for Administration Route.")

                count = 0
                for sphn_administration_route_code in sphn_administration_route_codes_extracted:
                    if sphn_administration_route_code not in sphn_administration_route_codes:
                        sphn_administration_route_codes.append(sphn_administration_route_code)
                        count += 1
                logger.debug(" "*(indent+2) + f"Added '{count}' new SPHN Administration Route Code object(s) to the list.")

            else:
                logger.debug(" "*(indent+2) + "Failed to create an SPHN Administration Route Code object from DICOM Contrast/Bolus Route (free text).")

        #
        # 7. Process the Contrast/Bolus Volume (Total volume administered in milliliters of diluted contrast agent)
        #

        sphn_quantity_total_diluted_volume = None

        volume = get_contrast_bolus_volume_from_dicom(dataset, context, indent=indent+2)

        if volume is not None:
            # Process the volume information here
            sphn_quantity_total_diluted_volume = create_sphn_quantity_for_volume(volume, context, indent=indent+2)

            if sphn_quantity_total_diluted_volume is not None:
                logger.debug(" "*(indent+2) + f"Successfully created SPHN Quantity for administered total (diluted) volume: '{volume}' ml.")
            else:
                logger.debug(" "*(indent+2) +"Failed to create SPHN Quantity for administered total (diluted) volume.")

        #
        # 8. Process the Contrast/Bolus Total Dose (Total amount of (undiluted) contrast agent administered)
        #
        
        sphn_quantity_total_undiluted_dose = None

        total_dose = get_contrast_bolus_total_dose_from_dicom(dataset, context, indent=indent+2)

        if total_dose is not None:
            # Process the total dose information here
            sphn_quantity_total_undiluted_dose = create_sphn_quantity_for_volume(total_dose, context, indent=indent+2)

            if sphn_quantity_total_undiluted_dose is not None:
                logger.debug(" "*(indent+2) + f"Successfully created SPHN Quantity for administered total (undiluted) dose: '{total_dose}' ml.")
            else:
                logger.debug(" "*(indent+2) + "Failed to create SPHN Quantity for administered total (undiluted) dose.")

        # 
        # 9. Process the Contrast/Bolus Flow Rate (Rate at which the contrast agent is administered)
        #
        
        flow_rate_list = get_contrast_flow_rate_from_dicom(dataset, context, indent=indent+2)

        # 
        # 10. Process the Contrast/Bolus Flow Duration (Duration over which the contrast agent is administered)
        #
        
        flow_duration_list = get_contrast_flow_duration_from_dicom(dataset, context, indent=indent+2)
        
        # 
        # 11. Combine Flow Rate and Duration
        #
        
        sphn_flow_profile_interval_list = []

        if flow_rate_list and flow_duration_list:
            
            if len(flow_rate_list) != len(flow_duration_list):
                logger.debug(" "*(indent+2) + "Mismatch between number of flow rates and flow durations.")
            else:
                for flow_rate, flow_duration in zip(flow_rate_list, flow_duration_list):
                    
                    sphn_flow_profile_interval = None
                    sphn_quantity_flow_rate = None
                    sphn_quantity_flow_duration = None

                    if flow_rate is not None:
                        sphn_quantity_flow_rate = create_sphn_quantity_for_flow_rate(flow_rate, context, indent=indent+2)

                    if flow_duration is not None:
                        sphn_quantity_flow_duration = create_sphn_quantity_for_flow_duration(flow_duration, context, indent=indent+2)

                    if sphn_quantity_flow_rate is not None:
                        logger.debug(" "*(indent+2) +f"Successfully created SPHN Quantity for contrast/bolus flow rate: {flow_rate} ml/s")
                    else:
                        logger.debug(" "*(indent+2) +"Failed to determine contrast/bolus flow rate.")

                    if sphn_quantity_flow_duration is not None:
                        logger.debug(" "*(indent+2) +f"Successfully created SPHN Quantity for contrast/bolus flow duration: {flow_duration} s")
                    else:
                        logger.debug(" "*(indent+2) +"Failed to determine contrast/bolus flow duration.")

                    #  Check if any of the processed information is available before creating the SPHNFlowProfileInterval object.
                    if sphn_quantity_flow_rate is not None or sphn_quantity_flow_duration is not None:

                        sphn_flow_profile_interval = SPHNFlowProfileInterval(
                            sphn_schema = sphn_schema,
                            has_start_datetime = None,
                            has_end_datetime = None,
                            has_volume = None,
                            has_volumetric_flow_rate = sphn_quantity_flow_rate,
                            has_duration = sphn_quantity_flow_duration
                            )

                    if sphn_flow_profile_interval is not None:
                        logger.debug(" "*(indent+2) +"Successfully created SPHN Flow Profile Interval object.")
                        
                        # Add the SPHN Flow Profile Interval to the list, even duplicates
                        sphn_flow_profile_interval_list.append(sphn_flow_profile_interval)
                        logger.debug(" "*(indent+2) +"Added SPHN Flow Profile Interval object to the list.")

                    else:
                        logger.debug(" "*(indent+2) +"Failed to create SPHN Flow Profile Interval object.")


    #
    # 12. Process the start time and combine it with a relevant date to get the complete start datetime.
    #

    contrast_bolus_start_datetime = None

    start_time = get_contrast_bolus_start_time_from_dicom(dataset, context, indent=indent+2)

    if start_time is not None:

        # Complete the DICOM contrast/bolus start time to ensure it has all necessary components (hours, minutes, seconds) 
        # and return it as a TM object (or type datetime.time).
        contrast_bolus_start_time = complete_dicom_time(start_time, logger, indent=indent+2)

        if contrast_bolus_start_time is None:
            logger.debug(" "*(indent+2) + "Failed to complete contrast/bolus start time from DICOM dataset.")
        else:
            # Get the complete contrast/bolus start datetime by combining the start time with the relevant acquisition/series/study date.
            contrast_bolus_start_datetime = get_contrast_bolus_datetime(
                contrast_bolus_time=contrast_bolus_start_time, 
                acquisition_datetime=data_store.acquisition_start_datetime, 
                series_datetime=data_store.series_start_datetime,
                study_datetime=data_store.study_start_datetime,
                context=context, 
                indent=indent+2
            )

            if contrast_bolus_start_datetime is not None:
                logger.debug(" "*(indent+2) + f"Determined contrast/bolus start datetime: {contrast_bolus_start_datetime!s}")
            else:
                logger.debug(" "*(indent+2) + "Failed to combine contrast/bolus start time with relevant date to get start datetime.")
    
    if contrast_bolus_start_datetime is None:
        logger.debug(" "*(indent+2) + "Contrast/bolus start datetime is not available, trying fallback datetimes.")
        
        # ToDo: Edwin: Search other hospital databases for contrast/bolus start time information.

        contrast_bolus_start_datetime = get_contrast_bolus_datetime_fallback(context=context, indent=indent+4)

        if contrast_bolus_start_datetime is not None:
            logger.debug(" "*(indent+2) + f"Using fallback contrast/bolus start datetime: {contrast_bolus_start_datetime!s}")
        else:
            logger.debug(" "*(indent+2) + "No fallback contrast/bolus start datetime available.")

    #
    # 13. Process the end time and combine it with a relevant date to get the complete end datetime.
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
                acquisition_datetime=data_store.acquisition_start_datetime, 
                series_datetime=data_store.series_start_datetime,
                study_datetime=data_store.study_start_datetime,
                context=context, 
                indent=indent+2
            )

            if contrast_bolus_end_datetime is not None:
                logger.debug(" "*(indent+2) + f"Determined contrast/bolus end datetime: {contrast_bolus_end_datetime!s}")
            else:
                logger.debug(" "*(indent+2) + "Failed to determine contrast/bolus end datetime.")

    #
    # 14. Create SPHN Contrast Agent Administration Event object(s) based on the collected information
    #

    if len(sphn_contrast_agent_list) == 0 \
        and contrast_bolus_start_datetime is not None \
        and contrast_bolus_end_datetime != data_store.fallback_contrast_agent_datetime \
        and sphn_administration_route_code is not None:

        # No contrast agent case but there is other information available
        # The SPHN schema requires a contrast agent
        # Creating a contrast agent object with a placeholder active ingredient

        logger.debug(" "*(indent+2) + "No contrast agent found. Creating a contrast agent with a general 'Contrast Media' active ingredient.")
        sphn_contrast_agent_active_ingredient = create_sphn_contrast_agent_active_ingredient(
            code_scheme_designator="SNOMED",
            code_value="385420005",
            code_descr="| Contrast media (substance) |", 
            context=context, 
            indent=indent+2
        )
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
            start_datetime=contrast_bolus_start_datetime,
            end_datetime=contrast_bolus_end_datetime,
            sphn_flow_profile_interval_list=None,
            context=context,
            indent=indent+2
        )

        if sphn_contrast_agent_administration_event is None:
            logger.debug(" "*(indent+2) + "Failed to create SPHN Contrast Agent Administration Event object.")
        else:
            logger.debug(" "*(indent+2) + "Successfully created SPHN Contrast Agent Administration Event object.")
            
            # Add to the list if not already in it
            data_store.add_sphn_contrast_agent_administration_event_to_list(
                sphn_contrast_agent_administration_event=sphn_contrast_agent_administration_event,
                logger=logger,
                indent=indent+2
            )

    if len(sphn_contrast_agent_list) == 1 \
        and contrast_bolus_start_datetime is not None:

        # Single contrast agent case, create an administration event for it.

        logger.debug(" "*(indent+2) + "Single contrast agent found.")

        sphn_contrast_agent = sphn_contrast_agent_list[0]

        # ToDo: Edwin: Add more information if available for the single contrast agent case.

        # Check if there are multiple administration route codes for the single contrast agent case.
        sphn_administration_route_code_checked = None
        if len(sphn_administration_route_codes) == 0:
            logger.debug(" "*(indent+2) + "No administration route code found for the single contrast agent.")
        elif len(sphn_administration_route_codes) == 1:
            logger.debug(" "*(indent+2) + "Single administration route code found for the single contrast agent.")
            sphn_administration_route_code_checked = sphn_administration_route_codes[0]
        elif len(sphn_administration_route_codes) > 1:
            logger.debug(" "*(indent+2) + f"Multiple administration route codes found for the single contrast agent: '{len(sphn_administration_route_codes)}'.")

        # Check and assign the total diluted volume to the SPHN Contrast Agent object if available.
        if sphn_quantity_total_diluted_volume is not None:
            # Assign the volume to the SPHN Contrast Agent object
            sphn_contrast_agent.has_quantity = sphn_quantity_total_diluted_volume
            logger.debug(" "*(indent+0) +"Added contrast/bolus total administered (diluted) volume to SPHN Contrast Agent object.")

        # Check and assign the total undiluted dose to the SPHN Contrast Agent Active Ingredient object if available.
        # Only when there is a single contrast agent active ingredient
        if sphn_quantity_total_undiluted_dose is not None \
            and sphn_contrast_agent.has_active_ingredient_list is not None \
            and len(sphn_contrast_agent.has_active_ingredient_list) == 1:
            # Assign the total dose to the SPHN Contrast Agent Active Ingredient object
            sphn_contrast_agent.has_active_ingredient_list[0].has_quantity = sphn_quantity_total_undiluted_dose
            logger.debug(" "*(indent+0) +"Added contrast/bolus total administered (undiluted) dose to SPHN Contrast Agent Active Ingredient object.")

        sphn_contrast_agent_administration_event = create_sphn_contrast_agent_administration_event(
            sphn_contrast_agent=sphn_contrast_agent,
            sphn_administration_route_code=sphn_administration_route_code_checked,
            start_datetime=contrast_bolus_start_datetime,
            end_datetime=contrast_bolus_end_datetime,
            sphn_flow_profile_interval_list=sphn_flow_profile_interval_list,
            context=context,
            indent=indent+2
        )
        
        if sphn_contrast_agent_administration_event is None:
            logger.debug(" "*(indent+2) + "Failed to create SPHN Contrast Agent Administration Event object.")
        else:
            logger.debug(" "*(indent+2) + "Successfully created SPHN Contrast Agent Administration Event object.")
            
            # Add to the list if not already in it
            data_store.add_sphn_contrast_agent_administration_event_to_list(
                sphn_contrast_agent_administration_event=sphn_contrast_agent_administration_event,
                logger=logger,
                indent=indent+2
            )

    if len(sphn_contrast_agent_list) > 1 \
        and contrast_bolus_start_datetime is not None:

        # Multiple contrast agent case, create administration events for each. 
        # We cannot use the other information as we donn't know which contrast agent it belongs to.

        logger.debug(" "*(indent+2) + f"Multiple contrast agents found: '{len(sphn_contrast_agent_list)}'.")

        for index, sphn_contrast_agent in enumerate(sphn_contrast_agent_list):
            
            logger.debug(" "*(indent+2) + f"Start creating SPHN Contrast Agent Administration Event object {index}/{len(sphn_contrast_agent_list)}")

            sphn_contrast_agent_administration_event = create_sphn_contrast_agent_administration_event(
                sphn_contrast_agent=sphn_contrast_agent,
                sphn_administration_route_code=sphn_administration_route_code,
                start_datetime=contrast_bolus_start_datetime,
                end_datetime=contrast_bolus_end_datetime,
                sphn_flow_profile_interval_list=None,
                context=context,
                indent=indent+2
            )

            if sphn_contrast_agent_administration_event is None:
                logger.debug(" "*(indent+2) + "Failed to create SPHN Contrast Agent Administration Event object.")
                continue

            logger.debug(" "*(indent+2) + "Successfully created SPHN Contrast Agent Administration Event object.")

            # Add to the list if not already in it
            data_store.add_sphn_contrast_agent_administration_event_to_list(
                sphn_contrast_agent_administration_event=sphn_contrast_agent_administration_event,
                logger=logger,
                indent=indent+2
            )


# ---------------------------------------------------------------------------------------------------------------------
# Functions for Processing Legacy (single-frame) module attributes
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-11-06
#
def process_legacy_contrast_bolus_agent_sequence_item(dataset: Dataset, context: Context, indent:int=0) -> SPHNContrastAgent|None:
    """
    Process the DICOM Legacy (single-frame) ContrastBolusAgentSequence item (Dataset) and return an SPHNContrastAgent object, if any.
    Parameters:
        - dataset: The DICOM Legacy (single-frame) ContrastBolusAgentSequence item (Dataset).
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int)

    logger = context.logger

    sphn_contrast_agent_active_ingredient: SPHNContrastAgentActiveIngredient|None = None

    #
    # 1. Process the coding information in the dataset and create the SPHN Contrast Agent Active Ingredient object
    #

    sphn_contrast_agent_active_ingredient = process_coding_data_in_contrast_bolus_sequence_item(dataset, context, indent=indent+2)
    
    # 
    # 2. Create the SPHN Contrast Agent object
    # 
    
    logger.debug(" "*(indent+0) + "Starting to create an SPHN Contrast Agent object")

    sphn_contrast_agent = create_sphn_contrast_agent(
        active_ingredient_list=[sphn_contrast_agent_active_ingredient],
        article=None,
        context=context,
        indent=indent+2
    )
    
    if sphn_contrast_agent is None:
        logger.debug(" "*(indent+0) + "Failed to create an SPHN Contrast Agent object")
        return None

    logger.debug(" "*(indent+0) + "Successfully created an SPHN Contrast Agent object")

    return sphn_contrast_agent


#
# Edwin 2026-10-20
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

    trade_name = None

    # Get the concentration as part of the name of the contrast agent from the dictionary
    concentration = contrast_agent_dict.get("concentration", None)

    assert concentration is None or isinstance(concentration, int)

    # Get the dose as part of the name of the contrast agent from the dictionary
    dose_value = None
    dose_unit = None
    dose_dict = contrast_agent_dict.get("dose", None)
    if dose_dict is not None:
        assert isinstance(dose_dict, dict)
    
        dose_value = dose_dict.get("value", None)
        if dose_value is not None:
            assert isinstance(dose_value, (int, float))
    
        dose_unit = dose_dict.get("unit", None)
        if dose_unit is not None:
            assert dose_unit in ["ml", "mg"]

    # Get the name of the contrast agent from the dictionary
    agent_name = contrast_agent_dict.get("agent", None)
    if agent_name is None:
        logger.debug(" "*(indent+0) + "Contrast agent name is missing in the provided dictionary")
        return None
    
    assert is_valid_string(agent_name)

    #
    # Check whether the agent_name is a trade name or an active ingredient name or an active element (or fuctional group) name
    # 

    # Note: Case-sensitive lookup in the dictionaries should not be a problem as the "extract_contrast_agents" function 
    #       already normalizes the names to match the case used in the dictionaries.

    # ToDo: Edwin
    # Check if the agent_name is a trade name
    # Note: In case the trade name contains multiple contrast agent ingredient names, 
    #       each one is added as a SPHN Contrast Agent Active Ingredient to the same SPHN contrast agent.
    if agent_name in DataConverter.contrast_agent_trade_name_2_manufacturer_and_ingredient_name:
        logger.debug(" "*(indent+0) + f"DICOM contrast agent '{agent_name}' is identified as a trade name")
        trade_name = agent_name

        sphn_contrast_agent = process_contrast_bolus_agent_trade_name(trade_name, concentration, dose_value, dose_unit, context, indent=indent+2)
        if sphn_contrast_agent is None:
            raise ValueError("This should never happen as the agent_name was found in the mapping dictionary before.")

    # ToDo: Edwin
    # Check if the agent_name is a contrast agent active ingredient name
    # Note: Each contrast agent active ingredient name is added as a SPHN Contrast Agent Active Ingredient
    #       to a separate SPHN Contrast Agent
    elif agent_name in DataConverter.contrast_agent_active_ingredient_name_2_snomed_code:
        logger.debug(" "*(indent+0) + f"DICOM contrast agent '{agent_name}' is identified as a contrast agent ingredient name")
        active_ingredient_name = agent_name

        sphn_contrast_agent = process_contrast_bolus_agent_active_ingredient_name(active_ingredient_name, context, indent=indent+2)
        if sphn_contrast_agent is None:
            raise ValueError("This should never happen as the agent_name was found in the mapping dictionary before.")

    # ToDo: Edwin
    # Check if the agent_name is a contrast agent active element (or functional group) name
    # Note: Each contrast agent active element (or functional group) name is added as a SPHN Contrast Agent Active Ingredient
    #       to a separate SPHN Contrast Agent
    elif agent_name.title() in DataConverter.contrast_agent_active_element_names_2_snomed_code: 
        logger.debug(" "*(indent+0) + f"DICOM contrast agent '{agent_name}' is identified as a contrast agent active element (or functional group) name")
        active_element_name = agent_name.title()

        sphn_contrast_agent = process_contrast_bolus_agent_active_element_name(active_element_name, context, indent=indent+2)
        if sphn_contrast_agent is None:
            raise ValueError("This should never happen as the agent_name was found in the mapping dictionary before.")

    else:
        raise ValueError("This should never happen. Any agent_name found by the extract_contrast_agents function should be in one of the mapping dictionaries.")

    return sphn_contrast_agent


#
# Edwin 2026-11-06
#
def process_contrast_bolus_agent_trade_name(trade_name:str, concentration: int|None, dose_value: float|None, dose_unit: str|None, context: Context, indent:int=0) -> SPHNContrastAgent|None:
    """
    Process the contrast agent normalized trade name and return a SPHNContrastAgent object
    Parameters:
        - trade_name: The contrast agent normalized trade name.
        - concentration: The concentration of the contrast agent as part of the name (can be None if not available)
        - dose_value: The dose value of the contrast agent (can be None if not available)
        - dose_unit: The dose unit ["ml", "mg"] of the contrast agent (can be None if not available)
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert is_valid_string(trade_name)
    assert concentration is None or isinstance(concentration, int)
    assert dose_value is None or isinstance(dose_value, (int, float))
    assert dose_unit is None or dose_unit in ["ml", "mg"]
    assert isinstance(context, Context)
    assert isinstance(indent, int)

    logger = context.logger
    data_store = context.data_store
    sphn_schema = context.sphn_schema

    sphn_contrast_agent_active_ingredient_list = []

    # Get the contrast agent active ingredient(s) list corresponding to the trade name
    # Note: Case-sensitive lookup as the name is expected to be normalized.
    result = DataConverter.contrast_agent_trade_name_2_manufacturer_and_ingredient_name.get(trade_name, None)

    # Check the format of the result
    assert isinstance(result, tuple) and len(result) == 3 and isinstance(result[1], list)

    # Extract the list of contrast agent active ingredient names from the result tuple
    contrast_agent_active_ingredient_name_list = result[1]
    assert len(contrast_agent_active_ingredient_name_list) > 0

    for index, contrast_agent_active_ingredient_name in enumerate(contrast_agent_active_ingredient_name_list, start=1):
        logger.debug(" "*(indent+2) + f"Processing contrast agent active ingredient {index}/{len(contrast_agent_active_ingredient_name_list)}: {contrast_agent_active_ingredient_name}")    

        assert is_valid_string(contrast_agent_active_ingredient_name)

        # Get the corresponding SNOMED code for the contrast agent active ingredient name
        # Note: Case-sensitive lookup as the name is expected to be normalized.
        contrast_agent_active_ingredient_code = DataConverter.contrast_agent_active_ingredient_name_2_snomed_code.get(contrast_agent_active_ingredient_name, None)

        # Check the format of the contrast_agent_active_ingredient_snomed_code
        assert isinstance(contrast_agent_active_ingredient_code, tuple) \
            and len(contrast_agent_active_ingredient_code) == 3 \
            and all(is_valid_string(item) for item in contrast_agent_active_ingredient_code)

        coding_scheme_designator = contrast_agent_active_ingredient_code[0]
        code_value = contrast_agent_active_ingredient_code[1]
        code_descr = contrast_agent_active_ingredient_code[2]

        logger.debug(" "*(indent+2) + "Starting to create an SPHN Contrast Agent Active Ingredient object")

        # Create the SPHN Contrast Agent Active Ingredient object
        sphn_contrast_agent_active_ingredient = create_sphn_contrast_agent_active_ingredient(
            coding_scheme_designator=coding_scheme_designator,
            code_value=code_value,
            code_descr=code_descr,
            context=context,
            indent=indent+4
        )

        if sphn_contrast_agent_active_ingredient is None:
            logger.debug(" "*(indent+2) + "Failed to create an SPHN Contrast Agent Active Ingredient object")
            return None

        logger.debug(" "*(indent+2) + "Successfully created an SPHN Contrast Agent Active Ingredient object")

        # Add to the list if it is not already in the list
        if sphn_contrast_agent_active_ingredient not in sphn_contrast_agent_active_ingredient_list:
            sphn_contrast_agent_active_ingredient_list.append(sphn_contrast_agent_active_ingredient)
            logger.debug(" "*(indent+2) + "SPHN Contrast Agent Active Ingredient added to the list")
        else:
            logger.debug(" "*(indent+2) + "SPHN Contrast Agent Active Ingredient is already in the list")

    # Create the SPHN Drug Article object with the trade name, concentration, and dose (if available)
    name = trade_name
    if concentration is not None:
        name = f"{name}-{concentration}"
    if dose_value is not None and dose_unit is not None:
        name = f"{name} {dose_value}{dose_unit}"

    logger.debug(" "*(indent+0) + "Creating an SPHN Drug Article object")

    sphn_drug_article = SPHNDrugArticle(
        sphn_schema = sphn_schema,
        has_name=name,
        has_source_system_list=[data_store.sphn_source_system]
    )

    logger.debug(" "*(indent+0) + "Starting to create an SPHN Contrast Agent object")

    # Create the SPHN Contrast Agent object
    sphn_contrast_agent = create_sphn_contrast_agent(
        active_ingredient_list=sphn_contrast_agent_active_ingredient_list,
        article=sphn_drug_article,
        context=context,
        indent=indent+2
    )

    logger.debug(" "*(indent+0) + "Successfully created an SPHN Contrast Agent object")

    return sphn_contrast_agent


#
# Edwin 2026-11-06
#
def process_contrast_bolus_agent_active_ingredient_name(active_ingredient_name:str, context: Context, indent:int=0) -> SPHNContrastAgent|None:
    """
    Process the contrast agent active ingredient normalized name and return a SPHNContrastAgent object
    Parameters:
        - active_ingredient_name: The contrast agent active ingredient normalized name
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert is_valid_string(active_ingredient_name)
    assert isinstance(context, Context)
    assert isinstance(indent, int)

    logger = context.logger

    sphn_contrast_agent_active_ingredient_list = []

    # Get the corresponding SNOMED code for the contrast agent active ingredient name
    # Note: Case-sensitive lookup as the name is expected to be normalized.
    contrast_agent_active_ingredient_code = DataConverter.contrast_agent_active_ingredient_name_2_snomed_code.get(active_ingredient_name, None)

    # Check the format
    assert isinstance(contrast_agent_active_ingredient_code, tuple) \
        and len(contrast_agent_active_ingredient_code) == 3 \
        and all(is_valid_string(item) for item in contrast_agent_active_ingredient_code)

    coding_scheme_designator = contrast_agent_active_ingredient_code[0]
    code_value = contrast_agent_active_ingredient_code[1]
    code_descr = contrast_agent_active_ingredient_code[2]

    logger.debug(" "*(indent+0) + "Starting to create an SPHN Contrast Agent Active Ingredient object")

    # Create the SPHN Contrast Agent Active Ingredient object
    sphn_contrast_agent_active_ingredient = create_sphn_contrast_agent_active_ingredient(
        coding_scheme_designator=coding_scheme_designator,
        code_value=code_value,
        code_descr=code_descr,
        context=context,
        indent=indent+2
    )

    if sphn_contrast_agent_active_ingredient is None:
        logger.debug(" "*(indent+0) + "Failed to create an SPHN Contrast Agent Active Ingredient object")
        return None

    logger.debug(" "*(indent+0) + "Successfully created an SPHN Contrast Agent Active Ingredient object")

    # Add to the list (There should only be one active ingredient)
    sphn_contrast_agent_active_ingredient_list = [sphn_contrast_agent_active_ingredient]
    logger.debug(" "*(indent+0) + "SPHN Contrast Agent Active Ingredient added to the list")

    logger.debug(" "*(indent+0) + "Starting to create an SPHN Contrast Agent object")

    # Create the SPHN Contrast Agent object
    sphn_contrast_agent = create_sphn_contrast_agent(
        active_ingredient_list=sphn_contrast_agent_active_ingredient_list,
        article=None,
        context=context,
        indent=indent+2
    )

    logger.debug(" "*(indent+0) + "Successfully created an SPHN Contrast Agent object")

    return sphn_contrast_agent


#
# Edwin 2026-11-06
#
def process_contrast_bolus_agent_active_element_name(active_element_name:str, context: Context, indent:int=0) -> SPHNContrastAgent:
    """
    Process the contrast agent active element (or functional group) normalized name and return a SPHNContrastAgent object
    Parameters:
        - active_element_name: The contrast agent active element (or functional group) normalized name
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert is_valid_string(active_element_name)
    assert isinstance(context, Context)
    assert isinstance(indent, int)

    logger = context.logger

    sphn_contrast_agent_active_ingredient_list = []

    # Get the corresponding SNOMED code for the contrast agent active element (or functional group) name
    # Note: Case-sensitive lookup as the name is expected to be normalized.
    contrast_agent_active_element_code = DataConverter.contrast_agent_active_element_names_2_snomed_code.get(active_element_name, None)

    # Check the format
    assert isinstance(contrast_agent_active_element_code, tuple) \
        and len(contrast_agent_active_element_code) == 3 \
        and all(is_valid_string(item) for item in contrast_agent_active_element_code)

    coding_scheme_designator = contrast_agent_active_element_code[0]
    code_value = contrast_agent_active_element_code[1]
    code_descr = contrast_agent_active_element_code[2]

    logger.debug(" "*(indent+0) + "Starting to create an SPHN Contrast Agent Active Ingredient object")

    # Create the SPHN Contrast Agent Active Ingredient object
    sphn_contrast_agent_active_ingredient = create_sphn_contrast_agent_active_ingredient(
        coding_scheme_designator=coding_scheme_designator,
        code_value=code_value,
        code_descr=code_descr,
        context=context,
        indent=indent+2
    )

    if sphn_contrast_agent_active_ingredient is None:
        logger.debug(" "*(indent+0) + "Failed to create an SPHN Contrast Agent Active Ingredient object")
        return None

    logger.debug(" "*(indent+0) + "Successfully created an SPHN Contrast Agent Active Ingredient object")

    # Add to the list (There should only be one active ingredient)
    sphn_contrast_agent_active_ingredient_list = [sphn_contrast_agent_active_ingredient]
    logger.debug(" "*(indent+0) + "SPHN Contrast Agent Active Ingredient added to the list")

    logger.debug(" "*(indent+0) + "Starting to create an SPHN Contrast Agent object")

    # Create the SPHN Contrast Agent object
    sphn_contrast_agent = create_sphn_contrast_agent(
        active_ingredient_list=sphn_contrast_agent_active_ingredient_list,
        article=None,
        context=context,
        indent=indent+2
    )
    
    logger.debug(" "*(indent+0) + "Successfully created an SPHN Contrast Agent object")

    return sphn_contrast_agent


#
# Edwin 2026-11-06
#
def process_contrast_bolus_ingredient(ingredient_term:str, context: Context, indent:int=0) -> SPHNContrastAgentActiveIngredient|None:
    """
    Process the DICOM contrast ingredient term and return an SPHNContrastAgentActiveIngredient object, if any.
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

    # Convert the ingredient term to title case for consistent lookup
    term_title_case = ingredient_term.title()

    # Get the corresponding SNOMED code for the DICOM contrast ingredient term
    # Note: Case-sensitive lookup as the name is expected to be normalized.
    contrast_agent_active_element_code = DataConverter.contrast_agent_active_element_names_2_snomed_code.get(term_title_case, None)

    # Check if the ingredient term is known
    if contrast_agent_active_element_code is None:
        logger.debug(" "*(indent+0) + f"DICOM contrast ingredient term '{ingredient_term}' normalised as '{term_title_case}' is not in the mapping dictionary")
        return None

    # Check the format
    assert isinstance(contrast_agent_active_element_code, tuple) \
        and len(contrast_agent_active_element_code) == 3 \
        and all(is_valid_string(item) for item in contrast_agent_active_element_code)

    coding_scheme_designator = contrast_agent_active_element_code[0]
    code_value = contrast_agent_active_element_code[1]
    code_descr = contrast_agent_active_element_code[2]

    logger.debug(" "*(indent+0) + "Starting to create an SPHN Contrast Agent Active Ingredient object")

    # Create the SPHN Contrast Agent Active Ingredient object
    sphn_contrast_agent_active_ingredient = create_sphn_contrast_agent_active_ingredient(
        coding_scheme_designator=coding_scheme_designator,
        code_value=code_value,
        code_descr=code_descr,
        context=context,
        indent=indent+2
    )

    if sphn_contrast_agent_active_ingredient is None:
        logger.debug(" "*(indent+0) + "Failed to create an SPHN Contrast Agent Active Ingredient object")
        return None

    logger.debug(" "*(indent+0) + "Successfully created an SPHN Contrast Agent Active Ingredient object")

    return sphn_contrast_agent_active_ingredient


#
# Edwin 2026-10-28
#
def process_contrast_bolus_route(route_string:str, context: Context, indent:int=0) -> list[SPHNCode]:
    """
    Process the DICOM route string and return a list of matched SPHN administration routes codes
    Parameters:
        - route_string: The DICOM contrast bolus route string.
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert is_valid_string(route_string)
    assert isinstance(context, Context)
    assert isinstance(indent, int)
    
    logger = context.logger
    data_store = context.data_store
    sphn_schema = context.sphn_schema
    
    sphn_code_list = []
    routes_found = []

    matches_found = extract_administration_routes(route_string, context, indent=indent)

    if not matches_found:
        logger.debug(" "*(indent+0) + f"No matches found for route: '{route_string}'")
        # For statistics, add the route string to the unknown contrast bolus routes dictionary
        data_store.add_unknown_contrast_bolus_route_to_dict(route_string)

    for item_dict in matches_found:

        route_str = item_dict.get('Route', None)
        code_tuple = item_dict.get('Code', None)

        assert isinstance(code_tuple, tuple) and len(code_tuple) == 3
        assert all(is_valid_string(item) for item in code_tuple)

        coding_scheme_designator = code_tuple[0]
        code_value = code_tuple[1]
        code_descr = code_tuple[2]

        sphn_code_route = SPHNCode( 
            sphn_schema = sphn_schema,
            has_coding_system_and_version = coding_scheme_designator,
            has_identifier = code_value,
            has_name = code_descr
            )

        logger.debug(" "*(indent+0) + f"Successfully Created SPHN Code object for code: '{code_tuple}'")

        if sphn_code_route not in sphn_code_list:
            sphn_code_list.append(sphn_code_route)

        # For statistics, add the route string to the known contrast bolus routes dictionary
        data_store.add_known_contrast_bolus_route_to_dict(route_str)
        # For statistics, keep track of the routes found for this route string
        routes_found.append(route_str)

    # For statistics, add the route string and routes_found to the contrast bolus routes dictionary
    data_store.add_contrast_bolus_route_to_dict(route_string, routes_found)

    return sphn_code_list


#
# Edwin 2026-10-28
#
def extract_administration_routes(route_string:str, context: Context, indent: int=0) -> list[dict]:
    """
    Extracts administration route codes from the Contrast/Bolus Route Tag string.
    Parameters:
        - route_string: The DICOM contrast bolus (administration) route string.
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    Returns:
        - A list of dictionaries containing the matched administration routes and their corresponding Codes.
    """

    assert is_valid_string(route_string)
    assert isinstance(context, Context)
    assert isinstance(indent, int)
    
    # Ensure that every route pattern has a corresponding code in the DataConverter class
    assert hasattr(DataConverter, "route_patterns") \
        and hasattr(DataConverter, "sphn_route_codes") \
        and isinstance(DataConverter.route_patterns, dict) \
        and isinstance(DataConverter.sphn_route_codes, dict) \
        and all(isinstance(route_name, str) and isinstance(pattern, str) for route_name, pattern in DataConverter.route_patterns.items()) \
        and all(isinstance(route_name, str) and isinstance(snomed_code, tuple) for route_name, snomed_code in DataConverter.sphn_route_codes.items()) \
        and all(len(snomed_code) == 3 for snomed_code in DataConverter.sphn_route_codes.values()) \
        and all(route_name in DataConverter.sphn_route_codes for route_name in DataConverter.route_patterns)
    
    logger = context.logger
    
    # Define the regex patterns for the administration routes (case-insensitive)
    route_patterns = {}
    for route_name, pattern in DataConverter.route_patterns.items():
        route_patterns[route_name] = re.compile(pattern, re.IGNORECASE)
            
    matches_found = []
    # Check each route pattern against the route string
    for route_name, pattern in route_patterns.items():
        if pattern.search(route_string):

            # Retrieve the corresponding Code for the matched route name
            code = DataConverter.sphn_route_codes.get(route_name, None)

            # Append the matched route and its Code to the list of matches found
            matches_found.append({
                "Route": route_name,
                "Code": code
            })
            logger.debug(" "*(indent+0) + f"Matched route: '{route_name}' and mapped it to SPHN route code: '{code}'")

    return matches_found    


# ---------------------------------------------------------------------------------------------------------------------
# # Functions for reading DICOM tags in the Legacy (single-frame) Contrast/Bolus module
# ---------------------------------------------------------------------------------------------------------------------

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
    contrast_bolus_agent_str = value.strip()

    # Check if value is not empty
    if len(contrast_bolus_agent_str) == 0:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAgent tag value contains only whitespace")
        return None

    assert is_valid_string(contrast_bolus_agent_str)

    return contrast_bolus_agent_str

#
# Edwin 2026-10-22
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
# Edwin 2026-10-29
#
def get_contrast_bolus_total_dose_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
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

    # Convert value to float
    try:
        contrast_bolus_total_dose = float(value)
    except (ValueError, TypeError):
        logger.warning(" "*(indent+0) + "DICOM ContrastBolusTotalDose tag value could not be converted to float")
        return None

    if contrast_bolus_total_dose < 0:
        logger.warning(" "*(indent+0) + f"DICOM ContrastBolusTotalDose: '{contrast_bolus_total_dose}' is probably not a valid value.")
        return None

    return contrast_bolus_total_dose


# ---------------------------------------------------------------------------------------------------------------------
# Functions for reading the "Enhanced Contrast/Bolus" module 
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-10-12
#
def process_enhanced_contrast_bolus_module_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> None:
    """
    Processes the DICOM Enhanced (multi-frame) Contrast/Bolus Module information 
    and stores contrast agent administration events in the data_store.
    Parameters:
        - dataset: The DICOM Dataset containing the Enhanced (multi-frame) Contrast/Bolus Module
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
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAgentSequence (coded info) not found in the dataset")
        return

    assert isinstance(contrast_bolus_agent_sequence, Sequence)

    logger.debug(" "*(indent+0) + f"DICOM ContrastBolusAgentSequence (coded info) found with {len(contrast_bolus_agent_sequence)} item(s)")

    #
    # 2. Process the items in the ContrastBolusAgentSequence (coded info)
    #

    # Process each item in the ContrastBolusAgentSequence
    for i, item in enumerate(contrast_bolus_agent_sequence):
        
        assert isinstance(item, Dataset)

        logger.debug(" "*(indent+2) + f"Processing item {i+1} of {len(contrast_bolus_agent_sequence)} in ContrastBolusAgentSequence")
        
        sphn_contrast_agent_administration_event = process_enhanced_contrast_bolus_agent_sequence_item(item, context, indent+4)

        # Store the collected SPHN contrast agent administration event in the data store
        if sphn_contrast_agent_administration_event is not None:
            data_store.add_sphn_contrast_agent_administration_event_to_list(
                sphn_contrast_agent_administration_event=sphn_contrast_agent_administration_event,
                logger=logger,
                indent=indent+4
            )
        else:
            logger.debug(" "*(indent+4) + "No SPHN Contrast Agent Administration Event object to store in the data store")


#
# Edwin 2026-11-07
#
def process_enhanced_contrast_bolus_agent_sequence_item(dataset:Dataset, context: Context, indent:int=0) -> SPHNContrastAgentAdministrationEvent|None:
    """
    Process the DICOM Enhanced (multi-frame) ContrastBolusAgentSequence item (Dataset) and return an SPHNContrastAgentAdministrationEvent object, if any.
    Parameters:
        - dataset: The DICOM Enhanced (multi-frame) ContrastBolusAgentSequence item (Dataset).
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger
    sphn_schema = context.sphn_schema

    sphn_contrast_agent_active_ingredient: SPHNContrastAgentActiveIngredient|None = None
    ingredient_list: list[SPHNContrastAgentActiveIngredient] = []
    sphn_contrast_agent: SPHNContrastAgent|None = None
    sphn_administration_route_code: SPHNCode|None = None
    sphn_flow_profile_interval_list: list[SPHNFlowProfileInterval] = []

    #
    # 1. Process the coding information in the dataset and create the SPHN Contrast Agent Active Ingredient object
    #

    sphn_contrast_agent_active_ingredient = process_coding_data_in_contrast_bolus_sequence_item(dataset, context, indent=indent+2)

    
    #
    # 2. Extract the Contrast/Bolus Ingredient Code Sequence from the DICOM sequence item (dataset)
    #    and create a list of SPHN Contrast Agent Active Ingredient objects
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

    #
    # 2.2. Process the ingredient concentration
    # 

    contrast_bolus_ingredient_concentration = get_contrast_bolus_ingredient_concentration_from_dicom(dataset, context, indent=indent+2)

    if contrast_bolus_ingredient_concentration is not None:

        assert isinstance(contrast_bolus_ingredient_concentration, float)

        logger.debug(" "*(indent+2) + f"ContrastBolusIngredientConcentration found: {contrast_bolus_ingredient_concentration} mg/ml")

        # Convert the concentration to a SPHNQuantity object
        sphn_code_mg_per_ml = SPHNCode( 
            sphn_schema = sphn_schema,
            has_identifier = "mgpermL",  # SPHN UCUM unit code, label: "mg/ml", comment: "milligrams per milliliter"
            has_coding_system_and_version = "UCUM"
        )
        sphn_unit_mg_per_ml = SPHNUnit(
            sphn_schema = sphn_schema,
            has_code = sphn_code_mg_per_ml
        )
        sphn_quantity_concentration = SPHNQuantity(
            sphn_schema = sphn_schema,
            has_value = contrast_bolus_ingredient_concentration,
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
            has_identifier = "percent",  # SPHN UCUM unit code, label: "%", comment: "percent"
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
    new_ingredient_list = None
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
        active_ingredient_list=new_ingredient_list,
        article=None,
        context=context,
        indent=indent+2
    )

    logger.debug(" "*(indent+2) + "Created an SPHN Contrast Agent object")

    #
    # 4. Check if there is a Contrast/Bolus Administration Route Sequence in the DICOM sequence item (dataset)
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

    sphn_quantity_total_diluted_volume = None

    volume = get_contrast_bolus_volume_from_dicom(dataset, context, indent=indent+2)

    if volume is not None:
        # Process the volume information here
        sphn_quantity_total_diluted_volume = create_sphn_quantity_for_volume(volume, context, indent=indent+2)

    if sphn_quantity_total_diluted_volume is not None:
        logger.debug(" "*(indent+2) + f"Successfully created SPHN Quantity for administered total diluted volume: '{volume}' ml.")
        # Assign the volume to the SPHN contrast agent object
        sphn_contrast_agent.has_quantity = sphn_quantity_total_diluted_volume
        logger.debug(" "*(indent+2) +"Added contrast/bolus total administered (diluted) volume to SPHN Contrast Agent object.")
    else:
        logger.debug(" "*(indent+2) +"Failed to create SPHN Quantity for administered total (diluted) volume.")

    #
    # 7. Extract the Contrast Administration Profile Sequence from the DICOM sequence item (dataset)
    #

    # Also record the earliest start and latest end times
    contrast_bolus_start_datetime = None
    contrast_bolus_end_datetime = None

    contrast_administration_profile_sequence = get_contrast_administration_profile_sequence_from_dicom(dataset, context, indent=indent+2)

    if contrast_administration_profile_sequence is not None:
        
        assert isinstance(contrast_administration_profile_sequence, Sequence)

        logger.debug(" "*(indent+0) + f"DICOM ContrastAdministrationProfileSequence (coded info) found with {len(contrast_administration_profile_sequence)} item(s)")

        #
        # 7.1. Process each item in the sequence
        #

        # Process each item in the ContrastAdministrationProfileSequence
        for i, item in enumerate(contrast_administration_profile_sequence):
            
            assert isinstance(item, Dataset)

            logger.debug(" "*(indent+2) + f"Processing item {i+1} of {len(contrast_administration_profile_sequence)} in ContrastAdministrationProfileSequence")
            
            sphn_flow_profile_interval = process_contrast_administration_profile_sequence_item(item, context, indent+4)

            if sphn_flow_profile_interval:

                # Add the SPHN Flow Profile Interval to the list, even duplicates
                sphn_flow_profile_interval_list.append(sphn_flow_profile_interval)

                # Update the earliest start and latest end times
                if sphn_flow_profile_interval.has_start_datetime and (contrast_bolus_start_datetime is None or sphn_flow_profile_interval.has_start_datetime < contrast_bolus_start_datetime):
                    contrast_bolus_start_datetime = sphn_flow_profile_interval.has_start_datetime
                if sphn_flow_profile_interval.has_end_datetime and (contrast_bolus_end_datetime is None or sphn_flow_profile_interval.has_end_datetime > contrast_bolus_end_datetime):
                    contrast_bolus_end_datetime = sphn_flow_profile_interval.has_end_datetime

            else:
                logger.debug(" "*(indent+2) + "Failed to process Profile from item")

    else:
        logger.debug(" "*(indent+0) + "DICOM ContrastAdministrationProfileSequence not found in the dataset")


    # 
    # 8. Determine the SPHNContrastAdministrationEvent start datetime
    #

    if contrast_bolus_start_datetime is None:
        logger.debug(" "*(indent+0) + "Contrast/bolus start datetime is not available, trying fallback datetimes.")
        
        # ToDo: Edwin: Search other hospital databases for contrast/bolus start time information.

        contrast_bolus_start_datetime = get_contrast_bolus_datetime_fallback(context=context, indent=indent+2)

        if contrast_bolus_start_datetime is not None:
            logger.debug(" "*(indent+0) + f"Using fallback contrast/bolus start datetime: {contrast_bolus_start_datetime!s}")
        else:
            logger.debug(" "*(indent+0) + "No fallback contrast/bolus start datetime available.")

    #
    # 9. Create the SPHN Contrast Agent Administration Event
    #

    sphn_contrast_agent_administration_event = create_sphn_contrast_agent_administration_event(
        sphn_contrast_agent=sphn_contrast_agent,
        sphn_administration_route_code=sphn_administration_route_code,
        start_datetime=contrast_bolus_start_datetime,
        end_datetime=contrast_bolus_end_datetime,
        sphn_flow_profile_interval_list=sphn_flow_profile_interval_list if len(sphn_flow_profile_interval_list) > 0 else None,
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
# Edwin 2026-11-07
#
def process_coding_data_in_contrast_bolus_sequence_item(dataset:Dataset, context: Context, indent:int=0) -> SPHNContrastAgentActiveIngredient|None:
    """
    Process only the coding info in the:
        - DICOM Contrast Bolus Agent Sequence item (Dataset) (both legacy and enhanced) or
        - DICOM Contrast Bolus Ingredient Code Sequence item (Dataset)  
    and return an SPHNContrastAgentActiveIngredient object
    Parameters:
        - dataset: The Sequence item (Dataset).
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger
    data_store = context.data_store

    sphn_contrast_agent_active_ingredient: SPHNContrastAgentActiveIngredient|None = None

    #
    # 1. Extract the coding scheme designator, code value, and code meaning from the DICOM sequence item (dataset)
    #

    logger.debug(" "*(indent+0) + "Starting to extract DICOM coding information: coding scheme designator, code value and description")

    coding_scheme_designator = get_coding_scheme_designator_from_dicom(dataset, context, indent=indent+2)
    code_value = get_code_value_from_dicom(dataset, context, indent=indent+2)
    code_descr = get_code_meaning_from_dicom(dataset, context, indent=indent+2)

    if coding_scheme_designator is None or code_value is None:
        logger.debug(" "*(indent+0) + "Failed to extract DICOM coding information: missing coding scheme designator or code value")
        data_store.add_unknown_contrast_bolus_agent_sequence_code_to_dict(coding_scheme_designator, code_value, code_descr)
        return None

    logger.debug(" "*(indent+0) + f"Successfully extracted DICOM coding scheme designator: '{coding_scheme_designator}', code value: '{code_value}' and description: '{code_descr}'")

    #
    # 2. Convert the DICOM coding information to a SPHN Contrast Agent Active Ingredient SNOMED-CT code
    #

    logger.debug(" "*(indent+0) + "Starting to map DICOM coding information to SPHN Contrast Agent Active Ingredient SNOMED-CT code")

    assert is_valid_string(coding_scheme_designator)
    assert is_valid_string(code_value)
    assert code_descr is None or is_valid_string(code_descr)

    sphn_contrast_agent_active_ingredient_snomed_code = mapping_dicom_coded_contrast_agent_2_sphn_contrast_agent_active_ingredient_snomed_code(
        coding_scheme_designator=coding_scheme_designator,
        code_value=code_value,
        code_descr=code_descr,
        context=context,
        indent=indent+2
    )

    if sphn_contrast_agent_active_ingredient_snomed_code is None:
        logger.debug(" "*(indent+0) + "Failed to map DICOM coding information to SPHN Contrast Agent Active Ingredient SNOMED-CT code")
        data_store.add_unknown_contrast_bolus_agent_sequence_code_to_dict(coding_scheme_designator, code_value, code_descr)
        return None

    assert isinstance(sphn_contrast_agent_active_ingredient_snomed_code, tuple) \
        and len(sphn_contrast_agent_active_ingredient_snomed_code) == 3 \
        and all(is_valid_string(item) for item in sphn_contrast_agent_active_ingredient_snomed_code)

    new_coding_scheme_designator, new_code_value, new_code_descr = sphn_contrast_agent_active_ingredient_snomed_code
    logger.debug(" "*(indent+0) + f"Successfully mapped the DICOM coding to SPHN SNOMED-CT code: '{(new_coding_scheme_designator, new_code_value, new_code_descr)}'")

    #
    # 2 Create the SPHN Contrast Agent Active Ingredient object
    #

    logger.debug(" "*(indent+0) + "Starting to create SPHN Contrast Agent Active Ingredient object")

    sphn_contrast_agent_active_ingredient = create_sphn_contrast_agent_active_ingredient(
        coding_scheme_designator=new_coding_scheme_designator,
        code_value=new_code_value,
        code_descr=new_code_descr,
        context=context,
        indent=indent+2
    )

    if sphn_contrast_agent_active_ingredient is None:
        logger.debug(" "*(indent+0) + "Failed to create an SPHN Contrast Agent Active Ingredient object")
        data_store.add_unknown_contrast_bolus_agent_sequence_code_to_dict(coding_scheme_designator, code_value, code_descr)
        return None

    logger.debug(" "*(indent+0) + "Successfully created an SPHN Contrast Agent Active Ingredient object")
    # Add the contrast bolus ingredient code to the data store dictionary for statistical purposes
    data_store.add_known_contrast_bolus_agent_sequence_code_to_dict(coding_scheme_designator, code_value, code_descr)

    return sphn_contrast_agent_active_ingredient


#
# Edwin 2026-11-07
#
def process_contrast_bolus_ingredient_code_sequence_item(dataset:Dataset, context: Context, indent:int=0) -> SPHNContrastAgentActiveIngredient|None:
    """
    Process the DICOM Enhanced (multi-frame) ContrastBolusIngredientCodeSequence item (Dataset) and return an SPHNContrastAgentActiveIngredient object, if any.
    Parameters:
        - dataset: The DICOM ContrastBolusIngredientCodeSequence item (Dataset).
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    sphn_contrast_agent_active_ingredient: SPHNContrastAgentActiveIngredient|None = None

    sphn_contrast_agent_active_ingredient = process_coding_data_in_contrast_bolus_sequence_item(dataset, context, indent=indent+2)

    # Contrast bolus ingredient code sequence item has no more items to process

    return sphn_contrast_agent_active_ingredient


#
# Edwin 2026-10-12
#
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
        data_store.add_unknown_contrast_bolus_administration_route_sequence_code_to_dict(coding_scheme_designator, code_value, code_descr)
        return None

    logger.debug(" "*(indent+4) + f"DICOM ContrastBolusAdministrationRouteSequence item has coding scheme designator '{coding_scheme_designator}' and code value '{code_value}' with description '{code_descr}'")

    # Try to convert the DICOM coding scheme designator and code value to a SPHN administration route SNOMED-CT code
    result = DataConverter.administration_routes_list.get((coding_scheme_designator, code_value), None)

    # Check if the route is known
    if result is None:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusAdministrationRouteSequence item could not be mapped to a known SPHN Administrative Route code")
        data_store.add_unknown_contrast_bolus_administration_route_sequence_code_to_dict(coding_scheme_designator, code_value, code_descr)
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

    logger.debug(" "*(indent+0) + f"Successfully mapped the DICOM coding: '{(coding_scheme_designator, code_value, code_descr)}' " + 
                f" to SPHN coding: '{result}' and created SPHN Code object"
                )

    return sphn_code_route

#
# Edwin 2026-10-16
#
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
                acquisition_datetime=data_store.acquisition_start_datetime, 
                series_datetime=data_store.series_start_datetime,
                study_datetime=data_store.study_start_datetime,
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
                acquisition_datetime=data_store.acquisition_start_datetime, 
                series_datetime=data_store.series_start_datetime,
                study_datetime=data_store.study_start_datetime,
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
        sphn_quantity_volume = create_sphn_quantity_for_volume(volume, context, indent=indent+2)

    if sphn_quantity_volume is not None:
        logger.debug(" "*(indent+0) +f"Determined contrast/bolus volume: {volume} ml")
    else:
        logger.debug(" "*(indent+0) +"Failed to determine contrast/bolus volume.")

    #
    #  4. Process the flow rate, if available.
    #

    sphn_quantity_flow_rate = None

    flow_rate_list = get_contrast_flow_rate_from_dicom(dataset, context, indent=indent+2)

    # The Enhanced Contrast/Bolus module allows only one value
    if flow_rate_list is not None \
        and len(flow_rate_list) == 1 \
        and flow_rate_list[0] is not None:

        flow_rate = flow_rate_list[0]
        sphn_quantity_flow_rate = create_sphn_quantity_for_flow_rate(flow_rate, context, indent=indent+2)

    if sphn_quantity_flow_rate is not None:
        logger.debug(" "*(indent+0) +f"Successfully created SPHN Quantity for contrast/bolus flow rate: {flow_rate} ml/s")
    else:
        logger.debug(" "*(indent+0) +"Failed to determine contrast/bolus flow rate.")

    #
    #  5. Process the flow duration, if available.
    #

    sphn_quantity_flow_duration = None

    flow_duration_list = get_contrast_flow_duration_from_dicom(dataset, context, indent=indent+2)

    # The Enhanced Contrast/Bolus module allows only one value
    if flow_duration_list is not None \
        and len(flow_duration_list) == 1 \
        and flow_duration_list[0] is not None:

        flow_duration = flow_duration_list[0]
        sphn_quantity_flow_duration = create_sphn_quantity_for_flow_duration(flow_duration, context, indent=indent+2)

    if sphn_quantity_flow_duration is not None:
        logger.debug(" "*(indent+0) +f"Successfully created SPHN Quantity for contrast/bolus flow duration: {flow_duration} s")
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
        logger.debug(" "*(indent+0) +"Successfully created SPHN Flow Profile Interval object.")
    else:
        logger.debug(" "*(indent+0) +"Failed to create SPHN Flow Profile Interval object.")

    return sphn_flow_profile_interval


# ---------------------------------------------------------------------------------------------------------------------
# Functions for Mapping
# ---------------------------------------------------------------------------------------------------------------------

def mapping_dicom_coded_contrast_agent_2_sphn_contrast_agent_active_ingredient_snomed_code(
        coding_scheme_designator: str,
        code_value: str,
        code_descr: str|None,
        context: Context,
        indent: int=0
    ) -> tuple[str, str, str]|None:
    """
    Converts the given DICOM coding scheme designator and code value to the corresponding SPHN SNOMED-CT code if available.
    Parameters:
        - coding_scheme_designator: The coding scheme designator for the contrast agent component, as listed in DICOM
        - code_value: The code value for the contrast agent component, as listed in DICOM
        - code_descr: The code description for the contrast agent component, as listed in DICOM
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    Returns:
        - A tuple with the SPHN SNOMED-CT coding scheme designator, code value and code meaning if available, otherwise None
    """

    assert is_valid_string(coding_scheme_designator)
    assert is_valid_string(code_value)
    assert code_descr is None or is_valid_string(code_descr)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Check if it is a known DICOM contrast agent code as listed in DICOM Table CID 12
    # Link: https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_12.html
    result = DataConverter.dicom_contrast_agents_coded_2_sphn_snomed_coded.get((coding_scheme_designator.upper(), code_value), None)

    if result is None:
        logger.warning(" "*(indent+0) + f"Failed to map the DICOM coding : '{(coding_scheme_designator, code_value, code_descr)}' to SPHN SNOMED-CT code")
        return

    assert isinstance(result, tuple) and len(result) == 3
    assert all(is_valid_string(item) for item in result)
    
    return result


# ---------------------------------------------------------------------------------------------------------------------
# Functions for Creating
# ---------------------------------------------------------------------------------------------------------------------


#
# Edwin 2026-10-12
#
def create_sphn_contrast_agent_active_ingredient(
        coding_scheme_designator: str, 
        code_value: str, 
        code_descr: str|None, 
        context: Context, 
        indent: int=0
    ) -> SPHNContrastAgentActiveIngredient:
    """
    Creates a SPHN Contrast Agent Active Ingredient object. The given DICOM coding scheme designator and code value 
    are converted to the corresponding SPHN SNOMED-CT code if available.
    Parameters:
        - coding_scheme_designator: The coding scheme designator for the contrast agent component, as listed in DICOM
        - code_value: The code value for the contrast agent component, as listed in DICOM
        - code_descr: The code description for the contrast agent component, as listed in DICOM
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

    # Check
    assert is_valid_string(coding_scheme_designator)
    assert is_valid_string(code_value)
    assert code_descr is None or is_valid_string(code_descr)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    data_store = context.data_store
    sphn_schema = context.sphn_schema

    sphn_code = SPHNCode( 
        sphn_schema = sphn_schema,
        has_coding_system_and_version = coding_scheme_designator,
        has_identifier = code_value,
        has_name = code_descr
        )
    sphn_contrast_agent_active_ingredient = SPHNContrastAgentActiveIngredient(
        sphn_schema = sphn_schema,
        has_code = sphn_code,
        has_source_system_list = [data_store.sphn_source_system]
        )

    return sphn_contrast_agent_active_ingredient


#
# Edwin 2026-10-12
#
def create_sphn_contrast_agent(
        active_ingredient_list:list[SPHNContrastAgentActiveIngredient]|None,
        article: SPHNDrugArticle|None,
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

    assert active_ingredient_list is None \
        or (isinstance(active_ingredient_list, list) \
            and all(isinstance(i, SPHNContrastAgentActiveIngredient) for i in active_ingredient_list))
    assert article is None or isinstance(article, SPHNDrugArticle)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    data_store = context.data_store
    sphn_schema = context.sphn_schema

    sphn_contrast_agent = SPHNContrastAgent(
        sphn_schema = sphn_schema,
        has_active_ingredient_list=active_ingredient_list if active_ingredient_list else None,
        has_article = article,
        has_source_system_list=[data_store.sphn_source_system]
    )

    return sphn_contrast_agent


#
# Edwin 2026-10-12
#
def create_sphn_contrast_agent_administration_event(
        sphn_contrast_agent:SPHNContrastAgent,
        sphn_administration_route_code:SPHNCode|None,
        start_datetime:datetime,
        end_datetime:datetime|None,
        sphn_flow_profile_interval_list: list[SPHNFlowProfileInterval]|None,
        context: Context,
        indent:int=0
    ) -> SPHNContrastAgentAdministrationEvent:
    """
    Creates an SPHN Contrast Agent Administration Event object with the provided information.
    Parameters:
        - sphn_contrast_agent: SPHN Contrast Agent object.
        - sphn_administration_route_code: The SPHN administration route code.
        - start_datetime: The start date and time of the administration event.
        - end_datetime: The end date and time of the administration event (optional).
        - sphn_flow_profile_interval_list: List of SPHN Flow Profile Interval objects (optional).
        - context: The Context object that holds the data_store, logger and other relevant information
        - indent: The indentation level for logging (default is 0)
    """

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
    sphn_schema = context.sphn_schema

    logger.debug(" "*(indent+0) + "Start creating an SPHN Contrast Agent Administration Event object...")

    sphn_contrast_agent_administration_event = SPHNContrastAgentAdministrationEvent(
        sphn_schema = sphn_schema,
        has_start_datetime=start_datetime,
        has_end_datetime=end_datetime,
        has_drug=sphn_contrast_agent,
        has_administration_route_code=sphn_administration_route_code,
        has_subject_pseudo_identifier = data_store.sphn_subject_pseudo_identifier,
        has_source_system_list = [data_store.sphn_source_system],
        has_flow_profile_interval_list=sphn_flow_profile_interval_list
    )

    logger.debug(" "*(indent+0) + "Done  creating SPHN Contrast Agent Administration Event object.")

    return sphn_contrast_agent_administration_event


#
# Edwin 2026-10-16
#
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
        has_identifier = "mL",  # SPHN UCUM unit code, label: "mL", comment: "milliliters"
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
#
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
        has_identifier = "mLpers",  # SPHN UCUM unit code, label: "mL/s", comment: "milliliter per second"
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
#
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
        has_identifier = "s",  # SPHN UCUM unit code, label: "s", comment: "second"
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
# Functions for reading DICOM tags in the Enhanced (Multi-frame) Contrast/Bolus module
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
#
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
#
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
#
def get_contrast_bolus_ingredient_concentration_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> float|None:
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

    # Convert the value to a float
    try:
        contrast_bolus_ingredient_concentration = float(value)
    except (ValueError, TypeError):
        logger.debug(" "*(indent+0) + f"DICOM ContrastBolusIngredientConcentration: '{value}' could not be converted to float.")
        return None
    
    if contrast_bolus_ingredient_concentration < 0:
        logger.warning(" "*(indent+0) + f"DICOM ContrastBolusIngredientConcentration: '{contrast_bolus_ingredient_concentration}' is not a valid value.")
        return None

    return contrast_bolus_ingredient_concentration


#
# Edwin 2026-10-12
#
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
#
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
#
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
# Edwin 2026-10-28
#
def get_contrast_flow_rate_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> list[float|None]|None:
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

    # Note: Only a single value allowed for the Enhanced Contrast/Bolus Module

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

    # It could be a multi-valued tag, a list with DSfloat or DSdecimal
    elif isinstance(value, MultiValue):

        for value_item in value:
            if isinstance(value_item, (DSfloat, DSdecimal)):
                # Convert value_item to float
                try:
                    value_item_float = float(value_item)
                except (ValueError, TypeError):
                    logger.warning(" "*(indent+0) + "DICOM ContrastFlowRate tag value-item could not be converted to float")
                    value_item_float = None

                # Add value_item to the list
                contrast_flow_rate_float_list.append(value_item_float)

            elif isinstance(value_item, float):
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

        # Convert value to float
        try:
            value_float = float(value)
        except (ValueError, TypeError):
            logger.warning(" "*(indent+0) + "DICOM ContrastFlowRate tag value could not be converted to float")
            value_float = None

        # Add value to the list
        contrast_flow_rate_float_list.append(value_float)

    elif isinstance(value, float):
        contrast_flow_rate_float_list.append(value)

    # Warning otherwise
    else:
        logger.warning(" "*(indent+0) + "DICOM ContrastFlowRate tag value has an unknown format")
        return None

    # Check for negative values in the contrast flow rate list
    if any(contrast_flow_rate_float is not None and contrast_flow_rate_float < 0 for contrast_flow_rate_float in contrast_flow_rate_float_list):
        logger.warning(" "*(indent+0) + "DICOM ContrastFlowRate tag contains negative values")
        return None

    return contrast_flow_rate_float_list if len(contrast_flow_rate_float_list)>0 else None


#
# Edwin 2026-10-28
#
def get_contrast_flow_duration_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> list[float|None]|None:
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

    # Note: Only a single value allowed for the Enhanced Contrast/Bolus Module

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
                # Convert value_item to float
                try:
                    value_item_float = float(value_item)
                except (ValueError, TypeError):
                    logger.warning(" "*(indent+0) + "DICOM ContrastFlowDuration tag value-item could not be converted to float")
                    value_item_float = None

                # Add value_item_float to the list
                contrast_flow_duration_float_list.append(value_item_float)

            elif isinstance(value_item, float):
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

        # Convert value to float
        try:
            value_float = float(value)
        except (ValueError, TypeError):
            logger.warning(" "*(indent+0) + "DICOM ContrastFlowDuration tag value could not be converted to float")
            value_float = None

        # Add value to the list
        contrast_flow_duration_float_list.append(value_float)

    elif isinstance(value, float):
        contrast_flow_duration_float_list.append(value)

    # Warning otherwise
    else:
        logger.warning(" "*(indent+0) + "DICOM ContrastFlowDuration tag value has an unknown format")
        return None

    # Check for negative values in the contrast flow duration list
    if any(contrast_flow_duration_float is not None and contrast_flow_duration_float < 0 for contrast_flow_duration_float in contrast_flow_duration_float_list):
        logger.warning(" "*(indent+0) + "DICOM ContrastFlowDuration tag contains negative values")
        return None

    return contrast_flow_duration_float_list if len(contrast_flow_duration_float_list)>0 else None


#
# Edwin 2026-10-15
#
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

    # Convert a possible DICOM TM object to a string representation and remove leading/trailing whitespace
    contrast_bolus_start_time = str(value).strip()

    # Check if value is not empty
    if len(contrast_bolus_start_time) == 0:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusStartTime tag value contains only whitespace")
        return None

    assert is_valid_string(contrast_bolus_start_time)

    return contrast_bolus_start_time


#
# Edwin 2026-10-15
#
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

    # Convert a possible DICOM TM object to a string representation and remove leading/trailing whitespace
    contrast_bolus_stop_time = str(value).strip()

    # Check if value is not empty
    if len(contrast_bolus_stop_time) == 0:
        logger.debug(" "*(indent+0) + "DICOM ContrastBolusStopTime tag value contains only whitespace")
        return None

    assert is_valid_string(contrast_bolus_stop_time)

    return contrast_bolus_stop_time

# ---------------------------------------------------------------------------------------------------------------------
# Not yet used functions
# ---------------------------------------------------------------------------------------------------------------------

#
# Edwin 2026-10-12
# Not Used
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
        logger.debug(" "*(indent+0) + f"DICOM ContrastBolusIngredientOpaque: '{contrast_bolus_ingredient_opaque}' is not a valid value.")
        return None

    return contrast_bolus_ingredient_opaque


#
# Edwin 2026-10-12
# Not Used
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
        logger.debug(" "*(indent+0) + f"DICOM ContrastBolusT1Relaxivity: '{contrast_bolus_t1_relaxivity}' is probably not a valid value.")
        return None

    return contrast_bolus_t1_relaxivity


#
# Edwin 2026-10-09
# Not Used
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
#
def get_contrast_bolus_datetime(
        contrast_bolus_time: time, 
        acquisition_datetime: datetime|None, 
        series_datetime: datetime|None,
        study_datetime: datetime|None,
        context: Context, 
        indent: int=0
    ) -> datetime|None:
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
        datetime|None: The estimated datetime of the contrast/bolus, adjusted for potential midnight boundary crossings. Returns None if insufficient information is provided.

    Note: At least one of acquisition_datetime, series_datetime, or study_datetime must be provided.
    """
    assert isinstance(contrast_bolus_time, time)
    assert acquisition_datetime is None or isinstance(acquisition_datetime, datetime)
    assert series_datetime is None or isinstance(series_datetime, datetime)
    assert study_datetime is None or isinstance(study_datetime, datetime)
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    logger = context.logger

    # 1. Validate input parameters and ensure at least one datetime is provided
    if acquisition_datetime is None and series_datetime is None and study_datetime is None:
        logger.warning(" "*(indent+0) + "At least one of acquisition_datetime, series_datetime, or study_datetime must be provided.")
        return None
    
    # 2. Safely retrieve required tags with logical fallbacks
    acq_date = acquisition_datetime.strftime("%Y%m%d") if acquisition_datetime else series_datetime.strftime("%Y%m%d") if series_datetime else study_datetime.strftime("%Y%m%d")
    acq_time = acquisition_datetime.strftime("%H%M%S") if acquisition_datetime else series_datetime.strftime("%H%M%S") if series_datetime else study_datetime.strftime("%H%M%S")
    contrast_time = contrast_bolus_time.strftime("%H%M%S")
    
    if not all([acq_date, acq_time, contrast_time]):
        logger.warning(" "*(indent+0) + "Required date/time values are missing.")
        return None
    
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


#
# Edwin 2026-11-08
#
def get_contrast_bolus_datetime_fallback(context: Context, indent: int=0) -> datetime|None:
    """
    Tries to determine a fallback datetime for the contrast/bolus, based on available: Series, Acquisition, Study, 
    or Provided fallback contrast agent datetimes.
    Parameters:
        context (Context): The context object containing logger and other information.
        indent (int): The indentation level for logging.

    Returns:
        datetime|None: The fallback datetime for the contrast/bolus start, or None if unavailable.
    """
    assert isinstance(context, Context)
    assert isinstance(indent, int) and indent >= 0

    data_store = context.data_store
    logger = context.logger

    contrast_bolus_start_datetime = None

    if data_store.series_start_datetime is not None:
        contrast_bolus_start_datetime = data_store.series_start_datetime
        logger.debug(" "*(indent+2) + f"Using DICOM Series start datetime as fallback: {contrast_bolus_start_datetime!s}")
    
    elif data_store.acquisition_start_datetime is not None:
        contrast_bolus_start_datetime = data_store.acquisition_start_datetime
        logger.debug(" "*(indent+2) + f"Using DICOM Acquisition start datetime as fallback: {contrast_bolus_start_datetime!s}")
    
    elif data_store.study_start_datetime is not None:
        contrast_bolus_start_datetime = data_store.study_start_datetime
        logger.debug(" "*(indent+2) + f"Using DICOM Study start datetime as fallback: {contrast_bolus_start_datetime!s}")
    
    elif data_store.fallback_contrast_agent_datetime is not None:
        contrast_bolus_start_datetime = data_store.fallback_contrast_agent_datetime
        logger.debug(" "*(indent+2) + f"Using fallback contrast agent datetime as fallback: {contrast_bolus_start_datetime!s}")
    
    else:
        logger.debug(" "*(indent+2) + "No fallback datetime available for contrast/bolus start.")

    return contrast_bolus_start_datetime
