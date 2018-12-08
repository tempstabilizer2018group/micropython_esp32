# -*- coding: utf-8 -*-

import uos
import utime
import machine

# See: https://github.com/tempstabilizer2018group/tempstabilizer2018/blob/master/software/http_server/python/python3_github_pull.py
strFILENAME_SW_VERSION = 'VERSION.TXT'

strMAC = ''.join(['%02X'%i for i in machine.unique_id()])

# See: https://github.com/tempstabilizer2018group/temp_stabilizer_2018/blob/master/software_rpi/rpi_root/etc/dhcpcd.conf
strGATEWAY_PI = '192.168.4.1'
strSERVER_PI = 'http://%s' % strGATEWAY_PI
strSERVER_DEFAULT = 'http://www.tempstabilizer2018.org'

# See: https://github.com/tempstabilizer2018group/temp_stabilizer_2018/blob/master/software_rpi/rpi_root/etc/hostapd/hostapd.conf
strWLAN_SSID = 'TempStabilizer2018'
strWLAN_PW = None

def __getSwVersion():
  '''TODO: Cache'''
  try:
    with open(strFILENAME_SW_VERSION, 'r') as fIn:
      return fIn.read().strip()
  except:
    return 'none'

strSwVersion = __getSwVersion()

def getServer(wlan):
  listIfconfig = wlan.ifconfig()
  strGateway = listIfconfig[2]
  if strGateway == strGATEWAY_PI:
    return strSERVER_PI
  return strSERVER_DEFAULT

def getDownloadUrl(wlan):
  return __getUrl(wlan, 'software')

def getVersionCheckUrl(wlan):
  return __getUrl(wlan, 'versioncheck')

def __getUrl(wlan, strFunction):
  return '%s/pull/%s.download?mac=%s&version=%s' % (getServer(wlan), strFunction, strMAC, strSwVersion)

class Gpio:
  def __init__(self):
    self.pin_button = machine.Pin(16, machine.Pin.IN, machine.Pin.PULL_UP)
    self.pin_led = machine.Pin(22, machine.Pin.OUT)
    self.pwm = None

  def pwmLed(self, freq=10):
    self.pwm = machine.PWM(self.pin_led, freq=freq)

  def setLed(self, bOn=True):
    if self.pwm != None:
      self.pwm.deinit()
    self.pin_led.value(bOn)

  def isButtonPressed(self):
    '''Returns True if the Button is pressed.'''
    return self.pin_button.value() == 0

  def isPowerOnBoot(self):
    '''Returns True if power on. False if reboot by software or watchdog.'''
    return machine.PWRON_RESET == machine.reset_cause()


objGpio = Gpio()

def isFilesystemEmpty():
  # Only 'boot.py' exists.
  return len(uos.listdir()) == 1

def isUpdateFinished():
  return strFILENAME_SW_VERSION in uos.listdir()

def reboot(strReason):
  print(strReason)
  objGpio.setLed(bOn=False)
  # uos.sync() does not exist. Maybe a pause does the same. Maybe its event not used.
  utime.sleep_ms(1000)
  machine.reset()

def formatAndReboot():
  '''Destroy the filesystem so that it will be formatted during next boot'''
  objGpio.pwmLed(freq=10)
  import inisetup
  # See: https://github.com/micropython/micropython/blob/master/ports/esp32/modules/inisetup.py
  inisetup.setup()
  reboot('Reboot after format filesystem')

