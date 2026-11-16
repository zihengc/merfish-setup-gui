"""Build merfish_setup_gui_en.py (English UI) from merfish_setup_gui.py (Chinese UI).

The Chinese file is the source of truth. After changing it, run:
    python build_english_version.py
Every Chinese string is replaced by an exact-match lookup; the script lists anything
left untranslated and refuses to write the English file until the list is empty.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "merfish_setup_gui.py")
DST = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "merfish_setup_gui_en.py")

# Exact source-text string literals (including quotes / f prefix)
LIT = {
    '" 到 "': '" to "',
    '"(如 U2OS / cell / tissue，可留空)"': '"(e.g. U2OS / cell / tissue; optional)"',
    '"(未保存的新文件)"': '"(new, unsaved file)"',
    '"(没有步骤)"': '"(no steps)"',
    '"4色 z-stack (650/560/488/405 f10)"': '"4-color z-stack (650/560/488/405 f10)"',
    '"5色单帧 (750/650/560/488/405 f1)"': '"5-color single frame (750/650/560/488/405 f1)"',
    '"Fiducial + 4色 z-stack (405f1 750/650/560/405 f10)"': '"Fiducial + 4-color z-stack (405f1 750/650/560/405 f10)"',
    '"Fiducial + 5色 z-stack (405f1 750/650/560/488/405 f10)"': '"Fiducial + 5-color z-stack (405f1 750/650/560/488/405 f10)"',
    '"MERFISH 显微镜参数设置"': '"MERFISH Setup"',
    '"MERFISH 显微镜参数设置工具"': '"MERFISH Microscope Setup"',
    '"Z 扫描 (hardware_z_scan / z_offsets)"': '"Z scan (hardware_z_scan / z_offsets)"',
    '"\\n\\n仍然保存?"': '"\\n\\nSave anyway?"',
    '"settings 文件中的所有参数。双击「值」可修改；这里的修改与「②」页同步。"':
        '"Every parameter in the settings file. Double-click a value to edit it; changes stay in sync with tab 2."',
    '"speed 必须是数字"': '"Speed must be a number"',
    '"x 偏移"': '"x offset"',
    '"y 偏移"': '"y offset"',
    '"z 步长 (µm)"': '"z step (µm)"',
    '"z 起点 (µm)"': '"z start (µm)"',
    '"z-stack 之间用 \', \' 分隔 (与原文件格式一致)，相邻的单帧之间用 \',\'。"':
        '"z-stacks are separated by \', \' (matching the original files); adjacent single frames by \',\'."',
    '"z_offsets 与自动规则不一致，已关闭自动生成并保留原值"':
        '"z_offsets do not match the auto rule, so auto-generate was turned off and the original values were kept"',
    '"z_offsets 格式错误 (应为逗号分隔的数字)"': '"Invalid z_offsets (expected comma-separated numbers)"',
    '"z_offsets 格式错误"': '"Invalid z_offsets"',
    '"↑ 上移"': '"↑ Up"',
    '"↓ 下移"': '"↓ Down"',
    '"① 拍摄序列 Shutters / Z"': '"1  Sequence (shutters / Z)"',
    '"② 显微镜参数 Settings"': '"2  Microscope settings"',
    '"③ 全部参数 (高级)"': '"3  All parameters (advanced)"',
    '"④ 流控 Kilroy"': '"4  Fluidics (Kilroy)"',
    '"✎ 更新所选"': '"✎ Update selected"',
    '"✕ 删除"': '"✕ Delete"',
    '"⬇ 一键导出 shutters + settings…"': '"⬇ Export shutters + settings…"',
    '"不扫 Z (全部为起点)"': '"No Z scan (all at start)"',
    '"以下文件已存在，覆盖?\\n\\n"': '"These files already exist. Overwrite?\\n\\n"',
    '"保存 settings…"': '"Save settings…"',
    '"保存 shutters…"': '"Save shutters…"',
    '"保存"': '"Save"',
    '"值"': '"Value"',
    '"全部 = 1"': '"All = 1"',
    '"其他阀门"': '"Other valves"',
    '"其余相机参数 (ROI、binning、trigger…) 在「③ 全部参数」里修改"':
        '"Other camera parameters (ROI, binning, trigger…) are in tab 3, All parameters"',
    '"内置默认模板 (Dsk-650s10-560s10-488s10-405s10-U2OS)"': '"Built-in default template (Dsk-650s10-560s10-488s10-405s10-U2OS)"',
    '"删除"': '"Delete"',
    '"前缀 (Dsk / Epi …)"': '"Prefix (Dsk / Epi …)"',
    '"功率 Power"': '"Power"',
    '"功率"': '"Power"',
    '"协议 Protocols"': '"Protocols"',
    '"协议"': '"protocol"',
    '"协议列表"': '"Protocol list"',
    '"协议名格式"': '"Protocol name format"',
    '"协议名称:"': '"Protocol name:"',
    '"单帧步骤 (如 405 fiducial) 固定在 z 起点；多帧步骤做 z-stack。"':
        '"Single-frame steps (e.g. 405 fiducial) stay at z start; multi-frame steps take a z-stack."',
    '"参数"': '"Parameter"',
    '"双击单元格修改名称 / 端口 (port)。重命名会同步更新协议中的引用。"':
        '"Double-click a cell to edit the name or port. Renaming also updates references in protocols."',
    '"发现问题"': '"Problems found"',
    '"另存为…"': '"Save as…"',
    '"同名协议会被覆盖。{n} 代表轮次号。"': '"Protocols with the same name are overwritten. {n} stands for the round number."',
    '"名称 (如 Flow 1.5 ml/min):"': '"Name (e.g. Flow 1.5 ml/min):"',
    '"名称 (如 Set Hyb 17):"': '"Name (e.g. Set Hyb 17):"',
    '"名称"': '"Name"',
    '"命令"': '"Command"',
    '"在 Treeview 单元格上原地编辑。column 是列名。"': '"Edit a Treeview cell in place. column is the column name."',
    '"复制"': '"Duplicate"',
    '"导出完成"': '"Export complete"',
    '"尝试从已有 z_offsets 推断 (起点, 步长, 模式)。失败返回 None。"':
        '"Try to infer (start, step, mode) from existing z_offsets. Returns None on failure."',
    '"就绪"': '"Ready"',
    '"已存在同名协议"': '"A protocol with that name already exists"',
    '"已存在同名命令"': '"A command with that name already exists"',
    '"已载入"': '"Loaded"',
    '"帧数 Frames"': '"Frames"',
    '"帧数"': '"Frames"',
    '"帧数必须是 ≥1 的整数，功率必须是数字"': '"Frames must be an integer ≥ 1 and power must be a number"',
    '"帧范围"': '"Frame range"',
    '"常用:"': '"Common:"',
    '"开始时间"': '"Start time"',
    '"开泵命令"': '"Pump command"',
    '"当前 z_offsets (float 列表)，解析失败返回 None。"': '"Current z_offsets as a list of floats, or None if they cannot be parsed."',
    '"当前物镜"': '"Active objective"',
    '"当前物镜的 µm/pixel 不是数字"': '"µm/pixel of the active objective is not a number"',
    '"影片名包含样品标签"': '"Include sample tag in movie name"',
    '"影片文件名 film/filename"': '"Movie name (film/filename)"',
    '"影片文件名为空"': '"Movie name is empty"',
    '"往返 serpentine"': '"Serpentine (up, down, …)"',
    '"恢复"': '"Reset"',
    '"恢复内置模板"': '"Reset to built-in template"',
    '"打开 Kilroy 协议文件"': '"Open Kilroy protocol file"',
    '"打开 Kilroy…"': '"Open Kilroy…"',
    '"打开 settings 文件"': '"Open settings file"',
    '"打开 settings…"': '"Open settings…"',
    '"打开 shutters 文件"': '"Open shutters file"',
    '"打开 shutters…"': '"Open shutters…"',
    '"扫描方式"': '"Scan mode"',
    '"批量生成 (杂交轮次 / Prime)"': '"Generate (hyb rounds / Prime)"',
    '"把快速表单 + 序列派生值写回 settings 树。"': '"Write the quick form and the sequence-derived values back into the settings tree."',
    '"拍摄序列为空"': '"The sequence is empty"',
    '"按 HAL / Kilroy 原文件格式写出: ISO-8859-1 编码, Windows 换行."':
        '"Write in the original HAL / Kilroy format: ISO-8859-1 encoding, Windows line endings."',
    '"按模板批量生成杂交轮次协议"': '"Generate hybridization-round protocols from a template"',
    '"提示"': '"Note"',
    '"提示: 选中一行后修改上面的字段再点「更新所选」，或直接双击表格单元格修改"':
        '"Tip: select a row, change the fields above and click Update selected, or double-click a cell to edit it"',
    '"数字 -> 简洁字符串 (2.4000000000000004 -> \'2.4\', 4.0 -> \'4\')."':
        '"Number -> compact string (2.4000000000000004 -> \'2.4\', 4.0 -> \'4\')."',
    '"文件命名"': '"File naming"',
    '"新名称:"': '"New name:"',
    '"新建"': '"New"',
    '"新建协议"': '"New protocol"',
    '"新建泵命令"': '"New pump command"',
    '"新建阀门命令"': '"New valve command"',
    '"时序预览 (色块 = 每帧激光, 折线 = z 偏移)"': '"Timing preview (blocks = laser per frame, line = z offset)"',
    '"时长 (s)"': '"Duration (s)"',
    '"时长"': '"Duration"',
    '"时长必须是数字 (秒)"': '"Duration must be a number (seconds)"',
    '"曝光时间 exposure_time (s)"': '"Exposure time (s)"',
    '"曝光时间无效"': '"Invalid exposure time"',
    '"曝光步骤 (按顺序执行，每一步 = 一个激光 × N 帧)"': '"Exposure steps (run in order; each step = one laser × N frames)"',
    '"最后阀门"': '"Last valve"',
    '"杂交瓶数 N"': '"Hyb bottles N"',
    '"样品标签"': '"Sample tag"',
    '"根据序列自动生成 z_offsets"': '"Auto-generate z_offsets from the sequence"',
    '"检查结果"': '"Check results"',
    '"检查错误"': '"Check for errors"',
    '"模板:"': '"Template:"',
    '"模板协议"': '"Template protocol"',
    '"模板对应轮次 n ="': '"Template round n ="',
    '"步骤 (双击单元格修改)"': '"Steps (double-click a cell to edit)"',
    '"每个 Hyb 阀门时长 (s)"': '"Duration per Hyb valve (s)"',
    '"每次从下往上 always up"': '"Always bottom-up"',
    '"没有发现问题 ✓"': '"No problems found ✓"',
    '"注意"': '"Warning"',
    '"泵命令 Pump commands"': '"Pump commands"',
    '"泵命令"': '"pump command"',
    '"清空"': '"Clear"',
    '"激光 Laser"': '"Laser"',
    '"激光"': '"Laser"',
    '"物镜 / Mosaic"': '"Objective / Mosaic"',
    '"生成 Prime 协议 (冲洗所有管路)"': '"Generate Prime protocol (flush all lines)"',
    '"生成 Prime 协议"': '"Generate Prime protocol"',
    '"生成名为「Prime N + 4」的协议: 开泵 → Set Hyb 1…N → 其他阀门 → 最后阀门 → Stop Flow"':
        '"Creates a protocol named \\"Prime N + 4\\": pump on → Set Hyb 1…N → other valves → last valve → Stop Flow"',
    '"生成杂交协议"': '"Generate hyb protocols"',
    '"生成轮次"': '"Rounds"',
    '"用内置模板替换当前 settings 参数? (拍摄序列不变)"': '"Replace the current settings with the built-in template? (The sequence is kept.)"',
    '"相机 camera1"': '"Camera (camera1)"',
    '"确定清空所有步骤?"': '"Remove all steps?"',
    '"确认生成"': '"Confirm"',
    '"端口号必须是整数"': '"Port must be an integer"',
    '"类型"': '"Type"',
    '"类型错误"': '"Type error"',
    '"自动"': '"Auto"',
    '"覆盖"': '"Overwrite"',
    '"覆盖确认"': '"Confirm overwrite"',
    '"说明: 复制模板协议，把其中的「阀门命令格式(n=模板轮次)」替换为对应轮次；"':
        '"Copies the template protocol and replaces its valve command (format with n = template round) with each round\'s. "',
    '"请先在表格中选中一行"': '"Select a row in the table first"',
    '"请先选择或新建一个协议"': '"Select or create a protocol first"',
    '"请检查数字"': '"Check the numbers"',
    '"请检查轮次号与格式 (格式中用 {n} 表示轮次)"': '"Check the round numbers and formats (use {n} for the round number)"',
    '"请选择模板协议"': '"Choose a template protocol"',
    '"读取失败"': '"Could not read file"',
    '"输入错误"': '"Invalid input"',
    '"返回每个 step 对应的 z 列表。单帧 step (如 405 fiducial) 固定在 z 起点。"':
        '"Return the list of z values for each step. Single-frame steps (e.g. 405 fiducial) stay at z start."',
    '"选择导出文件夹"': '"Choose export folder"',
    '"通道 Ch"': '"Channel"',
    '"重命名"': '"Rename"',
    '"重命名协议"': '"Rename protocol"',
    '"错误"': '"Error"',
    '"阀门命令 Valve commands"': '"Valve commands"',
    '"阀门命令"': '"valve command"',
    '"阀门命令格式"': '"Valve command format"',
    '"阀门数量 num_valves:"': '"Number of valves (num_valves):"',
    '"阀门数量"': '"Number of valves"',
    '"阀门数量…"': '"Number of valves…"',
    '"预设:"': '"Preset:"',
    '"默认激光功率 illumination/default_power (0–1)"': '"Default laser power (illumination/default_power, 0–1)"',
    '"＋ 新建"': '"＋ New"',
    '"＋ 泵步骤"': '"＋ Pump step"',
    '"＋ 添加"': '"＋ Add"',
    '"＋ 阀门步骤"': '"＋ Valve step"',
    '"＋405 fiducial 到开头"': '"＋405 fiducial at start"',
    'f"  film/frames = {nfr}      focuslock/hardware_z_scan/z_offsets = {len(zv or [])} 个值\\n"':
        'f"  film/frames = {nfr}      focuslock/hardware_z_scan/z_offsets = {len(zv or [])} values\\n"',
    'f"  保存为: {self.settings_filename()}"': 'f"  Saved as: {self.settings_filename()}"',
    'f"\\n\\n⚠ 以下阀门命令尚未定义，请到「阀门命令」页添加:\\n"':
        'f"\\n\\n⚠ These valve commands are not defined yet; add them on the Valve commands tab:\\n"',
    'f"\\n\\n其中 {len(to_overwrite)} 个已存在，将被覆盖。"': 'f"\\n\\n{len(to_overwrite)} of them already exist and will be overwritten."',
    'f"\\n\\n注意: 有 {used} 个协议步骤引用了它!"': 'f"\\n\\nWarning: {used} protocol steps use it!"',
    'f"\\n… 共 {len(probs)} 条"': 'f"\\n… {len(probs)} in total"',
    'f"shutters 文件: {shutters_filename(self.steps)}     settings 文件: {self.settings_filename()}"':
        'f"Shutters file: {shutters_filename(self.steps)}     Settings file: {self.settings_filename()}"',
    'f"z_offsets 数量 ({len(zv)}) 与总帧数 ({total_frames(self.steps)}) 不一致"':
        'f"Number of z_offsets ({len(zv)}) does not match total frames ({total_frames(self.steps)})"',
    'f"{LASERS[i][1]} nm 功率 {p} 不在 0–1 之间"': 'f"{LASERS[i][1]} nm power {p} is not between 0 and 1"',
    'f"{LASERS[i][1]} nm 功率不是数字"': 'f"{LASERS[i][1]} nm power is not a number"',
    'f"{el.tag} 需要 {typ}，输入为: {v}"': 'f"{el.tag} needs a {typ}, got: {v}"',
    'f"{kind}名称重复: {it[0]}"': 'f"Duplicate {kind} name: {it[0]}"',
    'f"{len(k.pumps)} 个泵命令, {k.num_valves} 个阀门"': 'f"{len(k.pumps)} pump commands, {k.num_valves} valves"',
    'f"{name}    —   {len(k.protocols)} 个协议, {len(k.valves)} 个阀门命令, "':
        'f"{name}    —   {len(k.protocols)} protocols, {len(k.valves)} valve commands, "',
    'f"✓ z 数量 {len(zv)} = 总帧数 {nfr}"': 'f"✓ {len(zv)} z values = {nfr} total frames"',
    'f"✗ z 数量 {len(zv)} ≠ 总帧数 {nfr}"': 'f"✗ {len(zv)} z values ≠ {nfr} total frames"',
    'f"「{name}」总时长 {fmt_duration(tt)}"': 'f"\\"{name}\\" total duration {fmt_duration(tt)}"',
    'f"不是 Kilroy 文件 (根节点是 <{root.tag}>)"': 'f"Not a Kilroy file (root element is <{root.tag}>)"',
    'f"不是 shutters 文件 (根节点是 <{root.tag}>，应为 <repeat>)"': 'f"Not a shutters file (root element is <{root.tag}>, expected <repeat>)"',
    'f"以下参数由「① 拍摄序列」自动填写:\\n"': 'f"Filled in automatically from tab 1 (Sequence):\\n"',
    'f"共 {len(self.steps)} 步，{nfr} 帧{tstr}"': 'f"{len(self.steps)} steps, {nfr} frames{tstr}"',
    'f"删除协议「{self.kilroy.protocols[i][0]}」?"': 'f"Delete protocol \\"{self.kilroy.protocols[i][0]}\\"?"',
    'f"删除泵命令「{name}」?"': 'f"Delete pump command \\"{name}\\"?"',
    'f"删除阀门命令「{name}」?"': 'f"Delete valve command \\"{name}\\"?"',
    'f"协议 \'{pname}\' 第 {i} 步: 时长 \'{dur}\' 不是数字"': 'f"Protocol \'{pname}\' step {i}: duration \'{dur}\' is not a number"',
    'f"协议 \'{pname}\' 第 {i} 步: 未定义的泵命令 \'{cmd}\'"': 'f"Protocol \'{pname}\' step {i}: undefined pump command \'{cmd}\'"',
    'f"协议 \'{pname}\' 第 {i} 步: 未定义的阀门命令 \'{cmd}\'"': 'f"Protocol \'{pname}\' step {i}: undefined valve command \'{cmd}\'"',
    'f"协议「{name}」已存在，覆盖?"': 'f"Protocol \\"{name}\\" already exists. Overwrite?"',
    'f"如果这是 shutters 文件，请在「①」页用「打开 shutters」。"': 'f"If this is a shutters file, use Open shutters on tab 1."',
    'f"将生成 {b - a + 1} 个协议: {pfmt.format(n=a)} … {pfmt.format(n=b)}"':
        'f"This will create {b - a + 1} protocols: {pfmt.format(n=a)} … {pfmt.format(n=b)}"',
    'f"已保存 Kilroy: {path}"': 'f"Saved Kilroy: {path}"',
    'f"已保存 settings: {path}"': 'f"Saved settings: {path}"',
    'f"已保存 shutters: {path}"': 'f"Saved shutters: {path}"',
    'f"已修改 {el.tag} = {v}"': 'f"Changed {el.tag} = {v}"',
    'f"已写入 {folder}:\\n\\n"': 'f"Wrote to {folder}:\\n\\n"',
    'f"已同时载入关联的 shutters 文件: {sh}"': 'f"Also loaded the linked shutters file: {sh}"',
    'f"已导出到 {folder}"': 'f"Exported to {folder}"',
    'f"已应用预设: {name}"': 'f"Applied preset: {name}"',
    'f"已生成 {pfmt.format(n=a)} … {pfmt.format(n=b)}"': 'f"Generated {pfmt.format(n=a)} … {pfmt.format(n=b)}"',
    'f"已生成协议「{name}」({fmt_duration(k.protocol_seconds(steps))})"':
        'f"Generated protocol \\"{name}\\" ({fmt_duration(k.protocol_seconds(steps))})"',
    'f"已载入 Kilroy: {path}"': 'f"Loaded Kilroy: {path}"',
    'f"已载入 settings: {path}"': 'f"Loaded settings: {path}"',
    'f"已载入 shutters: {path}"': 'f"Loaded shutters: {path}"',
    'f"已重命名 \'{old}\' → \'{v}\'，并更新了 {cnt} 处协议引用"': 'f"Renamed \'{old}\' → \'{v}\' and updated {cnt} protocol references"',
    'f"文件中 <frames>={file_frames}，但事件总帧数={total_frames(steps)}"':
        'f"File says <frames>={file_frames}, but the events add up to {total_frames(steps)} frames"',
    'f"无效的值: {v}"': 'f"Invalid value: {v}"',
    'f"未找到关联的 shutters 文件 {sh}，拍摄序列保持不变"': 'f"Linked shutters file {sh} not found; the sequence was left unchanged"',
    'f"根节点是 <{root.tag}>，不是 <settings>。\\n"': 'f"Root element is <{root.tag}>, not <settings>.\\n"',
    'f"模板协议「{tmpl[0]}」中没有找到阀门命令「{tvalve}」"': 'f"Template protocol \\"{tmpl[0]}\\" has no valve command \\"{tvalve}\\""',
    'f"通道 {e[\'channel\']} 的 on={e[\'on\']} 与上一事件不连续 (预期 {t})"':
        'f"Channel {e[\'channel\']}: on={e[\'on\']} does not follow the previous event (expected {t})"',
    'f"通道 {e[\'channel\']} 的帧数 {n} 不是整数，已四舍五入"': 'f"Channel {e[\'channel\']}: {n} frames is not an integer, rounded"',
    'f"阀门 {v}"': 'f"Valve {v}"',
    'f"，约 {nfr * exp:.1f} s / 视野"': 'f", about {nfr * exp:.1f} s per field of view"',
}

# Comments, docstrings and other free text (plain substring replacement, applied after LIT)
FREE = {
    "MERFISH 显微镜参数设置工具 (MERFISH microscope setup GUI)": "MERFISH microscope setup GUI (English version)",
    "编辑 / 生成三类文件:": "Edits / generates three kinds of files:",
    "1. HAL shutters 序列文件  ": "1. HAL shutters sequence ",
    "2. HAL settings 参数文件  ": "2. HAL settings file      ",
    "3. Kilroy 流控协议文件    ": "3. Kilroy fluidics file   ",
    "只依赖 Python 标准库 (tkinter)，Windows / macOS / Linux 均可运行:": "Uses only the Python standard library (tkinter); runs on Windows / macOS / Linux:",
    "python merfish_setup_gui.py": "python merfish_setup_gui_en.py",
    "# 激光通道配置: (HAL channel 编号, 波长, 预览颜色)": "# Laser channels: (HAL channel index, wavelength, preview color)",
    "# 如果显微镜的通道顺序不同，只需改这里。": "# If a microscope uses a different channel order, change it here only.",
    "# 内置默认 settings 模板 (来自 Dsk-650s10-560s10-488s10-405s10-U2OS.xml)": "# Built-in default settings template (from Dsk-650s10-560s10-488s10-405s10-U2OS.xml)",
    "# 通用工具": "# Utilities",
    "# Shutters 序列 (model)": "# Shutters sequence (model)",
    "# Settings (model): 直接保留 ElementTree，保证所有参数原样保存": "# Settings (model): keeps the ElementTree so every parameter is saved unchanged",
    "# Kilroy (model)": "# Kilroy (model)",
    "# GUI 小部件": "# GUI widgets",
    "# 主程序": "# Main application",
    "# 步骤编辑器": "# step editor",
    "# --- 预设 + 文件 ---": "# --- presets + files ---",
    "# --- 步骤表 ---": "# --- step table ---",
    "# --- Z 扫描 ---": "# --- Z scan ---",
    "# --- 预览 ---": "# --- preview ---",
    "# 命名": "# naming",
    "# 相机": "# camera",
    "# 激光功率": "# laser power",
    "# 物镜 / mosaic": "# objective / mosaic",
    "# 序列派生": "# derived from the sequence",
    "# 关联的 shutters 文件": "# linked shutters file",
    "# z offsets: 能推断就自动，否则保留原文": "# z offsets: auto if the rule can be inferred, else keep the text",
    "# 影片名": "# movie name",
    "# 放在最后一个同格式协议之后": "# insert after the last protocol with the same name format",
}


# ---- additions: Dave tab, presets, layout tweaks ----
LIT.update({
    'f"{name}    —   {len(k.protocols)} 个协议, {len(k.valves)} 个阀门命令, "':
        'f"{name}  —  {len(k.protocols)} protocols · {len(k.valves)} valve cmds · "',
    'f"{len(k.pumps)} 个泵命令, {k.num_valves} 个阀门"': 'f"{len(k.pumps)} pump cmds · {k.num_valves} valves"',
    '"settings 名去掉样品标签 = Dave 里的影片名 (\'Dsk-405s1-750s6-U2OS\' -> \'Dsk-405s1-750s6\')."':
        '"Settings name without the sample tag = movie name in Dave (\'Dsk-405s1-750s6-U2OS\' -> \'Dsk-405s1-750s6\')."',
    '"成像一次"': '"Image once"',
    '"杂交循环"': '"Hyb loop"',
    '"make_round_values 的逆运算。识别不了返回 None。"': '"Inverse of make_round_values. Returns None if no pattern is found."',
    'f"不是 Dave 流程文件 (根节点是 <{root.tag}>，应为 <recipe>)"': 'f"Not a Dave recipe (root element is <{root.tag}>, expected <recipe>)"',
    '"缺少 <command_sequence>"': '"Missing <command_sequence>"',
    'f"loop_variable 中有不支持的内容 <{ch.tag}>"': 'f"Unsupported content in loop_variable: <{ch.tag}>"',
    'f"movie 中有本工具不支持的设置: {\', \'.join(\'<%s>\' % e for e in extra)}"':
        'f"This movie uses settings the tool does not support: {\', \'.join(\'<%s>\' % e for e in extra)}"',
    '"不支持嵌套的杂交循环"': '"Nested hyb loops are not supported"',
    'f"循环「{name}」里应正好有一个成像步骤，实际 {len(inner)} 个"': 'f"Loop \\"{name}\\" should contain exactly one imaging step, found {len(inner)}"',
    'f"找不到循环「{name}」的 loop_variable 取值"': 'f"No loop_variable values found for loop \\"{name}\\""',
    'f"本工具不支持的 Dave 元素 <{ch.tag}>"': 'f"Unsupported Dave element <{ch.tag}>"',
    '"流程里没有任何阶段"': '"The recipe has no stages"',
    'f"成像位置文件 ({self.positions_loop}) 为空，运行前需要在 Dave 里指定"':
        'f"The imaging positions file ({self.positions_loop}) is empty; set it in Dave before running"',
    '"唤醒时长不是整数 (ms)"': '"Wakeup duration is not an integer (ms)"',
    'f"阶段 {i}: 没有指定 settings"': 'f"Stage {i}: no settings chosen"',
    'f"阶段 {i}: 帧数「{st[\'length\']}」无效"': 'f"Stage {i}: invalid frame count \\"{st[\'length\']}\\""',
    'f"阶段 {i}: 帧数 {n} 与 settings「{st[\'params\']}」的 {f} 帧不一致"':
        'f"Stage {i}: {n} frames does not match the {f} frames of settings \\"{st[\'params\']}\\""',
    'f"阶段 {i}: 杂交循环没有任何轮次"': 'f"Stage {i}: the hyb loop has no rounds"',
    'f"阶段 {i}: 当前 Kilroy 文件里没有这些协议: {\', \'.join(missing)}"':
        'f"Stage {i}: these protocols are not in the current Kilroy file: {\', \'.join(missing)}"',
    '"U2OS hyb · U2OS 1 轮成像 + 14 轮杂交"': '"U2OS hyb · U2OS 1 imaging round + 14 hyb rounds"',
    '"载入预设:"': '"Preset:"',
    '"⑤ 自动化 Dave"': '"5  Automation (Dave)"',
    '"打开 Dave…"': '"Open Dave…"',
    '"流程预设:"': '"Recipe preset:"',
    '"流程编辑"': '"Recipe"',
    '"XML 预览"': '"XML preview"',
    '"全局"': '"Global"',
    '"唤醒时长 wakeup (ms)"': '"Wakeup (ms)"',
    '"唤醒位置文件"': '"Wakeup positions file"',
    '"唤醒 settings / 帧数"': '"Wakeup settings / frames"',
    '"成像位置文件"': '"Imaging positions file"',
    '"位置文件是显微镜电脑上的路径 (如 D:\\\\…\\\\positions.txt)；可以留空，运行前在 Dave 里指定。"':
        '"Positions files are paths on the microscope PC (e.g. D:\\\\…\\\\positions.txt); you can leave them empty and set them in Dave before running."',
    '"流程阶段 (按顺序执行；杂交循环 = 每轮先跑 Kilroy 协议，再唤醒、成像)"':
        '"Stages (run in order; each hyb round: Kilroy protocols → wakeup → imaging)"',
    '"轮次 / 流控协议"': '"Rounds / fluidics"',
    '"唤醒对焦"': '"Wakeup focus"',
    '"影片名"': '"Movie name"',
    '"对焦"': '"Focus"',
    '"轮次"': '"Rounds"',
    '"每轮流控协议"': '"Protocols per round"',
    '"  对焦次数"': '"  Focus checks"',
    '"成像前唤醒，对焦次数"': '"Wakeup first, focus checks"',
    '"选择 settings 后会自动填写影片名和帧数；协议用逗号分隔，{n} 代表轮次号。"':
        '"Choosing settings fills in movie name and frames. Protocols: comma-separated, {n} = round number."',
    '"+ 添加阶段"': '"+ Add stage"',
    '"填入 ② 页当前 settings"': '"Use current settings (tab 2)"',
    'f"自定义 {len(st[\'values\'])} 轮"': 'f"Custom, {len(st[\'values\'])} rounds"',
    '"(未保存)"': '"(unsaved)"',
    'f"共 {len(d.stages)} 个阶段，{n_img} 次成像 (每次遍历所有位置)，{n_rounds} 轮杂交"':
        'f"{len(d.stages)} stages, {n_img} imaging passes (each over all positions), {n_rounds} hyb rounds"',
    'f"；流控总时长约 {fmt_duration(fl)}"': 'f"; fluidics about {fmt_duration(fl)} in total"',
    '" (部分协议在 Kilroy 中找不到)"': '" (some protocols are not in Kilroy)"',
    '"settings 文件里的 film/frames (缓存)。不是 settings 文件返回 None。"':
        '"film/frames from a settings file (cached). Returns None if it is not a settings file."',
    '"settings 名对应的帧数: ② 页当前设置 > 内置预设 > 文件夹中的文件。未知返回 None。"':
        '"Frames for a settings name: current tab-2 settings > built-in presets > files in the folder. None if unknown."',
    '"请选择或填写 settings"': '"Choose or type a settings name"',
    '"帧数必须是 ≥1 的整数"': '"Frames must be an integer ≥ 1"',
    '"请检查轮次号与流控协议格式 (用 {n} 表示轮次)"': '"Check the round numbers and protocol format (use {n} for the round number)"',
    '"每轮流控协议不能为空"': '"Protocols per round cannot be empty"',
    '"已填入当前 settings；点「添加阶段」或「更新所选」应用到流程"':
        '"Filled in the current settings; click Add stage or Update selected to apply it"',
    '"载入流程预设"': '"Load recipe preset"',
    'f"用预设「{name}」替换当前 Dave 流程?"': 'f"Replace the current Dave recipe with preset \\"{name}\\"?"',
    'f"已载入流程预设: {name}"': 'f"Loaded recipe preset: {name}"',
    '"打开 Dave 流程文件"': '"Open Dave recipe"',
    'f"本工具只支持「成像 + 杂交循环」结构的 Dave 流程。"': 'f"This tool supports Dave recipes made of imaging stages and hyb loops only."',
    'f"已载入 Dave: {path}"': 'f"Loaded Dave: {path}"',
    'f"已保存 Dave: {path}"': 'f"Saved Dave: {path}"',
    '"载入预设"': '"Load preset"',
    'f"载入预设「{p[\'name\']}」?\\n\\n这会替换当前的拍摄序列和 settings 参数。"':
        'f"Load preset \\"{p[\'name\']}\\"?\\n\\nThis replaces the current sequence and settings."',
    'f"预设 {preset_label(p)}"': 'f"Preset {preset_label(p)}"',
    'f"已载入预设: {preset_label(p)}"': 'f"Loaded preset: {preset_label(p)}"',
})
FREE.pop("编辑 / 生成三类文件:", None)
FREE.update({
    "编辑 / 生成四类文件:": "Edits / generates four kinds of files:",
    "4. Dave 自动化流程文件    ": "4. Dave automation recipe ",
    "# 内置 settings 预设。每个预设 = 拍摄序列 + z 规则 + 相对内置模板改动过的参数。":
        "# Built-in settings presets. Each preset = sequence + z rule + parameters changed from the built-in template.",
    "# film/filename、film/frames、illumination/shutters、z_offsets 都由序列自动生成。":
        "# film/filename, film/frames, illumination/shutters and z_offsets are generated from the sequence.",
    "# z = (起点 µm, 步长 µm, Z_MODES 序号)": "# z = (start µm, step µm, index into Z_MODES)",
    "(出现在该 section 之前)": "(comments that appear before that section)",
    "# Dave 自动化流程 (model)": "# Dave automation recipe (model)",
    "# 支持实验室常用的 MERFISH 结构:": "# Supports the lab's usual MERFISH structure:",
    "#   [唤醒] → 成像 (Movie Loop 1, 遍历所有位置)": "#   [wakeup] → imaging (Movie Loop 1, over all positions)",
    "#   杂交循环 (Hybridize loop k): 每轮 Kilroy 协议 → [唤醒] → 成像":
        "#   hyb loop (Hybridize loop k): each round Kilroy protocols → [wakeup] → imaging",
    "# 焦点在 combobox 下拉列表里": "# focus is in the combobox drop-down list",
    "        # 全局\n": "        # global\n",
    "        # 阶段表\n": "        # stage table\n",
    "# 自定义轮次: 保持不变": "# custom rounds: keep as they are",
    "＋ ": "+ ",
    "＋405": "+ 405",
})

# ---- additions: Kilroy presets, Dave templates ----
LIT.update({
    '"U2OS hyb · 流动时间更长"': '"U2OS hyb · longer flow times"',
    '"模板 · 1 轮成像 + 14 轮杂交 (② 页当前 settings)"': '"Template · 1 imaging round + 14 hyb rounds (current settings)"',
    '"模板 · 只成像一次，不跑流控 (② 页当前 settings)"': '"Template · image once, no fluidics (current settings)"',
    '"流控预设:"': '"Fluidics preset:"',
    'f"这个流程配套的流控预设是「{kp}」。\\n\\n同时把 ④ 页的 Kilroy 换成它?"':
        'f"This recipe goes with the fluidics preset \\"{kp}\\".\\n\\nAlso switch the Kilroy protocols on tab 4 to it?"',
    '"配套流控"': '"Matching fluidics"',
    'f"用预设「{name}」替换当前 Kilroy 协议?\\n\\n(不会改动磁盘上的文件，保存时再选位置。)"':
        'f"Replace the current Kilroy protocols with preset \\"{name}\\"?\\n\\n(Files on disk are not changed; you choose where to save.)"',
    '"载入流控预设"': '"Load fluidics preset"',
    'f"已载入流控预设: {name}"': 'f"Loaded fluidics preset: {name}"',
    'f"预设 {self.kilroy_preset_name} (未保存)"': 'f"Preset {self.kilroy_preset_name} (unsaved)"',
})
FREE.update({
    "# 内置 Kilroy 预设: 按实验室的阀门接法和协议模板生成，只有流动/静置时间不同。":
        "# Built-in Kilroy presets: generated from the lab's valve wiring and protocol templates; only flow/wait times differ.",
    "cleave = (TCEP 流, TCEP 静置, 洗 流, 洗 静置) 秒;": "cleave = (TCEP flow, TCEP wait, wash flow, wash wait) in seconds;",
    "hyb = (Hyb 流, Hyb 静置, 洗1 流, 洗1 静置, Readout 流, Readout 静置, 洗2 流, 洗2 静置, Image 流, Image 静置) 秒。":
        "hyb = (hyb flow, hyb wait, wash1 flow, wash1 wait, readout flow, readout wait, wash2 flow, wash2 wait, image flow, image wait) in seconds.",
    "# 阀门串联: 阀门 1 的 5–7 口 = Hyb 1–3；阀门 2/3/4 的 1–7 口 = Hyb 4–10 / 11–17 / 18–24":
        "# Daisy-chained valves: valve 1 ports 5–7 = Hyb 1–3; valves 2/3/4 ports 1–7 = Hyb 4–10 / 11–17 / 18–24",
    "用 ② 页当前 settings 的通用流程: 成像一次 [+ n 轮杂交]。ctx = {'settings', 'movie', 'frames'}。":
        "Generic recipe using the current tab-2 settings: image once [+ n hyb rounds]. ctx = {'settings', 'movie', 'frames'}.",
    "# make(ctx) -> DaveRecipe；kilroy = 配套的 Kilroy 预设 (可选)": "# make(ctx) -> DaveRecipe; kilroy = matching Kilroy preset (optional)",
    "# 启动时载入的就是这个流程": "# this is the recipe loaded at startup",
    "# 启动时: 用内置预设代替": "# at startup: fall back to the built-in preset",
    "# 手动打开失败: 保留当前内容": "# opened by hand: keep the current content",
})

src = open(SRC, encoding="utf-8").read()
for k in sorted(LIT, key=len, reverse=True):
    if k not in src:
        print("LIT NOT FOUND:", k)
    src = src.replace(k, LIT[k])
for k, v in FREE.items():
    if k not in src:
        print("FREE NOT FOUND:", k)
    src = src.replace(k, v)
left = [(i + 1, l) for i, l in enumerate(src.splitlines()) if re.search(r"[一-鿿　-〿！-，：-？]", l)]
for i, l in left:
    print("REMAINING", i, l.strip()[:120])
if left:
    sys.exit(f"{len(left)} lines still contain Chinese; add them to LIT / FREE. {DST} was not written.")
open(DST, "w", encoding="utf-8").write(src)
print("written", DST)
