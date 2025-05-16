from pathlib import Path
from zipfile import is_zipfile
import imghdr
import zipfile

# Define the file path
file_path = Path("./2024-11-12_report-99.jpeg")
extraction_path = Path("./extracted_files")

# Step 1: Basic file type checks
file_info = {
    "file_exists": file_path.exists(),
    "file_size_bytes": file_path.stat().st_size if file_path.exists() else None,
    "image_type": imghdr.what(file_path) if file_path.exists() else None,
    "is_zip_disguised": is_zipfile(file_path) if file_path.exists() else None
}

print(file_info)
# Step 2: Check for hidden files

extracted_files = []
try:
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        extraction_path.mkdir(exist_ok=True)
        zip_ref.extractall(extraction_path)
        extracted_files = zip_ref.namelist()
except zipfile.BadZipFile:
    extracted_files = ["Not a valid ZIP archive."]

# Step 3: Check for suspicious file types
suspicious_files = []
