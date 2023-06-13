# sqlapydantic

Generate Pydantic Model from SQLAlchemy Model

This package is helpful while building web apps with FastAPI and SQLAlchemy. It generates Pydantic Model from SQLAlchemy Model.


Installation
============

To install,

    pip install sqlapydantic


Quickstart
==========

You may use `generate_models` function directly to generate Pydantic Model from SQLAlchemy Model. It takes `Generator`'s init arguments and init a Generator class. 

Examples:

```python
    from sqlapydantic import generate_model
    
    generate_model(models=[MyModel], base_model=CustomBaseModel)

```

```python
from  sqlapydantic import Generator

generator = Generator(base_model=CustomBaseModel)
generator.generate_from_module(models=my_models_module, output_path="schemas.py")
```


Generator Class takes following init arguments
- `split_models`: Whether to split models into Base, Create, Update and Read models. Default is `Fakse`.
- `base_model`: Base model to inherit from. Default is `BaseModel` from `pydantic`.
- `restrict_fields`: Which takes a `set` of fields to restrict. Default is `None`. This is useful when you want to restrict some fields to be readonly such as id, created_at, updated_at.
- `indentation`: Indentation to use in generated code.


## RoadMap
-  Strict typing, such as using `conint` for limiting `Integer` size and `constr` for `String` length.
-  Probably, generate relationships as well.
