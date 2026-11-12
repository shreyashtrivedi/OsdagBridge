from osdagbridge.core.utils.common import (
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_DEPTH,
    KEY_TS_NO_OF_GIRDERS
)


def _tex(value):
    """Escape a Python value for safe LaTeX embedding."""
    s = str(value) if value is not None else ''
    if not s:
        return r''
    # Normalise non-ASCII glyphs from section designations (e.g. "∠ 100 ⅹ 100ⅹ 10")
    # that pdflatex cannot render.
    for uni, ascii_ in [('∠', 'L'), ('ⅹ', 'x'), ('×', 'x')]:
        s = s.replace(uni, ascii_)
    s = s.replace('\\', r'\textbackslash{}')
    for ch, esc in [('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'),
                    ('{', r'\{'), ('}', r'\}'),          
                    ('_', r'\_\allowbreak{}'),            
                    ('~', r'\textasciitilde{}'), ('^', r'\^{}')]:
        s = s.replace(ch, esc)
    s = s.replace(':', r':\allowbreak{}')
    # Unicode math symbols that pdflatex cannot typeset directly (mapped after
    # escaping so the inserted commands are not escaped themselves).
    for uni, cmd in [('≤', r'\ensuremath{\leq}'), ('≥', r'\ensuremath{\geq}'),
                     ('≠', r'\ensuremath{\neq}'), ('±', r'\ensuremath{\pm}'),
                     ('√', r'\ensuremath{\surd}'), ('·', r'\ensuremath{\cdot}'),
                     ('φ', r'\ensuremath{\phi}'), ('ϕ', r'\ensuremath{\phi}'),
                     ('γ', r'\ensuremath{\gamma}'), ('λ', r'\ensuremath{\lambda}'),
                     ('τ', r'\ensuremath{\tau}'), ('σ', r'\ensuremath{\sigma}'),
                     ('Δ', r'\ensuremath{\Delta}'), ('δ', r'\ensuremath{\delta}'),
                     ('χ', r'\ensuremath{\chi}'), ('μ', r'\ensuremath{\mu}'),
                     ('–', '--'), ('—', '---')]:
        s = s.replace(uni, cmd)
    return s


def _fmt_number(val):
    """Trim floating-point noise (12.149999999999999 -> 12.15) without
    changing intentional precision: up to 4 significant decimals are kept."""
    if isinstance(val, bool) or not isinstance(val, float):
        return val
    if val != val:            # NaN
        return ""
    s = f"{val:.4f}".rstrip("0")
    return s + "0" if s.endswith(".") else s


def _render_value(source_dict, key, unit=""):
    val = source_dict.get(key)
    if val in ("", None):
        return ""
    return _tex(_fmt_number(val)) + unit


def get_girder_entries(input_dict):
    """
    Retrieve all girder labels and member IDs from backend keys.

    Usage Example:
    --------------------------
    girder_entries = get_girder_entries(bridge.input_dict)
    
    # 1. Fallback handling (if backend hasn't populated keys yet)
    if not girder_entries:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]
        
    # 2. Get total number of girders safely
    n_girders = len(girder_entries)
    
    # 3. Iterate over the girders to build table rows
    for lbl, mid in girder_entries:
        # lbl will be e.g., "G1", mid will be e.g., "G1M1"
        # Access girder specific keys dynamically:
        # val = input_dict.get(f"{KEY_MP_GIRDER_DEPTH}.{lbl}.{mid}")
        pass

    Returns:
        List[Tuple[str, str]]
    """
    n = int(input_dict.get(KEY_TS_NO_OF_GIRDERS, 0))

    entries = []

    for i in range(1, n + 1):
        entries.append(
            (
                input_dict.get(f"{KEY_MP_GD_SELECT_GIRDER}.G{i}", ""),
                input_dict.get(f"{KEY_MP_GD_MEMBER_ID}.G{i}.M1", ""),
            )
        )

    return entries


def placeholder_box(caption, width=r'\linewidth'):
    """Light framed box shown where a figure is not available.

    Always a self-contained, full-width block (never sits side by side with
    another box), so it cannot run into the margin."""
    from osdagbridge.core.reports.styles import FIGURE
    return (r'\par\noindent{\setlength{\fboxsep}{' + FIGURE["placeholder_pad"]
            + r'}\fcolorbox{tblRule}{white}{\parbox{\dimexpr '
            + width + r'-2\fboxsep-2\fboxrule\relax}{\centering\footnotesize\color{textMuted}'
            r'\textit{[ Figure not available: ' + caption + r' ]}}}}\par')


def _fig_or_placeholder(path, caption, width=None):
    """Embed figure if path is provided (file already copied to assets), else show placeholder box.
    path is the relative path as pdflatex will see it (e.g. 'assets/plan.png').
    """
    from osdagbridge.core.reports.styles import FIGURE
    width = width or FIGURE["default_width"]
    if path:
        p = path.replace('\\', '/')
        return (r'\begin{figure}[H]' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[width=' + width + ',height=0.42\\textheight,keepaspectratio]{' + p + '}\n'
                r'\caption*{' + caption + '}\n'
                r'\end{figure}')
    return (r'\begin{figure}[H]' + '\n'
            r'\centering' + '\n'
            + placeholder_box(caption) + '\n'
            r'\caption*{' + caption + '}\n'
            r'\end{figure}')

def _fig_embed(path, caption, width=r'\textwidth', height=None):
    """Embed a real figure when path is provided (already copied); otherwise use a placeholder box."""
    if path:
        p = path.replace('\\', '/')
        opts = 'width=' + width
        if height:
            opts += ',height=' + height + ',keepaspectratio'
        return (r'\begin{figure}[H]' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[' + opts + ']{' + p + '}\n'
                r'\caption*{\small ' + caption + '}\n'
                r'\end{figure}')
    return (r'\begin{figure}[H]' + '\n'
            + placeholder_box(caption) + '\n'
            r'\end{figure}')


