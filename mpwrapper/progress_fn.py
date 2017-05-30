from __future__ import print_function
import sys, time
import threading


class ProgressFn():
    def __init__(self, logger_name='', update_interval=1):
        import logging
        self.logger = logging.getLogger(logger_name)
        self.update_interval = update_interval
        self.execution_tracker = dict(errors=0)
        self.print_progress_loop = False
        self.start_time = time.time()

    def progress(self, percent, completed, errors):
        change = not 'completed' in self.execution_tracker or \
                 self.execution_tracker['completed'] != completed or \
                 self.execution_tracker['errors'] != errors
        if change:
            elapsed_time = time.time() - self.start_time
            est_remaining = (100 * (elapsed_time / percent) - elapsed_time) if percent > 0  else 0
            self.execution_tracker['completed'] = completed
            self.execution_tracker['errors'] = errors
            self.execution_tracker['last_progress'] = \
                ('%100s' % '\r%.1f%% | %d completed | %d errors | %.0f min elapsed | %.0f min remaining' %
                 (percent, completed, errors, elapsed_time / 60, est_remaining / 60))
            print(self.execution_tracker['last_progress'], end='\r')

    def start_print_progress(self):
        self.start_time = time.time()
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
