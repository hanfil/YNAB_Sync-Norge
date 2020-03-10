class CLI:
    from .start import run as start
    from . import settingsfile

    def __init__(self, settings_files=[], cron=False):
        self.settings_files = settings_files
        self.cron = cron
        self.start()
        
