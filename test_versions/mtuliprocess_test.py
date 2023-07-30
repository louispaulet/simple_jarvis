import multiprocessing
import time

def count_to_ten(shared_queue):
    for i in range(1, 11):
        print(f'Counting : {i}')
        shared_queue.put(i)
        time.sleep(0.1)

def print_numbers(shared_queue):
    while True:
        if not shared_queue.empty():
            number = shared_queue.get()
            time.sleep(0.5)
            print(f"Reading: {number}")
        else:
            print('empty queue')
            time.sleep(0.1)
            
            if shared_queue.empty():
                break

if __name__ == '__main__':
    manager = multiprocessing.Manager()
    shared_queue = manager.Queue()

    process1 = multiprocessing.Process(target=count_to_ten, args=(shared_queue,))
    process2 = multiprocessing.Process(target=print_numbers, args=(shared_queue,))
    
    process1.start()
    process2.start()
    
    process1.join()
    process2.join()
