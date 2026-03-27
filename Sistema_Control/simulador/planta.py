import threading

class Planta:
    def __init__(self):

        # Estados
        self.t1_level = 0
        self.t2_level = 0
        self.t3_level = 0

        self.v1 = False
        self.v2 = False
        self.v3 = False
        self.bomba = False

        self.auto = False

        self.step = 0

        self.lock = threading.Lock()

    # ---------------- CONTROL AUTOMÁTICO ----------------
    def control_auto(self):

        print(f"\n[STEP {self.step}] T1:{self.t1_level} T2:{self.t2_level} T3:{self.t3_level}")

        # Reset de actuadores
        self.bomba = False
        self.v1 = False
        self.v2 = False
        self.v3 = False

        # ---------------- ETAPA 0: LLENAR T1 ----------------
        if self.step == 0:
            self.bomba = True

            if self.t1_level >= 100:
                print("➡️ Paso a ETAPA 1 (T1 lleno)")
                self.step = 1

        # ---------------- ETAPA 1: LLENAR T2 ----------------
        elif self.step == 1:
            self.v1 = True

            if self.t2_level >= 100:
                print("➡️ Paso a ETAPA 2 (T2 lleno)")
                self.step = 2

        # ---------------- ETAPA 2: LLENAR T3 ----------------
        elif self.step == 2:
            self.v2 = True

            if self.t3_level >= 100:
                print("➡️ Paso a ETAPA 3 (T3 lleno)")
                self.step = 3

        # ---------------- ETAPA 3: VACIAR T3 ----------------
        elif self.step == 3:
            self.v3 = True

            if self.t3_level <= 0:
                print("🔁 Reinicio ciclo → ETAPA 0")
                self.step = 0


    # ---------------- SIMULACIÓN ----------------
    def update(self):
       

        with self.lock:

            if self.auto:
                self.control_auto()
            
            # Bomba llena T1
            if self.bomba:
                self.t1_level += 2

            # V1 pasa de T1 a T2
            if self.v1:
                flow = min(2, self.t1_level)
                self.t1_level -= flow
                self.t2_level += flow

            # V2 pasa de T2 a T3
            if self.v2:
                flow = min(2, self.t2_level)
                self.t2_level -= flow
                self.t3_level += flow
           
            # V3 descarga T3
            if self.v3:
                flow = min(2, self.t3_level)
                self.t3_level -= flow    

            # Saturaciones
            self.t1_level = max(0, min(100, self.t1_level))
            self.t2_level = max(0, min(100, self.t2_level))
            self.t3_level = max(0, min(100, self.t3_level))
    
    # ---------------- COMANDOS ----------------
    def command(self, cmd):

        with self.lock:

            if cmd["cmd"] == "toggle_bomba":
                self.bomba = not self.bomba

            elif cmd["cmd"] == "set_valve":
                valve = cmd.get("valve")

                if valve == "v1":
                    self.v1 = not self.v1
                elif valve == "v2":
                    self.v2 = not self.v2
                elif valve == "v3":   
                    self.v3 = not self.v3

            elif cmd["cmd"] == "marcha":
                self.auto = True

            elif cmd["cmd"] == "paro":
                self.auto = False
                self.bomba = False
                self.v1 = False
                self.v2 = False
                self.v3 = False

    # ---------------- ESTADO ----------------
    def get_state(self):

        with self.lock:

            return {
                # 🔹 TANQUE 1
                "t1_high": self.t1_level > 70,
                "t1_low": self.t1_level < 30,

                # 🔹 TANQUE 2
                "t2_high": self.t2_level > 70,
                "t2_low": self.t2_level < 30,

                # 🔹 TANQUE 3
                "t3_high": self.t3_level > 70,
                "t3_low": self.t3_level < 30,

                # 🔹 ACTUADORES
                "v1": self.v1,
                "v2": self.v2,
                "v3": self.v3,
                "bomba": self.bomba
            }