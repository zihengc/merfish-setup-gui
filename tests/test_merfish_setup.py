"""Tests for the MERFISH setup GUI's file handling and presets.

Run from the repository root:
    python -m unittest discover tests -v

The GUI tests open a real Tk window, so they only run when MERFISH_GUI_TESTS=1 is set
(macOS's built-in /usr/bin/python3 ships a Tk that hangs instead of opening windows).
"""
import copy
import glob
import os
import sys
import unittest
import xml.etree.ElementTree as ET

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "app"))
import merfish_setup_gui as M  # noqa: E402

HAL = os.path.join(REPO, "lab_files", "hal")
KILROY = os.path.join(REPO, "lab_files", "kilroy", "kilroy_protocol_MERFISH_lab.xml")
DAVE = os.path.join(REPO, "lab_files", "dave")
KILROY_U2OS_HYB = os.path.join(REPO, "lab_files", "kilroy", "kilroy_protocol_MERFISH_U2OS_hyb.xml")


def norm(el):
    """Structure + stripped text of an XML tree, ignoring whitespace and comments."""
    return (el.tag, tuple(sorted(el.attrib.items())), (el.text or "").strip(),
            tuple(norm(c) for c in el if c.tag is not ET.Comment))


def read_text(path):
    with open(path, encoding="iso-8859-1") as f:
        return f.read().replace("\r\n", "\n")


def settings_files(folder):
    out = []
    for p in sorted(glob.glob(os.path.join(folder, "*.xml"))):
        if ET.parse(p).getroot().tag == "settings":
            out.append(p)
    return out


def build_preset_settings(p):
    """What the app writes for a settings preset (same steps as App.apply_settings_preset + push_quick)."""
    root = M.settings_from_string(M.DEFAULT_SETTINGS_XML)
    for path, val in p["set"].items():
        M.sset(root, path, val)
    steps = [M.new_step(w, n) for w, n in p["steps"]]
    prefix, tag = M.split_settings_name(p["name"])
    film = f"{prefix}-{M.sequence_tokens(steps)}" + (f"-{tag}" if p.get("tag_in_film") else "")
    z0, dz, mi = p["z"]
    M.sset(root, "illumination/shutters", M.shutters_filename(steps))
    M.sset(root, "film/frames", str(M.total_frames(steps)))
    M.sset(root, "film/filename", film)
    M.sset(root, "focuslock/hardware_z_scan/z_offsets",
           M.z_groups_to_string(M.make_z_groups(steps, z0, dz, M.Z_MODES[mi])))
    return root, steps


class ShuttersTests(unittest.TestCase):
    def test_round_trip_and_name(self):
        files = glob.glob(os.path.join(HAL, "*_shutters_1cam.xml"))
        self.assertTrue(files)
        for path in files:
            with self.subTest(os.path.basename(path)):
                overs, steps, warnings = M.parse_shutters(path)
                self.assertEqual(warnings, [])
                out = M.shutters_to_string(steps, overs)
                self.assertEqual(norm(ET.fromstring(out)), norm(ET.parse(path).getroot()))
                self.assertEqual(M.shutters_filename(steps), os.path.basename(path))


class SettingsTests(unittest.TestCase):
    def test_round_trip_is_byte_identical(self):
        for path in settings_files(HAL):
            with self.subTest(os.path.basename(path)):
                root = ET.parse(path).getroot()
                self.assertEqual(M.settings_to_string(root), read_text(path))

    def test_z_offsets_follow_the_auto_rule(self):
        for path in settings_files(HAL):
            with self.subTest(os.path.basename(path)):
                root = ET.parse(path).getroot()
                _, steps, _ = M.parse_shutters(os.path.join(HAL, M.sget(root, "illumination/shutters")))
                z = M.parse_float_list(M.sget(root, "focuslock/hardware_z_scan/z_offsets"))
                self.assertIsNotNone(M.infer_z_params(steps, z))

    def test_presets_reproduce_files(self):
        names = {p["name"] for p in M.SETTINGS_PRESETS}
        self.assertEqual(names, {os.path.basename(f)[:-4] for f in settings_files(HAL)},
                         "every settings file in lab_files/hal should have a preset, and vice versa")
        for p in M.SETTINGS_PRESETS:
            with self.subTest(p["name"]):
                root, steps = build_preset_settings(p)
                orig = ET.parse(os.path.join(HAL, p["name"] + ".xml")).getroot()
                if p["group"] == "U2OS hyb":  # the original film/filename is out of date; the preset corrects it
                    M.sset(orig, "film/filename", M.sget(root, "film/filename"))
                self.assertEqual(norm(root), norm(orig))
                sh = ET.parse(os.path.join(HAL, M.shutters_filename(steps))).getroot()
                self.assertEqual(norm(ET.fromstring(M.shutters_to_string(steps))), norm(sh))

    def test_startup_preset_uses_every_laser(self):
        p = M.find_settings_preset(M.STARTUP_SETTINGS_PRESET)
        self.assertIsNotNone(p)
        self.assertEqual({w for w, _ in p["steps"]}, {w for _, w, _ in M.LASERS})


