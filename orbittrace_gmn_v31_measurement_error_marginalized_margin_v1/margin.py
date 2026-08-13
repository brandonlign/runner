import numpy as np

def compute(X, y, folds, groups):
    m = np.zeros(len(X), float)
    for f in range(5):
        tr = folds != f
        te = folds == f
        assert tr.any() and te.any()
        assert {groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]})
        mu = X[tr].mean(0)
        sd = X[tr].std(0)
        sd[sd == 0] = 1
        A = (X[tr] - mu) / sd
        B = (X[te] - mu) / sd
        P = A[y[tr]]
        N = A[~y[tr]]
        for j, i in enumerate(np.where(te)[0]):
            dp = np.linalg.norm(P - B[j], axis=1).min()
            dn = np.linalg.norm(N - B[j], axis=1).min()
            m[i] = dn - dp
    assert np.isfinite(m).all()
    return m
