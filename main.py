import sys
import os
import socket
import subprocess
import re
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QTabWidget, QScrollArea, QDialog, QPushButton,
    QCheckBox, QSizePolicy, QSplitter, QLineEdit, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QAction, QIntValidator
from PyQt6.QtGui import QIcon

# Admin jog ellenőrzése és újraindítás ha szükséges
import ctypes
if not ctypes.windll.shell32.IsUserAnAdmin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit()


# ---------------------------------------------------------------------------
# Assets elérési út
# ---------------------------------------------------------------------------

def asset(filename):
    if hasattr(sys, '_MEIPASS'):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets", filename)


# ---------------------------------------------------------------------------
# Log rendszer – kikapcsolható
# ---------------------------------------------------------------------------

LOG_ENABLED = True
LOG_PATH    = os.path.join(os.path.expanduser("~"), "Documents", "MicroIPTool.log")

def _log(msg):
    if not LOG_ENABLED:
        return
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            from datetime import datetime
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Nyelvi szótár
# ---------------------------------------------------------------------------

LANGUAGES = {
    "hu": {
        "window_title":           "Micro IP Tool",
        "tab_ip":                 "IP Beállítás",
        "tab_ping":               "Ping",
        "tab_scan":               "Szkennelés",
        "status_pc":              "Számítógép neve",
        "status_domain":          "Domain / Workgroup",
        "warning_overlap":        "⚠  Figyelem: {0} és {1} tartománya átfed ({2}.x)",
        "adapter_no_ip":          "N/A",
        "adapter_no_ssid":        "Nincs kapcsolat",
        "adapter_mac":            "MAC",
        "adapter_ip":             "IP",
        "adapter_subnet":         "Subnet",
        "adapter_gateway":        "Gateway",
        "adapter_ssid":           "SSID",
        "adapter_desc":           "Leírás",
        "adapter_status_up":      "Csatlakozva",
        "adapter_status_down":    "Leválasztva",
        "adapter_badge_virtual":  "VIRTUÁLIS",
        "adapter_badge_physical": "FIZIKAI",
        "show_virtual":           "Virtuális adapterek mutatása",
        "btn_refresh":            "⟳  Frissítés",
        "menu_file":              "Fájl",
        "menu_file_exit":         "Kilépés",
        "menu_settings":          "Beállítások",
        "menu_settings_lang":     "Nyelv",
        "menu_help":              "Súgó",
        "menu_help_about":        "Névjegy",
        "about_title":            "Névjegy",
        "about_version":          "Verzió: 0.8.1",
        "about_author":           "Készítette: Nozy82",
        "about_desc":             "Hálózati eszköz IP beállításhoz, pingeléshez és szkenneléshez.",
        "about_github":           "Forráskód és letöltés:",
        "about_close":            "Bezárás",
        "placeholder_ping":       "Ping – hamarosan",
        "placeholder_scan":       "Szkennelés – hamarosan",
        "ip_current_title":       "Jelenlegi beállítások",
        "ip_adapter_name":        "Adapter",
        "ip_desc":                "Leírás",
        "ip_mac":                 "MAC cím",
        "ip_address":             "IP cím",
        "ip_subnet":              "Alhálózati maszk",
        "ip_gateway":             "Átjáró",
        "ip_type":                "IP típusa",
        "ip_type_dhcp":           "DHCP",
        "ip_type_static":         "Statikus",
        "ip_dns":                 "DNS szerver",
        "ip_set_title":           "Beállítás",
        "ip_btn_dhcp":            "DHCP",
        "ip_btn_static":          "Statikus",
        "ip_new_ip":              "IP cím",
        "ip_new_subnet":          "Alhálózati maszk",
        "ip_new_gateway":         "Átjáró",
        "ip_apply":               "Alkalmaz",
        "ip_apply_ok":            "✔  Beállítás sikeresen alkalmazva",
        "ip_apply_err":           "✖  Hiba: {0}",
        "ip_apply_admin":         "✖  Rendszergazdai jog szükséges",
        "ip_no_adapter":          "Nincs kiválasztott adapter",
        "ping_title":             "Pingelés",
        "ping_target":            "Célállomás IP cím",
        "ping_btn_start":         "Ping indítása",
        "ping_btn_clear":         "Törlés",
        "ping_running":           "Pingelés folyamatban...",
        "ping_no_adapter":        "Nincs kiválasztott adapter",
        "ping_invalid_ip":        "Érvénytelen IP cím – csak 0-255 közötti számok megengedettek",
        "scan_title":             "Hálózat szkennelés",
        "scan_range_from":        "Tartomány kezdete",
        "scan_range_to":          "Tartomány vége",
        "scan_btn_start":         "▶  Szkennelés",
        "scan_btn_stop":          "■  Stop",
        "scan_btn_export":        "⬇  Exportálás CSV",
        "scan_btn_clear":         "Törlés",
        "scan_col_ip":            "IP cím",
        "scan_col_mac":           "MAC cím",
        "scan_col_hostname":      "Név",
        "scan_col_vendor":        "Gyártó",
        "scan_no_adapter":        "Nincs kiválasztott adapter",
        "scan_running":           "Szkennelés folyamatban... {0}/{1}",
        "scan_done":              "Szkennelés kész – {0} eszköz találva",
        "scan_stopped":           "Szkennelés leállítva – {0} eszköz találva",
        "scan_export_ok":         "✔  Exportálva: {0}",
        "scan_export_err":        "✖  Export hiba: {0}",
        "scan_no_results":        "Nincs exportálható eredmény",
    },
    "en": {
        "window_title":           "Micro IP Tool",
        "tab_ip":                 "IP Settings",
        "tab_ping":               "Ping",
        "tab_scan":               "Scan",
        "status_pc":              "Computer name",
        "status_domain":          "Domain / Workgroup",
        "warning_overlap":        "⚠  Warning: {0} and {1} share the same range ({2}.x)",
        "adapter_no_ip":          "N/A",
        "adapter_no_ssid":        "Not connected",
        "adapter_mac":            "MAC",
        "adapter_ip":             "IP",
        "adapter_subnet":         "Subnet",
        "adapter_gateway":        "Gateway",
        "adapter_ssid":           "SSID",
        "adapter_desc":           "Description",
        "adapter_status_up":      "Connected",
        "adapter_status_down":    "Disconnected",
        "adapter_badge_virtual":  "VIRTUAL",
        "adapter_badge_physical": "PHYSICAL",
        "show_virtual":           "Show virtual adapters",
        "btn_refresh":            "⟳  Refresh",
        "menu_file":              "File",
        "menu_file_exit":         "Exit",
        "menu_settings":          "Settings",
        "menu_settings_lang":     "Language",
        "menu_help":              "Help",
        "menu_help_about":        "About",
        "about_title":            "About",
        "about_version":          "Version: 0.8.1",
        "about_author":           "Created by: Nozy82",
        "about_desc":             "Network tool for IP configuration, ping and scanning.",
        "about_github":           "Source code and download:",
        "about_close":            "Close",
        "placeholder_ping":       "Ping – coming soon",
        "placeholder_scan":       "Scan – coming soon",
        "ip_current_title":       "Current settings",
        "ip_adapter_name":        "Adapter",
        "ip_desc":                "Description",
        "ip_mac":                 "MAC address",
        "ip_address":             "IP address",
        "ip_subnet":              "Subnet mask",
        "ip_gateway":             "Gateway",
        "ip_type":                "IP type",
        "ip_type_dhcp":           "DHCP",
        "ip_type_static":         "Static",
        "ip_dns":                 "DNS server",
        "ip_set_title":           "Configuration",
        "ip_btn_dhcp":            "DHCP",
        "ip_btn_static":          "Static",
        "ip_new_ip":              "IP address",
        "ip_new_subnet":          "Subnet mask",
        "ip_new_gateway":         "Gateway",
        "ip_apply":               "Apply",
        "ip_apply_ok":            "✔  Settings applied successfully",
        "ip_apply_err":           "✖  Error: {0}",
        "ip_apply_admin":         "✖  Administrator rights required",
        "ip_no_adapter":          "No adapter selected",
        "ping_title":             "Ping",
        "ping_target":            "Target IP address",
        "ping_btn_start":         "Start ping",
        "ping_btn_clear":         "Clear",
        "ping_running":           "Pinging...",
        "ping_no_adapter":        "No adapter selected",
        "ping_invalid_ip":        "Invalid IP address – only values 0-255 are allowed",
        "scan_title":             "Network Scan",
        "scan_range_from":        "Range start",
        "scan_range_to":          "Range end",
        "scan_btn_start":         "▶  Scan",
        "scan_btn_stop":          "■  Stop",
        "scan_btn_export":        "⬇  Export CSV",
        "scan_btn_clear":         "Clear",
        "scan_col_ip":            "IP address",
        "scan_col_mac":           "MAC address",
        "scan_col_hostname":      "Hostname",
        "scan_col_vendor":        "Vendor",
        "scan_no_adapter":        "No adapter selected",
        "scan_running":           "Scanning... {0}/{1}",
        "scan_done":              "Scan complete – {0} devices found",
        "scan_stopped":           "Scan stopped – {0} devices found",
        "scan_export_ok":         "✔  Exported: {0}",
        "scan_export_err":        "✖  Export error: {0}",
        "scan_no_results":        "No results to export",
    }
}

