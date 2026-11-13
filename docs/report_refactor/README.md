# OsdagBridge Design Report Generator — Refactoring & Enhancements

Technical changes for the FOSSEE Osdag screening task. The full report with figures is
[`Technical_Report.pdf`](Technical_Report.pdf) (LaTeX source: [`technical_report.tex`](technical_report.tex)).

## Summary

Every table in the report now goes through one PyLaTeX-based builder, and every visual attribute comes
from one style module. All six task items are done and were checked against the same design data before
and after the change. On the sample design (30 m span, 5 girders) the report went from **56 to 46 pages**,
and the hidden LaTeX errors went from **140 to 0**. "Page X of Y" is now correct.

| # | Requirement | Result | Main files |
|---|---|---|---|
| 1 | Repeated table headers | Caption + header repeat on every page (`\endfirsthead` / `\endhead`); short tables never split | `report_tables.py` |
| 2 | Footer overlap & spacing | Row groups (e.g. girder "G4") can no longer split or bleed into the footer; footer drawn inside the bottom margin | `report_tables.py`, `styles.py` |
| 3 | Load tables | Separate vehicle live-load table (Vehicle, Total Load, Impact Factor, Braking: Considered / Value / Eccentricity) and footway table; only vehicles selected in the Loading tab | `chap3.py` |
| 4 | UR charts | Section 5.5: governing UR per element and UR per check, red dashed UR = 1.0 line | `report_charts.py`, `chap5.py` |
| 5 | Material charts | Chapter 7: steel tonnage (girders, bracing, end diaphragms); concrete m³ vs reinforcement MT; embedded via PyLaTeX `Figure` | `report_charts.py`, `chap7.py`, `boq_generator.py` |
| 6 | Central style system | `styles.py` holds page geometry, colours, fonts, table padding, header/footer and chart style | `styles.py` |

## Architecture

The chapters keep their data-extraction code. Only the *presentation* was moved, into three new modules:

```
report_generator.py   orchestration, preamble, ReportDataBridge
  └─ executive_summary, chap1 … chap9
       ├─ every table  → report_tables.ReportTable   (PyLaTeX LongTable / Tabular)
       ├─ every chart  → report_charts               (matplotlib PNG → PyLaTeX Figure)
       └─ every length / colour / font → styles
```

A full PyLaTeX `Document` rewrite would have touched about 4,400 lines of engineering logic. With this
hybrid approach the reported values don't change, and all layout behaviour lives in one place.

## Key layout fixes (root causes)

1. **Split multirow groups.** A girder's 13-row block could break across a page boundary, so the
   `\multirow` label printed in the footer. Rows in a group are now bound together with `\nopagebreak`.
2. **`\cline` is a page-break point.** colortbl's `\cline` ends with `\noalign{\vskip-\arrayrulewidth}`,
   which is a legal break. A non-breaking `\nbcline` (defined in the preamble) is used inside groups.
3. **Orphaned headers.** A `\needspace` placed directly before `\begin{longtable}` moves the break *inside*
   the table, so it was removed. Longtable's own start check now measures the header plus the first group.
4. The footer is one box inside the bottom margin, replacing the old negative `\vspace` in `\footrule`.

## `styles.py` structure

| Item | Contents |
|---|---|
| `PAGE` | paper, font size, margins, header/footer geometry, line spacing |
| `COLORS` | brand, heading ink, table fills, rule colour, PASS/WARN/FAIL colours |
| `TYPOGRAPHY` | heading, caption and note styles |
| `TABLE` | fonts, padding, row stretch, rules, spacing, keep-together / page-bottom thresholds |
| `FIGURE`, `TITLE_PAGE` | figure widths and placement, placeholder style, title-page layout |
| `CHART` | matplotlib DPI, sizes, fonts, series / fail / limit-line colours |
| `HEADER_FOOTER` | running header/footer content and rules |
| `status()`, `ur_value()`, `note()` | uniform PASS/WARN/FAIL badges, UR formatting, notes |
| `build_preamble()` | generates the LaTeX preamble from the settings above |

## Files changed

| File | Change |
|---|---|
| `reports/styles.py` *(new)* | central style configuration + preamble builder |
| `reports/report_tables.py` *(new)* | PyLaTeX table builder |
| `reports/report_charts.py` *(new)* | UR and quantity charts, PyLaTeX `Figure` embedding |
| `reports/report_generator.py` | styles-based preamble/title/TOC, end-diaphragm data view, chart folder, 3 LaTeX passes |
| `reports/report_utils.py` | unicode-safe escaping, float formatting, placeholder box |
| `reports/executive_summary.py`, `chap1`–`chap8` | tables moved to the builder + chapter changes |
| `boq/boq_generator.py` | end-diaphragm quantities |
| `utils/codes/irc6_2017.py` | braking force: `NameError` for 1–2 lanes, N → tonne unit fix |
| `tools/report_preview.py` *(new)* | headless preview / before-after reproduction |
| `environment.yml`, `pyproject.toml` | `pylatex` dependency |

## Additional fixes

- The End Diaphragm tables were showing **cross-bracing data** (40×40×3 instead of IS 100×100×10). They now
  read the end-diaphragm data, and when the analysis returns no diaphragm forces the checks are marked "not evaluated".
- "Page X of Y" was one page short: the `titlepage` environment reset the counter, and two passes weren't enough.
- 140 hidden LaTeX errors, including unescaped ≤/≥ in check names and an unclosed `\begingroup`, are fixed.
- Braking force printed "N/A" because of a `NameError`. After that fix, the function returned newtons labelled
  as tonnes. Both are fixed: 108.7 kN for 2 lanes.
- Computed wind and seismic coefficients are now printed (they were computed but dropped). Float noise is trimmed.
  Table 4.2 is populated, transverse shear appears in the summary, and Executive Summary tables are numbered ES.1/ES.2.

## Reproducing Before / After

```bash
conda activate osdagbridge-env
python tools/report_preview.py design --snapshot snap.pkl
python tools/report_preview.py report --snapshot snap.pkl --stem Report_After
python tools/report_preview.py report --snapshot snap.pkl --stem Report_Before --src <path-to-dev-checkout>/src
```

The headless preview shows placeholder boxes for the CAD views. Use the desktop app
(Design → Generate Report) for the fully illustrated report.

## Known limitations

- The wheeled 70R/AA impact factor comes from the existing IRC 6 Cl. 208.3 function, which doesn't distinguish
  wheeled from tracked vehicles. It was left unchanged because it is design logic, not report code.
- The analysis does not return end-diaphragm member forces, so those capacity checks show "not evaluated".
