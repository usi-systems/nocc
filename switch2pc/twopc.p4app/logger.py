import time
import json
import threading
import os
from Queue import Queue, Empty

class Logger:
    def __init__(self, filename, stdout=False, append=False):
        mode = os.O_CREAT | os.O_WRONLY
        if append: mode = mode | os.O_APPEND
        self.logfile = os.fdopen(os.open(filename, mode, 0666), 'a' if append else 'w')
        self.stdout = stdout
        self.last_log = 0
        self.connected_cnt = 0
        self.q = Queue()

        t = threading.Thread(target=self.logthread)
        t.daemon = False
        t.start()

    def logthread(self):
        while True:
            try:
                x = self.q.get(True, 2)
            except Empty:
                if time.time() - self.last_log > 5: self._log("heartbeat")
                self.logfile.flush()
                continue

            if x is None:
                self.logfile.flush()
                self.logfile.close()
                break

            args, kwargs = x
            self._log(*args, **kwargs)

    def open(self):
        self.connected_cnt += 1

    def log(self, *args, **kwargs):
        self.q.put((args, kwargs))

    def _log(self, *args, **kwargs):
        self.last_log = time.time()
        l = dict(time=self.last_log)
        if len(args): l.update(dict(event=args[0]))
        if len(args) > 1: l.update(dict(data=' '.join(args[1:])))
        l.update(kwargs)
        line = json.dumps(l, ensure_ascii=False, default=lambda x: dict(x), sort_keys=True)
        line = line.replace('\\u0000', '') # strip all null chars
        if self.stdout:
            print line
        self.logfile.write(line + "\n")

    def close(self):
        self.connected_cnt -= 1
        if self.connected_cnt > 0: return
        self.q.put(None)

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
