
class GatewayConnectionError(Exception):
    """Gateway failed connection"""
    pass


class EndpointException(Exception):
    pass


class EndpointHealthException(EndpointException):
    """CRUD Endpoint failed to pass health check"""
    pass


class EndpointValueException(EndpointException):
    """CRUD Endpoint request using the wrong value or value type"""
    pass


class EndpointRuntimeException(EndpointException, RuntimeError):
    """CRUD Endpoint failed to handle a request"""
    pass


class EndpointFactoryException(EndpointException):
    """CRUD Endpoint Factory failed to instantiate object"""
    pass
