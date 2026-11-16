# MERFISH 显微镜参数设置工具

```
python merfish_setup_gui.py       # 中文界面
python merfish_setup_gui_en.py    # English UI
```

只用 Python 标准库 (tkinter)，不需要安装任何包。显微镜电脑上装 storm-control 用的 Python 就能直接运行。

| 页面 | 作用 |
|---|---|
| ① 拍摄序列 | 编辑激光步骤 (激光 × 帧数 × 功率)，自动生成 `*_shutters_1cam.xml`、z_offsets，带时序预览 |
| ② 显微镜参数 | 前缀 (Dsk/Epi)、样品标签、曝光时间、相机/mosaic 翻转、物镜、默认激光功率 |
| ③ 全部参数 | settings 里的所有参数 (ROI、focuslock 等)，双击修改 |
| ④ 流控 Kilroy | 协议、阀门/泵命令的编辑；按模板批量生成 Hybridize N、Prime N + 4 |
| ⑤ 自动化 Dave | 编辑 Dave 流程: 唤醒 → 成像 → 杂交循环 (每轮 Kilroy 协议 → 唤醒 → 成像)，带 XML 预览 |

**常规流程**：顶部「载入预设」或「打开 settings…」→ 修改序列和参数 →「一键导出」→ 到 ⑤ 页把这些 settings 排进 Dave 流程并保存。

## 预设

- **settings 预设** (顶部「载入预设」): 实验室的 4 个 settings + U2OS hyb 的 2 个
  (`Dsk-405s1-750s6-650s6-405s6-U2OS`, `Dsk-405s1-750s6-650s6-560s6-U2OS`)。
  载入后再导出，得到的文件与原文件一致；唯一的区别是 U2OS hyb 文件里过时的 `film/filename` 会被改成正确的名字。
- **流控预设** (④ 页左上「流控预设」): 实验室标准 Kilroy 协议，以及 U2OS hyb 的版本 (流动/静置时间更长)。
  两者都按阀门接法和协议模板生成，与对应的原文件完全一致。载入预设不会改动磁盘上的文件。
- **Dave 流程预设** (⑤ 页左上「流程预设」):
  - U2OS hyb · U2OS 1 轮成像 + 14 轮杂交 (会询问是否同时载入配套的 U2OS hyb 流控预设)
  - 模板 · 1 轮成像 + 14 轮杂交 (用 ② 页当前 settings)
  - 模板 · 只成像一次，不跑流控 (用 ② 页当前 settings)

新增预设: 在 `merfish_setup_gui.py` 的 `SETTINGS_PRESETS` / `KILROY_PRESETS` / `DAVE_PRESETS` 里加一项，
然后运行 `python build_english_version.py` 更新英文版。

## Dave 页说明

- 支持的结构: 「成像一次」和「杂交循环」两种阶段，可以任意组合、排序。
  含有其他 Dave 指令 (如 delay、move_stage) 的流程文件会拒绝载入，而不会悄悄丢掉内容。
- 选择 settings 后自动填写影片名 (去掉样品标签) 和帧数；帧数和 settings 不一致、Kilroy 里找不到协议、
  位置文件为空都会提示。
- 流控总时长根据当前载入的 Kilroy 文件计算。

## 英文版

`merfish_setup_gui_en.py` 由中文版自动生成。修改中文版之后运行:

```
python build_english_version.py
```

脚本会列出还没有翻译的字符串；全部翻译之前不会写出英文文件。

## 其他

- 激光通道对应关系在 `merfish_setup_gui.py` 顶部的 `LASERS` 里 (0=750, 1=650, 2=560, 3=488, 4=405)。
- z 扫描规则：单帧步骤 (405 fiducial) 固定在 z 起点；多帧步骤从起点按步长做 z-stack，默认往返 (serpentine)，与现有文件一致。
- 保存时使用原文件的格式 (ISO-8859-1 编码，Windows 换行)。
- 在 Mac 上: `mamba activate cellpose && python merfish_setup_gui.py` (系统自带的 python3 的 Tk 无法打开窗口)。