class KilroyTests(unittest.TestCase):
    def test_round_trip(self):
        k = M.KilroyConfig.load(KILROY)
        self.assertEqual(k.validate(), [])
        self.assertEqual(norm(ET.fromstring(k.to_string())), norm(ET.parse(KILROY).getroot()))

    def test_lab_preset_matches_file(self):
        preset = M.KILROY_PRESETS["Lab · kilroy_protocol_MERFISH_lab"]["make"]()
        self.assertEqual(preset.to_string(), M.KilroyConfig.load(KILROY).to_string())

    def test_u2os_hyb_preset_matches_file(self):
        preset = M.KILROY_PRESETS["U2OS hyb · longer flow times"]["make"]()
        self.assertEqual(preset.to_string(), M.KilroyConfig.load(KILROY_U2OS_HYB).to_string())


class DaveTests(unittest.TestCase):
    def test_preset_round_trip(self):
        d = M.dave_preset_u2os_hyb()
        d2 = M.DaveRecipe.from_root(ET.fromstring(d.to_string()))
        self.assertEqual(vars(d), vars(d2))

    def test_round_pattern(self):
        vals = M.make_round_values("Cleave, Hybridize {n}", 9, 12)
        self.assertEqual(M.detect_round_pattern(vals), ("Cleave, Hybridize {n}", 9, 12))
        self.assertIsNone(M.detect_round_pattern([["A"], ["B"]]))

    def test_rejects_unsupported_commands(self):
        for xml in ('<recipe><command_sequence><loop name="x"><movie><name>a</name><delay>3</delay>'
                    '</movie></loop></command_sequence></recipe>',
                    '<recipe><command_sequence><valve_protocol>Cleave</valve_protocol>'
                    '</command_sequence></recipe>'):
            with self.assertRaises(ValueError):
                M.DaveRecipe.from_root(ET.fromstring(xml))

    def test_validation_flags_missing_protocols(self):
        d = M.dave_preset_u2os_hyb()
        d.stages[1]["values"] = M.make_round_values("Cleave, Hybridize {n}", 1, 16)
        probs = d.validate(M.KilroyConfig.load(KILROY), lambda name: 19)
        self.assertTrue(any("Hybridize 15" in p and "Hybridize 16" in p for p in probs))

    def test_recipe_files(self):
        files = glob.glob(os.path.join(DAVE, "*.xml"))
        self.assertTrue(files)
        for path in files:
            with self.subTest(os.path.basename(path)):
                d = M.DaveRecipe.load(path)
                self.assertEqual(norm(ET.fromstring(d.to_string())), norm(ET.parse(path).getroot()))
                for st in d.stages:  # every stage's settings is in lab_files/hal with a matching frame count
                    settings = os.path.join(HAL, st["params"] + ".xml")
                    self.assertTrue(os.path.exists(settings), st["params"])
                    frames = M.sget(ET.parse(settings).getroot(), "film/frames")
                    self.assertEqual(st["length"], frames, st["params"])

    def test_u2os_hyb_preset_matches_file(self):
        d = M.DaveRecipe.load(os.path.join(DAVE, "dave_recipe_U2OS_1round+14rounds.xml"))
        self.assertEqual(vars(d), vars(M.dave_preset_u2os_hyb()))


@unittest.skipUnless(os.environ.get("MERFISH_GUI_TESTS") == "1", "set MERFISH_GUI_TESTS=1 to run GUI tests")
class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tkinter import messagebox
        cls._saved = {k: getattr(messagebox, k) for k in ("askyesno", "showinfo", "showwarning", "showerror")}
        messagebox.askyesno = lambda *a, **k: True
        messagebox.showinfo = messagebox.showwarning = messagebox.showerror = lambda *a, **k: None
        cls.app = M.App()
        cls.app.update()
        cls.startup = (cls.app.settings_filename(), {st["channel"] for st in cls.app.steps})

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()
        from tkinter import messagebox
        for k, v in cls._saved.items():
            setattr(messagebox, k, v)

    def test_startup_shows_every_channel(self):
        self.assertEqual(self.startup, (M.STARTUP_SETTINGS_PRESET + ".xml", {c for c, _, _ in M.LASERS}))

    def test_load_settings_and_save_unchanged(self):
        for path in settings_files(HAL):
            with self.subTest(os.path.basename(path)):
                self.app.load_settings(path)
                self.app.update()
                self.assertEqual(self.app.validate_settings(), [])
                self.app.push_quick()
                self.assertEqual(norm(ET.fromstring(M.settings_to_string(self.app.settings_root))),
                                 norm(ET.parse(path).getroot()))

    def test_every_preset_applies(self):
        for p in M.SETTINGS_PRESETS:
            with self.subTest(p["name"]):
                self.app.apply_settings_preset(p)
                self.app.update()
                self.assertEqual(self.app.settings_filename(), p["name"] + ".xml")
                self.assertEqual(self.app.validate_settings(), [])
        for name in M.KILROY_PRESETS:
            self.app.apply_kilroy_preset(name)
            self.assertEqual(self.app.kilroy.validate(), [])
        for name in M.DAVE_PRESETS:
            self.app.v_dave_preset.set(name)
            self.app.choose_dave_preset()
            self.assertTrue(self.app.dave.stages)

    def test_hyb_generation_matches_existing(self):
        self.app.load_kilroy(KILROY)
        before = copy.deepcopy(self.app.kilroy.protocols)
        self.app.g_from.set("1")
        self.app.g_to.set("14")
        self.app.generate_hybs()
        self.assertEqual(self.app.kilroy.protocols, before)

    def test_all_tabs_open(self):
        for i in range(len(self.app.nb.tabs())):
            self.app.nb.select(i)
            self.app._on_tab_changed()
            self.app.update()


if __name__ == "__main__":
    unittest.main()
