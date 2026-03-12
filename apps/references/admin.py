from django.contrib import admin
from .models import Department, DocumentType, EducationLevel, Institute, Specialty
from .models import Program
admin.site.register(Institute)
admin.site.register(Department)
admin.site.register(EducationLevel)
admin.site.register(DocumentType)
admin.site.register(Specialty)
admin.site.register(Program)