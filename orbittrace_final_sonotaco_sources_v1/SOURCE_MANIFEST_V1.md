# OrbitTrace final SonotaCo 2013/2014 source manifest — v1

## Status

This is a **metadata-only pre-access freeze**. It identifies the official permanent SonotaCo SNMv3 yearly sources for the already-fixed final literature-test years. It does not download either archive, inspect a CSV row, read a shower label, run a detector, or compute any performance value.

No alternative source, mirror, year, combined file, quality subset, or regenerated export may replace these yearly archives after scientific access begins.

## Official archive provenance

Authoritative public index: SonotaCo Network Meteor orbit data sets v3 (SNMv3), original SonotaCo Network archive page, with permanent IAU MDC mirror links.

### 2013

- final-test year: **2013**
- official yearly dataset name: `_U2_20130101_S.csv`
- permanent archive URL: `https://www.astro.sk/iaumdcDB/PDA/SNMv3/013a.zip`
- expected archive member path: `013a/_U2_20130101_S.csv` or, if the ZIP stores the CSV at its root, the unique basename `_U2_20130101_S.csv`
- public index orbit count: **26,855**
- public index published date: **18 July 2021**

### 2014

- final-test year: **2014**
- official yearly dataset name: `_U2_20140101_S.csv`
- permanent archive URL: `https://www.astro.sk/iaumdcDB/PDA/SNMv3/014a.zip`
- expected archive member path: `014a/_U2_20140101_S.csv` or, if the ZIP stores the CSV at its root, the unique basename `_U2_20140101_S.csv`
- public index orbit count: **22,079**
- public index published date: **18 July 2021**

## First-access integrity rule

Archive byte hashes and exact member byte hashes are intentionally **not guessed** before the authorized first download. On the one permitted final-test access, the execution workflow must:

1. download exactly the permanent URL above;
2. record the archive SHA-256 before extraction;
3. list ZIP members without selecting among multiple science CSVs by content;
4. require exactly one member whose basename equals the frozen yearly dataset name above;
5. record that member's full ZIP path and SHA-256;
6. require the frozen 45-field U2 schema through the already-audited final normalizer;
7. record physical row count and compare it with the public index orbit count as an integrity diagnostic;
8. freeze these hashes/paths before any detector output or truth read is interpreted.

A hash cannot be selected post hoc because there is only one frozen URL per year. If the permanent archive is unavailable, corrupt, contains no uniquely matching frozen member basename, or fails the frozen schema, the result is a structural/integrity failure—not permission to switch data sources after scientific access.

## Dataset role

These archives are the **single permanent SonotaCo 2013/2014 final matched literature-test panel**. They are not development data and may not be used for method selection, threshold selection, feature changes, comparator tuning, or validation-panel choice.

## Firewall

The metadata freeze authorizes no scientific access. Solar longitude 20°–55° remains sealed and must be removed by the final normalizer before any other scientific field is decoded. OrbitTrace reference information remains inaccessible.