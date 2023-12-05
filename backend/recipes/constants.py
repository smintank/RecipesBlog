
class Limits:
    MAX_STANDARD_FIELD_LENGTH = 200
    MIN_STANDARD_VALUE = 1
    MAX_COOKING_TIME = 600
    MAX_AMOUNT = 10000
    MAX_USER_FIELDS_LENGTH = 150


class Messages:
    ALREADY_EXISTING_ERROR = 'Это запись уже существует'
    REQUIRED_FIELD_ERROR = 'Обязательное поле'
    NOT_UNIQUE_ERROR = 'Значения должны быть уникальными'
    NOT_EXISTING_ERROR = 'Нельзя удалить несуществующую запись'
    SUBSCRIBE_BY_YOURSELF_ERROR = 'Вы не можете быть подписаны на себя'


class PdfSettings:
    FILE_NAME = 'groceries.pdf'
    TITLE_TEXT = 'Список покупок'
    TITLE_X_Y = (230, 800)
    FONT = 'Roboto-Regular'
    FONT_PATH = 'Roboto-Regular.ttf'
    TITLE_FONT_SIZE = 16
    TEXT_FONT_SIZE = 12
    INGREDIENT_X = 70
    AMOUNT_X = 450
    ROW_START_Y = 760
    ROW_SHIFT_Y = 25
