"""
Script to read in VIAME CSV(s), 
and copy all relevant images to one folder
"""

import logging
import pandas as pd
from cloudpathlib import CloudPath


logging.basicConfig(
    format="%(name)s:%(asctime)s:%(levelname)s:%(message)s [line %(lineno)d]",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

# From esdglider
def check_gcs_file_exists(bucket, file_path):
    """
    Checks if a file exists in GCS. Function adapted from Gemini

    Parameters
    ----------
    bucket : Bucket
        An object of class Bucket, created via eg storage_client.bucket(bucket_name)
    file_path : str
        Path to the object/file in the bucket.
        Path does not include the bucket name

    Returns
    -------
    bool
        True if object exists, and False otherwise
    """
    # # This can be initialized once outside the function in your actual script
    # storage_client = storage.Client()
    # bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    return blob.exists()



## --- Configuration --- ##
# The local path to your CSV file.
CSV_FILE_PATH = 'image_list.csv'

# The name of the column in your CSV that contains the image filenames.
IMAGE_COLUMN_NAME = 'filename'

# Your source Google Cloud Storage details.
SOURCE_BUCKET_NAME = 'amlr-gliders-imagery-raw-dev'
SOURCE_PREFIX = 'path/to/original/images/'

# Your destination Google Cloud Storage details.
DESTINATION_BUCKET_NAME = 'your-destination-bucket-name'
# The "folder" or prefix where the new images should be copied.
# Leave as '' if they should go in the root of the bucket.
DESTINATION_PREFIX = 'path/to/renamed/images/'

if __name__ == "__main__":
    # Read CSV
    deployments = {
        "amlr08-20220513": {
            "project": "SANDIEGO", 
            "year": "2022"
        }
    }
    bucket_raw_img_dir = CloudPath(f"gs://{SOURCE_BUCKET_NAME}")  # pyright: ignore[reportAbstractUsage]
    bucket_img_library = CloudPath("gs://esd-image-library-dev")  # pyright: ignore[reportAbstractUsage]

    viame_csv_dir = bucket_img_library/ "viame-annotations"
    viame_csv_files = [item for item in viame_csv_dir.iterdir() if item.is_file()]

    # for f in viame_csv_dir.glob('**/*.csv'):
    #     text_data = f.read_text()
    #     print(f)
    #     # print(text_data)

    # For each deployment
    for d, value in deployments.items():
        vcsv_file = viame_csv_dir / f"{d}-annotations-all.csv"
        if not vcsv_file.is_file():
            logging.error("%s does not exist", vcsv_file)
        
        vcsv_df = pd.read_csv(vcsv_file)
        logging.debug("viame csv %s", vcsv_df)

        # Because we don't know the directory, get a list of all of images
        img_root_dir = (
            bucket_raw_img_dir / value["project"] / value["year"] / d / "images"
        )
        logging.debug("img_root_dir %s", img_root_dir)
        img_paths = list(img_root_dir.glob('**/*.jpg')) # Or use other extensions like '*.png', '*.jpeg'

        # Temporary fix: spaces are still in the file names
        img_to_get = [i.replace("-", " ", 1) for i in vcsv_df.iloc[:, 1]]
        # img_to_get = vcsv_df.iloc[:, 1]

        # Find the various full file paths
        subset_img_paths = [p for p in img_paths if p.name in img_to_get]
        logging.info("There are %s files to copy", len(subset_img_paths))

        # For each file, copy it to...
        viame_img_dir = viame_csv_dir / f"annotated-images-{d}"
        for source in subset_img_paths:
            logging.debug("source, dest")
            logging.debug(source)
            dest_name = source.name.replace(" ", "-")
            dest = viame_img_dir / dest_name
            logging.debug(dest)

            try:
                # shutil.copy(source, dest)
                source.copy(dest)
                logging.debug("File '%s' successfully copied to '%s'", source, dest)
            except FileNotFoundError:
                logging.error("Error: Source file '%s' not found", source)
            except Exception as e:
                logging.error("An error occurred: %s", e)
