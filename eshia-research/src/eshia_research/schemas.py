import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: str | None
    name_original: str
    name_en: str | None
    parent_id: int | None
    source_url: str


class AuthorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name_original: str
    name_normalised: str
    source_url: str | None


class VolumeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    volume_number: int
    source_url: str | None


class PageTextBlock(BaseModel):
    kind: str
    text: str | None = None


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_book_id: str
    title_original: str
    title_normalised: str
    authors: list[AuthorRead]
    category: CategoryRead | None
    language: str | None
    source_url: str
    volume_count: int | None
    has_content: bool
    created_at: dt.datetime
    updated_at: dt.datetime


class BookSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_book_id: str
    title_original: str
    title_normalised: str
    authors: list[AuthorRead]
    source_url: str
    volume_count: int | None
    has_content: bool


class PageIndexEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    volume_number: int | None
    page_number: int
    source_url: str


class PageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    volume_number: int | None
    page_number: int
    text_raw: str | None
    text_normalised: str | None
    source_url: str
    checksum: str
    scraped_at: dt.datetime
    text_blocks: list[PageTextBlock] | None = None


class HadithFootnote(BaseModel):
    marker: str
    text: str
    volume: int | None = None
    page: int | None = None


class HadithTranslationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    language: str
    translation_version: str
    rendered_isnad_en: str | None
    matn_translation: str
    full_translation: str | None = None
    status: Literal["human_reviewed", "published"]
    risk_level: Literal["green"]
    risk_flags: list | None = None
    provider: str | None = None
    model: str | None = None
    provenance_json: dict | None = None


class HadithStructureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kitab_id: str
    kitab_name_en: str
    chapter_id: int
    chapter_name_en: str
    number_in_chapter: int | None
    mapping_status: str
    thaqalayn_url: str | None = None


class HadithGradingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    grader_key: str
    author_name_en: str
    grade_ar: str
    grade_en: str | None = None
    reference_en: str | None = None


class KitabSummary(BaseModel):
    kitab_id: str
    name_en: str
    volume: int
    chapter_count: int
    hadith_count: int
    first_chapter_id: int


class ThaqalaynChapterSummary(BaseModel):
    chapter_id: int
    name_en: str
    hadith_count: int
    number_min: int | None = None
    number_max: int | None = None


class HadithRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_id: str
    book_id: int
    page_start_id: int | None
    page_end_id: int | None
    sequence_in_book: int
    sequence_in_page: int
    printed_number: str | None
    volume_start: int | None
    volume_end: int | None
    page_start: int
    page_end: int
    section_title: str | None
    full_text_raw: str
    isnad_raw: str | None
    matn_raw: str
    footnotes_json: list[HadithFootnote] | None = Field(
        default=None, serialization_alias="footnotes"
    )
    source_url: str
    extraction_method: str
    extraction_confidence: int
    review_status: str
    translation: HadithTranslationRead | None = None
    structure: HadithStructureRead | None = None
    gradings: list[HadithGradingRead] | None = None


class NarratorSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canonical_name_ar: str
    canonical_name_en: str | None
    kunya: str | None
    laqab: str | None
    nisba: str | None
    father_name: str | None
    death_year_note: str | None
    generation_layer: int | None
    school_or_sect: str | None
    summary_status: str | None


class ChainNodeCandidateRead(BaseModel):
    rank: int
    score: int
    match_type: str
    evidence_summary: str | None
    narrator: NarratorSummaryRead


class PersonRef(BaseModel):
    """A resolved historical person (Tamyiz Engine), with its generation.

    `narrator_id` points at the underlying Mu'jam narrator entry when the
    person was seeded from one, so the UI can reuse the existing narrator page.
    Latent (nasab-only) and Ma'sum persons have no narrator_id.
    """

    id: int
    canonical_name_ar: str
    kind: str
    narrator_id: int | None = None
    generation: int | None = None
    generation_method: str | None = None


class MentionCandidateRead(BaseModel):
    rank: int
    status: str
    method: str | None
    person: PersonRef | None
    evidence_summary: str | None


