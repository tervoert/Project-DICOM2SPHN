"""
dicom_code_sequence_tags_reader.py:
    Part of the example dicom2sphn package.
    It contains functions for reading DICOM code sequence like tags.
"""

from pydicom import Dataset

from .context import Context
from .tools import is_valid_string


#
#  Edwin 2026-08-31
#
def get_code_value_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM CodeValue tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Tag:                  (0008,0100)
    # Type:	                Conditionally Required (1C)
    # Keyword:	            CodeValue
    # Value Multiplicity	1
    # Value Representation:	Short String (SH)
    
    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM CodeValue tag
    value = dataset.get("CodeValue", None)

    # Check if the value is None
    if value is None:
        logger.debug(" "*(indent+0) + "DICOM CodeValue tag was not found")  
        return None

    assert isinstance(value, str)

    # Remove whitespace
    code_value = value.strip()

    # Check if value is not empty
    if len(code_value) == 0:
        logger.debug(" "*(indent+0) + "DICOM CodeValue tag value contains only whitespace")
        return None

    assert is_valid_string(code_value)

    return code_value


#
#  Edwin 2026-08-31
#
def get_coding_scheme_designator_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM Coding Scheme Designator tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Tag:                  (0008,0102)
    # Type:	                Conditionally Required (1C)
    # Keyword:	            CodingSchemeDesignator
    # Value Multiplicity	1
    # Value Representation:	Short String (SH)
    
    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM CodingSchemeDesignator tag
    value = dataset.get("CodingSchemeDesignator", None)

    # Check if the value is None
    if value is None:
        logger.debug(" "*(indent+0) + "DICOM Coding Scheme Designator tag was not found")  
        return None

    assert isinstance(value, str)

    # Remove whitespace
    coding_scheme_designator = value.strip()

    # Check if value is not empty
    if len(coding_scheme_designator) == 0:
        logger.debug(" "*(indent+0) + "DICOM Coding Scheme Designator tag value contains only whitespace")
        return None

    assert is_valid_string(coding_scheme_designator)

    return coding_scheme_designator


#
#  Edwin 2026-08-31
#
def get_coding_scheme_version_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM Coding Scheme Version tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Tag:                  (0008,0103)
    # Type:	                Conditionally Required (1C)
    # Keyword:	            CodingSchemeVersion
    # Value Multiplicity	1
    # Value Representation:	Short String (SH)
    
    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM CodingSchemeVersion tag
    value = dataset.get("CodingSchemeVersion", None)

    # Check if the value is None
    if value is None:
        logger.debug(" "*(indent+0) + "DICOM Coding Scheme Version tag was not found")  
        return None

    assert isinstance(value, str)

    # Remove whitespace
    coding_scheme_version = value.strip()

    # Check if value is not empty
    if len(coding_scheme_version) == 0:
        logger.debug(" "*(indent+0) + "DICOM Coding Scheme Version tag value contains only whitespace")
        return None

    assert is_valid_string(coding_scheme_version)

    return coding_scheme_version


#
#  Edwin 2026-08-31
#
def get_code_meaning_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM Code Meaning tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Tag:                  (0008,0104)
    # Type:	                Required (1)
    # Keyword:	            CodeMeaning
    # Value Multiplicity	1
    # Value Representation:	Long String (LO)
    
    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM CodeMeaning tag
    value = dataset.get("CodeMeaning", None)

    # Check if the value is None
    if value is None:
        logger.debug(" "*(indent+0) + "DICOM Code Meaning tag was not found")  
        return None

    assert isinstance(value, str)

    # Remove whitespace
    code_meaning = value.strip()

    # Check if value is not empty
    if len(code_meaning) == 0:
        logger.debug(" "*(indent+0) + "DICOM Code Meaning tag value contains only whitespace")
        return None

    assert is_valid_string(code_meaning)

    return code_meaning


#
#  Edwin 2026-08-31
#
def get_long_code_value_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM LongCodeValue tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Tag:                  (0008,0119)
    # Type:	                Conditionally Required (1C)
    # Keyword:	            LongCodeValue
    # Value Multiplicity	1
    # Value Representation:	Unlimited Characters (UC)
    
    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM LongCodeValue tag
    value = dataset.get("LongCodeValue", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM Long Code Value tag was not found")  
        return None

    assert isinstance(value, str)

    # Remove whitespace
    long_code_value = value.strip()

    # Check if value is not empty
    if len(long_code_value) == 0:
        logger.debug(" "*(indent+0) + "DICOM Long Code Value tag value contains only whitespace")
        return None

    assert is_valid_string(long_code_value)

    return long_code_value


#
#  Edwin 2026-08-31
#
def get_urn_code_value_from_dicom(dataset: Dataset, context: Context, indent: int=0) -> str|None:
    """
    Returns the string corresponding to the value of the DICOM URNCodeValue tag
        - dataset is the DICOM Dataset (DICOM header) that contains DICOM DataElements (tags)
    """

    # Tag:                  (0008,0120)
    # Type:	                Conditionally Required (1C)
    # Keyword:	            URNCodeValue
    # Value Multiplicity	1
    # Value Representation:	URL (UR) 
    
    # Check
    assert isinstance(dataset, Dataset)
    assert isinstance(context, Context)
    assert isinstance(indent,int) and indent>=0

    logger = context.logger

    # Get the value of the DICOM URNCodeValue tag
    value = dataset.get("URNCodeValue", None)

    if value is None:
        logger.debug(" "*(indent+0) + "DICOM URN Code Value tag was not found")  
        return None

    assert isinstance(value, str)

    # Remove whitespace
    urn_code_value = value.strip()

    # Check if value is not empty
    if len(urn_code_value) == 0:
        logger.debug(" "*(indent+0) + "DICOM URN Code Value tag value contains only whitespace")
        return None

    assert is_valid_string(urn_code_value)

    return urn_code_value
