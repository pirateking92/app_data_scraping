import json
import csv
import os
import traceback
import logging
from typing import List, Dict


class JSONToCSVConverter:
    def json_to_csv(self, data: List[Dict], output_filename: str) -> str:
        """Converts a list of dictionaries (JSON data) into a CSV file."""
        if not data:
            raise ValueError("The JSON data is empty.")

        fieldnames = list(data[0].keys())

        # Ensure the filename is valid
        output_filename = "".join(
            c for c in output_filename if c.isalnum() or c in (" ", ".", "_")
        ).rstrip()
        if not output_filename.endswith(".csv"):
            output_filename += ".csv"

        # Write to CSV file
        with open(output_filename, "w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)

        return output_filename

    def process_json_file(self, json_file_path):
        """Converts a JSON file to a CSV file and saves it in the same folder."""
        base_name = os.path.basename(
            json_file_path
        )  # Get the base name (e.g., 'file.json')
        csv_file_name = base_name.replace(
            ".json", ".csv"
        )  # Replace extension with .csv
        folder_path = os.path.dirname(json_file_path)  # Get the folder path
        csv_file_path = os.path.join(
            folder_path, csv_file_name
        )  # Create the full CSV path

        try:
            with open(json_file_path, "r") as json_file:
                data = json.load(json_file)

            # Handle both list and dictionary JSON data
            if isinstance(data, dict):
                data = [
                    data
                ]  # Wrap the dict in a list to handle it as a list of one element

            if isinstance(data, list) and data:
                # If it's a list and not empty, proceed with CSV conversion
                keys = data[0].keys()  # Get keys for CSV header
                with open(csv_file_path, "w", newline="") as csv_file:
                    writer = csv.DictWriter(csv_file, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(data)
                logging.info(f"Converted JSON to CSV: {csv_file_path}")
            else:
                logging.error(
                    f"Invalid JSON format in {json_file_path}, expected a list or dict."
                )

        except json.JSONDecodeError as e:
            logging.error(
                f"JSONDecodeError: Failed to parse JSON file {json_file_path}: {e}"
            )
        except Exception as e:
            logging.error(f"Error converting {json_file_path} to CSV: {e}")

    def process_folder(self, folder_path: str) -> None:
        """Processes all JSON files in a folder and converts them to CSV."""
        processed_files = 0
        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                file_path = os.path.join(folder_path, filename)
                print(f"Processing file: {file_path}")
                try:
                    self.process_json_file(file_path)
                    processed_files += 1
                except Exception as e:
                    print(f"Error processing {filename}: {str(e)}")
        print(f"Processed {processed_files} files.")

    @staticmethod
    def get_valid_path(prompt: str) -> str:
        """Prompts the user for a valid file or folder path."""
        while True:
            path = input(prompt).strip()
            if not os.path.exists(path):
                print(f"The path '{path}' does not exist. Please try again.")
            else:
                return path


if __name__ == "__main__":
    converter = JSONToCSVConverter()
    try:
        # Handle both file and folder inputs
        path = JSONToCSVConverter.get_valid_path(
            "Enter the path to the JSON file or folder: "
        )

        if os.path.isfile(path):
            if os.path.getsize(path) == 0:
                raise ValueError("The JSON file is empty.")
            converter.process_json_file(path)
        elif os.path.isdir(path):
            converter.process_folder(path)
        else:
            raise ValueError("The provided path is neither a file nor a directory.")

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format. {str(e)}")
    except ValueError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        print("Detailed error information:")
        print(traceback.format_exc())
