from pathlib import Path
import shutil
from subprocess import run, STDOUT
import tempfile
# import multiprocessing as mp
# from itertools import repeat
import logging
import time


def copy_file_to_dir(image_file, destination_dir):
    """
    Copy image_file to the directory destination_dir
    The image will maintain the same name
    
    """
    destination_file = Path(destination_dir) / image_file.name
    logging.debug("Destination '%s'", destination_file)
    if not destination_file.is_file():
        logging.debug("Copying file '%s' to destination", destination_file)
        shutil.copy(image_file, destination_file)


def segment_file_management(indir: Path, outdir: Path):
    """
    The OSU segmentation tool writes its output to individual folders
    for each image. This makes it difficult to review images. 
    This function takes these outputs, and 'merges' the crop, frame, 
    and measurements folders across images.

    Parameters
    ----------
    indir : Path
        Path object to the segmentation output dir. 
        Specifically, the -o argument of segment call
        Expects `folders_to_merge` folders at this location
    outdir : Path
        Path object to where the files will be copied
    """
    folders_to_merge = [
        "segmentation/corrected_crop", 
        "segmentation/frame", 
        "measurements", 
    ]

    for folder in folders_to_merge:
        logging.info("Copying contents of source to destination")
        logging.info("source '%s'", folder)
        
        # Make output directory, if necessary
        dest_path = outdir / Path(folder).stem
        if not dest_path.exists():
            dest_path.mkdir(parents=True, exist_ok=True)
        logging.info("destination '%s'", dest_path)

        # For each image folder...
        for source_path in indir.rglob(f'*/{folder}'):
            logging.debug(source_path)
            if not source_path.is_dir():
                continue
            # For each source file, copy to destination
            for source_file in source_path.iterdir():
                logging.debug(source_file)
                if source_file.is_file():
                    dest_file = dest_path / source_file.name
                    # Remove spaces from filename, if necessary
                    new_name_str = dest_file.name.replace(" ", "_")
                    if new_name_str != dest_file.name:
                        dest_file = dest_file.with_name(new_name_str)
                    if not dest_file.exists():
                        logging.debug(f"Moving '{str(source_file)}' to '{str(dest_file)}'")
                        shutil.copy(source_file, dest_file)
                    else:
                        logging.debug(f"Skipping '{source_file.name}' as it already exists in '{dest_path}'")

        logging.info(
            "There are now %s files in destination '%s'", 
            len(list(dest_path.glob("*"))), 
            str(dest_path)
        )



project = "REFOCUS"
year = "2024"
deployment_name = "george-20240907"

# Which directories to run this on
dirnames = ["Dir0010"]

crop_params = {
    "left": "1200", 
    "right": "1200", 
    "bottom": "1200", 
    "top": "600", 
}

# # Different facttor, depending on the image size:
if deployment_name in ["amlr08-20220513"]:
    # Dimensions: 4056 x 3040 pixels, 72dpi
    factor = 1.0
elif deployment_name in ["george-20240907"]:
    # Dimensions: 2028 x 1520 pixels, 72dpi
    factor = 2.0 
else:
    raise ValueError("Given deployment is not yet accounted for by factor")

for k, v in crop_params.items():
    crop_params[k] = str(int(round(int(v)/factor, 0)))


