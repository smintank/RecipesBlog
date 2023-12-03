import csv

from django.core.management import BaseCommand

from foodgram import settings
from recipes.models import Recipe, Tag
from users.models import User

MODEL_FILE_MAPPING = {
    User: 'users.csv',
    Tag: 'tags.csv',
    Recipe: 'recipes.csv'
}

DEFAULT_PATH = str(settings.BASE_DIR) + '/data/'


class Command(BaseCommand):
    help = 'Команда для загрузки csv файлов в базу данных.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-c', '--clear', action='store_true',
            help='Очистить таблицу перед добавлением данных'
        )

        parser.add_argument(
            '-f', '--files', type=str, nargs='+',
            help='Файлы которые будут загружены'
        )

        parser.add_argument(
            '-p', '--path', type=str,
            help='Путь к загружаемым файлам'
        )

    def handle(self, *args, **options):
        folder_path = options['path'] or DEFAULT_PATH
        file_names = [file if file[-4] == '.csv' else f'{file}.csv'
                      for file in options['files']]

        for model, file_name in MODEL_FILE_MAPPING.items():
            if file_names and file_name not in file_names:
                continue
            file_path = folder_path + file_name
            with open(file_path, newline='\n', encoding='utf-8') as file:
                data = csv.DictReader(file)
                values = [model(row) for row in data]
                if options['clear']:
                    model.objects.all().delete()
                model.objects.bulk_create(values)
                self.stdout.write(self.style.SUCCESS(f'{file_name} is loaded'))
