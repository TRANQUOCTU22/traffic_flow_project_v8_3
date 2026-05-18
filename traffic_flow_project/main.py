import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    # Khởi chạy ứng dụng desktop PySide6.
    app=QApplication(sys.argv)
    app.setApplicationName('Traffic Flow Optimization')
    w=MainWindow(); w.show()
    sys.exit(app.exec())
if __name__=='__main__': main()
