import time

def waitForTcpPort(port, timeout=20, poll=0.1):
    start = time.time()
    with open('/proc/net/tcp', 'r') as f4, open(
            '/proc/net/tcp6', 'r') as f6:
        while True:
            f4.seek(0)
            f6.seek(0)
            lines = f4.readlines()[1:] + f6.readlines()[1:]
            sockets = map(str.split, lines)
            listeners = [l for l in sockets if l[3] == '0A']
            ports = [int(l[1].split(':')[1], 16) for l in listeners]
            if port in ports:
                break
            time.sleep(poll)
            if time.time() - start > timeout:
                raise Exception("Timed out waiting (>%gs) for TCP port %d"
                        % (timeout, port))