class NodePersonResolution(BaseModel):
    """Person-level resolution of one chain node (separate from the older
    entry-level `narrator`/`candidates`). Carries the dalil for display.

    `effective` is the resolver's rank-1 pick overlaid with any admin review
    decision; when a decision applies, `status`/`resolved_person` above already
    reflect it (so existing UI needs no change) and `effective.source` is
    "admin".
    """

    status: str  # resolved | ambiguous | via_collective | latent | unresolved
    resolved_person: PersonRef | None = None
    primary_dalil: str | None = None
    candidates: list[MentionCandidateRead] = Field(default_factory=list)
    effective: "PersonResolutionEffectiveRead | None" = None


class PersonResolutionStatusCount(BaseModel):
    status: str
    total: int


class PersonResolutionNodeTypeCount(BaseModel):
    node_type: str
    status: str
    total: int


class PersonResolutionMethodCount(BaseModel):
    method: str | None
    status: str
    total: int


class PersonResolutionAuditSummary(BaseModel):
    source_book_id: str
    total_nodes: int
    with_rank1_resolution: int
    without_rank1_resolution: int
    open_nodes: int
    status_counts: list[PersonResolutionStatusCount]
    node_type_counts: list[PersonResolutionNodeTypeCount]
    method_counts: list[PersonResolutionMethodCount]


class PersonResolutionDecisionCount(BaseModel):
    key: str
    total: int


class PersonResolutionDecisionSummary(BaseModel):
    source_book_id: str
    reviewer: str
    total_decisions: int
    decision_counts: list[PersonResolutionDecisionCount]
    confidence_counts: list[PersonResolutionDecisionCount]


class PersonResolutionAuditCandidate(BaseModel):
    rank: int
    status: str
    method: str | None
    person: PersonRef | None
    evidence_summary: str | None
    score: int | None = None
    winner_score: int | None = None
    margin_to_winner: int | None = None


class PersonResolutionAdminDecisionRead(BaseModel):
    decision_type: str
    confidence_tier: str
    reviewer: str
    selected_person: PersonRef | None = None
    summary: str | None = None
    external_verdict: str | None = None
    external_case_id: str | None = None
    source_reference: str | None = None


class PersonResolutionEffectiveRead(BaseModel):
    source: str
    status: str
    label: str
    person: PersonRef | None = None
    reason: str | None = None


class PersonResolutionAuditItem(BaseModel):
    hadith_id: int
    public_id: str
    sequence_in_book: int
    section_title: str | None
    volume_start: int | None
    page_start: int
    page_end: int
    chain_id: int
    chain_number: int
    node_id: int
    position: int
    raw_token: str
    token_normalised: str
    node_type: str
    relation_kind: str | None
    status: str
    method: str | None
    resolved_person: PersonRef | None = None
    admin_decision: PersonResolutionAdminDecisionRead | None = None
    effective_resolution: PersonResolutionEffectiveRead | None = None
    primary_dalil: str | None = None
    candidates: list[PersonResolutionAuditCandidate] = Field(default_factory=list)
    candidate_count: int = 0
    top_score: int | None = None
    top_margin: int | None = None
    risk_flags: list[str] = Field(default_factory=list)
    isnad_excerpt: str | None = None
    matn_excerpt: str


class PersonResolutionAuditPage(BaseModel):
    source_book_id: str
    status: str
    node_type: str | None
    risk: str | None
    q: str | None
    total: int
    skip: int
    limit: int
    items: list[PersonResolutionAuditItem]


class ChainNodeRead(BaseModel):
    id: int
    position: int
    raw_token: str
    token_normalised: str
    transmission_phrase: str | None
    node_type: str
    relation_kind: str | None
    narrator: NarratorSummaryRead | None
    confidence: int | None
    resolution_method: str | None
    resolution_reason: str | None
    review_status: str
    candidates: list[ChainNodeCandidateRead]
    person_resolution: NodePersonResolution | None = None


class ChainRead(BaseModel):
    id: int
    chain_number: int
    raw_isnad: str
    parser_version: str
    node_count: int
    flags: str | None
    review_status: str
    nodes: list[ChainNodeRead]


