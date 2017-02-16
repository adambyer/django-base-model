from __future__ import unicode_literals
from django.db import models
from hashids import Hashids
from django.conf import settings

class BaseModel(models.Model):
	def __init__(self, *args, **kwargs):
		super(BaseModel, self).__init__(*args, **kwargs)

	class Meta:
		abstract = True

	created_at = models.DateTimeField(auto_now_add=True)
	modified_at = models.DateTimeField(auto_now=True)
	is_deleted = models.BooleanField(default=False)

	@property
	def hash(self):
		if not self.id:
			return None

		hashids = Hashids(salt=settings.SECRET_KEY)
		hash = hashids.encode(self.id)

		return hash

	def id_from_hash(self, hash):
		hashids = Hashids(salt=settings.SECRET_KEY)
		ids = hashids.decrypt(hash)

		if len(ids) > 0:
			return ids[0]

		return None
