import os
import zipfile
from io import BytesIO

import openpyxl
import pandas as pd
import requests
from openpyxl.drawing.image import Image as ExcelImage
from openpyxl.styles import Alignment, Font
from PIL import Image

import streamlit as st

# Map German month names to their respective month numbers
month_map = {
    "Januar": "01",
    "Februar": "02",
    "März": "03",
    "April": "04",
    "Mai": "05",
    "Juni": "06",
    "Juli": "07",
    "August": "08",
    "September": "09",
    "Oktober": "10",
    "November": "11",
    "Dezember": "12",
}


def parse_date(date_str):
    for german, number in month_map.items():
        date_str = date_str.replace(german, number)
    return pd.to_datetime(date_str, format="%d. %m %Y")


def process_file(uploaded_file):
    # Read the CSV file
    df = pd.read_csv(uploaded_file)

    # Parse the date column with the correct format
    if "date" in df.columns:
        try:
            df["date"] = df["date"].apply(parse_date)
        except Exception as e:
            st.error(f"Error parsing date column: {e}")
            return None, None
        df = df.sort_values(by="date")

    # Create a new Excel writer object
    with pd.ExcelWriter("processed_file.xlsx", engine="openpyxl") as writer:
        # Write the dataframe to the excel file
        df.to_excel(writer, index=False, sheet_name="Sheet1")

        # Load the workbook and select the sheet
        workbook = writer.book
        worksheet = workbook["Sheet1"]

        # Set column widths and header styles
        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter  # Get the column name
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = max_length + 2
            worksheet.column_dimensions[column].width = adjusted_width
            cell = worksheet[f"{column}1"]
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")

        # Adjust the width of the picture column and set row height
        img_dir = "images"
        if "picture" in df.columns:
            picture_col_idx = (
                df.columns.get_loc("picture") + 1
            )  # +1 because openpyxl is 1-indexed
            picture_col_letter = openpyxl.utils.get_column_letter(picture_col_idx)
            worksheet.column_dimensions[picture_col_letter].width = (
                30  # Set a suitable width for images
            )

            if not os.path.exists(img_dir):
                os.makedirs(img_dir)

            for index, row in df.iterrows():
                image_url = row["picture"]
                response = requests.get(image_url)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    img.thumbnail((100, 100))
                    img_filename = f"{row['date'].strftime('%Y-%m-%d')}_{row['id']}_{row['user']}_{row['type']}_{row['customer']}.png"
                    img_path = os.path.join(img_dir, img_filename)
                    img.save(img_path)
                    img = ExcelImage(img_path)
                    cell_ref = f"{picture_col_letter}{index + 2}"
                    worksheet.add_image(img, cell_ref)
                    worksheet.row_dimensions[index + 2].height = (
                        75  # Adjust row height for the image
                    )

    # Create a zip file of the images
    zip_filename = "images.zip"
    with zipfile.ZipFile(zip_filename, "w") as img_zip:
        for foldername, subfolders, filenames in os.walk(img_dir):
            for filename in filenames:
                img_zip.write(
                    os.path.join(foldername, filename),
                    os.path.relpath(os.path.join(foldername, filename), img_dir),
                )

    return "processed_file.xlsx", zip_filename


def main():
    st.title("CSV to Excel Processor with Embedded Images")

    uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

    if uploaded_file is not None:
        st.write("File uploaded successfully.")
        processed_file_path, zip_file_path = process_file(uploaded_file)

        if processed_file_path and zip_file_path:
            with open(processed_file_path, "rb") as file:
                st.download_button(
                    label="Download Processed Excel File",
                    data=file,
                    file_name="processed_file.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            with open(zip_file_path, "rb") as file:
                st.download_button(
                    label="Download Images Zip File",
                    data=file,
                    file_name="images.zip",
                    mime="application/zip",
                )


if __name__ == "__main__":
    main()
