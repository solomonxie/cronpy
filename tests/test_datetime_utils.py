import pytest
from datetime import datetime

import datetime_utils as utils


def test_convert_string_and_date():
    assert '2022-01-01' == utils.date_to_string(utils.string_to_date('2022-01-01'))
    assert '1999-01-01' == utils.date_to_string(utils.string_to_date('1999-01-01'))
    with pytest.raises(Exception):
        utils.string_to_date('2022-13-32')


def test_utc_now():
    now = datetime.utcnow()
    assert utils.date_to_string(now) == utils.date_to_string(utils.get_utc_now())


def test_get_day_of_a_week():
    day = utils.string_to_date('2022-08-01')
    assert '2022-07-31' == utils.date_to_string(utils.get_day_of_a_week(day, 0))
    assert '2022-08-01' == utils.date_to_string(utils.get_day_of_a_week(day, 1))
    assert '2022-08-02' == utils.date_to_string(utils.get_day_of_a_week(day, 2))
    assert '2022-08-03' == utils.date_to_string(utils.get_day_of_a_week(day, 3))
    assert '2022-08-04' == utils.date_to_string(utils.get_day_of_a_week(day, 4))
    assert '2022-08-05' == utils.date_to_string(utils.get_day_of_a_week(day, 5))
    assert '2022-08-06' == utils.date_to_string(utils.get_day_of_a_week(day, 6))
    day = utils.string_to_date('2021-01-01')
    assert '2020-12-27' == utils.date_to_string(utils.get_day_of_a_week(day, 0))
    assert '2020-12-28' == utils.date_to_string(utils.get_day_of_a_week(day, 1))
    assert '2020-12-29' == utils.date_to_string(utils.get_day_of_a_week(day, 2))
    assert '2020-12-30' == utils.date_to_string(utils.get_day_of_a_week(day, 3))
    assert '2020-12-31' == utils.date_to_string(utils.get_day_of_a_week(day, 4))
    assert '2021-01-01' == utils.date_to_string(utils.get_day_of_a_week(day, 5))
    assert '2021-01-02' == utils.date_to_string(utils.get_day_of_a_week(day, 6))


def test_date_to_time():
    assert '2022-08-01 13:59:20' == utils.date_to_time(datetime(2022, 8, 1, 13, 59, 20))
    assert '2022-08-01 00:00:00' == utils.date_to_time(datetime(2022, 8, 1))


def test_get_n_days_of_month():
    assert 29 == utils.get_n_days_of_month(2020, 2)
    assert 28 == utils.get_n_days_of_month(2022, 2)
    assert 31 == utils.get_n_days_of_month(2022, 7)
    assert 31 == utils.get_n_days_of_month(2022, 8)
    assert 30 == utils.get_n_days_of_month(2022, 9)
    assert 31 == utils.get_n_days_of_month(2022, 12)


def test_get_nth_weekday_of_datetime():
    assert 1 == utils.get_nth_weekday_of_datetime(datetime(2022, 8, 1))
    assert 1 == utils.get_nth_weekday_of_datetime(datetime(2022, 8, 2))
    assert 1 == utils.get_nth_weekday_of_datetime(datetime(2022, 8, 3))
    assert 1 == utils.get_nth_weekday_of_datetime(datetime(2022, 8, 4))
    assert 1 == utils.get_nth_weekday_of_datetime(datetime(2022, 8, 5))
    assert 1 == utils.get_nth_weekday_of_datetime(datetime(2022, 8, 6))
    assert 1 == utils.get_nth_weekday_of_datetime(datetime(2022, 8, 7))
    assert 2 == utils.get_nth_weekday_of_datetime(datetime(2022, 8, 8))
    assert 2 == utils.get_nth_weekday_of_datetime(datetime(2022, 8, 9))
    assert 5 == utils.get_nth_weekday_of_datetime(datetime(2022, 8, 31))


def test_how_many_weeks_of_month():
    assert 6 == utils.how_many_weeks_of_month(2022, 1)
    assert 5 == utils.how_many_weeks_of_month(2022, 2)
    assert 5 == utils.how_many_weeks_of_month(2022, 3)
    assert 5 == utils.how_many_weeks_of_month(2022, 4)
    assert 5 == utils.how_many_weeks_of_month(2022, 5)
    assert 5 == utils.how_many_weeks_of_month(2022, 6)
    assert 6 == utils.how_many_weeks_of_month(2022, 7)
    assert 5 == utils.how_many_weeks_of_month(2022, 8)
    assert 5 == utils.how_many_weeks_of_month(2022, 9)
    assert 6 == utils.how_many_weeks_of_month(2022, 10)
    assert 5 == utils.how_many_weeks_of_month(2022, 11)
    assert 5 == utils.how_many_weeks_of_month(2022, 12)
