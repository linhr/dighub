from collections import defaultdict

import numpy as np
cimport numpy as np


def update_rank_numpy(
        np.ndarray[np.float_t, ndim=1] rank, np.ndarray[np.float_t, ndim=1] updated,
        int u, np.ndarray[np.int_t, ndim=1] degrees,
        np.ndarray[np.int_t, ndim=1] row, np.ndarray[np.int_t, ndim=1] col,
        float alpha):
    cdef int r = row.shape[0]
    cdef int c = col.shape[0]
    cdef int count = min(r, c)
    cdef int i, a, b

    for i in xrange(count):
        a, b = row[i], col[i]
        updated[a] += alpha * rank[b] / degrees[b]
    updated[u] += 1 - alpha
