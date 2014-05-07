from itertools import izip
from operator import itemgetter

import numpy as np
from scipy.sparse import csr_matrix

from ghanalyzer.utils.datatools import slide


class JaccardSimilarity(object):
    def __init__(self, features):
        self.features = features.tocsr()
        self.size, _ = self.features.shape
        self._initialize_similarity()

    def _initialize_similarity(self):
        features = self.features.tocsc()
        
        # count the number of object pairs sharing a certain feature
        pair_count = sum((end-start)**2 for start, end in slide(features.indptr, 2))

        row = np.zeros((pair_count,), dtype=int)
        col = np.zeros((pair_count,), dtype=int)
        s = 0
        for start, end in slide(features.indptr, 2):
            object_ids = features.indices[start:end]
            step = len(object_ids)
            # store all object pairs sharing the feature
            for x in object_ids:
                row[s:s+step] = x
                col[s:s+step] = object_ids
                s += step
        data = np.ones((pair_count,))
        
        similarities = csr_matrix((data, (row, col)), shape=(self.size, self.size))
        del row, col, data

        features = self.features.tocsr()
        indptr = features.indptr
        indices = features.indices
        coo = similarities.tocoo()
        for i, (u, v) in enumerate(izip(coo.row, coo.col)):
            u_start, u_end = indptr[u], indptr[u+1]
            v_start, v_end = indptr[v], indptr[v+1]
            uv = set(indices[u_start:u_end]) | set(indices[v_start:v_end])
            coo.data[i] /= float(len(uv))

        self.similarities = similarities

    def __getitem__(self, pair):
        return self.similarities[pair]

    def measure(self, u):
        start, end = self.similarities.indptr[u:u+2]
        return list(izip(self.similarities.indices[start:end],
            self.similarities.data[start:end]))

    def nearest(self, u, k):
        neighbors = sorted(self.measure(u), key=itemgetter(1), reverse=True)
        neighbors = list((v, s) for v, s in neighbors if v != u)
        k = min(k, len(neighbors))
        return neighbors[:k]
