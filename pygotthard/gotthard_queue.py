from gotthard import *

R, W, RB = GotthardClient.R, GotthardClient.W, GotthardClient.RB

class GotthardQueue:

    def __init__(self, cl, size=20):
        self.cl = cl
        self.size = size
        if self.cl.closed: self.cl.open()
        res = self.cl.req(RB(1, ''), W(1, '0 0 0'))
        self.meta = res.op(k=1).value
        self.count, _, _ = self._unpack_meta(self.meta)

    def _pack_meta(self, count, head, tail):
        return ' '.join(map(str, [count, head, tail]))

    def _unpack_meta(self, s):
        count, head, tail = map(int, s.rstrip('\0').split(' '))
        return (count, head, tail)

    def push(self, v):
        while True:
            self.count, head, tail = self._unpack_meta(self.meta)
            assert self.count+1 <= self.size

            new_head = (head + 1) % self.size
            new_meta = self._pack_meta(self.count+1, new_head, new_head if self.count == 0 else tail)

            res = self.cl.req(RB(1, self.meta), W(1, new_meta), W(new_head+2, v))
            self.meta = new_meta

            if res.status == STATUS_OK:
                break
            else:
                self.meta = res.op(k=1).value

    def pop(self):
        while True:
            self.count, head, tail = self._unpack_meta(self.meta)

            if self.count == 0:
                return None

            new_tail = (tail + 1) % self.size
            new_meta = self._pack_meta(self.count-1, head, new_tail)

            res = self.cl.req(RB(1, self.meta), W(1, new_meta), R(tail+2))
            self.meta = res.op(k=1).value

            if res.status != STATUS_OK:
                continue

            return res.op(k=tail+2).value.rstrip('\0')


if __name__ == '__main__':
    logger = GotthardLogger('/dev/null', stdout=False)
    with GotthardClient(store_addr=('127.0.0.1', 9999), logger=logger) as cl:
        assert cl.reset().status == STATUS_OK

        gq = GotthardQueue(cl, size=4)

        assert gq.pop() == None

        gq.push('a')
        assert gq.pop() == 'a'

        gq.push('a')
        gq.push('b')
        gq.push('c')
        assert gq.pop() == 'a'
        assert gq.pop() == 'b'
        assert gq.pop() == 'c'

        gq.push('a')
        gq.push('b')
        assert gq.pop() == 'a'
        gq.push('c')
        gq.push('d')
        assert gq.pop() == 'b'
        assert gq.pop() == 'c'
        assert gq.pop() == 'd'

        for n in xrange(gq.size):
            gq.push(str(n))
        for n in xrange(gq.size):
            assert gq.pop() == str(n)

        for n in xrange(gq.size):
            gq.push(str(n))
        assert gq.pop() == str(0)
        gq.push(str(gq.size))
        assert gq.pop() == str(1)
        for n in xrange(2, gq.size+1):
            assert gq.pop() == str(n)

