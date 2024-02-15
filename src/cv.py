import easyocr
import re
from datetime import datetime

dates = ["січня", "лютого", "березня", "квітня", "травня", "червня", "липня", "серпня", "вересня", "жовтня",
         "листопада", "грудня"]


def get_data(image_path):
    text_ = get_text_from_image(image_path)
    series = get_series_from_text(text_)
    date, year = get_date_and_year_from_text(text_)
    faculty = get_faculty_from_text(text_)
    group = get_group_from_text(text_)
    updated_group = get_updated_group(group, date, year)

    if not series or len(date) != 2 or len(year) != 2 or not date and not year or not faculty or not group:
        return False, "Provided image is invalid"

    if not updated_group:
        return False, "You are not studying anymore"

    return True, {
        "series": series,
        "date": date,
        "year": year,
        "faculty": faculty,
        "group": updated_group
    }


def get_text_from_image(image):
    reader = easyocr.Reader(['uk'], gpu=False)
    text = reader.readtext(image)
    return text


def get_series_from_text(text):
    series = None
    for t in range(len(text) - 1):
        if re.match(r'.*с[ое]рія.*н[ое]м[ое]р.*', text[t][1].lower()):
            series = text[t + 1][1]
            pattern = re.compile(r'^[А-Яа-я]{2}\s(№|.{2})\d+$')
            if pattern.match(series):
                series = series if "№" in series else series[:3] + "№" + series[5:]
            break
    return series


def get_date_and_year_from_text(text):
    date = [t[1] for t in text if any(date1 in t[1].lower() for date1 in dates)]
    year = [re.match(r'\b\d{4}\sр\.?', t[1].lower()).group(0) for t in text if
            re.match(r'\b\d{4}\sр\.?', t[1].lower())]
    return date, year


def get_faculty_from_text(text):
    faculty = ""
    for t_, t in enumerate(text):
        if re.compile(r'форма\s+на[све][чнш]ан[ня]').search(t[1].lower()):
            for i in range(t_ + 1, len(text)):
                if "денна" in text[i][1].lower() or "заочна" in text[i][1].lower():
                    break
                faculty += text[i][1] + " "
            break
    return faculty


def get_group_from_text(text):
    group = next((text[i + 1][1] for i in range(len(text) - 1) if "група" in text[i][1].lower()), None)
    return group


def convert_to_datetime(date_str, year_str):
    day, month = date_str.split()
    month_num = dates.index(month) + 1
    year = int(year_str.split()[0])
    out = datetime(year, month_num, int(day))
    return out


def get_updated_group(group, date, year):
    current_date = datetime.now()
    years_of_studying = current_date.year - int(year[0].split()[0])
    second_date = convert_to_datetime(date[1], year[1])
    if current_date > second_date:
        return False
    return f"{group.split('-')[0]}-{years_of_studying}"
