# -*- coding: utf-8 -*-

#
# These constants are shared between the firmware
# and the application using this firmware.
# The original of this file is in the firmware.
# https://github.com/tempstabilizer2018group/micropython_esp32/blob/master/ports/esp32/modules/portable_firmware_constants.py
#
# The application may copy this file to be able to run on windows/linux
#

strHTTP_PATH_SOFTWAREUPDATE = '/softwareupdate'
strHTTP_PATH_VERSIONCHECK = '/versioncheck'

strHTTP_ARG_MAC = 'mac'
strHTTP_ARG_VERSION = 'version'
strHTTP_ARG_FILENAME = 'filename'

strFILENAME_VERSION = 'VERSION.TXT'

# See: https://github.com/tempstabilizer2018group/temp_stabilizer_2018/blob/master/software_rpi/rpi_root/etc/hostapd/hostapd.conf
strWLAN_SSID = 'TempStabilizer2018'
strWLAN_PW = 'wmm_enabled'
iWLAN_ScanTime_ms = 1500
iWLAN_Channel = 0 # All channels

# Reboot: slow blink, sharp
iLedReboot_pwm_hz = 2
iLedReboot_duty_1023 = 50
# Scan: blink, dark
iLedWlanScan_pwm_hz = 10
iLedWlanScan_duty_1023 = 100
# Connected: blink, bright
iLedWlanConnected_pwm_hz = 10
iLedWlanConnected_duty_1023 = 512

# See: https://github.com/tempstabilizer2018group/temp_stabilizer_2018/blob/master/software_rpi/rpi_root/etc/dhcpcd.conf
strGATEWAY_PI = '192.168.4.1'
strSERVER_PI = 'http://%s' % strGATEWAY_PI
strSERVER_DEFAULT = 'http://www.tempstabilizer2018.org'



