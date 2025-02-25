import streamlit as st
from google import genai
from google.genai import types
from dotenv import dotenv_values
import PIL.Image
import re
import os
import json
from datetime import datetime

class PrescriptionParser:
    def __init__(self):
        """Initializes the prescription parser."""
        self.api_key = dotenv_values(".env").get("key")
        self.client = genai.Client(api_key=self.api_key)
        self.extracted_data = None

    @staticmethod
    def load_image(image_file):
        """Loads and converts the uploaded image to RGB format."""
        img = PIL.Image.open(image_file)
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

    def extract_text(self, image):
        """
        Extracts structured information from the prescription image using the Gemini API.
        """
        image = self.load_image(image)

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
        """
        if not self.extracted_data:
            st.error("Error: No extracted data available.")
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
                st.error("Error: Extracted text is not valid JSON.")
                return None
        else:
            st.error("Error: No JSON found in response.")
            return None

    def process_prescription(self, image):
        """
        Executes the full pipeline: extract text, parse JSON, and return structured data.
        """
        self.extract_text(image)              
        structured_data = self.parse_json()   

        if structured_data:
            return structured_data
        else:
            return None

# -------------------- STREAMLIT UI --------------------

st.set_page_config(page_title="Prescription AI", layout="centered")
st.title("AI-Powered Prescription Parser")

# File uploader
uploaded_file = st.file_uploader("Upload Prescription Image", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Display the uploaded image
    st.image(uploaded_file, caption="Uploaded Prescription", use_column_width=True)

    # Process prescription
    parser = PrescriptionParser()
    with st.spinner("Extracting prescription details... Please wait."):
        extracted_data = parser.process_prescription(uploaded_file)

    if extracted_data:
        st.subheader("📄 Extracted Prescription Details")
        st.json(extracted_data)

        # Convert extracted data to JSON format for download
        json_str = json.dumps(extracted_data, indent=4)
        st.download_button(
            label="Download JSON",
            data=json_str,
            file_name="prescription_details.json",
            mime="application/json"
        )