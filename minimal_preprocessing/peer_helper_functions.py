import nibabel as nib
from scipy.stats import zscore
import numpy as np
import pandas as pd
from sklearn.svm import SVR


def load_peer_image(image, eyemask_path):
    img = nib.load(image)
    data = img.get_fdata()
    eye_mask = nib.load(eyemask_path).get_fdata()
    for i in range(data.shape[3]):
        data[:, :, :, i] *= eye_mask
    return data


def reshape_image(data):
    arr_temp = []
    for i in range(data.shape[3]):
        arr_temp.append(data[:, :, :, i].ravel())
    arr = np.array(arr_temp)
    return arr


def preprocess_array(arr):
    arr = zscore(arr, 0)
    arr[np.isnan(arr)] = 0
    return arr


def make_targets(
    _calibration_points_removed, _stimulus_path, monitor_width, monitor_height
):
    fixations = pd.read_csv(_stimulus_path)
    x_targets = np.repeat(np.array(fixations["pos_x"]), 1) * monitor_width / 2
    y_targets = np.repeat(np.array(fixations["pos_y"]), 1) * monitor_height / 2
    x_targets = list(np.delete(np.array(x_targets), _calibration_points_removed))
    y_targets = list(np.delete(np.array(y_targets), _calibration_points_removed))
    return x_targets, y_targets


def default_algorithm():
    return SVR(kernel="linear", C=100, epsilon=0.01, verbose=2)


def train_peer(x, y, peer_algorithm=default_algorithm):
    _xmodel = peer_algorithm()
    _xmodel.fit(x, y[0])

    _ymodel = peer_algorithm()
    _ymodel.fit(x, y[1])

    return _xmodel, _ymodel


def predict_fixations(_xmodel, _ymodel, _data):
    _x_fix = _xmodel.predict(_data)
    _y_fix = _ymodel.predict(_data)
    return _x_fix, _y_fix


def get_slice_order(slices, multiband, inca):
    axial_slice_indices = list(range(0, 60))
    stride = slices // multiband
    slice_order = []
    for i in range(stride):
        loc = (i * inca) % stride
        slices_at_time = list(range(loc, slices, stride))

        slice_indices = [axial_slice_indices[s] for s in slices_at_time]
        slice_order.append(slice_indices)
    return slice_order


def get_slice_timeseries(data, slice_order, slice_timing=0.08):
    timepoints = []
    timings = []
    timing_ind = 0
    data = data.astype(float)

    # data[data <= 0] = np.nan
    for ind in range(data.shape[3]):
        for slice in slice_order:
            timings.append(timing_ind * slice_timing)
            timing_ind += 1
            timepoints.append(data[:, :, slice, ind].ravel())

    arr = np.array(timepoints)
    return arr
