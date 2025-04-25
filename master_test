import struct
import time
from pymodbus.client.sync import ModbusSerialClient

client = ModbusSerialClient(
    method='rtu',
    port='COM5',        # Đổi thành cổng serial phù hợp
    baudrate=230400,
    timeout=0.01
)

client.connect()

def decode_frame_from_registers(regs):
    # 10 ký tự số
    digits = ''.join(chr(r) for r in regs[:10])
    # 2 số nguyên (signed 16 bit)
    int1 = struct.unpack('>h', regs[10].to_bytes(2, 'big'))[0]
    int2 = struct.unpack('>h', regs[11].to_bytes(2, 'big'))[0]
    # 1 số thực 32 bit (float)
    float_bytes = regs[12].to_bytes(2, 'big') + regs[13].to_bytes(2, 'big')
    float1 = struct.unpack('>f', float_bytes)[0]
    return f"{digits}_{int1}_{int2}_{float1}"

t1 = time.time()
for i in range(200):
    start = time.time()
    response = client.read_holding_registers(address=0, count=70, unit=1)
    end = time.time()
    elapsed_ms = (end - start) * 1000

    if not response.isError():
        data = response.registers
        print(f"Lần {i+1}:")
        for j in range(5):
            frame_regs = data[j*14:(j+1)*14]
            frame_str = decode_frame_from_registers(frame_regs)
            print(f"  Frame {j+1}: {frame_str}")
        print(f"  Thời gian giao tiếp: {elapsed_ms:.2f} ms\n")
    else:
        print(f"Lần {i+1}: Lỗi đọc dữ liệu: {response} | Thời gian: {elapsed_ms:.2f} ms")

    time.sleep(0.1)
t2 = time.time()
# thời gian trung binh bỏ qua time.sleep(0.1)
average_time = (t2 - t1 - 0.1 * 200) / 200 * 1000
print(f"Thời gian trung bình mỗi lần đọc: {average_time:.2f} ms")
client.close()
