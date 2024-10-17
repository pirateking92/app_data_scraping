import os
import logging
from json_to_csv_converter import JSONtoCSVConverter  # Import the JSON converter
from db_conn import db_conn
from html_to_pdf import html_to_pdf
from pattern_recognition import Pattern_Recog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection details
DB_HOST = "127.0.0.1"
DB_NAME = "datamigrationmakers"
DB_USER = "mattdoyle"
DB_PASS = ""

filename_counts = {}

# Instantiate classes
json_converter = JSONtoCSVConverter()
db_conn = db_conn()
Pattern_Recog = Pattern_Recog()
htmlpdf = html_to_pdf


def increment_filename(directory, filename):
    """Ensures that the filename is unique in the directory by incrementing it if needed."""
    base, ext = os.path.splitext(filename)
    new_filename = filename
    counter = 1

    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base}({counter}){ext}"
        counter += 1

    return new_filename


def rename_file(file_path):
    """Renames a file and converts it if needed."""
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)

    new_filename, is_html = Pattern_Recog.remove_unique_identifier(filename)

    if filename == new_filename:
        logger.info(f"Skipped: {filename} (No change. Not needed or no name found.)")
        return False

    new_filename = increment_filename(directory, new_filename)

    try:
        new_file_path = os.path.join(directory, new_filename)
        os.rename(file_path, new_file_path)
        logger.info(f"Renamed: {filename} -> {new_filename}")

        if is_html:
            pdf_file = htmlpdf.convert_html_file_to_pdf(new_file_path)
            if pdf_file:
                logger.info(f"Converted HTML to PDF: {pdf_file}")
            else:
                logger.warning(f"Failed to convert HTML to PDF: {new_file_path}")
        return True
    except OSError as e:
        logger.error(f"Error renaming {filename}: {e}")
        return False


def process_individual_file(file_path):
    """Process a single file."""
    if os.path.isfile(file_path):
        if file_path.endswith(".json"):
            # Use the JSON to CSV converter for JSON files
            try:
                json_converter.process_json_file(file_path)
            except Exception as e:
                logger.error(f"Error processing JSON file '{file_path}': {e}")
        else:
            rename_file(file_path)
    else:
        logger.error(f"Error: The file '{file_path}' does not exist.")


def process_multiple_files(file_paths):
    """Process multiple files."""
    renamed_count = 0
    for file_path in file_paths:
        if os.path.isfile(file_path):
            if rename_file(file_path):
                renamed_count += 1
        else:
            logger.warning(f"Skipped: '{file_path}' (file not found)")
    logger.info(f"Renamed {renamed_count} out of {len(file_paths)} files.")


def process_files_in_folder(folder_path):
    """Processes all files in a folder."""
    if not os.path.isdir(folder_path):
        logger.error(f"The folder '{folder_path}' does not exist.")
        return

    files = [
        f
        for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
    ]
    renamed_count = 0

    for filename in files:
        file_path = os.path.join(folder_path, filename)
        if file_path.endswith(".json"):
            # Use the JSON to CSV converter for JSON files
            try:
                json_converter.process_json_file(file_path)
                renamed_count += 1
            except Exception as e:
                logger.error(f"Error processing JSON file '{file_path}': {e}")
        else:
            if rename_file(file_path):
                renamed_count += 1

    logger.info(f"Processed {renamed_count} out of {len(files)} files in the folder.")


def main():
    """Main function to handle user input and process files."""
    while True:
        print("Choose an option:")
        print("1. Process a single file")
        print("2. Process multiple files")
        print("3. Process all files in a folder")

        choice = input("Enter your choice (1/2/3): ").strip()

        if choice == "1":
            file_path = input("Enter the full path of the file: ").strip()
            process_individual_file(file_path)
        elif choice == "2":
            file_paths = []
            print(
                "Enter full file paths (one per line). Enter an empty line to finish:"
            )
            while True:
                file_path = input().strip()
                if not file_path:
                    break
                file_paths.append(file_path)
            process_multiple_files(file_paths)
        elif choice == "3":
            folder_path = input("Enter the folder path: ").strip()
            process_files_in_folder(folder_path)
        else:
            print("Invalid choice. Please run the script again and choose 1 or 2.")
            continue

        restart = input("Start again? (y/n): ").strip().lower()
        if restart != "y":
            print("Exiting program.")
            break


if __name__ == "__main__":
    main()
