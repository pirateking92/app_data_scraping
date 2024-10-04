import json
import csv
import os
import traceback
from typing import List, Dict  # [1] Added type hints for better code clarity


# [2] Refactored json_to_csv function to be more modular
def json_to_csv(data: List[Dict], output_filename: str) -> str:
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


# [3] New function to process individual JSON files
def process_json_file(json_file_path: str) -> None:
    with open(json_file_path, "r") as json_file:
        data = json.load(json_file)

    if not isinstance(data, list):
        data = [data]

    if "comment" not in data[0]:
        raise ValueError("The JSON data does not contain a 'comment' field.")

    comment_str = data[0]["comment"]
    submission_date = data[0]["submissionDate"]
    file_id = data[0]["id"]

    # Check if 'files' exists and has at least 2 items
    if (
        "files" in data[0]
        and isinstance(data[0]["files"], list)
        and len(data[0]["files"]) > 1
    ):
        file_name = data[0]["files"][1].get("fileName", "unknown_file")
        output_filename = f"{data[0]['submitterFirstName']} {data[0]['submitterLastName']} {file_name} {comment_str[0:30]}_{submission_date[:9]}.csv"
    else:
        # Handle case where 'files' is missing or has fewer than 2 items
        output_filename = f"{data[0]['submitterFirstName']} {data[0]['submitterLastName']} {comment_str[0:30]}_{submission_date[:10]} {file_id[:8]}.csv"

    output_file = json_to_csv(data, output_filename)
    print(
        f"Conversion complete for {json_file_path}. CSV file saved as '{output_file}'"
    )


# [4] New function to process a folder of JSON files
def process_folder(folder_path: str) -> None:
    processed_files = 0
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            print(f"Processing file: {file_path}")
            try:
                process_json_file(file_path)
                processed_files += 1
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
    print(f"Processed {processed_files} files.")


# [5] Renamed and modified function to handle both file and folder paths
def get_valid_path(prompt: str) -> str:
    while True:
        path = input(prompt).strip()
        if not os.path.exists(path):
            print(f"The path '{path}' does not exist. Please try again.")
        else:
            return path


if __name__ == "__main__":
    try:
        # [6] Modified to handle both file and folder inputs
        path = get_valid_path("Enter the path to the JSON file or folder: ")

        if os.path.isfile(path):
            if os.path.getsize(path) == 0:
                raise ValueError("The JSON file is empty.")
            process_json_file(path)
        elif os.path.isdir(path):
            process_folder(path)
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
