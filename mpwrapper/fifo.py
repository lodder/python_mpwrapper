from collections import deque


class FiFoQueue():
    def __init__(self):
        self.queue = deque()

    def push(self, item):
        self.queue.append(item)

    def push_multiple(self, items):
        self.queue.extend(items)

    def pop(self):
        if self.len() == 0:
            return EmptyQueueObj()
        else:
            item = self.queue.popleft()
        return item

    def pop_all(self):
        lst = list(self.queue)
        self.queue.clear()
        return lst

    def is_empty(self):
        return self.len() == 0

    def len(self):
        return self.queue.__len__()


class EmptyQueueObj(object):
    pass
