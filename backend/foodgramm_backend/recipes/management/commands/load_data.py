import csv

from django.core.management.base import BaseCommand
from django.conf import settings

from recipes.models import Ingredient, Tag
from recipes.constants import (BEGIN_LOAD, LOAD_DONE,
                               INGREDIENTS_CSV_PATH, TAGS_CSV_PATH,
                               CSV_LOAD_ERROR, UNIQUE_CONSTRANT)


class Command(BaseCommand):
    """ Импорт таблиц csv в базу данных. """

    def handle(self, *args, **options):
        to_do_list = ((INGREDIENTS_CSV_PATH, Ingredient),
                      (TAGS_CSV_PATH, Tag))
        try:
            for path, model in to_do_list:
                with open(settings.BASE_DIR / path,
                          encoding='utf-8') as file:
                    self.stdout.write(BEGIN_LOAD + path)
                    file_reader = csv.DictReader(file)
                    number = 0
                    for row in file_reader:
                        obj_data = {key: value for key, value in row.items()}
                        number += 1
                        _, create = model.objects.get_or_create(**obj_data)
                        if not create:
                            self.stdout.write(UNIQUE_CONSTRANT.format(
                                number, model.__name__))
                    self.stdout.write(LOAD_DONE.format(model.__name__, number))
        except Exception as e:
            self.stdout.write(CSV_LOAD_ERROR.format(path, e))
