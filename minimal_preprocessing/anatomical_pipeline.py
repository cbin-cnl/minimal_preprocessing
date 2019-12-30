import argparse
from pathlib import Path
import shutil
from subprocess import Popen, PIPE
import shlex
import os

REFIT = "3drefit -deoblique {filepath}"
RESAMPLE = "3dresample -orient RPI -prefix {outpath} -inset {filepath}"
SKULLSTRIP = "3dSkullStrip -orig_vol -prefix {outpath} -input {filepath}"
SEGMENT = "fast -t 1 -o {outpath}/segment -p -g -S 1 {filepath}"
THRESH = "fslmaths {filepath} -thr 0.5 -bin {outpath}"
REGISTRATION = (
    "antsRegistration "
    "--collapse-output-transforms 0 "
    "--dimensionality 3 "
    "--initial-moving-transform [/usr/share/fsl/5.0/data/standard/MNI152_T1_2mm_brain.nii.gz,"
    "{filepath},0] "
    "--interpolation Linear "
    "--output [{outpath}/transform,{outpath}/transform_Warped.nii.gz] "
    "--transform Rigid[0.1] "
    "--metric MI[/usr/share/fsl/5.0/data/standard/MNI152_T1_2mm_brain.nii.gz,"
    "{filepath},1,32,Regular,0.25] "
    "--convergence [1000x500x250x100,1e-08,10] "
    "--smoothing-sigmas 3.0x2.0x1.0x0.0 "
    "--shrink-factors 8x4x2x1 "
    "--use-histogram-matching 1 "
    "--transform Affine[0.1] "
    "--metric MI[/usr/share/fsl/5.0/data/standard/MNI152_T1_2mm_brain.nii.gz,"
    "{filepath},1,32,Regular,0.25] "
    "--convergence [1000x500x250x100,1e-08,10] "
    "--smoothing-sigmas 3.0x2.0x1.0x0.0 "
    "--shrink-factors 8x4x2x1 "
    "--use-histogram-matching 1 "
    "--transform SyN[0.1,3.0,0.0] "
    "--metric CC[/usr/share/fsl/5.0/data/standard/MNI152_T1_2mm_brain.nii.gz,"
    "{filepath},1,4] "
    "--convergence [100x100x70x20,1e-09,15] "
    "--smoothing-sigmas 3.0x2.0x1.0x0.0 "
    "--shrink-factors 6x4x2x1 "
    "--use-histogram-matching 1 "
    "--winsorize-image-intensities [0.01,0.99] -v"
)


def print_afni_cmd(cmd_str):
    print(cmd_str.replace(" -", "\n -"))


def anat_pipeline(anatomical_path, output_path):
    if not Path(anatomical_path).exists():
        print("The anat file does not exist at: " + anatomical_path)
        exit(1)
    if not Path(output_path).exists():
        print("The output folder does not exist at: " + output_path)
        exit(1)
    shutil.copy(anatomical_path, output_path)
    output_folder = Path(output_path)
    anatomical_file = Path(anatomical_path).name
    infile = str(output_folder / anatomical_file)
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

    # 3dSkullStrip
    skullstrip = resampled.replace(".nii.gz", "_skullstrip_orig.nii.gz")
    if not Path(skullstrip).exists():
        skullstrip_cmd = SKULLSTRIP.format(filepath=resampled, outpath=skullstrip)
        run_cmd(env, skullstrip_cmd)

    # Segment
    wm_segment = output_folder / "segment_prob_2_maths.nii.gz"
    if not Path(wm_segment).exists():
        segment_cmd = SEGMENT.format(filepath=skullstrip, outpath=output_folder)
        run_cmd(env, segment_cmd)
        thresh_cmd = THRESH.format(
            filepath=output_folder / "segment_prob_2.nii.gz", outpath=wm_segment
        )
        run_cmd(env, thresh_cmd)

    # Register to MNI

    transform3 = os.path.join(output_path, "transform3Warp.nii.gz")
    transform2 = os.path.join(output_path, "transform2Affine.mat")
    transform1 = os.path.join(output_path, "transform1Rigid.mat")
    transform0 = os.path.join(
        output_path, "transform0DerivedInitialMovingTranslation.mat"
    )
    if not (
        os.path.exists(transform3)
        and os.path.exists(transform2)
        and os.path.exists(transform1)
        and os.path.exists(transform0)
    ):
        reg_cmd = REGISTRATION.format(filepath=skullstrip, outpath=output_folder)
        run_cmd(env, reg_cmd)
    return skullstrip, wm_segment, transform3, transform2, transform1, transform0


def run_cmd(env, refit_cmd):
    print_afni_cmd(refit_cmd)
    p = Popen(shlex.split(refit_cmd), stdout=PIPE, stderr=PIPE, env=env)
    stdout, stderr = p.communicate()
    print(stdout.decode("UTF-8"))
    print(stderr.decode("UTF-8"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process an anatomical image")
    parser.add_argument("anat_path", help="path to the anatomical image")
    parser.add_argument("output_path", help="path to the output folder")
    args = parser.parse_args()
    anat_pipeline(args.anat_path, args.output_path)
