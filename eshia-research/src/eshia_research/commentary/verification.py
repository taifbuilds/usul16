"""Verify that a deployed commentary is actually being served.

This is the last stage of `infra/deploy/deploy-db.sh`, and it exists because a
successful import is not the same claim as "the reader can see it". Between the
two sit a service restart and a serialisation layer, either of which can fail
while the database is perfectly correct.

It replaces a check that asked a much weaker question:

    curl -fsS localhost:8000/hadiths/alkafi-2 | head -c 4000   # then grep for
                                                               # "commentaries"

That was wrong three times over. It truncated the response at 4 KB and searched
the remainder as text, so whether it passed depended on how long the hadith's
isnad, matn, footnotes and translation happened to be — a property of the data,
not of the deployment. It asked about a hardcoded hadith with no necessary
relationship to the source being deployed. And finding the *word* "commentaries"
proved nothing about whether the source just imported had arrived.

On the first production deployment it reported failure — and printed a rollback
command — for a deployment that had entirely succeeded, because `alkafi-2`'s
`commentaries` field begins after byte 4000. A false negative here is worse than
no check at all: it invites an operator to revert work that worked.

So the question asked here is the specific one: pick a hadith that this source is
actually linked to, fetch the whole response, parse it as JSON, and require that
this source appears in it.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from eshia_research.models import Hadith, HadithCommentary

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 30


class VerificationError(RuntimeError):
    """The deployed commentary could not be confirmed as served."""


def pick_linked_public_id(db: Session, source_key: str) -> str | None:
    """A hadith this source is actually published on, or None if there are none.

    Deliberately not a fixed hadith: verifying `alkafi-2` tells you nothing
    about a commentary that never touches `alkafi-2`. Only `matched` rows are
    considered, because only those reach the reader — a row that exists as
    internal evidence is not something the API will show.
    """
    return db.execute(
        select(Hadith.public_id)
        .join(HadithCommentary, HadithCommentary.hadith_id == Hadith.id)
        .where(
            HadithCommentary.source_key == source_key,
            HadithCommentary.match_status == "matched",
        )
        .order_by(Hadith.id)
        .limit(1)
    ).scalar_one_or_none()


def fetch_hadith(public_id: str, base_url: str = DEFAULT_BASE_URL, *, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> str:
    """The complete response body. Never truncated — that was the original bug."""
    url = f"{base_url.rstrip('/')}/hadiths/{public_id}"
    try:
        with urlopen(url, timeout=timeout) as response:  # noqa: S310 - fixed localhost URL
            return response.read().decode("utf-8")
    except URLError as error:
        raise VerificationError(f"Could not reach {url}: {error}") from error
    except OSError as error:
        raise VerificationError(f"Could not reach {url}: {error}") from error


def verify_payload(payload: str, source_key: str, *, public_id: str = "") -> dict[str, Any]:
    """Assert the response really carries this commentary. Raises on failure.

    Returns the matching commentary entry, so the caller can report something
    specific rather than just "ok".
    """
    where = f" for {public_id}" if public_id else ""

    try:
        document = json.loads(payload)
    except json.JSONDecodeError as error:
        raise VerificationError(
            f"The API response{where} is not valid JSON: {error}"
        ) from error

    if not isinstance(document, dict):
        raise VerificationError(
            f"The API response{where} is {type(document).__name__}, expected an object."
        )

    if "commentaries" not in document:
        raise VerificationError(
            f"The API response{where} has no 'commentaries' field. "
            "The database was written but the API is not serving it — check that "
            "the deployed code is recent enough to expose commentary."
        )

    commentaries = document["commentaries"]
    if not isinstance(commentaries, list):
        raise VerificationError(
            f"'commentaries'{where} is {type(commentaries).__name__}, expected a list."
        )

    if not commentaries:
        raise VerificationError(
            f"'commentaries'{where} is empty, but this hadith is linked to "
            f"'{source_key}' in the database. The API is not serving what was imported."
        )

    for entry in commentaries:
        if isinstance(entry, dict) and entry.get("source_key") == source_key:
            return entry

    served = sorted(
        str(entry.get("source_key"))
        for entry in commentaries
        if isinstance(entry, dict) and entry.get("source_key")
    )
    raise VerificationError(
        f"'{source_key}' is absent from the response{where}. "
        f"The API served: {', '.join(served) or '(none)'}."
    )


def verify_deployment(
    db: Session,
    source_key: str,
    *,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[str, dict[str, Any]]:
    """End to end: choose a linked hadith, fetch it whole, prove the source is served."""
    public_id = pick_linked_public_id(db, source_key)
    if public_id is None:
        raise VerificationError(
            f"No hadith is linked to '{source_key}' in this database, so there is "
            "nothing to verify. Either the import wrote no matched rows, or the "
            "source key is wrong."
        )

    payload = fetch_hadith(public_id, base_url, timeout=timeout)
    entry = verify_payload(payload, source_key, public_id=public_id)
    return public_id, entry
