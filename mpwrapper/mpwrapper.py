import sys, time, logging
import multiprocessing as mp
from fifo import FiFoQueue, EmptyQueueObj
from multiprocessing.managers import BaseManager


# -----------------------------------------------------------
# Default Executor class
# -----------------------------------------------------------

class MpWrapper(object):
    def __init__(self, multithreaded_if_possible=True, n_threads=None):
        self.n_threads = n_threads

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

        # only run multithreaded if we can
        start_time = time.time()
        if self.run_multithreaded:
            if self.n_threads is None:
                self.n_threads = mp.cpu_count()
            nodes = [WorkerNode(request_queue, result_queue, tracker, execute_fn) for i in range(0, self.n_threads)]
            for node in nodes:
                node.start()
        else:
            nodes = [WorkerNode(request_queue, result_queue, tracker, execute_fn)]
            nodes[0].run()  # execution will be done on the same thread (note we call run() here and not start())
        self.elapsed_time = time.time() - start_time

        # wait for all execution nodes to finish
        while not request_queue.is_empty() or any([node.is_alive() for node in nodes]):
            if progress_fn is not None:
                success = tracker.get_success()
                errors, _ = tracker.get_errors()
                progress = 0 if n_tasks == 0 else 100.0 * (success + errors) / n_tasks
                progress_fn(progress, success, errors)
            time.sleep(0.1)

        # read all outputs into a list
        lst_outputs = result_queue.pop_all()

        # log execution results and return output
        return lst_outputs

    def validate_tasks(self, tasks_list):
        for task in tasks_list:
            if type(task) is not dict:
                raise Exception('All tasks have to be in a dictionary format, eg. {id:1, path:\'filepath1\', user:\'x1\'}')


# -----------------------------------------------------------
# Worker node/class: Depending on if multiprocessing is chosen,
# will run on same or multile new threads
# -----------------------------------------------------------
class WorkerNode(mp.Process):
    def __init__(self, req_queue, result_queue, tracker, execute_fn):
        super(WorkerNode, self).__init__()
        self.req_queue = req_queue
        self.result_queue = result_queue
        self.tracker = tracker
        self.execute_fn = execute_fn

    def run(self):
        # run until the queue is empty or termination signal sent
        while not self.tracker.should_terminate():
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
