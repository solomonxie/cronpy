import logging
from datetime import datetime

import datetime_utils

logger = logging.getLogger(__name__)

MINUTE, HOUR, DOM, DOW, NWEEK, MONTH, YEAR = 0, 1, 2, 3, 4, 5, 6
UNIT_NAMES = ['MINUTE', 'HOUR', 'DOM', 'DOW', 'NWEEK', 'MONTH', 'YEAR']


class Cronpy:
    def __init__(self, cron: str, now: datetime = None):
        """ Cron Expression:
        REF: https://crontab.guru
        Minute; Hour; Day(of month); Month; Day(of week)
        0 3 * * * D-2 ==> 3AM everyday
        0 3 * * 2 W-1 ==> 3AM on every Tuesday
        0 3 10 * * M-1 ==> 3AM on every month's 10th
        0 3 * * 2#1 M-1 ==> 3AM on every month's first Tuesday
        0 3 */2 * * D-2 ==> 3AM on Every 2 days
        * 3 * * * D-2 ==> Every minute of 3AM every day
        """
        self.now = now or datetime_utils.get_utc_now()
        self.last_schedule = None
        self.cron = cron
        self.sign = 1
        parts = cron.split(' ')
        self.cron_minute = parts[0]
        self.cron_hour = parts[1]
        self.cron_dom = parts[2]
        self.cron_month = parts[3]
        dow = parts[4]
        if datetime_utils.is_int(dow):
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
        # FINAL
        self.options = [[]] * 7  # HARD LIMIT
        self.fixed = [None] * 7
        # Set Initial Options (can be changed later)
        self._set_init_options(self.cron_minute, MINUTE, range(60))
        self._set_init_options(self.cron_hour, HOUR, range(24))
        self._set_init_options(self.cron_month, MONTH, range(1, 13))
        self._set_init_options('*', YEAR, [self.now.year - 1, self.now.year, self.now.year + 1])
        self.options[DOM] = self._get_day_options(self.now)

    def _set_init_options(self, cron: str, idx: int, xrange: list):
        options = self._get_options(cron, xrange)
        self.options[idx] = options
        if len(options) == 1:
            self.fixed[idx] = options[0]
        elif len(options) == 0:
            raise NotImplementedError(f'NOT SUPPORTED {UNIT_NAMES[idx]}: {cron}')
        return options

    def _get_day_options(self, dt: datetime) -> list:
        max_days = datetime_utils.how_many_days_of_month(dt.year, dt.month)
        max_weeks = datetime_utils.how_many_weeks_of_month(dt.year, dt.month)
        dom_options = self._get_options(self.cron_dom, range(1, max_days + 1))
        dow_options = self._get_options(self.cron_dow, range(1, 8))
        nweek_options = self._get_options(self.cron_nweek, range(1, max_weeks + 1))
        options = []
        for dom in dom_options:
            next_dt = dt.replace(day=dom)
            dow = next_dt.isoweekday()
            nweek = datetime_utils.get_nth_weekday_of_datetime(next_dt)
            if dow in dow_options and nweek in nweek_options:
                options.append(next_dt.day)
        return options

    def _get_options(self, cron: str, xrange: range) -> list:
        options = []
        if datetime_utils.is_int(cron):
            options = [int(cron)]
        elif cron == '*':
            options = xrange
        elif '/' in cron:
            every = int(cron[2:])
            options = [i for i in xrange if i % every == 0]
        elif ',' in cron:
            options = [int(s) for s in cron.split(',')]
        elif '-' in cron:
            start, end = cron.split('-')
            options = range(int(start), int(end) + 1)
        carry_point = max(xrange) + 1
        options = sorted({i % carry_point for i in options if i in xrange})
        return options

    def _incr_year(self, dt: datetime) -> datetime:
        next_dt = dt.replace(year=dt.year + 1 * self.sign)
        self.options[YEAR] = [next_dt.year]
        return next_dt

    def _incr_month(self, dt: datetime) -> datetime:
        options_next = [v for v in self.options[MONTH] if (v - dt.month) * self.sign > 0]
        inext = 0 if self.sign > 0 else -1
        if self.fixed[MONTH]:
            next_dt = self._incr_year(dt)
        elif options_next:
            next_dt = dt.replace(month=options_next[inext], day=1)
        else:
            next_dt = self._incr_year(dt.replace(month=self.options[MONTH][inext]))
        # UPDATE DAY OPTIONS WHEN MONTH/YEAR CHANGES
        self.options[DOM] = self._get_day_options(next_dt)  # FIXME
        if not self.options[DOM]:
            self._incr_month(next_dt)
        return next_dt

    def _incr_day(self, dt: datetime) -> datetime:
        options_next = [v for v in self.options[DOM] if (v - dt.day) * self.sign > 0]
        inext = 0 if self.sign > 0 else -1
        if self.fixed[DOM]:
            next_dt = self._incr_month(dt)
        elif options_next:
            next_dt = dt.replace(day=options_next[inext])
        else:
            next_dt = self._incr_month(dt)
            next_dt = next_dt.replace(day=self.options[DOM][inext])
        return next_dt

    def _incr_hour(self, dt: datetime) -> datetime:
        options_next = [v for v in self.options[HOUR] if (v - dt.hour) * self.sign > 0]
        inext = 0 if self.sign > 0 else -1
        if self.fixed[HOUR] is not None:
            next_dt = self._incr_day(dt)
        elif dt < self.now:
            next_dt = self._incr_day(dt)
        elif options_next:
            next_dt = dt.replace(hour=options_next[inext])
        else:
            # FIXME: NEED TO CHECK -> INCREASE ONLY WHEN Y/M/D IS NOT CERTAIN
            next_dt = self._incr_day(dt.replace(hour=self.options[HOUR][inext]))
        return next_dt

    def _incr_minute(self, dt: datetime) -> datetime:
        options_next = [v for v in self.options[MINUTE] if (v - dt.minute) * self.sign > 0]
        inext = 0 if self.sign > 0 else -1
        if self.fixed[MINUTE] is not None:
            next_dt = self._incr_hour(dt)
        elif dt < self.now:
            next_dt = self._incr_hour(dt)
        elif options_next:
            next_dt = dt.replace(minute=options_next[inext])
        else:
            next_dt = self._incr_hour(dt.replace(minute=self.options[MINUTE][inext]))
        return next_dt

    def match_schedule(self) -> datetime:
        dt = datetime(
            year=self.fixed[YEAR] or self.now.year,
            month=self.fixed[MONTH] or self.now.month,
            day=self.fixed[DOM] or self.now.day,
            hour=self.fixed[HOUR] if self.fixed[HOUR] else self.now.hour,
            minute=self.fixed[MINUTE] if self.fixed[MINUTE] is not None else self.now.minute,
            second=0,
            microsecond=0,
        )
        while 1999 < dt.year < 2100:
            # CHECK
            delta = self.sign * (dt - (self.last_schedule or self.now)).total_seconds()
            checks = [
                delta > 0 if self.last_schedule else delta >= 0,
                dt.year in self.options[YEAR],
                dt.month in self.options[MONTH],
                dt.day in self.options[DOM],
                dt.hour in self.options[HOUR],
                dt.minute in self.options[MINUTE],
            ]
            if all(checks):
                self.last_schedule = self.now = dt
                return dt
            if self.fixed[MINUTE] is None:
                dt = self._incr_minute(dt)
            elif self.fixed[HOUR] is None:
                dt = self._incr_hour(dt)
            else:
                dt = self._incr_day(dt)
        raise NotImplementedError('Not found schedule')

    def next_schedule(self) -> datetime:
        self.sign = 1
        return self.match_schedule()

    def prev_schedule(self) -> datetime:
        self.sign = -1
        return self.match_schedule()


def main():
    from datetime_utils import date_to_time
    now = datetime(2022, 8, 10, 5, 0, 0)
    c = Cronpy('0 3 11,13,20 * *', now=now)
    assert '2022-07-20 03:00:00' == date_to_time(c.prev_schedule())
    assert '2022-07-13 03:00:00' == date_to_time(c.prev_schedule())
    assert '2022-07-11 03:00:00' == date_to_time(c.prev_schedule())
    assert '2022-06-20 03:00:00' == date_to_time(c.prev_schedule())
    # sla = c.get_sla_by_metric_date('2022-08-10')
    # print('SLA:', sla)
    # for t in c.prev_schedule():
    #     print(t)


if __name__ == '__main__':
    main()
