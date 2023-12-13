import csv

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import IntegrityError

from recipes.models import Ingredient, Tag
from recipes.constants import (BEGIN_LOAD, LOAD_DONE,
                               LOAD_ENTRIES, INGREDIENTS_CSV_PATH,
                               TAGS_CSV_PATH, LOAD_ENTRIES,
                               UNIQUE_CONSTRAINT)


class Command(BaseCommand):
    """ Импорт таблицы с ингредиентами в базу данных """
    def handle(self, *args, **options):
        to_do_list = ((INGREDIENTS_CSV_PATH, Ingredient),
                      (TAGS_CSV_PATH, Tag))
        for path, model in to_do_list:
            with open(settings.BASE_DIR / path,
                      encoding='utf-8') as file:
                self.stdout.write(BEGIN_LOAD + path, ending='')
                file_reader = csv.DictReader(file)
                created = passed = 0
                for row in file_reader:
                    obj_data = {key: value for key, value in row.items()}
                    try:
                        _, create = model.objects.get_or_create(**obj_data)
                        if create:
                            created += 1
                        else:
                            passed += 1
                    except IntegrityError:
                        passed += 1
                self.stdout.write(LOAD_ENTRIES + str(created), ending='')
                self.stdout.write(UNIQUE_CONSTRAINT + str(passed))
        self.stdout.write(LOAD_DONE)
