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

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) != 2:
                    self.stdout.write(self.style.WARNING(
                        f'Неверный формат строки: {row}')
                    )
                    continue
                name, measurement_unit = row
                # Создаем или обновляем ингредиент
                ingredient, created = Ingredient.objects.get_or_create(
                    name=name.strip(),
                    measurement_unit=measurement_unit.strip()
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f'Ингредиент добавлен: {ingredient.name}')
                    )
                else:
                    self.stdout.write(self.style.WARNING(
                        f'Ингредиент уже существует: {ingredient.name}')
                    )
