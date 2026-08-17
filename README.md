# Cronpy

A small, dependency-free Python library for parsing cron expressions and computing the
next/previous run time — including a non-standard extension for "Nth weekday of the month"
(e.g. "the first Tuesday", "the third Friday") that most cron parsers can't express directly.

```python
from datetime import datetime
from cron_utils import Cronpy

# 3 AM on the first Tuesday of every month
c = Cronpy('0 3 * * 2#1', now=datetime(2022, 8, 10))
c.next_schedule()   # -> datetime(2022, 9, 6, 3, 0)
c.prev_schedule()   # -> datetime(2022, 8, 2, 3, 0)
```

## Supported expression syntax

Standard 5-field cron layout: `MINUTE HOUR DOM MONTH DOW`.

| Field | Range | Supported forms |
|---|---|---|
| Minute | 0-59 | `*`, `N`, `N,M,...`, `N-M`, `*/N` |
| Hour | 0-23 | `*`, `N`, `N,M,...`, `N-M`, `*/N` |
| Day of month | 1-31 | `*`, `N`, `N,M,...`, `N-M`, `*/N` |
| Month | 1-12 | `*`, `N`, `N,M,...`, `N-M`, `*/N` |
| Day of week | 1-7 (Mon-Sun) | `*`, `N`, `N#W` (Nth weekday of month) |

The `N#W` extension (e.g. `2#1` = the first Tuesday, `5#3` = the third Friday) is Quartz/AWS-style,
not part of POSIX cron. Unlike plain cron — where specifying both day-of-month *and* day-of-week
falls back to OR semantics — cronpy always ANDs day-of-month, day-of-week, and the `#`
nth-weekday-of-month qualifier together, so "10th of the month AND a Tuesday" is expressible too.

## The algorithm

Cronpy doesn't tokenize-and-regex-match against a live clock tick like a typical cron daemon does.
Instead it works in two phases:

**1. Expand each field into a sorted list of candidate values.**
`_get_options()` turns `*`, `N`, `N,M`, `N-M`, and `*/N` into a concrete list of valid ints for
that field's range (e.g. minute `*/15` → `[0, 15, 30, 45]`). Day-of-month is special: because it
can depend on day-of-week and the `#` nth-weekday qualifier, `_get_day_options()` expands all
three sub-fields independently and then intersects them against the actual calendar for the
target month (`dt.replace(day=dom)` → `isoweekday()` → nth-weekday-of-month) to get the final
list of valid days. If a field collapses to exactly one option, it's cached in `self.fixed[idx]`;
`match_schedule()` and the `_incr_*` chain check that flag to skip re-scanning a pinned unit (e.g.
a fixed minute/hour) and jump straight to incrementing the next unit that actually varies.

**2. Walk the clock through candidate values like an odometer.**
`match_schedule()` starts from `now` (or the last match) and, when the current instant doesn't
satisfy all five fields, calls a chain of `_incr_minute → _incr_hour → _incr_day → _incr_month →
_incr_year` — each one looks up the next (or previous) candidate in its own `options` list and,
if it has run out of candidates, "carries" into the next larger unit and resets, the same way you'd
carry a digit doing addition by hand. This means cronpy never iterates minute-by-minute across
weeks of dead time looking for a rare match — `0 3 10 * *` (3 AM on the 10th) run from Aug 15
jumps straight to Sept 10 in one carry, without stepping through every day in between.

**3. One engine, both directions.**
`next_schedule()` and `prev_schedule()` are the same `match_schedule()` loop with a `sign` of
`+1` or `-1`. Every increment function multiplies its delta by `sign`, so "find the next larger
candidate" and "find the next smaller candidate" are literally the same comparison expression
run backwards. This avoids maintaining two parallel traversal implementations.

Because month/day options depend on the calendar (leap years, days-per-month, weekday-of-month),
`_incr_month` recomputes `options[DOM]` every time the month or year changes, and recurses if that
lands on a month with zero valid days (e.g. day-of-month `31` combined with a 30-day month).

## Why hand-roll this instead of using croniter / python-crontab / APScheduler?

