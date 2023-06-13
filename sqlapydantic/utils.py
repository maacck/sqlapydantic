import inspect

from sqlalchemy.orm import DeclarativeMeta

models_in = []
models = []


def generate_from_module(module, generator):
    for model in dir(module):
        class_ = getattr(module, model)
        if isinstance(getattr(module, model), DeclarativeMeta) and inspect.isclass(
            class_
        ):
            if getattr(class_, "__table__", None) is None:
                continue
            models_in.append(getattr(module, model))


for model in dir(models):
    class_ = getattr(models, model)
    if isinstance(getattr(models, model), DeclarativeMeta) and inspect.isclass(class_):
        if getattr(class_, "__table__", None) is None:
            continue
        models_in.append(getattr(models, model))
