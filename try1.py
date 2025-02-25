from google import genai
from google.genai import types
from dotenv import dotenv_values
import PIL.Image
import re
import os
import json
from datetime import datetime

class PrescriptionParser:
    def __init__(self, image_path: str, output_file: str = "prescription_output.txt"):
        """
        Initializes the prescription parser with an image path.

        :param image_path: Path to the prescription image.
        :param output_file: File to save the extracted structured data.
        """
        self.image_path = image_path
        self.output_file = output_file
        self.api_key = dotenv_values(".env").get("key")
        self.client = genai.Client(api_key=self.api_key)
        self.extracted_data = None

    def load_image(self):
        """Loads and converts image to RGB if necessary."""
        img = PIL.Image.open(self.image_path)
        if img.mode in ("P", "RGBA", "LA"):
            img = img.convert("RGB")
        return img

    @staticmethod
    def calculate_age(dob_str: str, prescription_date_str: str) -> int:
        """
        Calculate age based on date of birth (DOB) and prescription date.

        :param dob_str: Patient's date of birth in 'YYYY-MM-DD' format
        :param prescription_date_str: Prescription date in 'DD-MM-YYYY' format
        :return: Patient's age as an integer
        """
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
            prescription_date = datetime.strptime(prescription_date_str, "%d-%m-%Y")
            age = prescription_date.year - dob.year - (
                (prescription_date.month, prescription_date.day) < (dob.month, dob.day)
            )
            return age
        except ValueError:
            return None  

    def extract_text(self):
        """
        Extracts structured information from the prescription image using the Gemini API.
        """
        image = self.load_image()

        # Define system instructions for text extraction
        sys_instruct = """You are assisting a pharmacy in extracting structured information from handwritten or printed prescriptions.
        Analyze the provided image and accurately extract key details, including the patient’s full name, age, and the date of the prescription.
        Identify the prescribing doctor’s name and license number if available.
        Extract all medication details, including the drug name, dosage (such as 500mg or 10ml), frequency (such as once daily or twice a day), and duration (such as 7 days or 2 weeks).
        Additionally, capture any relevant notes, such as special instructions like ‘Take after meals,’ refill status if mentioned, and any allergy warnings.
        Ensure the extracted details are presented in a structured JSON format.
        Maintain accuracy in parsing the text, preserving medical terminology, and ensuring the structured data is complete and reliable for pharmacy use.
        If something is not defined, leave that field blank, don't make assumptions.
        
        The JSON format should be:
        {
            "patient_name": "John Doe",
            "patient_age": null,
            "date": "DD-MM-YYYY",
            "doctor_name": "Dr. Jane Smith",
            "doctor_license": "12345",
            "medications": [
                {
                    "drug_name": "Amoxicillin",
                    "dosage": "500 mg",
                    "frequency": "Twice daily",
                    "duration": "7 days",
                    "notes": "Take after meals"
                }
            ],
            "refills": "1",
            "allergies": "Penicillin",
            "patient_dob": "1990-05-10",
            "patient_weight": "70 kg"
        }

        Return **only** this JSON object."""

        # Call the Gemini API
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=["Extract structured details from this prescription and return only JSON", image],
            config=types.GenerateContentConfig(system_instruction=sys_instruct),
        )

        # Store extracted text
        self.extracted_data = response.text

    def parse_json(self):
        """
        Parses the extracted text into a structured JSON format.

        :return: Structured prescription data as a dictionary.
        """
        if not self.extracted_data:
            print("Error: No extracted data available.")
            return None

        json_match = re.search(r"\{.*\}", self.extracted_data, re.DOTALL)
        if json_match:
            extracted_json = json_match.group(0)
            try:
                structured_data = json.loads(extracted_json)

                # Calculate and update patient's age if DOB is present
                if structured_data.get("patient_dob") and structured_data.get("date"):
                    structured_data["patient_age"] = self.calculate_age(
                        structured_data["patient_dob"], structured_data["date"]
                    )

                return structured_data  

            except json.JSONDecodeError:
                print("Error: Extracted text is not valid JSON.")
                return None
        else:
            print("Error: No JSON found in response.")
            return None

    def process_prescription(self):
        """
        Executes the full pipeline: extract text, parse JSON, and return structured data.

        :return: Structured prescription data as JSON.
        """
        self.extract_text()                     # Extract text from image
        structured_data = self.parse_json()     # Parse extracted text into JSON

        if structured_data:
            structured_json = json.dumps(structured_data, indent=4)
            with open(self.output_file, "w") as file:
                file.write(structured_json)

            print("Structured Order:\n", structured_json)  # Print final structured JSON
            return structured_json
        else:
            print("Error: Failed to process prescription.")
            return None


# -------------------- EXECUTION --------------------

if __name__ == "__main__":
    parser = PrescriptionParser("prescription.jpg")
    parser.process_prescription()