import json
import locale
import os
import re
import string
import zipfile
from datetime import datetime
from io import BytesIO

import cv2
import easyocr
import numpy as np
import pandas as pd
import pillow_heif
import pytesseract
import requests
from openai import OpenAI
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from PIL import Image, UnidentifiedImageError

import streamlit as st

# Set up Tesseract environment
TESSDATA_PREFIX = "./tessdata/"
if not os.path.exists(TESSDATA_PREFIX):
    os.makedirs(TESSDATA_PREFIX)

# Download German language data for Tesseract if not present
deu_traineddata_path = os.path.join(TESSDATA_PREFIX, "deu.traineddata")
if not os.path.exists(deu_traineddata_path):
    url = "https://github.com/tesseract-ocr/tessdata/raw/main/deu.traineddata"
    response = requests.get(url)
    with open(deu_traineddata_path, "wb") as f:
        f.write(response.content)

os.environ["TESSDATA_PREFIX"] = TESSDATA_PREFIX

# Set up OpenAI API key from environment variable
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


@st.cache_resource
def load_ocr_reader():
    return easyocr.Reader(["de"], gpu=True)  # Initialize the OCR reader for German


def denoise(image):
    img_array = np.array(image)
    if len(img_array.shape) == 2 or (
        len(img_array.shape) == 3 and img_array.shape[2] == 1
    ):
        # Grayscale image
        denoised = cv2.fastNlMeansDenoising(img_array, None, 10, 7, 21)
    else:
        # Color image
        denoised = cv2.fastNlMeansDenoisingColored(img_array, None, 10, 10, 7, 21)
    return Image.fromarray(denoised)


