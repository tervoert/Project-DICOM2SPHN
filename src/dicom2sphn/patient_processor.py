"""
patient_processor.py:
    Part of the example dicom2sphn package.
    It starts the processing of patient data.
"""
from .tools import is_valid_string
from .context import Context

class PatientProcessor:

    context: Context
    patient_id: str

    def __init__(self, context, patient_id):
        """ 
        Initializes the instance
        """

        self.context = context
        self.patient_id = patient_id

    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    def process(self) -> None:
        """
        Processes the patient data
        """
        print("Processing")

    def save_to_json_file(self) -> None:
        """
        Saves the patient data to a JSON file
        """
        print("Saving to JSON file")
