from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def is_int(s: str) -> bool:
    result = False
    try:
        result = int(s) - float(s) == 0
    except Exception:
        pass
    return result


def get_utc_now() -> datetime:
    # FOR EASIER MOCKING / TESTING
    return datetime.utcnow()


def get_day_of_a_week(day: datetime, n: int) -> datetime:
    # Monday: 1; ... ; Friday: 5; Saturday: 6; Sunday: 7;
    assert n in range(7)
    sunday = day - timedelta(days=day.isoweekday() % 7)
    target = sunday + timedelta(days=n)
    return target


def string_to_date(string_date: str) -> datetime:
    return datetime.strptime(string_date, '%Y-%m-%d')


def date_to_string(date: datetime) -> str:
    return date.strftime('%Y-%m-%d')


def date_to_time(date: datetime) -> str:
    return date.strftime('%Y-%m-%d %H:%M:%S')


def date_to_start_end(dstr: str, granularity: str = 'daily') -> tuple:
    assert isinstance(dstr, str) and isinstance(granularity, str)
    start = end = day = datetime.strptime(dstr, '%Y-%m-%d')
    if granularity == 'weekly':
        weekday_n = day.isoweekday() % 7
        start = day - timedelta(days=weekday_n)
        end = day + timedelta(days=6 - weekday_n)
    elif granularity == 'monthly':
        start = day.replace(day=1)
        end = (start + relativedelta(months=1)) - relativedelta(days=1)
    start_str, end_str = start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
    return start_str, end_str


def enumerate_dates(start_date: str, end_date: str, granularity: str) -> list:
    start, end = datetime.strptime(start_date, '%Y-%m-%d'), datetime.strptime(end_date, '%Y-%m-%d')
    daily_dates = [start + timedelta(days=i) for i in range((end - start).days + 1)]

    target_dates = []
    if granularity == 'daily':
        target_dates = daily_dates
    elif granularity == 'weekly':
        # Start from Monday: weeday_index = day.weekday()
        # Start from Sunday: weeday_index = (day.weekday() + 1) % 7
        target_dates = sorted(set([day - timedelta(days=(day.weekday() + 1) % 7) for day in daily_dates]))  # Sundays
    elif granularity == 'monthly':
        target_dates = sorted(set([day.replace(day=1) for day in daily_dates]))

    combos = [date_to_start_end(day.strftime('%Y-%m-%d'), granularity) for day in target_dates]
    return combos


def get_date_combinations(date_expression: str, granularity: str) -> list:
    date_combos = []
    if not date_expression:
        return []
    for dstr in str(date_expression).split(','):
        if '_' in dstr:
            start, end = dstr.split('_')
            date_combos += enumerate_dates(start, end, granularity)
        else:
            start, end = date_to_start_end(dstr, granularity)
            date_combos += [(start, end)]
    return date_combos


def get_n_days_of_month(year: int, month: int):
    dt = datetime(year=year, month=month % 12 + 1, day=1)
    n_days = (dt - timedelta(days=1)).day
    return n_days


def get_dom_by_nth_weekday(year: str, month: str, weekday: int, nth: int) -> int:
    assert nth <= 5
    d = datetime(year=year, month=month, day=1)
    weekdays = []
    while d.month == month:
        if d.isoweekday() == weekday % 7:
            weekdays.append(d.day)
        d += relativedelta(days=1)
    dom = weekdays[nth - 1] if len(weekdays) >= nth else None
    return dom
