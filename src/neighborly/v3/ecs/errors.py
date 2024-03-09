"""Neighborly ECS Errors.

"""

class ResourceNotFoundError(Exception):
    """Exception raised when attempting to access a resource that does not exist."""

    __slots__ = ("resource_type", "message")

    resource_type: str
    """The class name of the resource."""
    message: str
    """An error message."""

    def __init__(self, resource_type: str) -> None:
        """
        Parameters
        ----------
        resource_type
            The type of the resource not found.
        """
        super().__init__()
        self.resource_type = resource_type
        self.message = f"Could not find resource with type: {resource_type!r}."

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.resource_type = })"


class SystemNotFoundError(Exception):
    """Exception raised when attempting to access a system that does not exist."""

    __slots__ = ("system_type", "message")

    system_type: str
    """The class name of the system."""
    message: str
    """An error message."""

    def __init__(self, system_type: str) -> None:
        """
        Parameters
        ----------
        system_type
            The class name of the resource.
        """
        super().__init__()
        self.system_type = system_type
        self.message = f"Could not find system with type: {system_type!r}."

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.system_type = })"


class GameObjectNotFoundError(Exception):
    """Exception raised when attempting to access a GameObject that does not exist."""

    __slots__ = ("gameobject_id", "message")

    gameobject_id: int
    """The UID of the desired GameObject."""
    message: str
    """An error message."""

    def __init__(self, gameobject_id: int) -> None:
        """
        Parameters
        ----------
        gameobject_id
            The UID of the desired GameObject.
        """
        super().__init__()
        self.gameobject_id = gameobject_id
        self.message = f"Could not find GameObject with ID: {gameobject_id!r}."

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.gameobject_id = })"


class ComponentNotFoundError(Exception):
    """Exception raised when attempting to access a component that does not exist."""

    __slots__ = ("component_type", "message")

    component_type: str
    """The class name of component not found."""
    message: str
    """An error message."""

    def __init__(self, component_type: str) -> None:
        """
        Parameters
        ----------
        component_type
            The class name of the desired component.
        """
        super().__init__()
        self.component_type = component_type
        self.message = f"Could not find Component with type: {component_type!r}."

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.component_type = })"

