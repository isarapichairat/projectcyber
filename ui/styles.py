"""
HD Private Player - Design System & Styles
ศูนย์รวมค่าสี, ฟอนต์ และการตั้งค่าสไตล์สำหรับ UI ทั้งหมด
"""

# ==========================================
# Color Palette (ธีม Dark สุภาพ พรีเมียม)
# ==========================================
BG_DARK = "#0F172A"         # พื้นหลังหลักของหน้าต่าง (Deep Slate Dark)
PANEL_BG = "#1E293B"        # พื้นหลังส่วนควบคุมและ Header (Slate Card)
VIDEO_BG = "#020617"        # พื้นหลังสำหรับพื้นที่วิดีโอ (Pure Dark Black)
CONTROL_BG = "#1E293B"      # พื้นหลังแถบควบคุมด้านล่าง

# Accent Colors (Teal / Cyan)
ACCENT_TEAL = "#06B6D4"     # สีเน้นหลัก ปุ่ม/สไลเดอร์ (Teal/Cyan 500)
ACCENT_TEAL_HOVER = "#0891B2" # สีเมื่อ hover ปุ่มเน้น (Teal/Cyan 600)
ACCENT_CYAN = "#22D3EE"     # สี Cyan สว่างสำหรับจุดเด่น/ไอคอน
ACCENT_CYAN_GLOW = "#38BDF8" # สี Cyan Glow สำหรับ badge หรือกราฟิก

# Button Colors (Secondary / Dark Buttons)
BTN_BG = "#334155"          # สีพื้นหลังปุ่มทั่วไป
BTN_HOVER = "#475569"       # สีพื้นหลังปุ่มทั่วไปเมื่อ hover
BTN_ACTIVE = "#64748B"      # สีพื้นหลังปุ่มเมื่อกด

# Text Colors
TEXT_WHITE = "#F8FAFC"      # ข้อความหลัก สีขาวนวล
TEXT_MUTED = "#94A3B8"      # ข้อความรอง สีเทาอ่อน
TEXT_DARK = "#64748B"       # ข้อความสีเทาเข้ม/รายละเอียด

# Quality Badge Colors
BADGE_BG = "#0C4A6E"        # พื้นหลังป้าย 1080p
BADGE_TEXT = "#38BDF8"      # สีตัวอักษรป้าย 1080p
BADGE_BORDER = "#0284C7"    # ขอบป้าย 1080p

# Progress & Slider Colors
SLIDER_PROGRESS = "#06B6D4" # สีส่วนที่เล่นแล้ว
SLIDER_BG = "#334155"       # สีส่วนที่ยังไม่ได้เล่น
PROGRESS_BAR_BG = "#1E293B"# สีพื้นหลัง progress bar หน้า loading

# ==========================================
# Typography (ฟอนต์และขนาดตัวอักษร)
# ==========================================
FONT_FAMILY = "Segoe UI"
FONT_MONO = "Consolas"

FONT_TITLE = (FONT_FAMILY, 18, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 14, "bold")
FONT_BODY = (FONT_FAMILY, 12, "normal")
FONT_BODY_BOLD = (FONT_FAMILY, 12, "bold")
FONT_SMALL = (FONT_FAMILY, 10, "normal")
FONT_TIME = (FONT_MONO, 11, "bold")
FONT_BADGE = (FONT_FAMILY, 10, "bold")

# ==========================================
# Sample Video & App Defaults
# ==========================================
DEFAULT_FILENAME = "private_clip.mp4"
DEFAULT_QUALITY = "1080p"
DEFAULT_DURATION = 225  # ความยาววิดีโอจำลอง (3 นาที 45 วินาที)
WINDOW_TITLE = "HD Private Player"
WINDOW_INIT_SIZE = "900x600"
WINDOW_MIN_WIDTH = 700
WINDOW_MIN_HEIGHT = 450
