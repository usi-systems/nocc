# Source: https://gist.github.com/lemiant/10660092

import threading
class ReadWriteLock(object):
    """ An implementation of a read-write lock for Python.
    Any number of readers can work simultaneously but they
    are mutually exclusive with any writers (which can
    only have one at a time).

    This implementation is reader biased. This can be harmful
    under heavy load because it can starve writers.
    However under light load it will be quite perfomant since
    reads are usually much less resource intensive than writes,
    and because it maximizes concurrency.
    """


    def __init__(self):
        self.__monitor = threading.Lock()
        self.__exclude = threading.Lock()
        self.readers = 0


    def acquire_read(self):
        with self.__monitor:
            self.readers += 1
            if self.readers == 1:
                self.__exclude.acquire()

    def release_read(self):
        with self.__monitor:
            self.readers -= 1
            if self.readers == 0:
                self.__exclude.release()


    def acquire_write(self):
        self.__exclude.acquire()

    def release_write(self):
        self.__exclude.release()
