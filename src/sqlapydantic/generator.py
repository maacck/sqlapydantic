import sys
from collections import defaultdict
from importlib import import_module
from textwrap import indent
from typing import TypeVar, Any, ClassVar, Set

from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase

from sqlapydantic.models import ModelClass, ColumnAttribute

CustomBaseModel = TypeVar("CustomBaseModel", bound=BaseModel)

IntPrimaryKey = int


class GeneratorOptions(BaseModel):
    constraint_str_length: bool = True
    constraint_int_length: bool = True


class Generator(object):
    imports = []
    builtin_module_names: ClassVar[set[str]] = set(sys.builtin_module_names) | {
        "dataclasses"
    }

    def __init__(
            self,
            base_model: CustomBaseModel = BaseModel,
            indentation: str = "    ",
            sys_fields: Set[str] = None,
            **kwargs):
        self.base_model = base_model
        self.imports: dict[str, set[str]] = defaultdict(set)
        if type(self.base_model) != BaseModel:
            self.add_import(self.base_model)
        self.indentation = indentation
        if sys_fields:
            self.sys_fields = sys_fields
        else:
            self.sys_fields = {'id', 'created_at', 'updated_at'}

    def add_import(self, obj: Any) -> None:
        # Don't store builtin imports
        if getattr(obj, "__module__", "builtins") == "builtins":
            return

        type_ = type(obj) if not isinstance(obj, type) else obj
        pkgname = type_.__module__

        # The column types have already been adapted towards generic types if possible,
        # so if this is still a vendor specific type (e.g., MySQL INTEGER) be sure to
        # use that rather than the generic sqlalchemy type as it might have different
        # constructor parameters.
        if pkgname.startswith("sqlalchemy.dialects."):
            dialect_pkgname = ".".join(pkgname.split(".")[0:3])
            dialect_pkg = import_module(dialect_pkgname)

            if type_.__name__ in dialect_pkg.__all__:
                pkgname = dialect_pkgname
        else:
            pkgname = type_.__module__

        self.add_literal_import(pkgname, type_.__name__)

    def add_literal_import(self, pkgname: str, name: str) -> None:
        names = self.imports.setdefault(pkgname, set())
        names.add(name)

    def group_imports(self) -> list[list[str]]:
        future_imports: list[str] = []
        stdlib_imports: list[str] = []
        thirdparty_imports: list[str] = []

        for package in sorted(self.imports):
            imports = ", ".join(sorted(self.imports[package]))
            collection = thirdparty_imports
            if package == "__future__":
                collection = future_imports
            elif package in self.builtin_module_names:
                collection = stdlib_imports
            elif package in sys.modules:
                if "site-packages" not in (sys.modules[package].__file__ or ""):
                    collection = stdlib_imports

            collection.append(f"from {package} import {imports}")

        return [
            group
            for group in (future_imports, stdlib_imports, thirdparty_imports)
            if group
        ]

    def generate(self, model: DeclarativeBase, **kwargs):
        sections: list[str] = []

        models = self.generate_models([model])
        for model in models:
            sections.append(self.render_class(model))

        groups = self.group_imports()
        imports = "\n\n".join("\n".join(line for line in group) for group in groups)
        if imports:
            sections.insert(0, imports)

        return "\n\n".join(sections) + "\n"

    def generate_models(self, models_in: list[DeclarativeBase]) -> list[ModelClass]:
        models: list[ModelClass] = []
        for model_in in models_in:
            model = ModelClass(name=model_in.__name__, columns=[])
            # Get Columns
            for column in model_in.__table__.c:
                self.add_import(column.type.python_type)
                model.columns.append(
                    ColumnAttribute(
                        optional=column.nullable is False,
                        key=column.key,
                        type_hint=column.type.python_type.__name__,
                    )
                )
            # Get Relationships
            """
            model_relationships = inspect(model_in).relationships.items()
            for rel in model_relationships:
                rel_prop: Relationship = rel[1]
                print(rel_prop.entity.columns)
            """
            models.append(model)
        return models

    def render_column(self, col: ColumnAttribute, manual_optional: bool = False):
        type_hint = col.type_hint
        if col.optional is True or manual_optional is True:
            type_hint = f"Optional[{col.type_hint}]"
            self.add_literal_import("typing", "Optional")
        return f"{col.key}: {type_hint}"

    def render_class_declaration(self, model: ModelClass, name_suffix="") -> str:
        return f"class {model.name}{name_suffix.strip()}({self.base_model.__name__}):"

    def render_class(self, model: ModelClass):
        sections = []
        sections.append(self.render_class_declaration(model))
        for column in model.columns:
            sections.append(indent(self.render_column(column), self.indentation))
        return "\n".join(sections)

    def render_base_class(self, model: ModelClass):
        sections = []
        sections.append(self.render_class_declaration(model, name_suffix="Base"))
        for column in model.columns:
            sections.append(indent(self.render_column(column), self.indentation))
        return "\n".join(sections)

    def render_update_class(self, model: ModelClass):
        sections = []
        sections.append(self.render_class_declaration(model, name_suffix="Update"))
        for column in model.columns:
            if column.key in self.sys_fields:
                continue
            sections.append(indent(self.render_column(column, manual_optional=True), self.indentation))
        return "\n".join(sections)

    def render_read_class(self, model: ModelClass):
        sections = []
        sections.append(self.render_class_declaration(model, name_suffix="Read"))
        for column in model.columns:
            if column.key in self.sys_fields:
                continue
            sections.append(indent(self.render_column(column, manual_optional=True), self.indentation))
        return "\n".join(sections)