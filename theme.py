"""
全局主题配色 - 深色赛博朋克风格
所有颜色值为 Kivy 格式 (R, G, B, A)，范围 0~1
"""

# ============ 背景色 ============
BG_DARK    = (0, 0, 0, 1)
BG_CARD    = (0.1, 0.1, 0.1, 1)
BG_INPUT   = (0.2, 0.2, 0.2, 1)

# ============ 强调/状态色 (Kivy RGBA) ============
ACCENT     = (1, 0.5, 0, 1)
GREEN      = (0, 1, 0, 1)
YELLOW     = (1, 1, 0, 1)
RED        = (1, 0, 0, 1)
PURPLE     = (0.7, 0.4, 1, 1)

# ============ HEX 颜色 (给 Kivy markup 用) ============
ACCENT_HEX = "FF8000"
GREEN_HEX  = "00FF00"
YELLOW_HEX = "FFFF00"
RED_HEX    = "FF0000"
PURPLE_HEX = "B266FF"

# ============ 按钮色 ============
BTN_PRIMARY = (0, 0.5, 1, 1)
BTN_SUCCESS = (0, 1, 0.5, 1)
BTN_DANGER  = (1, 0, 0.5, 1)
BTN_NEUTRAL = (0.3, 0.3, 0.35, 1)
BTN_WARN    = (1, 0.7, 0, 1)

# ============ 文字色 ============
TEXT_PRIMARY = (1, 1, 1, 1)
TEXT_DIM     = (0.5, 0.5, 0.55, 1)

# ============ 字体大小 ============
FONT_XL = "20sp"
FONT_LG = "16sp"
FONT_MD = "14sp"
FONT_SM = "12sp"
FONT_XS = "10sp"

# ============ 圆角半径 ============
RADIUS_LG = [16]
RADIUS_MD = [10]

# ============ 图标路径 ============
ICONS = {
    "home": "path/to/icon/home.svg",
    "settings": "path/to/icon/settings.svg",
}