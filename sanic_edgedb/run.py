import os
import webapp


if __name__ == "__main__":
    kwargs = {
        'host': "127.0.0.1",
        'port': 8100,
    }
    if os.getenv('BENCH_NOLOG', '').lower() == 'true':
        kwargs['debug'] = False
        kwargs['access_log'] = False

    webapp.app.run(**kwargs)
