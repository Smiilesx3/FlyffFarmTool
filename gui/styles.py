APP_STYLE = """
QMainWindow {
    background-color: #f4f5f1;
}

QWidget {
    font-family: "Segoe UI";
    font-size: 10pt;
    color: #242821;
}

QFrame#panel {
    background-color: #ffffff;
    border: 1px solid #dfe3da;
    border-radius: 12px;
}

QLabel#sectionTitle {
    font-size: 12pt;
    font-weight: 600;
    color: #242821;
}

QLabel#appTitle {
    font-size: 18pt;
    font-weight: 700;
    color: #242821;
}

QLabel#muted {
    color: #747b70;
}

QLabel#statusReady {
    color: #657452;
    font-weight: 600;
}

QLabel#statusWarning {
    color: #9a6b22;
    font-weight: 600;
}

QLabel#statusEmergency {
    color: #a63d40;
    font-weight: 700;
}

QPushButton {
    min-height: 34px;
    padding: 4px 14px;
    border-radius: 8px;
    border: 1px solid #d4d9cf;
    background-color: #ffffff;
}

QPushButton:hover {
    background-color: #f0f2ec;
}

QPushButton:pressed {
    background-color: #e5e9df;
}

QPushButton#primaryButton {
    background-color: #6f7f58;
    color: white;
    border: none;
    font-weight: 600;
}

QPushButton#primaryButton:hover {
    background-color: #64734f;
}

QPushButton#dangerButton {
    background-color: #a94c4c;
    color: white;
    border: none;
    font-weight: 600;
}

QPushButton#dangerButton:hover {
    background-color: #983f3f;
}

QPushButton#resetButton {
    background-color: #ffffff;
    color: #a63d40;
    border: 1px solid #a63d40;
}

QLineEdit,
QComboBox,
QSpinBox,
QDoubleSpinBox {
    min-height: 30px;
    padding-left: 8px;
    padding-right: 8px;
    background-color: #ffffff;
    border: 1px solid #d4d9cf;
    border-radius: 7px;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 17px;
    height: 17px;
}

QProgressBar {
    border: 1px solid #d4d9cf;
    border-radius: 6px;
    background-color: #ecefe8;
    text-align: center;
    min-height: 20px;
}

QProgressBar::chunk {
    background-color: #788963;
    border-radius: 5px;
}

QStatusBar {
    background-color: #ffffff;
    border-top: 1px solid #dfe3da;
}
"""