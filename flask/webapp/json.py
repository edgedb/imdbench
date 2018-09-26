import flask
import rapidjson


def jsonify(*args, **kwargs):
    """This is meant as to be used instead of Flask's native jsonify."""
    app = flask.current_app
    indent = None

    if app.config['JSONIFY_PRETTYPRINT_REGULAR'] or app.debug:
        indent = 2

    if args and kwargs:
        raise TypeError(
            'jsonify() behavior undefined when passed both args and kwargs')
    elif len(args) == 1:  # single args are passed directly to dumps()
        data = args[0]
    else:
        data = args or kwargs

    return app.response_class(
        rapidjson.dumps(data, indent=indent) + '\n',
        mimetype=app.config['JSONIFY_MIMETYPE']
    )
