---
name: Usul16
description: A living, source-verifiable research environment for Shia hadith.
colors:
  scholars-green: "oklch(45% 0.075 160)"
  scholars-green-deep: "oklch(37% 0.065 160)"
  deep-ink: "oklch(26% 0.035 155)"
  study-cream: "oklch(95.3% 0.018 83)"
  reading-cream: "oklch(98.3% 0.015 83)"
  study-layer: "oklch(91.8% 0.025 83)"
  quiet-surface: "oklch(96.2% 0.02 83)"
  citation-bronze: "oklch(47% 0.06 65)"
  muted-ink: "oklch(43% 0.025 150)"
  hairline: "oklch(85% 0.025 83)"
  hairline-strong: "oklch(72% 0.035 82)"
  status-soft: "oklch(91% 0.038 155)"
  status-ink: "oklch(37% 0.068 158)"
  night-study: "oklch(18% 0.018 155)"
  night-surface: "oklch(24% 0.023 155)"
  night-ink: "oklch(93% 0.022 83)"
  night-green: "oklch(75% 0.07 160)"
  night-bronze: "oklch(76% 0.07 72)"
  night-muted: "oklch(73% 0.025 100)"
  library-stage: "oklch(23% 0.032 155)"
  library-stage-deep: "oklch(17% 0.025 155)"
  library-stage-ink: "oklch(93% 0.022 83)"
  library-stage-accent: "oklch(78% 0.07 160)"
  library-stage-line: "oklch(34% 0.03 155)"
typography:
  display:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "4.5rem"
    fontWeight: 600
    lineHeight: 1.08
    letterSpacing: "normal"
  headline:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "3rem"
    fontWeight: 600
    lineHeight: 1.12
    letterSpacing: "normal"
  title:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.3
  body:
    fontFamily: "Instrument Sans, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.75
  label:
    fontFamily: "Instrument Sans, Arial, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.4
  arabic:
    fontFamily: "Amiri, serif"
    fontSize: "1.65rem"
    fontWeight: 400
    lineHeight: 2.15
rounded:
  none: "0px"
  sm: "4px"
  md: "8px"
  book: "10px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  2xl: "48px"
  3xl: "64px"
components:
  button-primary:
    backgroundColor: "{colors.scholars-green}"
    textColor: "{colors.reading-cream}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
    height: "40px"
  button-primary-hover:
    backgroundColor: "{colors.scholars-green-deep}"
    textColor: "{colors.reading-cream}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
    height: "40px"
  button-secondary:
    backgroundColor: "{colors.reading-cream}"
    textColor: "{colors.deep-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
    height: "40px"
  search-input:
    backgroundColor: "{colors.reading-cream}"
    textColor: "{colors.deep-ink}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "0 12px 0 48px"
    height: "56px"
  status-chip:
    backgroundColor: "{colors.status-soft}"
    textColor: "{colors.status-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "2px 10px"
  reader-record:
    backgroundColor: "{colors.reading-cream}"
    textColor: "{colors.deep-ink}"
    typography: "{typography.arabic}"
    rounded: "{rounded.none}"
    padding: "28px"
---

# Design System: Usul16

## Overview

**Creative North Star: "The Living Reference"**

Usul16 should feel like a body of scholarship that is actively navigable rather than a digital facsimile left on a shelf. The interface is calm and exacting at rest, then becomes quietly magnificent when a user opens a physical book, follows a narrator through a chain, or sees a transmission network resolve into evidence. Beauty comes from typographic authority, proportion, material contrast, and purposeful motion.

Research surfaces remain disciplined and familiar. Source text, citations, controls, and evidence use conventional affordances so the tool disappears into the scholarly task. Expressive material is concentrated in the library bindings and network visualisation, never sprayed across every container.

The system explicitly rejects flashy or gamified design, sterile corporate dashboards, antiquated religious-text websites, difficult navigation, clunky interactions, and anything that feels abandoned or discontinued.

**Key Characteristics:**

- Calm, high-contrast research surfaces.
- A clear route from reading to searching to investigating.
- Arabic treated as the primary scholarly text.
- Tactile physical books as the signature library metaphor.
- Motion that reveals state, structure, or material.

## Colors

The palette combines warm olive-cream reading surfaces with authoritative green ink and a limited bronze reserved for bibliographic meaning. Cream is structural rather than ornamental: it reduces glare and softens long reading sessions without imitating parchment.

### Primary

