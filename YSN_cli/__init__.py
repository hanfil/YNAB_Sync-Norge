class CLI:
    from .start import start, stop
    from .process_editor import process_editor
    from . import settingsfile
    from . import thread_controller

    import logging
    

    def __init__(self, settings_files=[], cron=False):
        self.logger = self.logging.getLogger('YNAB_Sync')
        self.logger.debug('CLI Initializing | CLI imported.')
        self.settings_files = settings_files
        self.cron = cron
        self.thread_objects = []
        self.start()
        
