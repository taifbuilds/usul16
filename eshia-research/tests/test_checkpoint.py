import threading
from pathlib import Path

from eshia_research.crawler.client import Checkpoint


def test_mark_done_then_is_done(tmp_path: Path):
    checkpoint = Checkpoint(tmp_path / "checkpoint.json")
    checkpoint.mark_done("https://lib.eshia.ir/1/1/1", checksum="x")
    assert checkpoint.is_done("https://lib.eshia.ir/1/1/1")
    assert not checkpoint.is_done("https://lib.eshia.ir/1/1/2")


def test_checkpoint_persists_and_reloads_from_disk(tmp_path: Path):
    path = tmp_path / "checkpoint.json"
    Checkpoint(path).mark_done("https://lib.eshia.ir/1/1/1", checksum="x")

    reloaded = Checkpoint(path)
    assert reloaded.is_done("https://lib.eshia.ir/1/1/1")


def test_mark_done_is_safe_under_concurrent_writes(tmp_path: Path):
    # Regression: a real 71k-page concurrent crawl (10 worker threads, every
    # successful fetch calling mark_done) crashed with "dictionary changed
    # size during iteration" — one thread's json.dumps over `_done` raced
    # against another thread inserting a new key. Drives many real threads
    # at one Checkpoint to confirm it no longer crashes and every URL
    # ends up recorded.
    checkpoint = Checkpoint(tmp_path / "checkpoint.json")
    urls = [f"https://lib.eshia.ir/1/1/{n}" for n in range(500)]

    def worker(url: str) -> None:
        checkpoint.mark_done(url, checksum="x")

    threads = [threading.Thread(target=worker, args=(url,)) for url in urls]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all(checkpoint.is_done(url) for url in urls)

    reloaded = Checkpoint(tmp_path / "checkpoint.json")
    assert all(reloaded.is_done(url) for url in urls)
