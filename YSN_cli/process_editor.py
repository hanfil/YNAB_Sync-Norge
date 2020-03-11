import os
import logging

def process_editor(self, process):
    in_editor = True
    while in_editor:
        if not self.logger.isEnabledFor(logging.DEBUG):
            os.system('cls' if os.name == 'nt' else 'clear')
        print('Current wait time: '+str(int(process.waitTime/60))+'minutes.')
        print('Looking '+str(process.daysBack)+' days back to check for transactions.')
        print('Used '+str(process.ynabAPI.requestCounter)+' YNAB requests.')
        print('---------------')
        print('d | Change how many (d)ays back it look for transactions.')
        print('t | Change wait (t)ime between transaction sync.')
        print('l | Link accounts.')
        print('s | Save settings.')
        print('k | Kill process.')
        print('b | Back to menu.')
        user_input = input('Choose an option: ')
        if user_input == 'b': # Back
            in_editor = False
        elif user_input == 'k': # kill
            self.thread_controller.stopthread(self, process)
            in_editor = False
        elif user_input == 'd': # daysBack
            process.daysBack = int(input('How many days back? : '))
        elif user_input == 't': # waitTime
            process.waitTime = int(input('How many minutes between syncs? : '))*60
        elif user_input == 'l': # waitTime
            process.settings = self.settingsfile.link_accounts(process.settings)
        elif user_input == 's': # save
            settingsfile = input('Filename for settingsfile. (Created if not found): ') + ".YNAB.json"
            settings = process.settings
            settings['wait_time'] = process.waitTime
            settings['days_back'] = process.daysBack
            self.settingsfile.update_settings(self, settings, settingsfile)