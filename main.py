import time
import machine
import socket


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


def get_filled_calc(a, b):
    if b == 0:
        return "100%"

    percentage = (a / b) * 100
    return percentage


class SmartTrashBin:
    def __init__(self):
        self.TRIGGER_PIN = machine.Pin(12, machine.Pin.OUT)
        self.ECHO_PIN = machine.Pin(14, machine.Pin.IN)
        self.distancia = 0.0

    def medir_distancia(self):
        # Emitir um pulso curto no pino Trigger
        self.TRIGGER_PIN.on()
        time.sleep_us(10)
        self.TRIGGER_PIN.off()

        # Medir a duração do pulso no pino Echo
        pulse_duration = machine.time_pulse_us(self.ECHO_PIN, 1, 30000)  # 30.000 us = 30 ms (máximo alcance do HC-SR04)

        # Calcular a distância em centímetros
        distancia_cm = (pulse_duration / 2) / 29.1  # Fator de conversão (29.1 us/cm)

        return distancia_cm

    def store_trash_bin_info(self):
        content = str(self.medir_distancia())
        print(content)
        with open('trash_bin_size.txt', 'w') as file:
            file.write(content)
        return content

    def read_static(self, file_path):
        with open(file_path, 'r') as file:
            content = file.read()
        return content

    def do_connect(self):
        import network
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            print('Conectando à rede...')
            wlan.connect('DELTA_FIBRA_ANDERSON', 'Potato23@.')
            while not wlan.isconnected():
                pass
        print('Configuração de rede:', wlan.ifconfig())
        return wlan

    def start_app(self):
        wlan = self.do_connect()

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
                    print(from_client[1])
                    if from_client[1] == 'status':
                        self.distancia = self.medir_distancia()
                        trash_bin_size = self.read_static('trash_bin_size.txt')

                        self.distancia = get_filled_calc(float(self.distancia), float(trash_bin_size))
                        self.distancia = "{:.2f}%".format(self.distancia)
                        print("status - trash bin size:" + trash_bin_size + "now: " + self.distancia)

                    elif from_client[1] == 'start_or_restart':

                        trash_bin_size = self.store_trash_bin_info()
                        if trash_bin_size is not None:
                            self.distancia = '100.00%'

                        print("start_or_restart - trash bin size:" + trash_bin_size)
                else:
                    self.distancia = False
                print(from_client)
                conn.send((str(self.distancia) + " de espaço disponível").encode())

            conn.close()
            print('client disconnected and shutdown')


smart_bin = SmartTrashBin()
smart_bin.start_app()
