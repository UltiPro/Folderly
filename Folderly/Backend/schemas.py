from marshmallow import Schema, fields


class HelloSchema(Schema):
    name = fields.Str(required=True)
