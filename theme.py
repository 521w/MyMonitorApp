"""
全局主题配色 - 深色赛博朋克风格
所有颜色值为 Kivy 格式 (R, G, B, A)，范围 0~1
"""

# ━━━ 背景色 ━━━
BG_DARK = (0.06, 0.06, 0.10, 1)       # 最深背景
BG_CARD = (0.10, 0.11, 0.16, 1)       # 卡片背景
BG_INPUT = (0.12, 0.13, 0.18, 1)      # 输入框背景
BG_HEADER = (0.08, 0.09, 0.14, 1)     # 标题栏背景

# ━━━ 强调色 ━━━
ACCENT = (0.0, 0.75, 0.95, 1)         # 青色主色调
ACCENT_DIM = (0.0, 0.55, 0.70, 1)     # 青色暗调
ACCENT_HEX = "00bff2"                  # 用于 markup

# ━━━ 功能色 ━━━
GREEN = (0.18, 0.75, 0.35, 1)         # 成功/安全
GREEN_HEX = "2ebf59"
YELLOW = (0.95, 0.70, 0.15, 1)        # 警告
YELLOW_HEX = "f2b326"
RED = (0.90, 0.25, 0.25, 1)           # 危险/错误
RED_HEX = "e64040"
PURPLE = (0.60, 0.35, 0.85, 1)        # 特殊信息
PURPLE_HEX = "9959d9"

# ━━━ 按钮色 ━━━
BTN_PRIMARY = (0.08, 0.50, 0.72, 1)   # 主要按钮
BTN_SUCCESS = (0.15, 0.58, 0.30, 1)   # 成功按钮
BTN_DANGER = (0.72, 0.20, 0.20, 1)    # 危险按钮
BTN_NEUTRAL = (0.22, 0.23, 0.30, 1)   # 中性按钮
BTN_WARN = (0.70, 0.50, 0.15, 1)      # 警告按钮

# ━━━ 文字色 ━━━
TEXT_PRIMARY = (0.90, 0.92, 0.95, 1)   # 主要文字
TEXT_DIM = (0.55, 0.58, 0.65, 1)       # 次要文字
TEXT_ACCENT = (0.40, 0.85, 1.0, 1)     # 强调文字

# ━━━ 字体大小 ━━━
FONT_XL = "16sp"
FONT_LG = "14sp"
FONT_MD = "13sp"
FONT_SM = "12sp"
FONT_XS = "11sp"

# ━━━ 圆角半径 ━━━
RADIUS_LG = [12]
RADIUS_MD = [8]
RADIUS_SM = [5]

# ━━━ 标签页图标 ━━━
ICONS = {
    'monitor':  '◈ 监控',
    'process':  '◉ 进程',
    'terminal': '▸ 终端',
    'log':      '◇ 日志',
    'logcat':   '◆ 系统',
    'toolbox':  '★ 工具',
}