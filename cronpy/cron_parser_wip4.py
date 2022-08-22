import logging
from itertools import product
from datetime import datetime
from dateutil.relativedelta import relativedelta

from cronpy.datetime_utils import is_int
from cronpy.datetime_utils import get_utc_now
from cronpy.datetime_utils import date_to_time
from cronpy.datetime_utils import get_n_days_of_month

logger = logging.getLogger(__name__)

MINUTE, HOUR, DOM, DOW, NWEEK, MONTH, YEAR = 0, 1, 2, 3, 4, 5, 6
UNIT_NAMES = ['MINUTE', 'HOUR', 'DOM', 'DOW', 'NWEEK', 'MONTH', 'YEAR']
YYMM_TO_END_DAY = {
    (yy, mm): get_n_days_of_month(yy, mm) for yy, mm in product(range(2000, 2100), range(1, 13))
}
OPT_MARKS = ('*', ',', '-', '/')


def get_dom_by_nth_dow(year: int, month: int, dow: int, nth: int = None) -> int:
    # FIXME: HOW TO LIMIT nth?
    # ndays = YYMM_TO_END_DAY[(year, month)]
    dt = datetime(year=year, month=month, day=1)
    first_saturday = 7 - dt.isoweekday() % 7
    nweek = nth + (0 if dow < dt.isoweekday() else -1)
    target_saturday = first_saturday + nweek * 7
    dom = target_saturday - (7 - dow) + 1
    return dom


