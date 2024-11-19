import csv

from django.core.management.base import BaseCommand

from foodgram.models import Ingredient


class Command(BaseCommand):
    help = 'Loads ingredients from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str,
                            help='The path to the CSV file with ingredients')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

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
