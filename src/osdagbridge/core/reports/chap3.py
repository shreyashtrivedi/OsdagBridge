# =============================================================================
# Chapter 3: Loads and Load Combinations
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_BL_IRC_CLASS_SV,
    KEY_CB_LOAD,
    KEY_FOOTPATH,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_NO_OF_FOOTPATHS,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_ECCENTRICITY,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_RL_LOAD_VALUE,
    KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_TIME_PERIOD,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_ZONE_FACTOR,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE
)

from osdagbridge.core.reports.report_utils import _tex, _render_value

from osdagbridge.core.reports.report_tables import Col, ReportTable, kv_table
from osdagbridge.core.reports.styles import note

# kN per tonne (consistent with the IRC 6 module, which works in N = t * 9810)
_KN_PER_T = 9.81


def _selected(v):
    """UI check-box value -> bool (accepts bools and 'Yes'/'True'/'1' strings)."""
    if isinstance(v, str):
        return v.strip().lower() in ("yes", "true", "1", "checked", "on")
    return bool(v)


def _fmt(v, nd=2, unit=""):
    try:
        return f"{float(v):.{nd}f}" + unit
    except (TypeError, ValueError):
        return ""


def _vehicle_rows(input_dict, IRC6_2017):
    """One record per vehicle selected in the Loading tab (Additional Inputs).

    Gross loads come from the IRC 6 vehicle definitions in irc6_2017.py where
    they exist (Class A, 70R, SV, fatigue); Class AA / 70R bogie use the
    nominal IRC 6 Cl. 204 values.  Impact factors use the same IRC 6
    functions as the analysis (Cl. 208.2 for Class A, Cl. 208.3 for AA/70R).
    """
    def _sum_kn(fn):
        try:
            return sum(fn()['wheel_loads']) / 1000.0
        except Exception:
            return None

    def _70r_tracked():
        try:
            d = IRC6_2017.cl_204_1_Class70R_vehicle_track()
            length = d['x'][-1] - d['x'][0]
            return 2.0 * d['wheel_loads_udl'] * length / 1000.0   # two tracks
        except Exception:
            return 70.0 * _KN_PER_T

    def _sv():
        try:
            return float(IRC6_2017.cl_204_5_1_special_vehicle()['total_load_kN'])
        except Exception:
            return 385.0 * _KN_PER_T

    # (selection key, name, type, gross-load fn, impact group, braking rule)
    # Braking (IRC 6 Cl. 211.2) is derived from the vehicle *trains* on the
    # carriageway; Class SV braking is the separate opt-in check box in the
    # Loading tab; the 70R bogie (local deck loading) and the fatigue vehicle
    # are not braking trains.
    catalogue = [
        (KEY_LL_IRC_CLASS_A,       "Class A",             "Wheeled", lambda: _sum_kn(IRC6_2017.cl_204_1_ClassA_vehicle), "A", "yes"),
        (KEY_LL_IRC_70R_WHEELED,   "Class 70R (Wheeled)", "Wheeled", lambda: _sum_kn(IRC6_2017.cl_204_1_Class70R_vehicle_wheel), "AA", "yes"),
        (KEY_LL_IRC_70R_TRACKED,   "Class 70R (Tracked)", "Tracked", _70r_tracked, "AA", "yes"),
        (KEY_LL_IRC_70R_BOGIE,     "Class 70R (Bogie)",   "Wheeled", lambda: 40.0 * _KN_PER_T, "AA", "no"),
        (KEY_LL_IRC_AA_WHEELED,    "Class AA (Wheeled)",  "Wheeled", lambda: 40.0 * _KN_PER_T, "AA", "yes"),
        (KEY_LL_IRC_AA_TRACKED,    "Class AA (Tracked)",  "Tracked", lambda: 70.0 * _KN_PER_T, "AA", "yes"),
        (KEY_LL_IRC_CLASS_SV,      "Class SV",            "Wheeled", _sv, None, "sv"),
        (KEY_LL_IRC_CLASS_FATIGUE, "Fatigue Vehicle",     "Wheeled", lambda: _sum_kn(IRC6_2017.cl_204_6_fatigue_load), None, "no"),
    ]

    span = input_dict.get(KEY_SPAN)
    try:
        span_m = float(span)
    except (TypeError, ValueError):
        span_m = None

    def _impact(group):
        if span_m is None or group is None:
            return None
        try:
            im = (IRC6_2017.cl_208_2_impact_factor(span_m) if group == "A"
                  else IRC6_2017.cl_208_3_impact_factor(span_m))
            return 1.0 + im
        except Exception:
            return None

    sv_braking = _selected(input_dict.get(KEY_BL_IRC_CLASS_SV, True))
    rows = []
    for key, name, kind, load_fn, group, brake in catalogue:
        if not _selected(input_dict.get(key)):
            continue
        rows.append({"name": name, "type": kind, "gross_kN": load_fn(),
                     "impact": _impact(group),
                     "braking": brake == "yes" or (brake == "sv" and sv_braking)})

    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            name = c.get('name') if isinstance(c, dict) else (c if isinstance(c, str) else None)
            if name:
                rows.append({"name": f"{name} (custom)", "type": "User-defined",
                             "gross_kN": None, "impact": None, "braking": None})
    return rows


