from __future__ import annotations

from graphene import Boolean, DateTime, Field, InputObjectType, Int, ObjectType, String
from graphene.types.generic import GenericScalar

from infrahub.core import registry

from .interface import InfrahubInterface


class RelatedNodeInput(InputObjectType):
    id = String(required=True)
    _relation__is_visible = Boolean(required=False)
    _relation__is_protected = Boolean(required=False)
    _relation__owner = String(required=False)
    _relation__source = String(required=False)


class AttributeInterface(InfrahubInterface):
    is_inherited = Field(Boolean)
    is_protected = Field(Boolean)
    is_visible = Field(Boolean)
    updated_at = Field(DateTime)
    # Since source and owner are using a Type that is generated dynamically
    # these 2 fields will be dynamically inserted when we generate the GraphQL Schema
    # source = Field("DataSource")
    # owner = Field("DataOwner")


class BaseAttribute(ObjectType):
    id = Field(String)

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        registry.default_graphql_type[cls.__name__] = cls


class TextAttributeType(BaseAttribute):
    value = Field(String)

    class Meta:
        description = "Attribute of type Text"
        name = "TextAttribute"
        interfaces = {AttributeInterface}


class NumberAttributeType(BaseAttribute):
    value = Field(Int)

    class Meta:
        description = "Attribute of type Number"
        name = "NumberAttribute"
        interfaces = {AttributeInterface}


class CheckboxAttributeType(BaseAttribute):
    value = Field(Boolean)

    class Meta:
        description = "Attribute of type Checkbox"
        name = "CheckboxAttribute"
        interfaces = {AttributeInterface}


class StrAttributeType(BaseAttribute):
    value = Field(String)

    class Meta:
        description = "Attribute of type String"
        name = "StrAttribute"
        interfaces = {AttributeInterface}


class IntAttributeType(BaseAttribute):
    value = Field(Int)

    class Meta:
        description = "Attribute of type Integer"
        name = "IntAttribute"
        interfaces = {AttributeInterface}


class BoolAttributeType(BaseAttribute):
    value = Field(Boolean)

    class Meta:
        description = "Attribute of type Boolean"
        name = "BoolAttribute"
        interfaces = {AttributeInterface}


class ListAttributeType(BaseAttribute):
    value = Field(GenericScalar)

    class Meta:
        description = "Attribute of type List"
        name = "ListAttribute"
        interfaces = {AttributeInterface}


class JSONAttributeType(BaseAttribute):
    value = Field(GenericScalar)

    class Meta:
        description = "Attribute of type JSON"
        name = "JSONAttribute"
        interfaces = {AttributeInterface}


class AnyAttributeType(BaseAttribute):
    value = Field(GenericScalar)

    class Meta:
        description = "Attribute of type GenericScalar"
        name = "AnyAttribute"
        interfaces = {AttributeInterface}
