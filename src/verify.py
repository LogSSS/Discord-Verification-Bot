import asyncio
import discord
import base64
import urllib.parse
import time
import re
from io import BytesIO
from PIL import Image
from selenium import webdriver


async def verify_by_card(data, message, bot):
    json_data = await get_json_data(data, message, bot)
    if not json_data[0]:
        return False, json_data[1]
    json = json_data[1]
    new_data = await get_data_from_json(json, data)
    return True, new_data


async def get_data_from_json(json_data, data):
    return_data = {
        "series": json_data["documentSeries"] + " №" + json_data["documentNumber"],
        "name": json_data["fio"],
        "expired": json_data["documentExpiredDate"],
        "faculty": data["faculty"],
        "group": data["group"]
    }
    return return_data


async def get_json_data(data, message, bot):
    base_url = base64.b64decode("aHR0cHM6Ly9pbmZvLmVkYm8uZ292LnVhL3N0dWRlbnQtdGlja2V0cy8=").decode('utf-8')
    url = urllib.parse.unquote(base_url)
    driver = await get_driver()
    driver.get(url)
    captcha = await get_captcha_text(driver, message, bot, 0)
    if captcha[0]:
        captcha = captcha[1]
    else:
        driver.quit()
        return False, captcha[1]
    data = await get_proper_old_data(data, captcha)
    for key, value in data.items():
        element = driver.find_element_by_id(key)
        if key == "skipMiddleName":
            if value.lower() == "true":
                if not element.is_selected():
                    element.click()
            elif value.lower() == "false":
                if element.is_selected():
                    element.click()
        else:
            element.send_keys(value)

    with open("src/data/script.js", "r") as file:
        js_function = file.read()

    result = driver.execute_async_script(js_function)
    result = {key: value for key, value in result.items() if value != ''}
    driver.quit()
    res = await check_result(result)
    if not res[0]:
        return False, res[1]
    return True, result


async def check_result(result):
    if "Data encryption error" == result:
        return False, "Data encryption error"
    if "No data found" == result:
        return False, "No data"
    if "Активний" != result["documentStatus"]:
        return False, "Document is not active"
    if "Активний" != result["documentStatusActive"]:
        return False, "Document is not active"
    if "Прикарпатський національний університет імені Василя Стефаника" != result["universityName"]:
        return False, "You are not a student of the PNU"
    if result["documentExpiredDate"] < time.strftime("%d.%m.%Y"):
        return False, "Document is expired"
    if 1 == result["documentExists"]:
        return True, result
    return False, result


async def get_proper_old_data(data, captcha):
    series = data["series"]
    docMatches = re.match(r'([А-Яа-я]+) №(\d+)', series)
    documentSeries = docMatches.group(1)
    documentNumber = docMatches.group(2)

    name = data["name"]
    nameMatches = re.match(r'(\S+)\s+(\S+)\s*(\S*)', name)

    lastName = nameMatches.group(1)
    firstName = nameMatches.group(2)
    middleName = nameMatches.group(3)
    skipMiddleName = "false" if middleName else "true"

    return {
        "documentSeries": documentSeries,
        "documentNumber": documentNumber,
        "lastName": lastName,
        "firstName": firstName,
        "middleName": middleName,
        "skipMiddleName": skipMiddleName,
        "captcha": captcha
    }


async def get_captcha(driver, refresh=False):
    if refresh:
        refresh_but = driver.find_element_by_id("imgCaptcha")
        driver.execute_script("arguments[0].click();", refresh_but)
        time.sleep(2)
    img = driver.find_element_by_id("imgCaptcha")
    img_data = img.screenshot_as_base64
    img_data_bytes = base64.b64decode(img_data)
    img = Image.open(BytesIO(img_data_bytes))
    width, height = img.size
    img = img.crop((0, 0, width, height - 12))
    img_bytesio = BytesIO()
    img.save(img_bytesio, format="PNG")
    img_bytesio.seek(0)
    return discord.File(img_bytesio, filename="captcha.png")


async def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(executable_path="venv/Lib/chromedriver.exe", options=options)
    return driver


async def get_captcha_text(driver, message, bot, c):
    if c > 10:
        driver.quit()
        return False, "You have refresh the captcha too many times. Please try again by uploading the document again"
    bool_user_response = False
    if c != 0:
        file = await get_captcha(driver, True)
    else:
        file = await get_captcha(driver)
    await message.channel.send(
        "Please, enter the captcha. U have 60 seconds\nTo change captcha type \"!refresh\"" +
        f"\nU have {10 - c} refreshes left",
        file=file)

    while not bool_user_response:
        def check(m):
            return m.author == message.author and m.channel == message.channel

        try:
            user_response = await bot.wait_for("message", check=check, timeout=60)
        except asyncio.TimeoutError:
            driver.quit()
            return False, "You didn't enter the captcha\nResend the document and try again"
        if user_response.content.lower() == "!refresh":
            c += 1
            return await get_captcha_text(driver, message, bot, c)

        if len(user_response.content) == 4 and user_response.content.lower().isalnum():
            return True, user_response.content
        else:
            await message.channel.send("Input must be 4 characters long and contain only numbers and letters")


async def verify_by_qr(link):
    print(link)
    return True, "Current version of the bot does not support this feature, cause we haven't access to the DIYA API"