def _vehicle_live_load_table(input_dict, IRC6_2017, braking_force_str):
    """Table: Vehicle live loads — one row per vehicle selected in the Loading
    tab, laid out as in the task's reference table:

        Vehicle | Total Load (kN) | Impact Factor | Braking Load
                                                  | Considered? | Value (kN) | Eccentricity (m)
    """
    vehicles = _vehicle_rows(input_dict, IRC6_2017)
    try:
        ecc = float(input_dict.get(KEY_LL_ECCENTRICITY))
        ecc_src = "user input"
    except (TypeError, ValueError):
        ecc = IRC6_2017.cl_211_3_braking_force_location().get("height_m", 1.2)
        ecc_src = "IRC 6 Cl. 211.3 default"

    hdr = [
        r" & & & \multicolumn{3}{c|}{\textbf{Braking Load}}\\ \cline{4-6}",
        r"\multirow{-2}{=}{\textbf{Vehicle}} & \multirow{-2}{=}{\centering\textbf{Total Load (kN)}} & "
        r"\multirow{-2}{=}{\centering\textbf{Impact Factor}} & \textbf{Considered?} & \textbf{Value (kN)} & "
        r"\textbf{Eccentricity (m)}\\",
    ]
    t = ReportTable("Vehicle Live Loads (Carriageway) --- per IRC 6", [
        Col("", 2.0, "l"), Col("", 1.1, "c"), Col("", 1.1, "c"),
        Col("", 1.1, "c"), Col("", 1.0, "c"), Col("", 1.2, "c"),
    ], header_tex=hdr, note=(
        r"Impact factor shown as $(1 + I_M)$: IRC 6 Cl. 208.2 (Class A) and Cl. 208.3 (Class AA / 70R). "
        r"Braking value per vehicle = 20\% of its total load (IRC 6 Cl. 211.2); design braking force for the "
        r"carriageway = " + _tex(braking_force_str) + r". Eccentricity = height of the braking force above the "
        r"deck (" + ecc_src + r", Cl. 211.3). Class SV braking follows the opt-in check box in the Loading tab; "
        r"the 70R bogie (local deck loading) and the fatigue vehicle are not braking trains. "
        r"Centrifugal force (IRC 6 Cl. 212) applies only to horizontally curved decks --- not applicable "
        r"to this straight span."))
    if not vehicles:
        t.row(r"\textit{No vehicle selected}", "", "", "", "", "")
    for v in vehicles:
        g = v["gross_kN"]
        brake = v["braking"]
        considered = "---" if brake is None else ("Yes" if brake else "No")
        t.row(_tex(v["name"]), _fmt(g, 1), _fmt(v["impact"], 3), considered,
              _fmt(0.2 * g, 1) if (brake and g) else "---",
              _fmt(ecc, 2) if brake else "---")
    return t.dumps()


