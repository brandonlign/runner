# AMOS acquisition target

Fixed before receipt: complete multi-station AMOS solutions for calendar years 2023 and 2024.

Preferred transport is separated before delivery:

1. one minimal blinding-index CSV per year with exactly `event_id,utc_time,solar_longitude_deg`;
2. physical solutions in separate files keyed by the same stable event ID;
3. any shower associations in a third, separate ID mapping.

The committed `amos_blind_receipt_v1/blind_receipt.py` accepts only the minimal index, enforces the fixed year, rejects extra columns/duplicate IDs, and removes the inclusive 20.0-55.0 solar-longitude interval before later processing.

Physical solution fields requested after blinding are geocentric radiant, geocentric velocity, and a standard solution-quality flag. Request the complete solved sample, not only shower-associated meteors.

First use after receipt remains engineering/schema/capacity checking. No year switching or method tuning from received contents.