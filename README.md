# Python Multiprocessing Wrapper

A simple wrapper written to make the use of Python multiprocessing easy to use.

## Example usage:

```python

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
    sys.stdout.write('%.1f%% \t%d completed\t%d errors\r' % (percent, completed, errors))
    sys.stdout.flush()

# action
results = MpWrapper().run(task_list, execute_task, progress)

# alternatively to above (will print progress to console)
results = MpWrapper().run_with_progress(task_list, execute_task)

```

## Optional parameters

*multithreaded_if_possible*=True
*n_threads*=None

**Using 'n_threads=None' will set the number of threads to cpu_count()*