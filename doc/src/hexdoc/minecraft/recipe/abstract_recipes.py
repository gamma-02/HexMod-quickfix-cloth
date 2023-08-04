from typing import Any, Self, cast

from pydantic import ValidationInfo, model_validator

from hexdoc.utils import AnyPropsContext, ResourceLocation, TypeTaggedUnion
from hexdoc.utils.deserialize import load_json_dict


class Recipe(TypeTaggedUnion[AnyPropsContext], group="hexdoc.Recipe", type=None):
    id: ResourceLocation

    group: str | None = None

    @model_validator(mode="before")
    def _pre_root(
        cls,
        values: str | ResourceLocation | dict[str, Any] | Self,
        info: ValidationInfo,
    ):
        """Loads the recipe from json if the actual value is a resource location str."""
        if not info.context or isinstance(values, (dict, Recipe)):
            return values

        # if necessary, convert the id to a ResourceLocation
        match values:
            case str():
                id = ResourceLocation.from_str(values)
            case ResourceLocation():
                id = values

        # load the recipe
        context = cast(AnyPropsContext, info.context)
        for recipe_dir in context["props"].recipe_dirs:
            # TODO: should this use id.namespace somewhere?
            path = recipe_dir / f"{id.path}.json"
            if recipe_dir == context["props"].default_recipe_dir:
                # only load from one file
                values = load_json_dict(path) | {"id": id}
            elif not path.exists():
                # this is to ensure the recipe at least exists on all platforms
                # because we've had issues with that before (eg. Hexal's Mote Nexus)
                raise ValueError(f"Recipe {id} missing from path {path}")

        return values
