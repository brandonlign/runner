"""Transport-only constants from frozen PR #1032 used by v33."""
ROUTES=('sugar','hdbscan')
YEARS=(2013,2014)
PANELS=(('sugar',2013),('sugar',2014),('hdbscan',2013),('hdbscan',2014))
V24_EXPECT={
    ('sugar',2013):(0.27806630131631344,16),
    ('sugar',2014):(0.32869544907104964,17),
    ('hdbscan',2013):(0.14257102406283795,10),
    ('hdbscan',2014):(0.12833942693327394,7),
}
