from ds1000z import DS1000Z
from dp800 import DP800
from proxr import ProXRRelayModule

import matplotlib.pyplot as plt
import random
import json

def ds1000z_demo():

    # To connect on Ubuntu:
    # ip link # to get the name of the network interface. Mine is enp7s0.
    # sudo ifconfig enp7s0 down
    # sudo ifconfig enp7s0 inet 192.168.254.254 netmask 255.255.255.0
    # sudo ifconfig enp7s0 up
    # ip a show enp7s0
    # Load configuration
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: 'config.json' not found. Please check file path.")
        return 
    try:
        instrument = DS1000Z(config['oscilloscope_ip'])
        instrument.reset()
        print("Success: Connected to Oscilloscope.")
    except Exception as e:
        print(f"\nConnection Failed: {e}")
        print("Hardware not found. Aborting demo to prevent crash.")
        return
    instrument.reset()
    instrument.set_probe_ratio(1)
    instrument.show_channel()
    instrument.set_channel_scale(1)
    instrument.set_channel_offset(0)
    instrument.set_timebase_scale(5e-6)
    instrument.set_source_function('RAMP')
    instrument.set_source_frequency(50e3)
    instrument.set_source_amplitude(5)
    instrument.enable_source()
    x_axis, samples = instrument.get_waveform_samples()
    plt.plot(x_axis, samples)
    plt.show()

    instrument.set_source_modulation_type('FM')
    instrument.enable_source_modulation()
    instrument.take_screenshot()


def dp800_demo():
    instrument = DP800("192.168.254.101")
    #instrument.set_display_mode("NORM")
    instrument.set_display_mode("WAVE")
    #instrument.set_display_mode("DIAL")
    #instrument.set_display_mode("CLAS")

def proxr_demo():
    relay_board = ProXRRelayModule("192.168.1.88", 2101)
    bank_values = [random.randint(0, 255) for _ in range(4)]
    relay_board.disable_automatic_relay_refresh()
    for i, bank_value in enumerate(bank_values):
        relay_board.set_all_relays_by_bank(bank_value, i + 1)
        relay_board.refresh()
    relay_board.enable_automatic_relay_refresh()

def main():
    ds1000z_demo()

if __name__ == "__main__":
    main()
