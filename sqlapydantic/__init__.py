from typing import Set

from pydantic import BaseModel

from .generator import CustomBaseModel, Generator, GeneratorOptions


def generate_models(
    models: list,
    base_model: CustomBaseModel = BaseModel,
    indentation: str = "    ",
    split_models: bool = False,
    restrict_fields: Set[str] = None,
    strict_types: bool = False,
    constraint_str_length: bool = True,
    constraint_int_length: bool = True,
):
    _generator = Generator(
        base_model=base_model,
        indentation=indentation,
        split_models=split_models,
        restrict_fields=restrict_fields,
        strict_types=strict_types,
        constraint_str_length=constraint_str_length,
        constraint_int_length=constraint_int_length,
    )
    return _generator.generate_models(models)


__all__ = ["Generator", "GeneratorOptions"]
