import anatomical_pipeline as ap
import registration_pipeline as rp
import functional_pipeline as fp
import argparse
import shutil
from pathlib import Path


def main(func_image, anat_image, output_directory):
    tmp_functional = Path("/tmp/functional")
    tmp_anatomical = Path("/tmp/anatomical")
    if not tmp_functional.exists():
        tmp_functional.mkdir()
    if not tmp_anatomical.exists():
        tmp_anatomical.mkdir()

    skullstrip, wm_segment, transform3, transform2, transform1, transform0 =\
        ap.anat_pipeline(anat_image, str(tmp_anatomical))
    motion_corrected, masked, masked_mean = fp.func_pipeline(func_image, str(tmp_functional))
    warped = rp.main(skullstrip, motion_corrected, masked_mean, wm_segment, transform3, transform2,
                     transform1, transform0, tmp_functional)
    output_dir = Path(output_directory)
    if not output_dir.exists():
        output_dir.mkdir()
    shutil.copy(warped, str(output_dir))



if __name__ == "__main__":
    parser = argparse.ArgumentParser("run a minimal preprocessing pipeline")
    parser.add_argument("func_image", help="a functional MRI image, must be in .nii.gz format")
    parser.add_argument("anat_image", help="a structural MRI image, must be in .nii.gz format")
    parser.add_argument("output_directory", help="the output directory ")
    args = parser.parse_args()
    main(args.func_image, args.anat_image, args.output_directory)
