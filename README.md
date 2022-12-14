**Requires Python3.11+ (init script will auto install on RPi)**

install required libraries:

`python3.11 -m pip -r requirements.txt`

**On RPi**
Add PiCan device overlay

`sudo nano /boot/config`

```sh
dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25
```

`sudo reboot`

The init script installs Python and PyQt5. This will take a few hours to finish

```sh
cd $HOME
git clone https://github.com/MrTaco9001/wrx-digital-dashboard.git
cd wrx-digital-dashboard && chmod +x scripts/init_pi.sh && ./scripts/init_pi.sh
```

Recommendations:

- Overclock RPi to 2Ghz CPU 750Mhz GPU
- USB boot device
- Raspberry Pi OS 64-Bit
