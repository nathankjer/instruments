import time
import socket


class ProXRRelayModule:
    def __init__(self, ip_address, port):
        self.combus = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.combus.connect((ip_address, port))
        self.combus.settimeout(0.5)
        if "serial" in str(type(self.combus)):
            self.combus_type = "serial"
        else:
            self.combus_type = "socket"

    def __del__(self):
        self.combus.close()

    def send_command(self, command, bytes_back):
        bytes_in_packet = len(command)
        command.insert(0, bytes_in_packet)
        command.insert(0, 170)
        command.append(int(sum(command) & 255))
        if self.combus_type == "serial":
            self.combus.write(command)
            return self.combus.read(bytes_back)
        else:
            self.combus.send(bytearray(command))
            if bytes_back > 0:
                data = self.combus.recv(bytes_back + 3)
                handshake = data[0] == 170
                bytes_back = len(data) <= 1 or ord(data[1:2]) == (len(data) - 3)
                checksum = 0
                for byte in range(0, len(data) - 1):
                    checksum += data[byte]
                checksum = checksum & 255 == data[-1]
                if handshake and bytes_back and checksum:
                    payload = []
                    for byte in range(2, len(data) - 1):
                        payload.append(ord(data[byte : byte + 1]))
                    return payload
                else:
                    return None
            else:
                return []

    def turn_off_relay_in_bank(self, relay):
        assert relay >= 0 and relay < 8
        command = [254, relay]
        return self.send_command(command, 1)

    def turn_on_relay_in_bank(self, relay):
        assert relay >= 0 and relay < 8
        command = [254, 8 + relay]
        return self.send_command(command, 1)

    def get_relay_status_in_bank(self, relay):
        assert relay >= 0 and relay < 8
        command = [254, 16 + relay]
        return self.send_command(command, 1)

    def get_all_relay_status_in_bank(self):
        command = [254, 24]
        return self.send_command(command, 1)

    def enable_automatic_relay_refresh(self):
        command = [254, 25]
        return self.send_command(command, 1)

    def disable_automatic_relay_refresh(self):
        command = [254, 26]
        return self.send_command(command, 1)

    def enable_reporting_mode(self):
        command = [254, 27]
        return self.send_command(command, 1)

    def disable_reporting_mode(self):
        command = [254, 28]
        return self.send_command(command, 1)

    def turn_off_all_relays_in_bank(self):
        command = [254, 29]
        return self.send_command(command, 1)

    def turn_on_all_relays_in_bank(self):
        command = [254, 30]
        return self.send_command(command, 1)

    def invert_all_relays_in_bank(self):
        command = [254, 31]
        return self.send_command(command, 1)

    def reverse_all_relays_in_bank(self):
        command = [254, 32]
        return self.send_command(command, 1)

    def test_two_way_communication(self):
        command = [254, 33]
        return self.send_command(command, 1)

    def set_configuration_mode(self, duration):
        command = [254, 33, 140, 86, duration]
        return self.send_command(command, 1)

    def get_selected_bank(self):
        command = [254, 34]
        return self.send_command(command, 1)

    def store_automatic_refresh_setting(self):
        command = [254, 35]
        return self.send_command(command, 1)

    def get_automatic_refresh_setting(self):
        command = [254, 36]
        return self.send_command(command, 1)

    def refresh(self):
        command = [254, 37]
        return self.send_command(command, 1)

    def set_all_relays_in_bank(self, status):
        command = [254, 40, status]
        return self.send_command(command, 1)

        # Bank is only passed to these because we want to know how big the response will be

    def store_relay_defaults_in_bank(self, bank):
        command = [254, 42]
        return self.send_command(command, 1)

    def get_relay_defaults_in_bank(self, bank):
        command = [254, 43]
        return self.send_command(command, 32 if bank == 0 else 1)

    def get_relay_status(self, relay):
        lsb = relay & 255
        msb = relay >> 8
        command = [254, 44, lsb, msb]
        return self.send_command(command, 1)

    def set_all_flasher_speed(self, speed):
        command = [254, 45, 0, speed]
        return self.send_command(command, 1)

    def set_flasher_speed(self, flasher, speed):
        command = [254, 45, flasher, speed]
        return self.send_command(command, 1)

    def turn_off_relay_flasher(self, flasher):
        command = [254, 45, flasher, 0]
        return self.send_command(command, 1)

    def turn_on_relay_flasher(self, flasher):
        command = [254, 45, flasher, 1]
        return self.send_command(command, 1)

    def turn_on_relay_only(self, relay):
        lsb = relay & 255
        msb = relay >> 8
        command = [254, 46, lsb, msb]
        return self.send_command(command, 1)

    def turn_off_relay(self, relay):
        lsb = relay & 255
        msb = relay >> 8
        command = [254, 47, lsb, msb]
        return self.send_command(command, 1)

    def toggle_relay(self, relay):
        command = [254, 47, relay, 0, 1]
        return self.send_command(command, 1)

    def turn_on_relay(self, relay):
        lsb = relay & 255
        msb = relay >> 8
        command = [254, 48, lsb, msb]
        return self.send_command(command, 1)

    def select_all_banks(self):
        command = [254, 49, 0]
        return self.send_command(command, 1)

    def select_bank(self, bank):
        assert bank >= 1 and bank < 5
        command = [254, 49, bank]
        return self.send_command(command, 1)

    def turn_on_duration_timer(self, timer, hours, minutes, seconds, relay):
        assert timer >= 0 and timer < 16
        assert hours >= 0 and hours < 256
        assert minutes >= 0 and minutes < 256
        assert seconds >= 0 and seconds < 256
        assert relay >= 0 and relay < 256
        command = [254, 50, 50 + timer, hours, minutes, seconds, relay]
        return self.send_command(command, 1)

    def turn_on_pulse_timer(self, timer, hours, minutes, seconds, relay):
        assert timer >= 0 and timer < 16
        assert hours >= 0 and hours < 256
        assert minutes >= 0 and minutes < 256
        assert seconds >= 0 and seconds < 256
        assert relay >= 0 and relay < 256
        command = [254, 50, 70 + timer, hours, minutes, seconds, relay]
        return self.send_command(command, 1)

    def get_timer(self, timer):
        command = [254, 50, 130, timer]
        return self.send_command(command, 4)

    def toggle_timer(self, timer):
        command = [254, 50, 131, timer]
        return self.send_command(command, 1)

    def set_timer_calibration(self, timer, calibration):
        command = [254, 50, 132, timer, calibration]
        return self.send_command(command, 1)

    def get_timer_calibration(self, timer):
        command = [254, 50, 133, timer]
        return self.send_command(command, 2)

    def turn_on_calibrators(self):
        command = [254, 50, 134]
        return self.send_command(command, 1)

    def turn_off_calibrators(self):
        command = [254, 50, 135]
        return self.send_command(command, 1)

    def reset(self):
        command = [254, 50, 144]
        return self.send_command(command, 1)

    def get_testcyle_value(self):
        command = [254, 50, 145]
        return self.send_command(command, 4)

    def set_testcycle_value(self, value):
        command = [254, 50, 146, value]
        return self.send_command(command, 1)

    def reconnect(self):
        command = [254, 50, 147]
        return self.send_command(command, 1)

    def get_device_features(self):
        command = [254, 53, 243, 4]
        device_id_byte_1, device_id_byte_2, device_id_byte_3, device_id_byte_4, device_id_byte_5 = self.send_command(command, 8)
        return {
            "ProXR Controller": bool(0b00000001 & device_id_byte_1),
            "AD8": bool(0b00000010 & device_id_byte_1),
            "Input Contact Closure Scan": bool(0b00000100 & device_id_byte_1),
            "Programmable Potentiometer": bool(0b00001000 & device_id_byte_1),
            "ADC": bool(0b00010000 & device_id_byte_1),
            "Scratchpad Memory": bool(0b00100000 & device_id_byte_1),
            "AVA Security Protocols": bool(0b01000000 & device_id_byte_1),
            "Current Monitoring": bool(0b10000000 & device_id_byte_1),
            "E3C Commands": bool(0b00000001 & device_id_byte_2),
            "Pulsar Light Dimmer": bool(0b00000010 & device_id_byte_2),
            "AD8 Relay Activator Event Generator": bool(0b00001000 & device_id_byte_2),
            "8-Bit Digital I/O on Port 1": bool(0x00010000 & device_id_byte_2),
            "8-Bit Digital I/O on Port 2": bool(0x00100000 & device_id_byte_2),
            "Lifetime Counter": bool(0x01000000 & device_id_byte_2),
            "Fusion Decision Maker Logic": bool(0x10000000 & device_id_byte_2),
            "Taralist Time Activated Relay Command Set": bool(0x00000001 & device_id_byte_3),
            "AD8 Command Set on Port 2": bool(0x00000010 & device_id_byte_3),
            "Input Contact Closure Scan on Port 2": bool(0x00000100 & device_id_byte_3),
            "Programmable Potentiometer on Port 2": bool(0x00001000 & device_id_byte_3),
            "ADC on Port 2": bool(0x00010000 & device_id_byte_3),
            "Sonar Distance Measurement on Port 1": bool(0x00100000 & device_id_byte_3),
            "Sonar Distance Measurement on Port 2": bool(0x01000000 & device_id_byte_3),
            "Fusion Class Controller": bool(0x10000000 & device_id_byte_3),
            "Internal Bus I2C Communications": bool(0x00010000 & device_id_byte_4),
            "External Bus I2C Communications": bool(0x00100000 & device_id_byte_4),
            "Dual Communication Ports": bool(0x01000000 & device_id_byte_4),
            "API Command Set": bool(0x10000000 & device_id_byte_4),
            "Push Notifications": bool(0x00000001 & device_id_byte_5),
            "KFX Key Fob Configuration": bool(0x00010000 & device_id_byte_5),
            "MirW Control Functions": bool(0x00100000 & device_id_byte_5),
        }

    def turn_off_relay_all_banks(self, relay):
        command = [254, 100 + relay, 0]
        return self.send_command(command, 1)

    def turn_off_relay_by_bank(self, relay, bank):
        command = [254, 100 + relay, bank]
        return self.send_command(command, 1)

    def turn_off_relay_group(self, relay, bank, group_size):
        command = [254, 100 + relay, bank, group_size - 1]
        return self.send_command(command, 1)

    def turn_on_relay_all_banks(self, relay):
        command = [254, 108 + relay, 0]
        return self.send_command(command, 1)

    def turn_on_relay_by_bank(self, relay, bank):
        command = [254, 108 + relay, bank]
        return self.send_command(command, 1)

    def turn_on_relay_group(self, relay, bank, group_size):
        command = [254, 108 + relay, bank, group_size]
        return self.send_command(command, 1)

    def get_relay_status_by_bank(self, relay, bank):
        command = [254, 116 + relay, bank]
        return self.send_command(command, 1)

    def get_all_relay_status(self):
        command = [254, 124, 0]
        return self.send_command(command, 32)

    def get_all_relay_status_by_bank(self, bank):
        command = [254, 124, bank]
        return self.send_command(command, 1)

    def turn_off_all_relays(self):
        command = [254, 129, 0]
        return self.send_command(command, 1)

    def turn_off_all_relays_by_bank(self, bank):
        command = [254, 129, bank]
        return self.send_command(command, 1)

    def turn_on_all_relays(self):
        command = [254, 130, 0]
        return self.send_command(command, 1)

    def turn_on_all_relays_by_bank(self, bank):
        command = [254, 130, bank]
        return self.send_command(command, 1)

    def invert_all_relays(self):
        command = [254, 131, 0]
        return self.send_command(command, 1)

    def invert_all_relays_by_bank(self, bank):
        command = [254, 131, bank]
        return self.send_command(command, 1)

    def reverse_all_relays(self):
        command = [254, 132, 0]
        return self.send_command(command, 1)

    def reverse_all_relays_by_bank(self, bank):
        command = [254, 132, bank]
        return self.send_command(command, 1)

    def set_all_relays(self, status):
        command = [254, 140, status, 0]
        return self.send_command(command, 1)

    def set_all_relays_by_bank(self, status, bank):
        command = [254, 140, status, bank]
        return self.send_command(command, 1)

    def store_relay_defaults_by_bank(self, bank):
        command = [254, 142, bank]
        return self.send_command(command, 1)

    def get_relay_defaults_by_bank(self, bank):
        command = [254, 143, bank]
        return self.send_command(command, 1)

    def read_contact_closure_by_bank(self, bank):
        command = [254, 175, bank - 1]
        return self.send_command(command, 1)

    def read_contact_closure_by_bank_range(self, start_bank, count):
        command = [254, 175, start_bank, count]
        return self.send_command(command, count + 1)

    def get_device_description(self):
        command = [254, 246]
        return self.send_command(command, 5)

    def get_device_address(self):
        command = [254, 247]
        return self.send_command(command, 1)

    def enable_all_devices(self):
        command = [254, 248]
        return self.send_command(command, 0)

    def disable_all_devices(self):
        command = [254, 249]
        return self.send_command(command, 0)

    def enable_device(self, device):
        command = [254, 250, device]
        return self.send_command(command, 0)

    def disable_device(self, device):
        command = [254, 251, device]
        return self.send_command(command, 0)

    def enable_device_only(self, device):
        command = [254, 252, device]
        return self.send_command(command, 0)

    def disable_device_only(self, device):
        command = [254, 253, device]
        return self.send_command(command, 0)

    def store_device_number(self, device):
        command = [254, 255, device]
        return self.send_command(command, 0)