- **Scholar's Green** (`scholars-green`): Primary actions, active navigation, links, focus, and selected research states. Its darker companion is reserved for hover and pressed states.

### Secondary

- **Citation Bronze** (`citation-bronze`): Printed-page references, source metadata, book tooling, and restrained ornamental details. It never substitutes for the primary action colour.

### Neutral

- **Deep Ink** (`deep-ink`): Primary light-theme text and strong structural marks.
- **Study Cream** (`study-cream`): Default application background; a restrained cream balanced toward the green identity rather than a yellow parchment effect.
- **Reading Cream** (`reading-cream`): Arabic reading records, inputs, and focused content surfaces.
- **Study Layer** (`study-layer`) and **Quiet Surface** (`quiet-surface`): Secondary regions and subtle hierarchy without shadows.
- **Muted Ink** (`muted-ink`): Secondary prose and metadata; its contrast is intentionally strong enough for older readers.
- **Hairline** (`hairline`) and **Hairline Strong** (`hairline-strong`): Dividers, field borders, and structural boundaries.
- **Night Study**, **Night Surface**, **Night Ink**, **Night Green**, **Night Bronze**, and **Night Muted**: The low-light reading equivalents. Dark mode is a reading accommodation, not a neon alternative identity.
- **Library Stage**, **Library Stage Deep**, **Library Stage Ink**, **Library Stage Accent**, and **Library Stage Line**: A committed dark-green environment reserved for choosing physical collections. This is the one surface where the library becomes spatial and materially expressive; it must not leak into search, reader, narrator, or evidence panels.

**The Scholar's Green Rule.** Green means action, selection, focus, or navigable scholarship. It is not decorative filler.

**The Bronze Means Evidence Rule.** Bronze marks bibliography, provenance, print, and material book detail. If an element is not evidence-adjacent, it does not earn bronze.

## Typography

**Display Font:** Source Serif 4 (with Georgia fallback)  
**Body Font:** Instrument Sans (with Arial fallback)  
**Arabic Font:** Amiri (with serif fallback)

**Character:** Source Serif carries literary authority without imitating an old manuscript. Instrument Sans keeps navigation and research controls contemporary. Amiri receives generous vertical space so Arabic remains readable through long sessions.

### Hierarchy

- **Display** (600, `4.5rem`, `1.08`): Public-facing homepage statements only; it must wrap safely before mobile widths.
- **Headline** (600, `3rem`, `1.12`): Page titles and major section introductions.
- **Title** (600, `1.5rem`, `1.3`): Record titles and local information hierarchy.
- **Body** (400, `1rem`, `1.75`): Explanatory prose, capped at roughly 70 characters per line.
- **Label** (600, `0.875rem`, normal spacing): Controls, navigation, and compact metadata. Uppercase is exceptional, never the default scaffold.
- **Arabic** (400, `1.65rem`, `2.15`): Default matn reading size, with compact and large user-selectable modes.

**The Two Reading Voices Rule.** Serif belongs to public hierarchy, sans belongs to product operation, and Amiri belongs to source content. Do not use display typography in controls.

## Elevation

The product is structurally flat. Hierarchy comes from surface changes, whitespace, dividers, and typography. Shadows are not a default container treatment; they are reserved for temporary raised menus and the physical material illusion of a book. Reader records and research panels remain flat even when interactive.

### Shadow Vocabulary

- **Menu Lift:** A compact, directional shadow used only while a menu overlays content.
- **Book Material:** A directional physical shadow attached to the page block and cover, never copied onto ordinary cards.

**The Flat-by-Default Rule.** If a border and tonal layer already establish the hierarchy, a shadow is forbidden.

## Components

### Buttons

- **Shape:** Gently squared (`8px`) with a minimum control height of `40px`.
- **Primary:** Scholar's Green with Reading Cream text and `10px 16px` padding.
- **Hover / Focus:** Hover deepens to Scholar's Green Deep over `180–200ms`; keyboard focus uses a clearly visible green ring. Pressed state must feel immediate and disabled state must retain readable text.
- **Secondary:** Reading Cream with a Hairline border and Deep Ink text. It becomes green only through border and text on hover.

### Chips

- **Style:** Full pills are reserved for genuine compact metadata, status, hadith identifiers, and filters.
- **State:** Verified states use Status Soft with Status Ink. Unselected metadata stays neutral; pills are never used as decorative headings.

### Cards / Containers