def _footway_live_load_table(input_dict, IRC6_2017):
    """Table: Footway (pedestrian) live load — kept separate from vehicle loads."""
    footpath = str(input_dict.get(KEY_FOOTPATH, "None") or "None").strip()
    if footpath.lower() in ("none", ""):
        return note(r"Footway live load: not applicable --- no footpath is provided on this bridge.")

    fp_mode = str(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "") or "").strip()
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    auto = fp_mode.lower() in ("as per irc 6", "as per irc6", "automatic", "")
    intensity = None
    if auto or fp_value in (None, ""):
        try:
            intensity = float(IRC6_2017.cl_206_1_footway_load())
        except Exception:
            intensity = None
        basis = "IRC 6 Cl. 206.1 (software default)"
    else:
        try:
            intensity = float(fp_value)
        except (TypeError, ValueError):
            intensity = None
        basis = "User-defined"

    try:
        width = float(input_dict.get(KEY_TS_FOOTPATH_WIDTH))
    except (TypeError, ValueError):
        width = None
    try:
        n_fp = int(input_dict.get(KEY_TS_NO_OF_FOOTPATHS) or (2 if "both" in footpath.lower() else 1))
    except (TypeError, ValueError):
        n_fp = 2 if "both" in footpath.lower() else 1

    line_load = intensity * width if (intensity is not None and width is not None) else None
    sd = r"\sdstar{}" if auto else ""
    return kv_table("Footway Live Load (Pedestrian) --- per IRC 6", [
        ("Footpath Configuration", _tex(footpath)),
        ("Number of Footpaths", str(n_fp)),
        ("Footpath Width", _fmt(width, 2, " m")),
        ("Pressure Basis", _tex(fp_mode or "As per IRC 6") + " --- " + basis),
        ("Design Intensity", (_fmt(intensity, 3, r" kN/m\textsuperscript{2}") + sd) if intensity is not None else ""),
        ("Line Load per Footpath", _fmt(line_load, 2, " kN/m") if line_load is not None else ""),
        ("Total Footway Load on Span",
         _fmt(line_load * n_fp * float(input_dict.get(KEY_SPAN) or 0), 1, " kN") if line_load is not None else ""),
    ], note="Footway load is applied as a uniform patch load over each footpath (analysis load case "
            r"``Footpath load''). It is not combined with the vehicle impact factor.")


