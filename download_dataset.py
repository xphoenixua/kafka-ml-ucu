import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown"]) # ensure gdown is installed
import gdown
import zipfile
import os

# URL: https://drive.google.com/file/d/1rqnKe9IgU_crMaxRoel9_nuUsMEBBVQu/view?usp=sharing
FILE_ID = '1rqnKe9IgU_crMaxRoel9_nuUsMEBBVQu'
TARGET_DIR = 'data'
TEMP_ZIP_PATH = 'data/VisDrone2019-MOT-val.zip.tmp'

def download_and_unzip_visdrone():
    os.makedirs(TARGET_DIR, exist_ok=True)
    print(f"Attempting to download VisDrone dataset (File ID: {FILE_ID}) from Google Drive...")

    try:
        gdown.download(id=FILE_ID, output=TEMP_ZIP_PATH, quiet=False, fuzzy=True)

        print(f"Unzipping {TEMP_ZIP_PATH} to {TARGET_DIR}...")
        with zipfile.ZipFile(TEMP_ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(TARGET_DIR)

        os.remove(TEMP_ZIP_PATH)

    except Exception as e:
        print(f"\nError during download or unzip: {e}")
        if os.path.exists(TEMP_ZIP_PATH):
            os.remove(TEMP_ZIP_PATH)
        sys.exit(1)

if __name__ == "__main__":
    download_and_unzip_visdrone()
    