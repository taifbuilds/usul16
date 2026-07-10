import datetime as dt

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eshia_research.db import Base


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    name_original: Mapped[str] = mapped_column(String(512))
    name_en: Mapped[str | None] = mapped_column(String(512), nullable=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    source_url: Mapped[str] = mapped_column(String(1024))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    parent: Mapped["Category | None"] = relationship(remote_side="Category.id")
    books: Mapped[list["Book"]] = relationship(back_populates="category")


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_original: Mapped[str] = mapped_column(String(512))
    name_normalised: Mapped[str] = mapped_column(String(512), index=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    book_links: Mapped[list["BookAuthor"]] = relationship(back_populates="author")


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (UniqueConstraint("source_book_id", name="uq_books_source_book_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_book_id: Mapped[str] = mapped_column(String(64), index=True)
    title_original: Mapped[str] = mapped_column(String(1024))
    title_normalised: Mapped[str] = mapped_column(String(1024), index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    source_url: Mapped[str] = mapped_column(String(1024))
    volume_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Lower number = crawl sooner; NULL = unprioritized (crawled last, normal
    # ID order). Lets crawl_full_library launch on a hand-picked subset (e.g.
    # the core hadith collections) before the full ~3.5M-page crawl finishes.
    crawl_priority: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    category: Mapped["Category | None"] = relationship(back_populates="books")
    volumes: Mapped[list["Volume"]] = relationship(back_populates="book")
    pages: Mapped[list["Page"]] = relationship(back_populates="book")
    author_links: Mapped[list["BookAuthor"]] = relationship(
        back_populates="book", order_by="BookAuthor.position", cascade="all, delete-orphan"
    )

    @property
    def authors(self) -> list["Author"]:
        """Authors in source-page order (e.g. original scholar before compiler/editor)."""
        return [link.author for link in self.author_links]


class BookAuthor(Base):
    """Many-to-many link between Book and Author, preserving source-page order.

    eShia often lists multiple names for one book under a single combined
    string and a single author URL (e.g. "الخوئي، ... - ميرزا علي الغروي" for
    a marja's lecture transcribed/edited by a student) — see
    crawler.parser.split_author_names. `position` preserves which name came
    first on the page; there's no reliable per-name signal on eShia itself
    to label one as "author" vs "compiler"/"editor", so no `role` column is
    added here until that's actually derivable.
    """

    __tablename__ = "book_authors"

    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, default=0)

    book: Mapped["Book"] = relationship(back_populates="author_links")
    author: Mapped["Author"] = relationship(back_populates="book_links")


class Volume(Base):
    __tablename__ = "volumes"
    __table_args__ = (UniqueConstraint("book_id", "volume_number", name="uq_volumes_book_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    volume_number: Mapped[int] = mapped_column(Integer)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    book: Mapped["Book"] = relationship(back_populates="volumes")


class Page(Base):
    __tablename__ = "pages"
    __table_args__ = (
        UniqueConstraint(
            "book_id", "volume_number", "page_number", name="uq_pages_book_volume_page"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    volume_id: Mapped[int | None] = mapped_column(ForeignKey("volumes.id"), nullable=True)
    volume_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_number: Mapped[int] = mapped_column(Integer)
    text_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_normalised: Mapped[str | None] = mapped_column(Text, nullable=True)
    html_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(String(1024), index=True)
    checksum: Mapped[str] = mapped_column(String(64), index=True)
    scraped_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    book: Mapped["Book"] = relationship(back_populates="pages")


class Hadith(Base):
    __tablename__ = "hadiths"
    __table_args__ = (
        UniqueConstraint("public_id", name="uq_hadiths_public_id"),
        UniqueConstraint("book_id", "sequence_in_book", name="uq_hadiths_book_sequence"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(128), index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), index=True)
    page_start_id: Mapped[int | None] = mapped_column(ForeignKey("pages.id"), nullable=True)
    page_end_id: Mapped[int | None] = mapped_column(ForeignKey("pages.id"), nullable=True)
    sequence_in_book: Mapped[int] = mapped_column(Integer)
    sequence_in_page: Mapped[int] = mapped_column(Integer)
    printed_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    volume_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    volume_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_start: Mapped[int] = mapped_column(Integer)
    page_end: Mapped[int] = mapped_column(Integer)
    section_title: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    full_text_raw: Mapped[str] = mapped_column(Text)
    full_text_normalised: Mapped[str] = mapped_column(Text)
    isnad_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    isnad_normalised: Mapped[str | None] = mapped_column(Text, nullable=True)
    matn_raw: Mapped[str] = mapped_column(Text)
    matn_normalised: Mapped[str] = mapped_column(Text)
    # Edition footnotes owned by this hadith, matched via their inline
    # anchors («ابن مسكان[4]»): [{marker, text, volume, page}, ...]
    footnotes_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    source_url: Mapped[str] = mapped_column(String(1024))
    extraction_method: Mapped[str] = mapped_column(String(64), default="regex_v1")
    extraction_confidence: Mapped[int] = mapped_column(Integer, default=80)
    review_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    book: Mapped["Book"] = relationship()
    page_start_ref: Mapped["Page | None"] = relationship(foreign_keys=[page_start_id])
    page_end_ref: Mapped["Page | None"] = relationship(foreign_keys=[page_end_id])


class HadithSplitReview(Base):
    """Human-reviewed isnad/matn split for one hadith.

    The extractor's draft split remains in Hadith.isnad_raw/matn_raw. This
    table stores the approved or in-progress correction so rebuilding the
    extractor cannot wipe human review work.
    """

    __tablename__ = "hadith_split_reviews"
    __table_args__ = (UniqueConstraint("hadith_id", name="uq_hadith_split_reviews_hadith"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hadith_id: Mapped[int] = mapped_column(ForeignKey("hadiths.id"), index=True)
    approved_isnad_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_matn_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(String(32), default="unreviewed", index=True)
    reviewer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    split_version: Mapped[str] = mapped_column(String(32), default="manual_v1")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    hadith: Mapped["Hadith"] = relationship()


class Chain(Base):
    """One transmission chain (isnad) of a hadith.

    A hadith usually has exactly one chain, but can have several: تحويل
    («ح») switches, or a «جميعا» convergence expanded into its parallel
    routes. `raw_isnad` always preserves the full original isnad text, so
    expansion is reversible.
    """

    __tablename__ = "chains"
    __table_args__ = (
        UniqueConstraint("hadith_id", "chain_number", name="uq_chains_hadith_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hadith_id: Mapped[int] = mapped_column(ForeignKey("hadiths.id"), index=True)
    chain_number: Mapped[int] = mapped_column(Integer, default=1)
    raw_isnad: Mapped[str] = mapped_column(Text)
    parser_version: Mapped[str] = mapped_column(String(32), default="isnad_v1")
    node_count: Mapped[int] = mapped_column(Integer, default=0)
    # Comma-separated quality signals from the tokenizer, e.g.
    # "raf,citation_noise,convergence_expanded_heuristic". Not a judgement —
    # a machine-readable trail of what the parser did or could not do.
    flags: Mapped[str | None] = mapped_column(String(512), nullable=True)
    review_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    hadith: Mapped["Hadith"] = relationship()
    nodes: Mapped[list["ChainNode"]] = relationship(
        back_populates="chain", order_by="ChainNode.position", cascade="all, delete-orphan"
    )


class ChainNode(Base):
    """One link in a chain: a person or person-like phrase in the isnad.

    `raw_token` is never a resolved identity — «أبيه» stays «أبيه». Identity
    lives in `canonical_narrator_id` + `confidence` + `resolution_reason`,
    filled by the (separate) resolution engine, so uncertainty is stored,
    displayed, and revisable rather than baked into the text.
    """

    __tablename__ = "chain_nodes"
    __table_args__ = (
        UniqueConstraint("chain_id", "position", name="uq_chain_nodes_chain_position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain_id: Mapped[int] = mapped_column(ForeignKey("chains.id"), index=True)
    # 0 = closest to the compiler; the Imam (if reached) is the last node.
    position: Mapped[int] = mapped_column(Integer)
    raw_token: Mapped[str] = mapped_column(Text)
    token_normalised: Mapped[str] = mapped_column(String(512), index=True)
    # The transmission phrase that introduced this node (عن/حدثنا/أخبرنا/...);
    # NULL for a chain-opening node.
    transmission_phrase: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # named_narrator | pronoun_relation | collective_phrase | unknown_person | imam
    node_type: Mapped[str] = mapped_column(String(32), index=True)
    # For pronoun_relation: father | grandfather | brother | uncle | anaphora |
    # same_isnad. For imam: ambiguous (أحدهما). NULL otherwise.
    relation_kind: Mapped[str | None] = mapped_column(String(32), nullable=True)
    canonical_narrator_id: Mapped[int | None] = mapped_column(
        ForeignKey("narrators.id"), nullable=True, index=True
    )
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolution_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resolution_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(String(32), default="pending")

    chain: Mapped["Chain"] = relationship(back_populates="nodes")
    narrator: Mapped["Narrator | None"] = relationship()
    candidates: Mapped[list["ChainNodeCandidate"]] = relationship(
        back_populates="chain_node", cascade="all, delete-orphan"
    )


class ChainNodeCandidate(Base):
    """A possible narrator identity for a chain node.

    Resolution should be inspectable. Even when a winning narrator is written
    to ChainNode, close alternatives stay here with scores and evidence.
    """

    __tablename__ = "chain_node_candidates"
    __table_args__ = (
        UniqueConstraint(
            "chain_node_id",
            "narrator_id",
            "resolver_version",
            name="uq_chain_node_candidate_version",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain_node_id: Mapped[int] = mapped_column(ForeignKey("chain_nodes.id"), index=True)
    narrator_id: Mapped[int] = mapped_column(ForeignKey("narrators.id"), index=True)
    rank: Mapped[int] = mapped_column(Integer)
    score: Mapped[int] = mapped_column(Integer, index=True)
    match_type: Mapped[str] = mapped_column(String(64), index=True)
    evidence_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    evidence_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolver_version: Mapped[str] = mapped_column(String(32), default="resolver_v1", index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    chain_node: Mapped["ChainNode"] = relationship(back_populates="candidates")
    narrator: Mapped["Narrator"] = relationship()


class Narrator(Base):
    """A canonical narrator identity (one real person).

    Populated by the rijal extraction layer (Mu'jam Rijal al-Hadith first).
    Textual variants live in narrator_aliases (later phase); scholars' raw
    quotes live in rijal_statements (later phase) — this row holds identity,
    not judgement.
    """

    __tablename__ = "narrators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_name_ar: Mapped[str] = mapped_column(String(512))
    canonical_name_norm: Mapped[str] = mapped_column(String(512), index=True)
    canonical_name_en: Mapped[str | None] = mapped_column(String(512), nullable=True)
    kunya: Mapped[str | None] = mapped_column(String(256), nullable=True)
    laqab: Mapped[str | None] = mapped_column(String(256), nullable=True)
    nisba: Mapped[str | None] = mapped_column(String(256), nullable=True)
    father_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    # Free text because sources say things like «بعد 260» — precision varies.
    death_year_note: Mapped[str | None] = mapped_column(String(128), nullable=True)
    generation_layer: Mapped[int | None] = mapped_column(Integer, nullable=True)
    school_or_sect: Mapped[str | None] = mapped_column(String(128), nullable=True)
    summary_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    aliases: Mapped[list["NarratorAlias"]] = relationship(
        back_populates="narrator", cascade="all, delete-orphan"
    )
    rijal_entries: Mapped[list["RijalEntry"]] = relationship(back_populates="narrator")


class NarratorAlias(Base):
    """A textual form that may refer to a canonical narrator identity.

    Aliases are sourced evidence, not global replacement rules. A kunya like
    "Abu Basir" can point to more than one identity, so each alias stays tied
    to the narrator/source entry that supplied it.
    """

    __tablename__ = "narrator_aliases"
    __table_args__ = (
        UniqueConstraint(
            "narrator_id",
            "alias_normalised",
            "alias_type",
            "source_entry_id",
            name="uq_narrator_alias_source",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    narrator_id: Mapped[int] = mapped_column(ForeignKey("narrators.id"), index=True)
    source_entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("rijal_entries.id"), nullable=True, index=True
    )
    alias_raw: Mapped[str] = mapped_column(String(512))
    alias_normalised: Mapped[str] = mapped_column(String(512), index=True)
    alias_type: Mapped[str] = mapped_column(String(32), default="name_variant")
    source_note: Mapped[str | None] = mapped_column(String(256), nullable=True)
    confidence: Mapped[int] = mapped_column(Integer, default=80)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    narrator: Mapped["Narrator"] = relationship(back_populates="aliases")
    source_entry: Mapped["RijalEntry | None"] = relationship(back_populates="aliases")


class RijalEntry(Base):
    """One source-specific rijal entry.

    Mu'jam entries are first-class source witnesses. Later, Najashi/Tusi/etc.
    entries can be attached to the same narrator without flattening different
    books into one biography blob.
    """

    __tablename__ = "rijal_entries"
    __table_args__ = (
        UniqueConstraint("book_id", "entry_kind", "entry_number", name="uq_rijal_entry_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    narrator_id: Mapped[int | None] = mapped_column(ForeignKey("narrators.id"), index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), index=True)
    page_start_id: Mapped[int | None] = mapped_column(ForeignKey("pages.id"), nullable=True)
    page_end_id: Mapped[int | None] = mapped_column(ForeignKey("pages.id"), nullable=True)
    entry_kind: Mapped[str] = mapped_column(String(64), default="mujam_numbered_entry")
    entry_number: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    title_raw: Mapped[str] = mapped_column(String(512))
    title_normalised: Mapped[str] = mapped_column(String(512), index=True)
    canonical_name_raw: Mapped[str] = mapped_column(String(512))
    canonical_name_normalised: Mapped[str] = mapped_column(String(512), index=True)
    volume_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    volume_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text_raw: Mapped[str] = mapped_column(Text)
    text_normalised: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    parser_version: Mapped[str] = mapped_column(String(32), default="mujam_v1")
    flags: Mapped[str | None] = mapped_column(String(512), nullable=True)
    review_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    narrator: Mapped["Narrator | None"] = relationship(back_populates="rijal_entries")
    book: Mapped["Book"] = relationship()
    page_start_ref: Mapped["Page | None"] = relationship(foreign_keys=[page_start_id])
    page_end_ref: Mapped["Page | None"] = relationship(foreign_keys=[page_end_id])
    aliases: Mapped[list["NarratorAlias"]] = relationship(
        back_populates="source_entry", cascade="all, delete-orphan"
    )
    statements: Mapped[list["RijalStatement"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan"
    )
    occurrences: Mapped[list["RijalOccurrence"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan"
    )


class RijalStatement(Base):
    """A cited rijal judgement, quote, or source note inside a rijal entry."""

    __tablename__ = "rijal_statements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("rijal_entries.id"), index=True)
    narrator_id: Mapped[int | None] = mapped_column(ForeignKey("narrators.id"), index=True)
    source_name: Mapped[str] = mapped_column(String(128), index=True)
    statement_type: Mapped[str] = mapped_column(String(64), index=True)
    quote_raw: Mapped[str] = mapped_column(Text)
    quote_normalised: Mapped[str] = mapped_column(Text)
    evidence_text_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[int] = mapped_column(Integer, default=75)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    entry: Mapped["RijalEntry"] = relationship(back_populates="statements")
    narrator: Mapped["Narrator | None"] = relationship()


class RijalOccurrence(Base):
    """A Mu'jam occurrence note such as 'narrated from X' or 'X narrated from him'."""

    __tablename__ = "rijal_occurrences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("rijal_entries.id"), index=True)
    narrator_id: Mapped[int | None] = mapped_column(ForeignKey("narrators.id"), index=True)
    direction: Mapped[str] = mapped_column(String(32), index=True)
    related_name_raw: Mapped[str] = mapped_column(String(512))
    related_name_normalised: Mapped[str] = mapped_column(String(512), index=True)
    source_ref_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_text_raw: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[int] = mapped_column(Integer, default=70)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    entry: Mapped["RijalEntry"] = relationship(back_populates="occurrences")
    narrator: Mapped["Narrator | None"] = relationship()


class Person(Base):
    """A historical individual, distinct from Mu'jam entries and chain mentions.

    The Tamyiz Engine's core separation: a chain node is a MENTION, a rijal
    entry is an EVIDENCE DOCUMENT, and a Person is the individual both point
    at. Al-Khoei's bare-form entries («أحمد بن محمد») are disambiguation
    discussions about several people, so they get kind='bare_form_proxy'
    rather than pretending to be one person.
    """

    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_name_ar: Mapped[str] = mapped_column(String(512))
    canonical_name_norm: Mapped[str] = mapped_column(String(512), index=True)
    kunya: Mapped[str | None] = mapped_column(String(256), nullable=True)
    laqab: Mapped[str | None] = mapped_column(String(256), nullable=True)
    nisba: Mapped[str | None] = mapped_column(String(256), nullable=True)
    # Normalised name of the father as asserted by the nasab itself
    # (for فلان بن X the father IS X); matching to a person row is separate.
    father_name_norm: Mapped[str | None] = mapped_column(String(512), nullable=True)
    death_year_note: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # Filled by the tabaqat layer (Phase C); NULL until then.
    generation_layer: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # individual | bare_form_proxy | masum | latent
    kind: Mapped[str] = mapped_column(String(32), default="individual", index=True)
    # mujam_entry | fixed_masum | nasab_kinship (latent, Phase B+)
    origin: Mapped[str] = mapped_column(String(32), default="mujam_entry")
    primary_entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("rijal_entries.id"), nullable=True, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    primary_entry: Mapped["RijalEntry | None"] = relationship()
    entry_links: Mapped[list["PersonEntryLink"]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )
    surface_forms: Mapped[list["PersonSurfaceForm"]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )


class PersonEntryLink(Base):
    """Typed link between a person and a rijal entry as an evidence document.

    is_subject: the entry is about this person.
    bare_form_evidence: a bare-form entry whose occurrence notes are evidence
        about this (fuller-named) person among others.
    tamyiz_discussion: the entry text contains an identity ruling or
        disambiguation discussion relevant to this person.
    """

    __tablename__ = "person_entry_links"
    __table_args__ = (
        UniqueConstraint(
            "person_id", "entry_id", "link_type", name="uq_person_entry_link"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), index=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("rijal_entries.id"), index=True)
    link_type: Mapped[str] = mapped_column(String(32), index=True)
    evidence_quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[int] = mapped_column(Integer, default=80)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    person: Mapped["Person"] = relationship(back_populates="entry_links")
    entry: Mapped["RijalEntry"] = relationship()


class PersonSurfaceForm(Base):
    """One way a person can legally appear in an isnad.

    Generated by the name grammar (nasab truncations, kunya, ibn-form,
    nisba-form), so a bare form like «أحمد بن محمد» is ambiguous BY
    CONSTRUCTION: `shared_count` records how many persons claim the same
    normalised form corpus-wide.
    """

    __tablename__ = "person_surface_forms"
    __table_args__ = (
        UniqueConstraint("person_id", "form_norm", name="uq_person_surface_form"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), index=True)
    form_raw: Mapped[str] = mapped_column(String(512))
    form_norm: Mapped[str] = mapped_column(String(512), index=True)
    # full | nasab_truncation | first_name | kunya | ibn_form | nisba_form |
    # entry_title | masum_title
    derivation: Mapped[str] = mapped_column(String(32), index=True)
    shared_count: Mapped[int] = mapped_column(Integer, default=1, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    person: Mapped["Person"] = relationship(back_populates="surface_forms")


class PersonRelation(Base):
    """A typed relation between persons (or a person and a named-but-unmatched
    relative), each with a source note.

    `related_person_id` stays NULL when the relative's name is known from the
    nasab but no unique person row matches yet — the name itself is still
    stored in `related_name_norm` so Phase B relational resolution (عن أبيه)
    can use it.
    """

    __tablename__ = "person_relations"
    __table_args__ = (
        UniqueConstraint(
            "person_id", "relation_kind", "related_name_norm", name="uq_person_relation"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), index=True)
    related_person_id: Mapped[int | None] = mapped_column(
        ForeignKey("persons.id"), nullable=True, index=True
    )
    # father | son | brother | uncle | grandfather | mawla | same_person_as
    relation_kind: Mapped[str] = mapped_column(String(32), index=True)
    related_name_norm: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    confidence: Mapped[int] = mapped_column(Integer, default=80)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    person: Mapped["Person"] = relationship(foreign_keys=[person_id])
    related_person: Mapped["Person | None"] = relationship(foreign_keys=[related_person_id])


class CollectiveRoster(Base):
    """Documented membership of a collective isnad phrase, keyed by the next
    narrator in the chain.

    E.g. Kulayni's «عدة من أصحابنا» keyed by أحمد بن محمد بن عيسى has a
    documented member roster (Khulasat al-Aqwal, cited in the Mu'jam
    muqaddima). Member appearances resolved through a roster are attributed
    via_collective — never presented as direct transmission.
    """

    __tablename__ = "collective_rosters"
    __table_args__ = (
        UniqueConstraint(
            "collective_norm",
            "keyed_by_norm",
            "member_name_norm",
            name="uq_collective_roster_member",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collective_norm: Mapped[str] = mapped_column(String(512), index=True)
    # Normalised name of the narrator the collective transmits from.
    keyed_by_norm: Mapped[str] = mapped_column(String(512), index=True)
    member_person_id: Mapped[int | None] = mapped_column(
        ForeignKey("persons.id"), nullable=True, index=True
    )
    member_name_ar: Mapped[str] = mapped_column(String(512))
    member_name_norm: Mapped[str] = mapped_column(String(512), index=True)
    source_citation: Mapped[str] = mapped_column(String(512))
    confidence: Mapped[int] = mapped_column(Integer, default=80)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    member_person: Mapped["Person | None"] = relationship()


class PersonGeneration(Base):
    """A person's inferred generation (tabaqa) as an interval, not a point.

    Ayatollah Boroujerdi's method, automated: every narrator sits in a
    generation layer counted from the Prophet (0), and a chain is a strictly
    descending walk. Anchored from Imam companionship statements
    (`rijal_statements.tabaqah_membership`) and the fixed Imam layers, then
    tightened by propagation over confident transmission edges. Derived and
    revisable — kept separate from `persons` identity for that reason.
    """

    __tablename__ = "person_generations"
    __table_args__ = (UniqueConstraint("person_id", name="uq_person_generation"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), index=True)
    gen_lo: Mapped[int] = mapped_column(Integer)
    gen_hi: Mapped[int] = mapped_column(Integer)
    # Point estimate for display/filtering (usually gen_lo of a tight anchor).
    gen_point: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # imam_fixed | ashab_anchor | propagated | anchor_and_propagated | conflict
    method: Mapped[str] = mapped_column(String(32), index=True)
    evidence_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    resolver_version: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    person: Mapped["Person"] = relationship()


class MentionResolution(Base):
    """Person-level identity claim for one chain node (mention).

    Deliberately separate from ChainNode.canonical_narrator_id, which keeps
    meaning "Mu'jam ENTRY citation". Multiple rows per node express ranked
    ambiguity; every row carries a structured dalil in evidence_json.
    Populated from Phase B onward — the table exists from Phase A so the
    schema is stable for other agents.
    """

    __tablename__ = "mention_resolutions"
    __table_args__ = (
        UniqueConstraint(
            "chain_node_id", "person_id", "resolver_version", name="uq_mention_resolution"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain_node_id: Mapped[int] = mapped_column(ForeignKey("chain_nodes.id"), index=True)
    person_id: Mapped[int | None] = mapped_column(
        ForeignKey("persons.id"), nullable=True, index=True
    )
    rank: Mapped[int] = mapped_column(Integer, default=1)
    # resolved | ambiguous | via_collective | latent | unresolved
    status: Mapped[str] = mapped_column(String(32), index=True)
    method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evidence_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    evidence_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolver_version: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    chain_node: Mapped["ChainNode"] = relationship()
    person: Mapped["Person | None"] = relationship()


class PersonResolutionDecision(Base):
    """Review-layer decision for a person-resolution case.

    This is intentionally separate from `mention_resolutions`: the resolver's
    raw ranked claims remain intact, while machine/admin decisions record which
    claims are approved, flagged, or exported for deeper review.
    """

    __tablename__ = "person_resolution_decisions"
    __table_args__ = (
        UniqueConstraint(
            "chain_node_id",
            "reviewer",
            "resolver_version",
            name="uq_person_resolution_decision_node_reviewer_version",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain_node_id: Mapped[int] = mapped_column(ForeignKey("chain_nodes.id"), index=True)
    selected_person_id: Mapped[int | None] = mapped_column(
        ForeignKey("persons.id"), nullable=True, index=True
    )
    # approve_current | needs_external_review | flag_contradiction | keep_ambiguous
    decision_type: Mapped[str] = mapped_column(String(64), index=True)
    # high | medium | low | blocked
    confidence_tier: Mapped[str] = mapped_column(String(32), index=True)
    reviewer: Mapped[str] = mapped_column(String(128), default="codex-machine-v1", index=True)
    resolver_version: Mapped[str] = mapped_column(String(32), index=True)
    question_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    chain_node: Mapped["ChainNode"] = relationship()
    selected_person: Mapped["Person | None"] = relationship()


class PersonResolutionExternalReview(Base):
    """Imported result from an outside reviewer/LLM for one review-packet case.

    External reviews are evidence about a machine decision, not silent edits to
    the resolver. They can later be promoted into explicit overrides when the
    target person is matched safely.
    """

    __tablename__ = "person_resolution_external_reviews"
    __table_args__ = (
        UniqueConstraint(
            "chain_node_id",
            "source_label",
            "case_id",
            name="uq_person_resolution_external_review_case",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    decision_id: Mapped[int | None] = mapped_column(
        ForeignKey("person_resolution_decisions.id"), nullable=True, index=True
    )
    chain_node_id: Mapped[int] = mapped_column(ForeignKey("chain_nodes.id"), index=True)
    matched_person_id: Mapped[int | None] = mapped_column(
        ForeignKey("persons.id"), nullable=True, index=True
    )
    case_id: Mapped[str] = mapped_column(String(256), index=True)
    source_label: Mapped[str] = mapped_column(String(256), index=True)
    external_reviewer: Mapped[str] = mapped_column(String(128), default="external-llm")
    verdict: Mapped[str] = mapped_column(String(64), index=True)
    confidence_raw: Mapped[str | None] = mapped_column(String(256), nullable=True)
    confidence_tier: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    correct_person_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_consulted: Mapped[str | None] = mapped_column(Text, nullable=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_case_text: Mapped[str] = mapped_column(Text)
    parser_version: Mapped[str] = mapped_column(String(32), default="external_review_v1")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    decision: Mapped["PersonResolutionDecision | None"] = relationship()
    chain_node: Mapped["ChainNode"] = relationship()
    matched_person: Mapped["Person | None"] = relationship()


class CrawlLog(Base):
    __tablename__ = "crawl_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(1024), index=True)
    status: Mapped[str] = mapped_column(String(32))
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    scraped_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
