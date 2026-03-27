import os
import time
from PySide6.QtWidgets import (
QWidget, QVBoxLayout, QHBoxLayout,
QPushButton, QLabel, QFrame, QCheckBox,
QGridLayout, QComboBox, QLineEdit, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtGui import QPixmap

from comms.factory import get_comm
from comms.worker import CommWorker
from ui.widgets import TankWidget, ValveWidget

class SCADA(QWidget):
    def __init__(self):
        super().__init__()

        # ---------------- COMUNICACIONES ----------------
        self.comm = None
        self.thread = None
        self.worker = None

        # ---------------- ESTADO LOCAL ----------------
        self.bomba_on = False
        self.valvula_t1_on = False
        self.valvula_t2_on = False
        self.valvula_t3_on = False

        # ---------------- UI CONFIG ----------------
        self.setWindowTitle("SCADA - Sistema de Tanques")
        self.setStyleSheet("background-color: #2b2b2b; color: white;")
        self.setMinimumSize(950, 550)

        self.init_ui()

        # ---------------- WATCHDOG ----------------
        self.last_update = time.time()
        self.timeout = 2.0

        self.watchdog = QTimer()
        self.watchdog.timeout.connect(self.check_comm)
        self.watchdog.start(500)

    # ==================================================
    # CONEXIÓN DINÁMICA
    # ==================================================
    def conectar(self):
        tipo = self.combo_comm.currentText()
        valor = self.input_destino.text().strip()

        if not valor:
            self.lbl_comm.setText("⚠ CONFIGURACIÓN VACÍA")
            self.lbl_comm.setStyleSheet("color: orange; font-weight: bold;")
            return

        # 🔴 detener anterior
        if self.worker:
            self.worker.stop()
            self.thread.quit()
            self.thread.wait()

        if self.comm:
            self.comm.disconnect()

        # 🟢 crear nueva comunicación
        try:
            if tipo == "rest":
                url = f"http://{valor}"
                self.comm = get_comm("rest", url=url)

            elif tipo == "mqtt":
                self.comm = get_comm("mqtt", broker=valor)

            elif tipo == "serial":
                self.comm = get_comm("serial", port=valor)

            self.comm.connect()

        except Exception as e:
            self.lbl_comm.setText(f"ERROR: {str(e)}")
            self.lbl_comm.setStyleSheet("color: red; font-weight: bold;")
            return

        # 🟢 crear worker
        self.thread = QThread()
        self.worker = CommWorker(self.comm)

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.data_ready.connect(self.update_from_planta)

        self.thread.start()

        self.lbl_comm.setText("CONECTADO")
        self.lbl_comm.setStyleSheet("color: lime; font-weight: bold;")

    # ==================================================
    # UI
    # ==================================================
    def init_ui(self):
        main_layout = QHBoxLayout()

        # ----------- PROCESO ----------- #
        process_layout = QVBoxLayout()

        btn_style = """
            QPushButton {
                background-color: #8a8a8a; /* fondo más claro */
                color: white;
                border: 2px solid #888; /* borde más visible */
                border-radius: 2px;
                padding: 8px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #3a3a3a;
                border: 2px solid #00aaff;
            }

            QPushButton:pressed {
                background-color: #00aaff;
                color: black;
            }
            """

        # T1
        row_t1 = QHBoxLayout()
        self.t1 = TankWidget("T1", "LOW")

        col_v1 = QVBoxLayout()
        self.v1 = ValveWidget("V1", False)
        self.btn_v1 = QPushButton("V1")
        self.btn_v1.clicked.connect(self.toggle_v1)
        self.btn_v1.setMinimumHeight(40)
        self.btn_v1.setStyleSheet(btn_style)


        col_v1.addWidget(self.v1)
        col_v1.addWidget(self.btn_v1)
        col_v1.setAlignment(Qt.AlignHCenter)

        row_t1.addWidget(self.t1)
        row_t1.addLayout(col_v1)
        process_layout.addLayout(row_t1)

        # T2
        row_t2 = QHBoxLayout()
        self.t2 = TankWidget("T2", "LOW")

        col_v2 = QVBoxLayout()
        self.v2 = ValveWidget("V2", False)
        self.btn_v2 = QPushButton("V2")
        self.btn_v2.clicked.connect(self.toggle_v2)
        self.btn_v2.setMinimumHeight(40)
        self.btn_v2.setStyleSheet(btn_style)


        col_v2.addWidget(self.v2)
        col_v2.addWidget(self.btn_v2)
        col_v2.setAlignment(Qt.AlignHCenter)

        row_t2.addWidget(self.t2)
        row_t2.addLayout(col_v2)
        process_layout.addLayout(row_t2)

        # T3
        row_t3 = QHBoxLayout()
        self.t3 = TankWidget("T3", "LOW")

        col_v3 = QVBoxLayout()
        self.v3 = ValveWidget("V3", False)
        self.btn_v3 = QPushButton("V3")
        self.btn_v3.clicked.connect(self.toggle_v3)
        self.btn_v3.setMinimumHeight(40)
        self.btn_v3.setStyleSheet(btn_style)

        col_v3.addWidget(self.v3)
        col_v3.addWidget(self.btn_v3)
        col_v3.setAlignment(Qt.AlignHCenter)

        row_t3.addWidget(self.t3)
        row_t3.addLayout(col_v3)
        process_layout.addLayout(row_t3)

        # ----------- PANEL DERECHO ----------- #
        control_layout = QVBoxLayout()

        # 🔌 CONFIG CONEXIÓN
        self.combo_comm = QComboBox()
        self.combo_comm.addItems(["rest", "mqtt", "serial"])

        self.input_destino = QLineEdit()
        self.input_destino.setPlaceholderText("IP:PUERTO o COM (ej: 192.168.1.10:5000 o COM3)")

        self.btn_connect = QPushButton("CONECTAR")
        self.btn_connect.clicked.connect(self.conectar)
        self.btn_connect.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #0094ff;
            }
            QPushButton:pressed {
                background-color: #005f99;
            }
        """)

        # ----------- PANEL COMUNICACIÓN ----------- #
        comm_frame = QFrame()
        comm_frame.setStyleSheet("""
            background-color: #1e1e1e;
            border: 2px solid #444;
            border-radius: 2px;
            padding: 1px;
        """)

        comm_layout = QGridLayout()

        # Tipo
        comm_layout.addWidget(QLabel("Tipo:"), 0, 0)
        comm_layout.addWidget(self.combo_comm, 0, 1)

        # Destino
        comm_layout.addWidget(QLabel("Destino:"), 1, 0)
        comm_layout.addWidget(self.input_destino, 1, 1)

        # Botón
        comm_layout.addWidget(self.btn_connect, 2, 0, 1, 1)

         # Estado comunicación

        self.lbl_comm = QLabel("SIN CONEXIÓN")

        self.lbl_comm.setAlignment(Qt.AlignCenter)

        self.lbl_comm.setStyleSheet("""
            border: none;
            background: transparent;
            padding: 2px;
            color: red;
            font-weight: bold;
        """)
        
        self.lbl_comm.setStyleSheet("color: red; font-weight: bold;")
        comm_layout.addWidget(self.lbl_comm, 2, 1, 1, 1)

        control_layout.addWidget(QLabel("COMUNICACIÓN"))
        control_layout.addWidget(comm_frame)
        comm_frame.setLayout(comm_layout)


         # ----------- PANEL CENTRAL BOMBA ----------- #
        # Imagen bomba
        self.img_bomba = QLabel()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ruta_img = os.path.join(base_dir, "..", "recursos", "bomba.png")
        ruta_img = os.path.normpath(ruta_img)

        pixmap = QPixmap(ruta_img)

        if pixmap.isNull():
            self.img_bomba.setText("⚠ No imagen")
        else:
            pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_bomba.setPixmap(pixmap)

        self.img_bomba.setAlignment(Qt.AlignCenter)

        # Botón bomba
        self.btn_bomba = QPushButton("BOMBA ON/OFF")
        self.btn_bomba.clicked.connect(self.toggle_bomba)
        self.btn_bomba.setMinimumHeight(40)
        self.btn_bomba.setStyleSheet(btn_style)

        # Estado bomba
        self.lbl_bomba = QLabel("BOMBA APAGADA")
        self.lbl_bomba.setAlignment(Qt.AlignCenter)
        self.lbl_bomba.setStyleSheet("color: gray; font-weight: bold;")

        # -------- INFO --------
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            background-color: #111;
            border: 2px solid #444;
            border-radius: 1px;
            padding: 1px;
        """)

        grid = QGridLayout()

        grid.addWidget(QLabel("Tanques"), 0, 0)
        grid.addWidget(QLabel("T1"), 0, 1)
        grid.addWidget(QLabel("T2"), 0, 2)
        grid.addWidget(QLabel("T3"), 0, 3)

        grid.addWidget(QLabel("Nivel Alto"), 1, 0)
        grid.addWidget(QLabel("Nivel Bajo"), 2, 0)
        grid.addWidget(QLabel("Válvula"), 3, 0)



        self.t1_high = QLabel()
        self.t2_high = QLabel()
        self.t3_high = QLabel()

        self.t1_low = QLabel()
        self.t2_low = QLabel()
        self.t3_low = QLabel()

        self.v1_state = QLabel()
        self.v2_state = QLabel()
        self.v3_state = QLabel()

        grid.addWidget(self.t1_high, 1, 1)
        grid.addWidget(self.t2_high, 1, 2)
        grid.addWidget(self.t3_high, 1, 3)

        grid.addWidget(self.t1_low, 2, 1)
        grid.addWidget(self.t2_low, 2, 2)
        grid.addWidget(self.t3_low, 2, 3)

        grid.addWidget(self.v1_state, 3, 1)
        grid.addWidget(self.v2_state, 3, 2)
        grid.addWidget(self.v3_state, 3, 3)

        info_frame.setLayout(grid)

        # -------- CONTROLES --------
        self.btn_marcha = QPushButton("MARCHA")
        self.btn_marcha.setStyleSheet("background-color: green;")
        self.btn_marcha.clicked.connect(self.marcha)
         

        self.btn_paro = QPushButton("PARO")
        self.btn_paro.setStyleSheet("background-color: red;")
        self.btn_paro.clicked.connect(self.paro)

        self.manual = QCheckBox("MANUAL")
        self.manual.setChecked(True)

        self.lbl_estado = QLabel("SISTEMA PARADO")
        self.lbl_estado.setAlignment(Qt.AlignCenter)
        self.lbl_estado.setStyleSheet("color: red; font-weight: bold;")
       
        # Layout derecho
        control_layout.addWidget(self.img_bomba)
        control_layout.addWidget(self.btn_bomba)
        control_layout.addWidget(self.lbl_bomba)

        control_layout.addSpacing(15)
        control_layout.addWidget(info_frame)

        # Layout de botones 
        controles_grid = QGridLayout()

        # Botones ocupando 2 filas
        controles_grid.addWidget(self.manual, 0, 0)
        controles_grid.addWidget(self.lbl_estado, 0, 1)

        controles_grid.addWidget(self.btn_marcha, 1, 0, 2, 1)
        controles_grid.addWidget(self.btn_paro,   1, 1, 2, 1)

        self.btn_marcha.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.btn_paro.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.btn_marcha.setMinimumHeight(80)
        self.btn_paro.setMinimumHeight(80)

        self.manual.setMinimumHeight(40)


        controles_grid.setRowStretch(0, 1)
        controles_grid.setRowStretch(1, 1)

        control_layout.addSpacing(5)

        control_layout.addLayout(controles_grid)


        main_layout.addLayout(process_layout)
        main_layout.addLayout(control_layout)

        self.setLayout(main_layout)

        self.actualizar_info()

    # ==================================================
    # RECEPCIÓN DE DATOS
    # ==================================================
    def update_from_planta(self, data):

        self.last_update = time.time()

        if not data:
            return

        self.lbl_comm.setText("COMUNICACIÓN OK")
        self.lbl_comm.setStyleSheet("color: lime; font-weight: bold;")

        # -------- NIVELES --------
        def set_level(widget, high, low):
            if high and low:
                widget.level = "MID"
            elif high:
                widget.level = "HIGH"
            elif low:
                widget.level = "LOW"
            else:
                widget.level = "MID"

        set_level(self.t1, data.get("t1_high"), data.get("t1_low"))
        set_level(self.t2, data.get("t2_high"), data.get("t2_low"))
        set_level(self.t3, data.get("t3_high"), data.get("t3_low"))

        # -------- ACTUADORES --------
        self.valvula_t1_on = data.get("v1", False)
        self.valvula_t2_on = data.get("v2", False)
        self.valvula_t3_on = data.get("v3", False)

        self.v1.set_open(self.valvula_t1_on)
        self.v2.set_open(self.valvula_t2_on)
        self.v3.set_open(self.valvula_t3_on)

        self.bomba_on = data.get("bomba", False)

        if self.bomba_on:
            self.lbl_bomba.setText("BOMBA ENCENDIDA")
            self.lbl_bomba.setStyleSheet("color: lime; font-weight: bold;")
        else:
            self.lbl_bomba.setText("BOMBA APAGADA")
            self.lbl_bomba.setStyleSheet("color: gray; font-weight: bold;")

        # -------- MANUAL / AUTO --------
        manual = self.manual.isChecked()

        self.btn_bomba.setEnabled(manual)
        self.btn_v1.setEnabled(manual)
        self.btn_v2.setEnabled(manual)
        self.btn_v3.setEnabled(manual)

        if not manual:
            self.lbl_estado.setText("MODO AUTOMÁTICO")
            self.lbl_estado.setStyleSheet("color: cyan; font-weight: bold;")
        else:
            self.lbl_estado.setText("MODO MANUAL")
            self.lbl_estado.setStyleSheet("color: yellow; font-weight: bold;")

        # -------- REFRESCO --------
        self.t1.update()
        self.t2.update()
        self.t3.update()

        self.actualizar_info()

    # ==================================================
    # ENVÍO COMANDOS
    # ==================================================
    def toggle_bomba(self):
        if self.comm:
            self.comm.send_command({"cmd": "toggle_bomba"})

    def toggle_v1(self):
        if self.comm:
            self.comm.send_command({"cmd": "set_valve", "valve": "v1"})

    def toggle_v2(self):
        if self.comm:
            self.comm.send_command({"cmd": "set_valve", "valve": "v2"})

    def toggle_v3(self):
        if self.comm:
            self.comm.send_command({"cmd": "set_valve", "valve": "v3"})

    def marcha(self):
        if self.comm:
            self.comm.send_command({"cmd": "marcha"})

    def paro(self):
        if self.comm:
            self.comm.send_command({"cmd": "paro"})

    # ==================================================
    # WATCHDOG
    # ==================================================
    def check_comm(self):
        if time.time() - self.last_update > self.timeout:
            self.lbl_comm.setText("SIN COMUNICACIÓN")
            self.lbl_comm.setStyleSheet("color: red; font-weight: bold;")

    # ==================================================
    # INFO UI
    # ==================================================
    def actualizar_info(self):

        def nivel_alto(level):
            return "ON" if level == "HIGH" else "OFF"

        def nivel_bajo(level):
            return "ON" if level == "LOW" else "OFF"

        self.t1_high.setText(nivel_alto(self.t1.level))
        self.t2_high.setText(nivel_alto(self.t2.level))
        self.t3_high.setText(nivel_alto(self.t3.level))

        self.t1_low.setText(nivel_bajo(self.t1.level))
        self.t2_low.setText(nivel_bajo(self.t2.level))
        self.t3_low.setText(nivel_bajo(self.t3.level))

        self.v1_state.setText("ABIERTA" if self.valvula_t1_on else "CERRADA")
        self.v2_state.setText("ABIERTA" if self.valvula_t2_on else "CERRADA")
        self.v3_state.setText("ABIERTA" if self.valvula_t3_on else "CERRADA")

    # ==================================================
    # CIERRE LIMPIO
    # ==================================================
    def closeEvent(self, event):

        if self.worker:
            self.worker.stop()

        if self.thread:
            self.thread.quit()
            self.thread.wait()

        if self.comm:
            self.comm.disconnect()

        event.accept()

