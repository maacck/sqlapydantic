from typing import Set

from pydantic import BaseModel

from .generator import CustomBaseModel, Generator, GeneratorOptions


def generate_models(
    models: list,
    base_model: CustomBaseModel = BaseModel,
    indentation: str = "    ",
    split_models: bool = False,
    restrict_fields: Set[str] = None,
):
    _generator = Generator(
        base_model=base_model,
        indentation=indentation,
        split_models=split_models,
        restrict_fields=restrict_fields,
    )
    return _generator.generate_models(models)


__all__ = ["Generator", "GeneratorOptions"]
