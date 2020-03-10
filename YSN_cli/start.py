import os
import threading

def run(self):
    if self.settings_files != None:
        for settingsfile in self.settings_files:
            settings = self.create_check_settingsFile(settingsfile)
            newThread(settings)
            #process_Obj=sync.Process(settings)
            #process_Obj.main_loop()
        
    if self.cron:
        for process in threading.enumerate():
            process.running = False
        self.running = False
    else: self.running = True

    while self.running:
        #if not logger.isEnabledFor(logging.DEBUG):
        os.system('cls' if os.name == 'nt' else 'clear')
        ynab_requests = 0
        print('Running threads:')
        #-+-#for i in threading.enumerate():
            #-+-#print(str(i)+" | "+i.settings['name'])
            #-+-#ynab_requests += i.ynabAPI.requestCounter
        print('Total YNAB Requests: '+str(ynab_requests))
        print('---------------')

        print('n | New (thread) process with another setting')
        print('q | Quit the Program.')
        user_input = input('Choose an option: ')
        if user_input == 'q': # Quit
            for process in threading.enumerate():
                process.run = False
            self.running = False
        elif user_input == 'n': # New process with different settings
            settingsfile = input('Filename for settingsfile. (Created if not found): ')
            settings = self.settingsfile.create_or_check(self,settingsfile)
            newThread(settings)
        # Selecting process
        elif user_input.isdigit() and int(user_input) in range(threading.activeCount()):
            process = threading.enumerate()[int(user_input)]
            self.processEditor(process)
    
    """ self.thread_objects = []
    threads = {}
    def newThread(settings):
        process_Obj = sync.Process(settings)
        thread_objects.append(process_Obj)
        process_thread = threading.Thread(target=process_Obj.run)
        threads[settings['name']] = process_thread
        process_thread.start()
    def stopThread(process_Obj):
        process_Obj.run = False
        del threads[process_Obj.settings['name']]
        thread_objects.remove(process_Obj)


    if settings_files != None:
        for settingsFile in settings_files:
            settings = create_check_settingsFile(settingsFile)
            newThread(settings)
            #process_Obj=sync.Process(settings)
            #process_Obj.main_loop()

    running = True
    if self.cron:
        for process in thread_objects:
            process.run = False
        running = False
    while running:
        if not logger.isEnabledFor(logging.DEBUG):
            os.system('cls' if os.name == 'nt' else 'clear')
        ynab_requests = 0
        print('Running threads:')
        for i in range(len(thread_objects)):
            print(str(i)+" | "+thread_objects[i].settings['name'])
            ynab_requests += thread_objects[i].ynabAPI.requestCounter
        print('Total YNAB Requests: '+str(ynab_requests))
        print('---------------')

        print('n | New (thread) process with another setting')
        print('q | Quit the Program.')
        user_input = input('Choose an option: ')
        if user_input == 'q': # Quit
            for process in thread_objects:
                process.run = False
            running = False
        elif user_input == 'n': # New process with different settings
            settingsFile = input('Filename for settingsfile. (Created if not found): ')
            settings = create_check_settingsFile(settingsFile)
            newThread(settings)
        # Selecting process
        elif user_input.isdigit() and int(user_input) in range(len(thread_objects)):
            process = thread_objects[int(user_input)]
            processEditor(process) """