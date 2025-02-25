from google import genai
from google.genai import types
from dotenv import dotenv_values
import PIL.Image
import re
import json
from datetime import datetime

def calculate_age(dob_str, prescription_date_str):
    """
    Calculate age based on date of birth (DOB) and prescription date.
    
    :param dob_str: Patient's date of birth in 'YYYY-MM-DD' format
    :param prescription_date_str: Prescription date in 'DD-MM-YYYY' format
    :return: Patient's age as an integer
    """
    try:
        # Convert strings to datetime objects
        dob = datetime.strptime(dob_str, "%Y-%m-%d")
        prescription_date = datetime.strptime(prescription_date_str, "%d-%m-%Y")
        
        # Calculate age
        age = prescription_date.year - dob.year - ((prescription_date.month, prescription_date.day) < (dob.month, dob.day))
        return age
    except ValueError:
        return None  # If parsing fails, return None


# Load API Key
key = dotenv_values(".env")['key']

# Open Prescription Image
image = PIL.Image.open('prescription.jpg')

# Initialize Gemini API Client
client = genai.Client(api_key=key)

# Extract Text from Image
sys_instruct = """You are assisting a pharmacy in extracting structured information from handwritten or printed prescriptions.",
    "Analyze the provided image and accurately extract key details, including the patient’s full name, age, and the date of the prescription." 
    "Identify the prescribing doctor’s name and license number if available." 
    "Extract all medication details, including the drug name, dosage (such as 500mg or 10ml), frequency (such as once daily or twice a day), and duration (such as 7 days or 2 weeks)." 
    "Additionally, capture any relevant notes, such as special instructions like ‘Take after meals,’ refill status if mentioned, and any allergy warnings." 
    "Ensure the extracted details are presented in a structured JSON format." 
    "Maintain accuracy in parsing the text, preserving medical terminology, and ensuring the structured data is complete and reliable for pharmacy use."
    "If something is not defined, leave that field blank, don't make assumptions."
    "The JSON format should be:

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
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=["Extract structured details from this prescription and return only JSON", image],
    config=types.GenerateContentConfig(system_instruction=sys_instruct),
)

extracted_text = response.text
print("Extracted Text:\n", extracted_text)

json_match = re.search(r"\{.*\}", extracted_text, re.DOTALL)
if json_match:
    extracted_json = json_match.group(0)
    try:
        structured_data = json.loads(extracted_json)
        
        # Calculate and update patient's age if DOB is present
        if structured_data.get("patient_dob") and structured_data.get("date"):
            structured_data["patient_age"] = calculate_age(structured_data["patient_dob"], structured_data["date"])

        structured_json = json.dumps(structured_data, indent=4)
        print("Structured Order:\n", json.dumps(structured_data, indent=4))
    except json.JSONDecodeError:
        print("Error: Extracted text is not valid JSON.")
else:
    print("Error: No JSON found in response.")
