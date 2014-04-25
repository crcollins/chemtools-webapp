import os
import itertools
import cPickle
import datetime
import pytz
import shutil
import time

import numpy
import scipy.optimize
from sklearn import svm
from sklearn import cross_validation
from sklearn.metrics import mean_absolute_error

from constants import DATAPATH
from data.models import DataPoint
from project.utils import touch


def test_clf_kfold(X, y, clf, folds=10):
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
        idx = tuple([a.index(b) for a,b in zip(values, group) if len(a) > 1])
        a = dict(zip(keys, group))
        clf = function(**a)
        train, test = test_clf_kfold(X, y, clf)
        train_results[idx] = train[0]
        test_results[idx] = test[0]
    return train_results, test_results


class OptimizedCLF(object):
    def __init__(self, X, y, func, params):
        self.params = params
        self.func = func
        self.X = X
        self.y = y
        self.optimized_clf = None
        self.optimized_params = None

    def __call__(self, *args):
        a = dict(zip(self.params.keys(), *args))
        clf = self.func(**a)
        train, test = test_clf_kfold(self.X, self.y, clf, folds=5)
        return test[0]

    def get_optimized_clf(self):
        if not len(self.params.keys()):
            self.optimized_clf = self.func()
        if self.optimized_clf is not None:
            return self.optimized_clf
        items = self.params.items()
        types = set([list, tuple])
        listparams = dict((k,v) for k,v in items if type(v) in types)
        itemparams = dict((k,v) for k,v in items if type(v) not in types)
        listvalues = []
        itemvalues = []
        if listparams:
            _, test = scan(self.X, self.y, self.func, listparams)
            listvalues = []
            temp = numpy.unravel_index(test.argmin(), test.shape)
            for i, pick in enumerate(listparams.values()):
                listvalues.append(pick[temp[i]])
            listvalues = listvalues[::-1]
        if itemparams:
            bounds = ((1e-8, None), ) * len(self.params.keys())
            results = scipy.optimize.fmin_l_bfgs_b(
                self, self.params.values(),
                bounds=bounds,
                approx_grad=True, epsilon=1e-3)
            itemvalues = results[0].tolist()
        keys = listparams.keys() + itemparams.keys()
        values = listvalues + itemvalues
        self.optimized_params = dict(zip(keys, values))
        self.optimized_clf = self.func(**self.optimized_params)
        return self.optimized_clf


def fit_func(X, y, clf=None):
    func = svm.SVR
    if clf is None:
        params = {"C": 10, "gamma": 0.05}
    else:
        params = {"C": clf.C, "gamma": clf.gamma}

    clf = OptimizedCLF(X, y, func, params).get_optimized_clf()
    train, test = test_clf_kfold(X, y, clf, folds=10)
    clf.test_error = test
    return clf


def get_first_layer(X, homo, lumo, gap, in_clfs=None):
    if in_clfs is not None:
        in_homo_clf, in_lumo_clf, in_gap_clf = in_clfs
    else:
        in_homo_clf, in_lumo_clf, in_gap_clf = [None] * 3

    homo_clf = fit_func(X, homo, clf=in_homo_clf)
    lumo_clf = fit_func(X, lumo, clf=in_lumo_clf)
    gap_clf = fit_func(X, gap, clf=in_gap_clf)
    return homo_clf, lumo_clf, gap_clf


def get_second_layer(X, homo, lumo, gap, clfs, in_pred_clfs=None):
    if in_pred_clfs is not None:
        in_pred_homo, in_pred_lumo, in_pred_gap = in_pred_clfs
    else:
        in_pred_homo, in_pred_lumo, in_pred_gap = [None] * 3

    homo_clf, lumo_clf, gap_clf = clfs
    homop = numpy.matrix(homo_clf.predict(X)).T
    lumop = numpy.matrix(lumo_clf.predict(X)).T
    gapp = numpy.matrix(gap_clf.predict(X)).T

    X_homo = numpy.concatenate([X, lumop, gapp], 1)
    X_lumo = numpy.concatenate([X, gapp, homop], 1)
    X_gap = numpy.concatenate([X, homop, lumop], 1)

    pred_homo_clf = fit_func(X_homo, homo, clf=in_pred_homo)
    pred_lumo_clf = fit_func(X_lumo, lumo, clf=in_pred_lumo)
    pred_gap_clf = fit_func(X_gap, gap, clf=in_pred_gap)
    return pred_homo_clf, pred_lumo_clf, pred_gap_clf


def save_clfs(clfs, pred_clfs):
    path = path = os.path.join(DATAPATH, "decay_predictors.pkl")
    dst_path = os.path.join(DATAPATH, "decay_predictors_%d.pkl" % time.time())
    try:
        shutil.move(path, dst_path)
    except:
        pass
    with open(path, 'w') as f:
        cPickle.dump((clfs, pred_clfs), f, protocol=-1)


def load_clfs():
    clfs = []
    pred_clfs = []
    path = os.path.join(DATAPATH, "decay_predictors.pkl")
    try:
        with open(path, 'rb') as f:
            clfs, pred_clfs = cPickle.load(f)
    except OSError:
        pass
    except IOError:
        pass

    if len(clfs) < 3 or len(pred_clfs) < 3:
        clfs = None
        pred_clfs = None
    return clfs, pred_clfs


def run_all():
    FEATURE, HOMO, LUMO, GAP = DataPoint.get_all_data()
    latest = DataPoint.objects.latest()
    path = os.path.join(DATAPATH, "decay_predictors.pkl")
    try:
        mtime = os.path.getmtime(path)
        temp = datetime.datetime.fromtimestamp(mtime)
        last_update = pytz.utc.localize(temp)
        if latest.created < last_update:
            return
    except OSError:
        pass
    except IOError:
        pass

    in_clfs, in_pred_clfs = load_clfs()
    clfs = get_first_layer(FEATURE, HOMO, LUMO, GAP, in_clfs)
    pred_clfs = get_second_layer(FEATURE, HOMO, LUMO, GAP, clfs, in_pred_clfs)
    save_clfs(clfs, pred_clfs)


if __name__ == "__main__":
    run_all()
