import minimal_preprocessing.anatomical_pipeline as ap
import minimal_preprocessing.registration_pipeline as rp
import minimal_preprocessing.functional_pipeline as fp
import argparse
import shutil
from pathlib import Path
import minimal_preprocessing.command_utils as cu
import logging
import multiprocessing as mp


def run_pipelines(func_images, anat_image, output_directory):
    cu.set_logging(logging.DEBUG)

    tmp_anatomical = Path("/tmp/anatomical")
    output_dir = Path(output_directory)
    if not output_dir.exists():
        output_dir.mkdir()

    if not tmp_anatomical.exists():
        tmp_anatomical.mkdir()

    pool = mp.Pool(processes=3)
    anat_async = pool.apply_async(
        ap.anat_pipeline, args=(anat_image, str(tmp_anatomical))
    )
    async_list = []
    functional_dirs = []
    for func_image in func_images:
        tmp_functional = Path(Path("/tmp") / Path(func_image).name.split(".")[0])
        functional_dirs.append(tmp_functional)
        if not tmp_functional.exists():
            tmp_functional.mkdir()
        func_async = pool.apply_async(
            fp.func_pipeline, args=(func_image, str(tmp_functional))
        )
        async_list.append(func_async)
    skullstrip, wm_segment, transform3, transform2, transform1, transform0 = (
        anat_async.get()
    )
    anat_output = output_dir / "anatomical"
    if not anat_output.exists():
        anat_output.mkdir()
    shutil.copy(skullstrip, str(anat_output))
    shutil.copy(str(wm_segment), str(anat_output))
    shutil.copy(str(transform3), str(anat_output))
    shutil.copy(str(transform2), str(anat_output))
    shutil.copy(str(transform1), str(anat_output))
    shutil.copy(str(transform0), str(anat_output))
    registration_list = []
    for func_async, tmp_functional in zip(async_list, functional_dirs):
        motion_corrected, masked, masked_mean = func_async.get()
        func_output = output_dir / "functional"
        if not func_output.exists():
            func_output.mkdir()
        shutil.copy(motion_corrected, str(func_output))
        shutil.copy(masked, str(func_output))
        shutil.copy(masked_mean, str(func_output))

        register_async = pool.apply_async(
            rp.main, args=(skullstrip, motion_corrected, masked_mean, wm_segment, transform3,
                           transform2, transform1, transform0, tmp_functional)
        )
        registration_list.append(register_async)
    for register_async in registration_list:
        warped = register_async.get()
        shutil.copy(warped, str(output_dir))


def main():
    parser = argparse.ArgumentParser("run a minimal preprocessing pipeline")
    parser.add_argument("output_directory", help="the output directory ")
    parser.add_argument(
        "anat_image", help="a structural MRI image, must be in .nii.gz format"
    )
    parser.add_argument(
        "func_images", nargs="+", help="functional MRI images, must be in .nii.gz format"
    )
    args = parser.parse_args()
    run_pipelines(args.func_images, args.anat_image, args.output_directory)


if __name__ == "__main__":
    main()
