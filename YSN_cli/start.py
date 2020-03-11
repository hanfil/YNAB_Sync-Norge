import os
import time
import threading
import logging

def start(self):

    if self.settings_files != None:
        for settingsfile in self.settings_files:
            settings = self.settingsfile.create_or_check(self, settingsfile)
            self.thread_controller.newthread(self, settings)
        
    if self.cron:
        time.sleep(0.1)
        for process in self.thread_objects:
            process.running = False
        self.running = False
        message = "Processes are still running"
        msg_count = ""
        while threading.activeCount() > 1:
            if not self.logger.isEnabledFor(logging.DEBUG):
                os.system('cls' if os.name == 'nt' else 'clear')
            if len(msg_count) > 20:
                msg_count = ""
            msg_count += "."
            print("%s%s" % (message, msg_count))
            time.sleep(1)
        print("Done!")
    else: self.running = True


    while self.running:
        if not self.logger.isEnabledFor(logging.DEBUG):
            os.system('cls' if os.name == 'nt' else 'clear')
        ynab_requests = 0
        print('Running threads: %s' % str(threading.activeCount()-1))
        for i in range(len(self.thread_objects)):
            print(str(i)+" | %s - Running=%s" % (self.thread_objects[i].settings['name'], self.thread_objects[i].running))
            ynab_requests += self.thread_objects[i].ynabAPI.requestCounter
        print('Total YNAB Requests: %s/200 per hour' % str(ynab_requests))
        print('---------------')
        print('n | New process with new settings.')
        print('q | Quit the Program.')
        user_input = input('Choose an option: ')
        if user_input == 'q': # Quit
            for process in self.thread_objects:
                process.running = False
            self.running = False
        elif user_input == 'n': # New process with different settings
            settingsfile = input('Filename for settingsfile. (Created if not found): ') + ".YNAB.json"
            settings = self.settingsfile.create_or_check(self,settingsfile)
            self.thread_controller.newthread(self, settings)
        # Selecting process
        elif user_input.isdigit() and int(user_input) in range(len(self.thread_objects)):
            process = self.thread_objects[int(user_input)]
            self.process_editor(process)
