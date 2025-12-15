from django.db import models

class Role(models.Model):
    name = models.CharField('Название', max_length=50, unique=True)
    slug = models.SlugField('Слаг', max_length=50, unique=True)


    class Meta:
        db_table = 'role'

    def __str__(self):
        return self.name