LANG         = "hu"
SHOW_VIRTUAL = False


def t(key, *args):
    text = LANGUAGES.get(LANG, LANGUAGES["hu"]).get(key, key)
    if args:
        text = text.format(*args)
    return text


# ---------------------------------------------------------------------------
# Adapter szűrés
# ---------------------------------------------------------------------------

LOOPBACK_KEYWORDS      = ["loopback", "lo0", "software loopback"]
FORCE_VIRTUAL_KEYWORDS = ["xbox", "xbox wireless"]


def is_loopback(description):
    return any(k in description.lower() for k in LOOPBACK_KEYWORDS)


def is_force_virtual(description):
    return any(k in description.lower() for k in FORCE_VIRTUAL_KEYWORDS)


# ---------------------------------------------------------------------------
# Hálózati adatok lekérése – optimalizált, egyetlen PS hívás
# ---------------------------------------------------------------------------

def get_pc_info():
    pc_name = socket.gethostname()
    try:
        domain = subprocess.check_output(
            'wmic computersystem get domain', shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        ).decode().strip().split('\n')[-1].strip()
    except Exception:
        domain = "N/A"
    return pc_name, domain


# Egyetlen összevont PowerShell parancs – minimális modul betöltés
_PS_GET_ADAPTERS = (
    "Get-NetAdapter | ForEach-Object {"
    "$i=$_.ifIndex;"
    "$ip=Get-NetIPAddress -InterfaceIndex $i -AddressFamily IPv4 -ErrorAction SilentlyContinue;"
    "$cfg=Get-NetIPConfiguration -InterfaceIndex $i -ErrorAction SilentlyContinue;"
    "$dhcp=(Get-NetIPInterface -InterfaceIndex $i -AddressFamily IPv4 -ErrorAction SilentlyContinue).Dhcp;"
    "$dns=((Get-DnsClientServerAddress -InterfaceIndex $i -AddressFamily IPv4 -ErrorAction SilentlyContinue).ServerAddresses -join ',');"
    "Write-Output ("
    "$_.Name+'|'+"
    "$_.InterfaceDescription+'|'+"
    "$_.MacAddress+'|'+"
    "($ip.IPAddress -join ',')+' |'+"
    "($ip.PrefixLength -join ',')+' |'+"
    "$cfg.IPv4DefaultGateway.NextHop+'|'+"
    "$_.Status+'|'+"
    "$_.Virtual+'|'+"
    "$_.ConnectorPresent+'|'+"
    "$dhcp+'|'+"
    "$dns)"
    "}"
)

# Gyors állapot lekérés – csak IP és státusz, sokkal kisebb PS parancs
_PS_GET_STATUS = (
    "Get-NetAdapter | ForEach-Object {"
    "$i=$_.ifIndex;"
    "$ip=Get-NetIPAddress -InterfaceIndex $i -AddressFamily IPv4 -ErrorAction SilentlyContinue;"
    "Write-Output ($_.Name+'|'+$_.Status+'|'+($ip.IPAddress -join ','))"
    "}"
)


def _run_ps(cmd):
    """PowerShell parancs futtatása, eredmény soronként."""
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        ).decode("cp1250", errors="replace").strip()
        return [l.strip() for l in out.splitlines() if l.strip()]
    except Exception as e:
        print(f"PS hiba: {e}")
        return []


def get_network_adapters():
    """Teljes adapter lekérés – csak induláskor és frissítés gombra."""
    adapters = []
    lines    = _run_ps(_PS_GET_ADAPTERS)

    for line in lines:
        parts = line.split('|')
        if len(parts) < 7:
            continue

        name              = parts[0].strip()
        description       = parts[1].strip()
        mac               = parts[2].strip()
        ip                = parts[3].strip() if len(parts) > 3 and parts[3].strip() else "N/A"
        prefix            = parts[4].strip() if len(parts) > 4 else ""
        gateway           = parts[5].strip() if len(parts) > 5 and parts[5].strip() else "N/A"
        status            = parts[6].strip() if len(parts) > 6 else "Unknown"
        ps_virtual        = parts[7].strip().lower() == "true" if len(parts) > 7 else False
        connector_present = parts[8].strip().lower() == "true" if len(parts) > 8 else True
        dhcp              = parts[9].strip() if len(parts) > 9 else "Unknown"
        dns               = parts[10].strip() if len(parts) > 10 and parts[10].strip() else "N/A"

        if is_loopback(description):
            continue

        virtual = ps_virtual or (not connector_present) or is_force_virtual(description)

        subnet = "N/A"
        if prefix and prefix.isdigit():
            subnet = prefix_to_mask(int(prefix))

        desc_lower = description.lower()
        if any(k in desc_lower for k in ["wi-fi", "wireless", "wifi"]):
            adapter_type = "WiFi"
        elif any(k in desc_lower for k in ["ethernet", "realtek", "intel", "gigabit",
                                            "network connection", "family controller"]):
            adapter_type = "Ethernet"
        else:
            adapter_type = "Egyéb"

        ssid = ""
        if adapter_type == "WiFi" and status == "Up":
            try:
                wifi_out = subprocess.check_output(
                    "netsh wlan show interfaces", shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                ).decode("cp1250", errors="replace")
                for wline in wifi_out.splitlines():
                    if "SSID" in wline and "BSSID" not in wline:
                        ssid = wline.split(":", 1)[-1].strip()
                        break
            except Exception:
                ssid = ""

        adapters.append({
            "name": name, "type": adapter_type, "description": description,
            "mac": mac, "ip": ip, "subnet": subnet, "gateway": gateway,
            "status": status, "ssid": ssid, "virtual": virtual,
            "dhcp": dhcp, "dns": dns,
        })

    return adapters


def get_adapter_status():
    """Gyors állapot lekérés – csak névhez IP és státusz. Háttérfrissítéshez."""
    status_map = {}
    for line in _run_ps(_PS_GET_STATUS):
        parts = line.split('|')
        if len(parts) >= 2:
            name   = parts[0].strip()
            status = parts[1].strip()
            ip     = parts[2].strip() if len(parts) > 2 else "N/A"
            status_map[name] = {"status": status, "ip": ip}
    return status_map


def filter_adapters(adapters):
    if SHOW_VIRTUAL:
        return adapters
    return [a for a in adapters if not a["virtual"]]


def prefix_to_mask(prefix_length):
    if prefix_length < 0 or prefix_length > 32:
        return "N/A"
    bits = (0xFFFFFFFF >> (32 - prefix_length)) << (32 - prefix_length)
    return f"{(bits>>24)&0xFF}.{(bits>>16)&0xFF}.{(bits>>8)&0xFF}.{bits&0xFF}"


def mask_to_prefix(mask):
    try:
        return sum(bin(int(x)).count("1") for x in mask.split("."))
    except Exception:
        return 24


def auto_subnet(ip_first_octet):
    try:
        f = int(ip_first_octet)
        if 1 <= f <= 126:   return "255.0.0.0"
        if 128 <= f <= 191: return "255.255.0.0"
        return "255.255.255.0"
    except Exception:
        return "255.255.255.0"


def check_ip_overlap(adapters):
    active   = [a for a in adapters if a["ip"] != "N/A" and a["status"] == "Up"]
    warnings = []
    seen     = {}
    for a in active:
        parts = a["ip"].split(".")
        if len(parts) == 4:
            pfx = ".".join(parts[:3])
            if pfx in seen:
                warnings.append(t("warning_overlap", seen[pfx], a["name"], pfx))
            else:
                seen[pfx] = a["name"]
    return "\n".join(warnings)


# ---------------------------------------------------------------------------
# Háttérszálak
# ---------------------------------------------------------------------------

class FullRefreshThread(QThread):
    """Teljes adapter lekérés – induláskor és frissítés gombra."""
    finished = pyqtSignal(list, str, str, str)

    def run(self):
        all_adapters    = get_network_adapters()
        filtered        = filter_adapters(all_adapters)
        warning         = check_ip_overlap(filtered)
        pc_name, domain = get_pc_info()
        self.finished.emit(all_adapters, warning, pc_name, domain)


class StatusRefreshThread(QThread):
    """Gyors állapot lekérés – 5 másodpercenként, nem érinti a beviteli mezőket."""
    finished = pyqtSignal(dict)

    def run(self):
        status_map = get_adapter_status()
        self.finished.emit(status_map)


