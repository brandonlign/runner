import numpy as np
import representation
import margin
ITERATIONS = 1000

def expected(hard, ranks, measurements, support, base, y, folds, groups):
    total = np.zeros(226, float)
    first_seed = None
    last_seed = None
    for r in range(ITERATIONS):
        X, seed = representation.build(hard, ranks, measurements, support, base, r)
        total += margin.compute(X, y, folds, groups)
        if first_seed is None:
            first_seed = int(seed)
        last_seed = int(seed)
        if r == 0 or (r + 1) % 25 == 0:
            print(f'measurement-marginalization clone {r+1}/{ITERATIONS}', flush=True)
    out = total / float(ITERATIONS)
    assert np.isfinite(out).all()
    return out, first_seed, last_seed
