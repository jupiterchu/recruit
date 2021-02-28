from celery import Celery
"""
backend：每个异步的任务存储在什么地方，
broker：存储任务系统的代理
"""
app = Celery('tasks', backend='redis://127.0.0.1',broker='redis://127.0.0.1')

@app.task
def add(x, y):
    return x + y