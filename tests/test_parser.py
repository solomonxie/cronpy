from datetime import datetime

from cronpy import Cronpy
from cronpy.datetime_utils import date_to_time


def test_cron_next_schedule():
    now = datetime(2022, 8, 10, 5, 0, 0)
    # Every day's 3 am:
    c = Cronpy('0 3 * * *', now)
    assert '2022-08-11 03:00:00' == date_to_time(c.next_schedule())
    assert '2022-08-12 03:00:00' == date_to_time(c.next_schedule())
    # 3 am of every 10th of the month:
    c = Cronpy('0 3 10 * *', now)
    assert '2022-09-10 03:00:00' == date_to_time(c.next_schedule())
    # 3 am of every 1st Tuesday of the month
    c = Cronpy('0 3 * * 2#1', now)
    assert '2022-09-06 03:00:00' == date_to_time(c.next_schedule())
    # 3 am of every Tuesday
    c = Cronpy('0 3 * * 2', now)
    assert '2022-08-16 03:00:00' == date_to_time(c.next_schedule())
    # 3 am of every 4 days
    c = Cronpy('0 3 */4 * *', now)
    assert '2022-08-12 03:00:00' == date_to_time(c.next_schedule())
    # 3 am of every 7 days
    c = Cronpy('0 3 */7 * *', now)
    assert '2022-08-14 03:00:00' == date_to_time(c.next_schedule())
    # 3 am of every 11th, 13th and 20th of the month
    c = Cronpy('0 3 11,13,20 * *', now)
    assert '2022-08-11 03:00:00' == date_to_time(c.next_schedule())
    assert '2022-08-13 03:00:00' == date_to_time(c.next_schedule())
    assert '2022-08-20 03:00:00' == date_to_time(c.next_schedule())
    assert '2022-09-11 03:00:00' == date_to_time(c.next_schedule())
    # 3 am of every day between 20th to 22th of the month
    c = Cronpy('0 3 20-22 * *', now)
    assert '2022-08-20 03:00:00' == date_to_time(c.next_schedule())
    assert '2022-08-21 03:00:00' == date_to_time(c.next_schedule())
    assert '2022-08-22 03:00:00' == date_to_time(c.next_schedule())
    assert '2022-09-20 03:00:00' == date_to_time(c.next_schedule())
    # Every minute of 3 am every day
    c = Cronpy('* 3 * * *', now)
    assert '2022-08-11 03:00:00' == date_to_time(c.next_schedule())


def test_cron_prev_schedule():
    now = datetime(2022, 8, 10, 5, 0, 0)
    # ==>PREVIEWS SCHEDULE
    c = Cronpy('0 3 * * *', now)
    assert '2022-08-09 03:00:00' == date_to_time(c.prev_schedule())
    assert '2022-08-08 03:00:00' == date_to_time(c.prev_schedule())
    result = Cronpy('0 3 10 * *', now).prev_schedule()
    assert '2022-07-10 03:00:00' == date_to_time(result)
    result = Cronpy('0 3 * * 2#1', now).prev_schedule()
    assert '2022-08-02 03:00:00' == date_to_time(result)
    result = Cronpy('0 3 * * 2', now).prev_schedule()
    assert '2022-08-09 03:00:00' == date_to_time(result)
    result = Cronpy('0 3 */2 * *', now).prev_schedule()
    assert '2022-08-10 03:00:00' == date_to_time(result)
    result = Cronpy('0 3 */3 * *', now).prev_schedule()
    assert '2022-08-09 03:00:00' == date_to_time(result)
    result = Cronpy('0 3 */4 * *', now).prev_schedule()
    assert '2022-08-08 03:00:00' == date_to_time(result)
    result = Cronpy('* 3 * * *', now).prev_schedule()
    assert '2022-08-09 03:59:00' == date_to_time(result)


def test_cron_get_sla_by_metric_date():
    c = Cronpy('0 15 * * *')
    assert '2021-08-12 15:00:00' == date_to_time(c.get_sla_by_metric_date('2021-08-10'))
    c = Cronpy('0 3 10 * *')
    assert '2022-09-10 03:00:00' == date_to_time(c.get_sla_by_metric_date('2022-08-10'))
    c = Cronpy('0 3 * * 2#1')
    assert '2022-09-06 03:00:00' == date_to_time(c.get_sla_by_metric_date('2022-08-10'))
    c = Cronpy('0 3 * * 2')
    assert '2022-08-16 03:00:00' == date_to_time(c.get_sla_by_metric_date('2022-08-10'))
    c = Cronpy('0 3 */2 * *')
    assert '2022-08-12 03:00:00' == date_to_time(c.get_sla_by_metric_date('2022-08-10'))
    # FIXME ==>
    c = Cronpy('* 3 * * *')
    assert '2022-08-12 03:00:00' == date_to_time(c.get_sla_by_metric_date('2022-08-10'))