def update(strUrl):
  '''
    Returns True: If a new software was installed.
    Returns False: If there is no new software.
    On error: reboot
  '''
  import errno
  import upip
  import urequests
  import upip_utarfile
  
  # Forked from https://github.com/micropython/micropython/blob/master/tools/upip.py#L74
  # Expects *file* name
  def _makedirs(name, mode=0o777):
    ret = False
    s = ""
    comps = name.rstrip("/").split("/")[:-1]
    if len(comps) == 0:
      # There is not top-directory
      return True
    if comps[0] == "":
      s = "/"
    for c in comps:
      if s and s[-1] != "/":
        s += "/"
      s += c
      try:
        uos.mkdir(s)
        ret = True
      except OSError as e:
        if e.args[0] != errno.EEXIST and e.args[0] != errno.EISDIR:
          raise
        ret = False
    return ret

  print('HTTP-Get ' + strUrl)
  try:
    r = urequests.get(strUrl)
    if r.status_code != 200:
      reboot('FAILED %d %s' % (r.status_code, r.reason))
      r.close()
  except OSError as e:
    reboot('FAILED %s' % e)

  tar = upip_utarfile.TarFile(fileobj=r.raw)
  for info in tar:
    if info.type != upip_utarfile.REGTYPE:
      continue
    print('  extracting ' + info.name)
    _makedirs(info.name)
    subf = tar.extractfile(info)
    upip.save_file(info.name, subf)
  r.close()

  print('Successful update!')
  return True

def connect(wlan, strSsid, strPassword):
  wlan.connect(strSsid, strPassword)
  for iPause in range(10):
    # Do not use self.delay_ms(): Light sleep will kill the wlan!
    utime.sleep_ms(1000)
    if wlan.isconnected():
      print('connected!')
      return True
  return False

def connectWlanReboot():
  import network

  objGpio.pwmLed(freq=10)

  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)

  # listWlans = wlan.scan(200, 6)
  print('Connecting to %s/%s' % (strWLAN_SSID, strWLAN_PW))
  bConnected = connect(wlan, strWLAN_SSID, strWLAN_PW)
  if not bConnected:
    reboot('Could not connect to wlan' )
  return wlan

def updateAndReboot():
  wlan = connectWlanReboot()

  strUrl = getDownloadUrl(wlan)
  bSoftwareUpdated = update(strUrl)
  wlan.active(False)

  if not bSoftwareUpdated:
    # This is somehow strange: There shouldn't be any software installed....s
    return

  reboot('SUCCESS: Successful update. Reboot')

def bootCheckUpdate():
  '''
    May reboot several times to format the filesystem and do the update.
  '''
  objGpio.setLed(False)

  if objGpio.isButtonPressed() and objGpio.isPowerOnBoot():
    print('Button presed. Format')
    formatAndReboot()

  if isFilesystemEmpty():
    print('Filesystem is empty: Update')
    updateAndReboot()

  if not isUpdateFinished():
    print('Update was not finished. Format')
    formatAndReboot()

  objGpio.setLed(False)

def getSwVersionGit(wlan):
  '''
    returns verions: On success
    returns None: on failure
  '''
  import urequests
  strUrl = getVersionCheckUrl(wlan)
  print('HTTP-Get ' + strUrl)
  try:
    r = urequests.get(strUrl)
    if r.status_code != 200:
      print('FAILED %d %s' % (r.status_code, r.reason))
      r.close()
      return None
    strSwVersionGit = r.text
    r.close()
    return strSwVersionGit
  except OSError as e:
    print('FAILED %s' % e)
  return None

def checkForNewSwAndReboot(wlan):
  '''
    returns True: The version changed
    returns False: Same version or error
  '''
  strSwVersionGit = getSwVersionGit(wlan)
  if strSwVersionGit != None:
    print('Software versions: node/git: %s/%s' % (strSwVersion, strSwVersionGit))
    if strSwVersionGit != strSwVersion:
      print('Software version CHANGED')
      return True
  return False
  
def checkForNewSwAndRebootRepl():
  wlan = connectWlanReboot()
  bNewSwVersion = checkForNewSwAndReboot(wlan)
  wlan.active(False)
  if bNewSwVersion:
    formatAndReboot()
  objGpio.setLed(False)

class Command:
  def __init__(self, func):
    self.__func = func

  def __repr__(self):
    return self.__func()

  def __call__(self):
    return self.__repr__()
