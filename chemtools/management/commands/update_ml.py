import os
import itertools
import cPickle

from django.core.management.base import BaseCommand
from django.core.files import File
import numpy
from sklearn import svm
from sklearn import cross_validation
from sklearn.metrics import mean_absolute_error

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


def test_clf_kfold(X, y, clf, folds=5):
    train = numpy.zeros(folds)
    cross = numpy.zeros(folds)
    folds = cross_validation.KFold(y.shape[0], n_folds=folds)
    for i, (train_idx, test_idx) in enumerate(folds):
        X_train = X[train_idx]
        X_test = X[test_idx]
        y_train = y[train_idx].T.tolist()[0]
        y_test = y[test_idx].T.tolist()[0]
        clf.fit(X_train, y_train)
        train[i] = mean_absolute_error(clf.predict(X_train), y_train)
        cross[i] = mean_absolute_error(clf.predict(X_test), y_test)
    return (train.mean(), train.std()), (cross.mean(), cross.std())


def scan(X, y, function, params):
    size = [len(x) for x in params.values()]
    train_results = numpy.zeros(size)
    test_results = numpy.zeros(size)
    keys = params.keys()
    values = params.values()
    for group in itertools.product(*values):
        idx = tuple([a.index(b) for a, b in zip(values, group) if len(a) > 1])
        a = dict(zip(keys, group))
        clf = function(**a)
        train, test = test_clf_kfold(X, y, clf)
        train_results[idx] = train[0]
        test_results[idx] = test[0]
    return train_results, test_results


class MultiStageRegression(object):
    def __init__(self, model=svm.SVR):
        self.model = model
        self._first_layer = None
        self._second_layer = None

    def fit(self, X, y, sample_weight=None):
        if len(y.shape) == 1:
            y = y.reshape(y.shape[0], 1)

        self._first_layer = []
        predictions = []
        for i in xrange(y.shape[1]):
            m = self.model()
            m.fit(X, y[:, i])
            predictions.append(m.predict(X))
            self._first_layer.append(m)

        self._second_layer = []
        for i in xrange(y.shape[1]):
            added = predictions[:i] + predictions[i + 1:]
            X_new = numpy.hstack([X] + added)
            m = self.model()
            m.fit(X_new, y[:, i])
            self._second_layer.append(m)
        return self

    def predict(self, X):
        if self._models is None:
            raise ValueError("Model has not been fit")
        predictions = []
        for model in self._models[0]:
            predictions.append(model.predict(X))

        res = []
        for i in xrange(len(predictions)):
            added = predictions[:i] + predictions[i + 1:]
            X_new = numpy.hstack([X] + added)
            m = self._models[1][i]
            res.append(m.predict(X_new))
        return numpy.array(res)


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


@lock
def run_all():
    pred = Predictor.objects.latest()
    latest = DataPoint.objects.latest()

    if latest.created < pred.created:
        print "No Update"
        return

    print "Loading Data"
    X, HOMO, LUMO, GAP = DataPoint.get_all_data()
    model = MultiStageRegression()
    y = numpy.hstack([HOMO, LUMO, GAP])

    n = X.shape[0]
    split = int(0.9 * n)
    idxs = np.arange(n)
    np.random.shuffle(idxs)
    train_idx = idxs[:split]
    test_idx = idxs[split:]
    X_train = X[train_idx, :]
    X_test = X[test_idx, :]
    y_train = y[train_idx, :]
    y_test = y[test_idx, :]

    model.fit(X_train, y_train)
    errors = np.abs(model.predict(X_test) - y_test).mean(0)
    save_model(model, errors)

