from django.contrib import admin

from datasets.models import Dataset, DatasetFile, DatasetVersion, Tag

admin.site.register([Dataset, DatasetVersion, DatasetFile, Tag])
