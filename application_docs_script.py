import os
import zipfile
import gdown
import re


def download_from_drive(file_id, output_path):
    url = f"https://drive.google.com/uc?id={file_id}"
    gdown.download(url, output_path, quiet=False)


def unzip_and_rename(zip_path, new_folder_name):
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(new_folder_name)
    os.remove(zip_path)


def rename_files(folder_path, name_prefix):
    for filename in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, filename)):
            # Extract the information at the end of the string
            match = re.search(r"[-_]\s*(.+)\.(\w+)$", filename)
            if match:
                info = match.group(1)
                file_type = match.group(2)
                new_filename = f"{name_prefix} - {info}.{file_type}"
                os.rename(
                    os.path.join(folder_path, filename),
                    os.path.join(folder_path, new_filename),
                )


def main():
    # Step 1: Download the file from Google Drive
    file_id = input("Enter the Google Drive file ID: ")
    zip_path = "downloaded_file.zip"
    download_from_drive(file_id, zip_path)

    # Step 2: Rename the folder
    new_folder_name = input("Enter the new folder name: ")
    unzip_and_rename(zip_path, new_folder_name)

    # Step 3: Rename the files
    name_prefix = input("Enter the name prefix for the files: ")
    rename_files(new_folder_name, name_prefix)

    print("Process completed successfully!")


if __name__ == "__main__":
    main()
