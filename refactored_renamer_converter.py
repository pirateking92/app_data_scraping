import os
import re
import logging
from weasyprint import HTML

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

filename_counts = {}


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
    """Removes unique identifiers (UUIDs, timestamps, etc.) from filenames."""
    patterns = [
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\."
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\."
        r"\d{8}T\d{6}-\d{3}Z\.([a-zA-Z0-9\s\-.]+)\.(.*)$",
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\."
        r"\d{8}T\d{6}-\d{3}Z\.([a-zA-Z0-9\s\-.]+)\.(.*)$",
        r"^[a-f0-9-]{36}\.[0-9T-]{20}Z\.(.*)$",
        r"^[a-f0-9-]{36}\.[a-f0-9-]{36}\.[0-9T-]{20}Z\.(.*)$",
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.([a-zA-Z0-9\s\-.]+)\.\d{8}T\d{6}-\d{3}Z\.(.*)$",
    ]

    logger.info(f"Processing filename: {filename}")

    for pattern in patterns:
        match = re.match(pattern, filename)
        if match:
            # If the pattern matches, construct the new filename based on matched groups
            new_filename = (
                f"{match.group(1)}.{match.group(2)}"
                if match.lastindex > 1
                else match.group(1)
            )
            return new_filename, filename.endswith(".html")

    logger.info("No patterns matched.")
    return filename, False


def increment_filename(directory, filename):
    """Ensures that the filename is unique in the directory by incrementing it if needed."""
    base, ext = os.path.splitext(filename)
    new_filename = filename
    counter = 1

    # Loop to find a unique filename
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base}({counter}){ext}"
        counter += 1

    return new_filename


def rename_file(file_path):
    """Renames a file and converts it to PDF if it's an HTML file."""
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
        if rename_file(file_path):
            renamed_count += 1

    logger.info(f"Renamed {renamed_count} out of {len(files)} files in the folder.")


def main():
    """Main function to handle user input and process files."""
    print("Choose an option:")
    print("1. Rename a single file")
    print("2. Rename multiple files")
    print("3. Rename all files in a folder")

    choice = input("Enter your choice (1/2/3): ").strip()

    if choice == "1":
        file_path = input("Enter the full path of the file: ").strip()
        process_individual_file(file_path)
    elif choice == "2":
        file_paths = []
        print("Enter full file paths (one per line). Enter an empty line to finish:")
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
        print("Invalid choice. Please run the script again and choose 1, 2, or 3.")


if __name__ == "__main__":
    main()
