from __future__ import annotations

from app.utils import extract_channel_ref, parse_iso8601_duration_seconds


def test_parse_pt2h30m() -> None:
    assert parse_iso8601_duration_seconds("PT2H30M") == 9000


def test_parse_pt5m() -> None:
    assert parse_iso8601_duration_seconds("PT5M") == 300


def test_parse_pt30s() -> None:
    assert parse_iso8601_duration_seconds("PT30S") == 30


def test_parse_p1dt1h() -> None:
    assert parse_iso8601_duration_seconds("P1DT1H") == 90000


def test_parse_none() -> None:
    assert parse_iso8601_duration_seconds(None) is None


def test_parse_invalid() -> None:
    assert parse_iso8601_duration_seconds("not-a-duration") is None


def test_parse_empty() -> None:
    assert parse_iso8601_duration_seconds("") is None


def test_extract_channel_id() -> None:
    cid, handle = extract_channel_ref("UCabc123def456ghi789jkl012")
    assert cid == "UCabc123def456ghi789jkl012"
    assert handle is None


def test_extract_handle() -> None:
    cid, handle = extract_channel_ref("@GoogleDevelopers")
    assert cid is None
    assert handle == "@GoogleDevelopers"


def test_extract_youtube_handle_url() -> None:
    cid, handle = extract_channel_ref("https://www.youtube.com/@GoogleDevelopers")
    assert cid is None
    assert handle == "@GoogleDevelopers"


def test_extract_youtube_channel_url() -> None:
    cid, handle = extract_channel_ref("https://www.youtube.com/channel/UCabc123def456ghi789jkl012")
    assert cid == "UCabc123def456ghi789jkl012"
    assert handle is None


def test_extract_plain_handle_without_at() -> None:
    cid, handle = extract_channel_ref("GoogleDevelopers")
    assert cid is None
    assert handle == "@GoogleDevelopers"


def test_extract_empty() -> None:
    cid, handle = extract_channel_ref("")
    assert cid is None
    assert handle is None


def test_extract_whitespace() -> None:
    cid, handle = extract_channel_ref("   ")
    assert cid is None
    assert handle is None