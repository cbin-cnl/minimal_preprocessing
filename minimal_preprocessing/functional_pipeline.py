import argparse
from pathlib import Path
import shutil
from minimal_preprocessing.command_utils import run_cmd, set_logging
import os
import logging

REFIT = "3drefit -deoblique {filepath}"
RESAMPLE = "3dresample -orient RPI -prefix {outpath} -inset {filepath}"
MEAN = "3dTstat -mean -prefix {outpath} {filepath}"
MOTION_CORRECTION = (
    "3dvolreg -Fourier -twopass -1Dfile {out_folder}/resample.1D "
    "-1Dmatrix_save {out_folder}/aff12.1D "
    "-prefix {outpath} "
    "-base {meanpath} "
    "-zpad 4 "
    "-maxdisp1D {out_folder}/max_displacement.1D {filepath}"
)
AUTOMASK = "3dAutomask " "-apply_prefix {outpath} " "-prefix {maskpath} " "{filepath}"


def func_pipeline(functional_path, output_path):
    if not Path(functional_path).exists():
        print("The func file does not exist at: " + functional_path)
        exit(1)
    if not Path(output_path).exists():
        print("The output folder does not exist at: " + output_path)
        exit(1)
    shutil.copy(functional_path, output_path)
    functional_file = Path(functional_path).name
    output_folder = Path(output_path)
    infile = str(output_folder / functional_file)
    env = os.environ.copy()
    env["PATH"] = env["PATH"] + ":/opt/afni:/usr/share/fsl/5.0/bin:/usr/lib/fsl/5.0"
    env["FSLDIR"] = "/usr/share/fsl/5.0"
    env["LD_LIBRARY_PATH"] = "/usr/local/lib/:/usr/local/lib/:/usr/lib/fsl/5.0"
    env["FSLOUTPUTTYPE"] = "NIFTI_GZ"
    # 3drefit
    refit_cmd = REFIT.format(filepath=infile)
    run_cmd(env, refit_cmd)

    # 3dresample
    resampled = infile.replace(".nii.gz", "_resample.nii.gz")
    if not Path(resampled).exists():
        resample_cmd = RESAMPLE.format(filepath=infile, outpath=resampled)
        run_cmd(env, resample_cmd)

    # Mean
    mean = resampled.replace(".nii.gz", "_tstat.nii.gz")
    if not Path(mean).exists():
        mean_cmd = MEAN.format(filepath=resampled, outpath=mean)
        run_cmd(env, mean_cmd)

    # Motion correction
    volreg = resampled.replace(".nii.gz", "_volreg.nii.gz")
    if not Path(volreg).exists():
        volreg_cmd_one = MOTION_CORRECTION.format(
            filepath=resampled, meanpath=mean, outpath=volreg, out_folder=output_path
        )
        run_cmd(env, volreg_cmd_one)

    # Volreg Mean
    volreg_mean = volreg.replace(".nii.gz", "_tstat.nii.gz")
    if not Path(volreg_mean).exists():
        mean_cmd = MEAN.format(filepath=volreg, outpath=volreg_mean)
        run_cmd(env, mean_cmd)

    # Motion correction 2
    volregA = resampled.replace(".nii.gz", "_volregA.nii.gz")
    if not Path(volregA).exists():
        volreg_cmd_two = MOTION_CORRECTION.format(
            filepath=resampled, meanpath=volreg_mean, outpath=volregA, out_folder=output_path
        )
        run_cmd(env, volreg_cmd_two)

    masked = volregA.replace(".nii.gz", "_masked.nii.gz")
    mask = volregA.replace(".nii.gz", "_mask.nii.gz")
    if not Path(masked).exists():
        automask_cmd = AUTOMASK.format(outpath=masked, maskpath=mask, filepath=volregA)
        run_cmd(env, automask_cmd)

    masked_mean = masked.replace(".nii.gz", "_tstat.nii.gz")
    if not Path(masked_mean).exists():
        masked_mean_cmd = MEAN.format(filepath=masked, outpath=masked_mean)
        run_cmd(env, masked_mean_cmd)

    return volregA, masked, masked_mean


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a functional image")
    parser.add_argument("func_path", help="path to the functional image")
    parser.add_argument("output_path", help="path to the output folder")
    args = parser.parse_args()
    set_logging(logging.DEBUG)
    func_pipeline(args.func_path, args.output_path)
