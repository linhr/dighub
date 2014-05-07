from itertools import islice


def islide(iterable, size):
    iterator = iter(iterable)
    window = tuple(islice(iterator, size))
    if len(window) == size:
        yield window
    for x in iterator:
        window = window[1:] + (x,)
        yield window

def slide(sequence, size):
    stop = len(sequence) - size + 1
    for i in xrange(stop):
        yield tuple(sequence[i:i+size])