class HadithChainsRead(BaseModel):
    hadith_id: int
    public_id: str
    chains: list[ChainRead]


class NarratorAliasRead(BaseModel):
    id: int
    alias_raw: str
    alias_type: str
    source_note: str | None
    confidence: int


class RijalEntryRead(BaseModel):
    id: int
    entry_kind: str
    entry_number: int | None
    title_raw: str
    volume_start: int | None
    page_start: int | None
    volume_end: int | None
    page_end: int | None
    text_raw: str
    source_url: str | None
    review_status: str


class RijalStatementRead(BaseModel):
    id: int
    source_name: str
    statement_type: str
    quote_raw: str
    evidence_text_raw: str | None
    confidence: int


class RijalOccurrenceRead(BaseModel):
    id: int
    direction: str
    related_name_raw: str
    source_ref_raw: str | None
    evidence_text_raw: str
    confidence: int


class NarratorBookAppearanceCountRead(BaseModel):
    book_id: int
    source_book_id: str
    title_original: str
    total: int


class NarratorHadithAppearanceRead(BaseModel):
    hadith_id: int
    public_id: str
    book_id: int
    source_book_id: str
    book_title: str
    section_title: str | None
    sequence_in_book: int
    printed_number: str | None
    volume_start: int | None
    page_start: int
    page_end: int
    chain_id: int
    chain_number: int
    node_id: int
    node_position: int
    raw_token: str
    confidence: int | None
    resolution_method: str | None
    matn_excerpt: str


class NarratorHadithAppearancePage(BaseModel):
    narrator_id: int
    total: int
    skip: int
    limit: int
    source_book_id: str | None
    appearances: list[NarratorHadithAppearanceRead]


class NarratorTransmissionBookCountRead(BaseModel):
    book_id: int
    source_book_id: str
    title_original: str
    total: int


class NarratorTransmissionSampleRead(BaseModel):
    hadith_id: int
    public_id: str
    book_id: int
    source_book_id: str
    book_title: str
    section_title: str | None
    sequence_in_book: int
    printed_number: str | None
    volume_start: int | None
    page_start: int
    page_end: int
    chain_id: int
    chain_number: int
    node_id: int
    node_position: int
    related_node_id: int
    related_node_position: int
    raw_token: str
    related_raw_token: str
    confidence: int | None
    related_confidence: int | None
    matn_excerpt: str


class NarratorTransmissionEdgeRead(BaseModel):
    related_narrator: NarratorSummaryRead
    total: int
    book_counts: list[NarratorTransmissionBookCountRead]
    samples: list[NarratorTransmissionSampleRead]


class NarratorTransmissionEdgesRead(BaseModel):
    narrator_id: int
    source_book_id: str | None
    teachers: list[NarratorTransmissionEdgeRead]
    students: list[NarratorTransmissionEdgeRead]


class NarratorDetailRead(NarratorSummaryRead):
    aliases: list[NarratorAliasRead]
    rijal_entries: list[RijalEntryRead]
    statements: list[RijalStatementRead]
    occurrences: list[RijalOccurrenceRead]
    occurrences_total: int
    appearance_counts: list[NarratorBookAppearanceCountRead]
    appearances: list[NarratorHadithAppearanceRead]
    appearances_total: int


class HadithSplitReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hadith_id: int
    approved_isnad_raw: str | None
    approved_matn_raw: str | None
    review_status: str
    reviewer: str | None
    notes: str | None
    split_version: str
    created_at: dt.datetime
    updated_at: dt.datetime


class HadithSplitReviewSave(BaseModel):
    approved_isnad_raw: str | None = None
    approved_matn_raw: str
    review_status: str = "approved"
    reviewer: str | None = "local"
    notes: str | None = None


class HadithSplitReviewItem(BaseModel):
    hadith: HadithRead
    review: HadithSplitReviewRead | None = None
    active_isnad_raw: str | None
    active_matn_raw: str
    suspicion_flags: list[str]


