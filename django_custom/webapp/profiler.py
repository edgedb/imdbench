import json

from django.conf import settings
from django.db import connection


def profiled(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        if settings.DEBUG:
            q = connection.queries
            num = len(q)
            time = sum(float(x['time']) for x in q)
            # print the stats
            print(f'Queries: {num} in {round(time * 1000, 2)}ms')

            # inject the stats into the result
            stats = {
                'stats': {'queries': num, 'time_ms': round(time * 1000, 2)},
                'data': None,
            }
            # we might have either data or content to work with
            if hasattr(result, 'data'):
                stats['data'] = result.data
                result.data = stats

            else:
                stats = json.dumps(stats).encode()
                stats = stats.replace(b'"data": null',
                                      b'"data": ' + result.content)
                result.content = stats

        return result
    return wrapper
