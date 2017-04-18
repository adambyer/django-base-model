from django.db import models
from django.conf import settings

from hashids import Hashids


class BaseModelQuerySet(models.query.QuerySet):
    def get(self, *args, **kwargs):
        hash = kwargs.get('hash')

        if hash:
            del kwargs['hash']
            kwargs['id'] = self.id_from_hash(hash)

        return super().get(**kwargs)

    def all(self):
        return super().exclude(is_deleted=True)

    def filter(self, *args, **kwargs):
        if kwargs.get('is_deleted') is None and kwargs.get('is_deleted__exact') is None:
            kwargs.pop('is_deleted', None)
            kwargs['is_deleted__exact'] = False

        return super().filter(**kwargs)

    def exclude(self, *args, **kwargs):
        if kwargs.get('is_deleted') is None and kwargs.get('is_deleted__exact') is None:
            kwargs.pop('is_deleted', None)
            kwargs['is_deleted__exact'] = True

        return super().exclude(**kwargs)

    @classmethod
    def id_from_hash(cls, hsh):
        hashids = Hashids(salt=settings.SECRET_KEY)
        ids = hashids.decrypt(hsh)

        if len(ids) > 0:
            return ids[0]

        return None


class BaseModelManager(models.Manager.from_queryset(BaseModelQuerySet)):
    pass


class BaseAdminModelManager(models.Manager):
    """admin methods needs their own model manager to bypass is_deleted functionality"""
    pass


class BaseModel(models.Model):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(BaseModel, self).__init__(*args, **kwargs)

    objects = BaseModelManager()
    admin_objects = BaseAdminModelManager()

    fake_delete = True

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        if self.fake_delete:
            self.is_deleted = True
            self.save()
            return 1

        return super().delete(*args, **kwargs)

    @property
    def hash(self):
        if not self.id:
            return None

        hashids = Hashids(salt=settings.SECRET_KEY)
        h = hashids.encode(self.id)

        return h
