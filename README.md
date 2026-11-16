# MERFISH Setup GUI

A desktop app for preparing the files a [storm-control](https://github.com/ZhuangLab/storm-control) microscope needs for a MERFISH run: HAL shutters sequences, HAL settings, Kilroy fluidics protocols and Dave automation recipes. It uses only the Python standard library (tkinter), so it runs with any normal Python 3.9+ on Windows, macOS or Linux, with nothing to install.

```
python app/merfish_setup_gui.py
```

## Repository layout

```
app/
  merfish_setup_gui.py     the app (single file)
lab_files/
  hal/                     HAL settings and the shutters files they reference
  kilroy/                  the lab's Kilroy protocol file (loaded at startup)
  dave/                    Dave recipes
tests/
  test_merfish_setup.py    round-trip and preset tests
```

HAL settings and their shutters files sit in the same folder on purpose. A settings file names its shutters file in `illumination/shutters`, and the app looks for it next to the settings file.

What's in `lab_files/`:

- **Lab:** 4 settings (`Dsk-650s10-…`, `Dsk-750s1-…-cell`, `Epi-405s1-750s10-…` ×2) with their shutters files, and `kilroy_protocol_MERFISH_lab.xml`.
- **U2OS hyb:** `Dsk-405s1-750s6-650s6-405s6-U2OS` and `Dsk-405s1-750s6-650s6-560s6-U2OS` with their shutters files, and the Dave recipe `dave_recipe_U2OS_1round+14rounds.xml`. The recipe uses those two settings. His Kilroy file isn't included because it has the same name as the lab's; use the **U2OS hyb · longer flow times** fluidics preset instead, which reproduces it exactly.

## What each tab does

| Tab | Purpose |
|---|---|
| **1 Sequence (shutters / Z)** | Build the exposure sequence as laser × frames × power steps. The app writes the `*_shutters_1cam.xml` file, generates `z_offsets`, and shows a timing preview of the lasers and z position per frame. |
| **2 Microscope settings** | File-name prefix (Dsk / Epi) and sample tag, exposure time, camera and mosaic flips, objectives, and default laser powers. |
| **3 All parameters (advanced)** | Every parameter in the settings file (ROI, focus lock, …). Double-click a value to edit it. |
| **4 Fluidics (Kilroy)** | Edit protocols, valve commands and pump commands. Generate `Hybridize N` rounds from a template and `Prime N + 4` protocols. Shows each protocol's total duration. |
| **5 Automation (Dave)** | Build a Dave recipe from stages: *image once*, or a *hyb loop* (each round runs Kilroy protocols, then a wakeup and imaging). Includes an XML preview and an estimate of total fluidics time. |

A typical run setup:

1. Pick a settings preset at the top, or **Open settings…** (its shutters file loads with it).
2. Adjust the sequence and parameters, then **Export shutters + settings…**.
3. On tab 5, put those settings into a Dave recipe and save it. Choose the matching fluidics preset on tab 4 so the protocol checks and time estimate are right.

The app keeps the linked fields consistent: `illumination/shutters`, `film/frames`, `film/filename` and `z_offsets` all follow the sequence. When saving, it warns about mismatches such as a z-offset count that differs from the frame count, a Dave stage whose frame count differs from its settings, or protocols missing from Kilroy.

## Presets

| Where | Presets |
|---|---|
| Top bar, **Preset** | The lab's 4 settings, plus the U2OS hyb `Dsk-405s1-750s6-650s6-405s6-U2OS` and `Dsk-405s1-750s6-650s6-560s6-U2OS` |
| Tab 4, **Fluidics preset** | The lab's standard Kilroy protocols, and the U2OS hyb version with longer flow and wait times |
| Tab 5, **Recipe preset** | the U2OS hyb U2OS recipe (1 imaging round + 14 hyb rounds, which offers to load his fluidics preset too), a 1 + 14 round template, and an image-once template. The templates use the settings currently on tab 2. |

Loading a settings preset and exporting gives files identical to the ones in `lab_files/hal/`. The one exception is the U2OS hyb out-of-date `film/filename` (`Epi-405s1-750s10-…`), which is replaced with the correct name. Dave sets the movie name itself, so the old value doesn't affect runs. The Kilroy presets are generated from the lab's valve wiring and protocol templates, and they reproduce the original files exactly. Presets never change files on disk until you save.

To add a preset, add an entry to `SETTINGS_PRESETS`, `KILROY_PRESETS` or `DAVE_PRESETS` in `app/merfish_setup_gui.py`.

## File-format details

- Files are written the way HAL and Kilroy expect them: ISO-8859-1 encoding and Windows (CRLF) line endings. Loading a lab settings file and saving it again gives a byte-identical file.
- Laser channels: 0 = 750, 1 = 650, 2 = 560, 3 = 488, 4 = 405 nm (`LASERS` at the top of the app).
- Z scan rule: single-frame steps (e.g. the 405 fiducial) stay at the z start. Multi-frame steps take a z-stack from the start position in fixed steps, alternating direction between stacks (serpentine) by default, as in the existing files.
- Movie names: in Dave, the movie name is the settings name without the sample tag (`Dsk-405s1-750s6-650s6-405s6-U2OS` → `Dsk-405s1-750s6-650s6-405s6`).
- Dave support covers recipes built from imaging stages and hyb loops. A recipe containing other Dave commands (e.g. `delay`, `move_stage`) is refused on load rather than having those commands silently dropped.

## Running the tests

```
python -m unittest discover tests -v
```

The GUI tests open a real window, so they run only with `MERFISH_GUI_TESTS=1`. The test that compares the U2OS hyb fluidics preset with his original Kilroy file needs a local `reference/` folder (kept out of the repo by `.gitignore`), and is skipped without it.

## macOS note

The Python that ships with macOS (`/usr/bin/python3`) includes a Tk 8.5 that hangs instead of opening windows. Use a Python with Tk 8.6 instead, from python.org, Homebrew (`brew install python-tk@3.13`, then run with `python3.13`), or a conda/mamba environment:

```
mamba activate cellpose && python app/merfish_setup_gui.py
```
