# =============================================================================
# OsdagBridge Report — Centralized Formatting & Style System
# =============================================================================
#
# SINGLE SOURCE OF TRUTH for every visual attribute of the design report:
#
#   * PAGE          paper, font size, margins, header/footer geometry
#   * COLORS        brand palette, table fills, rule colour, status colours
#   * TYPOGRAPHY    heading styles, caption style, line spacing
#   * TABLE         padding, row height, rules, fonts, page-break thresholds
#   * FIGURE        default image widths and spacing
#   * CHART         matplotlib palette, sizes, fonts (for generated plots)
#   * HEADER_FOOTER running header / footer content and rules
#
# Chapter modules MUST NOT hardcode lengths, colours or fonts.  They import
# helpers from here (``status()``, ``note()``) or build tables/figures through
# ``report_tables`` / ``report_charts``, which in turn read these settings.
# To restyle the whole report, edit the dictionaries below — nothing else.
# =============================================================================

from osdagbridge.core.reports.report_utils import _tex

# ─────────────────────────────────────────────────────────────────────────────
# 1. PAGE GEOMETRY
# ─────────────────────────────────────────────────────────────────────────────
# The body text area never overlaps the header or footer: the header lives
# inside ``top`` and the full (multi-line) footer lives inside ``bottom``.
#   footer depth  ≈ footskip + 3 footer lines  (<  bottom)
PAGE = {
    "paper":       "a4paper",
    "font_size":   "11pt",
    "top":         "26mm",
    "bottom":      "27mm",
    "left":        "20mm",
    "right":       "20mm",
    "headheight":  "15pt",
    "headsep":     "7mm",
    "footskip":    "9mm",
    "line_stretch": 1.12,
    "par_skip":    "4pt",
}

