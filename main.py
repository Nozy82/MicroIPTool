import sys
import os
import re
import socket
import subprocess
import time
import csv
import tempfile
import concurrent.futures
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QTabWidget, QScrollArea, QDialog, QPushButton,
    QCheckBox, QSizePolicy, QSplitter, QLineEdit, QGridLayout,
    QFileDialog, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QAction, QPixmap, QIcon, QIntValidator

# Admin jog ellenőrzése
import ctypes
if not ctypes.windll.shell32.IsUserAnAdmin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit()


# ---------------------------------------------------------------------------
# Verzió
# ---------------------------------------------------------------------------

APP_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Betűméret skála – 0.8 (kis) és 1.4 (nagy) között
# ---------------------------------------------------------------------------

FONT_SCALE     = 1.0
FONT_SCALE_MIN = 0.8
FONT_SCALE_MAX = 1.4
FONT_SCALE_STEP = 0.1

# ---------------------------------------------------------------------------
# Alap betűméretek – ezekből számol a skála
# ---------------------------------------------------------------------------

_BASE_FONTS = {
    "font_tiny":   9,
    "font_small":  11,
    "font_normal": 12,
    "font_large":  13,
    "font_title":  15,
}


# ---------------------------------------------------------------------------
# Téma és méret beállítások
# ---------------------------------------------------------------------------

THEME = {
    "font_tiny":         9,
    "font_small":        11,
    "font_normal":       12,
    "font_large":        13,
    "font_title":        15,
    "color_bg":          "#0f0f1a",
    "color_bg_card":     "#1a1a2e",
    "color_bg_input":    "#16213e",
    "color_bg_dark":     "#0d0d1a",
    "color_bg_header":   "#1a1a2e",
    "color_accent":      "#4a9eff",
    "color_accent_dark": "#1e3a5f",
    "color_text":        "#cccccc",
    "color_text_muted":  "#888888",
    "color_text_dim":    "#555555",
    "color_ok":          "#4CAF50",
    "color_error":       "#F44336",
    "color_warning_bg":  "#7a4a00",
    "color_warning_fg":  "#ffcc00",
    "color_virtual_bg":  "#3a2a00",
    "color_virtual_fg":  "#ffaa00",
    "color_physical_bg": "#003a1a",
    "color_physical_fg": "#00cc66",
    "card_min_height":   210,
    "octet_width":       48,
    "octet_height":      30,
    "btn_height_small":  26,
    "btn_height_normal": 32,
    "btn_height_large":  36,
}


def th(key):
    return THEME.get(key, "")


def fs(key):
    """Betűméret lekérése skálázva."""
    base = _BASE_FONTS.get(key, THEME.get(key, 10))
    scaled = max(7, round(base * FONT_SCALE))
    return f"{scaled}px"


def fv(key):
    """Betűméret lekérése int értékként (pl. QFont-hoz)."""
    base = _BASE_FONTS.get(key, THEME.get(key, 10))
    return max(7, round(base * FONT_SCALE))


# ---------------------------------------------------------------------------
# Log rendszer
# ---------------------------------------------------------------------------

LOG_ENABLED = True
LOG_PATH    = os.path.join(os.path.expanduser("~"), "Documents", "MicroIPTool.log")


def _log(msg):
    if not LOG_ENABLED:
        return
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


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
        "about_version":          f"Verzió: {APP_VERSION}",
        "about_author":           "Készítette: Mózes Balázs (Nozy82)",
        "about_desc":             "Hálózati eszköz IP beállításhoz, pingeléshez és szkenneléshez.",
        "about_github":           "Forráskód és letöltés:",
        "about_close":            "Bezárás",
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
        "scan_running":           "Szkennelés... {0}/{1}",
        "scan_done":              "Kész – {0} eszköz találva",
        "scan_stopped":           "Leállítva – {0} eszköz találva",
        "scan_export_ok":         "✔  Exportálva: {0}",
        "scan_export_err":        "✖  Export hiba: {0}",
        "scan_no_results":        "Nincs exportálható eredmény",
        "scan_range_mismatch":    "A tartomány első 3 oktetje nem egyezik",
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
        "about_version":          f"Version: {APP_VERSION}",
        "about_author":           "Created by: Mózes Balázs (Nozy82)",
        "about_desc":             "Network tool for IP configuration, ping and scanning.",
        "about_github":           "Source code and download:",
        "about_close":            "Close",
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
        "ping_invalid_ip":        "Invalid IP – only values 0-255 are allowed",
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
        "scan_done":              "Done – {0} devices found",
        "scan_stopped":           "Stopped – {0} devices found",
        "scan_export_ok":         "✔  Exported: {0}",
        "scan_export_err":        "✖  Export error: {0}",
        "scan_no_results":        "No results to export",
        "scan_range_mismatch":    "First 3 octets of range must match",
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
# Hálózati adatok lekérése
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

_PS_GET_STATUS = (
    "Get-NetAdapter | ForEach-Object {"
    "$i=$_.ifIndex;"
    "$ip=Get-NetIPAddress -InterfaceIndex $i -AddressFamily IPv4 -ErrorAction SilentlyContinue;"
    "Write-Output ($_.Name+'|'+$_.Status+'|'+($ip.IPAddress -join ','))"
    "}"
)


def _run_ps(cmd):
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
# MAC gyártó adatbázis
# ---------------------------------------------------------------------------

_MAC_DB = {}


