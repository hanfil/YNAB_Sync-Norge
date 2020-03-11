from YSN_base import sync

def newthread(self, settings):
    process_obj = sync.Process(settings)
    self.thread_objects.append(process_obj)
    process_obj.start()

def stopthread(self, process_obj):
    process_obj.running = False
    self.thread_objects.remove(process_obj)