#  /opt/Threshold-MSER/build/segment --verbose -i ~/george-20240530/Dir0001 -o ~/george-20240530/Dir0001-out -l 600 -r 600 -b 300 -t 300 -f -m 50 -d 20
logging.basicConfig(
    # filename=os.path.join(paths["logdir"], log_file_name),
    # filemode="w",
    format="%(name)s:%(asctime)s:%(levelname)s:%(message)s [line %(lineno)d]",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

def main():
    # Set variables. 
    # Assume running from SMW home directory, also the home of the mount points
    raw_bucket = "amlr-gliders-imagery-raw-dev"
    proc_bucket = "amlr-gliders-imagery-proc-dev"
    segment_file = Path("/opt/Threshold-MSER/build/segment")
    # numcores = mp.cpu_count()

    base_path = "/home/sam_woodman_noaa_gov"
    raw_mount = Path(base_path).joinpath(raw_bucket)
    proc_mount = Path(base_path).joinpath(proc_bucket)

    # Make directories, if necessary, and mount
    if not raw_mount.exists():
        raw_mount.mkdir(parents=True, exist_ok=True)
    if not proc_mount.exists():
        proc_mount.mkdir(parents=True, exist_ok=True)

    run(["gcsfuse", "--implicit-dirs", "-o", "ro", raw_bucket, str(raw_mount)])
    # run(["gcsfuse", "--implicit-dirs", proc_bucket, str(proc_mount)])

    # raw_path  = raw_mount.joinpath("gliders/2022/amlr08-20220513/shadowgraph/images")
    raw_path  = raw_mount.joinpath(project, year, deployment_name, "images")
    proc_path = proc_mount.joinpath(project, year, deployment_name, "tmser")

    # Generate list of Directories to segment
    # dir_list = ['Dir0053', 'Dir0054', 'Dir0055', 'Dir0056']
    if dirnames == "all":
        dir_list_orig = ([i.name for i in raw_path.iterdir()])

        dir_list_ignore = ["Dir0000", "Dir0001", "Dir0002", "Dir0003"]
        dir_list = list(set(dir_list_orig) - set(dir_list_ignore))
    else:
        dir_list = dirnames

    logging.info(f"Path to segment file: {segment_file}")
    logging.info(f"Path to raw (in) directories: {raw_path}")
    logging.info(f"Path to proc (out) directories: {proc_path}")
    logging.info(f"Directory list: {dir_list}")

    logging.info(f"\nStart time of directory passes: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    if segment_file.is_file():
        for i in dir_list:
            logging.info("\n--------------------------------------------------")
            start_time = time.time()
            logging.info(f"Segmenting images in directory {i}, " + 
                    f"start time {time.strftime('%Y-%m-%d %H:%M:%S')}")

            with tempfile.TemporaryDirectory() as temp_dir:
                # Run segmentation tool
                logging.info(f"Running segment, and writing files to {temp_dir}")
                segment_args = [
                    str(segment_file), 
                    "-i", str(raw_path.joinpath(i)), 
                    "-o", temp_dir, 
                    "--verbose", 
                    "-f", 
                    "-m", "50", 
                    "-d", "20", 
                    "-l", crop_params["left"], 
                    "-r", crop_params["right"], 
                    "-b", crop_params["bottom"], 
                    "-t", crop_params["top"], 
                ]
                logging.debug(segment_args)
                with open(f"{base_path}/{deployment_name}-{i}.log", "w") as log_file:
                    run(
                        segment_args, 
                        stdout=log_file,
                        stderr=STDOUT, 
                        text=True, 
                    )
                logging.info(f"Segmentation runtime: {(time.time()-start_time)/60} minutes")
                
                
                
                # shutil.move(temp_dir, str(proc_path))
                segment_file_management(Path(temp_dir), proc_path)




                # dir_out_path = proc_path.joinpath(i)

                # # Copy crop images to destination directory, in parallel
                # crop_path = dir_out_path.joinpath("corrected_crop")
                # if not crop_path.exists():
                #     crop_path.mkdir(parents=True, exist_ok=True)        
                # logging.info(f"Copying segmented region images from {temp_dir} " + 
                #         f"to {crop_path}, using {numcores} cores")
                # with mp.Pool(numcores) as pool: 
                #     pool.starmap(
                #         copy_file_to_dir, 
                #         zip(Path(temp_dir).glob("**/*.png"), repeat(crop_path))
                #     )

                # # Copy frame images to destination directory, in parallel
                # frame_path = dir_out_path.joinpath("frame")
                # if not frame_path.exists():
                #     frame_path.mkdir(parents=True, exist_ok=True)       
                # logging.info(f"Copying frame images from {temp_dir} " + 
                #         f"to {frame_path}, using {numcores} cores")
                # with mp.Pool(numcores) as pool: 
                #     pool.starmap(
                #         copy_file_to_dir, 
                #         zip(Path(temp_dir).glob("**/*.tif"), repeat(frame_path))
                #     )

                # Extract and copy measurements files
                # measurement_path = dir_out_path.joinpath("m")

                # folders_to_merge = [
                #     "segmentation/corrected_crop", 
                #     "segmentation/frame", 
                #     "measurements", 
                # ]
                # for folder in folders_to_merge:
                #     logging.info("Copying contents of %s directory", folder)
                #     for source_path in Path(temp_dir).rglob(f'*/{folder}'):
                #         if not source_path.is_dir():
                #             continue
                #         for source_file in source_path.iterdir():
                #             if source_file.is_file():
                #                 dest_path = proc_path.joinpath(i) / source_path.stem
                #                 destination_file = dest_path / source_file.name
                #                 if not destination_file.exists():
                #                     logging.debug(f"Moving '{str(source_file)}' to '{str(destination_file)}'")
                #                     shutil.move(str(source_file), str(destination_file))
                #                 else:
                #                     logging.debug(f"Skipping '{source_file.name}' as it already exists in '{dest_path}'")

            logging.info(f"Time is {time.strftime('%Y-%m-%d %H:%M:%S')}")
            logging.info(f"Full directory runtime: {(time.time()-start_time)/60} minutes")

    else:
        logging.error("error, segment file does not exist")

    logging.info("\n--------------------------------------------------")
    logging.info("Unmounting buckets")
    run(["fusermount", "-u", str(raw_mount)])
    run(["fusermount", "-u", str(proc_mount)])

    logging.info("Script complete")



if __name__ == "__main__":
    main()
    # segment_file_management(
    #     Path("/home/sam_woodman_noaa_gov/amlr-gliders-imagery-proc-dev/REFOCUS/2024/george-20240907/tmser"), 
    #     Path("/home/sam_woodman_noaa_gov/tmp-tmser"), 
    # )
    

# cd /opt/Threshold-MSER && git pull && cd ~/
# sudo chmod -R 755 /opt/Threshold-MSER/python
# python3 /opt/Threshold-MSER/python/segment.py