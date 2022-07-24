import logging
from multiprocessing import current_process


def getSubProcessLogger():
    return logging.getLogger('GLAIVE.' + __name__ + ' | ' + current_process().name)