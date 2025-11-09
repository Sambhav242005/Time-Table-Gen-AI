import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import AdvancedTimetableApp

if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = AdvancedTimetableApp()
    window.show()
    
    # Execute the app event loop
    sys.exit(app.exec_())
