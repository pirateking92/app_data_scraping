import os
import shutil
import send2trash


class folder_organiser:
    def organise_files(self, directory):
        files = [
            f
            for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
        ]

        for file in files:
            words = file.split()[:2]
            if len(words) < 2:
                print(f"Skipping {file}: not enough words in filename.")
                continue

            folder_name = " ".join(words)
            folder_path = os.path.join(directory, folder_name)

            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            source = os.path.join(directory, file)
            destination = os.path.join(folder_path, file)
            shutil.move(source, destination)
            print(f"Moved {file} to {folder_name}")

    @staticmethod
    def merge_folders(source_paths, destination_name):
        # Create destination folder with full path
        desktop_path = os.path.join(
            os.path.expanduser("~"), "Desktop", "Activity Submissions"
        )
        destination_path = os.path.join(desktop_path, destination_name)

        if not os.path.exists(destination_path):
            os.makedirs(destination_path)
            print(f"Created destination folder: {destination_path}")

        file_count = 0
        total_files = 0
        # Process each source folder
        for source_path in source_paths:
            # Convert to absolute path if needed
            if not os.path.isabs(source_path):
                source_path = os.path.join(desktop_path, source_path)

            print(f"Processing folder: {source_path}")

            if os.path.exists(source_path):
                try:
                    # Get all files in the current folder and its subfolders
                    for root, _, files in os.walk(source_path):
                        for file in files:
                            total_files += 1
                            source_file = os.path.join(root, file)
                            dest_file = os.path.join(destination_path, file)

                            # Handle duplicate files
                            if os.path.exists(dest_file):
                                print(
                                    f"File {file} already exists in destination, skipping..."
                                )
                                continue

                            shutil.move(source_file, dest_file)
                            print(f"Moved {file} to {destination_name}")
                            file_count += 1

                    # Delete the source folder after moving all files
                    send2trash.send2trash(source_path)
                    print(f"Source folder moved to trash: {source_path}")

                except Exception as e:
                    print(f"Error processing folder {source_path}: {str(e)}")
            else:
                print(f"Source folder not found: {source_path}")
        print(f"Total files moved: {file_count} of {total_files}")


def main():
    while True:
        print("\nChoose an option:")
        print("1. Process a folder to organise its files")
        print("2. Process multiple folders to merge them into one folder")
        print("3. Exit")

        choice = input("Enter your choice (1/2/3): ").strip()

        if choice == "1":
            print("Enter the folder path:")
            directory = input().strip()
            organiser = folder_organiser()
            organiser.organise_files(directory)
        elif choice == "2":
            print("Enter name for the NEW merged folder:")
            destination_name = input().strip()

            source_paths = []
            print("\nEnter source folder paths (press Enter twice to finish):")
            while True:
                path = input().strip()
                if (
                    not path and source_paths
                ):  # If Enter pressed and we have at least one path
                    break
                elif path:  # If path is not empty
                    source_paths.append(path)

            if source_paths:
                print("\nProcessing these folders:", *source_paths, sep="\n")
                folder_organiser.merge_folders(source_paths, destination_name)
            else:
                print("No source paths provided!")
        elif choice == "3":
            print("Exiting program...")
            break
        else:
            print("Invalid choice, please try again")


if __name__ == "__main__":
    main()
