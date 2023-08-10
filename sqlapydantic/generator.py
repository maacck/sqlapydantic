import sys
from collections import defaultdict
from importlib import import_module
from textwrap import indent
from typing import Any, ClassVar, Set, TypeVar

from pydantic import BaseModel

# from sqlalchemy import inspect as sa_inspect
import inspect
from sqlalchemy.orm import DeclarativeBase, DeclarativeMeta, Relationship

from sqlapydantic.models import ColumnAttribute, ModelClass

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
        split_models: bool = False,
        restrict_fields: Set[str] = None,
        strict_types: bool = False,
        constraint_str_length: bool = True,
        constraint_int_length: bool = True,
        **kwargs,
    ):
        self.base_model = base_model
        self.imports: dict[str, set[str]] = defaultdict(set)
        if type(self.base_model) != BaseModel:
            self.add_import(self.base_model)
        self.indentation = indentation
        if restrict_fields:
            self.restrict_fields = restrict_fields
        else:
            self.restrict_fields = {"id", "created_at", "updated_at"}
        self.split_models = split_models
        self.strict_types = strict_types
        self.constraint_str_length = constraint_str_length
        self.constraint_int_length = constraint_int_length

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

    def parse_models(self, models_ins: list[DeclarativeBase]) -> list[ModelClass]:
        models: list[ModelClass] = []
        for model_in in models_ins:
            # Get Columns
            model = ModelClass(
                name=model_in.__name__, columns=[], relationship_classes=[]
            )
            for column in model_in.__table__.c:
                model.columns.append(
                    ColumnAttribute(
                        optional=column.nullable is not False,
                        key=column.key,
                        python_type=column.type.python_type.__name__,
                        orm_column=column,
                    )
                )
                self.add_import(column.type.python_type)
            # Get Relationships
            # In Roadmap
            """
            model_relationships = inspect(model_in).relationships.items()
            for rel in model_relationships:
                rel_prop: Relationship = rel[1]
                model.relationship_classes.append(rel_prop.mapper.class_)
            """
            # Split Models
            if self.split_models:
                model_base = ModelClass(name=f"{model_in.__name__}Base", columns=[])
                model_create = ModelClass(
                    name=f"{model_in.__name__}Create",
                    columns=[],
                    parent_class=model_base.name,
                )
                model_update = ModelClass(
                    name=f"{model_in.__name__}Update",
                    columns=[],
                )
                model_read = ModelClass(
                    name=f"{model_in.__name__}Read",
                    columns=[],
                    parent_class=model_base.name,
                )
                model_fields = set(model_in.__table__.columns.keys())
                # Base Columns: not in restrict_fields, create_only_fields, read_only_fields
                create_only_fields = getattr(model_in, "__create_only_fields__", set())
                read_only_fields = getattr(model_in, "__readonly_fields__", set())
                base_fields = (
                    model_fields
                    - self.restrict_fields
                    - set(create_only_fields)
                    - set(read_only_fields)
                )
                for col in model.columns:
                    if col.key not in self.restrict_fields:
                        if col.key in base_fields:
                            model_base.columns.append(col)
                            model_update.columns.append(
                                ColumnAttribute(
                                    **col.dict(exclude={"optional"}), optional=True
                                )
                            )
                        elif col.key in model_in.__create_only_fields__:
                            model_create.columns.append(col)
                        elif col.key in model_in.__readonly_fields__:
                            model_read.columns.append(col)
                    else:
                        model_read.columns.append(col)
                models.append(model_base)
                models.append(model_create)
                models.append(model_update)
                models.append(model_read)
            else:
                models.append(model)

        return models

    def render_column(self, col: ColumnAttribute, manual_optional: bool = False):
        field_type = ""
        python_type = col.python_type
        type_name = python_type.__class__.__name__
        if isinstance(python_type, str) and self.constraint_str_length:
            if (
                hasattr(col.orm_column.type, "length")
                and col.orm_column.type.length is not None
            ):
                self.add_literal_import("pydantic", "constr")
                python_type = "constr(max_length={})".format(col.orm_column.type.length)
        if self.strict_types and type_name in [
            "int",
            "str",
            "bool",
            "bytes",
            "float",
        ]:
            strict_type = f"Strict{type_name.capitalize()}"
            self.add_literal_import("pydantic", strict_type)
            python_type = strict_type
        if col.optional is True or manual_optional is True:
            python_type = f"Optional[{python_type}]"
            field_type = " = None"
            self.add_literal_import("typing", "Optional")
        return f"{col.key}: {python_type}{field_type}"

    def render_class_declaration(self, model: ModelClass) -> str:
        model_name = self.base_model.__name__
        if model.parent_class:
            model_name = model.parent_class
        return f"class {model.name}({model_name}):"

    def render_class(self, model: ModelClass):
        sections = []
        sections.append(self.render_class_declaration(model))
        for column in model.columns:
            sections.append(indent(self.render_column(column), self.indentation))
        if len(model.columns) == 0:
            sections.append(indent("pass", self.indentation))
        return "\n" + "\n".join(sections)

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
            if column.key in self.restrict_fields:
                continue
            sections.append(
                indent(
                    self.render_column(column, manual_optional=True), self.indentation
                )
            )
        return "\n".join(sections)

    def render_read_class(self, model: ModelClass):
        sections = []
        sections.append(self.render_class_declaration(model, name_suffix="Read"))
        for column in model.columns:
            if column.key in self.restrict_fields:
                continue
            sections.append(
                indent(
                    self.render_column(column, manual_optional=True), self.indentation
                )
            )
        return "\n".join(sections)

    def generate_models(self, models, **kwargs):
        sections: list[str] = []

        models_ins = self.parse_models(models)
        for model in models_ins:
            sections.append(self.render_class(model))

        groups = self.group_imports()
        imports = "\n\n".join("\n".join(line for line in group) for group in groups)
        if imports:
            sections.insert(0, imports)

        return "\n\n".join(sections) + "\n"

    def generate_from_module(self, module, output_path: str):
        model_ins = []
        for model in dir(module):
            class_ = getattr(module, model)
            if isinstance(getattr(module, model), DeclarativeMeta) and inspect.isclass(
                class_
            ):
                if getattr(class_, "__table__", None) is None:
                    continue
                model_ins.append(class_)
        file_content = self.generate_models(model_ins)
        with open(output_path, "w") as f:
            f.write(file_content)