Real cron-parsing libraries exist and are good — [croniter](https://github.com/pallets-eco/croniter),
[python-crontab](https://pypi.org/project/python-crontab/), and
[APScheduler](https://apscheduler.readthedocs.io/) are all more mature and more widely used than
this project. Cronpy exists for a narrower reason:

- **AND semantics for day-of-month + day-of-week by default.** In POSIX cron (and croniter's
  default), specifying both DOM and DOW ORs them together; getting "first Tuesday of the month"
  out of croniter requires passing `day_or=False` and re-deriving the expression as a day-of-month
  *range* (`'0 3 1-7 * 2'` with `day_or=False`) rather than writing the Nth-weekday intent
  directly. Cronpy takes `2#1` and treats DOM/DOW/nweek as one intersected set natively.
- **Zero dependencies.** The whole parser is ~200 lines across two files, importable in
  constrained runtimes (Lambda layers, embedded scripts, sandboxes) without pulling in a package.
  APScheduler in particular is a full scheduling framework (threads, executors, jobstores) when
  all that's needed is "what time is the next run".
- **One symmetric engine for next *and* previous.** Computing "when did this last run" is a
  first-class operation here (`prev_schedule()`), driven by the same code path as
  `next_schedule()`, which is useful for backfills/SLA-style "was this cron due since X" checks.
- **Small enough to fully audit.** The trade-off for all of the above is feature coverage —
  see Limitations below. For a general-purpose, spec-compliant cron parser, prefer croniter.

## A correctness bug worth knowing about

While tracing the algorithm above, one real bug surfaced (not just a missing feature): when
**both month and day-of-month are pinned to a single value** (e.g. `0 3 1 6 *`, June 1st), the
class can skip a whole year it shouldn't.

`self.fixed[DOM]` is *never actually set* — `_set_init_options()` is what populates `self.fixed[idx]`,
but day-of-month is populated separately via `self.options[DOM] = self._get_day_options(self.now)`
in `__init__`, which bypasses it. So `match_schedule()`'s initial `dt` is built with
`day=self.fixed[DOM] or self.now.day` → always falls back to `self.now.day`, even when the day
field is a fixed single value. If `now`'s day-of-month happens to be numerically greater than the
target day, `_incr_day` finds no same-month candidate, carries into `_incr_month`, and — because
month is also fixed — that carry always advances a full year instead of just moving to next
month/using the already-known day:

```python
>>> Cronpy('0 3 1 6 *', now=datetime(2022, 3, 10)).next_schedule()
datetime.datetime(2023, 6, 1, 3, 0)   # wrong — should be 2022-06-01, which is still in the future
```

Fix sketch: route `self.options[DOM] = self._get_day_options(self.now)` through the same
`fixed[DOM]`-setting logic `_set_init_options()` uses (or just set `self.fixed[DOM]` explicitly
when `_get_day_options` returns exactly one value).

## Limitations / where the expression grammar could go further

The field parser (`_get_options` in `cron_utils.py`) resolves `*`, `N`, `N,M,...`, `N-M`, and
`*/N` as **mutually exclusive** cases (an `elif` chain), which is the main ceiling on what
expressions can be written today:

- Combined forms raise `ValueError` rather than being parsed: `1-15/2` (stepped range),
  `5,10-20,*/30` (list mixed with ranges/steps), a step with a non-`*` start (e.g. `5/15` meaning
  "every 15 starting at 5"). The branches for `/`, `,`, and `-` are checked in that order and each
  one calls `int()` on the whole remaining string, so as soon as a field contains more than one of
  those characters it throws instead of degrading gracefully.
- Day-of-week only accepts a single integer, `*`, or `N#W` — not `1,3,5` (Mon/Wed/Fri) or `1-5`
  (weekdays), even though `_get_options` could already express those if the day-of-week branch
  in `Cronpy.__init__` called into it the same way minute/hour/month do.
- No named values (`JAN`-`DEC`, `MON`-`SUN`), no `L` (last day of month / last weekday), no `W`
  (nearest weekday), no `?`.
- Year is always implicit (`now.year - 1 .. now.year + 1`) and not user-specified, matching
  standard 5-field cron but ruling out one-off/expiring schedules.

None of these require changing the traversal algorithm — `_get_options` already returns a plain
list of ints and everything downstream just consumes that list, so extending the grammar is a
matter of broadening how a single field string is parsed into candidates.

## Development

```bash
pip install -r requirements-test.txt
pytest -vv --flake8 tests/
```
