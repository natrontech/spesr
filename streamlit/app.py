import json
import locale
import logging
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
import pytesseract
import requests
from openai import OpenAI
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from PIL import Image, ImageEnhance, ImageOps, UnidentifiedImageError
from reportlab.pdfgen import canvas
from scipy import ndimage

import streamlit as st

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Streamlit page configuration
st.set_page_config(
    page_title="CSV to Excel Processor with Embedded Images and OCR",
    initial_sidebar_state="expanded",
    page_icon="📄",
)

# Set up OpenAI API key from environment variable
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


@st.cache_resource
def load_ocr_reader():
    return easyocr.Reader(["de", "en"], gpu=True)


def preprocess_image(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Binarization using Otsu's method
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Detect skew angle
    coords = np.column_stack(np.where(binary > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Rotate the image to correct skew
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )

    # Enhance contrast
    lab = cv2.cvtColor(rotated, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    # Denoise
    denoised = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)

    # Adaptive thresholding
    gray_denoised = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(
        gray_denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    return binary


def compress_image(image_path, quality=85):
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        img_io = BytesIO()
        img.save(img_io, format="JPEG", quality=quality, optimize=True)
        img_io.seek(0)
    return img_io


def extract_text_with_easyocr(image, reader):
    results = reader.readtext(image, detail=0)
    return " ".join(results)


def format_date(date_string):
    date_formats = ["%d. %B %Y", "%d.%m.%Y", "%d.%m.%y"]
    current_locale = locale.getlocale()
    try:
        locale.setlocale(locale.LC_TIME, "de_DE")
    except locale.Error:
        return date_string

    for date_format in date_formats:
        try:
            date_obj = datetime.strptime(date_string, date_format)
            locale.setlocale(locale.LC_TIME, current_locale)
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue

    locale.setlocale(locale.LC_TIME, current_locale)
    return date_string


def clean_text(text):
    printable = set(string.printable)
    cleaned_text = "".join(filter(lambda x: x in printable, text))
    cleaned_text = re.sub(r"[\x00-\x1F\x7F-\x9F]", "", cleaned_text)
    return cleaned_text


def extract_receipt_info(extracted_text):
    prompt = f"""
    Rules:
    - Leave fields empty ("") if information is missing.
    - Return only the JSON object with specified keys.
    - Return only the requested information.
    - Do not include additional information.
    - Correct any spelling or formatting errors.

    Extract the following from the receipt text:
    1. Amount: Total paid, format "X.XX" (no currency symbol)
    2. Seller: Name and address, format "Name, Street Nr, ZIP City"
    3. Card information: Last 4 digits and card type, format "XXXX, Card Type"
    4. Date: Purchase date, format "YYYY-MM-DD"

    Format output EXACTLY as follows:
    {{
    "extracted_amount": "amount",
    "extracted_seller": "seller name",
    "extracted_card_info": "card information",
    "extracted_date": "date"
    }}

    Receipt text: {extracted_text}
    """

    for _ in range(3):  # Retry up to 3 times
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that extracts information from receipts. Please follow the rules and extract the requested information.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )

            json_content = completion.choices[0].message.content
            result = json.loads(json_content)
            return json.dumps(result, indent=4)
        except (json.JSONDecodeError, KeyError) as e:
            st.warning(f"Failed to parse OpenAI response: {e}. Retrying...")
            continue

    return json.dumps(
        {
            "extracted_amount": "",
            "extracted_seller": "",
            "extracted_card_info": "",
            "extracted_date": "",
        },
        indent=4,
    )


def process_file(uploaded_file):
    reader = load_ocr_reader()
    df = pd.read_csv(uploaded_file)
    img_dir = "images"
    extracted_info = []
    df["manual_amount"] = ""
    df["manual_seller"] = ""
    df["manual_card_info"] = ""
    df["extracted_amount"] = ""
    df["extracted_seller"] = ""
    df["extracted_card_info"] = ""
    df["extracted_date"] = ""
    df["pdf_index"] = ""
    df["image_filename"] = ""

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
                image = Image.open(image_bytes)
                
                formatted_date = format_date(row["date"])
                original_img_filename = f"{index:04d}_{formatted_date}_{row['id']}_original.png"
                original_img_path = os.path.join(img_dir, original_img_filename)
                image.save(original_img_path)
                
                # Preprocess the image
                cv_image = cv2.imread(original_img_path)
                preprocessed_image = preprocess_image(cv_image)
                preprocessed_img_path = os.path.join(img_dir, f"{index:04d}_preprocessed.png")
                cv2.imwrite(preprocessed_img_path, preprocessed_image)
                
                # Compress the image
                compressed_img_io = compress_image(original_img_path)
                compressed_img_filename = f"{index:04d}_{formatted_date}_{row['id']}_compressed.jpg"
                compressed_img_path = os.path.join(img_dir, compressed_img_filename)
                with open(compressed_img_path, "wb") as f:
                    f.write(compressed_img_io.getvalue())
                
                easyocr_text = extract_text_with_easyocr(compressed_img_path, reader)
                receipt_info = extract_receipt_info(easyocr_text)
                parsed_info = json.loads(receipt_info)
                
                extracted_info.append({
                    "id": row["id"],
                    "extracted_text": clean_text(easyocr_text),
                    "extracted_amount": parsed_info["extracted_amount"],
                    "extracted_seller": clean_text(parsed_info["extracted_seller"]),
                    "extracted_card_info": clean_text(parsed_info["extracted_card_info"]),
                    "extracted_date": format_date(parsed_info["extracted_date"]),
                })
                
                df.at[index, "extracted_text"] = clean_text(easyocr_text)
                df.at[index, "picture"] = compressed_img_filename 
                df.at[index, "extracted_amount"] = parsed_info["extracted_amount"]
                df.at[index, "extracted_seller"] = clean_text(parsed_info["extracted_seller"])
                df.at[index, "extracted_card_info"] = clean_text(parsed_info["extracted_card_info"])
                df.at[index, "extracted_date"] = format_date(parsed_info["extracted_date"])
                df.at[index, "pdf_index"] = index
                
            except (requests.RequestException, UnidentifiedImageError) as e:
                st.error(f"Error processing image from URL {image_url}: {e}")
                extracted_info.append({
                    "id": row["id"],
                    "extracted_text": f"Error processing image: {e}",
                    "extracted_amount": "",
                    "extracted_seller": "",
                    "extracted_card_info": "",
                    "extracted_date": "",
                })
                df.at[index, "extracted_text"] = f"Error processing image: {e}"
                df.at[index, "picture"] = ""
                df.at[index, "pdf_index"] = index
            
            progress_bar.progress((index + 1) / len(df))

    df["date"] = df["date"].apply(format_date)
    df["extracted_date"] = df["extracted_date"].apply(format_date)

    df = df[
        [
            "pdf_index",
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

        cell = worksheet["A1"]
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    zip_filename = "processed_files.zip"
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        zipf.write("processed_file.xlsx", "processed_file.xlsx")

        for index, row in df.iterrows():
            if row["picture"]:
                image_path = os.path.join(img_dir, row["picture"])
                if os.path.exists(image_path):
                    # Open the compressed image
                    img = Image.open(image_path)

                    # Create a PDF in memory
                    pdf_buffer = BytesIO()
                    pdf = canvas.Canvas(pdf_buffer)

                    # Add the image to the PDF
                    pdf.setPageSize((img.width, img.height))
                    pdf.drawInlineImage(img, 0, 0, width=img.width, height=img.height)
                    pdf.showPage()
                    pdf.save()

                    # Get the PDF content
                    pdf_content = pdf_buffer.getvalue()

                    # Create a PDF filename
                    pdf_filename = os.path.splitext(row["picture"])[0] + ".pdf"

                    # Add the PDF to the zip file
                    zipf.writestr(os.path.join("pdfs", pdf_filename), pdf_content)

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
