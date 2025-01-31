import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Указываем область доступа (права)
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# Указываем правильный путь к файлу с ключами
creds = ServiceAccountCredentials.from_json_keyfile_name(r"C:\python_projects\projecktfoto.json", scope)

# Авторизуемся в Google Sheets API
client = gspread.authorize(creds)

# Открываем таблицу по названию
spreadsheet = client.open("Проект фото")  # Замените на фактическое название вашей таблицы
sheet = spreadsheet.worksheet("Проект фото")  # Открываем лист с таким же названием

# Читаем данные из таблицы
data = sheet.get_all_records()  # Получаем все данные в виде списка словарей

# Выводим данные в консоль
print("Данные из таблицы:", data)