def ch3_loads(input_dict):
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    lanes_src = ""
    if lanes in (None, ""):
        # Fallback: number of design lanes from carriageway width (IRC 6 Table 6)
        try:
            w = float(input_dict.get(KEY_CARRIAGEWAY_WIDTH))
            lanes = next(n for n, lim in ((1, 5.3), (2, 9.6), (3, 13.1), (4, 16.6), (5, 20.1), (6, 23.6))
                         if w < lim) if w < 23.6 else 6
            lanes_src = ", per IRC 6 Table 6 from carriageway width"
        except (TypeError, ValueError, StopIteration):
            lanes = None
    braking_force_str = "N/A"
    if lanes not in (None, ""):
        try:
            lanes_int = int(lanes)
            braking_force_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
            braking_force_kN = braking_force_t * 9.81
            braking_force_str = (f"{braking_force_kN:.2f} kN ({braking_force_t:.2f} t; "
                                 f"{lanes_int} design lane(s){lanes_src})")
        except Exception:
            braking_force_str = "N/A"

    # Vz / Pz — prefer stored computed values; fall back to IRC6 Table 12
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not vz_val or not pz_val:
        try:
            _vb  = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or input_dict.get('wind_speed')
            _h   = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)
            _ter = {
                "Plain Terrain": "plain",
                "Terrain with Obstructions": "obstructed",
            }.get(str(input_dict.get(KEY_WL_TERRAIN_TYPE, "")).strip(), "plain")
            _res = IRC6_2017.table_12(float(_h), _ter, float(_vb))
            if not vz_val:
                vz_val = _res.get("Vz")
            if not pz_val:
                pz_val = _res.get("Pz")
        except Exception:
            pass
    vz_str = _fmt(vz_val, 2, " m/s")
    pz_str = _fmt(pz_val, 2, r" N/m\textsuperscript{2}")

    # Table — Seismic: prefer stored computed values; fall back to IRC6 cl_218_5_1
    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral    = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah          = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av          = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z    = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st   = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp   = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res  = IRC6_2017.cl_218_5_1(zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                        live_load_kN=_live, period_T=float(_tp) if _tp else None,
                        damping_percent=float(_damp))
            if not sl_zone_factor:
                sl_zone_factor = _res.get("Z")
            if not sl_spectral:
                sl_spectral    = _res.get("Sa_g_adjusted")
            if not sl_ah:
                sl_ah          = _res.get("Ah")
            if not sl_av:
                sl_av          = round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    def _sl(v):
        try:
            return f"{float(v):.4f}".rstrip("0").rstrip(".")
        except (TypeError, ValueError):
            return ""

    # Temperature: effective bridge temperature range from shade temperatures
    tl_temp_min = tl_temp_max = tl_rise = tl_fall = ""
    try:
        _tmax = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get('shade_temp_max')
        _tmin = input_dict.get(KEY_TL_LOWEST_MIN_TEMP)  or input_dict.get('shade_temp_min')
        if _tmax and _tmin:
            _res    = IRC6_2017.cl_215_2_effective_bridge_temperature(
                          float(_tmax), float(_tmin), 'metallic', False)
            _bt_min = _res.get('T_min', 0)
            _bt_max = _res.get('T_max', 0)
            _mean   = (_bt_max + _bt_min) / 2.0
            tl_temp_min = f"{_bt_min:.2f}"
            tl_temp_max = f"{_bt_max:.2f}"
            tl_rise     = f"{_bt_max - _mean:.2f}"
            tl_fall     = f"{_mean - _bt_min:.2f}"
    except Exception:
        pass
    tl_temp_min = _render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN) or tl_temp_min
    tl_temp_max = _render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX) or tl_temp_max
    tl_rise = _render_value(input_dict, KEY_TL_TEMP_RISE) or tl_rise
    tl_fall = _render_value(input_dict, KEY_TL_TEMP_FALL) or tl_fall

    # --- Load Combinations (dynamically generated from IRC 6) ---
    _LOAD_LABEL_MAP = {
        'dead_load':         'DL',
        'surfacing':         'SIDL',
        'live_load':         'LL',
        'wind_load':         'WL',
        'thermal_load':      'TL',
        'vehicle_collision': 'VC',
        'barge_impact':      'BI',
        'floating_bodies':   'FB',
        'seismic':           'EQ',
    }

    def _fmt_factors(factors):
        """Format a factors dict into a compact load-case string for the table."""
        parts = []
        for load, val in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):  # permanent load with adding/relieving
                add = val.get('adding')
                rel = val.get('relieving')
                add_s = f"{add:.2f}" if add is not None else '--'
                rel_s = f"{rel:.2f}" if rel is not None else '--'
                parts.append(f"{label}({add_s}/{rel_s})")
            else:
                if val is None:
                    continue  # skip N/A factors
                parts.append(f"{label}({val:.2f})")
        return ' + '.join(parts)

    lc = ReportTable("Load Combinations", [Col("Combination ID", 0.9, "c"), Col("Load Cases (partial safety factors)", 4.1, "l")],
                     note="All IRC 6 load combinations are auto-generated by OsdagBridge. "
                          "Permanent loads show (adding / relieving) factors. User-defined custom "
                          "combinations, if any, are appended.")
    for i, combo in enumerate(IRC6_2017.uls_load_combinations(), start=1):
        lc.row(f"ULS-{i:02d}", _fmt_factors(combo['factors']))
    for i, combo in enumerate(IRC6_2017.sls_load_combinations(), start=1):
        lc.row(f"SLS-{i:02d}", _fmt_factors(combo['factors']))

    unit3 = r" kN/m\textsuperscript{3}"
    dead = kv_table("Dead Load --- Self Weight", [
        ("Steel Self-Weight Applied", _render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, unit3)),
        ("Concrete Deck Weight", _render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, unit3)),
        ("Self-Weight Factor", _render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)),
    ])
    surfacing = kv_table("Dead Load for Surfacing (DW)", [
        ("Wearing Course", _render_value(input_dict, KEY_WC_MATERIAL) + ", "
         + _render_value(input_dict, KEY_WC_THICKNESS, " mm") + " thick"),
        ("Additional SIDL (Crash Barrier)", _render_value(input_dict, KEY_CB_LOAD, " kN/m per barrier")),
        ("Railing Load", _render_value(input_dict, KEY_RL_LOAD_VALUE, r" kN/m\sdstar{}")),
    ])
    wind = kv_table("Wind Load (WL) --- per IRC 6", [
        (r"Basic Wind Speed, $V_b$", _render_value(input_dict, 'wind_speed', ' m/s') + " (from Project Location)"),
        ("Terrain Type", _render_value(input_dict, KEY_WL_TERRAIN_TYPE)),
        (r"Average Exposed Height, $H$", _render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m')),
        (r"Hourly Mean Wind Speed, $V_z$", vz_str),
        (r"Hourly Wind Pressure, $P_z$", pz_str),
        ("Transverse Wind Force", _render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, ' kN')),
        ("Longitudinal Wind Force", _render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN')),
        ("Vertical Wind Force", _render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, ' kN')),
    ], note=r"$V_z$ and $P_z$ from IRC 6 Table 12 for the exposed height and terrain when not supplied.")
    seismic = kv_table("Earthquake Load (EL) --- per IRC 6", [
        ("Seismic Zone", _render_value(input_dict, 'seismic_zone') + " (from Project Location)"),
        (r"Zone Factor, $Z$", _sl(sl_zone_factor)),
        (r"Importance Factor, $I$", _render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR)),
        ("Type of Soil", _render_value(input_dict, KEY_SL_SOIL_TYPE)),
        (r"Spectral Acceleration Coefficient, $S_a/g$", _sl(sl_spectral)),
        (r"Horizontal Seismic Coefficient, $A_h$", _sl(sl_ah)),
        (r"Vertical Seismic Coefficient, $A_v$", _sl(sl_av)),
    ], note=r"IRC 6 Cl. 219 / IRC SP 114. $A_v = \tfrac{2}{3} A_h$.")
    temperature = kv_table("Temperature Load (TL) --- per IRC 6", [
        ("Maximum Shade Temperature", _render_value(input_dict, 'shade_temp_max', r" $^\circ$C")),
        ("Minimum Shade Temperature", _render_value(input_dict, 'shade_temp_min', r" $^\circ$C")),
        ("Effective Bridge Temperature Range",
         (tl_temp_min + r" to " + tl_temp_max + r" $^\circ$C") if tl_temp_min and tl_temp_max else ""),
        ("Temperature Rise / Fall for Design",
         (r"+" + tl_rise + r" $^\circ$C / $-$" + tl_fall + r" $^\circ$C") if tl_rise and tl_fall else ""),
    ], note="IRC 6 Cl. 215.2, metallic (steel-composite) superstructure.")

    return (r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\section{Permanent Loads}
""" + dead + surfacing + r"""
\section{Live Loads}
Carriageway (vehicle) live loads and footway (pedestrian) live loads are reported separately.
Only the vehicles selected in the \textit{Loading} tab of Additional Inputs are listed.
""" + _vehicle_live_load_table(input_dict, IRC6_2017, braking_force_str)
            + _footway_live_load_table(input_dict, IRC6_2017) + r"""
\section{Environmental Loads}
""" + wind + seismic + temperature + r"""
\section{Load Combinations}
""" + lc.dumps())
