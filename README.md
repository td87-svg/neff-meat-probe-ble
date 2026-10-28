# NEFF Meat Probe (BLE) for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories/)
[![Validate](https://github.com/td87-svg/neff-meat-probe-ble/actions/workflows/validate.yml/badge.svg)](https://github.com/td87-svg/neff-meat-probe-ble/actions/workflows/validate.yml)
[![Tests](https://github.com/td87-svg/neff-meat-probe-ble/actions/workflows/tests.yml/badge.svg)](https://github.com/td87-svg/neff-meat-probe-ble/actions/workflows/tests.yml)

[Deutsch](#deutsch) · [English](#english)

---

## Deutsch

Bringt das kabellose NEFF-Bratenthermometer als Gerät mit Temperatursensoren in
Home Assistant.

Die Sonde funkt ihre Temperaturen ständig per Bluetooth. Home Assistant hört
diese Funkpakete einfach mit. **Kein Home Connect, kein Konto, keine Cloud, keine
Kopplung.** App und Ladestation funktionieren ganz normal weiter.

> [!IMPORTANT]
> **Du brauchst Bluetooth in der Nähe des Backofens:** entweder einen
> Bluetooth-Adapter am Home-Assistant-Rechner (wenn der in der Küche steht) oder
> einen [ESPHome-Bluetooth-Proxy](https://esphome.io/components/bluetooth_proxy.html)
> (z. B. ein günstiger ESP32) in der Küche.

### Installation

1. In HACS: Menü ⋮ → **Benutzerdefinierte Repositories** →
   `https://github.com/td87-svg/neff-meat-probe-ble`, Typ **Integration**.
2. **NEFF Meat Probe (BLE)** herunterladen, Home Assistant neu starten.
3. Sonde aus der Ladestation nehmen. Home Assistant meldet sie unter
   **Einstellungen → Geräte & Dienste** als gefunden – bestätigen, fertig.

Voraussetzung: Home Assistant 2026.10 oder neuer.

### Sensoren

| Sensor | Inhalt |
| --- | --- |
| Mittelwert | Durchschnitt der vier Messpunkte in °C |
| Kanal 1–4 | Die vier Messpunkte einzeln, Kanal 1 = Spitze, Kanal 4 = nahe am Griff (standardmäßig deaktiviert) |
| Umgebungstemperatur | Temperatur um die Sonde herum, im Ofen also etwa die Ofentemperatur (zeigt die Home-Connect-App nicht an) |
| Signalstärke | Empfangsstärke in dBm (standardmäßig deaktiviert) |
| Letztes gültiges Paket | Wann zuletzt Daten ankamen |

Liegt die Sonde in der Ladestation, sendet sie meist nichts. Nach fünf Minuten
ohne Daten werden die Temperaturen **nicht verfügbar** – keine Fehlermeldung,
keine veralteten Werte.

### Gut zu wissen

- Getestet mit **NEFF Z1365WX0**, auch im heißen Ofen (Messpunkte über 100 °C).
- Baugleiche Sonden von Bosch, Siemens oder Gaggenau funktionieren vermutlich
  auch (Bluetooth-Name `BSHwfth`) – Rückmeldung gern als Issue.
- Das Datenformat wurde per Reverse Engineering ermittelt. Inoffiziell, keine
  Verbindung zu BSH, NEFF oder Home Connect. Details: [docs/protocol.md](docs/protocol.md).

---

## English

Adds the NEFF wireless meat probe to Home Assistant as a device with temperature
sensors.

The probe constantly broadcasts its temperatures via Bluetooth. Home Assistant
simply listens in. **No Home Connect, no account, no cloud, no pairing.** The app
and charging station keep working as usual.

> [!IMPORTANT]
> **You need Bluetooth near the oven:** either a Bluetooth adapter on the Home
> Assistant machine (if it sits in the kitchen) or an
> [ESPHome Bluetooth proxy](https://esphome.io/components/bluetooth_proxy.html)
> (e.g. a cheap ESP32) in the kitchen.

### Installation

1. In HACS: menu ⋮ → **Custom repositories** →
   `https://github.com/td87-svg/neff-meat-probe-ble`, type **Integration**.
2. Download **NEFF Meat Probe (BLE)**, restart Home Assistant.
3. Take the probe out of its charger. Home Assistant shows it as discovered under
   **Settings → Devices & services** – confirm, done.

Requires Home Assistant 2026.10 or newer.

### Sensors

| Sensor | Content |
| --- | --- |
| Average | Mean of the four measuring points in °C |
| Channel 1–4 | Each measuring point, channel 1 = tip, channel 4 = near the handle (disabled by default) |
| Ambient temperature | Temperature around the probe, i.e. roughly the oven temperature (not shown in the Home Connect app) |
| Signal strength | Reception strength in dBm (disabled by default) |
| Last valid packet | When data last arrived |

While docked, the probe usually sends nothing. After five minutes without data
the temperatures become **unavailable** – no errors, no stale values.

### Good to know

- Tested with the **NEFF Z1365WX0**, including in a hot oven (measuring points
  above 100 °C).
- Identical probes from Bosch, Siemens or Gaggenau probably work too (Bluetooth
  name `BSHwfth`) – feedback welcome as an issue.
- The data format was reverse engineered. Unofficial, not affiliated with BSH,
  NEFF or Home Connect. Details: [docs/protocol.md](docs/protocol.md).

## License

[MIT](LICENSE)
