import minimalmodbus
import time
import serial
import sys
import threading
import platform

if platform.system() == "Windows":
    import msvcrt  # Để dùng getch trên Windows

PORT = "COM3"  # ⚠️ Đổi thành COM đúng với thiết bị bạn (VD: COM3, COM5,...)
BAUDRATE = 230400

# Thanh ghi
CONTROL_REGISTER = 0
CAMERA_STATUS = 1
CONFIG_BASE = 10
QR_RESULT_BASE = 20

running = True


def setup_instrument(slave_address):
    instrument = minimalmodbus.Instrument(PORT, slave_address)
    instrument.serial.baudrate = BAUDRATE
    instrument.serial.bytesize = 8
    instrument.serial.parity = serial.PARITY_NONE
    instrument.serial.stopbits = 1
    instrument.serial.timeout = 1.0
    instrument.mode = minimalmodbus.MODE_RTU
    return instrument


def control_camera(instrument, command):
    try:
        instrument.write_register(CONTROL_REGISTER, command)
        print(
            f"\n[INFO] Send command {'ON' if command else 'OFF'} camera - Slave {instrument.address}"
        )
        time.sleep(0.01)
    except Exception as e:
        print(f"\n[ERROR] Control camera (Slave {instrument.address}): {e}")


def read_camera_status(instrument):
    try:
        status = instrument.read_register(CAMERA_STATUS)
        print(
            f"\n[INFO] Camera Slave {instrument.address}: {'RUNNING' if status else 'STOP'}"
        )
        return status
    except Exception as e:
        print(f"[ERROR] Read status (Slave {instrument.address}): {e} \n")
        return None


def read_qr_results(instrument):
    qr_results = []

    for i in range(5):  # Đọc 5 kết quả
        try:
            registers = instrument.read_registers(QR_RESULT_BASE + i * 20, 20)

            qr_string = ""
            for reg in registers:
                if reg > 0:
                    qr_string += chr(reg)

            if qr_string:
                qr_results.append(qr_string)
            else:
                qr_results.append("None")

        except Exception as e:
            print(f"Error when read QR {i+1}: {e}")
            qr_results.append("Error")

    return qr_results


def modify_config(instrument, param_address, value):
    try:
        instrument.write_register(CONFIG_BASE + param_address, value)
        print(
            f"\n[INFO] Update config addr {param_address} -> {value} (Slave {instrument.address})"
        )
    except Exception as e:
        print(f"\n[ERROR] Update config (Slave {instrument.address}): {e}")


def getch():
    if platform.system() == "Windows":
        return msvcrt.getch().decode("utf-8").lower()
    else:
        import termios, tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch.lower()


def keyboard_listener():
    global running
    print("\nPress '2' or '3' to START, 's' to STOP camera (both slaves), 'q' to QUIT")
    while running:
        key = getch()
        if key == "2":
            control_camera(instrument2, 1)
        elif key == "3":
            control_camera(instrument3, 1)
        elif key == "s":
            control_camera(instrument2, 0)
            control_camera(instrument3, 0)
        elif key == "q":
            print("[INFO] QUITTING...")
            running = False
            break
        time.sleep(0.05)


def process_slave(instrument):
    status = read_camera_status(instrument)
    if status == 1:
        qr_results = read_qr_results(instrument)
        print(f"\n[QR FRAME] Slave {instrument.address}")
        for i, r in enumerate(qr_results):
            print(f"  Frame {i+1}: {r}")


def main():
    global running, instrument2, instrument3
    print("=== TEST MULTI SLAVE QR CM4 ===")
    try:
        instrument2 = setup_instrument(2)
        instrument3 = setup_instrument(3)
        print(f"[INFO] Connected {PORT}, slaves: 2 & 3")

        read_camera_status(instrument2)
        read_camera_status(instrument3)

        keyboard_thread = threading.Thread(target=keyboard_listener, daemon=True)
        keyboard_thread.start()

        while running:
            process_slave(instrument2)
            time.sleep(0.5)
            process_slave(instrument3)
            time.sleep(0.5)

    except Exception as e:
        print(f"\n[ERROR] {e}")
    finally:
        try:
            control_camera(instrument2, 0)
            control_camera(instrument3, 0)
        except:
            pass
        print("\n[INFO] STOPPED.")


if __name__ == "__main__":
    main()
