import os
import cPickle
import logging

from django.core.management.base import BaseCommand
from django.core.files import File
import numpy
from sklearn import svm
from sklearn.model_selection import GridSearchCV, train_test_split

from chemtools.ml import MultiStageRegression
from data.models import DataPoint, Predictor
from project.utils import StringIO


logger = logging.getLogger(__name__)


def lock(func):
    def wrapper(*args, **kwargs):
        # Not very safe, but it will work well enough
        if os.path.exists(".updating_ml"):
            logger.info("Already Running")
            return
        with open(".updating_ml", "w"):
            try:
                value = func(*args, **kwargs)
            except Exception as e:
                logger.info("Exception: %s" % e)
                value = None
        os.remove(".updating_ml")
        return value
    return wrapper


class Command(BaseCommand):
    args = 'force'
    help = 'Update ML data'

    def handle(self, *args, **options):
        if not len(args):
            force = False
        else:
            force = bool(args[0])
        run_all(force=force)


def save_model(model, errors):
    logger.info("Saving Model")
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
def run_all(force=False):
    pred = Predictor.objects.latest()
    latest = DataPoint.objects.latest()

    if not force and latest.created < pred.created:
        logger.info("No Update")
        return

    logger.info("Loading Data")
    X, HOMO, LUMO, GAP = DataPoint.get_all_data()
    y = numpy.hstack([HOMO, LUMO, GAP])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)
    logger.info("Building Model")
    params = {"gamma": [1e-5, 1e-3, 1e-1, 1e1, 1e3],
              "C": [1e-5, 1e-3, 1e-1, 1e1, 1e3]}
    inner_model = GridSearchCV(estimator=svm.SVR(kernel="rbf"),
                               param_grid=params)
    model = MultiStageRegression(model=inner_model)
    model.fit(X_train, y_train)

    errors = numpy.abs(model.predict(X_test) - y_test).mean(0)
    logger.info("Errors: %s" % errors)
    save_model(model, errors)
