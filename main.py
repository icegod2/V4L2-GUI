import sys
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QComboBox, QLabel, QScrollArea, 
                             QFormLayout, QSlider, QCheckBox, QPushButton,
                             QSpinBox)
from PyQt6.QtCore import Qt, QTimer
import v4l2_wrapper

class CameraControlApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ubuntu Camera Control (v4l2-ctl)")
        self.setMinimumSize(500, 600)
        
        self.current_device = None
        self.controls_widgets = {} # name -> widget
        
        # Debounce timer for sliders
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(200) # 200ms
        self.pending_set = None # (name, value)
        self.debounce_timer.timeout.connect(self.apply_pending_set)

        self.init_ui()
        self.refresh_devices()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top Bar: Device Selection & Refresh
        top_layout = QHBoxLayout()
        self.device_combo = QComboBox()
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self.refresh_devices)
        
        preview_btn = QPushButton("Live Preview")
        preview_btn.clicked.connect(self.start_preview)
        
        top_layout.addWidget(QLabel("Device:"))
        top_layout.addWidget(self.device_combo, 1)
        top_layout.addWidget(refresh_btn)
        top_layout.addWidget(preview_btn)
        main_layout.addLayout(top_layout)

        # Middle: Scrollable Controls
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.controls_container = QWidget()
        self.controls_layout = QFormLayout(self.controls_container)
        self.scroll.setWidget(self.controls_container)
        main_layout.addWidget(self.scroll)

    def refresh_devices(self):
        self.device_combo.clear()
        devices = v4l2_wrapper.list_devices()
        for dev in devices:
            self.device_combo.addItem(f"{dev['name']} ({dev['path']})", dev['path'])
        
        if not devices:
            self.clear_controls()
            self.device_combo.addItem("No cameras found", None)

    def on_device_changed(self, index):
        path = self.device_combo.itemData(index)
        if path:
            self.current_device = path
            self.refresh_controls()

    def clear_controls(self):
        # Clear the layout
        while self.controls_layout.count():
            item = self.controls_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.controls_widgets = {}

    def refresh_controls(self):
        if not self.current_device:
            return
            
        self.clear_controls()
        controls = v4l2_wrapper.get_controls(self.current_device)
        
        for ctrl in controls:
            if 'inactive' in ctrl['flags']:
                continue
                
            label = QLabel(ctrl['name'].replace('_', ' ').title())
            widget = None
            
            if ctrl['type'] == 'int':
                widget = self.create_int_widget(ctrl)
            elif ctrl['type'] == 'bool':
                widget = self.create_bool_widget(ctrl)
            elif ctrl['type'] == 'menu':
                widget = self.create_menu_widget(ctrl)
                
            if widget:
                self.controls_layout.addRow(label, widget)
                self.controls_widgets[ctrl['name']] = widget

    def create_int_widget(self, ctrl):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(ctrl['min'], ctrl['max'])
        slider.setValue(ctrl['value'])
        
        spin = QSpinBox()
        spin.setRange(ctrl['min'], ctrl['max'])
        spin.setValue(ctrl['value'])
        
        # Sync slider and spinbox
        slider.valueChanged.connect(spin.setValue)
        spin.valueChanged.connect(slider.setValue)
        
        # Trigger update on value change
        slider.valueChanged.connect(lambda v, name=ctrl['name']: self.queue_set_control(name, v))
        
        layout.addWidget(slider)
        layout.addWidget(spin)
        return container

    def create_bool_widget(self, ctrl):
        check = QCheckBox()
        check.setChecked(bool(ctrl['value']))
        check.toggled.connect(lambda v, name=ctrl['name']: self.queue_set_control(name, int(v)))
        return check

    def create_menu_widget(self, ctrl):
        combo = QComboBox()
        for idx, label in ctrl['options'].items():
            combo.addItem(label, idx)
        
        # Set current index
        current_idx = combo.findData(ctrl['value'])
        if current_idx != -1:
            combo.setCurrentIndex(current_idx)
            
        combo.currentIndexChanged.connect(lambda i, name=ctrl['name'], c=combo: self.queue_set_control(name, c.itemData(i)))
        return combo

    def queue_set_control(self, name, value):
        self.pending_set = (name, value)
        self.debounce_timer.start()

    def apply_pending_set(self):
        if self.current_device and self.pending_set:
            name, value = self.pending_set
            v4l2_wrapper.set_control(self.current_device, name, value)
            self.pending_set = None
            # Refresh to update inactive flags if a dependency changed
            QTimer.singleShot(100, self.refresh_controls)

    def start_preview(self):
        if self.current_device:
            # 使用 ffplay 開啟預覽，這是一個非同步呼叫，不會卡住 GUI
            try:
                subprocess.Popen(['ffplay', '-i', self.current_device, '-window_title', f"Preview: {self.current_device}"])
            except FileNotFoundError:
                print("Error: ffplay not found. Please install ffmpeg.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraControlApp()
    window.show()
    sys.exit(app.exec())
