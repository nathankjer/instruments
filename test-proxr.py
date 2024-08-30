import time
import unittest

from proxr import ProXRRelayModule

IP_ADDRESS = "192.168.1.88"
PORT = 2101


class TestRelayController(unittest.TestCase):
    def test_relays_in_bank(self):

        num_banks = 4
        num_timers = num_flashers = 16
        self.instrument = ProXRRelayModule(IP_ADDRESS, PORT)
        assert self.instrument.reset() == [85]

        assert self.instrument.get_testcyle_value() == [85]

        for timer in range(num_timers):
            self.instrument.get_timer(timer)
            self.instrument.get_timer_calibration(timer)
            assert self.instrument.turn_on_duration_timer(timer, 0, 0, 0, timer) == [85]
            assert self.instrument.toggle_timer(timer) == [85]
            time.sleep(0.1)
            assert self.instrument.toggle_timer(timer) == [85]
            time.sleep(0.1)

        for timer in range(num_timers):
            assert self.instrument.turn_on_pulse_timer(timer, 0, 0, 0, timer)
        time.sleep(4)

        assert self.instrument.set_all_flasher_speed(0) == [85]
        for flasher in range(num_flashers + 1):
            assert self.instrument.set_flasher_speed(flasher, 0) == [85]
            assert self.instrument.turn_on_relay_flasher(flasher) == [85]
            assert self.instrument.turn_off_relay_flasher(flasher) == [85]

        assert self.instrument.test_two_way_communication() == [85]
        assert self.instrument.reconnect() == [85]

        device = self.instrument.get_device_address()[0]
        assert self.instrument.disable_all_devices() == []
        assert self.instrument.enable_all_devices() == []
        assert self.instrument.disable_device(device) == []
        assert self.instrument.enable_device(device) == []
        assert self.instrument.disable_device_only(device) == []
        assert self.instrument.enable_device_only(device) == []

        device_id_1, device_id_2, year_of_design, firmware_version, device_address = self.instrument.get_device_description()
        assert self.instrument.get_device_features()["ProXR Controller"]

        assert self.instrument.disable_automatic_relay_refresh() == [85]
        assert self.instrument.store_automatic_refresh_setting() == [85]
        assert self.instrument.get_automatic_refresh_setting() == [0]
        assert self.instrument.refresh() == [85]
        assert self.instrument.enable_automatic_relay_refresh() == [85]
        assert self.instrument.store_automatic_refresh_setting() == [85]
        assert self.instrument.get_automatic_refresh_setting() == [1]

        for relay in range(32):
            assert self.instrument.turn_on_relay(relay) == [85]
            assert self.instrument.get_relay_status(relay) == [1]
            assert self.instrument.turn_off_relay(relay) == [85]
            assert self.instrument.get_relay_status(relay) == [0]
            assert self.instrument.turn_on_relay_only(relay) == [85]
            assert self.instrument.get_relay_status(relay) == [1]
            assert self.instrument.turn_off_relay(relay) == [85]
            assert self.instrument.get_relay_status(relay) == [0]
            assert self.instrument.toggle_relay(relay) == [85]
            assert self.instrument.get_relay_status(relay) == [1]
            assert self.instrument.toggle_relay(relay) == [85]
            assert self.instrument.get_relay_status(relay) == [0]

        bank = 0
        assert self.instrument.select_all_banks() == [85]
        assert self.instrument.get_selected_bank() == [0]
        assert self.instrument.turn_on_all_relays_in_bank() == [85]
        assert self.instrument.turn_off_all_relays_in_bank() == [85]
        assert self.instrument.get_relay_defaults_in_bank(bank) == [0] * 32
        assert self.instrument.turn_on_all_relays() == [85]
        assert self.instrument.turn_off_all_relays() == [85]
        assert self.instrument.get_all_relay_status() == [0] * 32
        for relay in range(8):
            assert self.instrument.get_relay_status_in_bank(relay) == [0]
            assert self.instrument.turn_on_relay_in_bank(relay) == [85]
            assert self.instrument.get_relay_status_in_bank(relay) == [1]
            assert self.instrument.turn_off_relay_in_bank(relay) == [85]
            assert self.instrument.get_relay_status_in_bank(relay) == [0]
            assert self.instrument.turn_on_relay_all_banks(relay) == [85]
            assert self.instrument.turn_off_relay_all_banks(relay) == [85]
        assert self.instrument.set_all_relays_in_bank(85) == [85]
        assert self.instrument.invert_all_relays_in_bank() == [85]
        assert self.instrument.reverse_all_relays_in_bank() == [85]
        assert self.instrument.set_all_relays_in_bank(0) == [85]
        assert self.instrument.set_all_relays(85) == [85]
        assert self.instrument.invert_all_relays() == [85]
        assert self.instrument.reverse_all_relays() == [85]
        assert self.instrument.set_all_relays(0) == [85]
        for bank in range(1, num_banks + 1):
            assert self.instrument.select_bank(bank) == [85]
            assert self.instrument.get_selected_bank() == [bank]
            assert self.instrument.turn_on_all_relays_in_bank() == [85]
            assert self.instrument.turn_off_all_relays_in_bank() == [85]
            assert self.instrument.get_all_relay_status_in_bank() == [0]
            assert self.instrument.get_relay_defaults_in_bank(bank) == [0]
            assert self.instrument.turn_on_all_relays_by_bank(bank) == [85]
            assert self.instrument.turn_off_all_relays_by_bank(bank) == [85]
            assert self.instrument.get_all_relay_status_by_bank(bank) == [0]
            self.instrument.read_contact_closure_by_bank(bank) == [0]
            self.instrument.read_contact_closure_by_bank_range(bank, 0) == [0]
            for relay in range(8):
                assert self.instrument.get_relay_status_in_bank(relay) == [0]
                assert self.instrument.turn_on_relay_in_bank(relay) == [85]
                assert self.instrument.get_relay_status_in_bank(relay) == [1]
                assert self.instrument.turn_off_relay_in_bank(relay) == [85]
                assert self.instrument.get_relay_status_in_bank(relay) == [0]
                assert self.instrument.get_relay_status_by_bank(relay, bank) == [0]
                assert self.instrument.turn_on_relay_by_bank(relay, bank) == [85]
                assert self.instrument.get_relay_status_by_bank(relay, bank) == [1]
                assert self.instrument.turn_off_relay_by_bank(relay, bank) == [85]
                assert self.instrument.get_relay_status_by_bank(relay, bank) == [0]
                for group_size in range(1, 8 + 1 - relay):
                    assert self.instrument.turn_on_relay_group(relay, bank, group_size) == [85]
                    assert self.instrument.turn_off_relay_group(relay, bank, group_size) == [85]
            assert self.instrument.set_all_relays_in_bank(85) == [85]
            assert self.instrument.invert_all_relays_in_bank() == [85]
            assert self.instrument.reverse_all_relays_in_bank() == [85]
            assert self.instrument.set_all_relays_in_bank(0) == [85]
            assert self.instrument.set_all_relays_by_bank(85, bank) == [85]
            assert self.instrument.invert_all_relays_by_bank(bank) == [85]
            assert self.instrument.reverse_all_relays_by_bank(bank) == [85]
            assert self.instrument.set_all_relays_by_bank(0, bank) == [85]
        del self.instrument


if __name__ == "__main__":
    unittest.main()
