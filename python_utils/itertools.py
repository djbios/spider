def chain(*iterables):
    for iterable in iterables:
        for item in iterable:
            yield item
