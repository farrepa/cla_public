from .base import *


DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Marco Fucci', 'marco.fucci@digital.justice.co.uk'),
    ('Rai Kotecha', 'ravi.kotecha@digital.justice.gov.uk'),
)

MANAGERS = ADMINS


HOST_NAME = "http://cla-frontend.dsd.io"

BACKEND_BASE_URI = 'http://cla-backend.dsd.io'