import os
import re
import logging
import psycopg2
from weasyprint import HTML
from json_to_csv_converter import JSONtoCSVConverter  # Import the JSON converter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection details
DB_HOST = "127.0.0.1"
DB_NAME = "datamigrationmakers"
DB_USER = "mattdoyle"
DB_PASS = ""

filename_counts = {}

# Instantiate the JSONToCSVConverter
json_converter = JSONtoCSVConverter()


def connect_to_database():
    """Connects to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
        )
        logger.info("Connected to the database.")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return None


def get_learner_name(uuid):
    """Fetches the learner's full name from the database based on UUID."""
    conn = connect_to_database()
    if conn is None:
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT learner_full_name FROM apprentice_info WHERE ApplicationId = %s",
                (uuid.upper(),),
            )
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        logger.error(f"Failed to fetch learner name for UUID {uuid}: {str(e)}")
        return None
    finally:
        conn.close()


def convert_html_file_to_pdf(filename):
    """Convert an HTML file to PDF if applicable."""
    if filename.endswith(".html"):
        pdf_filename = filename.replace(".html", ".pdf")
        try:
            HTML(filename).write_pdf(pdf_filename)
            logger.info(f"Successfully converted {filename} to PDF.")
            return pdf_filename
        except Exception as e:
            logger.error(f"Failed to convert {filename} to PDF: {str(e)}")
            return None
    return None


def remove_unique_identifier(filename):
    """Removes unique identifiers (UUIDs, timestamps, etc.) from filenames and reformats."""
    logger.info(f"Processing filename: {filename}")

    patterns = [
        r"^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\."
        r"([a-zA-Z0-9]+)\.\d{8}T\d{6}-\d{3}Z(\.[a-zA-Z0-9]+)$",
        r"^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\."
        r"([a-zA-Z0-9]+)\.\d{8}T\d{6}-\d{3}Z\.(.*?)\.(.*)$",
        r"^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\."
        r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\."
        r"(\d{8}T\d{6}-\d{3}Z\.[\w\s\-().,'&_]+\.[a-zA-Z0-9]+$)",
        r"^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\."
        r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\."
        r"\d{8}T([0-9]{6}|[7-9][0-9]{4})-\d{3}Z\.[\w\s\-().,'&_+]+(\.[a-zA-Z0-9]+)+$",
        r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\."
        r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\."
        r"\d{8}T\d{5}-\d{3}Z\.[\w\s\-().,'&_+*]+(\.[a-zA-Z0-9]+)+$",
    ]

    for pattern in patterns:
        match = re.match(pattern, filename)
        if match:
            uuid = match.group(1)
            # identifier = match.group(2)
            remaining_part = match.group(3) if len(match.groups()) > 2 else ""
            file_extension = match.group(len(match.groups()))
            # identifier.rstrip()
            remaining_part.rstrip()

            learner_name = get_learner_name(uuid)
            if learner_name:
                if remaining_part:
                    new_filename = (
                        f"{learner_name} - {remaining_part[0:10]}.{file_extension}"
                    )
                else:
                    new_filename = f"{learner_name} - {file_extension}"

                return new_filename.rstrip(), filename.endswith(".html")
            else:
                logger.warning(
                    f"No learner name found for UUID {uuid}. Using original filename."
                )
                return filename, filename.endswith(".html")

    logger.info("No patterns matched.")
    return filename, False


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

    new_filename, is_html = remove_unique_identifier(filename)
    new_filename = increment_filename(directory, new_filename)

    if filename != new_filename:
        new_file_path = os.path.join(directory, new_filename)
        try:
            os.rename(file_path, new_file_path)
            logger.info(f"Renamed: {filename} -> {new_filename}")

            if is_html:
                pdf_file = convert_html_file_to_pdf(new_file_path)
                if pdf_file:
                    logger.info(f"Converted HTML to PDF: {pdf_file}")
                else:
                    logger.warning(f"Failed to convert HTML to PDF: {new_file_path}")
            return True
        except OSError as e:
            logger.error(f"Error renaming {filename}: {e}")
            return False
    else:
        logger.info(f"Skipped: {filename} (no change needed)")
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
        print("2. Process all files in a folder")

        choice = input("Enter your choice (1/2): ").strip()

        if choice == "1":
            file_path = input("Enter the full path of the file: ").strip()
            process_individual_file(file_path)
        elif choice == "2":
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
