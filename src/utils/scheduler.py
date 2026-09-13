import asyncio
from datetime import datetime, timedelta

_WEEKDAYS = {}
for _i, _n in enumerate(
    ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
):
    _WEEKDAYS[_n] = _i
for _i, _n in enumerate(
    ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
):
    _WEEKDAYS[_n] = _i
for _i, _n in enumerate(['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']):
    _WEEKDAYS[_n] = _i


def _parse_time(value):
    h, m = value.strip().split(':')
    return int(h), int(m)


def _parse_weekday(value):
    return _WEEKDAYS[str(value).strip().lower()]


class Scheduler:
    def __init__(self):
        self._events = []
        self._tasks = []

    def register(self, function, date):
        spec = self._parse(date)
        event = {'function': function, 'spec': spec}
        self._events.append(event)
        return event

    def _parse(self, date):
        if isinstance(date, str):
            h, m = _parse_time(date)
            return {'hour': h, 'minute': m, 'weekday': None}
        if isinstance(date, dict):
            time = date.get('time') or date.get('date')
            h, m = _parse_time(time)
            weekday = date.get('weekday')
            if weekday is not None:
                weekday = _parse_weekday(weekday)
            return {'hour': h, 'minute': m, 'weekday': weekday}
        h, m = _parse_time(date[0])
        weekday = _parse_weekday(date[1])
        return {'hour': h, 'minute': m, 'weekday': weekday}

    def start(self):
        for event in self._events:
            self._tasks.append(asyncio.create_task(self._runner(event)))
        return self._tasks

    async def _runner(self, event):
        function = event['function']
        spec = event['spec']
        while True:
            await asyncio.sleep(self._seconds_until(spec))
            try:
                if asyncio.iscoroutinefunction(function):
                    await function()
                else:
                    function()
            except Exception:
                pass
            await asyncio.sleep(60)

    def _seconds_until(self, spec):
        return max(0.0, (self._next_run(spec) - datetime.now()).total_seconds())

    def _next_run(self, spec):
        now = datetime.now()
        base = now.replace(second=0, microsecond=0)
        weekday = spec['weekday']
        if weekday is None:
            target = base.replace(hour=spec['hour'], minute=spec['minute'])
            if target <= now:
                target += timedelta(days=1)
            return target
        today = base.replace(hour=0, minute=0, second=0, microsecond=0)
        days_ahead = (weekday - now.weekday()) % 7
        candidate = (today + timedelta(days=days_ahead)).replace(
            hour=spec['hour'], minute=spec['minute']
        )
        if candidate <= now:
            candidate += timedelta(days=7)
        return candidate


scheduler = Scheduler()