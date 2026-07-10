// Hand-maintained mirror of eshia-research's Pydantic response schemas
// (eshia-research/src/eshia_research/schemas.py). Keep in sync by hand —
// the schema is small and stable enough that generation isn't worth it yet.

export interface CategoryRead {
  id: number;
  source_id: string | null;
  name_original: string;
  name_en: string | null;
  parent_id: number | null;
  source_url: string;
}

export interface AuthorRead {
  id: number;
  name_original: string;
  name_normalised: string;
  source_url: string | null;
}

export interface BookSummary {
  id: number;
  source_book_id: string;
  title_original: string;
  title_normalised: string;
  authors: AuthorRead[];
  source_url: string;
  volume_count: number | null;
  has_content: boolean;
}

export interface BookRead extends BookSummary {
  category: CategoryRead | null;
  language: string | null;
  created_at: string;
  updated_at: string;
}

export interface PageRead {
  id: number;
  book_id: number;
  volume_number: number | null;
  page_number: number;
  text_raw: string | null;
  text_normalised: string | null;
  source_url: string;
  checksum: string;
  scraped_at: string;
  text_blocks: PageTextBlock[] | null;
}

export interface PageIndexEntry {
  id: number;
  book_id: number;
  volume_number: number | null;
  page_number: number;
  source_url: string;
}

export interface PageTextBlock {
  kind: "heading" | "paragraph" | "footnote" | "divider";
  text: string | null;
}

export interface HadithFootnote {
  marker: string;
  text: string;
  volume: number | null;
  page: number | null;
}

export interface HadithRead {
  id: number;
  public_id: string;
  book_id: number;
  page_start_id: number | null;
  page_end_id: number | null;
  sequence_in_book: number;
  sequence_in_page: number;
  printed_number: string | null;
  volume_start: number | null;
  volume_end: number | null;
  page_start: number;
  page_end: number;
  section_title: string | null;
  full_text_raw: string;
  isnad_raw: string | null;
  matn_raw: string;
  footnotes: HadithFootnote[] | null;
  source_url: string;
  extraction_method: string;
  extraction_confidence: number;
  review_status: string;
}

export interface NarratorSummaryRead {
  id: number;
  canonical_name_ar: string;
  canonical_name_en: string | null;
  kunya: string | null;
  laqab: string | null;
  nisba: string | null;
  father_name: string | null;
  death_year_note: string | null;
  generation_layer: number | null;
  school_or_sect: string | null;
  summary_status: string | null;
}

export interface ChainNodeCandidateRead {
  rank: number;
  score: number;
  match_type: string;
  evidence_summary: string | null;
  narrator: NarratorSummaryRead;
}

export interface PersonRef {
  id: number;
  canonical_name_ar: string;
  kind: string;
  narrator_id: number | null;
  generation: number | null;
  generation_method: string | null;
}

export interface MentionCandidateRead {
  rank: number;
  status: string;
  method: string | null;
  person: PersonRef | null;
  evidence_summary: string | null;
}

export interface NodePersonResolution {
  status: string;
  resolved_person: PersonRef | null;
  primary_dalil: string | null;
  candidates: MentionCandidateRead[];
}

export interface PersonResolutionStatusCount {
  status: string;
  total: number;
}

export interface PersonResolutionNodeTypeCount {
  node_type: string;
  status: string;
  total: number;
}

export interface PersonResolutionMethodCount {
  method: string | null;
  status: string;
  total: number;
}

export interface PersonResolutionAuditSummary {
  source_book_id: string;
  total_nodes: number;
  with_rank1_resolution: number;
  without_rank1_resolution: number;
  open_nodes: number;
  status_counts: PersonResolutionStatusCount[];
  node_type_counts: PersonResolutionNodeTypeCount[];
  method_counts: PersonResolutionMethodCount[];
}

export interface PersonResolutionDecisionCount {
  key: string;
  total: number;
}

export interface PersonResolutionDecisionSummary {
  source_book_id: string;
  reviewer: string;
  total_decisions: number;
  decision_counts: PersonResolutionDecisionCount[];
  confidence_counts: PersonResolutionDecisionCount[];
}

export interface PersonResolutionAuditCandidate {
  rank: number;
  status: string;
  method: string | null;
  person: PersonRef | null;
  evidence_summary: string | null;
  score: number | null;
  winner_score: number | null;
  margin_to_winner: number | null;
}

