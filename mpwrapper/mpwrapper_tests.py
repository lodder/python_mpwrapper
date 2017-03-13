import numpy as np
from .mpwrapper import MpWrapper
import unittest, sys


class test_execution(unittest.TestCase):
    def setUp(self):
        super(test_execution, self).setUp()

    def test_execution(self):
        # set up
        task_list = list()
        n_items = 10000
        for i in range(0, n_items):
            # add task: all input params are stored in a dictionary
            task_list.append({'value1': i, 'value2': i + 1})
        task_list[5]['value1'] = np.NaN  # let one fail

        # a function representing some type of work
        def execute_task(task):
            if np.isnan(task['value1']):
                raise Exception('Let this one fail..')
            else:
                return task['value1'] * task['value2']

        # optional: a progress function used to give feedback
        def progress(percent, completed, errors):
            pass
            # sys.stdout.write('%.1f%% \t%d completed\t%d errors\r' % (percent, completed, errors))
            # sys.stdout.flush()

        # action
        test_excecutor = MpWrapper()
        results = test_excecutor.run(task_list, execute_task, progress)

        # validate
        expected_result = np.sum([execute_task(task) for task in task_list if np.isfinite(task['value1'])])
        self.assertEqual(n_items - 1, len(results))
        self.assertEqual(np.sum(results), expected_result)

    def test_if_mp(self):
        # set up
        n_items = 1000
        task_list = [{'value1': i} for i in range(0, n_items)]

        def execute_task(task):
            return task['value1']

        # action
        excecutor = MpWrapper(multithreaded_if_possible=True)
        results = excecutor.run(task_list, execute_task)

        # validate
        if sys.platform != 'win32':
            # validate by making sure the items were not all returned in the same sequence
            self.assertTrue(np.any(np.abs(np.array(results) - np.array(range(0, n_items))) != 0))

    def test_single_threaded(self):
        # set up
        n_items = 30
        task_list = [{'value1': i} for i in range(0, n_items)]

        def execute_task(task):
            return task['value1']

        # action
        excecutor = MpWrapper(multithreaded_if_possible=False)
        results = excecutor.run(task_list, execute_task)

        # validate by checking that the tasks ran in the same sequence that they were added to the task list
        for i in range(0, n_items):
            self.assertEqual(task_list[i]['value1'], results[i])
