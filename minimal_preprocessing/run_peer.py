import minimal_preprocessing.peer_helper_functions as phf
import numpy as np


class PEER:
    def __init__(self, training_image, testing_image, eyemask_path, x_target, y_target):
        self.train = training_image
        self.test = testing_image
        self.eyemask = eyemask_path
        self.x_target = x_target
        self.y_target = y_target
        self.xmodel = None
        self.ymodel = None

    def train(self):
        training_data = phf.load_peer_image(self.train, eyemask_path=self.eyemask)
        training_arr = phf.reshape_image(training_data)
        training_arr = phf.preprocess_array(training_arr)
        mean_data  = []
        for num in range(0, training_data.shape[3]//5, 5):
            mean_data.append(np.mean(training_arr[num:num+5], 0))

        X = np.array(mean_data)
        X_model, Y_model = phf.train_peer(X, (self.x_target, self.y_target))
        self.xmodel = X_model
        self.ymodel = Y_model
        return X_model, Y_model

    def test(self, xmodel, ymodel):
        test_data = phf.load_peer_image(self.test, self.eyemask)
        test_arr = phf.reshape_image(test_data)
        test_arr = phf.preprocess_array(test_arr)
        xfix, yfix = phf.predict_fixations(xmodel, ymodel, test_arr)
        return xfix, yfix




