"""Constants for the NEFF meat probe BLE integration."""

DOMAIN = "neff_probe_ble"

# Local name the probe sends in its scan response.
LOCAL_NAME = "BSHwfth"

# Title of config entries created by versions before 0.2.0.
LEGACY_TITLE = "NEFF Bratenthermometer BLE (experimentell)"

# The probe advertises roughly every 10-60 s while it is out of its charger.
# Without a valid packet for this long, measurements become unavailable.
STALE_SECONDS = 300

# The decoder was reconstructed by observing advertisements (reverse engineering).
DECODER_STATUS = "reverse_engineered"
