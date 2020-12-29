import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1
capture_output = True
errorlog = "-"
