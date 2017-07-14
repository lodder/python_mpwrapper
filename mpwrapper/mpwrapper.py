import sys, time, logging
import multiprocessing as mp
from .fifo import FiFoQueue, EmptyQueueObj
from multiprocessing.managers import BaseManager


# -----------------------------------------------------------
# Default Executor class
# -----------------------------------------------------------

class MpWrapper(object):
    def __init__(self, multithreaded_if_possible=True, n_threads=None, recycle_proc_after=0, raise_on_error_types=[]):
        self.n_threads = n_threads
        self.recycle_proc_after = recycle_proc_after
        self.raise_on_error_types = raise_on_error_types

        # for now, only support multithreading on non-windows machines
        python_version = sys.version_info  # 2.7.11 >
        self.run_multithreaded = multithreaded_if_possible and (sys.platform != 'win32') and not python_version == (2, 7, 10)

    # ----------------------------------------
    # Run this function to kick off execution
    # ----------------------------------------
    def run(self, tasks_list, execute_fn, progress_fn=None):
        '''
        :param tasks_list: should be a list of dictionaries containing the input parameters for each individual function call.
             Eg. [{id:1, path:'filepath1', user:'x1'},
                  {id:2, path:'filepath2', user:'x2'},
                  {id:3, path:'filepath3', user:'x3'}
                ]
        :param execute_fn: This should be a function that runs the desired execution for a single task in the 'tasks_list'
        :param progress_fn: An optional function that can be used to get feedback on the progress of execution
        '''

        # make sure the tasks are in the correct format
        self.validate_tasks(tasks_list)
        n_tasks = len(tasks_list)

        def submit_progress():
            if progress_fn is not None:
                success = tracker.get_success()
                errors, _ = tracker.get_errors()
                progress = 0 if n_tasks == 0 else 100.0 * (success + errors) / n_tasks
                progress_fn(progress, success, errors)

        # only run multithreaded if we can
        start_time = time.time()
        if self.run_multithreaded:
            # create input and output queues
            try:
                BaseManager.register('FiFoQueue', FiFoQueue)
                BaseManager.register('ExcecutionTracker', ExcecutionTracker)
                manager = BaseManager()
                manager.start()
                request_queue = manager.FiFoQueue()
                result_queue = manager.FiFoQueue()
                tracker = manager.ExcecutionTracker()
            except:
                logging.error('Unable to start BaseManager. \n'
                              'This is most likely due to an \'if __name__ == \'__main__\':\''
                              ' statement not being present in your main executing script.\n'
                              'See https://healthq.atlassian.net/browse/DMH-212?focusedCommentId=25606&page=com.atlassian.jira.plugin.system.issuetabpanels%3Acomment-tabpanel#comment-25606'
                              ' http://stackoverflow.com/a/18205006 for more details')
                raise

            # fill input queue with tasks
            request_queue.push_multiple(tasks_list)

            if self.n_threads is None:
                self.n_threads = mp.cpu_count()
            nodes = list()

            # wait for all execution nodes to finish
            while not request_queue.is_empty() or any([node.is_alive() for node in nodes]):
                exception_raised = len([node for node in nodes if not node.is_alive() and node.exitcode != 0]) > 0
                if exception_raised:
                    raise Exception('Exception while executing. Please see logs for more details.')

                nodes = [node for node in nodes if node.is_alive()]
                while len(nodes) < self.n_threads:
                    node = WorkerNode(request_queue, result_queue, tracker, execute_fn, self.recycle_proc_after, self.raise_on_error_types)
                    nodes.append(node)
                    node.start()

                submit_progress()
                time.sleep(0.5)
        else:
            request_queue = FiFoQueue()
            result_queue = FiFoQueue()
            tracker = ExcecutionTracker()
            node = WorkerNode(request_queue, result_queue, tracker, execute_fn, recycle_proc_after=0, raise_on_error_types=self.raise_on_error_types)
            for task in tasks_list:
                request_queue.push(task)
                node.run()  # execution will be done on the same thread (note we call run() here and not start())
                submit_progress()

        submit_progress()
        self.elapsed_time = time.time() - start_time

        # read all outputs into a list
        lst_outputs = result_queue.pop_all()

        # log execution results and return output
        return lst_outputs

    def run_with_progress(self, tasks_list, execute_fn):
        from .progress_fn import ProgressFn
        fn = ProgressFn()
        try:
            fn.start_print_progress()
            return self.run(tasks_list=tasks_list, execute_fn=execute_fn, progress_fn=fn.progress)
        except KeyboardInterrupt:
            print '\n###################'
            print 'User cancelled'
            print '###################\n'
            exit(1)
        except:
            raise
        finally:
            fn.stop_print_progress()

    def validate_tasks(self, tasks_list):
        for task in tasks_list:
            if type(task) is not dict:
                raise Exception('All tasks have to be in a dictionary format, eg. {id:1, path:\'filepath1\', user:\'x1\'}')


# -----------------------------------------------------------
# Worker node/class: Depending on if multiprocessing is chosen,
# will run on same or multile new threads
# -----------------------------------------------------------
class WorkerNode(mp.Process):
    def __init__(self, req_queue, result_queue, tracker, execute_fn, recycle_proc_after, raise_on_error_types):
        super(WorkerNode, self).__init__()
        self.req_queue = req_queue
        self.result_queue = result_queue
        self.tracker = tracker
        self.execute_fn = execute_fn
        self.recycle_proc_after = recycle_proc_after
        self.raise_on_error_types = raise_on_error_types
        self.tasks_performed = 0

    def run(self):
        # run until the queue is empty or termination signal sent
        while not self.tracker.should_terminate():
            if self.recycle_proc_after > 0 and self.tasks_performed >= self.recycle_proc_after:
                return

            try:
                item = self.req_queue.pop()
                if type(item) is EmptyQueueObj:
                    break
                output = self.execute_fn(item)
                self.result_queue.push(output)
                self.tracker.increment_success()
            except Exception as e:
                msg = '#Execution error: %s \n params: %s' % (e, item)
                logging.error(msg, exc_info=True)
                self.tracker.increment_error(msg)
                if type(e).__name__ in self.raise_on_error_types:
                    self.tracker.signal_terminate()
                    raise
            except KeyboardInterrupt:
                self.tracker.signal_terminate()
                raise
            finally:
                self.tasks_performed += 1


# -----------------------------------------------------------
# Class to keep track of progress
# -----------------------------------------------------------
class ExcecutionTracker(object):
    def __init__(self):
        self._errors = 0
        self._success = 0
        self.err_list = list()
        self._should_terminate = False

    def increment_success(self):
        self._success += 1

    def increment_error(self, error=None):
        self._errors += 1
        if error is not None:
            self.err_list.append(error)

    def signal_terminate(self):
        self._should_terminate = True

    def should_terminate(self):
        return self._should_terminate

    def get_errors(self):
        return self._errors, self.err_list

    def get_success(self):
        return self._success
