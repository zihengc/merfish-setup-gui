#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MERFISH microscope setup GUI

Edits / generates four kinds of files:
  1. HAL shutters sequence  e.g. 405f1_750f10_650f10_560f10_405f10_shutters_1cam.xml
  2. HAL settings file       e.g. Epi-405s1-750s10-650s10-560s10-405s10-U2OS.xml
  3. Kilroy fluidics file    e.g. kilroy_protocol_MERFISH_lab.xml
  4. Dave automation recipe  e.g. dave_recipe_U2OS_1round+14rounds.xml

Uses only the Python standard library (tkinter); runs on Windows / macOS / Linux:
    python app/merfish_setup_gui.py
"""

import copy
import os
import re
import sys
import tkinter as tk
import xml.etree.ElementTree as ET
from tkinter import filedialog, messagebox, simpledialog, ttk
from xml.sax.saxutils import escape, quoteattr

APP_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(APP_DIR)
# Where the lab files live in the repo (falls back to the app folder)
LAB_HAL_DIR = os.path.join(REPO_DIR, "lab_files", "hal")
LAB_KILROY_DIR = os.path.join(REPO_DIR, "lab_files", "kilroy")
LAB_DAVE_DIR = os.path.join(REPO_DIR, "lab_files", "dave")
DEFAULT_KILROY_NAME = "kilroy_protocol_MERFISH_lab.xml"


def dialog_dir(current_file, lab_dir, fallback):
    """Start folder for a file dialog: the current file's folder, else the lab folder, else fallback."""
    if current_file and os.path.isdir(os.path.dirname(current_file)):
        return os.path.dirname(current_file)
    return lab_dir if os.path.isdir(lab_dir) else fallback


def settings_search_dirs(*extra):
    """Folders to search for settings files (unique, in order)."""
    out = []
    for d in list(extra) + [LAB_HAL_DIR, APP_DIR]:
        if d and d not in out and os.path.isdir(d):
            out.append(d)
    return out

# ----------------------------------------------------------------------------
# Laser channels: (HAL channel index, wavelength, preview color)
# If a microscope uses a different channel order, change it here only.
# ----------------------------------------------------------------------------
LASERS = [
    (0, "750", "#7f1d1d"),
    (1, "650", "#dc2626"),
    (2, "560", "#d4a20a"),
    (3, "488", "#16a34a"),
    (4, "405", "#7c3aed"),
]
CH2WL = {c: w for c, w, _ in LASERS}
WL2CH = {w: c for c, w, _ in LASERS}
CH2COLOR = {c: col for c, _, col in LASERS}
N_CHANNELS = len(LASERS)

XML_HEADER = '<?xml version="1.0" encoding="ISO-8859-1"?>'

SEQUENCE_PRESETS = {
    "Fiducial + 5-color z-stack (405f1 750/650/560/488/405 f10)":
        [("405", 1), ("750", 10), ("650", 10), ("560", 10), ("488", 10), ("405", 10)],
    "Fiducial + 4-color z-stack (405f1 750/650/560/405 f10)":
        [("405", 1), ("750", 10), ("650", 10), ("560", 10), ("405", 10)],
    "4-color z-stack (650/560/488/405 f10)":
        [("650", 10), ("560", 10), ("488", 10), ("405", 10)],
    "5-color single frame (750/650/560/488/405 f1)":
        [("750", 1), ("650", 1), ("560", 1), ("488", 1), ("405", 1)],
}

# Built-in default settings template (from Dsk-650s10-560s10-488s10-405s10-U2OS.xml)
DEFAULT_SETTINGS_XML = """<?xml version="1.0" encoding="ISO-8859-1"?>
<settings>
  <camera1 validate="True">
    <binning type="string">1x1</binning>
    <default_max type="int">2000</default_max>
    <default_min type="int">100</default_min>
    <defect_correct_mode type="string">OFF</defect_correct_mode>
    <exposure_time type="float">0.25001094117647055</exposure_time>
    <extension type="string"/>
    <flip_horizontal type="boolean">True</flip_horizontal>
    <flip_vertical type="boolean">False</flip_vertical>
    <fps type="float">3.9998249488375337</fps>
    <readout_speed type="int">2</readout_speed>
    <saved type="boolean">True</saved>
    <subarray_hpos type="int">0</subarray_hpos>
    <subarray_hsize type="int">2304</subarray_hsize>
    <subarray_vpos type="int">0</subarray_vpos>
    <subarray_vsize type="int">2304</subarray_vsize>
    <transpose type="boolean">True</transpose>
    <trigger_active type="string">SYNCREADOUT</trigger_active>
    <trigger_polarity type="string">POSITIVE</trigger_polarity>
    <trigger_source type="string">INTERNAL</trigger_source>
    <x_bin type="int">1</x_bin>
    <x_end type="int">256</x_end>
    <x_pixels type="int">2304</x_pixels>
    <x_start type="int">1</x_start>
    <y_bin type="int">1</y_bin>
    <y_end type="int">256</y_end>
    <y_pixels type="int">2304</y_pixels>
    <y_start type="int">1</y_start>
  </camera1>
  <display00 validate="False">
    <camera1 validate="True">
      <center_x type="float">344.0</center_x>
      <center_y type="float">1728.0</center_y>
      <colortable type="string">ramp.ctbl</colortable>
      <display_max type="int">44353</display_max>
      <display_min type="int">100</display_min>
      <initialized type="boolean">True</initialized>
      <scale type="int">-3</scale>
      <sync type="int">0</sync>
    </camera1>
    <feed_name type="string">camera1</feed_name>
  </display00>
  <film validate="False">
    <acq_mode type="string">fixed_length</acq_mode>
    <auto_increment type="boolean">True</auto_increment>
    <auto_shutters type="boolean">True</auto_shutters>
    <extension type="string"/>
    <filename type="string">Dsk-650s10-560s10-488s10-405s10</filename>
    <filetype type="string">.tif</filetype>
    <frames type="int">40</frames>
    <want_bell type="boolean">True</want_bell>
  </film>
  <focuslock validate="True">
    <calibrate validate="True">
      <deadtime type="int">20</deadtime>
      <frames_to_pause type="int">2</frames_to_pause>
      <range type="float">600.0</range>
      <step_size type="float">10.0</step_size>
    </calibrate>
    <find_sum validate="True">
      <step_size type="float">0.1</step_size>
    </find_sum>
    <hardware_z_scan validate="True">
      <z_offsets type="string">0,0.8,1.6,2.4,3.2,4,4.8,5.6,6.4,7.2, 7.2,6.4,5.6,4.8,4,3.2,2.4,1.6,0.8,0, 0,0.8,1.6,2.4,3.2,4,4.8,5.6,6.4,7.2, 7.2,6.4,5.6,4.8,4,3.2,2.4,1.6,0.8,0 </z_offsets>
    </hardware_z_scan>
    <jump_size type="float">0.1</jump_size>
    <locked validate="True">
      <buffer_length type="int">3</buffer_length>
      <lock_gain type="float">0.1</lock_gain>
      <lock_gain_max type="float">0.1</lock_gain_max>
      <minimum_sum type="float">-1.0</minimum_sum>
      <offset_threshold type="float">50.0</offset_threshold>
    </locked>
    <optimal_mode validate="True">
      <bracket_step type="float">1000.0</bracket_step>
      <quality_threshold type="float">0.0</quality_threshold>
      <scan_hold type="int">10</scan_hold>
      <scan_step type="float">100.0</scan_step>
    </optimal_mode>
    <scan validate="True">
      <minimum_sum type="float">10000.0</minimum_sum>
      <offset_threshold type="float">20.0</offset_threshold>
      <scan_range type="float">10.0</scan_range>
      <scan_step type="float">0.05</scan_step>
    </scan>
  </focuslock>
  <illumination validate="True">
    <default_power type="custom">1.000,1.000,1.000,1.000,1.000</default_power>
    <on_off_state type="custom">False,False,False,False,False</on_off_state>
    <power_buttons type="custom">[[['Max', 1.0], ['Low', 0.1]], [['Max', 1.0], ['Low', 0.1]], [['Max', 1.0], ['Low', 0.1]], [['Max', 1.0], ['Low', 0.1]], [['Max', 1.0], ['Low', 0.0088]]]</power_buttons>
    <shutters type="string">650f10_560f10_488f10_405f10_shutters_1cam.xml</shutters>
  </illumination>
  <mosaic validate="False">
    <flip_horizontal type="boolean">False</flip_horizontal>
    <flip_vertical type="boolean">True</flip_vertical>
    <obj1 type="custom">60x,0.109,0.0,0.0</obj1>
    <obj2 type="custom">10x,0.67,0.0,0.0</obj2>
    <objective type="string">obj1</objective>
    <transpose type="boolean">True</transpose>
  </mosaic>
  <stage validate="True">
    <large_step_size type="float">25.0</large_step_size>
    <small_step_size type="float">5.0</small_step_size>
  </stage>
  <timing validate="True">
    <time_base type="string">camera1</time_base>
  </timing>
</settings>
"""


