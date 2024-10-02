import json
import csv
import os


def json_to_csv(json_file_path):
    # Read the JSON file
    with open(json_file_path, "r") as json_file:
        data = json.load(json_file)

    # Check if the data is a list of dictionaries
    if not isinstance(data, list):
        data = [data]

    # Get the fieldnames (keys) from the first item
    fieldnames = list(data[0].keys())

    # Extract the comment to use as filename
    if "comment" not in data[0]:
        raise ValueError("The JSON data does not contain a 'comment' field.")

    output_filename = f"{data[0]['comment']}.csv"

    # Ensure the filename is valid
    output_filename = "".join(
        c for c in output_filename if c.isalnum() or c in (" ", ".", "_")
    ).rstrip()
    if not output_filename.endswith(".csv"):
        output_filename += ".csv"

    # Write to CSV file
    with open(output_filename, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        # Write the header
        writer.writeheader()

        # Write the data
        for row in data:
            writer.writerow(row)

    return output_filename


def get_valid_file_path(prompt):
    while True:
        file_path = input(prompt).strip()
        if not os.path.exists(file_path):
            print(f"The file '{file_path}' does not exist. Please try again.")
        else:
            return file_path


if __name__ == "__main__":
    json_file_path = get_valid_file_path("Enter the path to the JSON file: ")

    try:
        output_file = json_to_csv(json_file_path)
        print(f"Conversion complete. CSV file saved as '{output_file}'")
    except ValueError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