export interface PersonResolutionAdminDecision {
  decision_type: string;
  confidence_tier: string;
  reviewer: string;
  selected_person: PersonRef | null;
  summary: string | null;
  external_verdict: string | null;
  external_case_id: string | null;
  source_reference: string | null;
}

export interface PersonResolutionEffectiveResult {
  source: string;
  status: string;
  label: string;
  person: PersonRef | null;
  reason: string | null;
}

export interface PersonResolutionAuditItem {
  hadith_id: number;
  public_id: string;
  sequence_in_book: number;
  section_title: string | null;
  volume_start: number | null;
  page_start: number;
  page_end: number;
  chain_id: number;
  chain_number: number;
  node_id: number;
  position: number;
  raw_token: string;
  token_normalised: string;
  node_type: string;
  relation_kind: string | null;
  status: string;
  method: string | null;
  resolved_person: PersonRef | null;
  admin_decision: PersonResolutionAdminDecision | null;
  effective_resolution: PersonResolutionEffectiveResult | null;
  primary_dalil: string | null;
  candidates: PersonResolutionAuditCandidate[];
  candidate_count: number;
  top_score: number | null;
  top_margin: number | null;
  risk_flags: string[];
  isnad_excerpt: string | null;
  matn_excerpt: string;
}

export interface PersonResolutionAuditPage {
  source_book_id: string;
  status: string;
  node_type: string | null;
  risk: string | null;
  q: string | null;
  total: number;
  skip: number;
  limit: number;
  items: PersonResolutionAuditItem[];
}

export interface ChainNodeRead {
  id: number;
  position: number;
  raw_token: string;
  token_normalised: string;
  transmission_phrase: string | null;
  node_type: string;
  relation_kind: string | null;
  narrator: NarratorSummaryRead | null;
  confidence: number | null;
  resolution_method: string | null;
  resolution_reason: string | null;
  review_status: string;
  candidates: ChainNodeCandidateRead[];
  person_resolution: NodePersonResolution | null;
}

export interface ChainRead {
  id: number;
  chain_number: number;
  raw_isnad: string;
  parser_version: string;
  node_count: number;
  flags: string | null;
  review_status: string;
  nodes: ChainNodeRead[];
}

export interface HadithChainsRead {
  hadith_id: number;
  public_id: string;
  chains: ChainRead[];
}

export interface NarratorAliasRead {
  id: number;
  alias_raw: string;
  alias_type: string;
  source_note: string | null;
  confidence: number;
}

export interface RijalEntryRead {
  id: number;
  entry_kind: string;
  entry_number: number | null;
  title_raw: string;
  volume_start: number | null;
  page_start: number | null;
  volume_end: number | null;
  page_end: number | null;
  text_raw: string;
  source_url: string | null;
  review_status: string;
}

export interface RijalStatementRead {
  id: number;
  source_name: string;
  statement_type: string;
  quote_raw: string;
  evidence_text_raw: string | null;
  confidence: number;
}

export interface RijalOccurrenceRead {
  id: number;
  direction: string;
  related_name_raw: string;
  source_ref_raw: string | null;
  evidence_text_raw: string;
  confidence: number;
}

export interface NarratorBookAppearanceCountRead {
  book_id: number;
  source_book_id: string;
  title_original: string;
  total: number;
}

export interface NarratorHadithAppearanceRead {
  hadith_id: number;
  public_id: string;
  book_id: number;
  source_book_id: string;
  book_title: string;
  section_title: string | null;
  sequence_in_book: number;
  printed_number: string | null;
  volume_start: number | null;
  page_start: number;
  page_end: number;
  chain_id: number;
  chain_number: number;
  node_id: number;
  node_position: number;
  raw_token: string;
  confidence: number | null;
  resolution_method: string | null;
  matn_excerpt: string;
}

export interface NarratorHadithAppearancePage {
  narrator_id: number;
  total: number;
  skip: number;
  limit: number;
  source_book_id: string | null;
  appearances: NarratorHadithAppearanceRead[];
}

export interface NarratorTransmissionBookCountRead {
  book_id: number;
  source_book_id: string;
  title_original: string;
  total: number;
}

