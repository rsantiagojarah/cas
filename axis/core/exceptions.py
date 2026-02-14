"""Excepciones personalizadas del núcleo AXIS."""


class ProjectNotFound(Exception):
    """Proyecto no encontrado."""

    pass


class NoActiveProject(Exception):
    """No hay proyecto activo definido."""

    pass


class OperationNotRegistered(Exception):
    """Operación no registrada en el REGISTRY."""

    pass


class InvalidInput(Exception):
    """Entrada o parámetros inválidos."""

    pass
