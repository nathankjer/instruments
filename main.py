from ds1000z import DS1000Z
from dp800 import DP800

import matplotlib.pyplot as plt

def ds1000z_demo():

    # To connect on Ubuntu:
    # ip link # to get the name of the network interface. Mine is enp7s0.
    # sudo ifconfig enp7s0 down
    # sudo ifconfig enp7s0 inet 192.168.254.254 netmask 255.255.255.0
    # sudo ifconfig enp7s0 up
    # ip a show enp7s0
    # ping 192.168.254.100
    instrument = DS1000Z('192.168.254.100')
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

def main():
    ds1000z_demo()

if __name__ == "__main__":
    main()