def load_mac_db():
    global _MAC_DB
    db_path = asset("mac_vendors.csv")
    if not os.path.exists(db_path):
        return
    try:
        with open(db_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                prefix = row.get("Mac Prefix", "").strip().upper()
                vendor = row.get("Vendor Name", "").strip()
                if prefix and vendor:
                    _MAC_DB[prefix] = vendor
    except Exception as e:
        print(f"MAC adatbázis hiba: {e}")


def get_vendor(mac):
    if not mac or mac in ("N/A", "–"):
        return "–"
    clean = re.sub(r'[:\-\.]', '', mac.strip().upper())
    if len(clean) >= 6:
        prefix = f"{clean[0:2]}:{clean[2:4]}:{clean[4:6]}"
        return _MAC_DB.get(prefix, "–")
    return "–"


# ---------------------------------------------------------------------------
# Háttérszálak
# ---------------------------------------------------------------------------

class FullRefreshThread(QThread):
    finished = pyqtSignal(list, str, str, str)

    def run(self):
        all_adapters    = get_network_adapters()
        filtered        = filter_adapters(all_adapters)
        warning         = check_ip_overlap(filtered)
        pc_name, domain = get_pc_info()
        self.finished.emit(all_adapters, warning, pc_name, domain)


class StatusRefreshThread(QThread):
    finished = pyqtSignal(dict)

    def run(self):
        self.finished.emit(get_adapter_status())


# ---------------------------------------------------------------------------
# IP oktet beviteli mező
# ---------------------------------------------------------------------------

class OctetField(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.next_field    = None
        self.prev_field    = None
        self.external_next = None
        self._error        = False
        self.setMaxLength(3)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedWidth(th("octet_width"))
        self.setFixedHeight(th("octet_height"))
        self.setValidator(QIntValidator(0, 255, self))
        self.textChanged.connect(self._validate)
        self._apply_normal_style()

    def _apply_normal_style(self):
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {th('color_bg_input')};
                color: {th('color_text')};
                border: 1px solid #333;
                border-radius: 4px;
                font-size: {fs('font_normal')};
                padding: 2px;
            }}
            QLineEdit:focus {{ border: 1px solid {th('color_accent')}; }}
            QLineEdit:disabled {{
                background-color: {th('color_bg')};
                color: {th('color_text_dim')};
                border: 1px solid #222;
            }}
        """)

    def _apply_error_style(self):
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: #3a0000;
                color: #ff6666;
                border: 1px solid {th('color_error')};
                border-radius: 4px;
                font-size: {fs('font_normal')};
                padding: 2px;
            }}
            QLineEdit:focus {{ border: 1px solid {th('color_error')}; }}
        """)

    def _validate(self, text):
        if text == "":
            self._error = False
            self._apply_normal_style()
            return
        try:
            val = int(text)
            if 0 <= val <= 255:
                self._error = False
                self._apply_normal_style()
            else:
                self._error = True
                self._apply_error_style()
        except ValueError:
            self._error = True
            self._apply_error_style()

    def is_valid(self):
        if self.text() == "":
            return False
        try:
            return 0 <= int(self.text()) <= 255
        except ValueError:
            return False

    def keyPressEvent(self, event):
        key       = event.key()
        modifiers = event.modifiers()
        has_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

        # Shift+Tab – visszafele ugrás
        if key == Qt.Key.Key_Backtab:
            if self.prev_field:
                self.prev_field.setFocus()
                self.prev_field.selectAll()
            return

        # Shift lenyomva – semmilyen ugrás nem történik, normál szövegkezelés
        if has_shift:
            super().keyPressEvent(event)
            return

        # Enter, pont – következő mező
        if key in (Qt.Key.Key_Period, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            target = self.next_field or self.external_next
            if target:
                target.setFocus()
                target.selectAll()
            return

        # Tab – következő mező
        if key == Qt.Key.Key_Tab:
            target = self.next_field or self.external_next
            if target:
                target.setFocus()
                target.selectAll()
                return

        # Backspace üres mezőn – előző mező
        if key == Qt.Key.Key_Backspace and self.text() == "" and self.prev_field:
            self.prev_field.setFocus()
            self.prev_field.selectAll()
            return

        super().keyPressEvent(event)

        # 3 számjegy után automatikus ugrás
        if len(self.text()) == 3 and key not in (
            Qt.Key.Key_Backspace, Qt.Key.Key_Delete,
            Qt.Key.Key_Left, Qt.Key.Key_Right,
            Qt.Key.Key_Tab
        ):
            target = self.next_field or self.external_next
            if target:
                target.setFocus()
                target.selectAll()

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
            dot.setStyleSheet(
                f"color:{th('color_text_dim')}; font-size:{fs('font_large')};"
            )
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

    def _section_label(self, key):
        lbl = QLabel(t(key))
        lbl.setFont(QFont("Segoe UI", fv("font_large"), QFont.Weight.Bold))
        lbl.setStyleSheet(f"color:{th('color_accent')}; font-size:{fs('font_large')};")
        return lbl

    def _key_label(self, key):
        lbl = QLabel(f"{t(key)}:")
        lbl.setStyleSheet(
            f"color:{th('color_text_muted')}; font-size:{fs('font_small')};"
        )
        lbl.setFixedWidth(140)
        return lbl

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
        info_frame.setStyleSheet(f"""
            QFrame {{
                background:{th('color_bg_card')};
                border:1px solid #2a2a4a;
                border-radius:8px;
            }}
        """)
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
            lbl = self._key_label(key)
            val = QLabel("–")
            val.setStyleSheet(
                f"color:{th('color_text')}; font-size:{fs('font_small')};"
            )
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
            btn.setFixedHeight(th("btn_height_normal"))
            btn.setFixedWidth(110)
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
            lbl = self._key_label(key)
            w, fields = make_octet_row()
            setattr(self, attr, fields)
            row.addWidget(lbl)
            row.addWidget(w)
            sl.addLayout(row)

        self.ip_fields[0].textChanged.connect(self._auto_subnet)
        self.ip_fields[3].external_next = self.sn_fields[0]
        self.sn_fields[3].external_next = self.gw_fields[0]

        main.addWidget(self.static_widget)
        self.static_widget.setVisible(False)

        apply_row = QHBoxLayout()
        self.btn_apply = QPushButton(t("ip_apply"))
        self.btn_apply.setFixedHeight(th("btn_height_large"))
        self.btn_apply.setFixedWidth(150)
        self.btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_apply.clicked.connect(self._apply)
        apply_row.addStretch()
        apply_row.addWidget(self.btn_apply)
        apply_row.addStretch()
        main.addLayout(apply_row)

        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setVisible(False)
        main.addWidget(self.lbl_status)

        main.addStretch()
        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self._update_mode_buttons()

    def _set_mode(self, static):
        self._static_mode = static
        self.static_widget.setVisible(static)
        self._update_mode_buttons()
        if static:
            QTimer.singleShot(50, lambda: (
                self.ip_fields[0].setFocus(),
                self.ip_fields[0].selectAll()
            ))

    def _update_mode_buttons(self):
        active = f"""
            QPushButton {{
                background-color:{th('color_accent_dark')};
                color:{th('color_accent')};
                border:1px solid {th('color_accent')};
                border-radius:4px;
                font-size:{fs('font_small')};
            }}
        """
        inactive = f"""
            QPushButton {{
                background-color:{th('color_bg_card')};
                color:{th('color_text_dim')};
                border:1px solid #333;
                border-radius:4px;
                font-size:{fs('font_small')};
            }}
            QPushButton:hover {{ color:{th('color_text_muted')}; border-color:#555; }}
        """
        self.btn_dhcp.setStyleSheet(active if not self._static_mode else inactive)
        self.btn_static.setStyleSheet(active if self._static_mode else inactive)
        self.btn_apply.setStyleSheet(f"""
            QPushButton {{
                background-color:{th('color_accent_dark')};
                color:{th('color_accent')};
                border:1px solid {th('color_accent')};
                border-radius:4px;
                font-size:{fs('font_small')};
            }}
            QPushButton:hover {{
                background-color:{th('color_accent')};
                color:#ffffff;
            }}
        """)

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

                invalid = [f for f in self.ip_fields + self.sn_fields if not f.is_valid()]
                if invalid:
                    invalid[0].setFocus()
                    invalid[0].selectAll()
                    self._show_status(
                        t("ip_apply_err",
                          "Érvénytelen érték – csak 0-255 közötti számok megengedettek"),
                        error=True
                    )
                    return

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
            script_path = os.path.join(tempfile.gettempdir(), "mipt_apply.ps1")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(ps)

            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive",
                 "-ExecutionPolicy", "Bypass", "-File", script_path],
                creationflags=subprocess.CREATE_NO_WINDOW,
                capture_output=True, text=True
            )

            _log(f"Visszatérési kód: {result.returncode}")
            if result.stderr: _log(f"Hiba: {result.stderr.strip()}")

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
        color = th("color_error") if error else th("color_ok")
        self.lbl_status.setStyleSheet(
            f"font-size:{fs('font_small')}; color:{color}; padding:4px;"
        )
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

    def refresh_styles(self):
        self._update_mode_buttons()
        for key, (lbl, val) in self._info_labels.items():
            lbl.setStyleSheet(
                f"color:{th('color_text_muted')}; font-size:{fs('font_small')};"
            )
            val.setStyleSheet(
                f"color:{th('color_text')}; font-size:{fs('font_small')};"
            )
        self.lbl_status.setStyleSheet(
            f"font-size:{fs('font_small')}; padding:4px;"
        )