class HadithSplitReviewStats(BaseModel):
    source_book_id: str
    total_hadiths: int
    reviewed: int
    approved: int
    needs_review: int
    rejected: int
    unreviewed: int
    suspicious_unreviewed: int


class HadithSplitFlagCount(BaseModel):
    flag: str
    total: int
    unreviewed: int
    approved: int
    needs_review: int
    rejected: int
    examples: list[str]


class HadithSplitAudit(BaseModel):
    source_book_id: str
    total_hadiths: int
    flagged_hadiths: int
    flags: list[HadithSplitFlagCount]


class ChapterSummary(BaseModel):
    """One باب/كتاب run of consecutive hadiths sharing a section title.

    Derived from Hadith.section_title at request time (not stored) — the
    hadith is the unit of reading; chapters are just contiguous runs of
    sequence_in_book.
    """

    index: int
    title: str | None
    volume: int | None
    page_start: int
    hadith_count: int
    start_sequence: int
    end_sequence: int


class TranslationPublicationEvidenceRead(BaseModel):
    status: Literal["human_reviewed", "published"]
    risk_level: Literal["green"]
    risk_flags: list | None = None
    provider: str | None = None
    model: str | None = None
    provenance_json: dict | None = None


class SearchResult(BaseModel):
    page: PageRead
    book: BookSummary
    snippet: str
    match_type: str = "arabic"
    hadith_public_id: str | None = None
    hadith_printed_number: str | None = None
    translation_evidence: TranslationPublicationEvidenceRead | None = None


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[SearchResult]


class LibraryStats(BaseModel):
    books_readable: int
    books_catalogued: int
    pages_digitized: int
    authors: int


class CorpusBookStatus(BaseModel):
    book_id: int
    source_book_id: str
    title_original: str
    pages_digitized: int
    visible_hadiths: int
    parsed_chains: int
    chains_needing_review: int
    public_english_translations: int
    approved_split_reviews: int


class CorpusStatusResponse(BaseModel):
    books: list[CorpusBookStatus]


class TransmissionGraphNode(BaseModel):
    """One person in the corpus-wide transmission graph.

    `id` is the cluster-root person id: same_person_as clusters are collapsed
    into one node so split identities (al-Ash'ari / al-Ash'ari al-Qumi) render
    as one dot. `narrator_id` links to the Mu'jam-backed profile page when the
    person has one.
    """

    id: int
    label: str
    kind: str  # imam | narrator
    generation: int | None
    narrator_id: int | None
    hadith_count: int
    merged_person_ids: list[int]


class TransmissionGraphEdge(BaseModel):
    """Directed student -> teacher edge, weighted by distinct hadith count.

    `quality`/`gen_violation` are populated only when the graph is requested
    with `quality=1`: the eval harness's Mu'jam-corroboration verdict for this
    edge (corroborated | contradicted | under_documented | no_mujam) and whether
    the two endpoints violate ṭabaqa (generation) monotonicity.
    """

    source: int
    target: int
    count: int
    quality: str | None = None
    gen_violation: bool | None = None


class TransmissionGraphRead(BaseModel):
    source_book_id: str
    min_count: int
    max_nodes: int
    total_nodes_unfiltered: int
    total_edges_unfiltered: int
    # How many admin review decisions changed the confident set for this book.
    decisions_applied: int = 0
    # When the underlying pair aggregation was computed (server time). Lets the
    # UI show a "data as of" stamp; the pair stage is TTL-cached server-side.
    computed_at: dt.datetime | None = None
    quality: bool = False
    nodes: list[TransmissionGraphNode]
    edges: list[TransmissionGraphEdge]


class TransmissionEdgeEvidenceItem(BaseModel):
    """One hadith that jointly attests a student->teacher transmission edge."""

    public_id: str
    sequence_in_book: int
    volume_start: int | None
    page_start: int | None
    isnad_excerpt: str | None


class TransmissionEdgeEvidenceRead(BaseModel):
    source_person_id: int
    target_person_id: int
    source_book_id: str
    total: int
    items: list[TransmissionEdgeEvidenceItem]
