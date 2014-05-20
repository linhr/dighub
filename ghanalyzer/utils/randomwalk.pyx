from collections import defaultdict

import numpy as np
cimport numpy as np


def update_rank_numpy(
        np.ndarray[np.float_t, ndim=1] rank, int u,
        np.ndarray[np.int_t, ndim=1] degrees,
        np.ndarray[np.int_t, ndim=1] row, np.ndarray[np.int_t, ndim=1] col,
        np.ndarray[np.float_t, ndim=1] edge_weights,
        float alpha):
    cdef int r = row.shape[0]
    cdef int c = col.shape[0]
    cdef int count = min(r, c)
    cdef int i, a, b
    cdef np.ndarray[np.float_t, ndim=1] updated = np.zeros((rank.shape[0],), dtype=rank.dtype)

    for i in xrange(count):
        a, b = row[i], col[i]
        updated[b] += alpha * rank[a] * edge_weights[i] / degrees[a]
    updated[u] += 1 - alpha
    
    return updated
