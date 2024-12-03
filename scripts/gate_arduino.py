import serial
import serial.tools.list_ports
import pygame
import time

# Initialize Pygame mixer for sound
pygame.mixer.init()

# Load the sound file
pygame.mixer.music.load("../assets/sound/alam.mp3")

def find_arduino():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.device == 'COM4':
            return port.device
    return None

def main():
    arduino_port = find_arduino()
    if not arduino_port:
        print("Arduino not found")
        return

    serial_inst = serial.Serial()
    serial_inst.baudrate = 9600
    serial_inst.port = arduino_port
    serial_inst.open()

    try:
        while True:
            if serial_inst.in_waiting:
                line = serial_inst.readline().decode('utf-8').rstrip()
                print(line)

    except KeyboardInterrupt:
        pass
    finally:
        serial_inst.close()

if __name__ == "__main__":
    main()
