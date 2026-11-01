def median(values):
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return s[mid]


def mean(values):
    return sum(values) / len(values)
