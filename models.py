from django.db import models
from django.conf import settings
from django.contrib.admin import ModelAdmin

from hashids import Hashids


def hash_decorator(func):
    def wrapper(*args, **kwargs):
        instance = args[0]  # first arg is the instance
        hsh = kwargs.get('hash')

        if hsh:
            del kwargs['hash']
            kwargs['pk'] = instance.id_from_hash(hsh)

        return func(*args, **kwargs)

    return wrapper


class BaseModelQuerySet(models.query.QuerySet):
    @hash_decorator
    def get(self, *args, **kwargs):
        return super().get(**kwargs)

    def all(self):
        # exclude is_deleted records
        return super().exclude(is_deleted=True)

    @hash_decorator
    def filter(self, *args, **kwargs):
        # allow filtering by is_deleted if specified, otherwise exclude them
        if kwargs.get('is_deleted') is None and kwargs.get('is_deleted__exact') is None:
            kwargs.pop('is_deleted', None)
            kwargs['is_deleted__exact'] = False

        return super().filter(**kwargs)

    @hash_decorator
    def exclude(self, *args, **kwargs):
        # allow excluding by is_deleted if specified, otherwise exclude them
        if kwargs.get('is_deleted') is None and kwargs.get('is_deleted__exact') is None:
            kwargs.pop('is_deleted', None)
            kwargs['is_deleted__exact'] = False

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
    """admin methods need their own model manager to bypass is_deleted functionality"""
    pass


class BaseModel(models.Model):
    class Meta:
        abstract = True

    class Options:
        fake_delete = False

    def __init__(self, *args, **kwargs):
        super(BaseModel, self).__init__(*args, **kwargs)

    objects = BaseModelManager()
    admin_objects = BaseAdminModelManager()

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        if self.Options.fake_delete:
            self.is_deleted = True
            self.save()
            return 1

        return super().delete(*args, **kwargs)

    def hard_delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)

    @property
    def hash(self):
        if not self.pk:
            return None

        hashids = Hashids(salt=settings.SECRET_KEY)
        h = hashids.encode(self.pk)

        return h


class BaseModelAdmin(ModelAdmin):
    readonly_fields = ('created_at', 'modified_at')

    list_display = ('created_at', 'is_deleted')

    fieldsets = (
        ('Base', {'fields': ('created_at', 'modified_at', 'is_deleted')}),
    )

    list_filter = ('is_deleted',)

    def get_queryset(self, request):
        """
        this was taken directly from ModelAdmin:get_queryset
        updated self.model._default_manager to self.model.admin_objects
        to bypass BaseModel is_deleted functionality
        """
        qs = self.model.admin_objects.get_queryset()
        ordering = self.get_ordering(request)

        if ordering:
            qs = qs.order_by(*ordering)

        return qs
