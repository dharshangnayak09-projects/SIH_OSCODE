class DeviceFingerprint:
    def __init__(self):
        self.trusted_devices = {
            "device123",
            "device456"
        }

    def evaluate(self, device_id, rooted=False, emulator=False):
        score = 100

        if device_id not in self.trusted_devices:
            score -= 30

        if rooted:
            score -= 40

        if emulator:
            score -= 30

        score = max(score, 0)

        return {
            "device_id": device_id,
            "device_score": score
        }