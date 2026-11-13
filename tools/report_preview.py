"""Headless design-report preview for OsdagBridge (no GUI required).

Runs one plate-girder design with the default inputs, snapshots the design
results, and renders the PDF design report from that snapshot.  Because the
snapshot is reused, two source trees (e.g. the original ``dev`` branch and the
refactored branch) can be compared on *identical* design data.

CAD views and analysis plots are captured from live GUI widgets, so they are
shown as "figure not available" boxes here; use the desktop app for the
final, fully illustrated report.

Usage (inside the ``osdagbridge-env`` conda environment)::

    # 1. run the design once and save the results
    python tools/report_preview.py design  --snapshot snap.pkl
    # 2. render a report from the snapshot with a given source tree
    python tools/report_preview.py report  --snapshot snap.pkl --out out --stem Report_After
    python tools/report_preview.py report  --snapshot snap.pkl --out out --stem Report_Before \
           --src ../OsdagBridge-baseline/src

Options for ``design``: --span (m), --carriageway (m), --footpath
("None" | "Single Side" | "Both Sides").
"""
import argparse
import os
import pickle
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SRC = os.path.normpath(os.path.join(HERE, "..", "src"))

LOCATION = {
    "method": "location_name",
    "data": {"district": "Mumbai", "state": "Maharashtra"},
    "weather_data": {"wind_speed": 44, "zone": "III", "max_temp": 40.0,
                     "min_temp": 10.0, "latitude": 19.07, "longitude": 72.87},
}


def _use_src(src):
    sys.path.insert(0, os.path.abspath(src))
    for name in [m for m in sys.modules if m.startswith("osdagbridge")]:
        del sys.modules[name]


def _ensure_osdag_database():
    """Osdag's section database (angles, beams, ...) is normally built from its
    SQL dump the first time the Osdag GUI starts.  Build it if it is missing or
    empty, otherwise cross-bracing design returns no results."""
    try:
        from osdag_gui.__main__ import create_sqlite
        create_sqlite()
    except Exception as exc:     # pragma: no cover - best effort
        print("[warn] could not initialise the Osdag database:", exc)


def run_design(args):
    _use_src(args.src)
    _ensure_osdag_database()
    from osdagbridge.core.bridge_types.plate_girder import defaults as d
    from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
    from osdagbridge.core.utils import common as c
    from osdagbridge.desktop.ui.dialogs import material_properties as mp

    inp = dict(d.BASIC_INPUT_DICT)
    inp.update({
        c.KEY_PROJECT_LOCATION: LOCATION,
        c.KEY_SPAN: args.span,
        c.KEY_CARRIAGEWAY_WIDTH: args.carriageway,
        c.KEY_SKEW_ANGLE: 0.0,
        c.KEY_FOOTPATH: args.footpath,
    })
    d.solve_extend_basic_input_dict(inp)

    # Mirror the Material Properties dialog defaults (girder steel + deck concrete).
    steel = mp.STEEL_MATERIAL_BASE_VALUES.get(mp._normalize_steel_material_name(inp[c.KEY_GIRDER])) or {}
    conc = mp.CONCRETE_GRADE_BASE_VALUES.get(
        str(inp[c.KEY_DECK_CONCRETE_GRADE_BASIC]).replace(" ", "").upper()) or {}
    for key, val in ((c.KEY_MATERIAL_GIRDER_E, steel.get("E")), (c.KEY_MATERIAL_GIRDER_G, steel.get("G")),
                     (c.KEY_MATERIAL_GIRDER_POISSON, steel.get("Poisson")),
                     (c.KEY_MATERIAL_GIRDER_FY, steel.get("Fy")), (c.KEY_MATERIAL_GIRDER_FU, steel.get("Fu")),
                     (c.KEY_MATERIAL_GIRDER_DENSITY, mp.STEEL_WEIGHT_DENSITY),
                     (c.KEY_MATERIAL_GIRDER_THERMAL, mp.STEEL_THERMAL_COEFF),
                     (c.KEY_MATERIAL_DECK_FCK, conc.get("fck")), (c.KEY_MATERIAL_DECK_FCTM, conc.get("fctm")),
                     (c.KEY_MATERIAL_DECK_ECM, conc.get("Ecm")),
                     (c.KEY_MATERIAL_DECK_DENSITY, mp.CONCRETE_WEIGHT_DENSITY),
                     (c.KEY_MATERIAL_DECK_THERMAL, mp.STEEL_THERMAL_COEFF)):
        if inp.get(key) in (None, "") and val is not None:
            inp[key] = val

    pgb = PlateGirderBridge()
    pgb.set_input(inp)
    pgb.design()
    data = {"input_dict": dict(pgb.input_dict), "output_dict": dict(pgb.output_dict),
            "lc": getattr(pgb, "_lc_summary", None), "rxn": getattr(pgb, "_reaction_summary", None)}
    with open(args.snapshot, "wb") as fh:
        pickle.dump(data, fh)
    print(f"snapshot written: {args.snapshot} ({len(data['output_dict'])} output keys)")


def run_report(args):
    _use_src(args.src)
    from osdagbridge.core.reports.report_generator import (
        ReportMetadata, ReportOptions, ReportRequest, build_report_payload, generate_report)

    with open(args.snapshot, "rb") as fh:
        data = pickle.load(fh)
    out = dict(data["output_dict"])
    if data["lc"] is not None or data["rxn"] is not None:
        out["analysis_summary"] = {"load_cases": data["lc"] or {}, "reactions": data["rxn"] or {}}
    md = ReportMetadata(project_name="Sample Highway Bridge", project_location=LOCATION,
                        designer="Design Engineer", client="Client Organisation",
                        company="FOSSEE, IIT Bombay", job_number="OB-2026-001",
                        subtitle="Rev 0", reviewer="Reviewer")
    opts = ReportOptions(sections=["loads", "analysis", "design_checks", "drawings"],
                         include_figures=True, include_toc=True, include_pdf=True)
    req = ReportRequest(metadata=md, options=opts, output_dir=args.out, file_stem=args.stem)
    result = generate_report(build_report_payload(req, dict(data["input_dict"]), out), req)
    print("PDF:", result.pdf_path, "| TeX:", result.tex_path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("design", help="run the design and save a snapshot")
    d.add_argument("--snapshot", default="snap.pkl")
    d.add_argument("--src", default=DEFAULT_SRC)
    d.add_argument("--span", type=float, default=30.0)
    d.add_argument("--carriageway", type=float, default=7.5)
    d.add_argument("--footpath", default="Both Sides")
    r = sub.add_parser("report", help="render a PDF report from a snapshot")
    r.add_argument("--snapshot", default="snap.pkl")
    r.add_argument("--src", default=DEFAULT_SRC)
    r.add_argument("--out", default="out")
    r.add_argument("--stem", default="Report_After")
    args = ap.parse_args()
    run_design(args) if args.cmd == "design" else run_report(args)


if __name__ == "__main__":
    main()
