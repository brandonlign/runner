# Audit-only correction — exclude prior freshness-audit machinery from exposure classification

The first CAMSv3 2017/2018 repository-history audit, Actions run `31204620525`, failed solely because source/workflow files from the immediately preceding CAMSv3 2016/2017 **freshness audit itself** contained literal `CAMSv3 2017` strings. Those files explicitly performed no meteor-archive access and are provenance/audit machinery, not scientific exposure.

The same first run found:

- all real historical CAMS dynamic ranges were `range(2010,2017)` or `range(2011,2017)`, which are half-open and therefore stop at 2016;
- CAMSv3 2018 had zero potential exposure hits;
- spent positive controls 2015 and 2016 were both correctly detected.

The corrected audit may classify paths under `orbittrace_multiplicity_camsv3_2016_2017_freshness_audit/` and its matching workflow as `prior_freshness_audit_only`. No real data-use path, archive reference, scientific workflow, dynamic range including a target year, or result artifact is excluded by this correction.

No CAMSv3 2017 or 2018 meteor archive is accessed by this correction.
