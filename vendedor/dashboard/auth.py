"""Autenticación Basic Auth para el dashboard admin"""

from functools import wraps
from flask import request, Response
from config import ADMIN_USER, ADMIN_PASS


def require_basic_auth(f):
    """
    Decorator que requiere Basic Auth (usuario/contraseña) para acceder a una ruta.

    Compara contra ADMIN_USER y ADMIN_PASS de env vars.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization

        if not auth or not (
            auth.username == ADMIN_USER and
            auth.password == ADMIN_PASS
        ):
            # Solicitar autenticación
            return Response(
                "Admin authentication required",
                401,
                {"WWW-Authenticate": 'Basic realm="Vendedor IA Admin"'}
            )

        return f(*args, **kwargs)

    return decorated_function
