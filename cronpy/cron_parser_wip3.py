import logging
from itertools import product
from datetime import datetime
from dateutil.relativedelta import relativedelta

from cronpy.datetime_utils import get_utc_now
from cronpy.datetime_utils import date_to_time
from cronpy.datetime_utils import string_to_date
from cronpy.datetime_utils import get_n_days_of_month

logger = logging.getLogger(__name__)

MINUTE, HOUR, DAY, MONTH, YEAR = 0, 1, 2, 3, 4
YEAR_MONTH_TO_NDAYS = {
    (yy, mm): get_n_days_of_month(yy, mm) for yy, mm in product(range(2000, 2100), range(1, 13))
}


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
        self.now = now or get_utc_now()
        self.cron = cron
        self.sign = 1
        parts = cron.split(' ')
        self.minute = parts[0]
        self.hour = parts[1]
        self.dom = parts[2]
        self.month = parts[3]
        self.dow = parts[4]
        target = parts[5] if len(parts) >= 6 else 'D-0'
        self.granularity = {'D': 'daily', 'W': 'weekly', 'M': 'monthly'}[target[0]]
        delta_granularity = {'D': 'days', 'W': 'weeks', 'M': 'months'}[target[0]]
        self.delta_n_periods = int(target[1:])
        self.date_delta = relativedelta(**{delta_granularity: self.delta_n_periods})
        # Set Smallest Attempt
        if any([x in self.minute for x in ('*', '/', ',', '-')]):
            self.step = relativedelta(minutes=1)
        elif any([x in self.hour for x in ('*', '/', ',', '-')]):
            self.step = relativedelta(hours=1)
        elif any([x in self.dom for x in ('*', '/', ',', '-')]):
            self.step = relativedelta(days=1)
        elif any([x in self.month for x in ('*', '/', ',', '-')]):
            self.step = relativedelta(months=1)
        elif any([x in self.month for x in ('*', '/', ',', '-')]):
            self.step = relativedelta(months=1)
        elif any([x in self.dow for x in ('*', '/', ',', '-')]):
            self.step = relativedelta(weeks=1)
        elif any([x in self.dow for x in ('#',)]):
            self.step = relativedelta(months=1)
        else:
            self.step = relativedelta(minutes=1)

    @property
    def minute_options(self):
        if getattr(self, '_minute_options', None):
            return self._minute_options
        self._minute_options = []
        return self._minute_options

    @property
    def hour_options(self):
        if getattr(self, '_hour_options', None):
            return self._hour_options
        self._hour_options = []
        return self._hour_options

    @property
    def month_options(self):
        if getattr(self, '_month_options', None):
            return self._month_options
        self._month_options = []
        return self._month_options

    @property
    def year_options(self):
        return range(self.now.year, 2100 if self.sign > 0 else 2000, self.sign)

    @property
    def day_options(self):
        options = []
        return options

    def _is_matched(self, dt: datetime):
        print('Given:', dt)
        # sign = 1 if self.forward else -1
        if all([
            self.sign * (dt - self.now).total_seconds() > 0,
            dt.year in self.year_options,
            dt.month in self.month_options,
            dt.hour in self.hour_options,
            dt.minute in self.minute_options,
            # Special on Day==>
            dt.day in self.day_options,
        ]):
            print('\t^^ MATCHED')
            self.now = dt
            return True
        return False

    def next_schedule(self) -> datetime:
        self.sign = 1
        while self.now.year < 2100:
            if self._is_now_matched():
                return self.now
            self.now += self.step

    def prev_schedule(self) -> datetime:
        self.sign = -1
        while 2000 < self.now.year:
            if self._is_now_matched():
                return self.now
            self.now -= self.step

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
    result = Cronpy('0 3 * * 2#1 M-1', now=now).next_schedule()
    assert '2022-09-06 03:00:00' == date_to_time(result)
    # sla = c.get_sla_by_metric_date('2022-08-10')
    # print('SLA:', sla)
    # for t in c.prev_schedule():
    #     print(t)


if __name__ == '__main__':
    main()
