# NEFF Meat Probe (BLE) for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories/)
[![Validate](https://github.com/td87-svg/neff-meat-probe-ble/actions/workflows/validate.yml/badge.svg)](https://github.com/td87-svg/neff-meat-probe-ble/actions/workflows/validate.yml)
[![Tests](https://github.com/td87-svg/neff-meat-probe-ble/actions/workflows/tests.yml/badge.svg)](https://github.com/td87-svg/neff-meat-probe-ble/actions/workflows/tests.yml)

[Deutsch](#deutsch) · [English](#english)

> [!WARNING]
> **Unofficial and reverse engineered.** This project is not affiliated with,
> endorsed by or connected to BSH Hausgeräte GmbH, NEFF or Home Connect. The
> data format was worked out by observing the probe's Bluetooth advertisements
> while heating and cooling it. It has only been verified between about 20 and
> 35 °C. Do not rely on it for food safety.

---

## Deutsch

Zeigt das kabellose NEFF-Bratenthermometer als Gerät mit Temperatursensoren in
Home Assistant an. Mehr macht die Integration nicht – keine Karten, keine
Automationen, keine Steuerung.

**So funktioniert es:** Die Sonde funkt ihre Messwerte ständig per Bluetooth
Low Energy in die Umgebung (sogenannte Advertisements), damit die Ladestation
sie empfangen kann. Home Assistant hört diese Funkpakete einfach mit –
„aus der Luft“. Die Integration läuft **nicht** über die Home-Connect-App oder
die Home-Connect-Cloud, braucht kein Konto, koppelt sich nicht mit der Sonde
und sendet nichts an sie. App und Ladestation funktionieren ganz normal weiter.

> [!IMPORTANT]
> **Bluetooth in der Nähe der Sonde ist Pflicht.** Home Assistant braucht einen
> Bluetooth-Empfänger in Funkreichweite des Backofens – entweder einen
> Bluetooth-Adapter am Home-Assistant-Rechner, wenn der in der Küche steht,
> oder einen [ESPHome-Bluetooth-Proxy](https://esphome.io/components/bluetooth_proxy.html)
> (z. B. ein ESP32 für wenige Euro) in der Küche. Der Backofen aus Metall kann
> das Signal dämpfen; der Empfänger sollte daher möglichst nah am Ofen stehen.

### Funktionen

| Entität | Beschreibung | Standard |
| --- | --- | --- |
| Mittelwert | Durchschnitt der vier Messpunkte, °C | aktiv |
| Kanal 1–4 | Die vier Messpunkte einzeln, °C (Kanal 1 vermutlich die Spitze) | deaktiviert |
| Signalstärke | RSSI der Sonde, dBm (Diagnose) | deaktiviert |
| Letztes gültiges Paket | Zeitpunkt des letzten dekodierten Pakets (Diagnose) | aktiv |

- Bluetooth-Discovery: Sobald die Sonde aus der Ladestation genommen wird,
  schlägt Home Assistant die Einrichtung vor.
- **Keine Fehlermeldungen in der Ladestation:** Dort sendet die Sonde meist gar
  nicht oder nur Raumtemperatur. Kommt fünf Minuten lang kein gültiges Paket,
  werden die Temperaturen *nicht verfügbar* statt alte Werte anzuzeigen.
  „Letztes gültiges Paket“ bleibt sichtbar.
- Diagnosedaten (Einstellungen → Geräte & Dienste → Integration → Diagnose
  herunterladen) ohne Bluetooth-Adresse.

### Unterstützte Sonden

| Modell | Bluetooth-Name | Status |
| --- | --- | --- |
| NEFF Z1365WX0 (kabelloses Bratenthermometer mit Ladestation) | `BSHwfth` | getestet |

Baugleiche Sonden anderer BSH-Marken (Bosch, Siemens, Gaggenau) senden
möglicherweise dasselbe Format – das ist ungetestet. Rückmeldungen bitte als
Issue mit heruntergeladenen Diagnosedaten.

### Voraussetzungen

- Home Assistant 2026.10 oder neuer
- Ein Bluetooth-Adapter oder ESPHome-Bluetooth-Proxy in Funkreichweite der
  Sonde (siehe Hinweis oben), mit aktivem Scannen (Standard), da der Name der
  Sonde in der Scan-Antwort steckt

### Installation über HACS

1. HACS öffnen → Menü ⋮ → **Benutzerdefinierte Repositories**.
2. Repository `https://github.com/td87-svg/neff-meat-probe-ble`, Typ
   **Integration**, hinzufügen.
3. **NEFF Meat Probe (BLE)** herunterladen und Home Assistant neu starten.
4. Sonde aus der Ladestation nehmen. Die gefundene Sonde erscheint unter
   Einstellungen → Geräte & Dienste; alternativ **Integration hinzufügen** →
   „NEFF Meat Probe“.

Manuell: Ordner `custom_components/neff_probe_ble` nach
`<config>/custom_components/` kopieren und neu starten.

### Wie der Decoder entstand

Die Sonde sendet als `BSHwfth` ein 14 Byte langes Manufacturer-Data-Feld. Die
ersten vier Bytes stiegen beim Erwärmen in der Hand und fielen beim Abkühlen;
sie werden als vier Messpunkte in ganzen °C gelesen. Weil die ersten zwei Bytes
von Bluetooth-Stacks als „Hersteller-ID“ abgetrennt werden, wechselt diese ID
ständig – der Decoder setzt sie wieder vorne an. Details und offene Fragen:
[docs/protocol.md](docs/protocol.md).

Bekannte Grenzen:

- Werte über 100 °C wurden nie beobachtet und werden derzeit verworfen. Für
  den Kern eines Bratens reicht das, ein Kanal am Griff kann im Ofen darüber
  liegen; dann ist die Sonde vorübergehend nicht verfügbar.
- Die Bedeutung von Byte 4, 6 und 7 (Umgebungstemperatur? Akku?) ist unklar.
  Sie stehen als Attribute am Mittelwert-Sensor zur Verfügung.

### Aktualisieren von 0.1.x

Entity-IDs bleiben erhalten (die Unique-IDs sind unverändert). Nur die
Anzeigenamen verlieren den Zusatz „(experimentell)“, und der Eintragstitel
wird zu „NEFF Meat Probe“.

---

## English

Shows the NEFF wireless meat probe as a device with temperature sensors in Home
Assistant. That is all it does – no cards, no automations, no control.

**How it works:** the probe constantly broadcasts its readings via Bluetooth Low
Energy (so-called advertisements) so its charging station can pick them up. Home
Assistant simply listens in on these radio packets – "out of the air". The
integration does **not** use the Home Connect app or cloud, needs no account,
never pairs with the probe and never sends anything to it. The app and the
charging station keep working as usual.

> [!IMPORTANT]
> **You need Bluetooth close to the probe.** Home Assistant needs a Bluetooth
> receiver within radio range of the oven – either a Bluetooth adapter on the
> Home Assistant machine if it sits in the kitchen, or an
> [ESPHome Bluetooth proxy](https://esphome.io/components/bluetooth_proxy.html)
> (e.g. a cheap ESP32) in the kitchen. The metal oven can weaken the signal, so
> place the receiver as close to the oven as possible.

### Features

| Entity | Description | Default |
| --- | --- | --- |
| Average | Mean of the four measuring points, °C | enabled |
| Channel 1–4 | Each measuring point, °C (channel 1 is probably the tip) | disabled |
| Signal strength | Probe RSSI, dBm (diagnostic) | disabled |
| Last valid packet | Time of the last decoded packet (diagnostic) | enabled |

- Bluetooth discovery as soon as the probe is taken out of its charger.
- **No errors while docked:** in the charger the probe usually sends nothing or
  just room temperature. After five minutes without a valid packet the
  temperatures become *unavailable* instead of showing stale values.
  "Last valid packet" stays visible.
- Diagnostics download without the Bluetooth address.

### Supported probes

| Model | Bluetooth name | Status |
| --- | --- | --- |
| NEFF Z1365WX0 (wireless meat probe with charging station) | `BSHwfth` | tested |

Identical probes sold under other BSH brands (Bosch, Siemens, Gaggenau) may use
the same format – untested. Please open an issue with a diagnostics download.

### Requirements

- Home Assistant 2026.10 or newer
- A Bluetooth adapter or ESPHome Bluetooth proxy within radio range of the
  probe (see note above), with active scanning (the default), because the
  probe's name is sent in the scan response

### Installation via HACS

1. Open HACS → menu ⋮ → **Custom repositories**.
2. Add `https://github.com/td87-svg/neff-meat-probe-ble` as type **Integration**.
3. Download **NEFF Meat Probe (BLE)** and restart Home Assistant.
4. Take the probe out of its charger. It shows up as discovered under
   Settings → Devices & services; or use **Add integration** → "NEFF Meat Probe".

Manual: copy `custom_components/neff_probe_ble` to `<config>/custom_components/`
and restart.

### How the decoder was built

The probe advertises as `BSHwfth` with a 14-byte manufacturer data field. The
first four bytes rose while warming the probe by hand and fell while it cooled;
they are read as four measuring points in whole °C. Because Bluetooth stacks
split off the first two bytes as a "company identifier", that identifier changes
all the time – the decoder puts it back in front. Details and open questions:
[docs/protocol.md](docs/protocol.md).

Known limits:

- Values above 100 °C have never been observed and are rejected for now. That
  covers a roast's core; a channel near the handle may exceed it in the oven,
  making the probe briefly unavailable.
- The meaning of bytes 4, 6 and 7 (ambient temperature? battery?) is unknown.
  They are exposed as attributes of the average sensor.

### Contributing

Captures from other probes, especially above 100 °C, are very welcome. Open an
issue with the `full_manufacturer_hex` attribute and the temperature shown in
the Home Connect app at the same moment.

Development:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements_test.txt
.venv/bin/pytest
```

## License

[MIT](LICENSE). NEFF, Home Connect and BSH are trademarks of their respective
owners and are used only to describe compatibility.
