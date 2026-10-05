import re

from marshmallow import Schema, ValidationError, fields, validate, post_load, pre_load

from models.foldershare import ROLES

from utils.access import to_full_path
from utils.regexes import (
    path_regex,
    path_regex_error,
    folder_regex,
    folder_regex_error,
    file_regex,
    file_regex_error,
    password_regex,
    password_regex_desc,
)


class UserLoginSchema(Schema):
    """Credentials for login. The password is never returned, only accepted."""

    email = fields.Email(required=True, metadata={"example": "user@example.com"})
    password = fields.Str(required=True, load_only=True, metadata={"example": "Secret123!"})


class UserSchema(UserLoginSchema):
    """Registration / account update - enforces the password policy."""

    email = fields.Email(
        required=True,
        validate=validate.Length(max=254),
        metadata={"example": "user@example.com"},
    )
    password = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Regexp(regex=password_regex, error=password_regex_desc),
        metadata={"example": "Secret123!", "description": password_regex_desc},
    )


class CurrentPasswordSchema(Schema):
    """Proof that the account holder is at the keyboard, not just someone
    holding their token - asked before anything that could lock them out of
    their account or take it away."""

    current_password = fields.Str(
        required=True,
        load_only=True,
        metadata={
            "example": "Secret123!",
            "description": "Your password.",
        },
    )


class UpdateUserSchema(UserSchema, CurrentPasswordSchema):
    """`email` and `password` are the new values."""


class UserInfoSchema(Schema):
    email = fields.Str(dump_only=True)
    # False until an activation code is redeemed; the client uses this to decide
    # whether to show the app or the activation screen.
    active = fields.Bool(dump_only=True)


class ActivationSchema(Schema):
    """The code as typed. Formatting (case, dashes, spaces) is normalised
    server-side, so anything the user pastes in is accepted."""

    code = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(max=64),
        metadata={"example": "K7M2-PX94-TB3H-QR8F"},
    )


class AccessTokenSchema(Schema):
    access_token = fields.Str(dump_only=True)


class TokensSchema(AccessTokenSchema):
    refresh_token = fields.Str(dump_only=True)


def _validate_share(value):
    """An empty string is rejected on purpose rather than read as "no share".

    Prevent `DELETE /folder` with `share: ""` from deleting the caller's own
    folder of that name instead of the shared one.
    """
    if value == "":
        raise ValidationError(
            "Leave `share` out, or send null, to work in your own files; an "
            "empty string is not a share."
        )
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", value):
        raise ValidationError("Invalid share.")


class OwnFolderSchema(Schema):
    """A folder in the caller's own files, where `/` is their root."""

    path = fields.Str(
        required=True,
        validate=validate.Regexp(regex=path_regex, error=path_regex_error),
        metadata={
            "example": "/Photos",
            "description": "Folder path, where `/` is the root of your files - "
            "or, with `share`, of the folder shared with you.",
        },
    )

    @post_load
    def _resolve_full_path(self, data, **kwargs):
        data["full_path"] = to_full_path(data["path"], data.get("share"))
        return data


class FolderSchema(OwnFolderSchema):
    """A folder in the caller's own files, or - with `share` - in a folder
    someone shared with them."""

    share = fields.Str(
        load_default=None,
        validate=_validate_share,
        metadata={
            "example": None,
            "description": "Leave out or null for your own files. To work inside a "
            "folder shared with you, its `share` from `GET /folder/shared`.",
        },
    )