# ─────────────────────────────────────────────────────────────────────────────
# 2. COLOUR PALETTE  (HTML hex, no leading '#')
# ─────────────────────────────────────────────────────────────────────────────
COLORS = {
    # Brand
    "osdagGreen":      "91B014",   # rules, accents (Osdag brand colour)
    "osdagGreenDark":  "4F6608",   # heading text (AA contrast on white)
    "osdagInk":        "1F2A10",   # chapter title ink
    # Tables
    "tblHeaderBg":     "E9F0D3",   # header row fill
    "tblSectionBg":    "F4F7EA",   # in-table section rows / group labels
    "tblRule":         "9A9A93",   # grid lines
    # Text
    "textMuted":       "52514E",
    # Status (text colours, chosen for >= 4.5:1 contrast on white)
    "statusPass":      "006300",
    "statusWarn":      "9A5B00",
    "statusFail":      "C62828",
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. TYPOGRAPHY
# ─────────────────────────────────────────────────────────────────────────────
TYPOGRAPHY = {
    "heading_family": r"\sffamily",
    "chapter_label":  r"\small\sffamily\bfseries\color{osdagGreen}",
    "chapter_title":  r"\LARGE\sffamily\bfseries\color{osdagInk}",
    "chapter_rule":   "0.9pt",
    "chapter_space_before": "0pt",
    "chapter_space_after":  "14pt",
    "section":        r"\large\sffamily\bfseries\color{osdagGreenDark}",
    "section_space_before": "14pt",
    "section_space_after":  "6pt",
    "subsection":     r"\normalsize\sffamily\bfseries\color{osdagGreenDark}",
    "caption_font":   "small",
    "caption_label":  "bf",
    "caption_text":   "bf",
    "caption_skip":   "4pt",
    "note_font":      r"\footnotesize",
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. TABLE STYLE
# ─────────────────────────────────────────────────────────────────────────────
TABLE = {
    "font":            r"\small",       # default table body font
    "font_dense":      r"\footnotesize",# wide/dense tables (7+ columns)
    "dense_from_cols": 7,
    "col_sep":         "4.5pt",         # \tabcolsep  (horizontal cell padding)
    "row_stretch":     1.30,            # \arraystretch (vertical cell padding)
    "extra_row_height": "1.5pt",        # \extrarowheight (top padding)
    "rule_width":      "0.4pt",         # \arrayrulewidth
    "header_bold":     True,
    "space_before":    "8pt",           # gap above each table (\LTpre)
    "space_after":     "10pt",          # gap below each table (\LTpost)
    # Page-bottom threshold: a table (caption + header + first rows) only
    # starts on the current page if at least this many lines remain.
    "needspace_lines": 7,
    # Tables with at most this many body rows are kept on one page
    # (they move to the next page as a whole instead of splitting).
    "keep_together_max_rows": 12,
    "continued_text":  r"\textit{continued on next page}",
    "continued_caption_suffix": r" \textnormal{\textit{(continued)}}",
    "empty_cell":      r"---",
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. FIGURES
# ─────────────────────────────────────────────────────────────────────────────
FIGURE = {
    "default_width":  r"0.85\textwidth",
    "chart_width":    r"0.95\textwidth",
    "placement":      "H",
    "needspace_lines": 12,
    "placeholder_pad": "8pt",          # inner padding of "figure not available" boxes
}

# ─────────────────────────────────────────────────────────────────────────────
# 5b. TITLE PAGE
# ─────────────────────────────────────────────────────────────────────────────
TITLE_PAGE = {
    "top_space":       "1.0cm",
    "rule_width":      "1.2pt",
    "title_size":      (34, 40),        # font size / baseline skip (pt)
    "table_row_stretch": 1.45,
    "key_col":         0.33,            # fraction of \linewidth
    "value_col":       0.57,
}

# ─────────────────────────────────────────────────────────────────────────────
# 6. CHARTS (matplotlib)
# ─────────────────────────────────────────────────────────────────────────────
# Colours follow a role-based scheme: one neutral series colour for bars,
# the reserved critical red for failures and the UR = 1.0 limit line.
CHART = {
    "dpi":            220,
    "figsize":        (7.0, 3.4),        # inches (≈ text width)
    "figsize_tall":   (7.0, 4.6),
    "font_family":    "DejaVu Sans",
    "font_size":      8.5,
    "title_size":     9.5,
    "series":         "#2A78D6",         # primary bar colour (passing / quantity)
    "series_alt":     "#1BAF7A",         # second quantity panel
    "series_muted":   "#9EC5F4",
    "fail":           "#D03B3B",         # bars with UR > 1.0
    "warn":           "#EDA100",         # 0.9 < UR <= 1.0
    "limit_line":     "#D03B3B",         # UR = 1.0 threshold (red dashed)
    "limit_style":    (0, (5, 3)),
    "limit_width":    1.4,
    "ink":            "#0B0B0B",
    "ink_secondary":  "#52514E",
    "grid":           "#E1E0D9",
    "axis":           "#C3C2B7",
    "bar_width":      0.6,
    "warn_threshold": 0.90,
}

# ─────────────────────────────────────────────────────────────────────────────
# 7. HEADER / FOOTER
# ─────────────────────────────────────────────────────────────────────────────
HEADER_FOOTER = {
    "font":        r"\footnotesize\sffamily",
    "rule_color":  "osdagGreen",
    "rule_width":  "0.8pt",
    "footer_left": r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay",
    "footer_right": r"Page \thepage\ of \pageref{LastPage}",
    "sd_note":     r"* Software default value",
}


# =============================================================================
# Helper API used by chapter modules
# =============================================================================

def color(name):
    """Return a LaTeX colour name defined in COLORS (validates the key)."""
    if name not in COLORS:
        raise KeyError(f"Unknown report colour '{name}'")
    return name


def status(value):
    """Uniform PASS / WARN / FAIL badge.

    Accepts a bool (True = PASS), a status string (any case, may contain
    extra words such as "FAIL (Ratio)"), or an already-empty value.
    Empty / unknown values return the empty-cell marker.
    """
    if value is None or value == "":
        return TABLE["empty_cell"]
    if isinstance(value, bool):
        value = "PASS" if value else "FAIL"
    s = str(value).strip()
    up = s.upper()
    if up in ("---", "--", "N/A", "NA"):
        return s
    if "FAIL" in up:
        col = "statusFail"
    elif "WARN" in up:
        col = "statusWarn"
    elif "PASS" in up or up == "OK":
        col = "statusPass"
    else:
        return s
    return r"\textcolor{" + col + r"}{\textbf{" + s + "}}"


def ur_value(ur, nd=2):
    """Format a utilization ratio; values above 1.0 are highlighted."""
    try:
        f = float(ur)
    except (TypeError, ValueError):
        return ""
    s = f"{f:.{nd}f}"
    return (r"\textcolor{statusFail}{\textbf{" + s + "}}") if f > 1.0 else s


def note(text):
    """Stand-alone note paragraph (for notes that are not attached to a table)."""
    return (r"\par\noindent{" + TYPOGRAPHY["note_font"] + r"\textit{" + text + r"}}\par")


# =============================================================================
# LaTeX preamble (document class, packages, layout, colours, headings, tables)
# =============================================================================

def _color_definitions():
    return "\n".join(r"\definecolor{" + k + "}{HTML}{" + v + "}" for k, v in COLORS.items())


def _running_header_footer(header_left, header_right):
    hf = HEADER_FOOTER
    rule = (r"{\color{" + hf["rule_color"] + r"}\rule{\headwidth}{" + hf["rule_width"] + "}}")
    # Footer box: [software-default note] / green rule / footer text.
    # It is top-aligned at \footskip below the text block and grows downward
    # into the bottom margin, so it can never overlap body content.
    footer = (
        r"\parbox[t]{\headwidth}{" + hf["font"]
        + r"\ifbool{hasSDonPage}{\textit{" + hf["sd_note"] + r"}}{\strut}\\[1pt]"
        + rule + r"\\[1pt]"
        + hf["footer_left"] + r"\hfill " + hf["footer_right"] + "}"
    )
    header = (
        r"\fancyhead[L]{" + hf["font"] + " " + header_left + "}\n"
        r"  \fancyhead[R]{" + hf["font"] + " " + header_right + "}\n"
        r"  \renewcommand{\headrule}{{\color{" + hf["rule_color"] + r"}\hrule width\headwidth height "
        + hf["rule_width"] + "}}\n"
    )
    return header, footer


def build_preamble(header_left, header_right):
    """Return the complete LaTeX preamble up to and including \\begin{document}.

    ``header_left`` / ``header_right`` must already be LaTeX-escaped.
    """
    p, t, ty = PAGE, TABLE, TYPOGRAPHY
    header, footer = _running_header_footer(header_left, header_right)

    return r"""
\documentclass[""" + p["font_size"] + "," + p["paper"] + r"""]{report}

% ── Packages ────────────────────────────────────────────────────────────────
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[""" + p["paper"] + r""",
  top=""" + p["top"] + r""", bottom=""" + p["bottom"] + r""",
  left=""" + p["left"] + r""", right=""" + p["right"] + r""",
  headheight=""" + p["headheight"] + r""", headsep=""" + p["headsep"] + r""",
  footskip=""" + p["footskip"] + r"""]{geometry}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{textcomp}
\usepackage{booktabs}
\usepackage{array}
\usepackage{tabularx}
\usepackage{float}
\usepackage{fancyhdr}
\usepackage[table]{xcolor}
\usepackage{setspace}
\usepackage{enumitem}
\usepackage{caption}
\usepackage{subcaption}
\usepackage{multirow}
\usepackage{longtable}
\usepackage{titlesec}
\usepackage{titletoc}
\usepackage{lastpage}
\usepackage{makecell}
\usepackage{etoolbox}
\usepackage{needspace}
\usepackage[hidelinks]{hyperref}

% ── Colours (styles.COLORS) ─────────────────────────────────────────────────
""" + _color_definitions() + r"""

% ── Captions (styles.TYPOGRAPHY) ────────────────────────────────────────────
\captionsetup{
    font=""" + ty["caption_font"] + r""",
    labelfont={""" + ty["caption_label"] + r""",color=osdagGreenDark},
    textfont=""" + ty["caption_text"] + r""",
    justification=raggedright,
    singlelinecheck=false,
    format=plain,
    skip=""" + ty["caption_skip"] + r"""
}
\numberwithin{table}{chapter}
\numberwithin{figure}{chapter}

% ── Tables (styles.TABLE) ───────────────────────────────────────────────────
\setlength{\tabcolsep}{""" + t["col_sep"] + r"""}
\renewcommand{\arraystretch}{""" + f"{t['row_stretch']:.2f}" + r"""}
\setlength{\extrarowheight}{""" + t["extra_row_height"] + r"""}
\setlength{\arrayrulewidth}{""" + t["rule_width"] + r"""}
\arrayrulecolor{tblRule}
\setlength{\LTpre}{""" + t["space_before"] + r"""}
\setlength{\LTpost}{""" + t["space_after"] + r"""}
\setlength{\LTleft}{\fill}
\setlength{\LTright}{\fill}
\setlength{\LTcapwidth}{\linewidth}
% Page-bottom threshold: never start a table in the last few lines.  Long
% tables get a per-table \needspace from report_tables (header + first rows);
% short tables are unbreakable minipages.
\BeforeBeginEnvironment{table}{\needspace{""" + str(t["needspace_lines"]) + r"""\baselineskip}}
\captionsetup[table]{position=top}
% \nbcline: a \cline that is not a page-break opportunity.  colortbl's \cline
% ends with \noalign{\vskip-\arrayrulewidth}; that skip follows a box and is
% therefore a legal breakpoint.  Used between rows of a merged-label group so
% the group (and its \multirow label) never splits across pages.
\makeatletter
\def\nbcline#1{\@nbcline#1\@nil}
\def\@nbcline#1-#2\@nil{%
  \omit
  \@multicnt#1%
  \advance\@multispan\m@ne
  \ifnum\@multicnt=\@ne\@firstofone{&\omit}\fi
  \@multicnt#2%
  \advance\@multicnt-#1%
  \advance\@multispan\@ne
  {\CT@arc@\leaders\hrule\@height\arrayrulewidth\hfill}%
  \cr
  \noalign{\nobreak\vskip-\arrayrulewidth\nobreak}}
\makeatother
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}

% ── Headings (styles.TYPOGRAPHY) ────────────────────────────────────────────
\titleformat{\chapter}[display]
  {\normalfont}
  {""" + ty["chapter_label"] + r"""CHAPTER \thechapter}
  {2pt}
  {""" + ty["chapter_title"] + r"""}
  [\vspace{2pt}{\color{osdagGreen}\titlerule[""" + ty["chapter_rule"] + r"""]}]
\titleformat{name=\chapter,numberless}[display]
  {\normalfont}{}{0pt}
  {""" + ty["chapter_title"] + r"""}
  [\vspace{2pt}{\color{osdagGreen}\titlerule[""" + ty["chapter_rule"] + r"""]}]
\titlespacing*{\chapter}{0pt}{""" + ty["chapter_space_before"] + r"""}{""" + ty["chapter_space_after"] + r"""}
\titleformat{\section}{\normalfont""" + ty["section"] + r"""}{\thesection}{0.8em}{}
\titlespacing*{\section}{0pt}{""" + ty["section_space_before"] + r"""}{""" + ty["section_space_after"] + r"""}
\titleformat{\subsection}{\normalfont""" + ty["subsection"] + r"""}{\thesubsection}{0.8em}{}

% ── Table of contents ───────────────────────────────────────────────────────
\setcounter{tocdepth}{1}
\titlecontents{chapter}[1.8em]
  {\addvspace{5pt}\normalfont\bfseries}
  {\contentslabel{1.8em}}
  {\hspace*{-1.8em}}
  {\hfill\contentspage}
\titlecontents{section}[4.2em]
  {\normalfont}
  {\contentslabel{2.4em}}
  {\hspace*{-2.4em}}
  {\titlerule*[0.6pc]{.}\contentspage}
\renewcommand{\contentsname}{Table of Contents}

% ── Software-default marker (drives the footer note) ────────────────────────
\newbool{hasSDonPage}
\boolfalse{hasSDonPage}
\newcommand{\markSD}{\global\booltrue{hasSDonPage}}
\newcommand{\sdstar}{\textsuperscript{*}\markSD{}}
\AddToHook{shipout/after}{\global\boolfalse{hasSDonPage}}

% ── Running header / footer (styles.HEADER_FOOTER) ──────────────────────────
\fancypagestyle{main}{%
  \fancyhf{}
  """ + header + r"""  \fancyfoot[C]{""" + footer + r"""}
  \renewcommand{\footrulewidth}{0pt}
}
\fancypagestyle{plain}{%
  \fancyhf{}
  """ + header + r"""  \fancyfoot[C]{""" + footer + r"""}
  \renewcommand{\footrulewidth}{0pt}
}
\fancypagestyle{firstpage}{%
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
  \renewcommand{\headrule}{}
  \fancyfoot[C]{""" + footer + r"""}
  \renewcommand{\footrulewidth}{0pt}
}
\pagestyle{main}

% ── Body text ───────────────────────────────────────────────────────────────
\setstretch{""" + f"{p['line_stretch']:.2f}" + r"""}
\setlength{\parskip}{""" + p["par_skip"] + r"""}
\setlist{itemsep=1pt,topsep=3pt}
\raggedbottom

% ── Misc commands kept for backwards compatibility ──────────────────────────
\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}
\newcommand{\todo}[1]{\colorbox{yellow}{TODO: #1}}

\begin{document}
"""


def header_texts(project_name, job_number, report_date, report_version):
    """Escaped running-header strings (left, right)."""
    left = _tex(project_name) + r" $|$ " + _tex(job_number)
    right = _tex(report_date) + r" $|$ " + _tex(report_version)
    return left, right
