import logging
from itertools import product
from datetime import datetime
from dateutil.relativedelta import relativedelta

from cronpy.datetime_utils import is_int
from cronpy.datetime_utils import get_utc_now
from cronpy.datetime_utils import date_to_time
from cronpy.datetime_utils import string_to_date
from cronpy.datetime_utils import get_n_days_of_month
from cronpy.datetime_utils import get_dom_by_nth_weekday

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
        self.cron = cron
        self.now = now or get_utc_now()
        self.matrix = [[]] * 5
        self.cursors = [0] * len(self.matrix)
        self.current_values = [self.now.minute, self.now.hour, self.now.day, self.now.month, self.now.year]
        self.matrix = [[]] * 5
        # MINUTE:
        if self.minute == '*':
            self.matrix[MINUTE] = range(60)
        elif is_int(self.minute):
            self.matrix[MINUTE] = [int(self.minute)]
        elif self.minute.startswith('*/'):
            mod = int(self.minute[2:])
            self.matrix[MINUTE] = [i for i in range(60) if i % mod == 0]
            assert len(self.matrix[MINUTE]) > 0
        else:
            raise NotImplementedError(f'Minute: {self.minute}')
        # HOUR:
        if self.hour == '*':
            self.matrix[HOUR] = range(24)
        elif is_int(self.hour):
            self.matrix[HOUR] = [int(self.hour)]
        elif self.hour.startswith('*/'):
            mod = int(self.hour[2:])
            self.matrix[HOUR] = [i for i in range(24) if i % mod == 0]
            assert len(self.matrix[HOUR]) > 0
        else:
            raise NotImplementedError(f'Hour: {self.hour}')
        # MONTH:
        if self.month == '*':
            self.matrix[MONTH] = range(1, 13)
        elif is_int(self.month):
            self.matrix[MONTH] = [int(self.month)]
        elif self.month.startswith('*/'):
            mod = int(self.month[2:])
            self.matrix[MONTH] = [i for i in range(1, 13) if i % mod == 0]
            assert len(self.matrix[MONTH]) > 0
        else:
            raise NotImplementedError(f'Month: {self.month}')
        # YEAR:
        self.matrix[YEAR] = range(2000, 2100)

    def _update_options(self, forward: bool = True):
        # Day of Month:
        if self.dom == '*':
            self.matrix[DAY] = range(1, 1 + YEAR_MONTH_TO_NDAYS[(self.now.year, self.now.month)])
        elif is_int(self.dom):
            self.matrix[DAY] = [int(self.dom)]
        elif self.dom.startswith('*/'):
            mod = int(self.dom[2:])
            days = range(1, 1 + YEAR_MONTH_TO_NDAYS[(self.now.year, self.now.month)])
            self.matrix[DAY] = [i for i in days if i % mod == 0]
            assert len(self.matrix[MONTH]) > 0
        else:
            raise NotImplementedError(f'Day of month: {self.dom}')
        self.matrix = [sorted(items, reverse=not forward) for items in self.matrix]

    def _get_next_value(self, options: list, current_value: int, forward: bool = False):
        assert len(options) > 0
        for v in sorted(options, reverse=not forward):
            if (1 if forward else -1) * (v - current_value) > 0:
                return v
        return options[0]

    def _match_day_of_week(self, dt: datetime, forward: bool) -> bool:
        is_match = True
        if (1 if forward else -1) * (dt - self.now).total_seconds() < 0:
            is_match = False
        elif is_int(self.dow) and dt.isoweekday() != int(self.dow):
            is_match = False
        elif '#' in self.dow:
            weekday = int(self.dow[:self.dow.index('#')])
            nth = int(self.dow[self.dow.index('#')+1:])
            if dt.day != get_dom_by_nth_weekday(dt.year, dt.month, weekday, nth):
                is_match = False
        return is_match

    def _reset_lower(self, idx: int):
        for i in range(idx, 0, -1):
            self.current_values[i] = self.matrix[i][0]

    def _match_schedule(self, forward: bool = True):
        args = ['minute', 'hour', 'day', 'month', 'year']
        self._update_options()
        for i in range(5):
            print('Now:', {0: 'minute', 1: 'hour', 2: 'day', 3: 'month', 4: 'year'}[i])
            print('\tOptions:', self.matrix[i])
            print('\tCurrent:', self.current_values[i])
            for v in self.matrix[i]:
                if (1 if forward else -1) * (v - self.current_values[i]) > 0:
                    self.current_values[i] = v
                    change = {args[i]: v for i, v in enumerate(self.current_values)}
                    dt = self.now.replace(**change)
                    print('\t Changed to next_value', dt)
                    if self._match_day_of_week(dt, forward):
                        self.now = dt
                        return dt
            self._reset_lower(i)
        print('No matched schedule')
        return None

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
    result = Cronpy('0 3 * * 2#1 M-1', now=now).next_schedule()
    assert '2022-09-06 03:00:00' == date_to_time(result)
    # sla = c.get_sla_by_metric_date('2022-08-10')
    # print('SLA:', sla)
    # for t in c.prev_schedule():
    #     print(t)


if __name__ == '__main__':
    main()