def get_nth_week_by_datetime(dt: datetime) -> int:
    this_saturday = dt.day - dt.isoweekday() % 7 + 6
    nth = int(this_saturday / 7) + 1
    return nth


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
        self.cron_minute = parts[0]
        self.cron_hour = parts[1]
        self.cron_dom = parts[2]
        self.cron_month = parts[3]
        dow = parts[4]
        if is_int(dow):
            self.cron_dow = dow
            self.cron_nweek = '*'
        elif dow == '*':
            self.cron_dow = '*'
            self.cron_nweek = '*'
        elif '#' in dow:
            self.cron_dow = dow[:dow.index('#')]
            self.cron_nweek = dow[dow.index('#')+1:]
        else:
            raise NotImplementedError(f'NOT SUPPORTED Day of Week: {dow}')
        target = parts[5] if len(parts) >= 6 else 'D-0'
        # METRIC RELATED-->
        self.granularity = {'D': 'daily', 'W': 'weekly', 'M': 'monthly'}[target[0]]
        delta_granularity = {'D': 'days', 'W': 'weeks', 'M': 'months'}[target[0]]
        self.delta_n_periods = int(target[1:])
        self.date_delta = relativedelta(**{delta_granularity: self.delta_n_periods})
        # FINAL
        self.options = [[]] * 7  # HARD LIMIT
        self.fixed = [None] * 7
        # Set Initial Options (can be changed later)
        self._set_init_options(self.cron_minute, MINUTE, range(60))
        self._set_init_options(self.cron_hour, MINUTE, range(60))
        self._set_init_options(self.cron_dom, MINUTE, range(60))
        self._set_init_options(self.cron_dow, MINUTE, range(60))
        self._set_init_options(self.cron_nweek, MINUTE, range(60))
        self._set_init_options(self.cron_month, MINUTE, range(60))
        self._set_init_options('*', YEAR, range(self.now.year, 2100))

    def _set_init_options(self, cron: str, idx: int, default_options: list) -> list:
        default_options = sorted(default_options)
        if is_int(cron):
            self.options[idx] = [int(cron)]
            self.fixed[idx] = int(cron)
        elif cron == '*':
            self.options[idx] = default_options
        elif '/' in cron:
            every = int(cron[2:])
            self.options[idx] = [i for i in default_options if i % every == 0]
        elif ',' in cron:
            self.options[idx] = sorted([int(s) % len(default_options) for s in cron.split(',')])
        elif '-' in cron:
            start, end = cron.split('-')
            self.options[idx] = range(int(start), int(end) + 1)
        else:
            raise NotImplementedError(f'NOT SUPPORTED {UNIT_NAMES[idx]}: {cron}')

    # def _increase(self, dt: datetime) -> datetime:
    #     # 1. INCREASE STARTS FROM THE LOWEST VARIANT POSITION
    #     # 2. WILL CARRY TO THE NEXT HIGHER VARIANT POSITION IF APPLICABLE
    #     dmn = (is_int(self.fixed[DOM]), is_int(self.fixed[DOW]), is_int(self.fixed[NWEEK]))
    #     if self.fixed[MINUTE] is None:
    #         next_dt = self._incr_minute(dt)
    #     elif self.fixed[HOUR] is None:
    #         next_dt = self._incr_hour(dt)
    #     elif dmn == (False, False, False):  # -> * * *
    #         next_dt = self._incr_dom(dt.replace(day=1))
    #     elif dmn == (False, True, False):  # -> * 2 *
    #         next_dt = self._incr_nweek(dt)
    #     elif dmn == (False, True, True):  # -> * 2 #1
    #         next_dt = self._incr_dom(dt)
    #     elif dmn == (True, False, False):  # -> 5 * *
    #         next_dt = self._incr_month(dt.replace(day=self.fixed[DOM]))
    #     elif dmn == (True, True, False):  # -> 5 2 *
    #         next_dt = self._incr_month(dt.replace(day=1))
    #     elif dmn == (True, True, True):  # -> 5 2 #1
    #         next_dt = self._incr_year(dt.replace(day=self.fixed[DOM]))
    #     elif not self.fixed[NWEEK]:
    #         next_dt = self._incr_nweek(dt)
    #     elif not self.fixed[MONTH]:
    #         next_dt = self._incr_month(dt)
    #     elif not self.fixed[YEAR]:
    #         next_dt = self._incr_year(dt)
    #     else:
    #         next_dt = dt
    #     return next_dt

    def _incr_year(self, dt: datetime) -> datetime:
        __import__('pudb').set_trace()
        next_dt = dt.replace(year=dt.year + 1)
        self.options[YEAR] = [next_dt.year]
        return next_dt

    def _incr_month(self, dt: datetime) -> datetime:
        __import__('pudb').set_trace()
        if self.fixed[MONTH]:
            return dt.replace(month=self.fixed[MONTH])
        options_next = [v for v in self.options[MONTH] if v > dt.month]
        if options_next:
            next_dt = dt.replace(month=options_next[0])
        else:
            next_dt = dt.replace(month=self.options[MONTH][0])
            next_dt = self._incr_year(next_dt)
        # UPDATE DAY OPTIONS WHEN MONTH/YEAR CHANGES
        self.options[DOM] = list(range(1, YYMM_TO_END_DAY[(dt.year, dt.month)] + 1))
        return next_dt

    def _incr_nweek(self, dt: datetime) -> datetime:
        __import__('pudb').set_trace()
        if self.fixed[NWEEK]:
            # return dt.replace(month=self.fixed[MONTH])
            return dt
        if dt.day + 7 > YYMM_TO_END_DAY([dt.year, dt.month]):
            next_dt = self._incr_month(dt)
        else:
            nweek = get_nth_week_by_datetime(dt)
            day = get_dom_by_nth_dow(dt.year, dt.month, dt.isoweekday(), nweek + 1)
            next_dt = dt.replace(day=day)
        return next_dt

    def _incr_dow(self, dt: datetime) -> datetime:
        __import__('pudb').set_trace()
        if self.fixed[DOW]:
            # return dt.replace(month=self.fixed[MONTH])
            return dt

    def _incr_dom(self, dt: datetime) -> datetime:
        __import__('pudb').set_trace()
        if self.fixed[DOM]:
            return dt.replace(day=self.fixed[DOM])
        end_day = YYMM_TO_END_DAY[(dt.year, dt.month)]
        if dt.day != end_day:
            next_dt = dt.replace(day=dt.day + 1)
        else:
            next_dt = self._incr_month(dt.replace(day=1))
        return next_dt

    def _incr_day(self, dt: datetime) -> datetime:
        # D M#N:
        pass

    def _incr_hour(self, dt: datetime) -> datetime:
        __import__('pudb').set_trace()
        if self.fixed[HOUR]:
            return dt.replace(hour=self.fixed[HOUR])
        options_next = [v for v in self.options[HOUR] if v > dt.hour]
        if options_next:
            next_dt = dt.replace(hour=options_next[0])
        else:
            next_dt = dt.replace(hour=self.options[HOUR][0])
            # FIXME: NEED TO CHECK -> INCREASE ONLY WHEN Y/M/D IS NOT CERTAIN
            next_dt = self._incr_dom(next_dt)
        return next_dt

    def _incr_minute(self, dt: datetime) -> datetime:
        __import__('pudb').set_trace()
        if self.fixed[MINUTE]:
            return dt.replace(minute=self.fixed[MINUTE])
        options_next = [v for v in self.options[MINUTE] if v > dt.minute]
        if options_next:
            next_dt = dt.replace(minute=options_next[0])
        else:
            next_dt = dt.replace(minute=self.options[MINUTE][0])
            next_dt = self._incr_hour(dt)
        return next_dt

    def next_schedule(self):
        dt = datetime(
            year=self.fixed[YEAR] or self.now.year,
            month=self.fixed[MONTH] or self.now.month,
            day=self.fixed[DOM] or self.now.day,
            hour=self.fixed[HOUR] or self.now.hour,
            minute=self.fixed[MINUTE] or self.now.minute,
            second=0,
            microsecond=0,
        )
        while dt.year < 2100:
            # CHECK
            nweek = get_nth_week_by_datetime(dt)
            dow = dt.isoweekday()
            checks = [
                dt >= self.now,
                dt.year in self.options[YEAR],
                dt.month in self.options[MONTH],
                dt.day in self.options[DOM],
                dow in self.options[DOW],
                nweek in self.options[NWEEK],
                dt.hour in self.options[HOUR],
                dt.minute in self.options[MINUTE],
                # TODO: Special check of DMN-->
                # ...
            ]
            __import__('pudb').set_trace()
            if all(checks):
                self.now = dt
                return dt
            if self.fixed[MINUTE] is None:
                dt = self._incr_minute(dt)
            elif self.fixed[HOUR] is None:
                dt = self._incr_hour(dt)
            else:
                dt = self._incr_day(dt)
        raise NotADirectoryError('Not found schedule')


def main():
    now = datetime(2022, 7, 13, 5, 0, 0)
    result = Cronpy('0 3 * * 2#1 M-1', now=now).next_schedule()
    __import__('pudb').set_trace()
    assert '2022-09-06 03:00:00' == date_to_time(result)
    # sla = c.get_sla_by_metric_date('2022-08-10')
    # print('SLA:', sla)
    # for t in c.prev_schedule():
    #     print(t)


if __name__ == '__main__':
    main()
