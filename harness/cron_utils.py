import datetime


def _cron_validate_field(field: str, low: int, high: int):
    if field == "*":
        return None
    if field.startswith("*/"):
        step_str = field[2:]
        if not step_str.isdigit():
            return f"Invalid step size:{field}"
        if int(step_str) <= 0:
            return f"Step size must be greater than 0:{field}"
        return None
    if "," in field:  # 1,5,8
        for part in field.split(","):
            err = _cron_validate_field(part.strip(), low, high)
            if err:
                return err
        return None
    if "-" in field:  # 1-5
        parts = field.split("-", 1)
        if not parts[0].isdigit() or not parts[1].isdigit():
            return f"Invalid range:{field}"
        a, b = int(parts[0]), int(parts[1])
        if a < low or a > high or b < low or b > high:
            return f"range {field} excessive {low}-{high}"
        if a > b:
            return f"The starting value of the range must be less than the ending value:{field}"
        return None
    if not field.isdigit():
        return f"Invalid filed:{field}"
    val = int(field)
    if val < low or val > high:
        return f"value: {val} excessive {low}-{high}"
    return None


def cron_validate(cron_expr: str):
    fileds = cron_expr.strip().split()
    if len(fileds) != 5:
        return f"cron require 5 fileds, currently passes {len(fileds)} "
    bounds = [
        (0, 59),
        (0, 23),
        (1, 31),
        (1, 12),
        (0, 6),
    ]
    names = ["minute", "hour", "day", "month", "week"]
    for field, (low, high), name in zip(fileds, bounds, names):
        err = _cron_validate_field(field, low, high)
        if err:
            return f"{name}: {err}"
    return None


def _cron_field_match(field: str, value: int):
    if field == "*":
        return True
    if field.startswith("*/"):
        step = int(field[2:])
        return step > 0 and value % step == 0
    if "," in field:
        return any(_cron_field_match(f.strip(), value) for f in field.split(","))
    if "-" in field:
        low, high = field.split("-", 1)
        return int(low) <= value <= int(high)
    return value == int(field)


def cron_matchs(cron_expr: str, dt: datetime):
    fields = cron_expr.strip().split()
    if len(fields) != 5:
        return False
    minute_field, hour_field, day_field, month_field, week_field = fields
    day_of_week_val = (dt.weekday() + 1) % 7
    minute_match = _cron_field_match(minute_field, dt.minute)
    hour_match = _cron_field_match(hour_field, dt.hour)
    day_match = _cron_field_match(day_field, dt.day)
    month_match = _cron_field_match(month_field, dt.month)
    week_match = _cron_field_match(week_field, day_of_week_val)
    if not (minute_match and hour_match and month_match):
        return False
    day_unconstrained = day_field == "*"
    week_unconstrained = week_field == "*"
    if day_unconstrained and week_unconstrained:
        return True
    if day_unconstrained:
        return week_match
    if week_unconstrained:
        return day_match
    return day_match or week_match
