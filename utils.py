from functools import wraps
import mailer_fn as mailer


def capture_api_exception(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except:
            mailer.send_exception_mail()
            return {'Response': {}, 'status': False, 'string_response': 'Api Failure Occurred'}
    return decorated_function