from datetime import datetime

from cronpy.cron_parser_wip1 import Cronpy
from cronpy.datetime_utils import date_to_time


def test_cron():
    now = datetime(2022, 8, 10, 5, 0, 0)
    # ==>NEXT SCHEDULE
    c = Cronpy('0 3 * * * D-2', now)
    assert '2022-08-11 03:00:00' == date_to_time(c.next_schedule())
    assert '2022-08-12 03:00:00' == date_to_time(c.next_schedule())
    result = Cronpy('0 3 10 * * M-1', now).next_schedule()
    assert '2022-09-10 03:00:00' == date_to_time(result)
    result = Cronpy('0 3 * * 2#1 M-1', now).next_schedule()
    assert '2022-09-06 03:00:00' == date_to_time(result)
    result = Cronpy('0 3 * * 2 W-1', now).next_schedule()
    assert '2022-08-16 03:00:00' == date_to_time(result)
    result = Cronpy('0 3 */4 * * D-2', now).next_schedule()
    assert '2022-08-12 03:00:00' == date_to_time(result)
    result = Cronpy('0 3 */7 * * D-2', now).next_schedule()
    assert '2022-08-14 03:00:00' == date_to_time(result)
    result = Cronpy('* 3 * * * D-2', now).next_schedule()
    assert '2022-08-11 03:00:00' == date_to_time(result)
    # ==>PREVIEWS SCHEDULE
    c = Cronpy('0 3 * * * D-2', now)
    assert '2022-08-09 03:00:00' == date_to_time(c.prev_schedule())
    assert '2022-08-08 03:00:00' == date_to_time(c.prev_schedule())
    result = Cronpy('0 3 10 * * M-1', now).prev_schedule()
    assert '2022-07-10 03:00:00' == date_to_time(result)
    result = Cronpy('0 3 * * 2#1 M-1', now).prev_schedule()
    assert '2022-08-02 03:00:00' == date_to_time(result)
    result = Cronpy('0 3 * * 2 W-1', now).prev_schedule()
    assert '2022-08-09 03:00:00' == date_to_time(result)
    result = Cronpy('0 3 */2 * * D-2', now).prev_schedule()
    assert '2022-08-10 03:00:00' == date_to_time(result)
    result = Cronpy('0 3 */3 * * D-2', now).prev_schedule()
    assert '2022-08-09 03:00:00' == date_to_time(result)
    result = Cronpy('0 3 */4 * * D-2', now).prev_schedule()
    assert '2022-08-08 03:00:00' == date_to_time(result)
    result = Cronpy('* 3 * * * D-2', now).prev_schedule()
    assert '2022-08-09 03:59:00' == date_to_time(result)


def test_cron_get_sla_by_metric_date():
    c = Cronpy('0 15 * * * D-2')
    assert '2021-08-12 15:00:00' == date_to_time(c.get_sla_by_metric_date('2021-08-10'))
    c = Cronpy('0 3 10 * * M-1')
    assert '2022-09-10 03:00:00' == date_to_time(c.get_sla_by_metric_date('2022-08-10'))
    c = Cronpy('0 3 * * 2#1 M-1')
    assert '2022-09-06 03:00:00' == date_to_time(c.get_sla_by_metric_date('2022-08-10'))
    c = Cronpy('0 3 * * 2 W-1')
    assert '2022-08-16 03:00:00' == date_to_time(c.get_sla_by_metric_date('2022-08-10'))

    # FIXME ==>
    c = Cronpy('0 3 */2 * * D-2')
    assert '2022-08-12 03:00:00' == date_to_time(c.get_sla_by_metric_date('2022-08-10'))
    # FIXME ==>
    c = Cronpy('* 3 * * * D-2')
    assert '2022-08-12 03:00:00' == date_to_time(c.get_sla_by_metric_date('2022-08-10'))
