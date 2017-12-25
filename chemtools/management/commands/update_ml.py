import os
import cPickle

from django.core.management.base import BaseCommand
from django.core.files import File
import numpy
from sklearn import svm
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_absolute_error
import sklearn

from data.models import DataPoint, Predictor
from project.utils import StringIO


def lock(func):
    def wrapper(*args, **kwargs):
        # Not very safe, but it will work well enough
        if os.path.exists(".updating_ml"):
            print "Already running"
            return
        with open(".updating_ml", "w"):
            try:
                value = func(*args, **kwargs)
            except Exception as e:
                print e
                value = None
        os.remove(".updating_ml")
        return value
    return wrapper


class Command(BaseCommand):
    args = ''
    help = 'Update ML data'

    def handle(self, *args, **options):
        run_all()


class MultiStageRegression(object):
    def __init__(self, model=svm.SVR()):
        self.model = model
        self._first_layer = None
        self._second_layer = None

    def fit(self, X, y, sample_weight=None):
        if len(y.shape) == 1:
            y = y.reshape(y.shape[0], 1)

        self._first_layer = []
        predictions = []
        for i in xrange(y.shape[1]):
            m = sklearn.clone(self.model)
            m.fit(X, y[:, i])
            predictions.append(m.predict(X).reshape(-1, 1))
            self._first_layer.append(m)

        self._second_layer = []
        for i in xrange(y.shape[1]):
            added = predictions[:i] + predictions[i + 1:]
            X_new = numpy.hstack([X] + added)
            m = sklearn.clone(self.model)
            m.fit(X_new, y[:, i])
            self._second_layer.append(m)
        return self

    def predict(self, X):
        if self._first_layer is None or self._second_layer is None:
            raise ValueError("Model has not been fit")
        predictions = []
        for model in self._first_layer:
            predictions.append(model.predict(X).reshape(-1, 1))

        res = []
        for i, m in enumerate(self._second_layer):
            added = predictions[:i] + predictions[i + 1:]
            X_new = numpy.hstack([X] + added)
            res.append(m.predict(X_new))
        return numpy.array(res).T


def save_model(model, errors):
    print "Saving clfs"

    with StringIO(name="decay_predictors.pkl") as f:
        cPickle.dump(model, f, protocol=-1)
        f.seek(0)

        pred = Predictor(
            homo_error=errors[0],
            lumo_error=errors[1],
            gap_error=errors[2],
            pickle=File(f),
        )
        pred.save()


#@lock
def run_all():
    #pred = Predictor.objects.latest()
    #latest = DataPoint.objects.latest()

    #if latest.created < pred.created:
    #    print "No Update"
    #    return

    #print "Loading Data"
    #X, HOMO, LUMO, GAP = DataPoint.get_all_data()
    n = 40
    m = 5
    X = numpy.random.rand(n, m)
    homo_weights = numpy.arange(m)
    lumo_weights = numpy.arange(m)
    gap_weights = numpy.arange(m)
    numpy.random.shuffle(homo_weights)
    numpy.random.shuffle(lumo_weights)
    numpy.random.shuffle(gap_weights)

    HOMO = (X.dot(homo_weights) + numpy.random.randn(n)).reshape(-1, 1)
    LUMO = (X.dot(lumo_weights) + numpy.random.randn(n)).reshape(-1, 1)
    GAP = (X.dot(gap_weights) + numpy.random.randn(n)).reshape(-1, 1)
    y = numpy.hstack([HOMO, LUMO, GAP])

    n = X.shape[0]
    split = int(0.9 * n)
    idxs = numpy.arange(n)
    numpy.random.shuffle(idxs)
    train_idx = idxs[:split]
    test_idx = idxs[split:]
    X_train = X[train_idx, :]
    X_test = X[test_idx, :]
    y_train = y[train_idx, :]
    y_test = y[test_idx, :]

    params = {"gamma": [1e-9, 1e-7, 1e-5, 1e-3, 1e-1, 1e1],
              "C": [1e-9, 1e-7, 1e-5, 1e-3, 1e-1, 1e1]}
    inner_model = GridSearchCV(estimator=svm.SVR(kernel="rbf"),
                               param_grid=params)
    model = MultiStageRegression(model=inner_model)
    model.fit(X_train, y_train)
    errors = numpy.abs(model.predict(X_test) - y_test).mean(0)
    print errors
    # save_model(model, errors)
