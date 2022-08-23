from datetime import datetime, timedelta


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


def get_n_days_of_month(year: int, month: int):
    dt = datetime(year=year, month=month % 12 + 1, day=1)
    n_days = (dt - timedelta(days=1)).day
    return n_days


def get_nth_week_by_datetime(dt: datetime) -> int:
    head = 7 - datetime(year=dt.year, month=dt.month, day=1).isoweekday()
    n = int((dt.day + 6 - dt.isoweekday() % 7 - head) / 7) + 1
    return n


def get_nth_weekday_of_datetime(dt: datetime) -> int:
    carry = dt.day % 7
    n = int((dt.day - carry) / 7) + (1 if carry else 0)
    return n


def how_many_weeks_of_month(year: int, month: int) -> int:
    max_days = get_n_days_of_month(year, month)
    head = 7 - datetime(year=year, month=month, day=1).isoweekday()
    tail = max_days - head - 21
    n = 3
    if head > 0:
        n += 1
    if tail > 0:
        n += 1
    return n
