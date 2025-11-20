import psutil # type: ignore

class SysInfoModule:
    def __init__(self, core):
        self.core = core

    def get_status(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        return {
            "cpu": cpu,
            "mem": mem,
            "disk": disk,
        }
