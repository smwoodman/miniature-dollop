# miniature-dollop
Development ESD Optics work. Work incldues viame-coco work, and semgenting via the T-MSER method.

Code here Will be moved to permanent repo once exploration is done, and the code is stable (or becoming stable).

## VIAME-COCO Process

The current process:

JW annotates images in viame-web-amlr. She tracks these annotations [here](https://docs.google.com/spreadsheets/d/1tP-AgewYAzWAJDJ6aM-9wRbs2Hr_EA9b5jWYuLcd1JM/edit?usp=sharing), including the location of the downloaded VIAME annotation CSVs. 

SMW then uses [viame-exp.ipynb](viame-exp.ipynb), on the imagery-dev Instance, to a) convert the VIAME CSVs to [COCO format](https://cocodataset.org/#format-data) using [viame2coco](https://github.com/nodd-tools/viame2coco), and b) extract regions from images using the COCO-formatted annotations. See the notebook for more details. The regions are written to the the bucket esd-image-library-dev/esd-shadowgraph-library. 

As noted in the notebook, the code to extract regions from images is heavliy based on this code: https://forum.image.sc/t/crop-image-and-annotations-to-bbox-coco-format/74520/4. Also, for COCO API functions see the top of https://github.com/ppwwyyxx/cocoapi/blob/master/PythonAPI/pycocotools/coco.py

To date, the following deployment/directories have been processed, and ROIs have been written to the shadowgraph library described above:

amlr08-20220513: Directories Dir0000, Dir0001, Dir0002, Dir0003, Dir0004, Dir0005, Dir0006, Dir0007, Dir0008, Dir0009

george-20240530: Dir0000, Dir0001 (partial)

george-20240907: 

## T-MSER Segmentation

July 2025: JW/SW are testing using the T-MSER segmentation method on shadowgraph imagery, to speed the work of building an ESD-specific shadowgraph image library. This is in place of (or in addition to) by-hand annotation by JW. 

The current segmentation tool is at [sullichrosu/Threshold-MSER](https://github.com/sullichrosu/Threshold-MSER). CS made this repo because the author of the original [paradom/Threshold-MSER](https://github.com/paradom/Threshold-MSER) was not responding at the time for update requests. Sam made a fork at [smwoodman/Threshold-MSER](https://github.com/smwoodman/Threshold-MSER), to add .jpg as valid file extension recognized by the tool. (Note that this fork was based off previous work done by Sam in the [us-amlr/Threshold-MSER](https://github.com/us-amlr/Threshold-MSER) fork.)

This tool has been installed on the tmser-dev Notebook. SMW is using the TODO python script, as a wrapper for running the tmser tool and organizing the outputs.

## Disclaimer

This repository is a scientific product and is not official communication of the National Oceanic and Atmospheric Administration, or the United States Department of Commerce. All NOAA GitHub project code is provided on an ‘as is’ basis and the user assumes responsibility for its use. Any claims against the Department of Commerce or Department of Commerce bureaus stemming from the use of this GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.
