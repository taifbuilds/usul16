from pathlib import Path

import pytest

from eshia_research.cloudstore import LocalFileStore


@pytest.fixture()
def store(tmp_path: Path) -> LocalFileStore:
    return LocalFileStore(tmp_path / "buffer")


def test_put_and_get_bytes_round_trip(store: LocalFileStore):
    store.put_bytes("pages/abc.jsonl.gz", b"hello world")
    assert store.get_bytes("pages/abc.jsonl.gz") == b"hello world"


def test_list_keys_returns_only_matching_prefix(store: LocalFileStore):
    store.put_bytes("pages/a.jsonl.gz", b"1")
    store.put_bytes("pages/b.jsonl.gz", b"2")
    store.put_bytes("other/c.jsonl.gz", b"3")

    keys = store.list_keys("pages/")
    assert keys == ["pages/a.jsonl.gz", "pages/b.jsonl.gz"]


def test_list_keys_empty_when_prefix_does_not_exist(store: LocalFileStore):
    assert store.list_keys("nonexistent/") == []


def test_delete_removes_the_object(store: LocalFileStore):
    store.put_bytes("pages/a.jsonl.gz", b"1")
    store.delete("pages/a.jsonl.gz")
    assert store.list_keys("pages/") == []


def test_delete_is_safe_to_call_on_missing_key(store: LocalFileStore):
    store.delete("pages/never-existed.jsonl.gz")  # should not raise
