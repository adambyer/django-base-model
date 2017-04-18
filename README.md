# django-base-model
Base class for Django models

- adds created_at, modified_at, and is_deleted fields
- adds hash property for obfuscating database ids
- updates get, all, delete, and filter methods to handle hash and is_deleted
