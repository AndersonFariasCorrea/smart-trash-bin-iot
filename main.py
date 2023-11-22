import time
import machine
import socket


TRIGGER_PIN = machine.Pin(12, machine.Pin.OUT)
ECHO_PIN = machine.Pin(14, machine.Pin.IN)


def medir_distancia():
    # Emitir um pulso curto no pino Trigger
    TRIGGER_PIN.on()
    time.sleep_us(10)
    TRIGGER_PIN.off()

    # Medir a duração do pulso no pino Echo
    pulse_duration = machine.time_pulse_us(ECHO_PIN, 1, 30000)  # 30.000 us = 30 ms (máximo alcance do HC-SR04)

    # Calcular a distância em centímetros
    distancia_cm = (pulse_duration / 2) / 29.1  # Fator de conversão (29.1 us/cm)

    return distancia_cm


def do_connect():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Conectando à rede...')
        wlan.connect('DELTA_FIBRA_ANDERSON', 'Potato23@.')
        while not wlan.isconnected():
            pass
    print('Configuração de rede:', wlan.ifconfig())
    return wlan  # Retorna a variável 'wlan' para uso fora da função


distancia = 0
do_connect()

def get_query(input_str):
    result = []
    start = 0

    while True:
        start_quote = input_str.find('"', start)
        if start_quote == -1:
            break

        end_quote = input_str.find('"', start_quote + 1)
        if end_quote == -1:
            break

        result.append(input_str[start_quote + 1:end_quote])
        start = end_quote + 1

    return result


def start_app():
    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv.bind(('0.0.0.0', 8080))
    serv.listen(5)

    while True:
        conn, addr = serv.accept()
        from_client = ''

        while True:
            data = conn.recv(4096)
            if not data:
                break
            from_client += data.decode('utf8')
            from_client = get_query(from_client)

            if from_client[0] == 'action':
                if from_client[1] == 'status':
                    # pega distancia
                    distancia = medir_distancia()
                    distancia = "{:.2f}".format(distancia)
            else:
                distancia = False
            print(from_client)
            conn.send(str(distancia).encode())

        conn.close()

        print('client disconnected and shutdown')


start_app()
