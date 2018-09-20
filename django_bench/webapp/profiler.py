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
            stats = {'_stats': {
                'queries': num, 'time_ms': round(time * 1000, 2)}}
            # we might have either data or content to work with
            if hasattr(result, 'data'):
                data = result.data
                if isinstance(data, dict):
                    stats.update(data)
                    data = stats
                else:
                    data = [stats] + data

                result.data = data

            else:
                data = result.content
                stats = json.dumps(stats)
                # based on first character we know if it's a JSON
                # array or object
                if data[0] == b'['[0]:
                    stats = f'[{stats}, '
                else:
                    stats = f'{stats[:-1]}, '

                data = stats.encode() + data[1:]
                result.content = data

        return result
    return wrapper
