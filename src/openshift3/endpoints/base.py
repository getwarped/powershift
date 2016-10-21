import os
import requests

_bool_tokens = ('1', 'true', 'enabled', 'on')

_internal_token = '/var/run/secrets/kubernetes.io/serviceaccount/token'

class Client(object):

    def __init__(self, host=None, token=None, verify=None):
        self.host = host
        self.token = token
        self.verify = verify

        if self.host is None:
            self.host = os.environ.get('OPENSHIFT_API_HOST')

        if self.host is None:
            self.host = 'openshift.default.svc.cluster.local'
            if self.token is None and os.path.exists(_internal_token):
                with open(_internal_token) as fp:
                    self.token = fp.read()
                self.verify = False

        if self.token is None:
            self.token = os.environ.get('OPENSHIFT_API_TOKEN', 'unset')

        if self.verify is None:
            self.verify = (os.environ.get('OPENSHIFT_API_VERIFY', 'true').lower()
                    in _bool_tokens)

    @property
    def api(self):
        return EndPoint(self, '/api')

    @property
    def oapi(self):
        return EndPoint(self, '/oapi')

_endpoint_api_types = {}

def registered_endpoint_types():
    return _endpoint_api_types

def register_endpoint(cls):
    _endpoint_api_types[cls.path] = cls
    return cls

class EndPoint(object):

    path = None

    _delete_ = {}
    _get_ = {}
    _head_ = {}
    _options_ = {}
    _patch_ = {}
    _post_ = {}
    _put_ = {}

    def __init__(self, _client_, _path_=None, **params):
        self.client = _client_

        if _path_:
            self.path = _path_

        self.params = params

    def __getattr__(self, name):
        path = '%s/%s' % (self.path, name)
        if path not in _endpoint_api_types:
            # This is a hack to deal with prefix on path changing
            # as we traverse. Need to ignore the first segment.

            if path.startswith('/oapi'):
                fallbackpath = path.replace('/oapi/', '/api/')
            elif path.startswith('/api'):
                fallbackpath = path.replace('/api/', '/oapi/')

            if fallbackpath not in _endpoint_api_types:
                raise AttributeError('invalid API endpoint %r' % path)

            return _endpoint_api_types[fallbackpath](self.client, **self.params)

        return _endpoint_api_types[path](self.client, **self.params)
