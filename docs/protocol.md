# BSHwfth advertisement format (reverse engineered)

Status: partially understood. Everything below comes from passive Bleak captures
on 2026-10-26 of one NEFF Z1365WX0 probe, compared with the temperature shown in
the Home Connect app. Nothing here is based on documentation from BSH or NEFF.

## Transport

- Local name `BSHwfth`, sent in the scan response (active scanning needed).
- Not connectable in the observed states. The integration never connects.
- The probe only advertises while it is out of its charger. In the charger it
  is usually silent or sends room temperature.
- A distance test (moving only the probe vs. only the charger) showed the
  signal follows the probe, so the probe itself is the sender.
- Observed interval between changed packets: about 10–60 s. Some stacks repeat
  the last cached packet with RSSI −127; those are ignored.

## Payload

One AD structure of type `0xFF` (manufacturer specific data), 14 bytes after
the type byte. Offsets below include the two bytes that BLE stacks expose as
the "company identifier" (little endian).

| Offset | Example | Meaning |
| --- | --- | --- |
| 0–3 | `1e 20 20 20` | Four measuring points, unsigned, whole °C. Which point is the tip is not confirmed. |
| 4 | `1b` | Unknown, follows temperature loosely (ambient/handle?) |
| 5 | `00` | Always 0 – used as format check |
| 6 | `21` | Unknown; once matched the value shown in the app exactly |
| 7 | `0b` | Unknown, varies (signed?) |
| 8 | `06` | Unknown, `05`/`06` |
| 9–13 | `08 08 a6 02 00` | Constant on the tested probe (model, firmware or serial?) |

Because offsets 0–1 are temperatures, the "company identifier" reported by
Windows/BlueZ changes all the time (`0x1616`, `0x1718`, `0x1a1a`, …). Home
Assistant merges manufacturer data per identifier across packets, so the
integration decodes the raw advertisement bytes when they are available.

## Verified range

Tested from room temperature to above 100 °C in an oven set to 180 °C:
channel values above 100 °C (up to 107 °C) were reported and rose
continuously, offset 4 read 176–184 throughout, and reception through the
closed oven door was −80 to −94 dBm without gaps. Behaviour below 0 °C and of
the station's own advertisements (if any) is unknown.

## Test data

`tests/fixtures/probe_packets.json` contains every distinct probe packet from
the captures, with the address removed and offsets 9–13 masked.
