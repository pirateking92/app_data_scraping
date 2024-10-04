import re


def remove_unique_identifier(filename):
    # Revised pattern for two UUIDs, timestamp, and file description
    pattern = (
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\."  # First UUID
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\."  # Second UUID
        r"\d{8}T\d{6}-\d{3}Z\."  # Timestamp in the format 20240415T92621-223Z
        r"([a-zA-Z0-9\s\-.]+)\.(.*)$"  # File description, extension
    )

    print(f"Processing filename: {filename}")

    # Attempt to match
    match = re.match(pattern, filename)
    if match:
        # Return the matched file description and extension
        return f"{match.group(1)}.{match.group(2)}"

    # If no patterns match, return the original filename
    print("No patterns matched.")
    return filename


# Test with the filenames
filenames = [
    "565b17eb-d43e-4249-b99e-b022009bdc5b.3446ad44-92fe-50ac-a659-43ece535e301.20240415T92621-223Z.Portfolio Release 1 - Version 1.0 - Jennifer Wark.docx",
    "565b17eb-d43e-4249-b99e-b022009bdc5b.3446ad44-92fe-50ac-a659-43ece535e301.20240415T92621-223Z.WARK SD v1.1 Stage  1 Knowledge Check.xlsx",
    "565b17eb-d43e-4249-b99e-b022009bdc5b.6984d7bc-8c3d-50aa-872a-d6b7f369864e.20231101T85802-610Z.Funding Circle Mail - Your reflection for Engineering Project II - Final Project.pdf",
    "565b17eb-d43e-4249-b99e-b022009bdc5b.20629d39-5996-5c66-b136-d705da4379cf.20231026T84328-497Z.Wark_Makers_Induction.pdf",
    "565b17eb-d43e-4249-b99e-b022009bdc5b.b87949ed-edc0-49d0-be40-4baa4c005fcc.20231026T83316-119Z.Funding Circle Mail - Fwd_ Your reflection for SwiftUI Engineering Project.pdf",
]

for file in filenames:
    print(f"Result: {remove_unique_identifier(file)}")
