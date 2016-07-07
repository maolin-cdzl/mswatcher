# -*- coding: UTF-8 -*-
MAX_DROPOUT = 100
MAX_MISORDER = 10

class Source:
    def __init__(self):
        self.init = True
        self.base_seq = 0
        self.bad_seq = 0
        self.max_seq = 0
        self.received = 0           # packets received
        self.expected_prior = 0     # packet expected at last interval
        self.received_prior = 0     # packet received at last interval
        self.transit = 0            # relative trans time for prev pkt
        self.jitter = 0             # estimated jitter

    def init_seq(self,seq):
        self.init = False
        self.base_seq = seq
        self.max_seq = seq
        self.received = 0
        self.received_prior = 0
        self.expected_prior = 0

    def update_seq(self,seq):
        if self.init:
            self.init_seq(seq)
            self.max_seq = seq - 1
        udelta = seq - self.max_seq

        if udelta > 0:
            if udelta < MAX_DROPOUT:
                self.max_seq = seq
            else:
                if seq == self.bad_seq:
                    self.init_seq(seq)
                else:
                    self.bad_seq = seq + 1
                return
        elif udelta < 0:
            udelta = abs(udelta)
            if udelta > MAX_MISORDER:
                if seq == self.bad_seq:
                    self.init_seq(seq)
                else:
                    self.bad_seq = seq + 1
                return
        else:
            # duplicate or reordered packet
            pass
        self.received += 1

    def expected(self):
        return self.max_seq - self.base_seq + 1

    def lost(self):
        return self.expected() - self.received

    '''
        The resulting fraction is an 8-bit fixed point number with the binary
        point at the left edge
    '''
    def lost_fraction(self):
        expected = self.expected()
        expected_interval = expected - self.expected_prior
        self.expected_prior = expected

        received_interval = self.received - self.received_prior
        self.received_prior = self.received

        lost_interval = expected_interval - received_interval
        if expected_interval == 0 or lost_interval <= 0:
            return 0
        else:
            return float(lost_interval) / float(expected_interval)


