from device_fingerprint import DeviceFingerprint

device = DeviceFingerprint()

print(device.evaluate("device123"))
print(device.evaluate("device999"))
print(device.evaluate("device999", rooted=True))
print(device.evaluate("device999", rooted=True, emulator=True))