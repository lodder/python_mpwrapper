from __future__ import print_function
import sys, re
import threading


class ProgressFn():
    def __init__(self, logger_name='', update_interval=1):
        import logging
        self.logger = logging.getLogger(logger_name)
        self.update_interval = update_interval
        self.execution_tracker = dict(errors=0)
        self.print_progress_loop = False
        self.last_text = ''

    def progress(self, percent, completed, errors):
        change = not 'completed' in self.execution_tracker or \
                 self.execution_tracker['completed'] != completed or \
                 self.execution_tracker['errors'] != errors
        if change:
            self.execution_tracker['completed'] = completed
            self.execution_tracker['errors'] = errors
            self.execution_tracker['last_progress'] = ('%100s' % '\r%.1f%% | %d completed | %d errors' % (percent, completed, errors))
            print(self.execution_tracker['last_progress'], end='\r')

    def start_print_progress(self):
        self.print_progress_loop = True
        self.print_progress()

    def stop_print_progress(self):
        self.print_progress_loop = False
        sys.stdout.write('\n')
        sys.stdout.flush()

    def print_progress(self):
        if self.print_progress_loop:
            threading.Timer(self.update_interval, self.print_progress).start()
        if self.execution_tracker is not None and 'last_progress' in self.execution_tracker:
            sys.stdout.write(self.execution_tracker['last_progress'])
            sys.stdout.flush()
