import datetime
import schedule
import time

from cron_utils import is_valid_cron, check_cron_condition
from data_fetching import list_cron_jobs

MINUTE_GRANULARITY = 1


def sample_task():
    print("This task is an example for implementation of task functions.")
    return


def run_task(task_ref):
    if task_ref == "sample":
        sample_task()


def job():
    end_time = datetime.datetime.now().replace(second=0, microsecond=0)
    start_time = end_time - datetime.timedelta(minutes=MINUTE_GRANULARITY-1)
    cron_list = list_cron_jobs()
    for cron in cron_list:
        if not is_valid_cron(cron['cron_expression']):
            continue
        if check_cron_condition(cron['cron_expression'], start_time, end_time):
            run_task(cron['task_ref'])


if __name__ == "__main__":
    schedule.every(MINUTE_GRANULARITY).minute.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)