# ============================================================================
# Utilities
# ============================================================================
def fmt_num(v, decimals=6):
    """Number -> compact string (2.4000000000000004 -> '2.4', 4.0 -> '4')."""
    s = f"{round(float(v), decimals):.{decimals}f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def fmt_duration(sec):
    sec = int(round(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def write_text_crlf(path, text):
    """Write in the original HAL / Kilroy format: ISO-8859-1 encoding, Windows line endings."""
    with open(path, "w", encoding="iso-8859-1", errors="xmlcharrefreplace", newline="\r\n") as f:
        f.write(text)


def parse_float_list(text):
    out = []
    for tok in (text or "").replace("\n", ",").split(","):
        tok = tok.strip()
        if tok:
            out.append(float(tok))
    return out


# ============================================================================
# Shutters sequence (model)
# ============================================================================
def new_step(wl, frames, power=1.0, color="255,255,255"):
    return {"channel": WL2CH[wl], "frames": int(frames), "power": float(power), "color": color}


def total_frames(steps):
    return sum(s["frames"] for s in steps)


def shutters_filename(steps):
    if not steps:
        return "empty_shutters_1cam.xml"
    return "_".join(f"{CH2WL.get(s['channel'], s['channel'])}f{s['frames']}" for s in steps) + "_shutters_1cam.xml"


def sequence_tokens(steps, letter="s"):
    return "-".join(f"{CH2WL.get(s['channel'], s['channel'])}{letter}{s['frames']}" for s in steps)


def parse_shutters(path):
    root = ET.parse(path).getroot()
    if root.tag != "repeat":
        raise ValueError(f"Not a shutters file (root element is <{root.tag}>, expected <repeat>)")
    overs = int(float(root.findtext("oversampling", "1")))
    events = []
    for ev in root.findall("event"):
        events.append({
            "channel": int(ev.findtext("channel")),
            "power": float(ev.findtext("power", "1")),
            "on": float(ev.findtext("on")),
            "off": float(ev.findtext("off")),
            "color": (ev.findtext("color") or "255,255,255").strip(),
        })
    events.sort(key=lambda e: e["on"])
    warnings = []
    steps = []
    t = 0.0
    for e in events:
        if abs(e["on"] - t) > 1e-6:
            warnings.append(f"Channel {e['channel']}: on={e['on']} does not follow the previous event (expected {t})")
        n = e["off"] - e["on"]
        if abs(n - round(n)) > 1e-6:
            warnings.append(f"Channel {e['channel']}: {n} frames is not an integer, rounded")
        steps.append({"channel": e["channel"], "frames": max(1, int(round(n))),
                      "power": e["power"], "color": e["color"]})
        t = e["off"]
    file_frames = int(float(root.findtext("frames", "0")))
    if file_frames != total_frames(steps):
        warnings.append(f"File says <frames>={file_frames}, but the events add up to {total_frames(steps)} frames")
    return overs, steps, warnings


def shutters_to_string(steps, oversampling=1):
    lines = [XML_HEADER, "<repeat>",
             f"  <oversampling>{int(oversampling)}</oversampling>",
             f"  <frames>{total_frames(steps)}</frames>", ""]
    t = 0
    for s in steps:
        lines += ["  <event>",
                  f"    <channel>{s['channel']}</channel>",
                  f"    <power>{fmt_num(s['power'])}</power>",
                  f"    <on>{float(t):.1f}</on>",
                  f"    <off>{float(t + s['frames']):.1f}</off>",
                  f"    <color>{s.get('color', '255,255,255')}</color>",
                  "  </event>", ""]
        t += s["frames"]
    lines.append("</repeat>")
    return "\n".join(lines) + "\n"


Z_MODES = ["Serpentine (up, down, …)", "Always bottom-up", "No Z scan (all at start)"]


def make_z_groups(steps, z_start, z_step, mode):
    """Return the list of z values for each step. Single-frame steps (e.g. 405 fiducial) stay at z start."""
    groups = []
    up = True
    for s in steps:
        n = s["frames"]
        if n == 1 or mode == Z_MODES[2]:
            groups.append([z_start] * n)
            continue
        zs = [z_start + i * z_step for i in range(n)]
        if not up:
            zs.reverse()
        groups.append(zs)
        if mode == Z_MODES[0]:
            up = not up
    return groups


def z_groups_to_string(groups):
    """z-stacks are separated by ', ' (matching the original files); adjacent single frames by ','."""
    out = ""
    for i, g in enumerate(groups):
        if i:
            out += "," if (len(g) == 1 and len(groups[i - 1]) == 1) else ", "
        out += ",".join(fmt_num(z) for z in g)
    return out + " "


def infer_z_params(steps, z_values):
    """Try to infer (start, step, mode) from existing z_offsets. Returns None on failure."""
    if len(z_values) != total_frames(steps):
        return None
    i = 0
    start = step = None
    for s in steps:
        g = z_values[i:i + s["frames"]]
        i += s["frames"]
        if len(g) > 1 and step is None:
            step = abs(g[1] - g[0])
            start = min(g)
    if start is None:
        start = z_values[0] if z_values else 0.0
        step = 0.8
    for mode in Z_MODES:
        gen = [z for g in make_z_groups(steps, start, step, mode) for z in g]
        if all(abs(a - b) < 1e-6 for a, b in zip(gen, z_values)):
            return start, step, mode
    return None


# ============================================================================
# Settings (model): keeps the ElementTree so every parameter is saved unchanged
# ============================================================================
def settings_from_string(text):
    return ET.fromstring(text.encode("iso-8859-1"))


def settings_to_string(root):
    r = copy.deepcopy(root)
    ET.indent(r, "  ")
    body = ET.tostring(r, encoding="unicode").replace(" />", "/>")
    return XML_HEADER + "\n" + body + "\n"


def sget(root, path, default=""):
    el = root.find(path)
    if el is None or el.text is None:
        return default
    return el.text


def sset(root, path, value, typ="string"):
    el = root.find(path)
    if el is None:
        parent = root
        for part in path.split("/"):
            child = parent.find(part)
            if child is None:
                child = ET.SubElement(parent, part)
            parent = child
        el = parent
        el.set("type", typ)
    el.text = str(value)


def split_settings_name(stem):
    """'Epi-405s1-750s10-U2OS' -> ('Epi', 'U2OS')."""
    toks = stem.split("-")
    idx = [i for i, t in enumerate(toks) if re.fullmatch(r"\d{3}s\d+", t)]
    if not idx:
        return stem, ""
    return "-".join(toks[:idx[0]]), "-".join(toks[idx[-1] + 1:])


def movie_name_for(settings_name):
    """Settings name without the sample tag = movie name in Dave ('Dsk-405s1-750s6-U2OS' -> 'Dsk-405s1-750s6')."""
    _, tag = split_settings_name(settings_name)
    return settings_name[:-(len(tag) + 1)] if tag and settings_name.endswith("-" + tag) else settings_name


# ----------------------------------------------------------------------------
# Built-in settings presets. Each preset = sequence + z rule + parameters changed from the built-in template.
# film/filename, film/frames, illumination/shutters and z_offsets are generated from the sequence.
# z = (start µm, step µm, index into Z_MODES)
# ----------------------------------------------------------------------------
U2OS_HYB_FOCUSLOCK = {
    "focuslock/locked/buffer_length": "5",
    "focuslock/locked/lock_gain": "0.5",
    "focuslock/locked/lock_gain_max": "0.7",
    "focuslock/locked/minimum_sum": "30000.0",
}
SETTINGS_PRESETS = [
    {"group": "Lab", "name": "Dsk-650s10-560s10-488s10-405s10-U2OS",
     "steps": [("650", 10), ("560", 10), ("488", 10), ("405", 10)], "z": (0, 0.8, 0), "set": {}},
    {"group": "Lab", "name": "Dsk-750s1-650s1-560s1-488s1-405s1-cell",
     "steps": [("750", 1), ("650", 1), ("560", 1), ("488", 1), ("405", 1)], "z": (0, 0.8, 0),
     "tag_in_film": True,
     "set": {"camera1/exposure_time": "0.1", "camera1/flip_horizontal": "False",
             "camera1/flip_vertical": "True", "illumination/default_power": "1.000,0.400,0.250,0.100,0.015",
             "mosaic/flip_horizontal": "True", "mosaic/flip_vertical": "False",
             "mosaic/obj1": "40x,0.16,0.0,0.0", "mosaic/obj2": "10x,0.66,0.0,0.0", "mosaic/objective": "obj2"}},
    {"group": "Lab", "name": "Epi-405s1-750s10-650s10-560s10-405s10-U2OS",
     "steps": [("405", 1), ("750", 10), ("650", 10), ("560", 10), ("405", 10)], "z": (0, 0.8, 0), "set": {}},
    {"group": "Lab", "name": "Epi-405s1-750s10-650s10-560s10-488s10-405s10-U2OS",
     "steps": [("405", 1), ("750", 10), ("650", 10), ("560", 10), ("488", 10), ("405", 10)], "z": (0, 0.8, 0),
     "set": {}},
    {"group": "U2OS hyb", "name": "Dsk-405s1-750s6-650s6-405s6-U2OS",
     "steps": [("405", 1), ("750", 6), ("650", 6), ("405", 6)], "z": (0, 1, 0),
     "set": dict(U2OS_HYB_FOCUSLOCK, **{"display00/camera1/center_x": "988.0", "display00/camera1/center_y": "116.0",
                                       "display00/camera1/display_max": "4749"})},
    {"group": "U2OS hyb", "name": "Dsk-405s1-750s6-650s6-560s6-U2OS",
     "steps": [("405", 1), ("750", 6), ("650", 6), ("560", 6)], "z": (0, 1, 0),
     "set": dict(U2OS_HYB_FOCUSLOCK, **{"display00/camera1/center_x": "352.0", "display00/camera1/center_y": "984.0",
                                       "display00/camera1/display_max": "6174", "mosaic/objective": "obj2"})},
]


def preset_label(p):
    return f"{p['group']} · {p['name']}"


def find_settings_preset(name):
    return next((p for p in SETTINGS_PRESETS if p["name"] == name), None)


# ============================================================================
# Kilroy (model)
# ============================================================================
class KilroyConfig:
    def __init__(self):
        self.attrib = {"num_valves": "4", "num_pumps": "1"}
        self.valves = []     # [ [name, {valve_id(int): port(str)}], ... ]
        self.pumps = []      # [ [name, {"speed": "2.6", "direction": "Forward"}], ... ]
        self.protocols = []  # [ [name, [[tag, duration(str), command], ...]], ... ]
        self.comments = {}   # section tag -> [comment text] (comments that appear before that section)

    @property
    def num_valves(self):
        n = int(self.attrib.get("num_valves", "1") or 1)
        for _, pos in self.valves:
            if pos:
                n = max(n, max(pos))
        return n

    @classmethod
    def load(cls, path):
        parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
        root = ET.parse(path, parser).getroot()
        if root.tag != "kilroy_configuration":
            raise ValueError(f"Not a Kilroy file (root element is <{root.tag}>)")
        k = cls()
        k.attrib = dict(root.attrib)
        pending = []
        for child in root:
            if child.tag is ET.Comment:
                pending.append(child.text)
                continue
            k.comments[child.tag] = pending
            pending = []
            if child.tag == "valve_commands":
                for vc in child.findall("valve_cmd"):
                    pos = {}
                    for vp in vc.findall("valve_pos"):
                        pos[int(vp.get("valve_ID"))] = vp.get("port_ID")
                    k.valves.append([vc.get("name", ""), pos])
            elif child.tag == "pump_commands":
                for pc in child.findall("pump_cmd"):
                    cfg = pc.find("pump_config")
                    k.pumps.append([pc.get("name", ""), dict(cfg.attrib) if cfg is not None else {}])
            elif child.tag == "kilroy_protocols":
                for p in child.findall("protocol"):
                    steps = []
                    for st in p:
                        if st.tag is ET.Comment:
                            continue
                        steps.append([st.tag, st.get("duration", "0"), (st.text or "").strip()])
                    k.protocols.append([p.get("name", ""), steps])
        k.comments["_end"] = pending
        return k

    def to_string(self):
        attrib = dict(self.attrib)
        attrib["num_valves"] = str(self.num_valves)
        L = [XML_HEADER,
             "<kilroy_configuration " + " ".join(f"{k}={quoteattr(v)}" for k, v in attrib.items()) + ">"]

        def comments(tag):
            for c in self.comments.get(tag, []):
                L.append(f"  <!--{c}-->")

        comments("valve_commands")
        L.append("  <valve_commands>")
        for name, pos in self.valves:
            L.append(f"    <valve_cmd name={quoteattr(name)}>")
            for vid in sorted(pos):
                L.append(f"      <valve_pos valve_ID=\"{vid}\" port_ID={quoteattr(str(pos[vid]))}></valve_pos>")
            L.append("    </valve_cmd>")
        L.append("  </valve_commands>")
        L.append("")
        comments("pump_commands")
        L.append("  <pump_commands>")
        for name, cfg in self.pumps:
            L.append(f"    <pump_cmd name={quoteattr(name)}>")
            attrs = " ".join(f"{k}={quoteattr(v)}" for k, v in cfg.items() if v != "")
            L.append(f"      <pump_config {attrs}/>")
            L.append("    </pump_cmd>")
        L.append("  </pump_commands>")
        L.append("")
        comments("kilroy_protocols")
        L.append("  <kilroy_protocols>")
        for name, steps in self.protocols:
            L.append(f"    <protocol name={quoteattr(name)}>")
            for tag, dur, cmd in steps:
                L.append(f"      <{tag} duration={quoteattr(str(dur))}>{escape(cmd)}</{tag}>")
            L.append("    </protocol>")
            L.append("")
        L.append("  </kilroy_protocols>")
        comments("_end")
        L.append("</kilroy_configuration>")
        return "\n".join(L) + "\n"

    def protocol_seconds(self, steps):
        tot = 0.0
        for _, dur, _ in steps:
            try:
                tot += float(dur)
            except ValueError:
                pass
        return tot

    def validate(self):
        problems = []
        vnames = {v[0] for v in self.valves}
        pnames = {p[0] for p in self.pumps}
        for kind, items in (("valve command", self.valves), ("pump command", self.pumps), ("protocol", self.protocols)):
            seen = set()
            for it in items:
                if it[0] in seen:
                    problems.append(f"Duplicate {kind} name: {it[0]}")
                seen.add(it[0])
        for pname, steps in self.protocols:
            for i, (tag, dur, cmd) in enumerate(steps, 1):
                if tag == "valve" and cmd not in vnames:
                    problems.append(f"Protocol '{pname}' step {i}: undefined valve command '{cmd}'")
                if tag == "pump" and cmd not in pnames:
                    problems.append(f"Protocol '{pname}' step {i}: undefined pump command '{cmd}'")
                try:
                    float(dur)
                except ValueError:
                    problems.append(f"Protocol '{pname}' step {i}: duration '{dur}' is not a number")
        return problems


# ----------------------------------------------------------------------------
# Built-in Kilroy presets: generated from the lab's valve wiring and protocol templates; only flow/wait times differ.
# ----------------------------------------------------------------------------
KILROY_PUMP_COMMENTS = [" speed 200 ~= 833 uL / 10 sec ", " 1 uL corresponds to 1.2 pump position units ",
                        " speed 33 corresponds to 1 mL / min "]


def make_kilroy_preset(cleave, hyb, n_hyb=14, primes=(11, 7, 13, 14)):
    """cleave = (TCEP flow, TCEP wait, wash flow, wash wait) in seconds;
    hyb = (hyb flow, hyb wait, wash1 flow, wash1 wait, readout flow, readout wait, wash2 flow, wash2 wait, image flow, image wait) in seconds."""
    k = KilroyConfig()
    k.comments = {"valve_commands": [], "pump_commands": list(KILROY_PUMP_COMMENTS), "kilroy_protocols": [], "_end": []}
    fixed = [("Set Image", {1: "3"}), ("Set Wash", {1: "4"}), ("Set TCEP", {1: "1"}),
             ("Set Readout", {1: "2", 4: "4"}), ("Seal", {})]
    k.valves = [[name, {v: pos.get(v, "8") for v in range(1, 5)}] for name, pos in fixed]
    # Daisy-chained valves: valve 1 ports 5–7 = Hyb 1–3; valves 2/3/4 ports 1–7 = Hyb 4–10 / 11–17 / 18–24
    hyb_ports = [(1, 5), (1, 6), (1, 7)] + [(v, p) for v in (2, 3, 4) for p in range(1, 8)]
    for n, (valve, port) in enumerate(hyb_ports, 1):
        k.valves.append([f"Set Hyb {n}", {v: (str(port) if v == valve else "8") for v in range(1, 5)}])
    k.pumps = [["Flow 2 ml/min", {"speed": "10.4", "direction": "Forward"}],
               ["Flow 1 ml/min", {"speed": "5.2", "direction": "Forward"}],
               ["Flow 0.5 ml/min", {"speed": "2.6", "direction": "Forward"}],
               ["Stop Flow", {"speed": "0.0"}]]
    V = lambda d, c: ["valve", str(d), c]
    P = lambda d, c: ["pump", str(d), c]
    F05, F1, F2, STOP = "Flow 0.5 ml/min", "Flow 1 ml/min", "Flow 2 ml/min", "Stop Flow"
    c = cleave
    k.protocols.append(["Cleave", [V(5, "Set TCEP"), P(c[0], F05), P(c[1], STOP), V(5, "Set Wash"),
                                   P(c[2], F1), P(c[3], STOP), V(5, "Seal")]])
    k.protocols.append(["Flow Image Buffer", [V(5, "Set Image"), P(120, F1), P(60, STOP), V(5, "Seal")]])
    for n in primes:
        k.protocols.append([f"Prime {n} + 4", [P(15, F2)] + [V(20, f"Set Hyb {i}") for i in range(1, n + 1)]
                            + [V(30, "Set Readout"), V(30, "Set TCEP"), V(30, "Set Image"), V(60, "Set Wash"),
                               P(5, STOP)]])
    h = hyb
    for n in range(1, n_hyb + 1):
        k.protocols.append([f"Hybridize {n}", [
            V(5, f"Set Hyb {n}"), P(h[0], F05), P(h[1], STOP),
            V(5, "Set Wash"), P(h[2], F05), P(h[3], STOP),
            V(5, "Set Readout"), P(h[4], F05), P(h[5], STOP),
            V(5, "Set Wash"), P(h[6], F05), P(h[7], STOP),
            V(5, "Set Image"), P(h[8], F05), P(h[9], STOP), V(5, "Seal")]])
    clean = []
    for name in [f"Set Hyb {i}" for i in range(1, 25)] + ["Set Readout", "Set TCEP", "Set Image"]:
        clean += [V(20, name), P(15, F2)]
    k.protocols.append(["Clean all", clean + [V(60, "Set Wash"), P(5, STOP)]])
    return k


KILROY_PRESETS = {
    "Lab · kilroy_protocol_MERFISH_lab": {
        "file": "kilroy_protocol_MERFISH_lab.xml",
        "make": lambda: make_kilroy_preset((300, 600, 400, 300), (500, 400, 300, 60, 300, 700, 300, 300, 240, 60))},
    "U2OS hyb · longer flow times": {
        "file": "kilroy_protocol_MERFISH_lab.xml",
        "make": lambda: make_kilroy_preset((500, 660, 500, 600), (600, 400, 400, 60, 400, 700, 400, 300, 400, 60))},
}


# ============================================================================
# Dave automation recipe (model)
#
# Supports the lab's usual MERFISH structure:
#   [wakeup] → imaging (Movie Loop 1, over all positions)
#   hyb loop (Hybridize loop k): each round Kilroy protocols → [wakeup] → imaging
# ============================================================================
WAKEUP_LOOP = "Movie Loop Wakeup"
DAVE_MOVIE_TAGS = {"name", "length", "parameters", "check_focus", "overwrite", "variable_entry"}
DAVE_KINDS = {"image": "Image once", "hyb": "Hyb loop"}


def make_round_values(fmt, a, b):
    """'Cleave, Hybridize {n}', 1, 3 -> [['Cleave', 'Hybridize 1'], ...]."""
    protos = [x.strip() for x in fmt.split(",") if x.strip()]
    return [[p.format(n=n) for p in protos] for n in range(a, b + 1)]


def detect_round_pattern(values):
    """Inverse of make_round_values. Returns None if no pattern is found."""
    if not values or not values[0]:
        return None
    nums = sorted({int(x) for p in values[0] for x in re.findall(r"\d+", p)})
    for a in nums:
        fmt = None
        for i, v in enumerate(values):
            n = a + i
            t = ", ".join(re.sub(rf"(?<!\d){n}(?!\d)", "{n}", p) for p in v)
            if fmt is None:
                fmt = t
            elif t != fmt:
                fmt = None
                break
        if fmt and "{n}" in fmt:
            return fmt, a, a + len(values) - 1
    return None


def new_dave_stage(kind, params, movie=None, length=1, checks="100", wake=True, wake_checks="100",
                   fmt="Cleave, Hybridize {n}", rounds=(1, 1)):
    st = {"kind": kind, "params": params, "movie": movie if movie is not None else movie_name_for(params),
          "length": str(length), "checks": str(checks), "overwrite": "False",
          "wake": bool(wake), "wake_checks": str(wake_checks)}
    if kind == "hyb":
        st["values"] = make_round_values(fmt, *rounds)
    return st


class DaveRecipe:
    def __init__(self):
        self.wakeup_ms = "10000"
        self.wakeup_file = "D:\\settings\\wakeup_position.txt"
        self.wakeup_params = "default"
        self.wakeup_length = "1"
        self.wakeup_name = "Wakeup"
        self.positions_loop = "Movie Loop 1"
        self.positions_file = ""
        self.stages = []

    @classmethod
    def load(cls, path):
        return cls.from_root(ET.parse(path).getroot())

    @classmethod
    def from_root(cls, root):
        if root.tag != "recipe":
            raise ValueError(f"Not a Dave recipe (root element is <{root.tag}>, expected <recipe>)")
        r = cls()
        cs = root.find("command_sequence")
        if cs is None:
            raise ValueError("Missing <command_sequence>")
        lv = {}
        for v in root.findall("loop_variable"):
            fp = v.find("file_path")
            vals = []
            for val in v.findall("value"):
                for ch in val:
                    if ch.tag != "valve_protocol":
                        raise ValueError(f"Unsupported content in loop_variable: <{ch.tag}>")
                vals.append([(p.text or "").strip() for p in val])
            lv[v.get("name")] = {"file": (fp.text or "").strip() if fp is not None else None, "values": vals}
        seen_wakeup = []

        def parse_movie(mv):
            extra = [c.tag for c in mv if c.tag not in DAVE_MOVIE_TAGS]
            if extra:
                raise ValueError(f"This movie uses settings the tool does not support: {', '.join('<%s>' % e for e in extra)}")
            cf = mv.find("check_focus")
            return {"name": (mv.findtext("name") or "").strip(), "length": (mv.findtext("length") or "").strip(),
                    "params": (mv.findtext("parameters") or "").strip(),
                    "checks": (cf.findtext("num_focus_checks") or "").strip() if cf is not None else "",
                    "overwrite": (mv.findtext("overwrite") or "False").strip()}

        def parse_seq(children, in_hyb):
            stages, wake = [], None
            for ch in children:
                if ch.tag == "wakeup":
                    wake = {"checks": ""}
                    if not seen_wakeup:
                        r.wakeup_ms = (ch.text or "").strip()
                    seen_wakeup.append(1)
                elif ch.tag == "variable_entry" and in_hyb:
                    continue
                elif ch.tag == "loop" and ch.find("variable_entry") is not None and ch.find("movie") is None:
                    if in_hyb:
                        raise ValueError("Nested hyb loops are not supported")
                    name = ch.get("name", "")
                    inner = parse_seq(list(ch), True)
                    if len(inner) != 1:
                        raise ValueError(f"Loop \"{name}\" should contain exactly one imaging step, found {len(inner)}")
                    if name not in lv or not lv[name]["values"]:
                        raise ValueError(f"No loop_variable values found for loop \"{name}\"")
                    st = inner[0]
                    st["kind"] = "hyb"
                    st["values"] = lv[name]["values"]
                    stages.append(st)
                elif ch.tag == "loop" and ch.find("movie") is not None and len(ch) == 1:
                    m = parse_movie(ch.find("movie"))
                    if ch.get("name") == WAKEUP_LOOP:
                        r.wakeup_name, r.wakeup_length, r.wakeup_params = m["name"], m["length"], m["params"]
                        wake = wake or {"checks": ""}
                        wake["checks"] = m["checks"]
                    else:
                        r.positions_loop = ch.get("name", r.positions_loop)
                        stages.append({"kind": "image", "params": m["params"], "movie": m["name"],
                                       "length": m["length"], "checks": m["checks"], "overwrite": m["overwrite"],
                                       "wake": wake is not None, "wake_checks": wake["checks"] if wake else "100"})
                        wake = None
                else:
                    raise ValueError(f"Unsupported Dave element <{ch.tag}>")
            return stages

        r.stages = parse_seq(list(cs), False)
        if lv.get(WAKEUP_LOOP, {}).get("file") is not None:
            r.wakeup_file = lv[WAKEUP_LOOP]["file"]
        if lv.get(r.positions_loop, {}).get("file") is not None:
            r.positions_file = lv[r.positions_loop]["file"]
        return r

    def hyb_loop_names(self):
        names, k = {}, 0
        for i, st in enumerate(self.stages):
            if st["kind"] == "hyb":
                k += 1
                names[i] = f"Hybridize loop {k}"
        return names

    def to_string(self):
        L = [XML_HEADER, "<recipe>", "\t<command_sequence>"]

        def movie(ind, name, length, params, checks, overwrite, loop):
            T = "\t" * ind
            out = [f"{T}<movie>", f'{T}\t<name increment="Yes">{escape(name)}</name>',
                   f"{T}\t<length>{escape(str(length))}</length>", f"{T}\t<parameters>{escape(params)}</parameters>"]
            if str(checks).strip():
                out += [f"{T}\t<check_focus>", f"{T}\t\t<num_focus_checks>{escape(str(checks))}</num_focus_checks>",
                        f"{T}\t\t<focus_scan/>", f"{T}\t</check_focus>"]
            out += [f"{T}\t<overwrite>{escape(overwrite)}</overwrite>",
                    f"{T}\t<variable_entry name={quoteattr(loop)}></variable_entry>", f"{T}</movie>"]
            return out

        def image(ind, st):
            T = "\t" * ind
            out = []
            if st["wake"]:
                out += [f"{T}<wakeup>{escape(self.wakeup_ms)}</wakeup>", f"{T}<loop name={quoteattr(WAKEUP_LOOP)}>"]
                out += movie(ind + 1, self.wakeup_name, self.wakeup_length, self.wakeup_params,
                             st["wake_checks"], "False", WAKEUP_LOOP)
                out += [f"{T}</loop>"]
            out += [f"{T}<loop name={quoteattr(self.positions_loop)}>"]
            out += movie(ind + 1, st["movie"], st["length"], st["params"], st["checks"], st.get("overwrite", "False"),
                         self.positions_loop)
            out += [f"{T}</loop>"]
            return out

        hyb_names = self.hyb_loop_names()
        for i, st in enumerate(self.stages):
            if st["kind"] == "hyb":
                name = hyb_names[i]
                L += [f"\t\t<loop name={quoteattr(name)}>", f"\t\t\t<variable_entry name={quoteattr(name)}></variable_entry>"]
                L += image(3, st)
                L += ["\t\t</loop>"]
            else:
                L += image(2, st)
            L.append("")
        L += ["\t</command_sequence>", ""]
        if any(st["wake"] for st in self.stages):
            L += [f"\t<loop_variable name={quoteattr(WAKEUP_LOOP)}>",
                  f"\t\t<file_path>{escape(self.wakeup_file)}</file_path>", "\t</loop_variable>", ""]
        L += [f"\t<loop_variable name={quoteattr(self.positions_loop)}>",
              f"\t\t<file_path>{escape(self.positions_file)}</file_path>", "\t</loop_variable>"]
        for i, st in enumerate(self.stages):
            if st["kind"] == "hyb":
                L += ["", f"\t<loop_variable name={quoteattr(hyb_names[i])}>"]
                for v in st["values"]:
                    L.append("\t\t<value>" + "".join(f"<valve_protocol>{escape(p)}</valve_protocol>" for p in v)
                             + "</value>")
                L.append("\t</loop_variable>")
        L.append("</recipe>")
        return "\n".join(L) + "\n"

    def n_movies(self):
        return sum(len(st["values"]) if st["kind"] == "hyb" else 1 for st in self.stages)

    def validate(self, kilroy=None, frames_lookup=None):
        problems = []
        if not self.stages:
            problems.append("The recipe has no stages")
        if not self.positions_file.strip():
            problems.append(f"The imaging positions file ({self.positions_loop}) is empty; set it in Dave before running")
        try:
            int(self.wakeup_ms)
        except ValueError:
            problems.append("Wakeup duration is not an integer (ms)")
        knames = {p[0] for p in kilroy.protocols} if kilroy and kilroy.protocols else None
        for i, st in enumerate(self.stages, 1):
            if not st["params"].strip():
                problems.append(f"Stage {i}: no settings chosen")
            try:
                n = int(st["length"])
                if n < 1:
                    raise ValueError
            except ValueError:
                problems.append(f"Stage {i}: invalid frame count \"{st['length']}\"")
            else:
                f = frames_lookup(st["params"]) if frames_lookup else None
                if f is not None and f != n:
                    problems.append(f"Stage {i}: {n} frames does not match the {f} frames of settings \"{st['params']}\"")
            if st["kind"] == "hyb":
                if not st["values"]:
                    problems.append(f"Stage {i}: the hyb loop has no rounds")
                if knames is not None:
                    missing = sorted({p for v in st["values"] for p in v if p not in knames})
                    if missing:
                        problems.append(f"Stage {i}: these protocols are not in the current Kilroy file: {', '.join(missing)}")
        return problems


def dave_preset_u2os_hyb():
    r = DaveRecipe()
    r.stages = [
        new_dave_stage("image", "Dsk-405s1-750s6-650s6-405s6-U2OS", length=19, wake_checks="100"),
        new_dave_stage("hyb", "Dsk-405s1-750s6-650s6-560s6-U2OS", length=19, wake_checks="50",
                       fmt="Cleave, Hybridize {n}", rounds=(1, 14)),
    ]
    return r


def dave_template(ctx, n_rounds):
    """Generic recipe using the current tab-2 settings: image once [+ n hyb rounds]. ctx = {'settings', 'movie', 'frames'}."""
    r = DaveRecipe()
    r.stages = [new_dave_stage("image", ctx["settings"], movie=ctx["movie"], length=ctx["frames"])]
    if n_rounds:
        r.stages.append(new_dave_stage("hyb", ctx["settings"], movie=ctx["movie"], length=ctx["frames"],
                                       wake_checks="50", rounds=(1, n_rounds)))
    return r


# make(ctx) -> DaveRecipe; kilroy = matching Kilroy preset (optional)
DAVE_PRESETS = {
    "U2OS hyb · 1 imaging round + 14 hyb rounds": {"make": lambda ctx: dave_preset_u2os_hyb(),
                                       "kilroy": "U2OS hyb · longer flow times"},
    "Template · 1 imaging round + 14 hyb rounds (current settings)": {"make": lambda ctx: dave_template(ctx, 14),
                                             "kilroy": None},
    "Template · image once, no fluidics (current settings)": {"make": lambda ctx: dave_template(ctx, 0),
                                             "kilroy": None},
}


# ============================================================================
# GUI widgets
# ============================================================================
def inline_edit(tree, item, column, on_done, values=None):
    """Edit a Treeview cell in place. column is the column name."""
    cols = list(tree["columns"])
    bbox = tree.bbox(item, f"#{cols.index(column) + 1}")
    if not bbox:
        return
    x, y, w, h = bbox
    cur = tree.set(item, column)
    if values is not None:
        ed = ttk.Combobox(tree, values=values)
        ed.set(cur)
    else:
        ed = ttk.Entry(tree)
        ed.insert(0, cur)
        ed.select_range(0, "end")
    ed.place(x=x, y=y, width=max(w, 60), height=h)
    ed.focus_set()
    state = {"done": False}

    def commit(_e=None):
        if state["done"]:
            return
        state["done"] = True
        val = ed.get()
        ed.destroy()
        if val != cur:
            on_done(val)

    def cancel(_e=None):
        state["done"] = True
        ed.destroy()

    def focus_out(_e=None):
        def check():
            if state["done"]:
                return
            try:
                f = ed.focus_get()
            except (KeyError, tk.TclError):
                return  # focus is in the combobox drop-down list
            if f is None or str(f).startswith(str(ed)):
                return
            commit()
        ed.after(50, check)

    ed.bind("<Return>", commit)
    ed.bind("<KP_Enter>", commit)
    ed.bind("<Escape>", cancel)
    ed.bind("<FocusOut>", focus_out)
    if values is not None:
        ed.bind("<<ComboboxSelected>>", commit)


def make_tree(parent, columns, widths, height=10, anchors=None):
    frame = ttk.Frame(parent)
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=height, selectmode="browse")
    for i, c in enumerate(columns):
        tree.heading(c, text=c)
        tree.column(c, width=widths[i], anchor=(anchors[i] if anchors else "w"), stretch=(i == len(columns) - 1))
    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    sb.grid(row=0, column=1, sticky="ns")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    return frame, tree


def tree_index(tree):
    sel = tree.selection()
    if not sel:
        return None
    return tree.index(sel[0])


def tree_reselect(tree, idx):
    kids = tree.get_children()
    if idx is not None and kids:
        idx = max(0, min(idx, len(kids) - 1))
        tree.selection_set(kids[idx])
        tree.see(kids[idx])


# ============================================================================
# Main application
# ============================================================================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MERFISH Microscope Setup")
        self.geometry("1200x820")
        self.minsize(1120, 780)
        self.last_dir = LAB_HAL_DIR if os.path.isdir(LAB_HAL_DIR) else APP_DIR

        # --- state ---
        self.steps = [new_step(w, n) for w, n in SEQUENCE_PRESETS["4-color z-stack (650/560/488/405 f10)"]]
        self.oversampling = tk.IntVar(value=1)
        self.settings_root = settings_from_string(DEFAULT_SETTINGS_XML)
        self.settings_source = "Built-in default template (Dsk-650s10-560s10-488s10-405s10-U2OS)"
        self.kilroy = None
        self.kilroy_path = None
        self.dave = dave_preset_u2os_hyb()
        self.dave_path = None
        self._film_frames_cache = {}

        self._build_vars()
        self._build_ui()
        self.pull_quick()
        self.refresh_steps()
        self.v_dave_preset.set(next(iter(DAVE_PRESETS)))  # this is the recipe loaded at startup
        self.refresh_dave()

        default_k = next((p for p in (os.path.join(LAB_KILROY_DIR, DEFAULT_KILROY_NAME),
                                      os.path.join(APP_DIR, DEFAULT_KILROY_NAME)) if os.path.exists(p)), None)
        if default_k:
            self.load_kilroy(default_k, quiet=True)
        else:
            self.apply_kilroy_preset(next(iter(KILROY_PRESETS)))

    # ------------------------------------------------------------------ vars
    def _build_vars(self):
        V = tk.StringVar
        self.v_prefix = V(value="Dsk")
        self.v_tag = V(value="U2OS")
        self.v_auto_film = tk.BooleanVar(value=True)
        self.v_tag_in_film = tk.BooleanVar(value=False)
        self.v_film = V()
        self.v_exposure = V()
        self.v_fps_hint = V()
        self.v_cam_fh = tk.BooleanVar()
        self.v_cam_fv = tk.BooleanVar()
        self.v_cam_tr = tk.BooleanVar()
        self.v_mos_fh = tk.BooleanVar()
        self.v_mos_fv = tk.BooleanVar()
        self.v_mos_tr = tk.BooleanVar()
        self.v_objective = V()
        self.v_obj = {k: [V(), V(), V(), V()] for k in ("obj1", "obj2", "obj3")}
        self.v_power = [V() for _ in range(N_CHANNELS)]
        self.v_auto_z = tk.BooleanVar(value=True)
        self.v_z_start = V(value="0")
        self.v_z_step = V(value="0.8")
        self.v_z_mode = V(value=Z_MODES[0])
        self.v_status = V(value="Ready")
        self.v_seq_info = V()
        self.v_names = V()
        # step editor
        self.v_step_wl = V(value=LASERS[1][1])
        self.v_step_frames = V(value="10")
        self.v_step_power = V(value="1")
        self.v_preset = V()

        self.v_exposure.trace_add("write", lambda *a: self._update_fps_hint())
        for v in (self.v_prefix, self.v_tag, self.v_z_start, self.v_z_step, self.v_z_mode):
            v.trace_add("write", lambda *a: self.update_derived())
        self.v_auto_film.trace_add("write", lambda *a: self.update_derived())
        self.v_tag_in_film.trace_add("write", lambda *a: self.update_derived())
        self.v_auto_z.trace_add("write", lambda *a: self._on_auto_z())
        self.oversampling.trace_add("write", lambda *a: self.update_derived())

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        style = ttk.Style(self)
        if sys.platform.startswith("linux"):
            style.theme_use("clam")
        style.configure("Big.TButton", font=("TkDefaultFont", 11, "bold"))
        style.configure("Hint.TLabel", foreground="#666666")
        style.configure("Bad.TLabel", foreground="#b91c1c")
        style.configure("Good.TLabel", foreground="#15803d")

        top = ttk.Frame(self, padding=(10, 8, 10, 0))
        top.pack(fill="x")
        ttk.Label(top, text="MERFISH Setup", font=("TkDefaultFont", 15, "bold")).pack(side="left")
        ttk.Button(top, text="⬇ Export shutters + settings…", style="Big.TButton",
                   command=self.export_both).pack(side="right")
        ttk.Button(top, text="Open settings…", command=self.open_settings).pack(side="right", padx=6)
        self.v_settings_preset = tk.StringVar()
        cb = ttk.Combobox(top, textvariable=self.v_settings_preset, values=[preset_label(p) for p in SETTINGS_PRESETS],
                          width=34, state="readonly")
        cb.pack(side="right", padx=(4, 6))
        cb.bind("<<ComboboxSelected>>", lambda e: self.choose_settings_preset())
        ttk.Label(top, text="Preset:").pack(side="right")

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=8)
        self.tab_seq = ttk.Frame(self.nb, padding=10)
        self.tab_set = ttk.Frame(self.nb, padding=10)
        self.tab_adv = ttk.Frame(self.nb, padding=10)
        self.tab_kil = ttk.Frame(self.nb, padding=10)
        self.tab_dave = ttk.Frame(self.nb, padding=10)
        self.nb.add(self.tab_seq, text="1  Sequence (shutters / Z)")
        self.nb.add(self.tab_set, text="2  Microscope settings")
        self.nb.add(self.tab_adv, text="3  All parameters (advanced)")
        self.nb.add(self.tab_kil, text="4  Fluidics (Kilroy)")
        self.nb.add(self.tab_dave, text="5  Automation (Dave)")
        self._current_tab = 0
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self._build_seq_tab(self.tab_seq)
        self._build_settings_tab(self.tab_set)
        self._build_adv_tab(self.tab_adv)
        self._build_kilroy_tab(self.tab_kil)
        self._build_dave_tab(self.tab_dave)

        bar = ttk.Frame(self, padding=(10, 0, 10, 6))
        bar.pack(fill="x")
        ttk.Label(bar, textvariable=self.v_status, style="Hint.TLabel").pack(side="left")

    def status(self, msg):
        self.v_status.set(msg)

    # ------------------------------------------------------------ tab 1 UI
    def _build_seq_tab(self, f):
        f.columnconfigure(0, weight=3)
        f.columnconfigure(1, weight=2)
        f.rowconfigure(1, weight=1)

        # --- presets + files ---
        bar = ttk.Frame(f)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(bar, text="Preset:").pack(side="left")
        cb = ttk.Combobox(bar, textvariable=self.v_preset, values=list(SEQUENCE_PRESETS), width=46, state="readonly")
        cb.pack(side="left", padx=4)
        cb.bind("<<ComboboxSelected>>", lambda e: self.apply_preset())
        ttk.Button(bar, text="Save shutters…", command=self.save_shutters_as).pack(side="right")
        ttk.Button(bar, text="Open shutters…", command=self.open_shutters).pack(side="right", padx=4)
        ttk.Label(bar, text="Oversampling:").pack(side="right", padx=(0, 2))
        ttk.Spinbox(bar, from_=1, to=100, textvariable=self.oversampling, width=4).pack(side="right", padx=(0, 12))

        # --- step table ---
        left = ttk.LabelFrame(f, text="Exposure steps (run in order; each step = one laser × N frames)", padding=8)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        cols = ("#", "Laser", "Channel", "Frames", "Power", "Frame range")
        tf, self.step_tree = make_tree(left, cols, [36, 90, 70, 90, 80, 120], height=10,
                                       anchors=["center"] * 6)
        tf.grid(row=0, column=0, sticky="nsew")
        self.step_tree.bind("<<TreeviewSelect>>", self._on_step_select)
        self.step_tree.bind("<Double-1>", self._on_step_double)
        for c, wl, col in LASERS:
            self.step_tree.tag_configure(f"ch{c}", foreground=col)

        ed = ttk.Frame(left)
        ed.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(ed, text="Laser").grid(row=0, column=0)
        ttk.Combobox(ed, textvariable=self.v_step_wl, values=[w for _, w, _ in LASERS], width=6,
                     state="readonly").grid(row=0, column=1, padx=(2, 10))
        ttk.Label(ed, text="Frames").grid(row=0, column=2)
        ttk.Spinbox(ed, from_=1, to=1000, textvariable=self.v_step_frames, width=6).grid(row=0, column=3, padx=(2, 10))
        ttk.Label(ed, text="Power").grid(row=0, column=4)
        ttk.Entry(ed, textvariable=self.v_step_power, width=6).grid(row=0, column=5, padx=(2, 10))
        ttk.Button(ed, text="+ Add", command=self.step_add).grid(row=0, column=6, padx=2)
        ttk.Button(ed, text="✎ Update selected", command=self.step_update).grid(row=0, column=7, padx=2)

        ed2 = ttk.Frame(left)
        ed2.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(ed2, text="↑ Up", command=lambda: self.step_move(-1)).pack(side="left")
        ttk.Button(ed2, text="↓ Down", command=lambda: self.step_move(1)).pack(side="left", padx=4)
        ttk.Button(ed2, text="✕ Delete", command=self.step_delete).pack(side="left")
        ttk.Button(ed2, text="+ 405 fiducial at start", command=self.step_add_fiducial).pack(side="left", padx=4)
        ttk.Button(ed2, text="Clear", command=self.step_clear).pack(side="left")
        ttk.Label(left, text="Tip: select a row, change the fields above and click Update selected, or double-click a cell to edit it",
                  style="Hint.TLabel").grid(row=3, column=0, sticky="w", pady=(6, 0))

        # --- Z scan ---
        right = ttk.LabelFrame(f, text="Z scan (hardware_z_scan / z_offsets)", padding=8)
        right.grid(row=1, column=1, sticky="nsew")
        right.columnconfigure(1, weight=1)
        right.rowconfigure(5, weight=1)
        ttk.Checkbutton(right, text="Auto-generate z_offsets from the sequence", variable=self.v_auto_z).grid(
            row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(right, text="z start (µm)").grid(row=1, column=0, sticky="w", pady=2)
        self.e_z_start = ttk.Entry(right, textvariable=self.v_z_start, width=8)
        self.e_z_start.grid(row=1, column=1, sticky="w")
        ttk.Label(right, text="z step (µm)").grid(row=2, column=0, sticky="w", pady=2)
        self.e_z_step = ttk.Entry(right, textvariable=self.v_z_step, width=8)
        self.e_z_step.grid(row=2, column=1, sticky="w")
        ttk.Label(right, text="Scan mode").grid(row=3, column=0, sticky="w", pady=2)
        self.cb_z_mode = ttk.Combobox(right, textvariable=self.v_z_mode, values=Z_MODES, state="readonly", width=22)
        self.cb_z_mode.grid(row=3, column=1, sticky="w")
        ttk.Label(right, text="Single-frame steps (e.g. 405 fiducial) stay at z start; multi-frame steps take a z-stack.",
                  style="Hint.TLabel", wraplength=300).grid(row=4, column=0, columnspan=3, sticky="w", pady=(4, 4))
        self.txt_z = tk.Text(right, width=36, height=6, wrap="word", font=("Courier", 10))
        self.txt_z.grid(row=5, column=0, columnspan=3, sticky="nsew")
        self.txt_z.bind("<KeyRelease>", lambda e: self.update_derived(from_z_text=True))
        self.lbl_zcount = ttk.Label(right, text="")
        self.lbl_zcount.grid(row=6, column=0, columnspan=3, sticky="w", pady=(4, 0))

        # --- preview ---
        pv = ttk.LabelFrame(f, text="Timing preview (blocks = laser per frame, line = z offset)", padding=6)
        pv.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.canvas = tk.Canvas(pv, height=150, background="white", highlightthickness=0)
        self.canvas.pack(fill="x", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw_preview())

        info = ttk.Frame(f)
        info.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        ttk.Label(info, textvariable=self.v_seq_info, font=("TkDefaultFont", 11, "bold")).pack(anchor="w")
        ttk.Label(info, textvariable=self.v_names, style="Hint.TLabel").pack(anchor="w")

    # ------------------------------------------------------------ tab 2 UI
    def _build_settings_tab(self, f):
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)

        src = ttk.Frame(f)
        src.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        ttk.Label(src, text="Template:").pack(side="left")
        self.lbl_source = ttk.Label(src, text="", style="Hint.TLabel")
        self.lbl_source.pack(side="left", padx=4)
        ttk.Button(src, text="Save settings…", command=self.save_settings_as).pack(side="right")
        ttk.Button(src, text="Reset to built-in template", command=self.reset_settings).pack(side="right", padx=4)
        ttk.Button(src, text="Open settings…", command=self.open_settings).pack(side="right")

        # naming
        g = ttk.LabelFrame(f, text="File naming", padding=8)
        g.grid(row=1, column=0, columnspan=2, sticky="ew", pady=4)
        g.columnconfigure(5, weight=1)
        ttk.Label(g, text="Prefix (Dsk / Epi …)").grid(row=0, column=0, sticky="w")
        ttk.Combobox(g, textvariable=self.v_prefix, values=["Dsk", "Epi"], width=8).grid(row=0, column=1, padx=4)
        ttk.Label(g, text="Sample tag").grid(row=0, column=2, sticky="w", padx=(12, 0))
        ttk.Entry(g, textvariable=self.v_tag, width=14).grid(row=0, column=3, padx=4)
        ttk.Label(g, text="(e.g. U2OS / cell / tissue; optional)", style="Hint.TLabel").grid(row=0, column=4, sticky="w")
        ttk.Label(g, text="Movie name (film/filename)").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.e_film = ttk.Entry(g, textvariable=self.v_film, width=56)
        self.e_film.grid(row=1, column=1, columnspan=4, sticky="w", padx=4, pady=(6, 0))
        ttk.Checkbutton(g, text="Auto", variable=self.v_auto_film,
                        command=self._on_auto_film).grid(row=1, column=5, sticky="w", pady=(6, 0))
        ttk.Checkbutton(g, text="Include sample tag in movie name", variable=self.v_tag_in_film).grid(
            row=2, column=1, columnspan=4, sticky="w", padx=4)
        self.lbl_linked = ttk.Label(g, text="", style="Hint.TLabel", justify="left")
        self.lbl_linked.grid(row=3, column=0, columnspan=6, sticky="w", pady=(6, 0))

        # camera
        cam = ttk.LabelFrame(f, text="Camera (camera1)", padding=8)
        cam.grid(row=2, column=0, sticky="nsew", padx=(0, 6), pady=4)
        ttk.Label(cam, text="Exposure time (s)").grid(row=0, column=0, sticky="w")
        ttk.Entry(cam, textvariable=self.v_exposure, width=12).grid(row=0, column=1, sticky="w", padx=4)
        ttk.Label(cam, textvariable=self.v_fps_hint, style="Hint.TLabel").grid(row=0, column=2, sticky="w")
        qe = ttk.Frame(cam)
        qe.grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 6))
        ttk.Label(qe, text="Common:", style="Hint.TLabel").pack(side="left")
        for val in ("0.05", "0.1", "0.2", "0.25", "0.5", "1.0"):
            ttk.Button(qe, text=val, width=5, command=lambda v=val: self.v_exposure.set(v)).pack(side="left", padx=1)
        ttk.Checkbutton(cam, text="flip_horizontal", variable=self.v_cam_fh).grid(row=2, column=0, sticky="w")
        ttk.Checkbutton(cam, text="flip_vertical", variable=self.v_cam_fv).grid(row=3, column=0, sticky="w")
        ttk.Checkbutton(cam, text="transpose", variable=self.v_cam_tr).grid(row=4, column=0, sticky="w")
        ttk.Label(cam, text="Other camera parameters (ROI, binning, trigger…) are in tab 3, All parameters",
                  style="Hint.TLabel", wraplength=380).grid(row=5, column=0, columnspan=3, sticky="w", pady=(6, 0))

        # laser power
        pw = ttk.LabelFrame(f, text="Default laser power (illumination/default_power, 0–1)", padding=8)
        pw.grid(row=2, column=1, sticky="nsew", pady=4)
        for i, (c, wl, col) in enumerate(LASERS):
            tk.Label(pw, text=f"■ {wl} nm (ch {c})", fg=col).grid(row=i, column=0, sticky="w", pady=1)
            ttk.Entry(pw, textvariable=self.v_power[i], width=8).grid(row=i, column=1, padx=4)
        bb = ttk.Frame(pw)
        bb.grid(row=N_CHANNELS, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Button(bb, text="All = 1", command=lambda: [v.set("1.000") for v in self.v_power]).pack(side="left")

        # objective / mosaic
        mo = ttk.LabelFrame(f, text="Objective / Mosaic", padding=8)
        mo.grid(row=3, column=0, columnspan=2, sticky="ew", pady=4)
        ttk.Label(mo, text="Active objective").grid(row=0, column=0, sticky="w")
        self.cb_objective = ttk.Combobox(mo, textvariable=self.v_objective, values=["obj1", "obj2"], width=6,
                                         state="readonly")
        self.cb_objective.grid(row=0, column=1, sticky="w", padx=4)
        for j, h in enumerate(("Name", "µm / pixel", "x offset", "y offset")):
            ttk.Label(mo, text=h, style="Hint.TLabel").grid(row=1, column=1 + j, sticky="w", padx=4)
        self.obj_rows = {}
        for r, key in enumerate(("obj1", "obj2", "obj3")):
            lbl = ttk.Label(mo, text=key)
            lbl.grid(row=2 + r, column=0, sticky="w")
            ents = []
            for j in range(4):
                e = ttk.Entry(mo, textvariable=self.v_obj[key][j], width=10)
                e.grid(row=2 + r, column=1 + j, padx=4, pady=1, sticky="w")
                ents.append(e)
            self.obj_rows[key] = (lbl, ents)
        ttk.Checkbutton(mo, text="flip_horizontal", variable=self.v_mos_fh).grid(row=1, column=6, sticky="w", padx=(24, 0))
        ttk.Checkbutton(mo, text="flip_vertical", variable=self.v_mos_fv).grid(row=2, column=6, sticky="w", padx=(24, 0))
        ttk.Checkbutton(mo, text="transpose", variable=self.v_mos_tr).grid(row=3, column=6, sticky="w", padx=(24, 0))

    # ------------------------------------------------------------ tab 3 UI
    def _build_adv_tab(self, f):
        f.rowconfigure(1, weight=1)
        f.columnconfigure(0, weight=1)
        ttk.Label(f, text="Every parameter in the settings file. Double-click a value to edit it; changes stay in sync with tab 2.",
                  style="Hint.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 6))
        frame = ttk.Frame(f)
        frame.grid(row=1, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.adv_tree = ttk.Treeview(frame, columns=("type", "value"), show="tree headings")
        self.adv_tree.heading("#0", text="Parameter")
        self.adv_tree.heading("type", text="Type")
        self.adv_tree.heading("value", text="Value")
        self.adv_tree.column("#0", width=300)
        self.adv_tree.column("type", width=80, anchor="center")
        self.adv_tree.column("value", width=600)
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.adv_tree.yview)
        self.adv_tree.configure(yscrollcommand=sb.set)
        self.adv_tree.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        self.adv_tree.bind("<Double-1>", self._on_adv_double)
        self.adv_items = {}

    # ------------------------------------------------------------ tab 4 UI
    def _build_kilroy_tab(self, f):
        f.rowconfigure(2, weight=1)
        f.columnconfigure(0, weight=1)
        bar = ttk.Frame(f)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(bar, text="Fluidics preset:").pack(side="left")
        self.v_kilroy_preset = tk.StringVar()
        cb = ttk.Combobox(bar, textvariable=self.v_kilroy_preset, values=list(KILROY_PRESETS), width=32,
                          state="readonly")
        cb.pack(side="left", padx=(4, 16))
        cb.bind("<<ComboboxSelected>>", lambda e: self.choose_kilroy_preset())
        ttk.Button(bar, text="Open Kilroy…", command=self.open_kilroy).pack(side="left")
        ttk.Button(bar, text="Save", command=self.save_kilroy).pack(side="left", padx=4)
        ttk.Button(bar, text="Save as…", command=self.save_kilroy_as).pack(side="left")
        ttk.Button(bar, text="Check for errors", command=self.check_kilroy).pack(side="left", padx=4)
        self.lbl_kilroy = ttk.Label(f, text="", style="Hint.TLabel")
        self.lbl_kilroy.grid(row=1, column=0, sticky="w", pady=(0, 6))

        knb = ttk.Notebook(f)
        knb.grid(row=2, column=0, sticky="nsew")
        tp = ttk.Frame(knb, padding=8)
        tv = ttk.Frame(knb, padding=8)
        tpu = ttk.Frame(knb, padding=8)
        tg = ttk.Frame(knb, padding=8)
        knb.add(tp, text="Protocols")
        knb.add(tg, text="Generate (hyb rounds / Prime)")
        knb.add(tv, text="Valve commands")
        knb.add(tpu, text="Pump commands")

        # ---- protocols ----
        tp.columnconfigure(1, weight=1)
        tp.rowconfigure(0, weight=1)
        lf = ttk.LabelFrame(tp, text="Protocol list", padding=6)
        lf.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        lf.rowconfigure(0, weight=1)
        self.proto_list = tk.Listbox(lf, width=28, exportselection=False, activestyle="none")
        self.proto_list.grid(row=0, column=0, sticky="nsew")
        psb = ttk.Scrollbar(lf, orient="vertical", command=self.proto_list.yview)
        self.proto_list.configure(yscrollcommand=psb.set)
        psb.grid(row=0, column=1, sticky="ns")
        self.proto_list.bind("<<ListboxSelect>>", lambda e: self.refresh_proto_steps())
        pb = ttk.Frame(lf)
        pb.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        for k, (txt, cmd) in enumerate((("New", self.proto_new), ("Duplicate", self.proto_dup),
                                        ("Rename", self.proto_rename), ("Delete", self.proto_delete),
                                        ("↑ Up", lambda: self.proto_move(-1)),
                                        ("↓ Down", lambda: self.proto_move(1)))):
            ttk.Button(pb, text=txt, command=cmd).grid(row=k // 3, column=k % 3, sticky="ew", padx=1, pady=1)
        for c in range(3):
            pb.columnconfigure(c, weight=1)

        rf = ttk.LabelFrame(tp, text="Steps (double-click a cell to edit)", padding=6)
        rf.grid(row=0, column=1, sticky="nsew")
        rf.rowconfigure(0, weight=1)
        rf.columnconfigure(0, weight=1)
        cols = ("#", "Type", "Duration (s)", "Command", "Start time")
        sf, self.pstep_tree = make_tree(rf, cols, [40, 70, 80, 220, 90], height=14,
                                        anchors=["center", "center", "e", "w", "e"])
        sf.grid(row=0, column=0, sticky="nsew")
        self.pstep_tree.tag_configure("valve", foreground="#1d4ed8")
        self.pstep_tree.tag_configure("pump", foreground="#15803d")
        self.pstep_tree.bind("<Double-1>", self._on_pstep_double)
        self.lbl_proto_total = ttk.Label(rf, text="", font=("TkDefaultFont", 11, "bold"))
        self.lbl_proto_total.grid(row=1, column=0, sticky="w", pady=(6, 0))
        sb2 = ttk.Frame(rf)
        sb2.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(sb2, text="+ Valve step", command=lambda: self.pstep_add("valve")).pack(side="left")
        ttk.Button(sb2, text="+ Pump step", command=lambda: self.pstep_add("pump")).pack(side="left", padx=2)
        ttk.Button(sb2, text="Duplicate", command=self.pstep_dup).pack(side="left")
        ttk.Button(sb2, text="✕ Delete", command=self.pstep_delete).pack(side="left", padx=2)
        ttk.Button(sb2, text="↑ Up", command=lambda: self.pstep_move(-1)).pack(side="left")
        ttk.Button(sb2, text="↓ Down", command=lambda: self.pstep_move(1)).pack(side="left", padx=2)

        # ---- valves ----
        tv.rowconfigure(0, weight=1)
        tv.columnconfigure(0, weight=1)
        self.valve_frame = ttk.Frame(tv)
        self.valve_frame.grid(row=0, column=0, sticky="nsew")
        self.valve_frame.rowconfigure(0, weight=1)
        self.valve_frame.columnconfigure(0, weight=1)
        self.valve_tree = None
        vb = ttk.Frame(tv)
        vb.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(vb, text="+ New", command=self.valve_new).pack(side="left")
        ttk.Button(vb, text="Duplicate", command=self.valve_dup).pack(side="left", padx=4)
        ttk.Button(vb, text="✕ Delete", command=self.valve_delete).pack(side="left")
        ttk.Button(vb, text="↑", width=3, command=lambda: self.valve_move(-1)).pack(side="left", padx=4)
        ttk.Button(vb, text="↓", width=3, command=lambda: self.valve_move(1)).pack(side="left")
        ttk.Button(vb, text="Number of valves…", command=self.valve_set_count).pack(side="left", padx=12)
        ttk.Label(tv, text="Double-click a cell to edit the name or port. Renaming also updates references in protocols.",
                  style="Hint.TLabel").grid(row=2, column=0, sticky="w", pady=(6, 0))

        # ---- pumps ----
        tpu.rowconfigure(0, weight=1)
        tpu.columnconfigure(0, weight=1)
        pf, self.pump_tree = make_tree(tpu, ("Name", "speed", "direction"), [240, 100, 120], height=8)
        pf.grid(row=0, column=0, sticky="nsew")
        self.pump_tree.bind("<Double-1>", self._on_pump_double)
        pbb = ttk.Frame(tpu)
        pbb.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(pbb, text="+ New", command=self.pump_new).pack(side="left")
        ttk.Button(pbb, text="✕ Delete", command=self.pump_delete).pack(side="left", padx=4)
        self.lbl_pump_comments = ttk.Label(pbb, text="", style="Hint.TLabel", justify="left")
        self.lbl_pump_comments.pack(side="right")

        # ---- generate ----
        self._build_kilroy_generate(tg)

    def _build_kilroy_generate(self, tg):
        V = tk.StringVar
        self.g_template = V(value="Hybridize 1")
        self.g_template_n = V(value="1")
        self.g_from = V(value="1")
        self.g_to = V(value="16")
        self.g_proto_fmt = V(value="Hybridize {n}")
        self.g_valve_fmt = V(value="Set Hyb {n}")

        h = ttk.LabelFrame(tg, text="Generate hybridization-round protocols from a template", padding=10)
        h.pack(fill="x")
        r = 0
        ttk.Label(h, text="Template protocol").grid(row=r, column=0, sticky="w")
        self.cb_g_template = ttk.Combobox(h, textvariable=self.g_template, width=28, state="readonly")
        self.cb_g_template.grid(row=r, column=1, sticky="w", padx=4)
        ttk.Label(h, text="Template round n =").grid(row=r, column=2, sticky="e", padx=(12, 0))
        ttk.Entry(h, textvariable=self.g_template_n, width=5).grid(row=r, column=3, sticky="w", padx=4)
        r += 1
        ttk.Label(h, text="Rounds").grid(row=r, column=0, sticky="w", pady=4)
        rr = ttk.Frame(h)
        rr.grid(row=r, column=1, sticky="w", padx=4)
        ttk.Spinbox(rr, from_=1, to=99, textvariable=self.g_from, width=5).pack(side="left")
        ttk.Label(rr, text=" to ").pack(side="left")
        ttk.Spinbox(rr, from_=1, to=99, textvariable=self.g_to, width=5).pack(side="left")
        r += 1
        ttk.Label(h, text="Protocol name format").grid(row=r, column=0, sticky="w")
        ttk.Entry(h, textvariable=self.g_proto_fmt, width=30).grid(row=r, column=1, sticky="w", padx=4)
        ttk.Label(h, text="Valve command format").grid(row=r, column=2, sticky="e", padx=(12, 0))
        ttk.Entry(h, textvariable=self.g_valve_fmt, width=20).grid(row=r, column=3, sticky="w", padx=4)
        r += 1
        ttk.Label(h, text="Copies the template protocol and replaces its valve command (format with n = template round) with each round's. "
                          "Protocols with the same name are overwritten. {n} stands for the round number.",
                  style="Hint.TLabel", wraplength=760).grid(row=r, column=0, columnspan=4, sticky="w", pady=(4, 6))
        r += 1
        ttk.Button(h, text="Generate hyb protocols", command=self.generate_hybs).grid(row=r, column=0, sticky="w")

        self.g_prime_n = V(value="16")
        self.g_prime_pump = V(value="Flow 2 ml/min")
        self.g_prime_pump_dur = V(value="15")
        self.g_prime_hyb_dur = V(value="20")
        self.g_prime_extra = V(value="Set Readout, Set TCEP, Set Image")
        self.g_prime_extra_dur = V(value="30")
        self.g_prime_last = V(value="Set Wash")
        self.g_prime_last_dur = V(value="60")
        p = ttk.LabelFrame(tg, text="Generate Prime protocol (flush all lines)", padding=10)
        p.pack(fill="x", pady=(10, 0))
        ttk.Label(p, text="Hyb bottles N").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(p, from_=1, to=99, textvariable=self.g_prime_n, width=5).grid(row=0, column=1, sticky="w", padx=4)
        ttk.Label(p, text="Pump command").grid(row=0, column=2, sticky="e", padx=(12, 0))
        self.cb_prime_pump = ttk.Combobox(p, textvariable=self.g_prime_pump, width=18)
        self.cb_prime_pump.grid(row=0, column=3, sticky="w", padx=4)
        ttk.Label(p, text="Duration").grid(row=0, column=4, sticky="e")
        ttk.Entry(p, textvariable=self.g_prime_pump_dur, width=5).grid(row=0, column=5, sticky="w", padx=4)
        ttk.Label(p, text="Duration per Hyb valve (s)").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(p, textvariable=self.g_prime_hyb_dur, width=5).grid(row=1, column=1, sticky="w", padx=4)
        ttk.Label(p, text="Other valves").grid(row=2, column=0, sticky="w")
        ttk.Entry(p, textvariable=self.g_prime_extra, width=36).grid(row=2, column=1, columnspan=3, sticky="w", padx=4)
        ttk.Label(p, text="Duration").grid(row=2, column=4, sticky="e")
        ttk.Entry(p, textvariable=self.g_prime_extra_dur, width=5).grid(row=2, column=5, sticky="w", padx=4)
        ttk.Label(p, text="Last valve").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(p, textvariable=self.g_prime_last, width=18).grid(row=3, column=1, columnspan=3, sticky="w", padx=4)
        ttk.Label(p, text="Duration").grid(row=3, column=4, sticky="e")
        ttk.Entry(p, textvariable=self.g_prime_last_dur, width=5).grid(row=3, column=5, sticky="w", padx=4)
        ttk.Label(p, text="Creates a protocol named \"Prime N + 4\": pump on → Set Hyb 1…N → other valves → last valve → Stop Flow",
                  style="Hint.TLabel").grid(row=4, column=0, columnspan=6, sticky="w", pady=(4, 6))
        ttk.Button(p, text="Generate Prime protocol", command=self.generate_prime).grid(row=5, column=0, sticky="w")

    # ------------------------------------------------------------ tab 5 UI
    def _build_dave_tab(self, f):
        V = tk.StringVar
        f.rowconfigure(2, weight=1)
        f.columnconfigure(0, weight=1)
        bar = ttk.Frame(f)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(bar, text="Recipe preset:").pack(side="left")
        self.v_dave_preset = V()
        cb = ttk.Combobox(bar, textvariable=self.v_dave_preset, values=list(DAVE_PRESETS), width=40, state="readonly")
        cb.pack(side="left", padx=(4, 16))
        cb.bind("<<ComboboxSelected>>", lambda e: self.choose_dave_preset())
        ttk.Button(bar, text="Open Dave…", command=self.open_dave).pack(side="left")
        ttk.Button(bar, text="Save", command=self.save_dave).pack(side="left", padx=4)
        ttk.Button(bar, text="Save as…", command=self.save_dave_as).pack(side="left")
        ttk.Button(bar, text="Check for errors", command=self.check_dave).pack(side="left", padx=4)
        self.lbl_dave = ttk.Label(f, text="", style="Hint.TLabel")
        self.lbl_dave.grid(row=1, column=0, sticky="w", pady=(0, 6))

        dnb = ttk.Notebook(f)
        dnb.grid(row=2, column=0, sticky="nsew")
        ed = ttk.Frame(dnb, padding=8)
        pv = ttk.Frame(dnb, padding=8)
        dnb.add(ed, text="Recipe")
        dnb.add(pv, text="XML preview")
        ed.columnconfigure(0, weight=1)
        ed.rowconfigure(1, weight=1)

        # global
        g = ttk.LabelFrame(ed, text="Global", padding=8)
        g.grid(row=0, column=0, sticky="ew")
        g.columnconfigure(3, weight=1)
        self.dv_wakeup_ms = V()
        self.dv_wakeup_file = V()
        self.dv_wakeup_params = V()
        self.dv_wakeup_length = V()
        self.dv_positions = V()
        ttk.Label(g, text="Wakeup (ms)").grid(row=0, column=0, sticky="w")
        ttk.Entry(g, textvariable=self.dv_wakeup_ms, width=8).grid(row=0, column=1, sticky="w", padx=4)
        ttk.Label(g, text="Wakeup positions file").grid(row=0, column=2, sticky="e", padx=(12, 0))
        ttk.Entry(g, textvariable=self.dv_wakeup_file, width=40).grid(row=0, column=3, sticky="ew", padx=4)
        ttk.Label(g, text="Wakeup settings / frames").grid(row=1, column=0, sticky="w", pady=(4, 0))
        wf = ttk.Frame(g)
        wf.grid(row=1, column=1, sticky="w", padx=4, pady=(4, 0))
        ttk.Entry(wf, textvariable=self.dv_wakeup_params, width=9).pack(side="left")
        ttk.Entry(wf, textvariable=self.dv_wakeup_length, width=4).pack(side="left", padx=(4, 0))
        ttk.Label(g, text="Imaging positions file").grid(row=1, column=2, sticky="e", padx=(12, 0), pady=(4, 0))
        ttk.Entry(g, textvariable=self.dv_positions, width=40).grid(row=1, column=3, sticky="ew", padx=4, pady=(4, 0))
        ttk.Label(g, text="Positions files are paths on the microscope PC (e.g. D:\\…\\positions.txt); you can leave them empty and set them in Dave before running.",
                  style="Hint.TLabel").grid(row=2, column=0, columnspan=4, sticky="w", pady=(4, 0))
        for v in (self.dv_wakeup_ms, self.dv_wakeup_file, self.dv_wakeup_params, self.dv_wakeup_length,
                  self.dv_positions):
            v.trace_add("write", lambda *a: self._dave_globals_changed())

        # stage table
        sf = ttk.LabelFrame(ed, text="Stages (run in order; each hyb round: Kilroy protocols → wakeup → imaging)", padding=8)
        sf.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        sf.columnconfigure(0, weight=1)
        sf.rowconfigure(0, weight=1)
        cols = ("#", "Type", "Rounds / fluidics", "Wakeup focus", "settings", "Movie name", "Frames", "Focus")
        tf, self.dave_tree = make_tree(sf, cols, [30, 70, 190, 70, 230, 180, 45, 45], height=5,
                                       anchors=["center", "center", "w", "center", "w", "w", "center", "center"])
        tf.grid(row=0, column=0, sticky="nsew")
        self.dave_tree.bind("<<TreeviewSelect>>", self._on_dave_select)

        self.dv_kind = V(value=DAVE_KINDS["hyb"])
        self.dv_from = V(value="1")
        self.dv_to = V(value="14")
        self.dv_fmt = V(value="Cleave, Hybridize {n}")
        self.dv_params = V()
        self.dv_movie = V()
        self.dv_length = V(value="1")
        self.dv_checks = V(value="100")
        self.dv_wake = tk.BooleanVar(value=True)
        self.dv_wake_checks = V(value="50")
        e = ttk.Frame(sf)
        e.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(e, text="Type").grid(row=0, column=0, sticky="w")
        ttk.Combobox(e, textvariable=self.dv_kind, values=list(DAVE_KINDS.values()), width=9,
                     state="readonly").grid(row=0, column=1, sticky="w", padx=4)
        ttk.Label(e, text="Rounds").grid(row=0, column=2, sticky="e", padx=(10, 0))
        rr = ttk.Frame(e)
        rr.grid(row=0, column=3, sticky="w", padx=4)
        ttk.Spinbox(rr, from_=1, to=99, textvariable=self.dv_from, width=4).pack(side="left")
        ttk.Label(rr, text=" to ").pack(side="left")
        ttk.Spinbox(rr, from_=1, to=99, textvariable=self.dv_to, width=4).pack(side="left")
        ttk.Label(e, text="Protocols per round").grid(row=0, column=4, sticky="e", padx=(10, 0))
        ttk.Entry(e, textvariable=self.dv_fmt, width=24).grid(row=0, column=5, columnspan=3, sticky="w", padx=4)
        ttk.Label(e, text="settings").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.cb_dv_params = ttk.Combobox(e, textvariable=self.dv_params, width=40)
        self.cb_dv_params.grid(row=1, column=1, columnspan=3, sticky="w", padx=4, pady=(6, 0))
        self.cb_dv_params.bind("<<ComboboxSelected>>", lambda ev: self._dave_params_chosen())
        ttk.Label(e, text="Movie name").grid(row=1, column=4, sticky="e", padx=(10, 0), pady=(6, 0))
        ttk.Entry(e, textvariable=self.dv_movie, width=24).grid(row=1, column=5, columnspan=3, sticky="w", padx=4,
                                                               pady=(6, 0))
        ttk.Label(e, text="Frames").grid(row=2, column=0, sticky="w", pady=(6, 0))
        nf = ttk.Frame(e)
        nf.grid(row=2, column=1, columnspan=3, sticky="w", padx=4, pady=(6, 0))
        ttk.Entry(nf, textvariable=self.dv_length, width=5).pack(side="left")
        ttk.Label(nf, text="  Focus checks").pack(side="left")
        ttk.Entry(nf, textvariable=self.dv_checks, width=5).pack(side="left", padx=4)
        ttk.Checkbutton(nf, text="Wakeup first, focus checks", variable=self.dv_wake).pack(side="left", padx=(12, 0))
        ttk.Entry(nf, textvariable=self.dv_wake_checks, width=5).pack(side="left", padx=4)
        ttk.Label(e, text="Choosing settings fills in movie name and frames. Protocols: comma-separated, {n} = round number.",
                  style="Hint.TLabel").grid(row=3, column=0, columnspan=8, sticky="w", pady=(6, 0))
        bb = ttk.Frame(sf)
        bb.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(bb, text="+ Add stage", command=self.dave_add).pack(side="left")
        ttk.Button(bb, text="✎ Update selected", command=self.dave_update).pack(side="left", padx=4)
        ttk.Button(bb, text="✕ Delete", command=self.dave_delete).pack(side="left")
        ttk.Button(bb, text="↑ Up", command=lambda: self.dave_move(-1)).pack(side="left", padx=4)
        ttk.Button(bb, text="↓ Down", command=lambda: self.dave_move(1)).pack(side="left")
        ttk.Button(bb, text="Use current settings (tab 2)", command=self.dave_use_current).pack(side="left", padx=12)
        self.lbl_dave_summary = ttk.Label(ed, text="", font=("TkDefaultFont", 11, "bold"))
        self.lbl_dave_summary.grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.lbl_dave_problems = ttk.Label(ed, text="", style="Bad.TLabel", justify="left", wraplength=1000)
        self.lbl_dave_problems.grid(row=3, column=0, sticky="w")

        pv.rowconfigure(0, weight=1)
        pv.columnconfigure(0, weight=1)
        self.txt_dave = tk.Text(pv, wrap="none", font=("Courier", 10), width=60)
        self.txt_dave.grid(row=0, column=0, sticky="nsew")
        ys = ttk.Scrollbar(pv, orient="vertical", command=self.txt_dave.yview)
        ys.grid(row=0, column=1, sticky="ns")
        xs = ttk.Scrollbar(pv, orient="horizontal", command=self.txt_dave.xview)
        xs.grid(row=1, column=0, sticky="ew")
        self.txt_dave.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)

    # ================================================================ tab 5 logic
    def refresh_dave(self, select=None):
        if not hasattr(self, "dave_tree"):
            return
        d = self.dave
        self._dave_loading = True
        self.dv_wakeup_ms.set(d.wakeup_ms)
        self.dv_wakeup_file.set(d.wakeup_file)
        self.dv_wakeup_params.set(d.wakeup_params)
        self.dv_wakeup_length.set(d.wakeup_length)
        self.dv_positions.set(d.positions_file)
        self._dave_loading = False
        t = self.dave_tree
        if select is None:
            select = tree_index(t)
        t.delete(*t.get_children())
        for i, st in enumerate(d.stages):
            if st["kind"] == "hyb":
                pat = detect_round_pattern(st["values"])
                rounds = f"{pat[1]}–{pat[2]}: {pat[0]}" if pat else f"Custom, {len(st['values'])} rounds"
            else:
                rounds = "—"
            wake = f"✓ {st['wake_checks']}" if st["wake"] else "—"
            t.insert("", "end", values=(i + 1, DAVE_KINDS[st["kind"]], rounds, wake, st["params"], st["movie"],
                                        st["length"], st["checks"]))
        tree_reselect(t, select)
        self.cb_dv_params.configure(values=self.known_settings_names())
        name = os.path.basename(self.dave_path) if self.dave_path else "(unsaved)"
        self.lbl_dave.configure(text=name)
        self.refresh_dave_summary()

    def _dave_globals_changed(self):
        if getattr(self, "_dave_loading", False):
            return
        d = self.dave
        d.wakeup_ms = self.dv_wakeup_ms.get().strip()
        d.wakeup_file = self.dv_wakeup_file.get().strip()
        d.wakeup_params = self.dv_wakeup_params.get().strip()
        d.wakeup_length = self.dv_wakeup_length.get().strip()
        d.positions_file = self.dv_positions.get().strip()
        self.refresh_dave_summary()

    def protocol_seconds_by_name(self):
        k = self.kilroy
        return {p[0]: k.protocol_seconds(p[1]) for p in k.protocols} if k else {}

    def refresh_dave_summary(self):
        d = self.dave
        n_img = d.n_movies()
        secs = self.protocol_seconds_by_name()
        fl, unknown = 0.0, False
        for st in d.stages:
            if st["kind"] == "hyb":
                for v in st["values"]:
                    for p in v:
                        if p in secs:
                            fl += secs[p]
                        else:
                            unknown = True
        n_rounds = sum(len(st["values"]) for st in d.stages if st["kind"] == "hyb")
        txt = f"{len(d.stages)} stages, {n_img} imaging passes (each over all positions), {n_rounds} hyb rounds"
        if n_rounds:
            txt += f"; fluidics about {fmt_duration(fl)} in total" + (" (some protocols are not in Kilroy)" if unknown else "")
        self.lbl_dave_summary.configure(text=txt)
        probs = d.validate(self.kilroy, self.settings_frames)
        self.lbl_dave_problems.configure(text="\n".join("⚠ " + p for p in probs))
        self.txt_dave.configure(state="normal")
        self.txt_dave.delete("1.0", "end")
        self.txt_dave.insert("1.0", d.to_string())
        self.txt_dave.configure(state="disabled")

    def known_settings_names(self):
        names = [p["name"] for p in SETTINGS_PRESETS]
        cur = os.path.splitext(self.settings_filename())[0]
        if cur not in names:
            names.insert(0, cur)
        for folder in settings_search_dirs(self.last_dir):
            try:
                for fn in sorted(os.listdir(folder)):
                    stem = os.path.splitext(fn)[0]
                    if fn.endswith(".xml") and stem not in names and self._file_frames(os.path.join(folder, fn)):
                        names.append(stem)
            except OSError:
                pass
        return names

    def _file_frames(self, path):
        """film/frames from a settings file (cached). Returns None if it is not a settings file."""
        try:
            key = (path, os.path.getmtime(path))
        except OSError:
            return None
        if key not in self._film_frames_cache:
            val = None
            try:
                root = ET.parse(path).getroot()
                if root.tag == "settings":
                    val = int(sget(root, "film/frames", "0"))
            except (ET.ParseError, ValueError, OSError):
                pass
            self._film_frames_cache[key] = val
        return self._film_frames_cache[key]

    def settings_frames(self, name):
        """Frames for a settings name: current tab-2 settings > built-in presets > files in the folder. None if unknown."""
        if name == os.path.splitext(self.settings_filename())[0]:
            return total_frames(self.steps)
        p = find_settings_preset(name)
        if p:
            return sum(n for _, n in p["steps"])
        for folder in settings_search_dirs(self.last_dir):
            f = self._file_frames(os.path.join(folder, name + ".xml"))
            if f:
                return f
        return None

    def _dave_params_chosen(self):
        name = self.dv_params.get().strip()
        self.dv_movie.set(movie_name_for(name))
        f = self.settings_frames(name)
        if f:
            self.dv_length.set(str(f))

    def _on_dave_select(self, _e=None):
        i = tree_index(self.dave_tree)
        if i is None:
            return
        st = self.dave.stages[i]
        self.dv_kind.set(DAVE_KINDS[st["kind"]])
        self.dv_params.set(st["params"])
        self.dv_movie.set(st["movie"])
        self.dv_length.set(st["length"])
        self.dv_checks.set(st["checks"])
        self.dv_wake.set(st["wake"])
        self.dv_wake_checks.set(st["wake_checks"])
        if st["kind"] == "hyb":
            pat = detect_round_pattern(st["values"])
            if pat:
                self.dv_fmt.set(pat[0])
                self.dv_from.set(str(pat[1]))
                self.dv_to.set(str(pat[2]))
            else:
                self.dv_fmt.set("")

    def _read_dave_editor(self, old=None):
        kind = next(k for k, v in DAVE_KINDS.items() if v == self.dv_kind.get())
        params = self.dv_params.get().strip()
        if not params:
            messagebox.showerror("Invalid input", "Choose or type a settings name")
            return None
        try:
            length = int(self.dv_length.get())
            if length < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid input", "Frames must be an integer ≥ 1")
            return None
        st = {"kind": kind, "params": params, "movie": self.dv_movie.get().strip() or movie_name_for(params),
              "length": str(length), "checks": self.dv_checks.get().strip(),
              "overwrite": old.get("overwrite", "False") if old else "False",
              "wake": self.dv_wake.get(), "wake_checks": self.dv_wake_checks.get().strip()}
        if kind == "hyb":
            fmt = self.dv_fmt.get().strip()
            if not fmt and old and old.get("values"):
                st["values"] = old["values"]  # custom rounds: keep as they are
            else:
                try:
                    a, b = int(self.dv_from.get()), int(self.dv_to.get())
                    if a > b:
                        a, b = b, a
                    st["values"] = make_round_values(fmt, a, b)
                except (ValueError, KeyError, IndexError):
                    messagebox.showerror("Invalid input", "Check the round numbers and protocol format (use {n} for the round number)")
                    return None
                if not st["values"] or not st["values"][0]:
                    messagebox.showerror("Invalid input", "Protocols per round cannot be empty")
                    return None
        return st

    def dave_add(self):
        st = self._read_dave_editor()
        if st:
            i = tree_index(self.dave_tree)
            pos = len(self.dave.stages) if i is None else i + 1
            self.dave.stages.insert(pos, st)
            self.refresh_dave(pos)

    def dave_update(self):
        i = tree_index(self.dave_tree)
        if i is None:
            messagebox.showinfo("Note", "Select a row in the table first")
            return
        st = self._read_dave_editor(self.dave.stages[i])
        if st:
            self.dave.stages[i] = st
            self.refresh_dave(i)

    def dave_delete(self):
        i = tree_index(self.dave_tree)
        if i is not None:
            del self.dave.stages[i]
            self.refresh_dave(i)

    def dave_move(self, d):
        i = tree_index(self.dave_tree)
        S = self.dave.stages
        if i is None or not (0 <= i + d < len(S)):
            return
        S[i], S[i + d] = S[i + d], S[i]
        self.refresh_dave(i + d)

    def dave_use_current(self):
        self.push_quick()
        self.dv_params.set(os.path.splitext(self.settings_filename())[0])
        self.dv_movie.set(self.v_film.get().strip())
        self.dv_length.set(str(total_frames(self.steps)))
        self.status("Filled in the current settings; click Add stage or Update selected to apply it")

    def choose_dave_preset(self):
        name = self.v_dave_preset.get()
        p = DAVE_PRESETS.get(name)
        if not p or not messagebox.askyesno("Load recipe preset", f"Replace the current Dave recipe with preset \"{name}\"?"):
            return
        self.push_quick()
        ctx = {"settings": os.path.splitext(self.settings_filename())[0], "movie": self.v_film.get().strip(),
               "frames": total_frames(self.steps)}
        self.dave = p["make"](ctx)
        self.dave_path = None
        self.status(f"Loaded recipe preset: {name}")
        kp = p.get("kilroy")
        if kp and kp in KILROY_PRESETS and messagebox.askyesno(
                "Matching fluidics", f"This recipe goes with the fluidics preset \"{kp}\".\n\nAlso switch the Kilroy protocols on tab 4 to it?"):
            self.apply_kilroy_preset(kp)
        self.refresh_dave(0)

    def open_dave(self):
        path = filedialog.askopenfilename(initialdir=dialog_dir(self.dave_path, LAB_DAVE_DIR, self.last_dir),
                                          title="Open Dave recipe",
                                          filetypes=[("XML", "*.xml"), ("All", "*.*")])
        if path:
            self.load_dave(path)

    def load_dave(self, path):
        try:
            d = DaveRecipe.load(path)
        except Exception as ex:
            messagebox.showerror("Could not read file", f"{os.path.basename(path)}\n\n{ex}\n\n"
                                         f"This tool supports Dave recipes made of imaging stages and hyb loops only.")
            return False
        self.dave = d
        self.dave_path = path
        self.v_dave_preset.set("")
        self.last_dir = os.path.dirname(path)
        self.refresh_dave(0)
        self.status(f"Loaded Dave: {path}")
        return True

    def check_dave(self):
        probs = self.dave.validate(self.kilroy, self.settings_frames)
        if probs:
            messagebox.showwarning("Check results", "\n".join("• " + p for p in probs))
        else:
            messagebox.showinfo("Check results", "No problems found ✓")

    def save_dave(self):
        if not self.dave_path:
            return self.save_dave_as()
        self._write_dave(self.dave_path)

    def save_dave_as(self):
        init = os.path.basename(self.dave_path) if self.dave_path else "dave_recipe.xml"
        path = filedialog.asksaveasfilename(initialdir=dialog_dir(self.dave_path, LAB_DAVE_DIR, self.last_dir),
                                            initialfile=init,
                                            defaultextension=".xml", filetypes=[("XML", "*.xml")])
        if path:
            self._write_dave(path)

    def _write_dave(self, path):
        if not self._confirm_problems(self.dave.validate(self.kilroy, self.settings_frames)):
            return
        write_text_crlf(path, self.dave.to_string())
        self.dave_path = path
        self.last_dir = os.path.dirname(path)
        self.refresh_dave()
        self.status(f"Saved Dave: {path}")

    # ================================================================ tab sync
    def _on_tab_changed(self, _e=None):
        new = self.nb.index(self.nb.select())
        old = self._current_tab
        if old == 1:
            self.push_quick()
        if old == 2:
            self.pull_quick()
            self.update_derived()
        if new == 2:
            self.push_quick()
            self.refresh_adv()
        if new == 4:
            self.refresh_dave()
        self._current_tab = new

    # ================================================================ tab 1 logic
    def apply_preset(self):
        name = self.v_preset.get()
        if name in SEQUENCE_PRESETS:
            self.steps = [new_step(w, n) for w, n in SEQUENCE_PRESETS[name]]
            self.refresh_steps()
            self.status(f"Applied preset: {name}")

    def refresh_steps(self, select=None):
        t = self.step_tree
        t.delete(*t.get_children())
        start = 0
        for i, s in enumerate(self.steps):
            wl = CH2WL.get(s["channel"], "?")
            t.insert("", "end", values=(i + 1, f"{wl} nm", s["channel"], s["frames"], fmt_num(s["power"]),
                                        f"{start} – {start + s['frames'] - 1}"),
                     tags=(f"ch{s['channel']}",))
            start += s["frames"]
        tree_reselect(t, select)
        self.update_derived()

    def _read_step_editor(self):
        try:
            frames = int(self.v_step_frames.get())
            power = float(self.v_step_power.get())
            if frames < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid input", "Frames must be an integer ≥ 1 and power must be a number")
            return None
        return new_step(self.v_step_wl.get(), frames, power)

    def _on_step_select(self, _e=None):
        i = tree_index(self.step_tree)
        if i is None:
            return
        s = self.steps[i]
        self.v_step_wl.set(CH2WL.get(s["channel"], LASERS[0][1]))
        self.v_step_frames.set(str(s["frames"]))
        self.v_step_power.set(fmt_num(s["power"]))

    def _on_step_double(self, e):
        item = self.step_tree.identify_row(e.y)
        col_id = self.step_tree.identify_column(e.x)
        if not item or not col_id:
            return
        col = self.step_tree["columns"][int(col_id[1:]) - 1]
        i = self.step_tree.index(item)

        def done_laser(v):
            wl = v.replace("nm", "").strip()
            if wl in WL2CH:
                self.steps[i]["channel"] = WL2CH[wl]
                self.refresh_steps(i)

        def done_num(key, conv):
            def f(v):
                try:
                    val = conv(v)
                    if key == "frames" and val < 1:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Invalid input", f"Invalid value: {v}")
                    return
                self.steps[i][key] = val
                self.refresh_steps(i)
            return f

        if col == "Laser" or col == "Channel":
            inline_edit(self.step_tree, item, "Laser", done_laser, values=[f"{w} nm" for _, w, _ in LASERS])
        elif col == "Frames":
            inline_edit(self.step_tree, item, col, done_num("frames", int))
        elif col == "Power":
            inline_edit(self.step_tree, item, col, done_num("power", float))

    def step_add(self):
        s = self._read_step_editor()
        if s:
            self.steps.append(s)
            self.refresh_steps(len(self.steps) - 1)

    def step_update(self):
        i = tree_index(self.step_tree)
        if i is None:
            messagebox.showinfo("Note", "Select a row in the table first")
            return
        s = self._read_step_editor()
        if s:
            s["color"] = self.steps[i].get("color", s["color"])
            self.steps[i] = s
            self.refresh_steps(i)

    def step_move(self, d):
        i = tree_index(self.step_tree)
        if i is None or not (0 <= i + d < len(self.steps)):
            return
        self.steps[i], self.steps[i + d] = self.steps[i + d], self.steps[i]
        self.refresh_steps(i + d)

    def step_delete(self):
        i = tree_index(self.step_tree)
        if i is None:
            return
        del self.steps[i]
        self.refresh_steps(i)

    def step_add_fiducial(self):
        self.steps.insert(0, new_step("405", 1))
        self.refresh_steps(0)

    def step_clear(self):
        if self.steps and messagebox.askyesno("Clear", "Remove all steps?"):
            self.steps = []
            self.refresh_steps()

    def _on_auto_z(self):
        st = "normal" if self.v_auto_z.get() else "disabled"
        for w in (self.e_z_start, self.e_z_step):
            w.configure(state=st)
        self.cb_z_mode.configure(state="readonly" if self.v_auto_z.get() else "disabled")
        self.update_derived()

    def current_z_values(self):
        """Current z_offsets as a list of floats, or None if they cannot be parsed."""
        try:
            return parse_float_list(self.txt_z.get("1.0", "end"))
        except ValueError:
            return None

    def get_z_text(self):
        return self.txt_z.get("1.0", "end").strip("\n")

    def set_z_text(self, text):
        self.txt_z.configure(state="normal")
        self.txt_z.delete("1.0", "end")
        self.txt_z.insert("1.0", text)
        if self.v_auto_z.get():
            self.txt_z.configure(state="disabled", background="#f3f4f6")
        else:
            self.txt_z.configure(background="white")

    def auto_film_name(self):
        name = "-".join(x for x in (self.v_prefix.get().strip(), sequence_tokens(self.steps)) if x)
        if self.v_tag_in_film.get() and self.v_tag.get().strip():
            name += "-" + self.v_tag.get().strip()
        return name

    def settings_filename(self):
        parts = [self.v_prefix.get().strip(), sequence_tokens(self.steps), self.v_tag.get().strip()]
        return "-".join(p for p in parts if p) + ".xml"

    def _on_auto_film(self):
        self.e_film.configure(state="disabled" if self.v_auto_film.get() else "normal")
        self.update_derived()

    def update_derived(self, from_z_text=False):
        if not hasattr(self, "txt_z"):
            return
        nfr = total_frames(self.steps)
        if self.v_auto_z.get() and not from_z_text:
            try:
                z0 = float(self.v_z_start.get())
                dz = float(self.v_z_step.get())
                self.set_z_text(z_groups_to_string(make_z_groups(self.steps, z0, dz, self.v_z_mode.get())))
            except ValueError:
                pass
        elif not from_z_text:
            self.set_z_text(self.get_z_text())
        zv = self.current_z_values()
        if zv is None:
            self.lbl_zcount.configure(text="Invalid z_offsets (expected comma-separated numbers)", style="Bad.TLabel")
        elif len(zv) == nfr:
            self.lbl_zcount.configure(text=f"✓ {len(zv)} z values = {nfr} total frames", style="Good.TLabel")
        else:
            self.lbl_zcount.configure(text=f"✗ {len(zv)} z values ≠ {nfr} total frames", style="Bad.TLabel")

        if self.v_auto_film.get():
            self.v_film.set(self.auto_film_name())
        exp = self._exposure()
        tstr = f", about {nfr * exp:.1f} s per field of view" if exp else ""
        self.v_seq_info.set(f"{len(self.steps)} steps, {nfr} frames{tstr}")
        self.v_names.set(f"Shutters file: {shutters_filename(self.steps)}     Settings file: {self.settings_filename()}")
        if hasattr(self, "lbl_linked"):
            self.lbl_linked.configure(
                text=f"Filled in automatically from tab 1 (Sequence):\n"
                     f"  illumination/shutters = {shutters_filename(self.steps)}\n"
                     f"  film/frames = {nfr}      focuslock/hardware_z_scan/z_offsets = {len(zv or [])} values\n"
                     f"  Saved as: {self.settings_filename()}")
        self.draw_preview()

    def _exposure(self):
        try:
            return float(self.v_exposure.get())
        except ValueError:
            return None

    def _update_fps_hint(self):
        e = self._exposure()
        self.v_fps_hint.set(f"≈ {1 / e:.2f} fps" if e else "")
        if hasattr(self, "v_seq_info"):
            self.update_derived()

    def draw_preview(self):
        c = self.canvas
        c.delete("all")
        W = max(c.winfo_width(), 200)
        H = int(c["height"])
        n = total_frames(self.steps)
        if n == 0:
            c.create_text(W / 2, H / 2, text="(no steps)", fill="#999")
            return
        L, R = 46, 12
        bar_y0, bar_y1 = H - 34, H - 14
        z_y0, z_y1 = 10, bar_y0 - 12
        fw = (W - L - R) / n
        x = L
        for s in self.steps:
            col = CH2COLOR.get(s["channel"], "#888")
            for _ in range(s["frames"]):
                c.create_rectangle(x, bar_y0, x + fw, bar_y1, fill=col, outline="white" if fw > 4 else col)
                x += fw
        x = L
        for s in self.steps:
            w = fw * s["frames"]
            label = f"{CH2WL.get(s['channel'])}×{s['frames']}"
            if w > 34:
                c.create_text(x + w / 2, bar_y1 + 8, text=label, font=("TkDefaultFont", 8), fill="#444")
            x += w
        zv = self.current_z_values() or []
        if zv:
            zmin, zmax = min(zv), max(zv)
            span = (zmax - zmin) or 1.0
            c.create_text(L - 6, z_y0, text=fmt_num(zmax, 2), anchor="e", font=("TkDefaultFont", 8), fill="#666")
            c.create_text(L - 6, z_y1, text=fmt_num(zmin, 2), anchor="e", font=("TkDefaultFont", 8), fill="#666")
            c.create_text(4, (z_y0 + z_y1) / 2, text="z\nµm", anchor="w", font=("TkDefaultFont", 8), fill="#666")
            c.create_line(L, z_y0, W - R, z_y0, fill="#eee")
            c.create_line(L, z_y1, W - R, z_y1, fill="#eee")
            pts = []
            for i, z in enumerate(zv[:n]):
                px = L + (i + 0.5) * fw
                py = z_y1 - (z - zmin) / span * (z_y1 - z_y0)
                pts += [px, py]
            if len(pts) >= 4:
                c.create_line(*pts, fill="#334155", width=1.5)
            if fw >= 5:
                for i in range(0, len(pts), 2):
                    c.create_oval(pts[i] - 2, pts[i + 1] - 2, pts[i] + 2, pts[i + 1] + 2, fill="#334155", outline="")

    # ---- shutters file I/O
    def open_shutters(self):
        path = filedialog.askopenfilename(initialdir=self.last_dir, title="Open shutters file",
                                          filetypes=[("XML", "*.xml"), ("All", "*.*")])
        if path:
            self.load_shutters(path)

    def load_shutters(self, path, quiet=False):
        try:
            overs, steps, warns = parse_shutters(path)
        except Exception as ex:
            messagebox.showerror("Could not read file", f"{os.path.basename(path)}\n\n{ex}")
            return False
        self.last_dir = os.path.dirname(path)
        self.steps = steps
        self.oversampling.set(overs)
        self.refresh_steps()
        self.status(f"Loaded shutters: {path}")
        if warns and not quiet:
            messagebox.showwarning("Warning", "\n".join(warns))
        return True

    def save_shutters_as(self):
        if not self._check_sequence():
            return
        path = filedialog.asksaveasfilename(initialdir=self.last_dir, initialfile=shutters_filename(self.steps),
                                            defaultextension=".xml", filetypes=[("XML", "*.xml")])
        if path:
            write_text_crlf(path, shutters_to_string(self.steps, self.oversampling.get()))
            self.last_dir = os.path.dirname(path)
            self.status(f"Saved shutters: {path}")

    def _check_sequence(self):
        if not self.steps:
            messagebox.showerror("Error", "The sequence is empty")
            return False
        return True

    # ================================================================ tab 2 logic
    def pull_quick(self):
        r = self.settings_root
        self.v_exposure.set(sget(r, "camera1/exposure_time"))
        b = lambda p: sget(r, p, "False").strip() == "True"
        self.v_cam_fh.set(b("camera1/flip_horizontal"))
        self.v_cam_fv.set(b("camera1/flip_vertical"))
        self.v_cam_tr.set(b("camera1/transpose"))
        self.v_mos_fh.set(b("mosaic/flip_horizontal"))
        self.v_mos_fv.set(b("mosaic/flip_vertical"))
        self.v_mos_tr.set(b("mosaic/transpose"))
        objs = []
        for key in ("obj1", "obj2", "obj3"):
            txt = sget(r, f"mosaic/{key}", None)
            parts = (txt.split(",") if txt else []) + ["", "", "", ""]
            for j in range(4):
                self.v_obj[key][j].set(parts[j].strip())
            lbl, ents = self.obj_rows[key]
            exists = txt is not None
            if exists:
                objs.append(key)
            if key == "obj3":
                for w in [lbl] + ents:
                    (w.grid if exists else w.grid_remove)()
        self.cb_objective.configure(values=objs)
        self.v_objective.set(sget(r, "mosaic/objective", "obj1"))
        pw = [p.strip() for p in sget(r, "illumination/default_power").split(",")]
        for i in range(N_CHANNELS):
            self.v_power[i].set(pw[i] if i < len(pw) else "1.000")
        self.lbl_source.configure(text=os.path.basename(self.settings_source)
                                  if os.path.isabs(self.settings_source) else self.settings_source)

    def push_quick(self):
        """Write the quick form and the sequence-derived values back into the settings tree."""
        r = self.settings_root
        sset(r, "camera1/exposure_time", self.v_exposure.get().strip(), "float")
        bs = lambda v: "True" if v.get() else "False"
        sset(r, "camera1/flip_horizontal", bs(self.v_cam_fh), "boolean")
        sset(r, "camera1/flip_vertical", bs(self.v_cam_fv), "boolean")
        sset(r, "camera1/transpose", bs(self.v_cam_tr), "boolean")
        sset(r, "mosaic/flip_horizontal", bs(self.v_mos_fh), "boolean")
        sset(r, "mosaic/flip_vertical", bs(self.v_mos_fv), "boolean")
        sset(r, "mosaic/transpose", bs(self.v_mos_tr), "boolean")
        for key in ("obj1", "obj2", "obj3"):
            if r.find(f"mosaic/{key}") is not None:
                vals = [v.get().strip() for v in self.v_obj[key]]
                sset(r, f"mosaic/{key}", ",".join(vals), "custom")
        sset(r, "mosaic/objective", self.v_objective.get(), "string")
        pw = []
        for v in self.v_power:
            try:
                pw.append(f"{float(v.get()):.3f}")
            except ValueError:
                pw.append(v.get().strip())
        sset(r, "illumination/default_power", ",".join(pw), "custom")
        # derived from the sequence
        sset(r, "illumination/shutters", shutters_filename(self.steps), "string")
        sset(r, "film/frames", str(total_frames(self.steps)), "int")
        sset(r, "film/filename", self.v_film.get().strip(), "string")
        sset(r, "focuslock/hardware_z_scan/z_offsets", self.get_z_text(), "string")

    def validate_settings(self):
        problems = []
        e = self._exposure()
        if not e or e <= 0:
            problems.append("Invalid exposure time")
        for i, v in enumerate(self.v_power):
            try:
                p = float(v.get())
                if not 0 <= p <= 1:
                    problems.append(f"{LASERS[i][1]} nm power {p} is not between 0 and 1")
            except ValueError:
                problems.append(f"{LASERS[i][1]} nm power is not a number")
        zv = self.current_z_values()
        if zv is None:
            problems.append("Invalid z_offsets")
        elif len(zv) != total_frames(self.steps):
            problems.append(f"Number of z_offsets ({len(zv)}) does not match total frames ({total_frames(self.steps)})")
        if not self.v_film.get().strip():
            problems.append("Movie name is empty")
        try:
            float(self.v_obj[self.v_objective.get()][1].get())
        except (ValueError, KeyError):
            problems.append("µm/pixel of the active objective is not a number")
        return problems

    def open_settings(self):
        path = filedialog.askopenfilename(initialdir=self.last_dir, title="Open settings file",
                                          filetypes=[("XML", "*.xml"), ("All", "*.*")])
        if path:
            self.load_settings(path)

    def load_settings(self, path):
        try:
            root = ET.parse(path).getroot()
            if root.tag != "settings":
                raise ValueError(f"Root element is <{root.tag}>, not <settings>.\n"
                                 f"If this is a shutters file, use Open shutters on tab 1.")
        except Exception as ex:
            messagebox.showerror("Could not read file", f"{os.path.basename(path)}\n\n{ex}")
            return
        self.last_dir = os.path.dirname(path)
        self.settings_root = root
        self.settings_source = path
        notes = []
        prefix, tag = split_settings_name(os.path.splitext(os.path.basename(path))[0])
        self.v_prefix.set(prefix)
        self.v_tag.set(tag)
        # linked shutters file
        sh = sget(root, "illumination/shutters").strip()
        sh_path = os.path.join(os.path.dirname(path), sh) if sh else ""
        if sh and os.path.exists(sh_path):
            self.load_shutters(sh_path, quiet=True)
            notes.append(f"Also loaded the linked shutters file: {sh}")
        elif sh:
            notes.append(f"Linked shutters file {sh} not found; the sequence was left unchanged")
        self.pull_quick()
        # z offsets: auto if the rule can be inferred, else keep the text
        ztxt = sget(root, "focuslock/hardware_z_scan/z_offsets")
        try:
            zv = parse_float_list(ztxt)
            inferred = infer_z_params(self.steps, zv)
        except ValueError:
            inferred = None
        if inferred:
            z0, dz, mode = inferred
            self.v_z_start.set(fmt_num(z0))
            self.v_z_step.set(fmt_num(dz))
            self.v_z_mode.set(mode)
            self.v_auto_z.set(True)
        else:
            self.v_auto_z.set(False)
            self.set_z_text(ztxt)
            notes.append("z_offsets do not match the auto rule, so auto-generate was turned off and the original values were kept")
        # movie name
        film = sget(root, "film/filename")
        self.v_tag_in_film.set(bool(tag) and film.endswith("-" + tag))
        if film == self.auto_film_name():
            self.v_auto_film.set(True)
        else:
            self.v_auto_film.set(False)
            self.v_film.set(film)
        self._on_auto_film()
        self._on_auto_z()
        self.refresh_steps()
        self.status(f"Loaded settings: {path}")
        if notes:
            messagebox.showinfo("Loaded", "\n".join(notes))

    def choose_settings_preset(self):
        label = self.v_settings_preset.get()
        p = next((x for x in SETTINGS_PRESETS if preset_label(x) == label), None)
        if p and messagebox.askyesno("Load preset", f"Load preset \"{p['name']}\"?\n\nThis replaces the current sequence and settings."):
            self.apply_settings_preset(p)

    def apply_settings_preset(self, p):
        root = settings_from_string(DEFAULT_SETTINGS_XML)
        for path, val in p["set"].items():
            sset(root, path, val)
        self.settings_root = root
        self.settings_source = f"Preset {preset_label(p)}"
        self.steps = [new_step(w, n) for w, n in p["steps"]]
        self.oversampling.set(1)
        prefix, tag = split_settings_name(p["name"])
        self.v_prefix.set(prefix)
        self.v_tag.set(tag)
        z0, dz, mi = p["z"]
        self.v_z_start.set(fmt_num(z0))
        self.v_z_step.set(fmt_num(dz))
        self.v_z_mode.set(Z_MODES[mi])
        self.v_auto_z.set(True)
        self.v_tag_in_film.set(p.get("tag_in_film", False))
        self.v_auto_film.set(True)
        self.pull_quick()
        self._on_auto_film()
        self._on_auto_z()
        self.refresh_steps()
        self.status(f"Loaded preset: {preset_label(p)}")

    def reset_settings(self):
        if messagebox.askyesno("Reset", "Replace the current settings with the built-in template? (The sequence is kept.)"):
            self.settings_root = settings_from_string(DEFAULT_SETTINGS_XML)
            self.settings_source = "Built-in default template (Dsk-650s10-560s10-488s10-405s10-U2OS)"
            self.pull_quick()
            self.update_derived()

    def _confirm_problems(self, problems):
        if not problems:
            return True
        return messagebox.askyesno("Problems found", "\n".join("• " + p for p in problems) + "\n\nSave anyway?")

    def save_settings_as(self):
        if not self._check_sequence() or not self._confirm_problems(self.validate_settings()):
            return
        path = filedialog.asksaveasfilename(initialdir=self.last_dir, initialfile=self.settings_filename(),
                                            defaultextension=".xml", filetypes=[("XML", "*.xml")])
        if path:
            self.push_quick()
            write_text_crlf(path, settings_to_string(self.settings_root))
            self.last_dir = os.path.dirname(path)
            self.status(f"Saved settings: {path}")

    def export_both(self):
        if not self._check_sequence() or not self._confirm_problems(self.validate_settings()):
            return
        folder = filedialog.askdirectory(initialdir=self.last_dir, title="Choose export folder")
        if not folder:
            return
        self.push_quick()
        files = {shutters_filename(self.steps): shutters_to_string(self.steps, self.oversampling.get()),
                 self.settings_filename(): settings_to_string(self.settings_root)}
        exist = [n for n in files if os.path.exists(os.path.join(folder, n))]
        if exist and not messagebox.askyesno("Confirm overwrite", "These files already exist. Overwrite?\n\n" + "\n".join(exist)):
            return
        for n, txt in files.items():
            write_text_crlf(os.path.join(folder, n), txt)
        self.last_dir = folder
        self.status(f"Exported to {folder}")
        messagebox.showinfo("Export complete", f"Wrote to {folder}:\n\n" + "\n".join(files))

    # ================================================================ tab 3 logic
    def refresh_adv(self):
        t = self.adv_tree
        opened = {self.adv_items[i].tag for i in self.adv_items if t.item(i, "open")} if self.adv_items else None
        t.delete(*t.get_children())
        self.adv_items = {}

        def add(parent_item, el, path):
            p = f"{path}/{el.tag}" if path else el.tag
            if len(el):
                label = el.tag + (f"   [validate={el.get('validate')}]" if el.get("validate") else "")
                it = t.insert(parent_item, "end", text=label, values=("", ""),
                              open=(opened is None or el.tag in opened))
                self.adv_items[it] = el
                for ch in el:
                    add(it, ch, p)
            else:
                it = t.insert(parent_item, "end", text=el.tag, values=(el.get("type", ""), el.text or ""))
                self.adv_items[it] = el

        for ch in self.settings_root:
            add("", ch, "")

    def _on_adv_double(self, e):
        item = self.adv_tree.identify_row(e.y)
        if not item or item not in self.adv_items:
            return
        el = self.adv_items[item]
        if len(el):
            return
        values = ["True", "False"] if el.get("type") == "boolean" else None

        def done(v):
            typ = el.get("type")
            try:
                if typ == "int":
                    int(v)
                elif typ == "float":
                    float(v)
            except ValueError:
                messagebox.showerror("Type error", f"{el.tag} needs a {typ}, got: {v}")
                return
            el.text = v
            self.adv_tree.set(item, "value", v)
            self.status(f"Changed {el.tag} = {v}")

        inline_edit(self.adv_tree, item, "value", done, values=values)

    # ================================================================ tab 4 logic
    def open_kilroy(self):
        path = filedialog.askopenfilename(initialdir=dialog_dir(self.kilroy_path, LAB_KILROY_DIR, self.last_dir),
                                          title="Open Kilroy protocol file",
                                          filetypes=[("XML", "*.xml"), ("All", "*.*")])
        if path:
            self.load_kilroy(path)

    def load_kilroy(self, path, quiet=False):
        try:
            k = KilroyConfig.load(path)
        except Exception as ex:
            if quiet:  # at startup: fall back to the built-in preset
                self.apply_kilroy_preset(next(iter(KILROY_PRESETS)))
            else:      # opened by hand: keep the current content
                messagebox.showerror("Could not read file", f"{os.path.basename(path)}\n\n{ex}")
            return
        self.kilroy = k
        self.kilroy_path = path
        self.kilroy_preset_name = None
        self.v_kilroy_preset.set("")
        self.refresh_kilroy_all()
        self.status(f"Loaded Kilroy: {path}")

    def save_kilroy(self):
        if not self.kilroy_path:
            return self.save_kilroy_as()
        self._write_kilroy(self.kilroy_path)

    def choose_kilroy_preset(self):
        name = self.v_kilroy_preset.get()
        if name in KILROY_PRESETS and messagebox.askyesno(
                "Load fluidics preset", f"Replace the current Kilroy protocols with preset \"{name}\"?\n\n(Files on disk are not changed; you choose where to save.)"):
            self.apply_kilroy_preset(name)

    def apply_kilroy_preset(self, name):
        self.kilroy = KILROY_PRESETS[name]["make"]()
        self.kilroy_path = None
        self.kilroy_suggest = KILROY_PRESETS[name]["file"]
        self.kilroy_preset_name = name
        self.v_kilroy_preset.set(name)
        self.refresh_kilroy_all()
        self.status(f"Loaded fluidics preset: {name}")

    def save_kilroy_as(self):
        init = (os.path.basename(self.kilroy_path) if self.kilroy_path
                else getattr(self, "kilroy_suggest", None) or "kilroy_protocol.xml")
        path = filedialog.asksaveasfilename(initialdir=dialog_dir(self.kilroy_path, LAB_KILROY_DIR, self.last_dir),
                                            initialfile=init,
                                            defaultextension=".xml", filetypes=[("XML", "*.xml")])
        if path:
            self._write_kilroy(path)

    def _write_kilroy(self, path):
        if not self._confirm_problems(self.kilroy.validate()):
            return
        write_text_crlf(path, self.kilroy.to_string())
        self.kilroy_path = path
        self.refresh_kilroy_label()
        self.status(f"Saved Kilroy: {path}")

    def check_kilroy(self):
        probs = self.kilroy.validate()
        if probs:
            messagebox.showwarning("Check results", "\n".join("• " + p for p in probs[:40]) +
                                   (f"\n… {len(probs)} in total" if len(probs) > 40 else ""))
        else:
            messagebox.showinfo("Check results", "No problems found ✓")

    def refresh_kilroy_label(self):
        k = self.kilroy
        if self.kilroy_path:
            name = os.path.basename(self.kilroy_path)
        elif getattr(self, "kilroy_preset_name", None):
            name = f"Preset {self.kilroy_preset_name} (unsaved)"
        else:
            name = "(new, unsaved file)"
        self.lbl_kilroy.configure(text=f"{name}  —  {len(k.protocols)} protocols · {len(k.valves)} valve cmds · "
                                       f"{len(k.pumps)} pump cmds · {k.num_valves} valves")

    def refresh_kilroy_all(self):
        self.refresh_kilroy_label()
        self.refresh_proto_list()
        self.refresh_valves()
        self.refresh_pumps()
        self.cb_g_template.configure(values=[p[0] for p in self.kilroy.protocols])
        self.cb_prime_pump.configure(values=[p[0] for p in self.kilroy.pumps])
        self.lbl_pump_comments.configure(text="\n".join(c.strip() for c in self.kilroy.comments.get("pump_commands", [])))
        if hasattr(self, "lbl_dave_summary"):
            self.refresh_dave_summary()

    # ---- protocols
    def _proto_idx(self):
        sel = self.proto_list.curselection()
        return sel[0] if sel else None

    def refresh_proto_list(self, select=None):
        if select is None:
            select = self._proto_idx()
        lb = self.proto_list
        lb.delete(0, "end")
        for name, steps in self.kilroy.protocols:
            lb.insert("end", f"{name}   ({fmt_duration(self.kilroy.protocol_seconds(steps))})")
        if self.kilroy.protocols:
            select = 0 if select is None else max(0, min(select, len(self.kilroy.protocols) - 1))
            lb.selection_clear(0, "end")
            lb.selection_set(select)
            lb.see(select)
        self.refresh_proto_steps()
        self.cb_g_template.configure(values=[p[0] for p in self.kilroy.protocols])

    def refresh_proto_steps(self, select=None):
        t = self.pstep_tree
        t.delete(*t.get_children())
        i = self._proto_idx()
        if i is None:
            self.lbl_proto_total.configure(text="")
            return
        name, steps = self.kilroy.protocols[i]
        tt = 0.0
        for j, (tag, dur, cmd) in enumerate(steps):
            t.insert("", "end", values=(j + 1, tag, dur, cmd, fmt_duration(tt)), tags=(tag,))
            try:
                tt += float(dur)
            except ValueError:
                pass
        self.lbl_proto_total.configure(text=f"\"{name}\" total duration {fmt_duration(tt)}")
        tree_reselect(t, select)

    def _update_proto_label(self):
        i = self._proto_idx()
        if i is None:
            return
        name, steps = self.kilroy.protocols[i]
        self.proto_list.delete(i)
        self.proto_list.insert(i, f"{name}   ({fmt_duration(self.kilroy.protocol_seconds(steps))})")
        self.proto_list.selection_set(i)

    def _unique_name(self, base, existing):
        if base not in existing:
            return base
        k = 2
        while f"{base} ({k})" in existing:
            k += 1
        return f"{base} ({k})"

    def proto_new(self):
        name = simpledialog.askstring("New protocol", "Protocol name:", parent=self)
        if not name:
            return
        if name in [p[0] for p in self.kilroy.protocols]:
            messagebox.showerror("Error", "A protocol with that name already exists")
            return
        i = self._proto_idx()
        pos = len(self.kilroy.protocols) if i is None else i + 1
        self.kilroy.protocols.insert(pos, [name, []])
        self.refresh_proto_list(pos)
        self.refresh_kilroy_label()

    def proto_dup(self):
        i = self._proto_idx()
        if i is None:
            return
        name, steps = self.kilroy.protocols[i]
        new = self._unique_name(name + " copy", [p[0] for p in self.kilroy.protocols])
        self.kilroy.protocols.insert(i + 1, [new, copy.deepcopy(steps)])
        self.refresh_proto_list(i + 1)
        self.refresh_kilroy_label()

    def proto_rename(self):
        i = self._proto_idx()
        if i is None:
            return
        old = self.kilroy.protocols[i][0]
        name = simpledialog.askstring("Rename protocol", "New name:", initialvalue=old, parent=self)
        if name and name != old:
            if name in [p[0] for p in self.kilroy.protocols]:
                messagebox.showerror("Error", "A protocol with that name already exists")
                return
            self.kilroy.protocols[i][0] = name
            self.refresh_proto_list(i)

    def proto_delete(self):
        i = self._proto_idx()
        if i is None:
            return
        if messagebox.askyesno("Delete", f"Delete protocol \"{self.kilroy.protocols[i][0]}\"?"):
            del self.kilroy.protocols[i]
            self.refresh_proto_list(i)
            self.refresh_kilroy_label()

    def proto_move(self, d):
        i = self._proto_idx()
        P = self.kilroy.protocols
        if i is None or not (0 <= i + d < len(P)):
            return
        P[i], P[i + d] = P[i + d], P[i]
        self.refresh_proto_list(i + d)

    def _cur_steps(self):
        i = self._proto_idx()
        return None if i is None else self.kilroy.protocols[i][1]

    def _cmd_names(self, tag):
        return [v[0] for v in (self.kilroy.valves if tag == "valve" else self.kilroy.pumps)]

    def pstep_add(self, tag):
        steps = self._cur_steps()
        if steps is None:
            messagebox.showinfo("Note", "Select or create a protocol first")
            return
        names = self._cmd_names(tag)
        j = tree_index(self.pstep_tree)
        pos = len(steps) if j is None else j + 1
        steps.insert(pos, [tag, "5" if tag == "valve" else "60", names[0] if names else ""])
        self.refresh_proto_steps(pos)
        self._update_proto_label()

    def pstep_dup(self):
        steps = self._cur_steps()
        j = tree_index(self.pstep_tree)
        if steps is None or j is None:
            return
        steps.insert(j + 1, list(steps[j]))
        self.refresh_proto_steps(j + 1)
        self._update_proto_label()

    def pstep_delete(self):
        steps = self._cur_steps()
        j = tree_index(self.pstep_tree)
        if steps is None or j is None:
            return
        del steps[j]
        self.refresh_proto_steps(j)
        self._update_proto_label()

    def pstep_move(self, d):
        steps = self._cur_steps()
        j = tree_index(self.pstep_tree)
        if steps is None or j is None or not (0 <= j + d < len(steps)):
            return
        steps[j], steps[j + d] = steps[j + d], steps[j]
        self.refresh_proto_steps(j + d)

    def _on_pstep_double(self, e):
        t = self.pstep_tree
        item = t.identify_row(e.y)
        col_id = t.identify_column(e.x)
        steps = self._cur_steps()
        if not item or not col_id or steps is None:
            return
        col = t["columns"][int(col_id[1:]) - 1]
        j = t.index(item)
        step = steps[j]

        def done(field):
            def f(v):
                v = v.strip()
                if field == 1:
                    try:
                        float(v)
                    except ValueError:
                        messagebox.showerror("Invalid input", "Duration must be a number (seconds)")
                        return
                if field == 0:
                    if v not in ("valve", "pump"):
                        return
                    if v != step[0]:
                        names = self._cmd_names(v)
                        step[2] = names[0] if names else ""
                step[field] = v
                self.refresh_proto_steps(j)
                self._update_proto_label()
            return f

        if col == "Type":
            inline_edit(t, item, col, done(0), values=["valve", "pump"])
        elif col == "Duration (s)":
            inline_edit(t, item, col, done(1))
        elif col == "Command":
            inline_edit(t, item, col, done(2), values=self._cmd_names(step[0]))

    # ---- valves
    def refresh_valves(self, select=None):
        if self.valve_tree is not None:
            if select is None:
                select = tree_index(self.valve_tree)
            self.valve_tree.master.destroy()
        n = self.kilroy.num_valves
        cols = ("Name",) + tuple(f"Valve {v}" for v in range(1, n + 1))
        fr, self.valve_tree = make_tree(self.valve_frame, cols, [220] + [80] * n, height=16,
                                        anchors=["w"] + ["center"] * n)
        fr.grid(row=0, column=0, sticky="nsew")
        self.valve_tree.bind("<Double-1>", self._on_valve_double)
        for name, pos in self.kilroy.valves:
            self.valve_tree.insert("", "end", values=(name,) + tuple(pos.get(v, "") for v in range(1, n + 1)))
        tree_reselect(self.valve_tree, select)

    def _on_valve_double(self, e):
        t = self.valve_tree
        item = t.identify_row(e.y)
        col_id = t.identify_column(e.x)
        if not item or not col_id:
            return
        ci = int(col_id[1:]) - 1
        col = t["columns"][ci]
        j = t.index(item)
        entry = self.kilroy.valves[j]
        if ci == 0:
            def done(v):
                v = v.strip()
                if not v or v in [x[0] for x in self.kilroy.valves]:
                    return
                old = entry[0]
                entry[0] = v
                cnt = self._rename_refs("valve", old, v)
                self.refresh_valves(j)
                self.refresh_proto_steps(tree_index(self.pstep_tree))
                if cnt:
                    self.status(f"Renamed '{old}' → '{v}' and updated {cnt} protocol references")
            inline_edit(t, item, col, done)
        else:
            vid = ci

            def done(v):
                v = v.strip()
                if v == "":
                    entry[1].pop(vid, None)
                elif v.isdigit():
                    entry[1][vid] = v
                else:
                    messagebox.showerror("Invalid input", "Port must be an integer")
                    return
                self.refresh_valves(j)
            inline_edit(t, item, col, done, values=[str(p) for p in range(1, 11)])

    def _rename_refs(self, tag, old, new):
        cnt = 0
        for _, steps in self.kilroy.protocols:
            for st in steps:
                if st[0] == tag and st[2] == old:
                    st[2] = new
                    cnt += 1
        return cnt

    def valve_new(self):
        name = simpledialog.askstring("New valve command", "Name (e.g. Set Hyb 17):", parent=self)
        if not name:
            return
        if name in [v[0] for v in self.kilroy.valves]:
            messagebox.showerror("Error", "A command with that name already exists")
            return
        n = self.kilroy.num_valves
        j = tree_index(self.valve_tree)
        pos = len(self.kilroy.valves) if j is None else j + 1
        self.kilroy.valves.insert(pos, [name, {v: "8" for v in range(1, n + 1)}])
        self.refresh_valves(pos)
        self.refresh_kilroy_label()

    def valve_dup(self):
        j = tree_index(self.valve_tree)
        if j is None:
            return
        name, pos = self.kilroy.valves[j]
        new = self._unique_name(name + " copy", [v[0] for v in self.kilroy.valves])
        self.kilroy.valves.insert(j + 1, [new, dict(pos)])
        self.refresh_valves(j + 1)
        self.refresh_kilroy_label()

    def valve_delete(self):
        j = tree_index(self.valve_tree)
        if j is None:
            return
        name = self.kilroy.valves[j][0]
        used = sum(1 for _, st in self.kilroy.protocols for s in st if s[0] == "valve" and s[2] == name)
        msg = f"Delete valve command \"{name}\"?" + (f"\n\nWarning: {used} protocol steps use it!" if used else "")
        if messagebox.askyesno("Delete", msg):
            del self.kilroy.valves[j]
            self.refresh_valves(j)
            self.refresh_kilroy_label()

    def valve_move(self, d):
        j = tree_index(self.valve_tree)
        V = self.kilroy.valves
        if j is None or not (0 <= j + d < len(V)):
            return
        V[j], V[j + d] = V[j + d], V[j]
        self.refresh_valves(j + d)

    def valve_set_count(self):
        n = simpledialog.askinteger("Number of valves", "Number of valves (num_valves):", initialvalue=self.kilroy.num_valves,
                                    minvalue=1, maxvalue=20, parent=self)
        if not n:
            return
        for _, pos in self.kilroy.valves:
            for v in list(pos):
                if v > n:
                    del pos[v]
            for v in range(1, n + 1):
                pos.setdefault(v, "8")
        self.kilroy.attrib["num_valves"] = str(n)
        self.refresh_valves()
        self.refresh_kilroy_label()

    # ---- pumps
    def refresh_pumps(self, select=None):
        t = self.pump_tree
        t.delete(*t.get_children())
        for name, cfg in self.kilroy.pumps:
            t.insert("", "end", values=(name, cfg.get("speed", ""), cfg.get("direction", "")))
        tree_reselect(t, select)
        self.cb_prime_pump.configure(values=[p[0] for p in self.kilroy.pumps])

    def _on_pump_double(self, e):
        t = self.pump_tree
        item = t.identify_row(e.y)
        col_id = t.identify_column(e.x)
        if not item or not col_id:
            return
        ci = int(col_id[1:]) - 1
        col = t["columns"][ci]
        j = t.index(item)
        entry = self.kilroy.pumps[j]

        def done(v):
            v = v.strip()
            if ci == 0:
                if not v or v in [p[0] for p in self.kilroy.pumps]:
                    return
                old = entry[0]
                entry[0] = v
                self._rename_refs("pump", old, v)
                self.refresh_proto_steps(tree_index(self.pstep_tree))
            elif ci == 1:
                try:
                    float(v)
                except ValueError:
                    messagebox.showerror("Invalid input", "Speed must be a number")
                    return
                entry[1]["speed"] = v
            else:
                if v:
                    entry[1]["direction"] = v
                else:
                    entry[1].pop("direction", None)
            self.refresh_pumps(j)

        inline_edit(t, item, col, done, values=["Forward", "Reverse", ""] if ci == 2 else None)

    def pump_new(self):
        name = simpledialog.askstring("New pump command", "Name (e.g. Flow 1.5 ml/min):", parent=self)
        if not name or name in [p[0] for p in self.kilroy.pumps]:
            return
        self.kilroy.pumps.append([name, {"speed": "0.0", "direction": "Forward"}])
        self.refresh_pumps(len(self.kilroy.pumps) - 1)
        self.refresh_kilroy_label()

    def pump_delete(self):
        j = tree_index(self.pump_tree)
        if j is None:
            return
        name = self.kilroy.pumps[j][0]
        if messagebox.askyesno("Delete", f"Delete pump command \"{name}\"?"):
            del self.kilroy.pumps[j]
            self.refresh_pumps(j)
            self.refresh_kilroy_label()

    # ---- generators
    def generate_hybs(self):
        k = self.kilroy
        try:
            tn = int(self.g_template_n.get())
            a, b = int(self.g_from.get()), int(self.g_to.get())
            pfmt, vfmt = self.g_proto_fmt.get(), self.g_valve_fmt.get()
            pfmt.format(n=1), vfmt.format(n=1)
        except (ValueError, KeyError, IndexError):
            messagebox.showerror("Invalid input", "Check the round numbers and formats (use {n} for the round number)")
            return
        if b < a:
            a, b = b, a
        tmpl = next((p for p in k.protocols if p[0] == self.g_template.get()), None)
        if tmpl is None:
            messagebox.showerror("Error", "Choose a template protocol")
            return
        tvalve = vfmt.format(n=tn)
        if not any(s[0] == "valve" and s[2] == tvalve for s in tmpl[1]):
            messagebox.showerror("Error", f"Template protocol \"{tmpl[0]}\" has no valve command \"{tvalve}\"")
            return
        names = [p[0] for p in k.protocols]
        to_overwrite = [pfmt.format(n=n) for n in range(a, b + 1) if pfmt.format(n=n) in names]
        vnames = {v[0] for v in k.valves}
        missing = [vfmt.format(n=n) for n in range(a, b + 1) if vfmt.format(n=n) not in vnames]
        msg = f"This will create {b - a + 1} protocols: {pfmt.format(n=a)} … {pfmt.format(n=b)}"
        if to_overwrite:
            msg += f"\n\n{len(to_overwrite)} of them already exist and will be overwritten."
        if missing:
            msg += f"\n\n⚠ These valve commands are not defined yet; add them on the Valve commands tab:\n" + ", ".join(missing)
        if not messagebox.askyesno("Confirm", msg):
            return
        tmpl_steps = copy.deepcopy(tmpl[1])
        insert_at = None
        for n in range(a, b + 1):
            steps = [[t, d, (vfmt.format(n=n) if (t == "valve" and c == tvalve) else c)] for t, d, c in tmpl_steps]
            pname = pfmt.format(n=n)
            idx = next((i for i, p in enumerate(k.protocols) if p[0] == pname), None)
            if idx is not None:
                k.protocols[idx][1] = steps
                insert_at = idx + 1
            else:
                if insert_at is None:
                    # insert after the last protocol with the same name format
                    pat = re.compile("^" + re.escape(pfmt).replace(re.escape("{n}"), r"\d+") + "$")
                    hits = [i for i, p in enumerate(k.protocols) if pat.match(p[0])]
                    insert_at = (hits[-1] + 1) if hits else len(k.protocols)
                k.protocols.insert(insert_at, [pname, steps])
                insert_at += 1
        self.refresh_proto_list()
        self.refresh_kilroy_label()
        self.status(f"Generated {pfmt.format(n=a)} … {pfmt.format(n=b)}")

    def generate_prime(self):
        k = self.kilroy
        try:
            n = int(self.g_prime_n.get())
            pd = fmt_num(float(self.g_prime_pump_dur.get()))
            hd = fmt_num(float(self.g_prime_hyb_dur.get()))
            ed = fmt_num(float(self.g_prime_extra_dur.get()))
            ld = fmt_num(float(self.g_prime_last_dur.get()))
        except ValueError:
            messagebox.showerror("Invalid input", "Check the numbers")
            return
        extras = [x.strip() for x in self.g_prime_extra.get().split(",") if x.strip()]
        steps = [["pump", pd, self.g_prime_pump.get()]]
        steps += [["valve", hd, self.g_valve_fmt.get().format(n=i)] for i in range(1, n + 1)]
        steps += [["valve", ed, x] for x in extras]
        if self.g_prime_last.get().strip():
            steps.append(["valve", ld, self.g_prime_last.get().strip()])
        stop = next((p[0] for p in k.pumps if p[1].get("speed", "0") in ("0", "0.0") or "stop" in p[0].lower()),
                    "Stop Flow")
        steps.append(["pump", "5", stop])
        name = f"Prime {n} + {len(extras) + (1 if self.g_prime_last.get().strip() else 0)}"
        idx = next((i for i, p in enumerate(k.protocols) if p[0] == name), None)
        if idx is not None:
            if not messagebox.askyesno("Overwrite", f"Protocol \"{name}\" already exists. Overwrite?"):
                return
            k.protocols[idx][1] = steps
        else:
            hits = [i for i, p in enumerate(k.protocols) if p[0].startswith("Prime")]
            idx = (hits[-1] + 1) if hits else 0
            k.protocols.insert(idx, [name, steps])
        self.refresh_proto_list(idx)
        self.refresh_kilroy_label()
        self.status(f"Generated protocol \"{name}\" ({fmt_duration(k.protocol_seconds(steps))})")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
