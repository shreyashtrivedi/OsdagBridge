# =============================================================================
# OsdagBridge Report — PyLaTeX table builder
# =============================================================================
#
# Every table in the report is produced through ``ReportTable`` so that all
# tables share one look (styles.TABLE / styles.COLORS) and one set of
# page-break rules:
#
#   * Built on ``pylatex.LongTable``.  The caption + column header is emitted
#     in ``\endfirsthead``; a "(continued)" caption + the same header row is
#     emitted in ``\endhead`` so the header repeats on EVERY page the table
#     spans.  A "continued on next page" line is placed in ``\endfoot``.
#   * Notes are attached in ``\endlastfoot`` so they can never be orphaned
#     on the next page.
#   * Column widths are given as relative weights and converted to
#     ``\linewidth``-based dimensions, so a table can never run into the
#     margin regardless of page geometry.
#   * Row groups (e.g. one girder spanning several rows via ``\multirow``)
#     are kept on one page (``\nopagebreak`` between their rows); this stops
#     a multirow label such as "G4" from being pushed into the footer.
#   * Short tables (<= styles.TABLE['keep_together_max_rows'] rows) are kept
#     together and move to the next page as a whole.
#
# Cell contents are expected to be LaTeX-ready strings (already escaped with
# ``report_utils._tex`` where they carry user data).
# =============================================================================

from dataclasses import dataclass

from pylatex import LongTable, MultiColumn, MultiRow, NoEscape, Tabular

from osdagbridge.core.reports.styles import TABLE, TYPOGRAPHY

_ALIGN = {
    "l": r"\raggedright",
    "c": r"\centering",
    "r": r"\raggedleft",
    "j": "",
}


@dataclass
class Col:
    """One table column.

    header : header text (LaTeX); may contain ``\\\\`` line breaks.
    weight : relative width (any positive number; normalised per table).
    align  : 'l' | 'c' | 'r' | 'j' (justified).
    """
    header: str = ""
    weight: float = 1.0
    align: str = "l"


def _cell(value):
    """Normalise a cell value: None/'' -> empty marker, everything -> NoEscape."""
    if isinstance(value, (MultiColumn, MultiRow)):
        return value
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return NoEscape(TABLE["empty_cell"])
    return NoEscape(str(value))


def _bold(text):
    """Header cell text.  ``\\\\`` marks a preferred line break; long headers
    still wrap automatically inside the fixed-width column."""
    if not text:
        return ""
    parts = text.split(r"\\")
    if TABLE["header_bold"]:
        parts = [r"\textbf{" + p.strip() + "}" for p in parts]
    return r"\newline ".join(parts)


