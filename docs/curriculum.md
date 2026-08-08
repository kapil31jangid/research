# Curriculum architecture

RAPID-Learn uses the hierarchy:

```text
Board → Class → Subject → Book → Chapter → Concept → Activity / Question
```

The validated registry is `data/curriculum/ncert/registry.json`. It represents NCERT
Classes 1–12 without assuming that every class has the same subjects. A subject has
an `available`, `partial`, or `planned` status; only `available` subjects are eligible
for learner pathways. Metadata is loaded separately from lesson bodies.

## Available content packs

- `ncert-class-5-mathematics` version `1.0.0`: the validated number foundations and
  fraction concepts, preserving all legacy concept IDs.
- `ncert-class-6-mathematics` version `1.0.0`: original Number Play and Fractions
  activities across four concepts, with cross-chapter and cross-class prerequisites.

Each pack has a manifest identifying its board, class, subject, version, language,
content origin, and official NCERT reference. Classes without an available pack are
shown as coming soon and cannot strand a learner in an empty adaptive pathway.

## Content integrity and alignment

Startup validation rejects duplicate identifiers, invalid class/status values,
unknown board/subject/book/chapter relationships, duplicate chapter sequences,
concepts without valid chapters, broken prerequisites, unknown activity/question
concepts, missing learner content, and invalid manifests. Every authored activity is
marked `original_adaptive_material`.

RAPID-Learn contains original adaptive instructional material aligned to curriculum
topics. NCERT/ePathshala references may be stored for alignment and attribution. The
application does not redistribute complete NCERT textbook content or present its
original explanations as official NCERT text.

## Learner pathways and prerequisites

A learner persists an active board, class, subject, book, and chapter. Question and
recommendation candidates stay within the active subject. Concept state is not
deleted on a pathway switch, so returning to a subject restores its progress.
Prerequisite edges may cross chapters or classes; an earlier-class activity is only
surfaced as a labelled `prerequisite_review`.

## Offline and research identity

IndexedDB content keys include board, class, subject, and activity identity. Queued
answers preserve their original curriculum context, so switching subjects before
reconnection cannot silently reinterpret an answer. Interaction/recommendation
records and synthetic experiment rows contain compact curriculum IDs and pack
version for reproducibility.

Existing SQLite databases receive additive columns and legacy learners with strong
fraction-pathway signals default to NCERT Class 5 Mathematics. For production-grade
deployment, use a managed migration framework rather than the prototype's additive
SQLite compatibility helper.