def preprocess_image(image):
    img_array = np.array(image)
    if len(img_array.shape) == 2 or (
        len(img_array.shape) == 3 and img_array.shape[2] == 1
    ):
        # Grayscale image
        gray = img_array
    else:
        # Color image
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

    denoised = denoise(Image.fromarray(gray))
    blurred = cv2.GaussianBlur(np.array(denoised), (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((2, 2), np.uint8)
    dilated = cv2.dilate(thresh, kernel, iterations=1)
    eroded = cv2.erode(dilated, kernel, iterations=1)
    return Image.fromarray(eroded)


def extract_text_with_easyocr(image_path, reader):
    results = reader.readtext(image_path)
    return " ".join([res[1] for res in results])


def extract_text_with_tesseract(image):
    return pytesseract.image_to_string(image, lang="deu")


def combine_ocr_results(easyocr_text, tesseract_text):
    # Simple combination strategy: concatenate results
    combined_text = easyocr_text + " " + tesseract_text
    return combined_text


def open_image(image_bytes, url):
    if url.lower().endswith(".heic") or url.lower().endswith(".heif"):
        heif_file = pillow_heif.read_heif(image_bytes)
        image = Image.frombytes(
            heif_file.mode,
            heif_file.size,
            heif_file.data,
            "raw",
            heif_file.mode,
            heif_file.stride,
        )
    else:
        image = Image.open(image_bytes)

    # Ensure the image is in RGB mode
    if image.mode != "RGB":
        image = image.convert("RGB")

    return image


def format_date(date_string):
    # Convert German date format to YYYY-MM-DD
    date_formats = ["%d. %B %Y", "%d.%m.%Y", "%d.%m.%y"]

    # Save the current locale
    current_locale = locale.getlocale()

    try:
        # Set the locale to German
        locale.setlocale(locale.LC_TIME, "de_DE")
    except locale.Error:
        # If setting the German locale fails, return the original string
        return date_string

    for date_format in date_formats:
        try:
            date_obj = datetime.strptime(date_string, date_format)
            # Reset the locale to its original setting
            locale.setlocale(locale.LC_TIME, current_locale)
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Reset the locale to its original setting if all formats fail
    locale.setlocale(locale.LC_TIME, current_locale)
    return date_string  # Return original string if parsing fails


def extract_receipt_info(extracted_text):
    prompt = f"""
    Extract the following information from the receipt text:
    1. Amount (total money paid WITHOUT currency symbol in the format: "X.XX")
    2. Seller (shop/restaurant name and address in the following format: "Name, Street Nr, ZIP City")
    3. Card information (last 4 digits, type of card in the format: "XXXX, Card Type")
    4. Date (purchase date in YYYY-MM-DD format)

    Format the output EXACTLY as follows:
    {{
        "extracted_amount": "amount",
        "extracted_seller": "seller name",
        "extracted_card_info": "card information",
        "extracted_date": "date"
    }}

    Receipt text:
    {extracted_text}
    """

    for _ in range(3):  # Retry up to 3 times
        try:
            completion = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that extracts information from receipts.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            # Access the content of the message
            json_content = completion.choices[0].message.content

            # remove ```json
            json_content = re.sub(r"```json", "", json_content)
            json_content = re.sub(r"```", "", json_content)

            # Parse the JSON response
            result = json.loads(json_content)
            return json.dumps(result, indent=4)
        except (json.JSONDecodeError, KeyError) as e:
            st.warning(
                f"Failed to parse OpenAI response: {json_content}, Error: {e}. Retrying..."
            )
            continue

    st.error("Failed to get a valid JSON response from OpenAI after 3 attempts.")
    return json.dumps(
        {
            "extracted_amount": "",
            "extracted_seller": "",
            "extracted_card_info": "",
            "extracted_date": "",
        },
        indent=4,
    )


# Function to remove illegal characters for Excel
def clean_text(text):
    # Define allowed printable characters
    printable = set(string.printable)
    # Remove non-printable characters
    cleaned_text = "".join(filter(lambda x: x in printable, text))
    # Remove any remaining control characters or illegal Excel characters
    cleaned_text = re.sub(r"[\x00-\x1F\x7F-\x9F]", "", cleaned_text)
    return cleaned_text


def process_file(uploaded_file):
    reader = load_ocr_reader()
    df = pd.read_csv(uploaded_file)
    img_dir = "images"
    extracted_info = []

    # Add columns for manual annotation and extracted info
    df["manual_amount"] = ""
    df["manual_seller"] = ""
    df["manual_card_info"] = ""
    df["extracted_amount"] = ""
    df["extracted_seller"] = ""
    df["extracted_card_info"] = ""
    df["extracted_date"] = ""
    df["image_index"] = ""
    df["image_filename"] = ""  # Ensure image_filename is initialized

    if "picture" in df.columns:
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)

        progress_bar = st.progress(0)
        for index, row in df.iterrows():
            image_url = row["picture"]
            try:
                response = requests.get(image_url)
                response.raise_for_status()
                image_bytes = BytesIO(response.content)
                image = open_image(image_bytes, image_url)

                # Format the date
                formatted_date = format_date(row["date"])

                # Save original image
                original_img_filename = (
                    f"{index:04d}_{formatted_date}_{row['id']}_original.png"
                )
                original_img_path = os.path.join(img_dir, original_img_filename)
                image.save(original_img_path)

                # Preprocess image for OCR
                preprocessed_image = preprocess_image(image)

                easyocr_text = extract_text_with_easyocr(original_img_path, reader)
                tesseract_text = extract_text_with_tesseract(preprocessed_image)
                combined_text = combine_ocr_results(easyocr_text, tesseract_text)

                # Extract receipt information using OpenAI
                receipt_info = extract_receipt_info(combined_text)
                parsed_info = json.loads(receipt_info)

                extracted_info.append(
                    {
                        "id": row["id"],
                        "extracted_text": clean_text(combined_text),
                        "extracted_amount": parsed_info["extracted_amount"],
                        "extracted_seller": clean_text(parsed_info["extracted_seller"]),
                        "extracted_card_info": clean_text(
                            parsed_info["extracted_card_info"]
                        ),
                        "extracted_date": format_date(parsed_info["extracted_date"]),
                    }
                )

                df.at[index, "extracted_text"] = clean_text(combined_text)
                df.at[index, "picture"] = original_img_filename
                df.at[index, "extracted_amount"] = parsed_info["extracted_amount"]
                df.at[index, "extracted_seller"] = clean_text(
                    parsed_info["extracted_seller"]
                )
                df.at[index, "extracted_card_info"] = clean_text(
                    parsed_info["extracted_card_info"]
                )
                df.at[index, "extracted_date"] = format_date(
                    parsed_info["extracted_date"]
                )
                df.at[index, "image_index"] = index

            except (requests.RequestException, UnidentifiedImageError) as e:
                st.error(f"Error processing image from URL {image_url}: {e}")
                extracted_info.append(
                    {
                        "id": row["id"],
                        "extracted_text": f"Error processing image: {e}",
                        "extracted_amount": "",
                        "extracted_seller": "",
                        "extracted_card_info": "",
                        "extracted_date": "",
                    }
                )
                df.at[index, "extracted_text"] = f"Error processing image: {e}"
                df.at[index, "picture"] = ""
                df.at[index, "image_index"] = index

            progress_bar.progress((index + 1) / len(df))

    # Ensure date columns are in the same format
    df["date"] = df["date"].apply(format_date)
    df["extracted_date"] = df["extracted_date"].apply(format_date)

    # Rearrange columns
    df = df[
        [
            "image_index",
            "id",
            "date",
            "extracted_date",
            "customer",
            "user",
            "picture",
            "amount",
            "extracted_amount",
            "extracted_seller",
            "company_credit_card",
            "extracted_card_info",
            "extracted_text",
        ]
    ]

    with pd.ExcelWriter("processed_file.xlsx", engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
        workbook = writer.book
        worksheet = workbook["Sheet1"]

        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = max_length + 2
            worksheet.column_dimensions[column].width = adjusted_width

            cell = worksheet[f"{column}1"]
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")

    zip_filename = "processed_files.zip"
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        zipf.write("processed_file.xlsx", "processed_file.xlsx")
        for index, row in df.iterrows():
            if row["picture"]:
                image_path = os.path.join(img_dir, row["picture"])
                if os.path.exists(image_path):
                    zipf.write(image_path, os.path.join("images", row["picture"]))

    return zip_filename


def main():
    st.title("CSV to Excel Processor with Embedded Images and OCR")
    uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

    if uploaded_file is not None:
        st.write("File uploaded successfully.")

        if st.button("Process File"):
            with st.spinner("Processing..."):
                zip_file_path = process_file(uploaded_file)

            if zip_file_path:
                with open(zip_file_path, "rb") as file:
                    st.download_button(
                        label="Download Processed Files",
                        data=file,
                        file_name="processed_files.zip",
                        mime="application/zip",
                    )


if __name__ == "__main__":
    main()
