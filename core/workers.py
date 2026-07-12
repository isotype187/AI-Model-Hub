import threading
import queue

MAX_WORKERS = 2
task_queue = queue.Queue()
active = []


def worker(callback=None):
    while True:
        task = task_queue.get()

        if task is None:
            break

        model, func = task

        try:
            func(model, callback)
        except Exception as e:
            if callback:
                callback(f'Worker error: {e}')

        task_queue.task_done()


def start_pool(callback=None):
    for _ in range(MAX_WORKERS):
        t = threading.Thread(target=worker, args=(callback,), daemon=True)
        t.start()
        active.append(t)


def add_task(model, func, callback=None):
    task_queue.put((model, func))
    start_pool(callback)
