# i want to make a dict or list that contains gets the names of the students from the file names i feed it
# then i want to iterate over the dict and add the files with the same student name, to a folder of that student name
import os
import shutil


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


def main():
    while True:
        print("Enter the folder path:")
        directory = input().strip()
        folder_organiser.organise_files(directory)

    if __name__ == "__main__":
        main()
