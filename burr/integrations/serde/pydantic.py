# try to import to serialize Pydantic Objects
import importlib

import pydantic

from burr.core import serde


@serde.serialize.register(pydantic.BaseModel)
def serialize_pydantic(value: pydantic.BaseModel, **kwargs) -> dict:
    """Uses pydantic to dump the model to a dictionary and then adds the __pydantic_class to the dictionary."""
    _dict = value.model_dump()
    _dict[serde.KEY] = "pydantic"
    # get qualified name of pydantic class. The module name should be fully qualified.
    _dict["__pydantic_class"] = f"{value.__class__.__module__}.{value.__class__.__name__}"
    return _dict


@serde.deserializer.register("pydantic")
def deserialize_pydantic(value: dict, **kwargs) -> pydantic.BaseModel:
    """Deserializes a pydantic object from a dictionary.
    This will pop the __pydantic_class and then import the class.
    """
    value.pop(serde.KEY)
    pydantic_class_name = value.pop("__pydantic_class")
    module_name, class_name = pydantic_class_name.rsplit(".", 1)
    module = importlib.import_module(module_name)
    pydantic_class = getattr(module, class_name)
    return pydantic_class.model_validate(value)
