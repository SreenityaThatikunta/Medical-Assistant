import kagglehub
import cv2
import os
import pytesseract

path = kagglehub.dataset_download("mehaksingal/illegible-medical-prescription-images-dataset")

print("Path to dataset files:", path)

# dataset_path = '/Users/sreenityathatikunta/.cache/kagglehub/datasets/mehaksingal/illegible-medical-prescription-images-dataset/versions/1'

input_dir = 'data'  
output_dir = "processed_images"

os.makedirs(output_dir, exist_ok=True)

image_files = [f for f in os.listdir(input_dir) if f.endswith(".jpg")]

for image_name in image_files:

    img_path = os.path.join(input_dir, image_name)
    img = cv2.imread(img_path)

    if img is None:
        print(f"Could not read {image_name}. Skipping...")
        continue

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    denoised = cv2.fastNlMeansDenoising(gray, None, h=30, templateWindowSize=7, searchWindowSize=21)

    output_path = os.path.join(output_dir, image_name)
    cv2.imwrite(output_path, denoised)

    # print(f"Processed and saved: {output_path}")

print("Image processing complete. Check the 'processed_images' folder.")

input_dir = "processed_images"  # Folder where denoised images are stored
output_dir = "extracted_text"
os.makedirs(output_dir, exist_ok=True)

# Get all processed images
image_files = [f for f in os.listdir(input_dir) if f.endswith(".jpg")]

# Loop through images and apply OCR
for image_name in image_files:
    img_path = os.path.join(input_dir, image_name)

    # Read image
    img = cv2.imread(img_path)

    # Convert to grayscale (optional, since images are already processed)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply OCR
    extracted_text = pytesseract.image_to_string(gray, lang="eng")  

    # Save text to a file
    text_filename = os.path.join(output_dir, image_name.replace(".jpg", ".txt"))
    with open(text_filename, "w", encoding="utf-8") as text_file:
        text_file.write(extracted_text)

    # print(f"Extracted text saved: {text_filename}")

print("✅ OCR completed. Check the 'extracted_text' folder for results.")