# TO DO
from marshmallow import Schema, fields, validate

from utils.regexes import path_regex, path_regex_error, folder_regex, folder_regex_error


class HelloSchema(Schema):
    name = fields.Str(required=True)


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    email = fields.Str(required=True)
    password = fields.Str(required=True)


class FolderSchema(Schema):
    root = fields.Str(required=True)
    path = fields.Str(
        required=True,
        validate=validate.Regexp(regex=path_regex, error=path_regex_error),
    )


class UpdateFolderSchema(FolderSchema):
    name = fields.Str(
        required=True,
        validate=validate.Regexp(regex=folder_regex, error=folder_regex_error),
    )


class FolderResponseSchema(Schema):
    folders = fields.Int(dump_only=True)
    files = fields.Int(dump_only=True)


"""class FolderFileSchema(Schema):
    files = fields."""


class FileSchema(Schema):
    name = fields.Str(dump_only=True)
