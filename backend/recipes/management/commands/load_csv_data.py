import csv

from django.core.management import BaseCommand

from foodgram import settings
from recipes.models import Ingredient


MODEL_FILE_MAPPING = {
    Ingredient: 'ingredients.csv'
}

MODEL_HEADERS_MAPPING = {
    Ingredient: ('name', 'measurement_unit')
}


class Command(BaseCommand):
    help = 'Команда для загрузки csv файлов в базу данных.'

    def handle(self, *args, **options):
        folder_path = str(settings.BASE_DIR) + '/data/'
        for model, file_name in MODEL_FILE_MAPPING.items():
            file_path = folder_path + file_name
            with open(file_path,
                      newline='\n',
                      encoding='utf-8') as file:
                data = csv.DictReader(
                    file, fieldnames=MODEL_HEADERS_MAPPING[model]
                )
                values = [model(**row) for row in data]
                model.objects.all().delete()
                model.objects.bulk_create(values)
                self.stdout.write(self.style.SUCCESS(f'{file_name} is loaded'))