# ---------------------------------------------------------------------------
# IP oktet beviteli mező
# ---------------------------------------------------------------------------

class OctetField(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.next_field = None
        self.prev_field = None
        self.setMaxLength(3)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedWidth(46)
        self.setFixedHeight(28)
        self.setValidator(QIntValidator(0, 255, self))
        self._error = False
        self.textChanged.connect(self._validate)
        self.setStyleSheet(self._normal_style())
        self.external_next = None  # Következő sor első mezője

    def _normal_style(self):
        return """
            QLineEdit {
                background-color: #16213e; color: #ffffff;
                border: 1px solid #333; border-radius: 4px;
                font-size: 13px; padding: 2px;
            }
            QLineEdit:focus { border: 1px solid #4a9eff; }
            QLineEdit:disabled {
                background-color: #0f0f1a; color: #444; border: 1px solid #222;
            }
        """

    def _error_style(self):
        return """
            QLineEdit {
                background-color: #3a0000; color: #ff6666;
                border: 1px solid #ff3333; border-radius: 4px;
                font-size: 13px; padding: 2px;
            }
            QLineEdit:focus { border: 1px solid #ff3333; }
        """

    def _validate(self, text):
        if text == "":
            self._error = False
            self.setStyleSheet(self._normal_style())
            return
        try:
            val = int(text)
            if 0 <= val <= 255:
                self._error = False
                self.setStyleSheet(self._normal_style())
            else:
                self._error = True
                self.setStyleSheet(self._error_style())
        except ValueError:
            self._error = True
            self.setStyleSheet(self._error_style())

    def is_valid(self):
        if self.text() == "":
            return False
        try:
            return 0 <= int(self.text()) <= 255
        except ValueError:
            return False

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key.Key_Period, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.next_field:
                self.next_field.setFocus()
                self.next_field.selectAll()
            elif self.external_next:
                # Ha nincs következő blokk de van külső következő mező
                self.external_next.setFocus()
                self.external_next.selectAll()
            return
        if key == Qt.Key.Key_Backspace and self.text() == "" and self.prev_field:
            self.prev_field.setFocus()
            self.prev_field.selectAll()
            return
        super().keyPressEvent(event)
        if len(self.text()) == 3 and key not in (
            Qt.Key.Key_Backspace, Qt.Key.Key_Delete,
            Qt.Key.Key_Left, Qt.Key.Key_Right
        ):
            if self.next_field:
                self.next_field.setFocus()
                self.next_field.selectAll()
            elif self.external_next:
                self.external_next.setFocus()
                self.external_next.selectAll()

def make_octet_row():
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(2)
    fields = [OctetField() for _ in range(4)]
    for i in range(4):
        if i > 0: fields[i].prev_field = fields[i-1]
        if i < 3: fields[i].next_field = fields[i+1]
    for i, f in enumerate(fields):
        layout.addWidget(f)
        if i < 3:
            dot = QLabel(".")
            dot.setStyleSheet("color:#666; font-size:14px;")
            dot.setFixedWidth(6)
            layout.addWidget(dot)
    layout.addStretch()
    return widget, fields


# ---------------------------------------------------------------------------
# IP beállítás fül
# ---------------------------------------------------------------------------

class IPSettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_adapter = None
        self._static_mode     = False
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")

        content = QWidget()
        main    = QVBoxLayout(content)
        main.setContentsMargins(24, 20, 24, 20)
        main.setSpacing(16)

        main.addWidget(self._section_label("ip_current_title"))

        info_frame = QFrame()
        info_frame.setStyleSheet(
            "QFrame { background:#1a1a2e; border:1px solid #2a2a4a; border-radius:10px; }"
        )
        info_grid = QGridLayout(info_frame)
        info_grid.setContentsMargins(16, 12, 16, 12)
        info_grid.setVerticalSpacing(6)
        info_grid.setHorizontalSpacing(16)

        self._info_labels = {}
        for i, key in enumerate([
            "ip_adapter_name", "ip_desc", "ip_mac",
            "ip_address", "ip_subnet", "ip_gateway",
            "ip_type", "ip_dns",
        ]):
            lbl = QLabel(f"{t(key)}:")
            lbl.setStyleSheet("color:#666; font-size:11px;")
            lbl.setFixedWidth(130)
            val = QLabel("–")
            val.setStyleSheet("color:#cccccc; font-size:11px;")
            val.setWordWrap(True)
            info_grid.addWidget(lbl, i, 0)
            info_grid.addWidget(val, i, 1)
            self._info_labels[key] = (lbl, val)

        main.addWidget(info_frame)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#2a2a4a; margin:4px 0;")
        main.addWidget(sep)

        main.addWidget(self._section_label("ip_set_title"))

        mode_row = QHBoxLayout()
        self.btn_dhcp   = QPushButton(t("ip_btn_dhcp"))
        self.btn_static = QPushButton(t("ip_btn_static"))
        for btn in [self.btn_dhcp, self.btn_static]:
            btn.setFixedHeight(30)
            btn.setFixedWidth(100)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_dhcp.clicked.connect(lambda: self._set_mode(False))
        self.btn_static.clicked.connect(lambda: self._set_mode(True))
        mode_row.addWidget(self.btn_dhcp)
        mode_row.addWidget(self.btn_static)
        mode_row.addStretch()
        main.addLayout(mode_row)

        self.static_widget = QWidget()
        sl = QVBoxLayout(self.static_widget)
        sl.setContentsMargins(0, 8, 0, 0)
        sl.setSpacing(10)

        for attr, key in [
            ("ip_fields", "ip_new_ip"),
            ("sn_fields", "ip_new_subnet"),
            ("gw_fields", "ip_new_gateway"),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(f"{t(key)}:")
            lbl.setFixedWidth(130)
            lbl.setStyleSheet("color:#888; font-size:11px;")
            w, fields = make_octet_row()
            setattr(self, attr, fields)
            row.addWidget(lbl)
            row.addWidget(w)
            sl.addLayout(row)

        self.ip_fields[0].textChanged.connect(self._auto_subnet)
        # IP utolsó blokkjáról subnet első blokkjára ugrás Enter/pont esetén
        self.ip_fields[3].external_next = self.sn_fields[0]
        # Subnet utolsó blokkjáról gateway első blokkjára
        self.sn_fields[3].external_next = self.gw_fields[0]
        main.addWidget(self.static_widget)
        self.static_widget.setVisible(False)

        apply_row = QHBoxLayout()
        self.btn_apply = QPushButton(t("ip_apply"))
        self.btn_apply.setFixedHeight(34)
        self.btn_apply.setFixedWidth(140)
        self.btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_apply.clicked.connect(self._apply)
        apply_row.addStretch()
        apply_row.addWidget(self.btn_apply)
        apply_row.addStretch()
        main.addLayout(apply_row)

        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("font-size:11px; padding:4px;")
        self.lbl_status.setVisible(False)
        main.addWidget(self.lbl_status)

        main.addStretch()
        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self._update_mode_buttons()

    def _section_label(self, key):
        lbl = QLabel(t(key))
        lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl.setStyleSheet("color:#4a9eff; font-size:12px;")
        return lbl

    def _set_mode(self, static):
        self._static_mode = static
        self.static_widget.setVisible(static)
        self._update_mode_buttons()
        # Automatikus fókusz az első IP mezőre statikus módban
        if static:
            QTimer.singleShot(50, lambda: (
                self.ip_fields[0].setFocus(),
                self.ip_fields[0].selectAll()
            ))
            
    def _update_mode_buttons(self):
        active = (
            "QPushButton { background-color:#1e3a5f; color:#4a9eff; "
            "border:1px solid #4a9eff; border-radius:4px; font-size:12px; }"
        )
        inactive = (
            "QPushButton { background-color:#1a1a2e; color:#555; "
            "border:1px solid #333; border-radius:4px; font-size:12px; } "
            "QPushButton:hover { color:#aaa; border-color:#555; }"
        )
        self.btn_dhcp.setStyleSheet(active if not self._static_mode else inactive)
        self.btn_static.setStyleSheet(active if self._static_mode else inactive)

    def _auto_subnet(self, text):
        if not self._static_mode:
            return
        if all(f.text() == "" for f in self.sn_fields):
            parts = auto_subnet(text).split(".")
            for i, f in enumerate(self.sn_fields):
                f.setText(parts[i])

    def load_adapter(self, adapter):
        self._current_adapter = adapter
        self._show_info(adapter)
        self._prefill_static(adapter)
        is_dhcp = adapter.get("dhcp", "").lower() == "enabled"
        self._set_mode(not is_dhcp)

    def update_info_only(self, adapter):
        """Csak az infó panel frissítése – beviteli mezőket nem érinti."""
        self._current_adapter = adapter
        self._show_info(adapter)

    def _show_info(self, a):
        is_dhcp = a.get("dhcp", "").lower() == "enabled"
        values  = {
            "ip_adapter_name": a.get("name", "–"),
            "ip_desc":         a.get("description", "–"),
            "ip_mac":          a.get("mac", "–"),
            "ip_address":      a.get("ip", "–"),
            "ip_subnet":       a.get("subnet", "–"),
            "ip_gateway":      a.get("gateway", "–"),
            "ip_type":         t("ip_type_dhcp") if is_dhcp else t("ip_type_static"),
            "ip_dns":          a.get("dns", "N/A"),
        }
        for key, val in values.items():
            if key in self._info_labels:
                self._info_labels[key][1].setText(val if val else "–")

    def _prefill_static(self, a):
        for fields, value in [
            (self.ip_fields, a.get("ip", "")),
            (self.sn_fields, a.get("subnet", "")),
            (self.gw_fields, a.get("gateway", "")),
        ]:
            parts = value.split(".") if value and value != "N/A" else ["", "", "", ""]
            for i, f in enumerate(fields):
                f.setText(parts[i] if i < len(parts) else "")

    def _apply(self):
        if not self._current_adapter:
            self._show_status(t("ip_no_adapter"), error=True)
            return

        name = self._current_adapter.get("name", "")

        try:
            if not self._static_mode:
                ps = (
                    f'$a=[string]"{name}";'
                    f'Remove-NetRoute -InterfaceAlias $a -Confirm:$false '
                    f'-ErrorAction SilentlyContinue;'
                    f'Remove-NetIPAddress -InterfaceAlias $a -AddressFamily IPv4 '
                    f'-Confirm:$false -ErrorAction SilentlyContinue;'
                    f'Set-NetIPInterface -InterfaceAlias $a -Dhcp Enabled '
                    f'-Confirm:$false -ErrorAction SilentlyContinue'
                )
            else:
                ip     = ".".join(f.text() for f in self.ip_fields)
                subnet = ".".join(f.text() for f in self.sn_fields)
                gw     = ".".join(f.text() for f in self.gw_fields)
                prefix = mask_to_prefix(subnet)

                # IP és subnet validáció
                invalid_fields = []
                for fields in [self.ip_fields, self.sn_fields]:
                    for f in fields:
                        if not f.is_valid():
                            invalid_fields.append(f)

                if invalid_fields:
                    invalid_fields[0].setFocus()
                    invalid_fields[0].selectAll()
                    self._show_status(
                        t("ip_apply_err",
                        "Érvénytelen érték – csak 0-255 közötti számok megengedettek"),
                        error=True
                    )
                    return

                # Gateway validáció
                if all(f.text().strip() for f in self.gw_fields):
                    try:
                        import ipaddress
                        network = ipaddress.IPv4Network(f"{ip}/{prefix}", strict=False)
                        gw_obj  = ipaddress.IPv4Address(gw)
                        if gw_obj not in network:
                            self._show_status(
                                t("ip_apply_err",
                                f"Az átjáró ({gw}) nem ugyanazon az alhálózaton van "
                                f"mint az IP ({ip}/{prefix})"),
                                error=True
                            )
                            return
                    except ValueError as e:
                        self._show_status(t("ip_apply_err", str(e)), error=True)
                        return

                gw_param = f'-DefaultGateway "{gw}"' if all(
                    f.text().strip() for f in self.gw_fields
                ) else ""

                ps = (
                    f'$a=[string]"{name}";'
                    f'Remove-NetRoute -InterfaceAlias $a -Confirm:$false '
                    f'-ErrorAction SilentlyContinue;'
                    f'Remove-NetIPAddress -InterfaceAlias $a -AddressFamily IPv4 '
                    f'-Confirm:$false -ErrorAction SilentlyContinue;'
                    f'Set-NetIPInterface -InterfaceAlias $a -Dhcp Disabled '
                    f'-Confirm:$false -ErrorAction SilentlyContinue;'
                    f'New-NetIPAddress -InterfaceAlias $a -IPAddress "{ip}" '
                    f'-PrefixLength {prefix} {gw_param} -ErrorAction Stop'
                )

            _log(f"PS parancs: {ps}")

            import tempfile
            script_path = os.path.join(tempfile.gettempdir(), "mipt_apply.ps1")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(ps)

            _log(f"Script fájl: {script_path}")

            result = subprocess.run(
                [
                    "powershell", "-NoProfile", "-NonInteractive",
                    "-ExecutionPolicy", "Bypass",
                    "-File", script_path
                ],
                creationflags=subprocess.CREATE_NO_WINDOW,
                capture_output=True,
                text=True
            )

            _log(f"Visszatérési kód: {result.returncode}")
            if result.stderr:
                _log(f"Hiba kimenet: {result.stderr.strip()}")
            if result.stdout:
                _log(f"Kimenet: {result.stdout.strip()}")

            if result.returncode != 0:
                err     = result.stderr.strip().splitlines()
                err_msg = err[-1] if err else "Ismeretlen hiba"
                self._show_status(t("ip_apply_err", err_msg), error=True)
            else:
                self._show_status(t("ip_apply_ok"), error=False)

        except Exception as e:
            _log(f"Kivétel: {e}")
            self._show_status(t("ip_apply_err", str(e)), error=True)

    def _show_status(self, msg, error=False):
        color = "#F44336" if error else "#4CAF50"
        self.lbl_status.setStyleSheet(f"font-size:11px; color:{color}; padding:4px;")
        self.lbl_status.setText(msg)
        self.lbl_status.setVisible(True)
        QTimer.singleShot(5000, lambda: self.lbl_status.setVisible(False))

    def update_texts(self):
        self.btn_dhcp.setText(t("ip_btn_dhcp"))
        self.btn_static.setText(t("ip_btn_static"))
        self.btn_apply.setText(t("ip_apply"))
        for key, (lbl, _) in self._info_labels.items():
            lbl.setText(f"{t(key)}:")
        self._update_mode_buttons()


# ---------------------------------------------------------------------------
# Ping fül
# ---------------------------------------------------------------------------

class PingThread(QThread):
    """Háttérszálon futtatja a pinget, soronként küldi az eredményt."""
    output_line = pyqtSignal(str)
    finished    = pyqtSignal()

    def __init__(self, ip):
        super().__init__()
        self.ip = ip

    def run(self):
        try:
            proc = subprocess.Popen(
                ["ping", "-n", "4", self.ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                encoding="cp1250",
                errors="replace"
            )
            for line in proc.stdout:
                line = line.rstrip()
                if line:
                    self.output_line.emit(line)
            proc.wait()
        except Exception as e:
            self.output_line.emit(f"Hiba: {e}")
        finally:
            self.finished.emit()


class PingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_adapter = None
        self._ping_thread     = None
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")

        content = QWidget()
        main    = QVBoxLayout(content)
        main.setContentsMargins(24, 20, 24, 20)
        main.setSpacing(16)

        # Cím
        self.lbl_title = QLabel(t("ping_title"))
        self.lbl_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color:#4a9eff; font-size:12px;")
        main.addWidget(self.lbl_title)

        # IP beviteli sor
        ip_row = QHBoxLayout()
        self.lbl_target = QLabel(f"{t('ping_target')}:")
        self.lbl_target.setFixedWidth(130)
        self.lbl_target.setStyleSheet("color:#888; font-size:11px;")
        ip_row.addWidget(self.lbl_target)

        self.ip_widget, self.ip_fields = make_octet_row()
        ip_row.addWidget(self.ip_widget)
        ip_row.addStretch()
        main.addLayout(ip_row)

        # Ping gomb
        btn_row = QHBoxLayout()
        self.btn_ping = QPushButton(t("ping_btn_start"))
        self.btn_ping.setFixedHeight(34)
        self.btn_ping.setFixedWidth(140)
        self.btn_ping.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ping.setStyleSheet("""
            QPushButton {
                background-color:#1e3a5f; color:#4a9eff;
                border:1px solid #4a9eff; border-radius:4px; font-size:12px;
            }
            QPushButton:hover { background-color:#4a9eff; color:#ffffff; }
            QPushButton:disabled { background-color:#1a1a2e; color:#444; border-color:#333; }
        """)
        self.btn_ping.clicked.connect(self._start_ping)
        btn_row.addWidget(self.btn_ping)
        btn_row.addStretch()
        main.addLayout(btn_row)

        # Eredmény box
        self.result_box = QLabel("")
        self.result_box.setStyleSheet("""
            QLabel {
                background-color: #0d1117;
                color: #cccccc;
                border: 1px solid #2a2a4a;
                border-radius: 6px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                padding: 12px;
            }
        """)
        self.result_box.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.result_box.setWordWrap(True)
        self.result_box.setMinimumHeight(120)
        self.result_box.setFixedHeight(160)
        main.addWidget(self.result_box)

        # Törlés gomb
        clear_row = QHBoxLayout()
        self.btn_clear = QPushButton(t("ping_btn_clear"))
        self.btn_clear.setFixedHeight(26)
        self.btn_clear.setFixedWidth(80)
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color:#1a1a2e; color:#666;
                border:1px solid #333; border-radius:4px; font-size:11px;
            }
            QPushButton:hover { color:#aaa; border-color:#555; }
        """)
        self.btn_clear.clicked.connect(self._clear)
        clear_row.addWidget(self.btn_clear)
        clear_row.addStretch()
        main.addLayout(clear_row)

        main.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def load_adapter(self, adapter):
        """Betölti a kiválasztott adapter IP-jét a ping mezőkbe."""
        self._current_adapter = adapter
        ip = adapter.get("ip", "")
        if ip and ip != "N/A":
            parts = ip.split(".")
            if len(parts) == 4:
                # Csak az első 3 oktet töltődik be, az utolsó üres marad
                for i in range(3):
                    self.ip_fields[i].setText(parts[i])
                self.ip_fields[3].setText("")
                self.ip_fields[3].setFocus()
                self.ip_fields[3].selectAll()

    def _clear(self):
        self.result_box.setText("")

    def _start_ping(self):
        if not self._current_adapter:
            self.result_box.setText(t("ping_no_adapter"))
            return

        # Validáció
        invalid = [f for f in self.ip_fields if not f.is_valid()]
        if invalid:
            invalid[0].setFocus()
            invalid[0].selectAll()
            self.result_box.setText(t("ping_invalid_ip"))
            return

        ip = ".".join(f.text() for f in self.ip_fields)

        # Box törlése és gomb letiltása
        self.result_box.setText(t("ping_running"))
        self.btn_ping.setEnabled(False)

        # Ping thread indítása
        self._ping_thread = PingThread(ip)
        self._ping_thread.output_line.connect(self._on_line)
        self._ping_thread.finished.connect(self._on_done)
        self._ping_thread.start()

    def _on_line(self, line):
        current = self.result_box.text()
        if current == t("ping_running"):
            self.result_box.setText(line)
        else:
            self.result_box.setText(current + "\n" + line)

    def _on_done(self):
        self.btn_ping.setEnabled(True)

    def update_texts(self):
        self.lbl_title.setText(t("ping_title"))
        self.lbl_target.setText(f"{t('ping_target')}:")
        self.btn_ping.setText(t("ping_btn_start"))
        self.btn_clear.setText(t("ping_btn_clear"))

# ---------------------------------------------------------------------------
# MAC gyártó adatbázis betöltése
# ---------------------------------------------------------------------------

_MAC_DB = {}

def load_mac_db():
    """Betölti a MAC gyártó adatbázist."""
    global _MAC_DB
    db_path = asset("mac_vendors.csv")
    if not os.path.exists(db_path):
        print(f"MAC adatbázis nem található: {db_path}")
        return
    try:
        import csv
        with open(db_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                prefix = row.get("Mac Prefix", "").strip().upper()
                vendor = row.get("Vendor Name", "").strip()
                if prefix and vendor:
                    _MAC_DB[prefix] = vendor
        print(f"MAC adatbázis betöltve: {len(_MAC_DB)} gyártó")
    except Exception as e:
        print(f"MAC adatbázis hiba: {e}")


def get_vendor(mac):
    """MAC cím alapján gyártó lekérése."""
    if not mac or mac == "N/A":
        return "–"
    # Egységesítés AA:BB:CC formátumra
    clean = re.sub(r'[:\-\.]', '', mac.strip().upper())
    if len(clean) >= 6:
        prefix = f"{clean[0:2]}:{clean[2:4]}:{clean[4:6]}"
        return _MAC_DB.get(prefix, "–")
    return "–"


# ---------------------------------------------------------------------------
# Scan háttérszál
# ---------------------------------------------------------------------------

class ScanThread(QThread):
    result_found = pyqtSignal(dict)   # Egy találat
    progress     = pyqtSignal(int, int)  # aktuális, összes
    finished     = pyqtSignal(int)    # találatok száma

    def __init__(self, base_ip, start_ip, end_ip, max_workers=25):
        super().__init__()
        self.base_ip     = base_ip
        self.start_ip    = start_ip
        self.end_ip      = end_ip
        self.max_workers = max_workers
        self._stop       = False

    def stop(self):
        self._stop = True

    def run(self):
        import concurrent.futures

        total   = self.end_ip - self.start_ip + 1
        targets = [f"{self.base_ip}.{i}" for i in range(self.start_ip, self.end_ip + 1)]
        done    = 0
        found   = 0

        # Saját IP-MAC párok előre lekérése
        own_mac_map = {}
        try:
            ps_out = subprocess.check_output(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                "Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | "
                "ForEach-Object { $idx=$_.InterfaceIndex; $ip=$_.IPAddress; "
                "$mac=(Get-NetAdapter | Where-Object {$_.ifIndex -eq $idx}).MacAddress; "
                "Write-Output ($ip+'|'+$mac) }"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stderr=subprocess.DEVNULL,
                timeout=5
            ).decode("cp1250", errors="replace")
            for line in ps_out.splitlines():
                parts = line.strip().split("|")
                if len(parts) == 2 and parts[1].strip():
                    own_mac_map[parts[0].strip()] = parts[1].strip().upper().replace("-", ":")
        except Exception:
            pass

        def check_host(ip):
            # Ping
            try:
                result = subprocess.run(
                    ["ping", "-n", "1", "-w", "500", ip],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode != 0:
                    return None
            except Exception:
                return None

            # Kis várakozás hogy az ARP cache feltöltődjön
            import time
            time.sleep(0.2)

            mac    = "–"
            vendor = "–"

            # Saját gép MAC-ja
            if ip in own_mac_map:
                mac    = own_mac_map[ip]
                vendor = get_vendor(mac)
            else:
                # ARP tábla – 3 próbálkozás
                for attempt in range(3):
                    try:
                        arp_out = subprocess.check_output(
                            ["arp", "-a"],  # Teljes ARP tábla, nem csak egy IP
                            creationflags=subprocess.CREATE_NO_WINDOW,
                            stderr=subprocess.DEVNULL,
                            timeout=2
                        ).decode("cp1250", errors="replace")

                        for line in arp_out.splitlines():
                            # Rugalmasabb IP keresés a sorban
                            if ip in line and re.search(
                                r'([0-9a-fA-F]{2}[:\-]){5}[0-9a-fA-F]{2}', line
                            ):
                                match = re.search(
                                    r'([0-9a-fA-F]{2}[:\-]){5}[0-9a-fA-F]{2}', line
                                )
                                if match:
                                    mac    = match.group(0).upper().replace("-", ":")
                                    vendor = get_vendor(mac)
                                    break

                        if mac != "–":
                            break
                        time.sleep(0.1)
                    except Exception:
                        break

            # Hostname
            hostname = ip
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except Exception:
                pass

            return {"ip": ip, "mac": mac, "hostname": hostname, "vendor": vendor}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(check_host, ip): ip for ip in targets}

            for future in concurrent.futures.as_completed(futures):
                if self._stop:
                    for f in futures:
                        f.cancel()
                    break

                done += 1
                self.progress.emit(done, total)

                result = future.result()
                if result:
                    found += 1
                    self.result_found.emit(result)

        self.finished.emit(found)

# ---------------------------------------------------------------------------
# Rendezhető táblázat sor
# ---------------------------------------------------------------------------

class ScanResultTable(QWidget):
    COLS   = ["scan_col_ip", "scan_col_mac", "scan_col_hostname", "scan_col_vendor"]
    FIELDS = ["ip", "mac", "hostname", "vendor"]
    WIDTHS = [130, 150, 200, 220]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows     = []
        self._sort_col = 0
        self._sort_asc = True
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Fejléc splitter
        self._header_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._header_splitter.setFixedHeight(28)
        self._header_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #2a2a4a;
                width: 3px;
            }
            QSplitter::handle:hover {
                background-color: #4a9eff;
            }
        """)
        self._header_splitter.setChildrenCollapsible(False)
        self._header_splitter.splitterMoved.connect(self._on_splitter_moved)

        self._header_btns = []
        for i, key in enumerate(self.COLS):
            btn = QPushButton(t(key))
            btn.setFlat(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumWidth(60)
            btn.clicked.connect(lambda _, col=i: self._sort_by(col))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a1a2e;
                    color: #4a9eff;
                    border: none;
                    border-bottom: 1px solid #2a2a4a;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 10px;
                    text-align: left;
                }
                QPushButton:hover { background-color: #16213e; }
            """)
            self._header_splitter.addWidget(btn)
            self._header_btns.append(btn)

        self._header_splitter.setSizes(self.WIDTHS)
        layout.addWidget(self._header_splitter)

        # Sorok scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        self.scroll.horizontalScrollBar().setVisible(False)

        self.rows_widget = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_widget)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(0)
        self.rows_layout.addStretch()
        self.scroll.setWidget(self.rows_widget)
        layout.addWidget(self.scroll, stretch=1)

    def _on_splitter_moved(self, pos, index):
        """Fejléc splitter mozgatásakor frissíti a sorokat."""
        self._redraw()

    def _get_col_widths(self):
        return self._header_splitter.sizes()

    def _sort_by(self, col):
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        self._refresh_header_labels()
        self._redraw()

    def _refresh_header_labels(self):
        for i, btn in enumerate(self._header_btns):
            label = t(self.COLS[i])
            if i == self._sort_col:
                label += " ▲" if self._sort_asc else " ▼"
            btn.setText(label)

    def add_row(self, data):
        self._rows.append(data)
        self._redraw()

    def clear(self):
        self._rows.clear()
        self._redraw()

    def get_rows(self):
        return self._rows

    def _redraw(self):
        while self.rows_layout.count() > 1:
            item = self.rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        key = self.FIELDS[self._sort_col]

        def sort_key(r):
            val = r.get(key, "")
            if key == "ip":
                try:
                    return tuple(int(x) for x in val.split("."))
                except Exception:
                    return (0, 0, 0, 0)
            return val

        rows      = sorted(self._rows, key=sort_key, reverse=not self._sort_asc)
        col_widths = self._get_col_widths()

        for i, row in enumerate(rows):
            bg         = "#0f0f1a" if i % 2 == 0 else "#13131f"
            row_widget = QWidget()
            row_widget.setStyleSheet(f"background:{bg};")
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(0)

            for j, field in enumerate(self.FIELDS):
                lbl = QLabel(row.get(field, "–"))
                lbl.setFixedWidth(col_widths[j] if j < len(col_widths) else 120)
                lbl.setStyleSheet(
                    "color:#cccccc; font-size:11px; padding:2px 10px;"
                    "border-right:1px solid #1a1a2e;"
                )
                if field in ("vendor", "hostname"):
                    lbl.setWordWrap(True)
                lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
                row_layout.addWidget(lbl)

            row_layout.addStretch()
            self.rows_layout.insertWidget(self.rows_layout.count() - 1, row_widget)

    def update_texts(self):
        self._refresh_header_labels()


# ---------------------------------------------------------------------------
# Scan fül
# ---------------------------------------------------------------------------

class ScanTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_adapter = None
        self._scan_thread     = None
        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(24, 20, 24, 20)
        main.setSpacing(12)

        # Cím
        self.lbl_title = QLabel(t("scan_title"))
        self.lbl_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color:#4a9eff; font-size:12px;")
        main.addWidget(self.lbl_title)

        # Tartomány sor
        range_row = QHBoxLayout()

        self.lbl_from = QLabel(f"{t('scan_range_from')}:")
        self.lbl_from.setStyleSheet("color:#888; font-size:11px;")
        self.lbl_from.setFixedWidth(110)
        range_row.addWidget(self.lbl_from)

        self.from_widget, self.from_fields = make_octet_row()
        range_row.addWidget(self.from_widget)

        range_row.addSpacing(16)

        self.lbl_to = QLabel(f"{t('scan_range_to')}:")
        self.lbl_to.setStyleSheet("color:#888; font-size:11px;")
        self.lbl_to.setFixedWidth(110)
        range_row.addWidget(self.lbl_to)

        self.to_widget, self.to_fields = make_octet_row()
        range_row.addWidget(self.to_widget)
        range_row.addStretch()
        main.addLayout(range_row)

        # Gombok
        btn_row = QHBoxLayout()
        self.btn_start = QPushButton(t("scan_btn_start"))
        self.btn_stop  = QPushButton(t("scan_btn_stop"))
        self.btn_export = QPushButton(t("scan_btn_export"))
        self.btn_clear  = QPushButton(t("scan_btn_clear"))

        for btn, color in [
            (self.btn_start,  "#4a9eff"),
            (self.btn_stop,   "#F44336"),
            (self.btn_export, "#4CAF50"),
            (self.btn_clear,  "#555"),
        ]:
            btn.setFixedHeight(30)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color:#1a1a2e; color:{color};
                    border:1px solid {color}; border-radius:4px; font-size:11px;
                    padding: 0 14px;
                }}
                QPushButton:hover {{ background-color:#16213e; }}
                QPushButton:disabled {{ color:#333; border-color:#333; }}
            """)

        self.btn_start.clicked.connect(self._start_scan)
        self.btn_stop.clicked.connect(self._stop_scan)
        self.btn_export.clicked.connect(self._export)
        self.btn_clear.clicked.connect(self._clear)
        self.btn_stop.setEnabled(False)

        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)
        btn_row.addSpacing(16)
        btn_row.addWidget(self.btn_export)
        btn_row.addWidget(self.btn_clear)
        btn_row.addStretch()
        main.addLayout(btn_row)

        # Státusz sor
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color:#888; font-size:11px;")
        main.addWidget(self.lbl_status)

        # Eredmény táblázat
        self.table = ScanResultTable()
        main.addWidget(self.table, stretch=1)

    def load_adapter(self, adapter):
        self._current_adapter = adapter
        ip = adapter.get("ip", "")
        if ip and ip != "N/A":
            parts = ip.split(".")
            if len(parts) == 4:
                # Első 3 oktet mindkét sorba
                for i in range(3):
                    self.from_fields[i].setText(parts[i])
                    self.to_fields[i].setText(parts[i])
                # Alapértelmezett tartomány: 1-254
                self.from_fields[3].setText("1")
                self.to_fields[3].setText("254")

    def _start_scan(self):
        if not self._current_adapter:
            self.lbl_status.setText(t("scan_no_adapter"))
            return

        # Validáció
        for fields in [self.from_fields, self.to_fields]:
            invalid = [f for f in fields if not f.is_valid()]
            if invalid:
                invalid[0].setFocus()
                invalid[0].selectAll()
                return

        base_ip = ".".join(f.text() for f in self.from_fields[:3])
        start   = int(self.from_fields[3].text())
        end     = int(self.to_fields[3].text())

        if start > end:
            self.from_fields[3].setFocus()
            return

        self.table.clear()
        self.lbl_status.setText(t("scan_running", 0, end - start + 1))
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self._scan_thread = ScanThread(base_ip, start, end, max_workers=25)
        self._scan_thread.result_found.connect(self._on_result)
        self._scan_thread.progress.connect(self._on_progress)
        self._scan_thread.finished.connect(self._on_done)
        self._scan_thread.start()

    def _stop_scan(self):
        if self._scan_thread:
            self._scan_thread.stop()

    def _on_result(self, data):
        self.table.add_row(data)

    def _on_progress(self, done, total):
        self.lbl_status.setText(t("scan_running", done, total))

    def _on_done(self, found):
        stopped = self._scan_thread and self._scan_thread._stop
        self.lbl_status.setText(
            t("scan_stopped", found) if stopped else t("scan_done", found)
        )
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def _clear(self):
        self.table.clear()
        self.lbl_status.setText("")

    def _export(self):
        rows = self.table.get_rows()
        if not rows:
            self.lbl_status.setText(t("scan_no_results"))
            return

        from datetime import datetime
        from PyQt6.QtWidgets import QFileDialog

        date_str     = datetime.now().strftime("%Y-%m-%d_%H-%M")
        default_name = f"scan_{date_str}.csv"
        documents    = os.path.join(os.path.expanduser("~"), "Documents")
        default_path = os.path.join(documents, default_name)

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            t("scan_btn_export"),
            default_path,
            "CSV fájl (*.csv)"
        )

        if not filepath:
            return  # Felhasználó megszakította

        try:
            import csv as csv_module
            with open(filepath, "w", encoding="utf-8", newline="") as f:
                writer = csv_module.writer(f)
                writer.writerow(["IP Address", "MAC Address", "Hostname", "Vendor"])
