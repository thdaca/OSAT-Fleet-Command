# Keep the architecture PDF current

Every future code modification must be reflected in the architecture PDF and
the cumulative changelog. Frozen 0.2.6 application code, tests, resources and
runtime requirements remain unchanged. Future application changes belong to a
new software version; this documentation edition only adds release materials.

## Editable owners

- [ARCHITECTURE_GUIDE.md](ARCHITECTURE_GUIDE.md): plain-English architecture,
  stable internal section IDs S01-S19 and S21. Change only the paragraphs, diagrams, tables or file
  references affected by the implementation change.
- [CHANGELOG.md](CHANGELOG.md): internal section S20, append-only version history from
  0.2.6. Add a version/date, changed files or responsibilities, affected section
  IDs, observable behavior, evidence limits and verification. Keep prior entries.
- [ARCHITECTURE_PDF_STYLE.json](ARCHITECTURE_PDF_STYLE.json): current version,
  document edition, review date and the high-contrast visual specification.
- [render_architecture_pdf.py](render_architecture_pdf.py): documentation-only
  renderer and packaging helper. It is outside the operational architecture.

## For each code modification

1. Identify which guide sections describe the changed behavior or boundary.
   Update those sections without rewriting unaffected explanations. If a purely
   internal change leaves architecture and behavior unchanged, record that in
   the changelog rather than inventing a prose change.
2. Add the change under its new version, or an Unreleased entry while a version
   is pending. At release, give that entry its actual version and date. Do not
   rewrite a previous release's claims or regenerate its frozen evidence.
3. Update current-version metadata, review date and any current source-identity
   statement. Keep section IDs, terminology and visual style stable. Version
   headers, page numbers and the changelog may change automatically; minimal
   revision means minimal substantive changes, not identical PDF binary bytes.
4. Regenerate the working PDF after the change. A pending version can remain a
   draft, but no final ZIP ships with stale architecture or missing history.

## Render and package

Use Python with the optional documentation requirements installed. This is
separate from root runtime requirements:

```powershell
.venv\Scripts\python -m pip install -r docs/requirements-pdf.txt
.venv\Scripts\python docs/render_architecture_pdf.py
```

The output is `.artifacts/output/pdf/OSAT_SemiGuard_Architecture.pdf`.
The renderer starts each architecture chapter on a new page and generates
clickable contents and bookmarks. Expanded stage descriptions use explicit
`::: pagebreak` markers within the same stable section. Continuation pages
repeat the chapter title and retain readable text size. Stage headings get
nested bookmarks so a reader can jump directly to PRE01, STEP07 or POST04.
Keep each stage beginner-friendly: purpose, inputs, processing, outputs, a
concrete example, evidence limits and a contributor entry. Add pages when
needed; do not shrink the approved fonts to fit longer explanations. Reader chapter numbers follow source order;
internal section IDs remain stable when pages move. Keep the catalog in
PRE01-PRE03, STEP01-STEP15, POST01-POST05 order, followed by chronological
preparation and monitoring walkthroughs. Keep both team pages in the same
physical-hypothesis-to-display handoff order. Inspect every page after rendering: readable
body text, dark text on light pages, no clipping or overlap, correctly wrapped
tables, visible state labels, current paths and correct version history.
Longer future history can extend the changelog at the end. Check page transitions.

After the application's required checks and PDF visual review:

```powershell
.venv\Scripts\python docs/render_architecture_pdf.py --package
```

This uses the unchanged release builder and adds exactly one PDF at:

```text
snapshots/<version>.zip
  Semiconductor-industrial-AI-main/
    OSAT_SemiGuard_Architecture.pdf
    docs/ARCHITECTURE_GUIDE.md
    docs/CHANGELOG.md
    docs/ARCHITECTURE_PDF_STYLE.json
    docs/render_architecture_pdf.py
    ...existing application and contributor files...
```

The metadata version must match the application VERSION. An existing same-version
ZIP can receive documentation updates only when its application/resources/tests
and runtime requirements still match byte-for-byte. Code changes require a new
version. The helper verifies member names, CRCs, a unique root PDF and all packaged
bytes before replacing the current ZIP. Historical snapshot archives are untouched.
Report the new ZIP SHA-256; do not embed that ZIP hash inside its own PDF.

## The frozen 0.2.6 root-layout test

The frozen root-organization assertion predates a root-level PDF. It permits
only its original source entries plus local artifact folders. To run that
unchanged suite on an extracted 0.2.6 ZIP, temporarily place the PDF inside
`.artifacts/`, run the ordinary required suite, then restore the PDF to the root.
Keep every application/test source byte unchanged. Validate the complete ZIP and
restored PDF separately; a future code version can recognize this documented
release metadata in its layout check. This is a packaging-only test arrangement,
not a relaxation of scientific, provenance, safety or behavior checks.
