import logging

module_logger = logging.getLogger('exampleApp.otherMod2')


def add(x, y):
    logger = logging.getLogger('exampleApp.otherMod2.add')

    logger.info(f'added {x} and {y} to get {x + y}')

    return x + y
