import csv
import os

from django.core.management.base import BaseCommand

from foodgram.models import Ingredient


class Command(BaseCommand):
    help = 'Loads ingredients from a CSV file'

    def handle(self, *args, **kwargs):
        file_path = os.path.join('foodgram/management/ingredients.csv')

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(
                f'Файл не найден: {file_path}')
            )
            return
        ingredients_to_create = []
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) != 2:
                    self.stdout.write(self.style.WARNING(
                        f'Неверный формат строки: {row}')
                    )
                    continue
                name, measurement_unit = row
                ingredients_to_create.append(
                    Ingredient(
                        name=name.strip(),
                        measurement_unit=measurement_unit.strip()
                    )
                )
            if ingredients_to_create:
                created_ingredients = Ingredient.objects.bulk_create(
                    ingredients_to_create, ignore_conflicts=True
                )

                for ingredient in created_ingredients:
                    self.stdout.write(self.style.SUCCESS(
                        f'Ингредиент добавлен: {ingredient.name}')
                    )
            self.stdout.write(self.style.WARNING('Обработка завершена!'))
