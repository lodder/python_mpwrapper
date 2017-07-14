from __future__ import print_function
import sys, time
import threading
import numpy as np


class ProgressFn():
    def __init__(self, logger_name='', update_interval=1):
        import logging
        self.logger = logging.getLogger(logger_name)
        self.update_interval = update_interval
        self.execution_tracker = dict(errors=0)
        self.print_progress_loop = False
        self.start_time = time.time()

    def progress(self, percent, completed, errors):
        elapsed_time = time.time() - self.start_time
        change = not 'completed' in self.execution_tracker or \
                 self.execution_tracker['completed'] != completed or \
                 self.execution_tracker['errors'] != errors or \
                 elapsed_time < 60
        if change:
            est_remaining = (100 * (elapsed_time / percent) - elapsed_time) if percent > 0  else 0
            est_remaining_str = \
                ('%.0fs' % est_remaining) if est_remaining < 60 \
                    else ('%.1f min' % (est_remaining / 60.0)) if est_remaining < 60 * 60 \
                    else ('%.1fh' % (est_remaining / (60 * 60.0)))
            elapsed_str = \
                ('%.0fs' % elapsed_time) if elapsed_time < 60 \
                    else ('%.1f min' % (elapsed_time / 60.0)) if elapsed_time < 60 * 60 \
                    else ('%.1fh' % (np.ceil(elapsed_time / (60 * 60.0))))

            self.execution_tracker['completed'] = completed
            self.execution_tracker['errors'] = errors
            self.execution_tracker['last_progress'] = '{0: <100}'.format(
                ('%.1f%% | %d completed | %d errors | %s elapsed | %s remaining' %
                 (percent, completed, errors, elapsed_str, est_remaining_str))
            ) + '\r'
            sys.stdout.write(self.execution_tracker['last_progress'])
            sys.stdout.flush()

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
