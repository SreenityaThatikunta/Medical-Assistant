from google import genai
from google.genai import types
from dotenv import dotenv_values
import PIL.Image
import re
import json

# Load API Key
key = dotenv_values(".env")['key']

# Open Prescription Image
image = PIL.Image.open('prescription.jpg')

# Initialize Gemini API Client
client = genai.Client(api_key=key)

# Extract Text from Image
sys_instruct = (
    "You are assisting a pharmacy in extracting structured information from handwritten or printed prescriptions.",
    "Analyze the provided image and accurately extract key details, including the patient’s full name, age, and the date of the prescription." 
    "Identify the prescribing doctor’s name and license number if available." 
    "Extract all medication details, including the drug name, dosage (such as 500mg or 10ml), frequency (such as once daily or twice a day), and duration (such as 7 days or 2 weeks)." 
    "Additionally, capture any relevant notes, such as special instructions like ‘Take after meals,’ refill status if mentioned, and any allergy warnings." 
    "Ensure the extracted details are presented in a structured JSON format, focusing only on relevant prescription information while ignoring unrelated text." 
    "Maintain accuracy in parsing the text, preserving medical terminology, and ensuring the structured data is complete and reliable for pharmacy use."
    "If something is not defined, leave that field blank, don't make assumptions."
    )
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=["Extract structured details from this prescription and return only JSON", image],
    config=types.GenerateContentConfig(system_instruction=sys_instruct),
)

extracted_text = response.text
print("Extracted Text:\n", extracted_text)

# Function to Parse Patient Information
def parse_prescription(text):
    patient_info = {
        "Patient Name": None,
        "Age": None,
        "Date": None,
        "Doctor Name": None,
        "License Number": None,
        "Medications": [],
        "Additional Notes": None  # New field for special instructions
    }

    # Extract Patient Name (Assuming "Name: XYZ" pattern)
    name_match = re.search(r"Name[:\s]+([\w\s]+)", text)
    if name_match:
        patient_info["Patient Name"] = name_match.group(1).strip()

    # Extract Age
    age_match = re.search(r"Age[:\s]+(\d+)", text)
    if age_match:
        patient_info["Age"] = age_match.group(1).strip()

    # Extract Date
    date_match = re.search(r"Date[:\s]+([\d/-]+)", text)
    if date_match:
        patient_info["Date"] = date_match.group(1).strip()

    # Extract Doctor's Name
    doctor_match = re.search(r"Dr\.\s*([\w\s]+)", text)
    if doctor_match:
        patient_info["Doctor Name"] = doctor_match.group(1).strip()

    # Extract License Number
    license_match = re.search(r"(?:License|Reg No|Lic No|NPI)[:\s]+([\w\d]+)", text)
    if license_match:
        patient_info["License Number"] = license_match.group(1).strip()

    # Extract Medications (Assuming Each Line has Drug Name + Dosage + Frequency)
    medications = []
    med_pattern = re.findall(r"(\w+)\s+(\d+mg|\d+ml)\s+(once|twice|thrice|daily)", text, re.IGNORECASE)

    for med in med_pattern:
        medications.append({
            "Drug Name": med[0],
            "Dosage": med[1],
            "Frequency": med[2]
        })

    patient_info["Medications"] = medications

    # Extract Additional Notes (Assuming "Notes: ..." pattern)
    notes_match = re.search(r"Notes[:\s]+([\w\s.,]+)", text)
    if notes_match:
        patient_info["Additional Notes"] = notes_match.group(1).strip()

    return patient_info

# Parse the Extracted Text
structured_data = parse_prescription(extracted_text)

# Convert to JSON Format
structured_json = json.dumps(structured_data, indent=4)
print("Structured Order:\n", structured_json)