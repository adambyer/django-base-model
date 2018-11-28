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
        return super().get(*args, **kwargs)

    @hash_decorator
    def filter(self, *args, **kwargs):
        """
        NOTE: cannot filter is_deleted because it's already False in the base query (get_queryset)
        """
        return super().filter(*args, **kwargs)

    @hash_decorator
    def exclude(self, *args, **kwargs):
        """
        NOTE: cannot exclude is_deleted because it's already False in the base query (get_queryset)
        """
        return super().exclude(*args, **kwargs)

    @classmethod
    def id_from_hash(cls, hsh):
        hashids = Hashids(salt=settings.SECRET_KEY)
        ids = hashids.decrypt(hsh)

        if len(ids) > 0:
            return ids[0]

        return None


class BaseModelManager(models.Manager.from_queryset(BaseModelQuerySet)):
    def get_queryset(self):
        return super().get_queryset().exclude(is_deleted=True)


class BaseAdminModelManager(models.Manager):
    """admin methods need their own model manager to bypass is_deleted functionality"""
    pass


class BaseModel(models.Model):
    class Meta:
        abstract = True

    class Options:
        fake_delete = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    objects = BaseModelManager()
    admin_objects = BaseAdminModelManager()

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        if self.Options.fake_delete and not kwargs.get('hard', False):
            self.is_deleted = True
            self.save(update_fields=['is_deleted'])
            return 1

        kwargs.pop('hard', None)
        return super().delete(*args, **kwargs)

    @staticmethod
    def get_hash_from_id(id):
        hashids = Hashids(salt=settings.SECRET_KEY)
        h = hashids.encode(id)

        return h

    @property
    def hash(self):
        if not self.pk:
            return None

        return self.get_hash_from_id(self.pk)


class BaseModelAdmin(ModelAdmin):
    list_display = ('pk', 'hash', 'created_at', 'is_deleted')

    fieldsets = (
        ('Base', {'fields': ('pk', 'hash', 'created_at', 'modified_at', 'is_deleted')}),
    )

    readonly_fields = ('pk', 'hash', 'created_at', 'modified_at')
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
