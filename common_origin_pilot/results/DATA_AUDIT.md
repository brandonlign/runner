# Common-origin pilot data audit

**Verdict:** `DATA_LABEL_GATE_NO_GO`

This audit checks whether the public IAU MDC video-orbit catalogues expose usable shower-association labels in at least two independent networks.

## CAMS

- Rows: **53,401**
- Columns: `IID, DB, IC, Ano, Yr, Mn, Dayy, delta_Dayy, LS, delta_LS, mv, delta_mv, HB, delta_HB, HM, delta_HM, HE, delta_HE, RA, delta_RA, DECL, delta_DECL, Vi, delta_Vi, Vg, delta_Vg, Vh, delta_Vh, cZ, delta_cZ, Qm, q, delta_q, e, delta_e, a1, delta_a1, a, delta_a, Qa, delta_Qa, i, delta_i, arg, delta_arg, nod, delta_nod, pi, delta_pi, sh, Mas, delta_Mas, lgM, delta_lgM, cor, crh, mr, delta_mr, Hrf, delta_Hrf, LpA, delta_LpA, dur`
- Best label candidate: `sh`
- Known-code hits: **0**
- Recognized codes: `{}`

## CAMS

- Rows: **110,352**
- Columns: `IID, DB, IC, Ano, Yr, Mn, Dayy, delta_Dayy, LS, delta_LS, mv, delta_mv, HB, delta_HB, HM, delta_HM, HE, delta_HE, RA, delta_RA, DECL, delta_DECL, Vi, delta_Vi, Vg, delta_Vg, Vh, delta_Vh, cZ, delta_cZ, Qm, q, delta_q, e, delta_e, a1, delta_a1, a, delta_a, Qa, delta_Qa, i, delta_i, arg, delta_arg, nod, delta_nod, pi, delta_pi, sh, Mas, delta_Mas, lgM, delta_lgM, cor, crh, mr, delta_mr, Hrf, delta_Hrf, LpA, delta_LpA, dur`
- Best label candidate: `sh`
- Known-code hits: **0**
- Recognized codes: `{}`

## SonotaCo

- Rows: **29,200**
- Columns: `IID, DB, IC, Ano, Yr, Mn, Dayy, delta_Dayy, LS, delta_LS, mv, delta_mv, HB, delta_HB, HM, delta_HM, HE, delta_HE, RA, delta_RA, DECL, delta_DECL, Vi, delta_Vi, Vg, delta_Vg, Vh, delta_Vh, cZ, delta_cZ, Qm, q, delta_q, e, delta_e, a1, delta_a1, a, delta_a, Qa, delta_Qa, i, delta_i, arg, delta_arg, nod, delta_nod, pi, delta_pi, sh, Mas, delta_Mas, lgM, delta_lgM, cor, crh, mr, delta_mr, Hrf, delta_Hrf, LpA, delta_LpA, dur`
- Best label candidate: `sh`
- Known-code hits: **0**
- Recognized codes: `{}`

## SonotaCo

- Rows: **47,087**
- Columns: `IID, DB, IC, Ano, Yr, Mn, Dayy, delta_Dayy, LS, delta_LS, mv, delta_mv, HB, delta_HB, HM, delta_HM, HE, delta_HE, RA, delta_RA, DECL, delta_DECL, Vi, delta_Vi, Vg, delta_Vg, Vh, delta_Vh, cZ, delta_cZ, Qm, q, delta_q, e, delta_e, a1, delta_a1, a, delta_a, Qa, delta_Qa, i, delta_i, arg, delta_arg, nod, delta_nod, pi, delta_pi, sh, Mas, delta_Mas, lgM, delta_lgM, cor, crh, mr, delta_mr, Hrf, delta_Hrf, LpA, delta_LpA, dur`
- Best label candidate: `sh`
- Known-code hits: **0**
- Recognized codes: `{}`

## EDMOND

- Rows: **45,293**
- Columns: `_Version, _#, _localtime, _mjd, _sol, _ID1, _ID2, _amag, _ra_o, _dc_o, _ra_t, _dc_t, _elng, _elat, _vo, _vi, _vg, _vs, _a, _q, _e, _p, _peri, _node, _incl, _stream, _dr, _dv%, _mag, _Qo, _dur, _av, _Voa, _Pra, _Pdc, _GPlng, _GPlat, _ra1, _dc1, _az1, _ev1, _lng1, _lat1, _H1, _LD1, _Qr1, _Qd1, _ra2, _dc2, _lng2, _lat2, _H2, _LD2, _Qr2, _Qd2, _LD21, _az1r, _ev1r, _evro, _evrt, _Nts, _Nos, _leap, _rstar, _ddeg, _cdeg, _drop, _inout, _tme, _dt, _GD, _Qc, _dGP, _Gm%, _dv12%, _zmv, _Ed, _Ex, _QA, _Y_ut, _M_ut, _D_ut, _h_ut, _m_ut, _s_ut, _No, _Qp`
- Best label candidate: `_stream`
- Known-code hits: **11,573**
- Recognized codes: `{'PER': 5458, 'GEM': 2493, 'ORI': 1036, 'STA': 603, 'NTA': 439, 'QUA': 417, 'ETA': 287, 'CAP': 278, 'LEO': 215, 'LYR': 214, 'URS': 91, 'AND': 19, 'DRA': 10, 'TAH': 7, 'CAM': 3, 'JBO': 3}`

## EDMOND

- Rows: **141**
- Columns: `_Version, _#, _localtime, _mjd, _sol, _ID1, _ID2, _amag, _ra_o, _dc_o, _ra_t, _dc_t, _elng, _elat, _vo, _vi, _vg, _vs, _a, _q, _e, _p, _peri, _node, _incl, _stream, _dr, _dv%, _mag, _Qo, _dur, _av, _Voa, _Pra, _Pdc, _GPlng, _GPlat, _ra1, _dc1, _az1, _ev1, _lng1, _lat1, _H1, _LD1, _Qr1, _Qd1, _ra2, _dc2, _lng2, _lat2, _H2, _LD2, _Qr2, _Qd2, _LD21, _az1r, _ev1r, _evro, _evrt, _Nts, _Nos, _leap, _rstar, _ddeg, _cdeg, _drop, _inout, _tme, _dt, _GD, _Qc, _dGP, _Gm%, _dv12%, _zmv, _Ed, _Ex, _QA, _Y_ut, _M_ut, _D_ut, _h_ut, _m_ut, _s_ut, _No, _Qp`
- Best label candidate: `_stream`
- Known-code hits: **10**
- Recognized codes: `{'QUA': 9, 'URS': 1}`

## Interpretation boundary

Passing this gate means a parent-body-disjoint empirical/surrogate simulation pilot can be constructed. It does not mean that the public labels are perfect, that the parent mappings are unambiguous, or that a learned metric will outperform D-criteria.
