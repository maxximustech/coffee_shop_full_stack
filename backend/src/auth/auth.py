import json
from flask import request, _request_ctx_stack, abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen
from dotenv import load_dotenv
import os

load_dotenv()
AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN")
API_AUDIENCE = os.environ.get("API_AUDIENCE")
ALGORITHMS = ['RS256']

# AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header

def get_token_auth_header():
    auth_header = request.headers.get('Authorization', None)
    if auth_header is None:
        raise AuthError('Authorization header is missing', 401)
    auth_header_arr = auth_header.split(' ')
    if auth_header_arr[0].lower() != 'bearer':
        raise AuthError('Authorization header does not match the "Bearer"', 401)
    elif len(auth_header_arr) <= 1:
        raise AuthError('Authorization token could not found', 401)
    elif auth_header_arr[1]:
        return auth_header_arr[1]
    raise AuthError('Authorization process could not be completed', 422)


def check_permissions(permission, payload):
    if 'permissions' not in payload:
        raise AuthError('Permissions could not be found', 404)
    if permission not in payload['permissions']:
        raise AuthError('You do not have permission to access this resource', 401)
    return True


def verify_decode_jwt(token):
    auth0ApiUrl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks_data = json.loads(auth0ApiUrl.read())
    raw_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in raw_header:
        raise AuthError('Authorization could not be completed', 401)

    for key in jwks_data['keys']:
        if key['kid'] == raw_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            return jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )
        except jwt.ExpiredSignatureError:
            raise AuthError('Token has expired', 401)
        except jwt.JWTClaimsError:
            raise AuthError('The authentication claims seem to be invalid', 401)
        except Exception:
            raise AuthError('Unable to parse authentication token', 401)
    raise AuthError('Unable to find the appropriate key', 401)


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                token = get_token_auth_header()
                payload = verify_decode_jwt(token)
            except:
                raise AuthError('Authentication failed', 401)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper

    return requires_auth_decorator
