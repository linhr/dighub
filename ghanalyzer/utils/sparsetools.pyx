import numpy as np
from scipy.sparse import coo_matrix
cimport numpy as np


def vector_coo_matrix_multiply(np.ndarray[np.float_t, ndim=1] v, M):
    """
    calculate v * M given row vector v and coo_matrix M
    """
    cdef np.ndarray[int, ndim=1] row = M.row
    cdef np.ndarray[int, ndim=1] col = M.col
    cdef np.ndarray[np.float_t, ndim=1] data = M.data
    cdef int length = v.shape[0]
    cdef np.ndarray[np.float_t, ndim=1] product = np.zeros((length,))
    cdef int r, c, i

    for i in xrange(data.size):
        r, c = row[i], col[i]
        product[c] += v[r] * data[i]

    return product


def coo_matrix_scale_row(M, np.ndarray[np.float_t, ndim=1] s, inplace=False):
    cdef np.ndarray[int, ndim=1] row = M.row
    cdef np.ndarray[int, ndim=1] col = M.col
    cdef np.ndarray[np.float_t, ndim=1] data = np.array(M.data, copy=not inplace)
    cdef int i

    for i in xrange(data.size):
        data[i] *= s[row[i]]

    if inplace:
        return M
    return coo_matrix((data, (row, col)), shape=M.shape)


def sum_coo_matrix_column(M):
    cdef np.ndarray[int, ndim=1] row = M.row
    cdef np.ndarray[np.float_t, ndim=1] data = M.data
    cdef np.ndarray[np.float_t, ndim=1] result = np.zeros((M.shape[0],))
    cdef int i

    for i in xrange(data.size):
        result[row[i]] += data[i]

    return result
