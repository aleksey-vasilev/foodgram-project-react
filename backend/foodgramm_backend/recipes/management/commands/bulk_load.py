import csv

from django.core.management.base import BaseCommand
from django.conf import settings

from recipes.models import Ingredient, Tag
from recipes.constants import (BEGIN_LOAD, LOAD_DONE,
                               INGREDIENTS_CSV_PATH, TAGS_CSV_PATH,
                               CSV_LOAD_ERROR)


class Command(BaseCommand):
    """ Импорт таблиц csv в базу данных. """

    def handle(self, *args, **options):
        to_do_list = ((INGREDIENTS_CSV_PATH, Ingredient),
                      (TAGS_CSV_PATH, Tag))
        try:
            for path, model in to_do_list:
                obj_list = []
                with open(settings.BASE_DIR / path,
                          encoding='utf-8') as file:
                    self.stdout.write(BEGIN_LOAD + path)
                    file_reader = csv.DictReader(file)
                    number = 0
                    for row in file_reader:
                        obj_data = {key: value for key, value in row.items()}
                        new_obj = model(**obj_data)
                        obj_list.append(new_obj)
                        number += 1
                    model.objects.bulk_create(obj_list, ignore_conflicts=True)
                    self.stdout.write(LOAD_DONE.format(model.__name__, number))
        except Exception as e:
            self.stdout.write(CSV_LOAD_ERROR.format(path, e))
