import queue
import threading
import time
from core.installer import install_model
from core.logs import write_log

install_queue = queue.Queue()
running = False
cancel_flag = False


def worker(callback=None):
    global running, cancel_flag
    running = True

    while True:
        model = install_queue.get()

        if model is None:
            break

        if cancel_flag:
            write_log('Queue cancelled before install')
            if callback:
                callback('Cancelled')
            install_queue.task_done()
            continue

        stages = ['Preparing', 'Downloading', 'Installing', 'Finalizing']

        for s in stages:
            if cancel_flag:
                break

            msg = f'{s}: {model["name"]}'
            write_log(msg)

            if callback:
                callback(msg)

            time.sleep(0.5)

        install_model(model, callback)

        write_log(f'Completed: {model["name"]}')

        install_queue.task_done()

    running = False


def start_worker(callback=None):
    global running
    if not running:
        t = threading.Thread(target=worker, args=(callback,), daemon=True)
        t.start()


def add_to_queue(model, callback=None):
    install_queue.put(model)
    start_worker(callback)


def cancel_all(callback=None):
    global cancel_flag
    cancel_flag = True

    write_log('Cancel requested')

    if callback:
        callback('Cancelling queue...')
