import cProfile
import io
import pstats
import flask


def profiled(func):
    def wrapper(*args, **kwargs):
        if flask.current_app.config['PROFILER']:
            pr = cProfile.Profile()
            pr.enable()

            result = func(*args, **kwargs)

            pr.disable()
            s = io.StringIO()
            ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
            ps.print_stats(r"'execute'.+'psycopg2.extensions.cursor'")

            # extract the number of execute calls and total time
            num = time = 0
            s.seek(0)
            for line in s:
                if "method 'execute'" in line:
                    num, time, _ = line.split(maxsplit=2)
                    num = int(num)
                    time = float(time) * 1000

            # augment the result
            stats = {
                'stats': {'queries': num, 'time_ms': time},
                'data': result,
            }

            return stats

        else:
            return func(*args, **kwargs)

    return wrapper
