# NASA ASFN WGN publication-only availability audit v1 — result

**Classification: POSITIVE preaccess documentation result. ASFN event bytes remain untouched.**

Binding run: `31834078469`  
Artifact: `9231801482`  
Artifact digest: `sha256:7df9691e1cc6a135eb3ca29d50dac2864a39e33b5e3521cb56a55e5e5cabdb81`  
Official IMO WGN 2020 archive SHA-256: `7e792429ec155c4f74b8d4eae28da6d95fd134e4e2fd1d18bc1d3e26ebfdab1b`  
Matching WGN 48:3 issue SHA-256: `ce1a457502de6251d5b18d3c6bec8422e120be64e9414baf9d570dd1a332e8c5`

The audit downloaded only the exact public IMO WGN 2020 archive and inspected the primary Kingery et al. (2020) publication. It did not contact the NASA fireball site or any ASFN event/bulk-data object.

## Primary-paper bulk release documentation

The paper states that the release is limited to meteors observed from **2013-01-01 through 2019-12-31 inclusive** and that the data are provided in:

`nasfn_2013-2019_data.txt`

with accompanying documentation:

`nasfn_2013-2019_readme.txt`

The exact primary-paper footnote gives the bulk archive target:

`https://fireballs.ndc.nasa.gov/public_data/nasfn_2013-2019.zip`

This target was **not followed** by the publication audit.

## Recurrent-EOM input compatibility from primary documentation

The same publication documents the fields needed by the frozen recurrent-EOM GEO6 representation:

- observation date/time;
- solar longitude `slon`;
- geocentric meteor radiant;
- geocentric speed `v_g`;
- geocentric radiant as RA/Dec and equivalent ecliptic longitude/latitude;
- the paper explicitly states that subtracting solar longitude from geocentric ecliptic longitude yields a Sun-centered ecliptic radiant.

Therefore the published release is **field-compatible without fitted or event-informed calibration** with recurrent-EOM's frozen solar-longitude / Sun-centered radiant / geocentric-speed inputs.

The paper also warns that geocentric radiants/orbital elements are absent for in-atmosphere speed below 13 km/s and are represented by zero values; handling of such documented missing/invalid geocentric solutions must be frozen before data-body access rather than chosen after inspecting rows.

## Binding gate

Verdict:

`PASS_NASA_ASFN_WGN_BULK_RELEASE_DOCUMENTED`

The next authorized step is only a separately frozen structure/HEAD/schema audit of the exact primary-paper bulk target. No GET of the ZIP or scientific event values is authorized by this result alone.

## Firewall

- `wgn_publication_access=true`
- `asfn_event_data_access=false`
- `asfn_bulk_catalogue_access=false`
- `fireballs_site_access=false`
- `discovered_links_followed=false`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
