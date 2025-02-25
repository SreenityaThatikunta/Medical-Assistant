# Pharmacist's Assistant

This project automates the extraction of structured prescription details from handwritten/printed medical prescriptions. It leverages Google Gemini AI to extract information from images and saves the structured output as a .txt file in JSON format.

## Requirements

- Python 3.7+
- Google GenAI
- Pillow
- python-dotenv
- streamlit

## Installation

1. Clone the repository:

```
git clone https://github.com/SreenityaThatikunta/Medical-Assistant.git
cd Medical-Assistant
```

2. Set up your Gemini API key in .env

```
key = 'YOUR_KEY_HERE'
```

## Usage

Run the script:

```
streamlit run PharmaAssist.py
```

## Working Priciple

This script contains the PrescriptionParser class which handles the following tasks:
- Loading and converting the image: The load_image method loads the prescription image and converts it to RGB if necessary.
- Extracting text: The extract_text method uses the Gemini API to extract structured information from the prescription image.
- Parsing JSON: The parse_json method parses the extracted text into a structured JSON format.
- Processing the prescription: The process_prescription method executes the full pipeline: extract text, parse JSON, and return structured data. It finally outputs the content in a text file.