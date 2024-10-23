import os
import re
import logging
from psycopg2 import pool
from weasyprint import HTML
from datetime import datetime
from tqdm import tqdm
import signal
from contextlib import contextmanager
import gc
import psutil


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database connection details
DB_HOST = "127.0.0.1"
DB_NAME = "datamigrationmakers"
DB_USER = "mattdoyle"
DB_PASS = ""

# Global connection pool
connection_pool = None


def log_memory_usage():
    """Log current memory usage of the process"""
    process = psutil.Process(os.getpid())
    logger.info(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")


def init_connection_pool():
    """Initialize the connection pool"""
    global connection_pool
    try:
        connection_pool = pool.SimpleConnectionPool(
            1,  # minimum connections
            50,  # maximum connections
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
        )
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.error(f"Failed to initialize connection pool: {str(e)}")
        raise


def get_db_connection():
    """Get a connection from the pool"""
    if connection_pool:
        return connection_pool.getconn()
    else:
        raise Exception("Connection pool not initialized")


def release_db_connection(conn):
    """Return a connection to the pool"""
    if connection_pool:
        connection_pool.putconn(conn)


def get_learner_name(uuid):
    """Fetches the learner's full name from the database based on UUID."""
    conn = None
    try:
        conn = get_db_connection()
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
        if conn:
            release_db_connection(conn)


@contextmanager
def timeout(seconds):
    """Context manager for timing out operations"""

    def signal_handler(signum, frame):
        raise TimeoutError("Operation timed out")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


def convert_html_file_to_pdf(filename):
    """Convert an HTML file to PDF if applicable."""
    if filename.endswith(".html"):
        pdf_filename = filename.replace(".html", ".pdf")
        try:
            # Create a new HTML object explicitly and clean it up
            html = HTML(filename)
            html.write_pdf(pdf_filename)

            # Explicitly delete the HTML object
            del html
            gc.collect()

            logger.info(f"Successfully converted {filename} to PDF.")
            return pdf_filename
        except Exception as e:
            logger.error(f"Failed to convert {filename} to PDF: {str(e)}")
            return None
        finally:
            # Force garbage collection
            gc.collect()
    return None


def remove_unique_identifier(filename):
    """Removes unique identifiers (UUIDs, timestamps, etc.) from filenames and reformats."""
    logger.info(f"Processing filename: {filename}")

    patterns = [
        # UUID.Identifier.Timestamp.FileExtension
        r"^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\."
        r"([a-zA-Z0-9]+)\.(\d{8}T\d{6}-\d{3}Z)\.([a-zA-Z0-9]+)$",
        # Add your additional patterns here
    ]

    for pattern in patterns:
        match = re.match(pattern, filename)
        if match:
            uuid = match.group(1)
            identifier = match.group(2)
            timestamp = match.group(3)
            file_extension = match.group(4)

            formatted_date = datetime.strptime(timestamp, "%Y%m%dT%H%M%S-%fZ")
            remaining_part = formatted_date.strftime("%Y %m %d - %H:%M:%S")

            learner_name = get_learner_name(uuid)
            if learner_name:
                new_filename = (
                    f"{learner_name} - {identifier} - {remaining_part}.{file_extension}"
                )
                return new_filename, filename.endswith(".html")
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
    """Renames a file and converts it to PDF if it's an HTML file."""
    try:
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
                    # Check if PDF already exists
                    pdf_filename = new_file_path.replace(".html", ".pdf")
                    if os.path.exists(pdf_filename):
                        logger.info(
                            f"PDF already exists: {pdf_filename}. Skipping conversion."
                        )
                        return False  # No need to increment renamed count or process further

                    try:
                        pdf_file = convert_html_file_to_pdf(new_file_path)
                        if pdf_file:
                            logger.info(f"Converted HTML to PDF: {pdf_file}")
                        else:
                            logger.warning(
                                f"Failed to convert HTML to PDF: {new_file_path}"
                            )
                    except Exception as e:
                        logger.error(
                            f"PDF conversion error for {new_file_path}: {str(e)}"
                        )
                        # Continue processing even if PDF conversion fails
                return True
            except OSError as e:
                logger.error(f"Error renaming {filename}: {e}")
                return False
        else:
            logger.info(f"Skipped: {filename} (no change needed)")
            return False
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
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
    for file_path in tqdm(file_paths, desc="Processing files"):
        if os.path.isfile(file_path):
            if rename_file(file_path):
                renamed_count += 1
        else:
            logger.warning(f"Skipped: '{file_path}' (file not found)")

        # Periodic garbage collection
        if renamed_count % 100 == 0:
            gc.collect()
            log_memory_usage()

    logger.info(f"Renamed {renamed_count} out of {len(file_paths)} files.")


def process_files_in_folder(folder_path):
    """Processes all files in a folder."""
    if not os.path.isdir(folder_path):
        logger.error(f"The folder '{folder_path}' does not exist.")
        return

    renamed_count = 0
    total_count = 0

    try:
        # Get total file count for progress bar
        total_files = sum(1 for entry in os.scandir(folder_path) if entry.is_file())

        # Process files with progress bar
        with tqdm(total=total_files, desc="Processing files") as pbar:
            # Process files in smaller batches
            batch_size = 50
            files = []

            for entry in os.scandir(folder_path):
                if entry.is_file():
                    total_count += 1
                    files.append(entry.path)

                    # Process batch
                    if len(files) >= batch_size:
                        for file_path in files:
                            try:
                                if rename_file(file_path):
                                    renamed_count += 1
                            except Exception as e:
                                logger.error(f"Error processing {file_path}: {e}")
                            finally:
                                pbar.update(1)

                        # Clear batch
                        files = []
                        gc.collect()

            # Process remaining files
            for file_path in files:
                try:
                    if rename_file(file_path):
                        renamed_count += 1
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                finally:
                    pbar.update(1)

    except Exception as e:
        logger.error(f"Error processing folder {folder_path}: {e}")
    finally:
        logger.info(
            f"Renamed {renamed_count} out of {total_count} files in the folder."
        )


def main():
    """Main function to handle user input and process files."""
    try:
        init_connection_pool()
        log_memory_usage()

        print("Choose an option:")
        print("1. Rename a single file")
        print("2. Rename multiple files")
        print("3. Rename all files in a folder")

        choice = input("Enter your choice (1/2/3): ").strip()

        try:
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
                print(
                    "Invalid choice. Please run the script again and choose 1, 2, or 3."
                )
        except Exception as e:
            logger.error(f"Process error: {str(e)}")

    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
    finally:
        if connection_pool:
            connection_pool.closeall()
        log_memory_usage()


if __name__ == "__main__":
    main()
