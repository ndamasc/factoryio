from pyModbusTCP.server import ModbusServer
import time

HOST = "0.0.0.0"
PORT = 5020

TURN_ADDR = 96        # Inputs.Turntable1_turn
FWD_ADDR  = 98        # Inputs.Turntable1_row_forward
SENSOR_TT3 = 18

server = ModbusServer(host=HOST, port=PORT, no_block=True)
server.start()
db = server.data_bank

print("Servidor Modbus ligado, controle da turntable pelos discrete inputs.")

def get_sensor(addr):
    """Lê coil (sensor no Factory I/O)"""
    return db.get_coils(addr, 1)[0]


mesa_ocupada = False
prev_sensor = False

def ciclo_turntable():
    global mesa_ocupada

    mesa_ocupada = True


    # 1) girar 90°
    print("Girando 90°...")
    db.set_discrete_inputs(TURN_ADDR, [1])
    time.sleep(2.0)        # ajustar até dar 90°

    # 2) rolar para frente (descarregar caixa)
    print("Ligando esteira roll forward...")
    db.set_discrete_inputs(FWD_ADDR, [1])
    time.sleep(2.5)        # tempo para a caixa sair
    db.set_discrete_inputs(FWD_ADDR, [0])
    print("Caixa descarregada.")

    # 3) esperar a caixa realmente sair do sensor
    timeout = time.time() + 5  # máx. 5s de espera
    while get_sensor(SENSOR_TT3) and time.time() < timeout:
        time.sleep(0.1)

    # 4) girar de volta para posição original
    print("Voltando a 0°...")
    db.set_discrete_inputs(TURN_ADDR, [0])  # se tiver sentido inverso; se não tiver, usar outro giro de +90
    time.sleep(2.0)


    mesa_ocupada = False
    print("✅ Ciclo da turntable concluído\n")


try:
    while True:
        caixa_no_sensor = get_sensor(SENSOR_TT3)

        # debug opcional
        # print(f"SENSOR_TT3: atual={caixa_no_sensor} prev={prev_sensor} mesa_ocupada={mesa_ocupada}")

        # dispara na borda 0->1 E somente se a mesa estiver livre
        if caixa_no_sensor and not prev_sensor and not mesa_ocupada:
            print("📦 Caixa detectada – iniciando sequência da turntable")
            ciclo_turntable()

        prev_sensor = caixa_no_sensor
        time.sleep(0.05)


except KeyboardInterrupt:
    server.stop()
    print("Servidor encerrado.")