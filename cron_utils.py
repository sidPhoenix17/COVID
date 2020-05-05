bound_map = {
    0: [0, 59], #minute
    1: [0, 23], #hour
    2: [1, 31], #date
    3: [1, 12], #month
    4: [0, 6]   #day
}


def is_between(term, bound):
    try:
        if int(bound[0]) <= int(term) <= int(bound[1]):
            return True
        return False
    except ValueError:
        return False


def is_list(term, bound):
    lst = term.split(",")
    return all(map(lambda x: is_between(x, bound) or is_range(x, bound) or is_interval(x, bound), lst))


def is_range(term, bound):
    range_values = term.split("-")
    if len(range_values) != 2:
        return False
    return is_between(range_values[0], bound) and is_between(range_values[1], bound) and int(range_values[0]) < int(range_values[1])


def is_interval(term, bound):
    interval = term.split("/")
    if len(interval) != 2:
        return False
    return is_between(interval[0], bound) and is_between(interval[1], bound)


def is_valid_cron(cron_exp):
    print(cron_exp)
    exp = cron_exp.split()
    if len(exp) != 5:
        return False
    for i in range(5):
        if not (exp[i] == "*" or is_list(exp[i], bound_map[i])):
            return False
    return True


def in_list(term, bound):
    values = term.split(",")
    return any(map(lambda x: is_between(x, bound) or in_range(x, bound) or in_interval(x, bound), values))


def in_range(term, bound):
    range_values = term.split("-")
    if len(range_values) != 2:
        return False
    return is_between(range_values[0], bound) or is_between(range_values[1], bound) or is_between(bound[0], range_values)


def in_interval(term, bound):
    interval = term.split("/")
    if len(interval) != 2:
        return False
    values = list(range(int(interval[0]), bound[1]+1, int(interval[1])))
    return any(map(lambda x: bound[0] <= x, values))


def check_cron_condition(cron_exp, start_time, end_time):
    exp = cron_exp.split()
    time_span = {0: [start_time.minute, end_time.minute],
                 1: [start_time.hour, end_time.hour],
                 2: [start_time.day, end_time.day],
                 3: [start_time.month, end_time.month],
                 4: [start_time.weekday(), end_time.weekday()]}
    for i in range(5):
        if not (exp[i] == "*" or in_list(exp[i], time_span[i])):
            return False
    return True
