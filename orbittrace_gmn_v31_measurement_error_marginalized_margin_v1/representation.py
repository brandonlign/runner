import numpy as np
import run_urc_union_ranker as q
import cloned_catalogue

def build(hard, ranks, measurements, support, base, iteration):
    fams, lookup, seed = cloned_catalogue.make(hard, measurements, support, iteration)
    centroids = q.centroid_matrix(fams)
    neighbors = q.neighbor_features(centroids)
    rows = []
    for i, fam in enumerate(fams):
        a = list(map(float, q.v1.structural_features(fam, ranks)[1:11]))
        b = list(map(float, q.v2.cohesion_features(fam, lookup, support, base)))
        c = list(map(float, neighbors[i]))
        rows.append(a + b + c)
    matrix = np.asarray(rows, dtype=float)
    assert matrix.shape == (226, 23)
    assert np.isfinite(matrix).all()
    return matrix, seed
