class CLI:
    from .start import start
    from .process_editor import process_editor
    from . import settingsfile
    from . import thread_controller

    import logging
    logger = logging.getLogger('YNAB_Sync')

    def __init__(self, settings_files=[], cron=False):
        self.settings_files = settings_files
        self.cron = cron
        self.thread_objects = []
        self.start()
        