#                writer.writerow([
#                    t("scan_col_ip"), t("scan_col_mac"),
#                    t("scan_col_hostname"), t("scan_col_vendor")
#                ])
                for row in rows:
                    writer.writerow([
                        row.get("ip", ""),
                        row.get("mac", ""),
                        row.get("hostname", ""),
                        row.get("vendor", ""),
                    ])
            self.lbl_status.setText(t("scan_export_ok", filepath))
        except Exception as e:
            self.lbl_status.setText(t("scan_export_err", str(e)))

    def update_texts(self):
        self.lbl_title.setText(t("scan_title"))
        self.lbl_from.setText(f"{t('scan_range_from')}:")
        self.lbl_to.setText(f"{t('scan_range_to')}:")
        self.btn_start.setText(t("scan_btn_start"))
        self.btn_stop.setText(t("scan_btn_stop"))
        self.btn_export.setText(t("scan_btn_export"))
        self.btn_clear.setText(t("scan_btn_clear"))
        self.table.update_texts()

# ---------------------------------------------------------------------------
# Névjegy ablak
# ---------------------------------------------------------------------------

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("about_title"))
        self.setFixedSize(360, 260)
        self.setModal(True)
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(10)

        # Program neve
        title = QLabel(t("window_title"))
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color:#4a9eff;")
        layout.addWidget(title)

        # Elválasztó
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#2a2a4a;")
        layout.addWidget(sep)

        # Verzió és szerző
        for key in ["about_version", "about_author", "about_desc"]:
            lbl = QLabel(t(key))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color:#aaaaaa; font-size:12px;")
            layout.addWidget(lbl)

        # GitHub link
        github_lbl = QLabel(t("about_github"))
        github_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        github_lbl.setStyleSheet("color:#888; font-size:11px; margin-top:4px;")
        layout.addWidget(github_lbl)

        github_url = "https://github.com/Nozy82/MicroIPTool"  # <- ide írd be a pontos GitHub URL-t
        link = QLabel(f'<a href="{github_url}" style="color:#4a9eff;">{github_url}</a>')
        link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        link.setOpenExternalLinks(True)
        link.setStyleSheet("font-size:11px;")
        layout.addWidget(link)

        layout.addStretch()

        # Bezárás gomb
        btn = QPushButton(t("about_close"))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self.close)
        btn.setFixedHeight(32)
        layout.addWidget(btn)

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog { background-color:#0f0f1a; color:#cccccc; font-family:'Segoe UI'; }
            QLabel  { color:#cccccc; font-size:12px; }
            QPushButton {
                background-color:#1e3a5f; color:#4a9eff;
                border:1px solid #4a9eff; border-radius:4px;
                font-size:12px; padding:4px 18px;
            }
            QPushButton:hover { background-color:#4a9eff; color:#ffffff; }
        """)


# ---------------------------------------------------------------------------
# Adapter kártya
# ---------------------------------------------------------------------------

class AdapterCard(QFrame):
    def __init__(self, adapter_data, parent=None):
        super().__init__(parent)
        self.adapter_data = adapter_data
        self.selected     = False
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_ui()
        self._apply_style(selected=False)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)
        a = self.adapter_data

        header   = QHBoxLayout()
        icon     = {"WiFi": "📶", "Ethernet": "🔌"}.get(a["type"], "🖧")
        name_lbl = QLabel(f"{icon}  {a['name']}")
        name_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        name_lbl.setWordWrap(True)
        header.addWidget(name_lbl, stretch=1)

        if a["virtual"]:
            badge = QLabel(f" {t('adapter_badge_virtual')} ")
            badge.setStyleSheet(
                "background:#3a2a00; color:#ffaa00; border:1px solid #ffaa00;"
                "border-radius:3px; font-size:10px; padding:1px 4px;"
            )
        else:
            badge = QLabel(f" {t('adapter_badge_physical')} ")
            badge.setStyleSheet(
                "background:#003a1a; color:#00cc66; border:1px solid #00cc66;"
                "border-radius:3px; font-size:10px; padding:1px 4px;"
            )
        header.addWidget(badge)

        is_up = a["status"] == "Up"
        self.status_lbl = QLabel(f"  ● {t('adapter_status_up') if is_up else t('adapter_status_down')}")
        self.status_lbl.setStyleSheet(f"color:{'#4CAF50' if is_up else '#F44336'}; font-size:12px;")
        header.addWidget(self.status_lbl)
        layout.addLayout(header)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color:#444;")
        layout.addWidget(line)

        self._data_labels = {}
        for key, value in [
            ("adapter_desc",    a["description"]),
            ("adapter_mac",     a["mac"]),
            ("adapter_ip",      a["ip"]),
            ("adapter_subnet",  a["subnet"]),
            ("adapter_gateway", a["gateway"]),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(f"{t(key)}:")
            lbl.setFixedWidth(58)
            lbl.setStyleSheet("color:#888; font-size:11px;")
            val = QLabel(value if value else t("adapter_no_ip"))
            val.setStyleSheet("font-size:11px;")
            val.setWordWrap(True)
            row.addWidget(lbl)
            row.addWidget(val, stretch=1)
            layout.addLayout(row)
            self._data_labels[key] = val

        if a["type"] == "WiFi":
            row = QHBoxLayout()
            lbl = QLabel(f"{t('adapter_ssid')}:")
            lbl.setFixedWidth(58)
            lbl.setStyleSheet("color:#888; font-size:11px;")
            self.ssid_val = QLabel(a["ssid"] if a["ssid"] else t("adapter_no_ssid"))
            self.ssid_val.setStyleSheet("font-size:11px;")
            row.addWidget(lbl)
            row.addWidget(self.ssid_val, stretch=1)
            layout.addLayout(row)

    def update_status(self, status, ip):
        """Csak a státuszt és IP-t frissíti, nem építi újra a kártyát."""
        is_up = status == "Up"
        self.adapter_data["status"] = status
        self.adapter_data["ip"]     = ip if ip else "N/A"
        self.status_lbl.setText(f"  ● {t('adapter_status_up') if is_up else t('adapter_status_down')}")
        self.status_lbl.setStyleSheet(f"color:{'#4CAF50' if is_up else '#F44336'}; font-size:12px;")
        if "adapter_ip" in self._data_labels:
            self._data_labels["adapter_ip"].setText(ip if ip else t("adapter_no_ip"))

    def _apply_style(self, selected):
        a = self.adapter_data
        if a["virtual"]:
            self.setStyleSheet(
                "AdapterCard { background-color:#2a1f00; border:2px solid #ffaa00;"
                "border-radius:10px; } QLabel { color:#ffffff; }"
                if selected else
                "AdapterCard { background-color:#1a1a2e; border:1px solid #4a3800;"
                "border-radius:10px; } QLabel { color:#aaaaaa; }"
            )
        else:
            self.setStyleSheet(
                "AdapterCard { background-color:#1e3a5f; border:2px solid #4a9eff;"
                "border-radius:10px; } QLabel { color:#ffffff; }"
                if selected else
                "AdapterCard { background-color:#1a1a2e; border:1px solid #333;"
                "border-radius:10px; } QLabel { color:#aaaaaa; }"
            )

    def set_selected(self, selected):
        self.selected = selected
        self._apply_style(selected)

    def mousePressEvent(self, event):
        widget = self
        while widget is not None:
            if isinstance(widget, MainWindow):
                widget.on_adapter_selected(self)
                return
            widget = widget.parent()


# ---------------------------------------------------------------------------
# Adapter panel
# ---------------------------------------------------------------------------

class AdapterPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(240)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Felső sor: checkbox + frissítés gomb
        top_row = QHBoxLayout()
        top_row.setContentsMargins(10, 6, 10, 4)

        self.cb_virtual = QCheckBox(t("show_virtual"))
        self.cb_virtual.setChecked(False)
        self.cb_virtual.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cb_virtual.setStyleSheet("""
            QCheckBox { color:#888; font-size:11px; }
            QCheckBox::indicator {
                width:15px; height:15px;
                border:1px solid #444; border-radius:3px; background:#1a1a2e;
            }
            QCheckBox::indicator:checked { background:#1e3a5f; border:1px solid #4a9eff; }
            QCheckBox::indicator:hover   { border-color:#4a9eff; }
        """)
        self.cb_virtual.stateChanged.connect(self._on_virtual_toggled)
        top_row.addWidget(self.cb_virtual)
        top_row.addStretch()

        self.btn_refresh = QPushButton(t("btn_refresh"))
        self.btn_refresh.setFixedHeight(22)
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color:#1a1a2e; color:#4a9eff;
                border:1px solid #4a9eff; border-radius:4px;
                font-size:11px; padding:0px 10px;
            }
            QPushButton:hover { background-color:#1e3a5f; }
        """)
        self.btn_refresh.clicked.connect(self._on_refresh_clicked)
        top_row.addWidget(self.btn_refresh)
        outer.addLayout(top_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#222;")
        outer.addWidget(sep)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")

        self.container   = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(8, 4, 8, 8)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()
        self.scroll.setWidget(self.container)
        outer.addWidget(self.scroll, stretch=1)

        self.cards         = []
        self.selected_card = None

    def _on_virtual_toggled(self, state):
        global SHOW_VIRTUAL
        SHOW_VIRTUAL = state == Qt.CheckState.Checked.value
        widget = self
        while widget is not None:
            if isinstance(widget, MainWindow):
                widget.apply_filter()
                return
            widget = widget.parent()

    def _on_refresh_clicked(self):
        widget = self
        while widget is not None:
            if isinstance(widget, MainWindow):
                widget.full_refresh()
                return
            widget = widget.parent()

    def update_texts(self):
        self.cb_virtual.setText(t("show_virtual"))
        self.btn_refresh.setText(t("btn_refresh"))

    def refresh(self, adapters):
        previously_selected = None
        if self.selected_card:
            previously_selected = self.selected_card.adapter_data["name"]

        for card in self.cards:
            self.list_layout.removeWidget(card)
            card.deleteLater()
        self.cards.clear()
        self.selected_card = None

        for adapter in adapters:
            card = AdapterCard(adapter, self.container)
            self.list_layout.insertWidget(self.list_layout.count() - 1, card)
            self.cards.append(card)

        restored = False
        if previously_selected:
            for card in self.cards:
                if card.adapter_data["name"] == previously_selected:
                    card.set_selected(True)
                    self.selected_card = card
                    restored = True
                    break

        if not restored and self.cards:
            self.cards[0].set_selected(True)
            self.selected_card = self.cards[0]

    def update_status_only(self, status_map):
        """Csak a státuszt frissíti a kártyákon – nem építi újra a listát."""
        for card in self.cards:
            name = card.adapter_data["name"]
            if name in status_map:
                s = status_map[name]
                card.update_status(s["status"], s["ip"])

    def select_card(self, card):
        if self.selected_card:
            self.selected_card.set_selected(False)
        card.set_selected(True)
        self.selected_card = card

    def get_selected_adapter(self):
        return self.selected_card.adapter_data if self.selected_card else None


# ---------------------------------------------------------------------------
# Fő ablak
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(t("window_title"))
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)
        self._full_thread   = None
        self._status_thread = None
        self._cached_adapters = []
        self._build_menu()
        self._build_ui()
        self._apply_global_style()
        icon_path = asset("MicroIPTool.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Első betöltés – teljes lekérés
        self.full_refresh()

        # Gyors állapot frissítés 5 másodpercenként – nem érinti a beviteli mezőket
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._status_refresh)
        self.status_timer.start(5000)

    # --- Teljes frissítés (induláskor + frissítés gomb) ---

    def full_refresh(self):
        if self._full_thread and self._full_thread.isRunning():
            return
        self._full_thread = FullRefreshThread()
        self._full_thread.finished.connect(self._on_full_done)
        self._full_thread.start()

    def _on_full_done(self, all_adapters, warning, pc_name, domain):
        self._cached_adapters = all_adapters
        filtered = filter_adapters(all_adapters)
        warning  = check_ip_overlap(filtered)
        self.adapter_panel.refresh(filtered)
        self.warning_bar.setText(warning)
        self.warning_bar.setVisible(bool(warning))
        self.status_bar_label.setText(
            f"  {t('status_pc')}: {pc_name}    |    {t('status_domain')}: {domain}"
        )
        selected = self.adapter_panel.get_selected_adapter()
        if selected:
            self.ip_tab.load_adapter(selected)
            self.ping_tab.load_adapter(selected)
            self.scan_tab.load_adapter(selected)

    # --- Gyors állapot frissítés (5 sec timer) ---

    def _status_refresh(self):
        if self._status_thread and self._status_thread.isRunning():
            return
        self._status_thread = StatusRefreshThread()
        self._status_thread.finished.connect(self._on_status_done)
        self._status_thread.start()

    def _on_status_done(self, status_map):
        """Frissíti a kártyák státuszát és az IP fül infó panelét – beviteli mezőket nem érinti."""
        self.adapter_panel.update_status_only(status_map)
        # Ha van kiválasztott adapter, az infó panelt is frissítjük – de csak az infót
        selected = self.adapter_panel.get_selected_adapter()
        if selected and selected["name"] in status_map:
            s = status_map[selected["name"]]
            selected["status"] = s["status"]
            selected["ip"]     = s["ip"]
            self.ip_tab.update_info_only(selected)

    # --- Szűrés ---

    def apply_filter(self):
        if not self._cached_adapters:
            return
        filtered = filter_adapters(self._cached_adapters)
        warning  = check_ip_overlap(filtered)
        self.adapter_panel.refresh(filtered)
        self.warning_bar.setText(warning)
        self.warning_bar.setVisible(bool(warning))

    # --- Adapter kiválasztás ---

    def on_adapter_selected(self, card):
        self.adapter_panel.select_card(card)
        self.ip_tab.load_adapter(card.adapter_data)
        self.ping_tab.load_adapter(card.adapter_data)
        self.scan_tab.load_adapter(card.adapter_data)

    # --- Nyelv ---

    def set_language(self, lang_code):
        global LANG
        LANG = lang_code
        self.setWindowTitle(t("window_title"))
        self.tabs.setTabText(0, t("tab_ip"))
        self.tabs.setTabText(1, t("tab_ping"))
        self.tabs.setTabText(2, t("tab_scan"))
        self.ping_tab.update_texts()
        self.scan_tab.update_texts()
        self.adapter_panel.update_texts()
        self.ip_tab.update_texts()
        if self._cached_adapters:
            filtered = filter_adapters(self._cached_adapters)
            self.adapter_panel.refresh(filtered)
        self.menuBar().clear()
        self._build_menu()

    # --- Menüsor ---

    def _build_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color:#0d0d1a; color:#aaaaaa;
                font-family:'Segoe UI'; font-size:12px;
                border-bottom:1px solid #222; padding:2px;
            }
            QMenuBar::item:selected { background-color:#1e3a5f; color:#ffffff; }
            QMenu {
                background-color:#1a1a2e; color:#cccccc;
                border:1px solid #333; font-size:12px;
            }
            QMenu::item:selected { background-color:#1e3a5f; color:#ffffff; }
            QMenu::separator { height:1px; background:#333; margin:4px 10px; }
        """)
        file_menu = menubar.addMenu(t("menu_file"))
        exit_act  = QAction(t("menu_file_exit"), self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        settings_menu = menubar.addMenu(t("menu_settings"))
        lang_menu     = settings_menu.addMenu(t("menu_settings_lang"))
        act_hu = QAction("🇭🇺  Magyar", self)
        act_hu.triggered.connect(lambda: self.set_language("hu"))
        lang_menu.addAction(act_hu)
        act_en = QAction("🇬🇧  English", self)
        act_en.triggered.connect(lambda: self.set_language("en"))
        lang_menu.addAction(act_en)

        help_menu = menubar.addMenu(t("menu_help"))
        about_act = QAction(t("menu_help_about"), self)
        about_act.triggered.connect(lambda: AboutDialog(self).exec())
        help_menu.addAction(about_act)

    # --- UI ---

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.warning_bar = QLabel("")
        self.warning_bar.setStyleSheet(
            "background-color:#7a4a00; color:#ffcc00; padding:6px 14px; font-size:12px;"
        )
        self.warning_bar.setVisible(False)
        main_layout.addWidget(self.warning_bar)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet("""
            QSplitter::handle { background-color:#333; width:2px; }
            QSplitter::handle:hover { background-color:#4a9eff; }
        """)
        self.splitter.setChildrenCollapsible(False)

        self.adapter_panel = AdapterPanel()
        self.splitter.addWidget(self.adapter_panel)

        right_panel  = QWidget()
        right_panel.setMinimumWidth(400)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border:none; background:#0f0f1a; }
            QTabBar::tab {
                background:#1a1a2e; color:#888;
                padding:12px 24px; border:none;
                font-size:12px; font-family:'Segoe UI';
            }
            QTabBar::tab:selected {
                background:#0f0f1a; color:#4a9eff; border-bottom:2px solid #4a9eff;
            }
            QTabBar::tab:hover { background:#16213e; color:#ccc; }
        """)

        self.ip_tab = IPSettingsTab()
        self.tabs.addTab(self.ip_tab, t("tab_ip"))

        self.ping_tab = PingTab()
        self.tabs.addTab(self.ping_tab, t("tab_ping"))

        self.scan_tab = ScanTab()
        self.tabs.addTab(self.scan_tab, t("tab_scan"))

        right_layout.addWidget(self.tabs)
        self.splitter.addWidget(right_panel)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([280, 820])
        main_layout.addWidget(self.splitter, stretch=1)

        self.status_bar_label = QLabel()
        self.status_bar_label.setFixedHeight(28)
        self.status_bar_label.setStyleSheet(
            "background-color:#0d0d1a; color:#555; padding:0px 14px;"
            "font-size:11px; border-top:1px solid #222;"
        )
        main_layout.addWidget(self.status_bar_label)

    def _apply_global_style(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color:#0f0f1a; color:#cccccc;
                font-family:'Segoe UI'; font-size:12px;
            }
            QScrollBar:vertical { background:#1a1a2e; width:6px; border-radius:3px; }
            QScrollBar::handle:vertical { background:#333; border-radius:3px; }
        """)


# ---------------------------------------------------------------------------
# Belépési pont
# ---------------------------------------------------------------------------

# MAC adatbázis betöltése induláskor
load_mac_db()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())