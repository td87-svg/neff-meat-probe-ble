"""Tests for the advertisement decoder, using real captured packets."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from custom_components.neff_probe_ble.decoder import (
    NoManufacturerData,
    ProbeSample,
    decode,
    decode_advertisement,
    manufacturer_payload,
)

PACKETS = json.loads(
    (Path(__file__).parent / "fixtures" / "probe_packets.json").read_text("utf-8")
)["packets"]


def _ad_structure(ad_type: int, payload: bytes) -> bytes:
    return bytes([len(payload) + 1, ad_type]) + payload


@pytest.mark.parametrize(
    "packet", PACKETS, ids=[f"{p['capture']}-{i}" for i, p in enumerate(PACKETS)]
)
def test_captured_packets(packet: dict) -> None:
    """Every captured probe packet decodes to its first four bytes."""
    data = bytes.fromhex(packet["manufacturer_data"])
    sample = decode({packet["manufacturer_id"]: data})
    assert list(sample.channels) == packet["expected_channels"]
    assert all(15 <= value <= 40 for value in sample.channels)


@pytest.mark.parametrize("packet", PACKETS[:5])
def test_captured_packets_from_raw(packet: dict) -> None:
    """The raw AD structures give the same result as the manufacturer mapping."""
    data = bytes.fromhex(packet["manufacturer_data"])
    payload = packet["manufacturer_id"].to_bytes(2, "little") + data
    raw = (
        _ad_structure(0x01, b"\x06")
        + _ad_structure(0xFF, payload)
        + _ad_structure(0x09, b"BSHwfth")
    )
    # A stale entry in the merged mapping must be ignored when raw is given.
    stale = {0x1616: bytes(12), packet["manufacturer_id"]: data}
    assert decode_advertisement(stale, raw) == decode({packet["manufacturer_id"]: data})


def test_heating_sequence() -> None:
    """Values documented while warming the probe by hand."""
    sample = decode({0x201E: bytes.fromhex("20201b00210b060808a60200")})
    assert sample.channels == (30, 32, 32, 32)
    assert sample.mean == 31.5
    assert sample.rounded_mean == 32
    assert sample.raw[4] == 27
    assert sample.raw[6] == 33


@pytest.mark.parametrize(
    ("payload_hex", "channels"),
    [
        # Captured in an oven set to 180 °C; tail masked.
        ("1817246ab00050f8050000000000", (24, 23, 36, 106)),
        ("2b2a3c6bb8005f06060000000000", (43, 42, 60, 107)),
    ],
)
def test_channels_above_100(payload_hex: str, channels: tuple[int, ...]) -> None:
    """Channels above 100 °C are valid readings."""
    payload = bytes.fromhex(payload_hex)
    sample = decode_advertisement({}, _ad_structure(0xFF, payload))
    assert sample.channels == channels


def test_mean() -> None:
    """The mean is the average of all four channels."""
    sample = ProbeSample(raw=bytes(14), channels=(26, 27, 28, 29))
    assert sample.mean == 27.5
    assert sample.rounded_mean == 28


def test_scan_response_without_manufacturer_data() -> None:
    """A name-only scan response is not an error."""
    with pytest.raises(NoManufacturerData):
        decode_advertisement({}, _ad_structure(0x09, b"BSHwfth"))


def test_raw_without_raw_falls_back_to_mapping() -> None:
    """Without raw bytes the merged mapping is used."""
    sample = decode_advertisement({0x1718: bytes.fromhex("171717001801060808a60200")})
    assert sample.channels == (24, 23, 23, 23)


@pytest.mark.parametrize(
    ("manufacturer_data", "message"),
    [
        ({}, "exactly one"),
        ({1: bytes(12), 2: bytes(12)}, "exactly one"),
        ({0x1718: bytes(11)}, "Unknown manufacturer payload"),
        ({0x1718: bytes.fromhex("171717011801060808a60200")}, "Unknown manufacturer"),
        ({0x1718: bytes.fromhex("6517170018010608")}, "Unknown manufacturer"),
        ({0x10000: bytes(12)}, "Invalid manufacturer"),
        ({-1: bytes(12)}, "Invalid manufacturer"),
    ],
)
def test_rejects_unknown_payloads(manufacturer_data: dict, message: str) -> None:
    """Unknown formats are rejected instead of guessed."""
    with pytest.raises(ValueError, match=message):
        decode(manufacturer_data)


@pytest.mark.parametrize(
    "raw",
    [
        b"\x05\xff\x18\x17",  # truncated structure
        _ad_structure(0xFF, b"\x18\x17" + bytes(12)) * 2,  # two fields
        _ad_structure(0xFF, b"\x18"),  # no company identifier
    ],
)
def test_rejects_malformed_raw(raw: bytes) -> None:
    """Malformed or ambiguous raw advertisements are rejected."""
    with pytest.raises(ValueError):
        decode_advertisement({}, raw)


def test_manufacturer_payload_of_rejected_packet() -> None:
    """Rejected packets can still be recorded."""
    payload = bytes.fromhex("6565656565001801060808a60200")
    assert manufacturer_payload({}, _ad_structure(0xFF, payload)) == payload
    assert manufacturer_payload({0x6565: payload[2:]}) == payload
    assert manufacturer_payload({}, b"\x05\xff\x18") is None
    assert manufacturer_payload({1: b"", 2: b""}) is None


def test_zero_length_terminates_raw() -> None:
    """A zero length byte ends the AD structure list (padding)."""
    payload = bytes.fromhex("1817171717001801060808a60200")
    raw = _ad_structure(0xFF, payload) + b"\x00\x00\x00"
    assert decode_advertisement({}, raw).channels == (24, 23, 23, 23)
