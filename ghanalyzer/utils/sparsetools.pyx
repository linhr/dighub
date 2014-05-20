import numpy as np
from scipy.sparse import coo_matrix, csr_matrix
cimport numpy as np


def vector_coo_matrix_multiply(np.ndarray[np.float_t, ndim=1] v, M):
    """calculate v * M given row vector v and coo_matrix M"""
    cdef np.ndarray[int, ndim=1] row = M.row
    cdef np.ndarray[int, ndim=1] col = M.col
    cdef np.ndarray[np.float_t, ndim=1] data = M.data
    cdef np.ndarray[np.float_t, ndim=1] product = np.zeros((v.shape[0],))
    cdef int r, c, i

    for i in xrange(data.size):
        r, c = row[i], col[i]
        product[c] += v[r] * data[i]

    return product


def vector_csr_matrix_multiply(np.ndarray[np.float_t, ndim=1] v, M):
    """calculate v * M given row vector v and csr_matrix M"""
    cdef np.ndarray[int, ndim=1] indptr = M.indptr
    cdef np.ndarray[int, ndim=1] indices = M.indices
    cdef np.ndarray[np.float_t, ndim=1] data = M.data
    cdef np.ndarray[np.float_t, ndim=1] product = np.zeros((v.shape[0],))
    cdef int r, c, i

    for r in xrange(M.shape[0]):
        for i in xrange(indptr[r], indptr[r+1]):
            c = indices[i]
            product[c] += v[r] * data[i]

    return product


def coo_matrix_scale_row(M, np.ndarray[np.float_t, ndim=1] s, inplace=False):
    """scale M[r, :] by s[r] given 1-D array v and coo_matrix M"""
    cdef np.ndarray[int, ndim=1] row = M.row
    cdef np.ndarray[int, ndim=1] col = M.col
    cdef np.ndarray[np.float_t, ndim=1] data = np.array(M.data, copy=not inplace)
    cdef int i

    for i in xrange(data.size):
        data[i] *= s[row[i]]

    if inplace:
        return M
    return coo_matrix((data, (row, col)), shape=M.shape)


def csr_matrix_scale_row(M, np.ndarray[np.float_t, ndim=1] s, inplace=False):
    """scale M[r, :] by s[r] given 1-D array v and csr_matrix M"""
    cdef np.ndarray[int, ndim=1] indptr = M.indptr
    cdef np.ndarray[int, ndim=1] indices = M.indices
    cdef np.ndarray[np.float_t, ndim=1] data = np.array(M.data, copy=not inplace)
    cdef int r, i

    for r in xrange(M.shape[0]):
        for i in xrange(indptr[r], indptr[r+1]):
            data[i] *= s[r]

    if inplace:
        return M
    return csr_matrix((data, indices, indptr), shape=M.shape)


def sum_coo_matrix_column(M):
    cdef np.ndarray[int, ndim=1] row = M.row
    cdef np.ndarray[np.float_t, ndim=1] data = M.data
    cdef np.ndarray[np.float_t, ndim=1] result = np.zeros((M.shape[0],))
    cdef int i

    for i in xrange(data.size):
        result[row[i]] += data[i]

    return result


def sum_csr_matrix_column(M):
    cdef np.ndarray[int, ndim=1] indptr = M.indptr
    cdef np.ndarray[np.float_t, ndim=1] data = M.data
    cdef np.ndarray[np.float_t, ndim=1] result = np.zeros((M.shape[0],))
    cdef int r, i

    for r in xrange(M.shape[0]):
        for i in xrange(indptr[r], indptr[r+1]):
            result[r] += data[i]

    return result