class FileUploadSchema(FolderSchema):
    """The multipart upload form: `path` is the destination folder.

    `file` is declared for the docs only, so Swagger renders a file picker.
    webargs' form location reads `request.form`, where the file never appears
    (it lives in `request.files`), so marshmallow cannot require it - the
    handler checks for it instead and answers 400, not 422.
    """

    file = fields.Raw(
        load_only=True,
        metadata={
            "type": "string",
            "format": "binary",
            "description": "The file to upload. Required.",
        },
    )

    # Blank rather than null, so Swagger's pre-filled form works on your own
    # files as sent. A form field cannot hold null at all.
    share = fields.Str(
        load_default=None,
        validate=_validate_share,
        metadata={
            "example": "",
            "description": "Leave empty for your own files. To upload into a "
            "folder shared with you, its `share` from `GET /folder/shared`.",
        },
    )

    @pre_load
    def _blank_share_is_no_share(self, data, **kwargs):
        """An empty `share` means "my own files" here, unlike everywhere else.

        A multipart form carries only strings, so a browser sends an empty one
        for a field left blank and there is no way to express null. Elsewhere an
        empty `share` is rejected as an unset client variable, because leaving
        the field out is easy; in a form it is impossible, so the same emptiness
        means the opposite.
        """
        if data.get("share") == "":
            data = {**data, "share": None}
        return data


class RenameFolderSchema(FolderSchema):
    name = fields.Str(
        required=True,
        validate=validate.Regexp(regex=folder_regex, error=folder_regex_error),
        metadata={"example": "Vacation", "description": "The new name, not a path."},
    )


ROLE_DESCRIPTION = (
    "`read`: view and download. `add`: also create folders and upload new "
    "files. `edit`: also overwrite, rename and delete."
)


# Sharing is owner-only, so its schemas build on OwnFolderSchema.
class UnshareFolderSchema(OwnFolderSchema):
    target_email = fields.Str(required=True, metadata={"example": "friend@example.com"})


class ShareFolderSchema(UnshareFolderSchema):
    role = fields.Str(
        load_default="read",
        validate=validate.OneOf(ROLES),
        metadata={"example": "read", "description": ROLE_DESCRIPTION},
    )


class FolderResponseSchema(Schema):
    folders = fields.Int(dump_only=True)
    files = fields.Int(dump_only=True)


class SharedFolderSchema(Schema):
    """A folder someone else shared with the caller. Only its own name is
    exposed - not where it sits in the owner's files."""

    share = fields.Str(
        dump_only=True,
        metadata={"description": "Pass as `share` to the Folders and Files endpoints."},
    )
    name = fields.Str(dump_only=True)
    owner_email = fields.Str(dump_only=True)
    role = fields.Str(
        dump_only=True,
        metadata={
            "description": "What you may do in it - the best of this share and "
            "any share above it. " + ROLE_DESCRIPTION
        },
    )


class FolderMemberSchema(Schema):
    """A user the folder's owner has granted access to."""

    email = fields.Str(dump_only=True)
    role = fields.Str(dump_only=True)


class FolderEntrySchema(Schema):
    name = fields.Str(dump_only=True)
    type = fields.Str(dump_only=True)
    extension = fields.Str(dump_only=True, allow_none=True)
    size = fields.Int(dump_only=True, allow_none=True)
    folders = fields.Int(dump_only=True, allow_none=True)
    files = fields.Int(dump_only=True, allow_none=True)


class FileSchema(FolderSchema):
    filename = fields.Str(
        required=True,
        metadata={"example": "notes.txt", "description": "The file's name inside `path`."},
    )


class RenameFileSchema(FileSchema):
    name = fields.Str(
        required=True,
        validate=validate.Regexp(regex=file_regex, error=file_regex_error),
        metadata={"example": "notes-final.txt", "description": "The new file name."},
    )


class FileInfoSchema(Schema):
    name = fields.Str(dump_only=True)
    size = fields.Int(dump_only=True)
    modified = fields.Str(dump_only=True)


class DiskUsageSchema(Schema):
    """Capacity of the storage disk, in bytes, plus the upload cut-off."""

    total = fields.Int(dump_only=True)
    used = fields.Int(dump_only=True)
    free = fields.Int(dump_only=True)
    percent_used = fields.Float(dump_only=True)
    limit_percent = fields.Float(dump_only=True)
    uploads_blocked = fields.Bool(dump_only=True)
