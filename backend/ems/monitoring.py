import logging
from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled, AuthenticationFailed

logger = logging.getLogger('ems.monitor')


def custom_exception_handler(exc, context):
    # Log throttled and authentication failures for monitoring
    request = context.get('request')
    remote = None
    if request is not None:
        remote = request.META.get('REMOTE_ADDR')

    if isinstance(exc, Throttled):
        logger.warning('Request throttled: %s %s from %s detail=%s', request.method, request.get_full_path(), remote, str(exc))
    if isinstance(exc, AuthenticationFailed):
        logger.warning('Authentication failed for %s from %s detail=%s', request.get_full_path(), remote, str(exc))

    # Delegate to the standard DRF exception handler for the response
    return exception_handler(exc, context)
