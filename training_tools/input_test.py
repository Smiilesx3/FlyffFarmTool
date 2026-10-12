import ctypes
import time
from ctypes import wintypes


# ============================================================
# Windows API
# ============================================================

user32 = ctypes.WinDLL(
    "user32",
    use_last_error=True,
)

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


# ============================================================
# Scan Codes
# ============================================================

SCAN_F2 = 0x3C
SCAN_RIGHT = 0x4D


# ============================================================
# Windows Structures
# ============================================================

ULONG_PTR = wintypes.WPARAM


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _anonymous_ = (
        "union",
    )

    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION),
    ]


# ============================================================
# SendInput
# ============================================================

def send_input(
        input_data: INPUT,
) -> bool:

    result = user32.SendInput(
        1,
        ctypes.byref(input_data),
        ctypes.sizeof(INPUT),
    )

    if result != 1:
        error_code = ctypes.get_last_error()

        print(
            f"SendInput FEHLER: {error_code}"
        )

        return False

    return True


# ============================================================
# Keyboard
# ============================================================

def keyboard_down(
        scan_code: int,
        extended: bool = False,
):
    flags = KEYEVENTF_SCANCODE

    if extended:
        flags |= KEYEVENTF_EXTENDEDKEY

    input_data = INPUT(
        type=INPUT_KEYBOARD,
        ki=KEYBDINPUT(
            wVk=0,
            wScan=scan_code,
            dwFlags=flags,
            time=0,
            dwExtraInfo=0,
        ),
    )

    return send_input(
        input_data
    )


def keyboard_up(
        scan_code: int,
        extended: bool = False,
):
    flags = (
            KEYEVENTF_SCANCODE
            | KEYEVENTF_KEYUP
    )

    if extended:
        flags |= KEYEVENTF_EXTENDEDKEY

    input_data = INPUT(
        type=INPUT_KEYBOARD,
        ki=KEYBDINPUT(
            wVk=0,
            wScan=scan_code,
            dwFlags=flags,
            time=0,
            dwExtraInfo=0,
        ),
    )

    return send_input(
        input_data
    )


def press_key(
        scan_code: int,
        duration: float = 0.08,
        extended: bool = False,
):
    keyboard_down(
        scan_code,
        extended,
    )

    time.sleep(
        duration
    )

    keyboard_up(
        scan_code,
        extended,
    )


# ============================================================
# Mouse
# ============================================================

def move_mouse_absolute(
        x: int,
        y: int,
):
    screen_width = user32.GetSystemMetrics(
        0
    )

    screen_height = user32.GetSystemMetrics(
        1
    )

    normalized_x = int(
        x
        * 65535
        / max(
            1,
            screen_width - 1,
            )
    )

    normalized_y = int(
        y
        * 65535
        / max(
            1,
            screen_height - 1,
            )
    )

    input_data = INPUT(
        type=INPUT_MOUSE,
        mi=MOUSEINPUT(
            dx=normalized_x,
            dy=normalized_y,
            mouseData=0,
            dwFlags=(
                    MOUSEEVENTF_MOVE
                    | MOUSEEVENTF_ABSOLUTE
            ),
            time=0,
            dwExtraInfo=0,
        ),
    )

    return send_input(
        input_data
    )


def left_click():
    down = INPUT(
        type=INPUT_MOUSE,
        mi=MOUSEINPUT(
            dx=0,
            dy=0,
            mouseData=0,
            dwFlags=MOUSEEVENTF_LEFTDOWN,
            time=0,
            dwExtraInfo=0,
        ),
    )

    up = INPUT(
        type=INPUT_MOUSE,
        mi=MOUSEINPUT(
            dx=0,
            dy=0,
            mouseData=0,
            dwFlags=MOUSEEVENTF_LEFTUP,
            time=0,
            dwExtraInfo=0,
        ),
    )

    send_input(
        down
    )

    time.sleep(
        0.08
    )

    send_input(
        up
    )


# ============================================================
# Countdown
# ============================================================

def countdown(
        seconds: int,
):
    print()
    print(
        "JETZT zu Flyff wechseln!"
    )

    for remaining in range(
            seconds,
            0,
            -1,
    ):
        print(
            f"Test in {remaining}..."
        )

        time.sleep(
            1
        )


# ============================================================
# Main
# ============================================================

def main():
    print()
    print(
        "======================================"
    )

    print(
        "Flyff SendInput Background Test"
    )

    print(
        "======================================"
    )

    print()
    print(
        "Der Test laeuft automatisch."
    )

    print()
    print(
        "Nach dem Start hast du 5 Sekunden, "
        "um Flyff in den Vordergrund zu holen."
    )

    print()
    print(
        "Danach passiert automatisch:"
    )

    print(
        "1. Maus -> Bildschirmmitte"
    )

    print(
        "2. 2 Sekunden warten"
    )

    print(
        "3. Linksklick"
    )

    print(
        "4. 2 Sekunden warten"
    )

    print(
        "5. Pfeil RECHTS fuer 1 Sekunde"
    )

    print(
        "6. 2 Sekunden warten"
    )

    print(
        "7. F2"
    )

    input(
        "\nENTER druecken, um zu starten..."
    )

    countdown(
        5
    )

    # --------------------------------------------------------
    # Maus bewegen
    # --------------------------------------------------------

    width = user32.GetSystemMetrics(
        0
    )

    height = user32.GetSystemMetrics(
        1
    )

    print(
        "TEST 1: Maus bewegen"
    )

    move_mouse_absolute(
        width // 2,
        height // 2,
        )

    time.sleep(
        2
    )

    # --------------------------------------------------------
    # Linksklick
    # --------------------------------------------------------

    print(
        "TEST 2: Linksklick"
    )

    left_click()

    time.sleep(
        2
    )

    # --------------------------------------------------------
    # Kamera
    # --------------------------------------------------------

    print(
        "TEST 3: Pfeil RECHTS"
    )

    keyboard_down(
        SCAN_RIGHT,
        extended=True,
    )

    time.sleep(
        1
    )

    keyboard_up(
        SCAN_RIGHT,
        extended=True,
    )

    time.sleep(
        2
    )

    # --------------------------------------------------------
    # F2
    # --------------------------------------------------------

    print(
        "TEST 4: F2"
    )

    press_key(
        SCAN_F2
    )

    time.sleep(
        1
    )

    print()
    print(
        "======================================"
    )

    print(
        "Test abgeschlossen."
    )

    print(
        "======================================"
    )

    print()

    input(
        "ENTER zum Beenden..."
    )


if __name__ == "__main__":
    main()