export interface NarratorTransmissionSampleRead {
  hadith_id: number;
  public_id: string;
  book_id: number;
  source_book_id: string;
  book_title: string;
  section_title: string | null;
  sequence_in_book: number;
  printed_number: string | null;
  volume_start: number | null;
  page_start: number;
  page_end: number;
  chain_id: number;
  chain_number: number;
  node_id: number;
  node_position: number;
  related_node_id: number;
  related_node_position: number;
  raw_token: string;
  related_raw_token: string;
  confidence: number | null;
  related_confidence: number | null;
  matn_excerpt: string;
}

export interface NarratorTransmissionEdgeRead {
  related_narrator: NarratorSummaryRead;
  total: number;
  book_counts: NarratorTransmissionBookCountRead[];
  samples: NarratorTransmissionSampleRead[];
}

export interface NarratorTransmissionEdgesRead {
  narrator_id: number;
  source_book_id: string | null;
  teachers: NarratorTransmissionEdgeRead[];
  students: NarratorTransmissionEdgeRead[];
}

export interface NarratorDetailRead extends NarratorSummaryRead {
  aliases: NarratorAliasRead[];
  rijal_entries: RijalEntryRead[];
  statements: RijalStatementRead[];
  occurrences: RijalOccurrenceRead[];
  occurrences_total: number;
  appearance_counts: NarratorBookAppearanceCountRead[];
  appearances: NarratorHadithAppearanceRead[];
  appearances_total: number;
}

export interface HadithSplitReviewRead {
  id: number;
  hadith_id: number;
  approved_isnad_raw: string | null;
  approved_matn_raw: string | null;
  review_status: "approved" | "needs_review" | "rejected" | "unreviewed";
  reviewer: string | null;
  notes: string | null;
  split_version: string;
  created_at: string;
  updated_at: string;
}

export interface HadithSplitReviewItem {
  hadith: HadithRead;
  review: HadithSplitReviewRead | null;
  active_isnad_raw: string | null;
  active_matn_raw: string;
  suspicion_flags: string[];
}

export interface HadithSplitReviewSave {
  approved_isnad_raw: string | null;
  approved_matn_raw: string;
  review_status: "approved" | "needs_review" | "rejected";
  reviewer: string | null;
  notes: string | null;
}

export interface HadithSplitReviewStats {
  source_book_id: string;
  total_hadiths: number;
  reviewed: number;
  approved: number;
  needs_review: number;
  rejected: number;
  unreviewed: number;
  suspicious_unreviewed: number;
}

export interface HadithSplitFlagCount {
  flag: string;
  total: number;
  unreviewed: number;
  approved: number;
  needs_review: number;
  rejected: number;
  examples: string[];
}

export interface HadithSplitAudit {
  source_book_id: string;
  total_hadiths: number;
  flagged_hadiths: number;
  flags: HadithSplitFlagCount[];
}

export interface ChapterSummary {
  index: number;
  title: string | null;
  volume: number | null;
  page_start: number;
  hadith_count: number;
  start_sequence: number;
  end_sequence: number;
}

export interface SearchResult {
  page: PageRead;
  book: BookSummary;
  snippet: string;
}

export interface SearchResponse {
  query: string;
  count: number;
  results: SearchResult[];
}

export interface LibraryStats {
  books_readable: number;
  books_catalogued: number;
  pages_digitized: number;
  authors: number;
}

export interface TransmissionGraphNode {
  id: number;
  label: string;
  kind: "imam" | "narrator";
  generation: number | null;
  narrator_id: number | null;
  hadith_count: number;
  merged_person_ids: number[];
}

export type EdgeQualityVerdict =
  | "corroborated"
  | "contradicted"
  | "under_documented"
  | "no_mujam";

export interface TransmissionGraphEdge {
  source: number;
  target: number;
  count: number;
  quality?: EdgeQualityVerdict | null;
  gen_violation?: boolean | null;
}

export interface TransmissionGraphRead {
  source_book_id: string;
  min_count: number;
  max_nodes: number;
  total_nodes_unfiltered: number;
  total_edges_unfiltered: number;
  decisions_applied: number;
  computed_at: string | null;
  quality: boolean;
  nodes: TransmissionGraphNode[];
  edges: TransmissionGraphEdge[];
}

export interface TransmissionEdgeEvidenceItem {
  public_id: string;
  sequence_in_book: number;
  volume_start: number | null;
  page_start: number | null;
  isnad_excerpt: string | null;
}

export interface TransmissionEdgeEvidenceRead {
  source_person_id: number;
  target_person_id: number;
  source_book_id: string;
  total: number;
  items: TransmissionEdgeEvidenceItem[];
}
