import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

from cronpy.datetime_utils import is_int
from cronpy.datetime_utils import get_utc_now
from cronpy.datetime_utils import date_to_time
from cronpy.datetime_utils import string_to_date
from cronpy.datetime_utils import get_dom_by_nth_weekday

logger = logging.getLogger(__name__)

MINUTE, HOUR, DAY, MONTH, YEAR = 0, 1, 2, 3, 4


class Cronpy:
    def __init__(self, cron: str, now: datetime = None):
        """ Cron Expression:
        Minute; Hour; Day(of month); Month; Day(of week)
        0 3 * * * D-2 ==> 3AM everyday
        0 3 * * 2 W-1 ==> 3AM on every Tuesday
        0 3 10 * * M-1 ==> 3AM on every month's 10th
        0 3 * * 2#1 M-1 ==> 3AM on every month's first Tuesday
        0 3 */2 * * D-2 ==> 3AM on Every 2 days
        * 3 * * * D-2 ==> Every minute of 3AM every day
        """
        parts = cron.split(' ')
        self.minute = parts[0]
        self.hour = parts[1]
        self.day_of_month = parts[2]
        self.month = parts[3]
        self.day_of_week = parts[4]
        target = parts[5] if len(parts) >= 6 else 'D-0'
        self.granularity = {'D': 'daily', 'W': 'weekly', 'M': 'monthly'}[target[0]]
        delta_granularity = {'D': 'days', 'W': 'weeks', 'M': 'months'}[target[0]]
        self.delta_n_periods = int(target[1:])
        self.date_delta = relativedelta(**{delta_granularity: self.delta_n_periods})
        self.cron = cron
        self.now = now or get_utc_now()

    def _get_delta(self, forward: bool):
        step = 1 if forward else -1
        delta = relativedelta()
        fixed = relativedelta()
        __import__('pudb').set_trace()
        # REGULAR PRIORITY: MONTH < DOM < HOUR < MINUTE
        if self.month == '*':
            delta = relativedelta(months=step)
        if self.day_of_month == '*':
            delta = relativedelta(days=step)
        if self.hour == '*':
            delta = relativedelta(hours=step)
        if self.minute == '*':
            delta = relativedelta(minutes=step)
        __import__('pudb').set_trace()
        # FAST-FORWARD PRIORITY: MINUTE < HOUR < DOM < MONTH
        if is_int(self.minute):
            fixed += relativedelta(minute=int(self.minute), minutes=0)
            if self.now.minute >= int(self.minute) and forward:
                delta = relativedelta(hours=step)
            elif self.now.minute <= int(self.minute) and not forward:
                delta = relativedelta(days=step)
        if is_int(self.hour):
            fixed += relativedelta(hour=int(self.hour), hours=0)
            if self.now.hour >= int(self.hour) and forward:
                delta = relativedelta(days=step)
            elif self.now.hour <= int(self.hour) and not forward:
                delta = relativedelta(days=step)
        if is_int(self.day_of_month):
            fixed += relativedelta(day=int(self.day_of_month), days=0)
            if self.now.day >= int(self.day_of_month) and forward:
                delta = relativedelta(months=step)
            elif self.now.day <= int(self.day_of_month) and not forward:
                delta = relativedelta(months=step)
        elif self.day_of_month.startswith('*/'):
            period = int(self.day_of_month[2:])
            if forward:
                mod = period - self.now.day % period
            else:
                mod = self.now.day % period
            delta = relativedelta(days=step * mod)
        if is_int(self.month):
            fixed += relativedelta(month=int(self.month), months=0)
            if self.now.month >= int(self.month) and forward:
                delta = relativedelta(years=step)
            elif self.now.month <= int(self.month) and not forward:
                delta = relativedelta(years=step)
        delta += fixed
        return delta

    def _match_schedule(self, forward: bool = True):
        # MOVING AND MATCHING
        while 1999 < self.now.year < 2099:
            self.now += self._get_delta(forward)
            # print(self.now)
            if is_int(self.day_of_week) and self.now.isoweekday() != int(self.day_of_week):
                continue
            elif '#' in self.day_of_week:
                weekday = int(self.day_of_week[:self.day_of_week.index('#')])
                nth = int(self.day_of_week[self.day_of_week.index('#')+1:])
                if self.now.day != get_dom_by_nth_weekday(self.now.year, self.now.month, weekday, nth):
                    continue
            # print('matched:', self.now)
            return self.now

    def next_schedule(self):
        return self._match_schedule(forward=True)

    def prev_schedule(self):
        return self._match_schedule(forward=False)

    def get_sla_by_metric_date(self, metric_date: str):
        self.now = string_to_date(metric_date)
        schedule_gen = self.next_schedule()
        sla = None
        for i in range(abs(self.delta_n_periods)):
            sla = next(schedule_gen)
            # print(sla)
        return sla


def main():
    now = datetime(2022, 8, 10, 5, 0, 0)
    result = Cronpy('0 3 * * * D-2', now=now).next_schedule()
    assert '2022-08-11 03:00:00' == date_to_time(result)
    # sla = c.get_sla_by_metric_date('2022-08-10')
    # print('SLA:', sla)
    # for t in c.prev_schedule():
    #     print(t)


if __name__ == '__main__':
    main()
