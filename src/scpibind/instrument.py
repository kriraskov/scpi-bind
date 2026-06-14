import pyvisa
import logging
from typing import Any, Self, Protocol


logger = logging.getLogger(__name__)


class VISAInterface(Protocol):
    """Protocol for VISA interfaces."""
    def write(self, message: str) -> None:
        """Write a message to the resource.
        
        Args:
            message (str): Message to write to the resource.
        """
        ...

    def query(self, message: str) -> str:
        """Write a message to the resource and query the response.
        
        Args:
            message (str): Message to write to the resource.
        
        Returns:
            str: Response from the resource.
        """
        ...


class SCPIProperty:
    """Descriptor for SCPI properties.
    
    Attributes:
        get_cmd (str): Command to get the property value.
        set_cmd (str | None): Command to set the property value. Set to
            `None` for read-only properties. 
    """
    def __init__(self, get_cmd: str, set_cmd: str | None = None,
                 typecast: type = str):
        """Initialize the SCPI property descriptor.
        
        Args:
            get_cmd (str): Command to get the property value.
            set_cmd (str | None): Command to set the property value.
                Set to None for read-only properties.
        """
        self.get_cmd = get_cmd
        self.set_cmd = set_cmd or get_cmd.replace("?", "")
        self.typecast = typecast

    def __get__(self, instance: VISAInterface, owner: type):
        """Get a property value from the instrument.

        Args:
            instance (VISAInterface): Instance of the instrument.
            owner (type): Owner class of the property.
        
        Returns:
            str: The property value.
        """
        if instance is None:
            return self

        get_cmd = self.get_cmd.format(**vars(instance))

        return self.typecast(instance.query(get_cmd))
    
    def __set__(self, instance: VISAInterface, value: Any) -> None:
        """Set a property value on the instrument.
        
        Args:
            instance (VISAInterface): Instance of the instrument.
            value (Any): Value to set for the property.
        """
        set_cmd = self.set_cmd.format(**vars(instance))
        instance.write(f"{set_cmd} {value}")


class Instrument:
    """Base class for instruments using the VISA interface."""
    identity = SCPIProperty("*IDN?")
    complete = SCPIProperty("*OPC?")

    def __init__(self, resource_name: str, label: str | None = None,
                 **kwargs) -> None:
        """Initialize the instrument interface.

        Args:
            resource_name (str): Resource name of the instrument. This
                is the name used by :class:`pyvisa.ResourceManager` to
                identify the instrument.
            label (str | None): Optional label for the instrument.
            kwargs (dict): Additional keyword arguments to forward to 
                :class:`pyvisa.ResourceManager.open_resource()`.

        See also:
            :class:`pyvisa.ResourceManager`: For managing VISA
                resources.
            :class:`pyvisa.Resource`: For interacting with the
                instrument.
        """
        self.label = label or self.__class__.__name__

        try:
            self._rm = pyvisa.ResourceManager()
            logger.debug(
                f"[{self.label}] Opened resource manager: {self._rm}"
            )
        except Exception as e:
            logger.error(
                f"[{self.label}] Failed to open resource manager: {e}"
            )

        try:
            self._resource = self._rm.open_resource(resource_name, **kwargs)
            logger.debug(
                f"[{self.label}] Opened resource: {self._resource}"
            )
        except Exception as e:
            logger.error(
                f"[{self.label}] Failed to open resource: {e}"
            )

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the underlying resource.

        This method allows dynamic access to attributes and methods of
        the underlying VISA resource while logging the calls. If the
        attribute is a method, it returns a wrapper that logs the call
        and its arguments. Set logging level to DEBUG to see the logs.

        Args:
            name (str): Name of the attribute to access.
        
        Returns:
            Any: The attribute value or a callable wrapper if the
                attribute is a method.
        """
        attr = getattr(self._resource, name)

        if not callable(attr):
            return attr
            
        def wrapper(*args, **kwargs):
            """Wrapper to log method calls and their arguments."""
            args_str = " ".join(map(str, args))
            kwargs_str = " ".join(f"{k}={repr(v)}" for k, v in kwargs.items())

            logger.debug(
                f"[{self.label}] Command: {name} | "
                f"Input: {args_str} {kwargs_str}".strip()
            )

            result = attr(*args, **kwargs)

            if result is not None:
                logger.debug(
                    f"[{self.label}] Command: {name} | Output: {result}"
                )

            return result

        return wrapper
    
    def __enter__(self) -> Self:
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type: type[BaseException] | None,
                 exc_value: BaseException | None,
                 traceback: object | None) -> None:
        """Exit the runtime context related to this object."""
        self.close()

    def close(self) -> None:
        """Close the instrument resource and resource manager.
        
        raise:
            Exception: If an error occurs while closing the resource or
                resource manager.
        """
        try:
            logger.debug(
                f"[{self.label}] Closing resource: {self._resource}"
            )
            self._resource.close()
        except Exception as e:
            logger.error(
                f"[{self.label}] Error closing resource: {e}"
            )

        try:
            logger.debug(
                f"[{self.label}] Closing resource manager: {self._rm}"
            )
            self._rm.close()
        except Exception as e:
            logger.error(
                f"[{self.label}] Error closing resource manager: {e}"
            )

    def setup(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(
                    f"{key} is not a valid attribute of "
                    f"{self.__class__.__name__}"
                )

    def reset(self):
        self.write("*RST")

    def clear(self):
        self.write("*CLS")

    def wait(self):
        self.write("*WAI")


class SubSystem:
    """Represents an SCPI subsystem for an instrument.

    Attributes:
        instrument (Instrument): The instrument instance to which the
            subsystem belongs.
        suffix (int): Subsystem suffix.
    """
    def __init__(self, instrument: Instrument, suffix: int) -> None:
        """Initialize the channel.
        
        Args:
            instrument (Instrument): The instrument instance to which
                the subsystem belongs.
            suffix (int): Subsystem suffix.
        """
        self.instrument = instrument
        self.suffix = suffix

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the instrument instance.
        
        Args:
            name (str): Name of the attribute to access.
        
        Returns:
            Any: The attribute value from the instrument instance.
        """
        return getattr(self.instrument, name)

    def setup(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(
                    f"{key} is not a valid attribute of "
                    f"{self.__class__.__name__}"
                )