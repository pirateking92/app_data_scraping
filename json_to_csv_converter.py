import json
import csv
import os
import traceback
from typing import List, Dict


class JSONtoCSVConverter:
    def json_to_csv(self, data: List[Dict], output_filepath: str) -> str:
        if not data:
            raise ValueError("The JSON data is empty.")

        fieldnames = list(data[0].keys())

        # Ensure the filename is valid
        output_filename = os.path.basename(output_filepath)
        output_filename = "".join(
            c for c in output_filename if c.isalnum() or c in (" ", ".", "_")
        ).rstrip()
        if not output_filename.endswith(".csv"):
            output_filename += ".csv"

        output_filepath = os.path.join(
            os.path.dirname(output_filepath), output_filename
        )

        # Write to CSV file
        with open(output_filepath, "w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)

        return output_filepath

    def process_json_file(self, json_file_path: str) -> None:
        with open(json_file_path, "r") as json_file:
            data = json.load(json_file)

        if not isinstance(data, list):
            data = [data]

        if "comment" not in data[0]:
            raise ValueError("The JSON data does not contain a 'comment' field.")

        comment_str = data[0]["comment"]
        submission_date = data[0]["submissionDate"]
        file_id = data[0]["id"]

        if (
            "files" in data[0]
            and isinstance(data[0]["files"], list)
            and len(data[0]["files"]) > 1
        ):
            file_name = data[0]["files"][0].get("fileName")
            output_filename = f"{data[0]['submitterFirstName']} {data[0]['submitterLastName']} filename: {file_name} comm: {comment_str[0:30]}_{submission_date[:9]}.csv"
        else:
            output_filename = f"{data[0]['submitterFirstName']} {data[0]['submitterLastName']} comm: {comment_str[0:30]}_{submission_date[:10]} {file_id[:8]}.csv"

        output_filename = output_filename.replace("/", "-")

        # Use the directory of the input JSON file for the output CSV file
        output_filepath = os.path.join(os.path.dirname(json_file_path), output_filename)
        output_file = self.json_to_csv(data, output_filepath)
        print(
            f"Conversion complete for {json_file_path}. CSV file saved as '{output_file}'"
        )

    def process_folder(self, folder_path: str) -> None:
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


if __name__ == "__main__":
    converter = JSONtoCSVConverter()
    try:
        while True:
            path = input("Enter the path to the JSON file or folder: ").strip()
            if not os.path.exists(path):
                print(f"The path '{path}' does not exist. Please try again.")
            else:
                break

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
