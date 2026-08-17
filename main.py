"""
HD Private Player - Main Entry Point
จุดเริ่มต้นสำหรับรันแอปพลิเคชัน HD Private Player
"""

from ui.main_window import HDPlayerApp


def main():
    # สร้าง instance ของแอปพลิเคชันหลัก
    app = HDPlayerApp()
    
    # รันลูปการทำงานหลักของ GUI
    app.mainloop()


if __name__ == "__main__":
    main()