- **Corner Style:** Research records are square; generic utility containers may use `8px`. Large rounded marketing cards are forbidden.
- **Background:** Reading Cream for primary records, Quiet Surface or Study Layer for secondary regions.
- **Shadow Strategy:** Flat by default; see Elevation.
- **Border:** One-pixel Hairline borders separate records when necessary.
- **Internal Padding:** `20–28px` for reading records, `16–24px` for controls and utility panels.

### Inputs / Fields

- **Style:** Reading Cream, one-pixel Hairline border, `8px` corners, clear native-feeling controls, and a minimum `40px` touch height.
- **Focus:** Scholar's Green border plus a visible focus ring. Placeholder text must remain at least WCAG AA contrast.
- **Error / Disabled:** Errors use explicit text and semantic colour; disabled controls remain legible and visibly inactive.

### Navigation

The header is a `72px` study surface with restrained dividers. Its permanent mental model is **Read / Find / Investigate**, each paired with a short functional description on wide screens. Navigation uses Instrument Sans at `14px`; active state is communicated through Scholar's Green text, a quiet tonal surface, and a two-pixel underline. Mobile navigation uses a familiar menu button and a full-width list, with no invented gestures.

### Research Folio

The homepage may demonstrate the source-verification model through a compact research folio: one flat, edition-like surface showing record ID, chain, Arabic matn, and printed citation together. It uses existing Reading Cream / Night Surface neutrals and Citation Bronze for evidence. It is a real product explanation, not a decorative manuscript card, and should never be repeated as a generic container.

### Research Paths

Read, Find, and Investigate appear as one connected, divider-based row rather than three floating cards. Each path uses one familiar line icon, a direct explanation, and a verb-led destination. This pattern establishes the product's navigation model and may be reused only when all three routes genuinely need equal prominence.

### Evidence Sequence

The text-to-evidence progression is an actual ordered workflow: source text, translation aid, narrator identity, transmission evidence, and stable citation. It uses a vertical ruled sequence with small bronze step numbers because order carries information here. Do not generalise numbered markers to unrelated sections.

### Physical Book

The library's signature component uses an unaltered scan or photograph of the exact catalogued edition cover, visible page edges, and a restrained cover-opening interaction. Never invent a title treatment, binding colour, ornament, publisher mark, or plausible substitute. When no edition image has been verified, show a clearly labelled archival placeholder that says the cover scan is unavailable. The book effect belongs to selection and orientation; it never appears inside the reader or research tools.

### Motion

Motion explains state and material. Authentic book covers lift and open by a few degrees; the homepage research folio traces its chain on hover; research paths and evidence steps acknowledge direct attention. Product transitions normally take `180–260ms`, while the physical book may take up to `420ms`. There is no continuous ambient motion or broad page-load choreography, and `prefers-reduced-motion` removes transforms and transition delays without hiding content.

### Arabic Reader

Reading records centre Arabic within a constrained column, preserve generous line height, separate isnad from matn, and expose English, footnotes, and narrator evidence progressively. Compact, comfortable, and large Arabic sizes are mandatory.

**The Familiar Controls Rule.** Standard research actions use standard affordances. Distinctiveness comes from the corpus and its material, not from making buttons or navigation strange.

## Do's and Don'ts

### Do:

- **Do** keep finding, reading, and investigating equally reachable throughout the product.
- **Do** use Scholar's Green for actions and Citation Bronze for source or print meaning.
- **Do** preserve at least WCAG 2.2 AA contrast, keyboard operation, reduced-motion behaviour, clear focus, and comfortable touch targets.
- **Do** constrain long prose to roughly `65–75ch` and Arabic reading records to a focused central column.
- **Do** use purposeful motion for state, structure, or physical material; honour reduced motion with an immediate alternative.
- **Do** concentrate expressive detail in physical books and the transmission network while keeping research records calm.

### Don't:

- **Don't** make Usul16 feel flashy or gamified.
- **Don't** turn research pages into a sterile corporate dashboard.
- **Don't** imitate an antiquated religious-text website through faux parchment, ornamental overload, or difficult navigation.
- **Don't** ship clunky interactions or anything that feels abandoned or discontinued.
- **Don't** use gradients on text, decorative glassmorphism, repeated glow cards, or full-page choreography.
- **Don't** use a coloured side stripe thicker than `1px` as a card or callout accent.
- **Don't** use the physical-book treatment for hadith records, narrator profiles, search results, or controls.
- **Don't** hide source verification, citation, or the Arabic authority behind decorative interaction.