# ---------------------------------------------------------------------------
# Ping fül
# ---------------------------------------------------------------------------

class PingThread(QThread):
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
                text=True, encoding="cp1250", errors="replace"
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

        self.lbl_title = QLabel(t("ping_title"))
        self.lbl_title.setFont(QFont("Segoe UI", fv("font_large"), QFont.Weight.Bold))
        self.lbl_title.setStyleSheet(
            f"color:{th('color_accent')}; font-size:{fs('font_large')};"
        )
        main.addWidget(self.lbl_title)

        ip_row = QHBoxLayout()
        self.lbl_target = QLabel(f"{t('ping_target')}:")
        self.lbl_target.setFixedWidth(140)
        self.lbl_target.setStyleSheet(
            f"color:{th('color_text_muted')}; font-size:{fs('font_small')};"
        )
        ip_row.addWidget(self.lbl_target)
        self.ip_widget, self.ip_fields = make_octet_row()
        ip_row.addWidget(self.ip_widget)
        ip_row.addStretch()
        main.addLayout(ip_row)

        btn_row = QHBoxLayout()
        self.btn_ping = QPushButton(t("ping_btn_start"))
        self.btn_ping.setFixedHeight(th("btn_height_large"))
        self.btn_ping.setFixedWidth(150)
        self.btn_ping.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ping.setStyleSheet(f"""
            QPushButton {{
                background-color:{th('color_accent_dark')};
                color:{th('color_accent')};
                border:1px solid {th('color_accent')};
                border-radius:4px;
                font-size:{fs('font_small')};
            }}
            QPushButton:hover {{
                background-color:{th('color_accent')};
                color:#ffffff;
            }}
            QPushButton:disabled {{
                background-color:{th('color_bg_card')};
                color:{th('color_text_dim')};
                border-color:#333;
            }}
        """)
        self.btn_ping.clicked.connect(self._start_ping)
        btn_row.addWidget(self.btn_ping)
        btn_row.addStretch()
        main.addLayout(btn_row)

        self.result_box = QLabel("")
        self.result_box.setStyleSheet(f"""
            QLabel {{
                background-color: {th('color_bg_dark')};
                color: {th('color_text')};
                border: 1px solid #2a2a4a;
                border-radius: 6px;
                font-family: 'Consolas', monospace;
                font-size: {fs('font_small')};
                padding: 10px;
            }}
        """)
        self.result_box.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.result_box.setWordWrap(True)
        self.result_box.setFixedHeight(170)
        main.addWidget(self.result_box)

        clear_row = QHBoxLayout()
        self.btn_clear = QPushButton(t("ping_btn_clear"))
        self.btn_clear.setFixedHeight(th("btn_height_small"))
        self.btn_clear.setFixedWidth(90)
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setStyleSheet(f"""
            QPushButton {{
                background-color:{th('color_bg_card')};
                color:{th('color_text_dim')};
                border:1px solid #333;
                border-radius:4px;
                font-size:{fs('font_tiny')};
            }}
            QPushButton:hover {{ color:{th('color_text_muted')}; border-color:#555; }}
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
        self._current_adapter = adapter
        ip = adapter.get("ip", "")
        if ip and ip != "N/A":
            parts = ip.split(".")
            if len(parts) == 4:
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
        invalid = [f for f in self.ip_fields if not f.is_valid()]
        if invalid:
            invalid[0].setFocus()
            invalid[0].selectAll()
            self.result_box.setText(t("ping_invalid_ip"))
            return
        ip = ".".join(f.text() for f in self.ip_fields)
        self.result_box.setText(t("ping_running"))
        self.btn_ping.setEnabled(False)
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

    def refresh_styles(self):
        self.lbl_title.setFont(QFont("Segoe UI", fv("font_large"), QFont.Weight.Bold))
        self.lbl_title.setStyleSheet(
            f"color:{th('color_accent')}; font-size:{fs('font_large')};"
        )
        self.lbl_target.setStyleSheet(
            f"color:{th('color_text_muted')}; font-size:{fs('font_small')};"
        )
        self.btn_ping.setStyleSheet(f"""
            QPushButton {{
                background-color:{th('color_accent_dark')};
                color:{th('color_accent')};
                border:1px solid {th('color_accent')};
                border-radius:4px;
                font-size:{fs('font_small')};
            }}
            QPushButton:hover {{ background-color:{th('color_accent')}; color:#ffffff; }}
            QPushButton:disabled {{
                background-color:{th('color_bg_card')};
                color:{th('color_text_dim')};
                border-color:#333;
            }}
        """)
        self.result_box.setStyleSheet(f"""
            QLabel {{
                background-color: {th('color_bg_dark')};
                color: {th('color_text')};
                border: 1px solid #2a2a4a;
                border-radius: 6px;
                font-family: 'Consolas', monospace;
                font-size: {fs('font_small')};
                padding: 10px;
            }}
        """)
        self.btn_clear.setStyleSheet(f"""
            QPushButton {{
                background-color:{th('color_bg_card')};
                color:{th('color_text_dim')};
                border:1px solid #333;
                border-radius:4px;
                font-size:{fs('font_tiny')};
            }}
            QPushButton:hover {{ color:{th('color_text_muted')}; border-color:#555; }}
        """)

# ---------------------------------------------------------------------------
# Scan háttérszál
# ---------------------------------------------------------------------------

class ScanThread(QThread):
    result_found = pyqtSignal(dict)
    progress     = pyqtSignal(int, int)
    finished     = pyqtSignal(int)

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
        total   = self.end_ip - self.start_ip + 1
        targets = [
            f"{self.base_ip}.{i}"
            for i in range(self.start_ip, self.end_ip + 1)
        ]
        done  = 0
        found = 0

        own_mac_map = {}
        try:
            ps_out = subprocess.check_output(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                 "Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | "
                 "ForEach-Object { $idx=$_.InterfaceIndex; $ip=$_.IPAddress; "
                 "$mac=(Get-NetAdapter | Where-Object {$_.ifIndex -eq $idx}).MacAddress; "
                 "Write-Output ($ip+'|'+$mac) }"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stderr=subprocess.DEVNULL, timeout=5
            ).decode("cp1250", errors="replace")
            for line in ps_out.splitlines():
                parts = line.strip().split("|")
                if len(parts) == 2 and parts[1].strip():
                    own_mac_map[parts[0].strip()] = (
                        parts[1].strip().upper().replace("-", ":")
                    )
        except Exception:
            pass

        def check_host(ip):
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

            time.sleep(0.2)

            mac    = "–"
            vendor = "–"

            if ip in own_mac_map:
                mac    = own_mac_map[ip]
                vendor = get_vendor(mac)
            else:
                for _ in range(3):
                    try:
                        arp_out = subprocess.check_output(
                            ["arp", "-a"],
                            creationflags=subprocess.CREATE_NO_WINDOW,
                            stderr=subprocess.DEVNULL, timeout=2
                        ).decode("cp1250", errors="replace")

                        for line in arp_out.splitlines():
                            if ip in line:
                                match = re.search(
                                    r'([0-9a-fA-F]{2}[:\-]){5}[0-9a-fA-F]{2}',
                                    line
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

            hostname = ip
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except Exception:
                pass

            return {"ip": ip, "mac": mac, "hostname": hostname, "vendor": vendor}

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
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
# Scan eredmény táblázat
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

        self._header_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._header_splitter.setFixedHeight(30)
        self._header_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: #2a2a4a;
                width: 3px;
            }}
            QSplitter::handle:hover {{
                background-color: {th('color_accent')};
            }}
        """)
        self._header_splitter.setChildrenCollapsible(False)
        self._header_splitter.splitterMoved.connect(self._redraw)

        self._header_btns = []
        for i, key in enumerate(self.COLS):
            btn = QPushButton(t(key))
            btn.setFlat(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumWidth(60)
            btn.clicked.connect(lambda _, col=i: self._sort_by(col))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {th('color_bg_header')};
                    color: {th('color_accent')};
                    border: none;
                    border-bottom: 1px solid #2a2a4a;
                    font-size: {fs('font_small')};
                    font-weight: bold;
                    padding: 0 8px;
                    text-align: left;
                }}
                QPushButton:hover {{ background-color: #16213e; }}
            """)
            self._header_splitter.addWidget(btn)
            self._header_btns.append(btn)

        self._header_splitter.setSizes(self.WIDTHS)
        layout.addWidget(self._header_splitter)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")

        self.rows_widget = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_widget)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(0)
        self.rows_layout.addStretch()
        self.scroll.setWidget(self.rows_widget)
        layout.addWidget(self.scroll, stretch=1)

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

    def _redraw(self, *args):
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

        rows       = sorted(self._rows, key=sort_key, reverse=not self._sort_asc)
        col_widths = self._header_splitter.sizes()

        for i, row in enumerate(rows):
            bg         = th("color_bg") if i % 2 == 0 else "#13131f"
            row_widget = QWidget()
            row_widget.setStyleSheet(f"background:{bg};")
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(0)

            for j, field in enumerate(self.FIELDS):
                lbl = QLabel(row.get(field, "–"))
                lbl.setFixedWidth(col_widths[j] if j < len(col_widths) else 120)
                lbl.setStyleSheet(
                    f"color:{th('color_text')}; font-size:{fs('font_small')};"
                    f"padding:2px 8px; border-right:1px solid #1a1a2e;"
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
        self._total           = 0
        self._build_ui()

    def _btn_style(self, color):
        return f"""
            QPushButton {{
                background-color:{th('color_bg_card')};
                color:{color};
                border:1px solid {color};
                border-radius:4px;
                font-size:{fs('font_small')};
                padding: 0 12px;
            }}
            QPushButton:hover {{ background-color:#16213e; }}
            QPushButton:disabled {{ color:#333; border-color:#333; }}
        """

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(24, 20, 24, 20)
        main.setSpacing(12)

        # Cím
        self.lbl_title = QLabel(t("scan_title"))
        self.lbl_title.setFont(QFont("Segoe UI", fv("font_large"), QFont.Weight.Bold))
        self.lbl_title.setStyleSheet(
            f"color:{th('color_accent')}; font-size:{fs('font_large')};"
        )
        main.addWidget(self.lbl_title)

        # Tartomány sor
        range_row = QHBoxLayout()
        self.lbl_from = QLabel(f"{t('scan_range_from')}:")
        self.lbl_from.setStyleSheet(
            f"color:{th('color_text_muted')}; font-size:{fs('font_small')};"
        )
        self.lbl_from.setFixedWidth(130)
        range_row.addWidget(self.lbl_from)
        self.from_widget, self.from_fields = make_octet_row()
        range_row.addWidget(self.from_widget)
        range_row.addSpacing(16)
        self.lbl_to = QLabel(f"{t('scan_range_to')}:")
        self.lbl_to.setStyleSheet(
            f"color:{th('color_text_muted')}; font-size:{fs('font_small')};"
        )
        self.lbl_to.setFixedWidth(130)
        range_row.addWidget(self.lbl_to)
        self.to_widget, self.to_fields = make_octet_row()
        range_row.addWidget(self.to_widget)
        range_row.addStretch()
        main.addLayout(range_row)

        # Gomb sor
        btn_row = QHBoxLayout()
        self.btn_start  = QPushButton(t("scan_btn_start"))
        self.btn_stop   = QPushButton(t("scan_btn_stop"))
        self.btn_export = QPushButton(t("scan_btn_export"))
        self.btn_clear  = QPushButton(t("scan_btn_clear"))

        self.btn_start.setStyleSheet(self._btn_style(th("color_accent")))
        self.btn_stop.setStyleSheet(self._btn_style(th("color_error")))
        self.btn_export.setStyleSheet(self._btn_style(th("color_ok")))
        self.btn_clear.setStyleSheet(self._btn_style(th("color_text_muted")))

        for btn in [self.btn_start, self.btn_stop, self.btn_export, self.btn_clear]:
            btn.setFixedHeight(th("btn_height_normal"))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

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
        self.lbl_status.setStyleSheet(
            f"color:{th('color_text_muted')}; font-size:{fs('font_small')};"
        )
        main.addWidget(self.lbl_status)

        # Progress bar – szolíd, vékony, igazodik a táblázat szélességéhez
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {th('color_bg_card')};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {th('color_accent')};
                border-radius: 3px;
            }}
        """)
        main.addWidget(self.progress_bar)

        # Eredmény táblázat
        self.table = ScanResultTable()
        main.addWidget(self.table, stretch=1)

    def load_adapter(self, adapter):
        self._current_adapter = adapter
        ip = adapter.get("ip", "")
        if ip and ip != "N/A":
            parts = ip.split(".")
            if len(parts) == 4:
                for i in range(3):
                    self.from_fields[i].setText(parts[i])
                    self.to_fields[i].setText(parts[i])
                self.from_fields[3].setText("1")
                self.to_fields[3].setText("254")

    def _start_scan(self):
        if not self._current_adapter:
            self.lbl_status.setText(t("scan_no_adapter"))
            return

        for fields in [self.from_fields, self.to_fields]:
            invalid = [f for f in fields if not f.is_valid()]
            if invalid:
                invalid[0].setFocus()
                invalid[0].selectAll()
                return

        from_base = ".".join(f.text() for f in self.from_fields[:3])
        to_base   = ".".join(f.text() for f in self.to_fields[:3])

        if from_base != to_base:
            self.lbl_status.setText(t("scan_range_mismatch"))
            return

        base_ip = from_base
        start   = int(self.from_fields[3].text())
        end     = int(self.to_fields[3].text())

        if start > end:
            self.from_fields[3].setFocus()
            return

        self._total = end - start + 1
        self.table.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(self._total)
        self.lbl_status.setText(t("scan_running", 0, self._total))
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
        self.progress_bar.setValue(done)
        self.lbl_status.setText(t("scan_running", done, total))

    def _on_done(self, found):
        self.progress_bar.setValue(self._total)
        stopped = self._scan_thread and self._scan_thread._stop
        self.lbl_status.setText(
            t("scan_stopped", found) if stopped else t("scan_done", found)
        )
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        # Progress bar visszaállítása pár másodperc után
        QTimer.singleShot(3000, lambda: self.progress_bar.setValue(0))

    def _clear(self):
        self.table.clear()
        self.lbl_status.setText("")
        self.progress_bar.setValue(0)

    def _export(self):
        rows = self.table.get_rows()
        if not rows:
            self.lbl_status.setText(t("scan_no_results"))
            return

        date_str     = datetime.now().strftime("%Y-%m-%d_%H-%M")
        default_name = f"scan_{date_str}.csv"
        documents    = os.path.join(os.path.expanduser("~"), "Documents")
        default_path = os.path.join(documents, default_name)

        filepath, _ = QFileDialog.getSaveFileName(
            self, t("scan_btn_export"), default_path, "CSV fájl (*.csv)"
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["IP Address", "MAC Address", "Hostname", "Vendor"])
                for row in rows:
                    writer.writerow([
                        row.get("ip", ""), row.get("mac", ""),
                        row.get("hostname", ""), row.get("vendor", ""),
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

    def refresh_styles(self):
        self.lbl_title.setFont(QFont("Segoe UI", fv("font_large"), QFont.Weight.Bold))
        self.lbl_title.setStyleSheet(
            f"color:{th('color_accent')}; font-size:{fs('font_large')};"
        )
        self.lbl_from.setStyleSheet(
            f"color:{th('color_text_muted')}; font-size:{fs('font_small')};"
        )
        self.lbl_to.setStyleSheet(
            f"color:{th('color_text_muted')}; font-size:{fs('font_small')};"
        )
        self.lbl_status.setStyleSheet(
            f"color:{th('color_text_muted')}; font-size:{fs('font_small')};"
        )
        self.btn_start.setStyleSheet(self._btn_style(th("color_accent")))
        self.btn_stop.setStyleSheet(self._btn_style(th("color_error")))
        self.btn_export.setStyleSheet(self._btn_style(th("color_ok")))
        self.btn_clear.setStyleSheet(self._btn_style(th("color_text_muted")))
        # Táblázat fejléc és sorok újrarajzolása
        self.table._refresh_header_labels()
        for btn in self.table._header_btns:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {th('color_bg_header')};
                    color: {th('color_accent')};
                    border: none;
                    border-bottom: 1px solid #2a2a4a;
                    font-size: {fs('font_small')};
                    font-weight: bold;
                    padding: 0 8px;
                    text-align: left;
                }}
                QPushButton:hover {{ background-color: #16213e; }}
            """)
        self.table._redraw()

# ---------------------------------------------------------------------------
# Névjegy ablak
# ---------------------------------------------------------------------------

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("about_title"))
        self.setFixedSize(380, 280)
        self.setModal(True)
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(10)

        title = QLabel(t("window_title"))
        title.setFont(QFont("Segoe UI", fv("font_title"), QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color:{th('color_accent')};")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#2a2a4a;")
        layout.addWidget(sep)

        for key in ["about_version", "about_author", "about_desc"]:
            lbl = QLabel(t(key))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(
                f"color:{th('color_text_muted')}; font-size:{fs('font_small')};"
            )
            layout.addWidget(lbl)

        github_lbl = QLabel(t("about_github"))
        github_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        github_lbl.setStyleSheet(
            f"color:{th('color_text_dim')}; font-size:{fs('font_tiny')}; margin-top:4px;"
        )
        layout.addWidget(github_lbl)

        github_url = "https://github.com/Nozy82/MicroIPTool"  # <- ide írd be a pontos URL-t
        link = QLabel(
            f'<a href="{github_url}" style="color:{th("color_accent")};">{github_url}</a>'
        )
        link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        link.setOpenExternalLinks(True)
        link.setStyleSheet(f"font-size:{fs('font_tiny')};")
        layout.addWidget(link)

        layout.addStretch()

        btn = QPushButton(t("about_close"))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self.close)
        btn.setFixedHeight(th("btn_height_normal"))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color:{th('color_accent_dark')};
                color:{th('color_accent')};
                border:1px solid {th('color_accent')};
                border-radius:4px;
                font-size:{fs('font_small')};
                padding:4px 16px;
            }}
            QPushButton:hover {{
                background-color:{th('color_accent')};
                color:#ffffff;
            }}
        """)
        layout.addWidget(btn)

    def _apply_style(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color:{th('color_bg')};
                color:{th('color_text')};
                font-family:'Segoe UI';
            }}
            QLabel {{ color:{th('color_text')}; font-size:{fs('font_small')}; }}
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
        layout.setSpacing(4)

        a = self.adapter_data

        header   = QHBoxLayout()
        icon     = {"WiFi": "📶", "Ethernet": "🔌"}.get(a["type"], "🖧")
        name_lbl = QLabel(f"{icon}  {a['name']}")
        name_lbl.setFont(QFont("Segoe UI", fv("font_normal"), QFont.Weight.Bold))
        name_lbl.setWordWrap(True)
        header.addWidget(name_lbl, stretch=1)

        if a["virtual"]:
            badge = QLabel(f" {t('adapter_badge_virtual')} ")
            badge.setStyleSheet(f"""
                background:{th('color_virtual_bg')};
                color:{th('color_virtual_fg')};
                border:1px solid {th('color_virtual_fg')};
                border-radius:3px;
                font-size:{fs('font_tiny')};
                padding:1px 4px;
            """)
        else:
            badge = QLabel(f" {t('adapter_badge_physical')} ")
            badge.setStyleSheet(f"""
                background:{th('color_physical_bg')};
                color:{th('color_physical_fg')};
                border:1px solid {th('color_physical_fg')};
                border-radius:3px;
                font-size:{fs('font_tiny')};
                padding:1px 4px;
            """)
        header.addWidget(badge)

        is_up = a["status"] == "Up"
        self.status_lbl = QLabel(
            f"  ● {t('adapter_status_up') if is_up else t('adapter_status_down')}"
        )
        self.status_lbl.setStyleSheet(
            f"color:{th('color_ok') if is_up else th('color_error')};"
            f"font-size:{fs('font_small')};"
        )
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
            lbl.setFixedWidth(60)
            lbl.setStyleSheet(
                f"color:{th('color_text_muted')}; font-size:{fs('font_tiny')};"
            )
            val = QLabel(value if value else t("adapter_no_ip"))
            val.setStyleSheet(f"font-size:{fs('font_tiny')};")
            val.setWordWrap(True)
            row.addWidget(lbl)
            row.addWidget(val, stretch=1)
            layout.addLayout(row)
            self._data_labels[key] = val

        if a["type"] == "WiFi":
            row = QHBoxLayout()
            lbl = QLabel(f"{t('adapter_ssid')}:")
            lbl.setFixedWidth(60)
            lbl.setStyleSheet(
                f"color:{th('color_text_muted')}; font-size:{fs('font_tiny')};"
            )
            self.ssid_val = QLabel(a["ssid"] if a["ssid"] else t("adapter_no_ssid"))
            self.ssid_val.setStyleSheet(f"font-size:{fs('font_tiny')};")
            row.addWidget(lbl)
            row.addWidget(self.ssid_val, stretch=1)
            layout.addLayout(row)

    def update_status(self, status, ip):
        is_up = status == "Up"
        self.adapter_data["status"] = status
        self.adapter_data["ip"]     = ip if ip else "N/A"
        self.status_lbl.setText(
            f"  ● {t('adapter_status_up') if is_up else t('adapter_status_down')}"
        )
        self.status_lbl.setStyleSheet(
            f"color:{th('color_ok') if is_up else th('color_error')};"
            f"font-size:{fs('font_small')};"
        )
        if "adapter_ip" in self._data_labels:
            self._data_labels["adapter_ip"].setText(ip if ip else t("adapter_no_ip"))

    def _apply_style(self, selected):
        a = self.adapter_data
        if a["virtual"]:
            self.setStyleSheet(
                f"AdapterCard {{ background-color:#2a1f00; border:2px solid "
                f"{th('color_virtual_fg')}; border-radius:8px; }} "
                f"QLabel {{ color:#ffffff; }}"
                if selected else
                f"AdapterCard {{ background-color:{th('color_bg_card')}; "
                f"border:1px solid #4a3800; border-radius:8px; }} "
                f"QLabel {{ color:{th('color_text_muted')}; }}"
            )
        else:
            self.setStyleSheet(
                f"AdapterCard {{ background-color:{th('color_accent_dark')}; border:2px solid "
                f"{th('color_accent')}; border-radius:8px; }} "
                f"QLabel {{ color:#ffffff; }}"
                if selected else
                f"AdapterCard {{ background-color:{th('color_bg_card')}; "
                f"border:1px solid #333; border-radius:8px; }} "
                f"QLabel {{ color:{th('color_text_muted')}; }}"
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

        top_row = QHBoxLayout()
        top_row.setContentsMargins(10, 6, 10, 4)

        self.cb_virtual = QCheckBox(t("show_virtual"))
        self.cb_virtual.setChecked(False)
        self.cb_virtual.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cb_virtual.setStyleSheet(f"""
            QCheckBox {{
                color:{th('color_text_muted')};
                font-size:{fs('font_tiny')};
            }}
            QCheckBox::indicator {{
                width:13px; height:13px;
                border:1px solid #444;
                border-radius:3px;
                background:{th('color_bg_card')};
            }}
            QCheckBox::indicator:checked {{
                background:{th('color_accent_dark')};
                border:1px solid {th('color_accent')};
            }}
            QCheckBox::indicator:hover {{ border-color:{th('color_accent')}; }}
        """)
        self.cb_virtual.stateChanged.connect(self._on_virtual_toggled)
        top_row.addWidget(self.cb_virtual)
        top_row.addStretch()

        self.btn_refresh = QPushButton(t("btn_refresh"))
        self.btn_refresh.setFixedHeight(th("btn_height_small"))
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color:{th('color_bg_card')};
                color:{th('color_accent')};
                border:1px solid {th('color_accent')};
                border-radius:4px;
                font-size:{fs('font_tiny')};
                padding:0px 8px;
            }}
            QPushButton:hover {{ background-color:{th('color_accent_dark')}; }}
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

        icon_path = asset("MicroIPTool.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._full_thread     = None
        self._status_thread   = None
        self._cached_adapters = []

        self._build_menu()
        self._build_ui()
        self._apply_global_style()

        self.full_refresh()

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._status_refresh)
        self.status_timer.start(5000)

    def _font_increase(self):
        global FONT_SCALE
        if FONT_SCALE < FONT_SCALE_MAX:
            FONT_SCALE = round(FONT_SCALE + FONT_SCALE_STEP, 1)
            self.apply_font_scale()

    def _font_decrease(self):
        global FONT_SCALE
        if FONT_SCALE > FONT_SCALE_MIN:
            FONT_SCALE = round(FONT_SCALE - FONT_SCALE_STEP, 1)
            self.apply_font_scale()

    def _font_reset(self):
        global FONT_SCALE
        FONT_SCALE = 1.0
        self.apply_font_scale()

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

    def _status_refresh(self):
        if self._status_thread and self._status_thread.isRunning():
            return
        self._status_thread = StatusRefreshThread()
        self._status_thread.finished.connect(self._on_status_done)
        self._status_thread.start()

    def _on_status_done(self, status_map):
        self.adapter_panel.update_status_only(status_map)
        selected = self.adapter_panel.get_selected_adapter()
        if selected and selected["name"] in status_map:
            s = status_map[selected["name"]]
            selected["status"] = s["status"]
            selected["ip"]     = s["ip"]
            self.ip_tab.update_info_only(selected)

    def apply_filter(self):
        if not self._cached_adapters:
            return
        filtered = filter_adapters(self._cached_adapters)
        warning  = check_ip_overlap(filtered)
        self.adapter_panel.refresh(filtered)
        self.warning_bar.setText(warning)
        self.warning_bar.setVisible(bool(warning))

    def on_adapter_selected(self, card):
        self.adapter_panel.select_card(card)
        self.ip_tab.load_adapter(card.adapter_data)
        self.ping_tab.load_adapter(card.adapter_data)
        self.scan_tab.load_adapter(card.adapter_data)

    def set_language(self, lang_code):
        global LANG
        LANG = lang_code
        self.setWindowTitle(t("window_title"))
        self.tabs.setTabText(0, t("tab_ip"))
        self.tabs.setTabText(1, t("tab_ping"))
        self.tabs.setTabText(2, t("tab_scan"))
        self.adapter_panel.update_texts()
        self.ip_tab.update_texts()
        self.ping_tab.update_texts()
        self.scan_tab.update_texts()
        if self._cached_adapters:
            filtered = filter_adapters(self._cached_adapters)
            self.adapter_panel.refresh(filtered)
        self.menuBar().clear()
        self._build_menu()

    def _build_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background-color:{th('color_bg_dark')};
                color:{th('color_text_muted')};
                font-family:'Segoe UI';
                font-size:{fs('font_small')};
                border-bottom:1px solid #222;
                padding:2px;
            }}
            QMenuBar::item:selected {{
                background-color:{th('color_accent_dark')};
                color:#ffffff;
            }}
            QMenu {{
                background-color:{th('color_bg_card')};
                color:{th('color_text')};
                border:1px solid #333;
                font-size:{fs('font_small')};
            }}
            QMenu::item:selected {{
                background-color:{th('color_accent_dark')};
                color:#ffffff;
            }}
            QMenu::separator {{ height:1px; background:#333; margin:4px 8px; }}
        """)

        file_menu = menubar.addMenu(t("menu_file"))
        exit_act  = QAction(t("menu_file_exit"), self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        settings_menu = menubar.addMenu(t("menu_settings"))
        lang_menu     = settings_menu.addMenu(t("menu_settings_lang"))
        act_hu        = QAction("🇭🇺  Magyar", self)
        act_hu.triggered.connect(lambda: self.set_language("hu"))
        lang_menu.addAction(act_hu)
        act_en        = QAction("🇬🇧  English", self)
        act_en.triggered.connect(lambda: self.set_language("en"))
        lang_menu.addAction(act_en)

        help_menu = menubar.addMenu(t("menu_help"))
        about_act = QAction(t("menu_help_about"), self)
        about_act.triggered.connect(lambda: AboutDialog(self).exec())
        help_menu.addAction(about_act)

        settings_menu.addSeparator()

        font_menu    = settings_menu.addMenu("Betűméret" if LANG == "hu" else "Font size")

        act_increase = QAction("🔺  Nagyobb  (A+)" if LANG == "hu" else "🔺  Larger  (A+)", self)
        act_increase.triggered.connect(self._font_increase)
        font_menu.addAction(act_increase)

        act_decrease = QAction("🔻  Kisebb  (A-)" if LANG == "hu" else "🔻  Smaller  (A-)", self)
        act_decrease.triggered.connect(self._font_decrease)
        font_menu.addAction(act_decrease)

        act_reset = QAction("↺  Alapméret" if LANG == "hu" else "↺  Default size", self)
        act_reset.triggered.connect(self._font_reset)
        font_menu.addAction(act_reset)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.warning_bar = QLabel("")
        self.warning_bar.setStyleSheet(f"""
            background-color:{th('color_warning_bg')};
            color:{th('color_warning_fg')};
            padding:6px 12px;
            font-size:{fs('font_small')};
        """)
        self.warning_bar.setVisible(False)
        main_layout.addWidget(self.warning_bar)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet(f"""
            QSplitter::handle {{ background-color:#333; width:2px; }}
            QSplitter::handle:hover {{ background-color:{th('color_accent')}; }}
        """)
        self.splitter.setChildrenCollapsible(False)

        self.adapter_panel = AdapterPanel()
        self.splitter.addWidget(self.adapter_panel)

        right_panel  = QWidget()
        right_panel.setMinimumWidth(400)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border:none; background:{th('color_bg')}; }}
            QTabBar::tab {{
                background:{th('color_bg_card')};
                color:{th('color_text_muted')};
                padding:10px 24px; border:none;
                font-size:{fs('font_small')};
                font-family:'Segoe UI';
            }}
            QTabBar::tab:selected {{
                background:{th('color_bg')};
                color:{th('color_accent')};
                border-bottom:2px solid {th('color_accent')};
            }}
            QTabBar::tab:hover {{ background:#16213e; color:{th('color_text')}; }}
        """)

        self.ip_tab   = IPSettingsTab()
        self.ping_tab = PingTab()
        self.scan_tab = ScanTab()

        self.tabs.addTab(self.ip_tab,   t("tab_ip"))
        self.tabs.addTab(self.ping_tab, t("tab_ping"))
        self.tabs.addTab(self.scan_tab, t("tab_scan"))

        right_layout.addWidget(self.tabs)
        self.splitter.addWidget(right_panel)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([280, 820])
        main_layout.addWidget(self.splitter, stretch=1)

        # Alsó státusz sáv – bal oldal: PC info, jobb oldal: verzió
        status_bar_widget = QWidget()
        status_bar_widget.setFixedHeight(28)
        status_bar_widget.setStyleSheet(f"""
            background-color:{th('color_bg_dark')};
            border-top:1px solid #222;
        """)
        status_bar_layout = QHBoxLayout(status_bar_widget)
        status_bar_layout.setContentsMargins(0, 0, 0, 0)
        status_bar_layout.setSpacing(0)

        self.status_bar_label = QLabel()
        self.status_bar_label.setStyleSheet(f"""
            color:{th('color_text_dim')};
            padding:0px 12px;
            font-size:{fs('font_tiny')};
        """)

        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setFixedWidth(60)
        version_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        version_label.setStyleSheet(f"""
            color:{th('color_text_dim')};
            padding:0px 12px;
            font-size:{fs('font_tiny')};
        """)

        status_bar_layout.addWidget(self.status_bar_label, stretch=1)
        status_bar_layout.addWidget(version_label)
        main_layout.addWidget(status_bar_widget)

    def _apply_global_style(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color:{th('color_bg')};
                color:{th('color_text')};
                font-family:'Segoe UI';
                font-size:{fs('font_small')};
            }}
            QScrollBar:vertical {{
                background:{th('color_bg_card')};
                width:6px;
                border-radius:3px;
            }}
            QScrollBar::handle:vertical {{
                background:#333;
                border-radius:3px;
            }}
        """)

    def apply_font_scale(self):
        """Újraépíti a teljes UI-t az új betűmérettel."""
        current_tab = self.tabs.currentIndex()

        self._apply_global_style()

        # Tab feliratok frissítése
        self.tabs.setTabText(0, t("tab_ip"))
        self.tabs.setTabText(1, t("tab_ping"))
        self.tabs.setTabText(2, t("tab_scan"))
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border:none; background:{th('color_bg')}; }}
            QTabBar::tab {{
                background:{th('color_bg_card')};
                color:{th('color_text_muted')};
                padding:10px 24px; border:none;
                font-size:{fs('font_small')};
                font-family:'Segoe UI';
            }}
            QTabBar::tab:selected {{
                background:{th('color_bg')};
                color:{th('color_accent')};
                border-bottom:2px solid {th('color_accent')};
            }}
            QTabBar::tab:hover {{ background:#16213e; color:{th('color_text')}; }}
        """)

        # Menüsor újraépítése
        self.menuBar().clear()
        self._build_menu()

        # Egyedi widgetek stílusfrissítése
        self.ip_tab.refresh_styles()
        self.ip_tab.update_texts()
        self.ping_tab.refresh_styles()
        self.ping_tab.update_texts()
        self.scan_tab.refresh_styles()
        self.scan_tab.update_texts()
        self.adapter_panel.update_texts()

        # Adapter kártyák újrarajzolása az új méretekkel
        if self._cached_adapters:
            filtered = filter_adapters(self._cached_adapters)
            self.adapter_panel.refresh(filtered)

        self.tabs.setCurrentIndex(current_tab) 

# ---------------------------------------------------------------------------
# Belépési pont
# ---------------------------------------------------------------------------

load_mac_db()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())