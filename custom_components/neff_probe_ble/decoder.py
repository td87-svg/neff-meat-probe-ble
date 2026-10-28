"""Decoder for NEFF meat probe advertisements.

The format was reconstructed by observing advertisements while heating and
cooling the probe (reverse engineering). It is not based on any documentation
by BSH or NEFF. This module has no Home Assistant dependency.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math

PAYLOAD_LENGTH = 14

# Highest channel value seen during reverse engineering. Larger values have
# not been observed yet, so they are rejected rather than guessed.
MAX_CHANNEL_C = 100


@dataclass(frozen=True)
class ProbeSample:
    """Values decoded from one advertisement."""

    raw: bytes
    channels: tuple[int, int, int, int]

    @property
    def mean(self) -> float:
        """Return the mean of the four measuring points."""
        return sum(self.channels) / 4

    @property
    def rounded_mean(self) -> int:
        """Return the mean rounded half up."""
        return math.floor(self.mean + 0.5)


class NoManufacturerData(ValueError):
    """The packet carries no temperature data, e.g. a name-only scan response."""


def decode_advertisement(
    manufacturer_data: Mapping[int, bytes], raw: bytes | None = None
) -> ProbeSample:
    """Decode a packet, preferring its raw AD structures when available.

    Home Assistant merges manufacturer data of consecutive packets. Because
    the probe puts temperatures into the bytes that are normally the company
    identifier, the merged mapping can hold several stale entries. The raw
    advertisement only contains the current one.
    """
    if not raw:
        return decode(manufacturer_data)
    manufacturers = []
    offset = 0
    while offset < len(raw):
        length = raw[offset]
        if length == 0:
            break
        end = offset + length + 1
        if end > len(raw):
            raise ValueError("Truncated advertising data structure")
        if raw[offset + 1] == 0xFF:
            manufacturers.append(raw[offset + 2 : end])
        offset = end
    if not manufacturers:
        raise NoManufacturerData("Packet contains no manufacturer data")
    if len(manufacturers) != 1 or len(manufacturers[0]) < 2:
        raise ValueError("Ambiguous manufacturer data")
    payload = manufacturers[0]
    return decode({int.from_bytes(payload[:2], "little"): payload[2:]})


def decode(manufacturer_data: Mapping[int, bytes]) -> ProbeSample:
    """Decode one manufacturer data field, rejecting unknown formats.

    BLE stacks split the first two bytes of AD type 0xFF off as the company
    identifier. On this probe they are the first two temperature channels, so
    they are put back in little endian order before decoding.
    """
    if len(manufacturer_data) != 1:
        raise ValueError("Expected exactly one manufacturer data field")
    company_id, data = next(iter(manufacturer_data.items()))
    if not isinstance(company_id, int) or not 0 <= company_id <= 0xFFFF:
        raise ValueError("Invalid manufacturer identifier")
    raw = company_id.to_bytes(2, "little") + bytes(data)
    if len(raw) != PAYLOAD_LENGTH or raw[5] != 0:
        raise ValueError("Unknown manufacturer payload format")
    channels = (raw[0], raw[1], raw[2], raw[3])
    if any(value > MAX_CHANNEL_C for value in channels):
        raise ValueError(f"Channel value above {MAX_CHANNEL_C} °C")
    return ProbeSample(raw=raw, channels=channels)