class ReportTable:
    """A styled, page-break-aware longtable.

    Parameters
    ----------
    caption : str        Table caption (LaTeX).  Numbered automatically.
    columns : list[Col]  Column definitions.
    note : str           Optional note printed directly under the table.
    width : float        Fraction of the text width used by the table.
    show_header : bool   Emit the column-header row (False for key/value
                         tables that have no header).
    header_tex : list    Optional raw LaTeX header rows (each a full row
                         ending in ``\\\\``) replacing the generated header —
                         for multi-level headers.
    font : str           Override styles.TABLE font.
    keep_together : bool Force/disable keeping the whole table on one page.
    label : str          Optional ``\\label``.
    """

    def __init__(self, caption, columns, *, note=None, width=1.0, show_header=True,
                 header_tex=None, font=None, keep_together=None, label=None):
        if not columns:
            raise ValueError("ReportTable needs at least one column")
        self.caption = caption
        self.columns = list(columns)
        self.note = note
        self.width = float(width)
        self.show_header = show_header
        self.header_tex = header_tex
        self.font = font
        self.keep_together = keep_together
        self.label = label
        self._items = []          # ('row', cells, keep_with_next) | ('group', ...) | ('section', text)
        self._n_rows = 0

    # ── public API ──────────────────────────────────────────────────────────
    @property
    def ncols(self):
        return len(self.columns)

    def row(self, *cells, keep_with_next=False):
        """Add one body row.  ``cells`` may be given as varargs or one list."""
        if len(cells) == 1 and isinstance(cells[0], (list, tuple)):
            cells = tuple(cells[0])
        self._check(cells)
        self._items.append(("row", cells, keep_with_next))
        self._n_rows += 1
        return self

    def rows(self, rows):
        for r in rows:
            self.row(*r)
        return self

    def group(self, label, rows, *, label_cols=1):
        """Add a block of rows whose first ``label_cols`` column(s) show one
        merged label (``\\multirow``).  The block is never split across pages.
        ``rows`` contain only the remaining cells."""
        rows = [tuple(r) for r in rows if r is not None]
        if not rows:
            return self
        for r in rows:
            self._check((None,) * label_cols + r)
        self._items.append(("group", label, rows, label_cols))
        self._n_rows += len(rows)
        return self

    def section(self, text):
        """Full-width shaded sub-heading row inside the table."""
        self._items.append(("section", text))
        self._n_rows += 1
        return self

    def dumps(self):
        """Return the LaTeX source of the table.

        Short tables (<= keep_together_max_rows, or keep_together=True) are
        emitted as a PyLaTeX ``Tabular`` inside an unbreakable minipage, so they
        move to the next page as a whole.  Longer tables use ``LongTable`` with
        a repeated header on every page.
        """
        keep_all = self.keep_together
        if keep_all is None:
            keep_all = self._n_rows <= TABLE["keep_together_max_rows"]
        font = self.font or (TABLE["font_dense"] if self.ncols >= TABLE["dense_from_cols"] else TABLE["font"])
        body = self._dumps_block() if keep_all else self._dumps_long()
        return "\n" + r"\begingroup" + font + "\n" + body + "\n" + r"\endgroup" + "\n"

    def _emit_body(self, table, allow_nobreak):
        flat = self._flatten()
        for idx, (kind, payload, no_break, cline) in enumerate(flat):
            last = idx == len(flat) - 1
            if kind == "row":
                table.add_row(payload, strict=True)
            else:  # pre-rendered raw row
                table.append(NoEscape(payload))
            # Rows of a group are bound together: a penalty after the row and a
            # non-breaking partial rule (\nbcline, defined in styles.py) — the
            # standard \cline ends in a \vskip that is itself a breakpoint.
            bind = allow_nobreak and no_break and not last
            if bind:
                table.append(NoEscape(r"\nopagebreak"))
            if cline:
                if allow_nobreak:
                    table.append(NoEscape(r"\nbcline{" + f"{cline[0]}-{cline[1]}" + "}"))
                else:
                    table.add_hline(cline[0], cline[1])
            else:
                table.add_hline()
            if bind:
                table.append(NoEscape(r"\nopagebreak"))

    def _note_tex(self):
        if not self.note:
            return ""
        return (r"\par\vspace{2pt}\parbox{" + self._total_width() + r"}{\raggedright"
                + TYPOGRAPHY["note_font"] + r"\textit{" + self.note + r"}}")

    def _dumps_block(self):
        """Unbreakable table: caption + tabular + note in one minipage."""
        table = Tabular(self._spec())
        self._emit_header(table)
        self._emit_body(table, allow_nobreak=False)
        cap = ""
        if self.caption:
            cap = r"\captionof{table}{" + self.caption + "}" + (
                (r"\label{" + self.label + "}") if self.label else "") + "\n"
        return (r"\par\vspace{\LTpre}\noindent\begin{minipage}{\linewidth}\centering" + "\n"
                + cap + table.dumps() + "\n" + self._note_tex() + "\n"
                + r"\end{minipage}\par\vspace{\LTpost}")

    def _dumps_long(self):
        n = self.ncols
        table = LongTable(self._spec())

        # First-page head: caption + header
        cap = self.caption or ""
        if cap:
            lbl = (r"\label{" + self.label + "}") if self.label else ""
            table.append(NoEscape(r"\caption{" + cap + "}" + lbl + r"\\"))
        self._emit_header(table)
        table.append(NoEscape(r"\endfirsthead"))

        # Continuation head: "(continued)" caption + header repeated on every page
        if cap:
            table.append(NoEscape(r"\caption[]{" + cap + TABLE["continued_caption_suffix"] + r"}\\"))
        self._emit_header(table)
        table.end_table_header()

        # Foot on pages where the table continues
        table.append(NoEscape(
            r"\multicolumn{" + str(n) + r"}{@{}r@{}}{\rule{0pt}{2.4ex}" + TYPOGRAPHY["note_font"]
            + " " + TABLE["continued_text"] + r"}\\"))
        table.end_table_footer()

        # Last foot: the note (kept with the final rows of the table)
        if self.note:
            table.append(NoEscape(
                r"\multicolumn{" + str(n) + r"}{@{}p{" + self._total_width() + r"}@{}}{"
                r"\rule{0pt}{2.6ex}" + TYPOGRAPHY["note_font"] + r"\textit{" + self.note + r"}}\\"))
        table.end_table_last_footer()
        self._emit_body(table, allow_nobreak=True)

        # Page-bottom threshold: longtable's own start check (\LT@start) moves
        # the table to a new page when caption + header + foot + the first row
        # do not fit.  Because group rows are bound together, the "first row"
        # it measures is the whole first group, so a header is never orphaned.
        # (An explicit \needspace directly before \begin{longtable} must NOT be
        # used: its penalty-9999 breakpoint lets the break fall inside the
        # table, leaving only the "continued" foot on the old page.)
        return table.dumps()

    # ── internals ───────────────────────────────────────────────────────────
    def _check(self, cells):
        span = 0
        for c in cells:
            span += c.size if isinstance(c, MultiColumn) else 1
        if span != self.ncols:
            raise ValueError(
                f"Row has {span} cells but table '{self.caption}' has {self.ncols} columns")

    def _weights(self):
        total = sum(max(c.weight, 0.01) for c in self.columns)
        return [max(c.weight, 0.01) / total * self.width for c in self.columns]

    def _total_width(self):
        return r"\dimexpr " + f"{self.width:.4f}" + r"\linewidth\relax"

    def _col_dim(self, frac):
        return (r"\dimexpr " + f"{frac:.4f}" + r"\linewidth-2\tabcolsep-1.2\arrayrulewidth\relax")

    def _spec(self):
        parts = []
        for col, frac in zip(self.columns, self._weights()):
            align = _ALIGN.get(col.align, r"\raggedright")
            pre = (r">{" + align + r"\arraybackslash}") if align else ""
            parts.append(pre + "m{" + self._col_dim(frac) + "}")
        return "|" + "|".join(parts) + "|"

    def _emit_header(self, table):
        table.add_hline()
        if self.header_tex:
            for raw in self.header_tex:
                table.append(NoEscape(r"\rowcolor{tblHeaderBg}" + raw))
            table.add_hline()
        elif self.show_header:
            cells = [NoEscape(_bold(c.header)) for c in self.columns]
            table.add_row(cells, color="tblHeaderBg", strict=True)
            table.add_hline()

    def _flatten(self):
        """Expand items to a list of (kind, payload, no_break, (cline_from, cline_to)|None)."""
        out = []
        n = self.ncols
        for item in self._items:
            kind = item[0]
            if kind == "row":
                _, cells, kwn = item
                out.append(("row", [_cell(c) for c in cells], kwn, None))
            elif kind == "section":
                txt = item[1]
                raw = (r"\rowcolor{tblSectionBg}\multicolumn{" + str(n) + r"}{|l|}{\textbf{" + txt + r"}}\\")
                out.append(("raw", raw, True, None))
            elif kind == "group":
                _, label, rows, lc = item
                k = len(rows)
                for i, r in enumerate(rows):
                    if i == 0:
                        lead = [MultiRow(k, data=NoEscape(r"\makecell{" + str(label) + "}"))]
                        lead += [NoEscape("")] * (lc - 1)
                    else:
                        lead = [NoEscape("")] * lc
                    cells = lead + [_cell(c) for c in r]
                    last_in_group = i == k - 1
                    cline = None if last_in_group else (lc + 1, n)
                    out.append(("row", cells, not last_in_group, cline))
        return out


# =============================================================================
# Convenience builders
# =============================================================================

def kv_table(caption, rows, *, note=None, headers=("Parameter", "Value"),
             weights=(0.40, 0.60), show_header=True, **kw):
    """Two-column parameter / value table.

    ``rows`` is an iterable of (parameter, value) pairs; ``None`` entries are
    skipped so callers can include rows conditionally.
    """
    t = ReportTable(caption,
                    [Col(headers[0], weights[0], "l"), Col(headers[1], weights[1], "l")],
                    note=note, show_header=show_header, **kw)
    for r in rows:
        if r is None:
            continue
        t.row(r[0], r[1])
    return t.dumps()


def multicol(text, size, align="c", first=False):
    """A merged cell spanning ``size`` columns.

    Keeps the vertical grid rules: the right rule always, the left rule only
    when the merged cell starts the row (``first=True``).
    """
    spec = ("|" if first else "") + align + "|"
    return MultiColumn(size, align=spec, data=NoEscape(text))
