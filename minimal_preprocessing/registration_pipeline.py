from pathlib import Path
from minimal_preprocessing.command_utils import run_cmd
import os

REGISTRATION = (
    "flirt "
    "-in {filepath} "
    "-ref {anatpath} "
    "-omat {outpath} "
    "-cost corratio "
    "-dof 6 "
    "-interp trilinear"
)

WM_REGISTRATION = (
    "flirt "
    "-in {filepath} "
    "-ref {anatpath} "
    "-omat {outpath} "
    "-cost bbr "
    "-wmseg {wmpath} "
    "-dof 6 "
    "-init {initpath} "
    "-schedule /usr/share/fsl/5.0/etc/flirtsch/bbr.sch"
)

CONVERT_AFFINE = (
    "c3d_affine_tool "
    "-ref {anatpath} "
    "-src {meanpath} "
    "{filepath} "
    "-fsl2ras -oitk {outfile}"
)

TO_ANTS = "sed 's/MatrixOffsetTransformBase_double_3_3/AffineTransform_double_3_3/' {filepath} -i"

ANTS_APPLY_TRANSFORM = (
    "antsApplyTransforms "
    "--default-value 0 "
    "--dimensionality 3 "
    "--float 0 "
    "--input {filepath} "
    "--input-image-type 3 "
    "--interpolation Linear "
    "--output {outpath} "
    "--reference-image /usr/share/fsl/5.0/data/standard/MNI152_T1_2mm_brain.nii.gz "
    "--transform {transform3} "
    "--transform {transform2} "
    "--transform {transform1} "
    "--transform {transform0} "
    "--transform {affine}"
)


def print_afni_cmd(cmd_str):
    print(cmd_str.replace(" -", "\n -"))


def main(anatomical_path, func, mean, wm, trans3, trans2, trans1, trans0, output_path):
    if not Path(anatomical_path).exists():
        print("The anat file does not exist at: " + anatomical_path)
        exit(1)
    if not Path(output_path).exists():
        print("The output folder does not exist at: " + output_path)
        exit(1)
    env = os.environ.copy()
    env["PATH"] = (
        env["PATH"] + ":/opt/afni:/usr/share/fsl/5.0/bin:/usr/lib/fsl/5.0:"
        "/opt/c3d-1.1.0-Linux-gcc64/bin:/opt/c3d/bin"
    )
    env["FSLDIR"] = "/usr/share/fsl/5.0"
    env["LD_LIBRARY_PATH"] = "/usr/local/lib/:/usr/local/lib/:/usr/lib/fsl/5.0"
    env["FSLOUTPUTTYPE"] = "NIFTI_GZ"

    # Registration
    flirtmat = str(mean).replace(".nii.gz", "_flirt.mat")
    if not Path(flirtmat).exists():
        registration_cmd = REGISTRATION.format(
            filepath=mean, anatpath=anatomical_path, outpath=flirtmat
        )
        run_cmd(env, registration_cmd)

    wmreg = str(mean).replace(".nii.gz", "_wmreg.mat")
    if not Path(wmreg).exists():
        wmreg_cmd = WM_REGISTRATION.format(
            filepath=mean,
            anatpath=anatomical_path,
            outpath=wmreg,
            wmpath=wm,
            initpath=flirtmat,
        )
        run_cmd(env, wmreg_cmd)

    affine = str(output_path / "affine.txt")
    if not Path(affine).exists():
        affine_cmd = CONVERT_AFFINE.format(
            anatpath=anatomical_path, meanpath=mean, filepath=wmreg, outfile=affine
        )
        run_cmd(env, affine_cmd)
        run_cmd(env, TO_ANTS.format(filepath=affine))

    warped = str(func).replace(".nii.gz", "_antswarp.nii.gz")
    if not Path(warped).exists():
        warp_cmd = ANTS_APPLY_TRANSFORM.format(
            filepath=func,
            outpath=warped,
            transform3=trans3,
            transform2=trans2,
            transform1=trans1,
            transform0=trans0,
            affine=affine,
        )
        run_cmd(env, warp_cmd)
    return warped


if __name__ == "__main__":
    output_path = Path("output")
    anat_path = (
        output_path
        / "co20190109_114343MPRAGESIEMENSTi1100s011a1001A_resample_skullstrip_orig.nii.gz"
    )
    func_path = output_path / "20190109_114343MOVIEs009a001_resample_volregA.nii.gz"
    func_mean_path = (
        output_path
        / "20190109_114343MOVIEs009a001_resample_volregA_masked_tstat.nii.gz"
    )
    wm_path = output_path / "segment_prob_2_maths.nii.gz"
    transform3 = output_path / "transform3Warp.nii.gz"
    transform2 = output_path / "transform2Affine.mat"
    transform1 = output_path / "transform1Rigid.mat"
    transform0 = output_path / "transform0DerivedInitialMovingTranslation.mat"
    main(
        anat_path,
        func_path,
        func_mean_path,
        wm_path,
        transform3,
        transform2,
        transform1,
        transform0,
        output_path,
    )
