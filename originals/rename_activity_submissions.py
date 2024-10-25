import os
import re
import logging
from weasyprint import HTML

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

filename_counts = {}


def convert_html_file_to_pdf(filename):
    if filename.endswith(".html"):
        pdf_filename = filename.replace(".html", ".pdf")

        try:
            HTML(filename).write_pdf(pdf_filename)
            logger.info(f"====== successfully converted {filename} to pdf ======")
            return pdf_filename
        except Exception as e:
            logger.error(f"Failed to convert {filename} to pdf: {str(e)}")
            return None
    else:
        logger.warning(f"{filename} is not an html file")
        return None


def remove_unique_identifier(filename):
    # List of patterns to match various filename structures
    patterns = [
        # Pattern for two UUIDs, timestamp, and a file description with spaces and periods
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\."
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\."
        r"\d{8}T\d{5,6}-\d{3}Z\.([a-zA-Z0-9\s\-.]+)\.(.*)$",  # Handles multiple periods in the description
        # Pattern for UUID, timestamp, and a description
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\."
        r"\d{8}T\d{6}-\d{3}Z\.([a-zA-Z0-9\s\-.]+)\.(.*)$",
        # Pattern for UUID.UUID.timestamp.rest
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\."
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\."
        r"\d{8}T\d{6}-\d{3}Z\.(.*)$",
        # Pattern for uuid.Other.timestamp.rest
        r"^[a-f0-9-]{36}\.Other\.[0-9T-]{20}Z\.(.*)$",
        # General pattern for UUID.Timestamp.Description.Extension
        r"^[a-f0-9-]{36}\.[0-9T-]{20}Z\.(.*)$",
        # General pattern for UUID.UUID.Timestamp.Description.Extension
        r"^[a-f0-9-]{36}\.[a-f0-9-]{36}\.[0-9T-]{20}Z\.(.*)$",
        # Pattern for snapshots
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.([a-zA-Z0-9\s\-.]+)\.\d{8}T\d{5,6}-\d{3}Z\.(.*)$",
    ]

    logger.info(f"Processing filename: {filename}")
    new_filename = filename

    # Iterate through patterns and attempt to match
    for pattern in patterns:
        match = re.match(pattern, filename)
        if match:
            new_filename = (
                f"{match.group(1)}.{match.group(2)}"
                if len(match.groups()) > 1
                else match.group(1)
            )

        # logic for checking if there are duplicate file names
        if new_filename in filename_counts:
            filename_counts[new_filename] += 1
            new_filename = f"{new_filename}({filename_counts[new_filename]})"
        else:
            filename_counts[new_filename] = 0

        return new_filename, filename.endswith(".html")

    # If no patterns match, return the original filename
    logger.info("No patterns matched.")
    return filename, False


def rename_file(file_path):
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    new_filename, is_html = remove_unique_identifier(filename)

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
    if os.path.isfile(file_path):
        rename_file(file_path)
    else:
        print(f"Error: The file '{file_path}' does not exist.")


def process_multiple_files(file_paths):
    renamed_count = 0
    for file_path in file_paths:
        if os.path.isfile(file_path):
            if rename_file(file_path):
                renamed_count += 1
        else:
            print(f"Skipped: '{file_path}' (file not found)")
    print(f"\nRenamed {renamed_count} out of {len(file_paths)} files.")


def process_files_in_folder(folder_path):
    if not os.path.isdir(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
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

    print(f"\nRenamed {renamed_count} out of {len(files)} files in the folder.")


def main():
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
