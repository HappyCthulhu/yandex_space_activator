import re

import yaml
import sys
import os
import time
from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException

logger.remove()


# настраиваем логгирование

def debug_only(record):
    return record["level"].name == "DEBUG"


def critical_only(record):
    return record["level"].name == "CRITICAL"


def info_only(record):
    return record["level"].name == "INFO"


logger_format_debug = "<green>{time:DD-MM-YY HH:mm:ss}</> | <bold><blue>{level}</></> | " \
                      "<cyan>{file}:{function}:{line}</> | <blue>{message}</> | <blue>🛠</>"
logger_format_info = "<green>{time:DD-MM-YY HH:mm:ss}</> | <bold><fg 255,255,255>{level}</></> | " \
                     "<cyan>{file}:{function}:{line}</> | <fg 255,255,255>{message}</> | <fg 255,255,255>✔</>"
logger_format_critical = "<green>{time:DD-MM-YY HH:mm:ss}</> | <RED><fg 255,255,255>{level}</></> " \
                         "| <cyan>{file}:{function}:{line}</> | <fg 255,255,255><RED>{message}</></> | " \
                         "<RED><fg 255,255,255>❌</></>"

logger.add(sys.stderr, format=logger_format_debug, level='DEBUG', filter=debug_only)
logger.add(sys.stderr, format=logger_format_info, level='INFO', filter=info_only)
logger.add(sys.stderr, format=logger_format_critical, level='CRITICAL', filter=critical_only)



def email_appointment(emails_list):
    email_login_pass = emails_list[0]
    email_login_pass_list = email_login_pass.split(':')
    del emails_list[0]
    email_login = email_login_pass_list[0]
    email_pass = email_login_pass_list[1]
    email_phone_number = email_login_pass_list[2]
    logger.debug(f'Взяли почту: {email_login}')
    return email_login, email_pass, email_phone_number, emails_list


def authorization_in_yandex(email_login, email_pass, email_phone_number):
    driver.get('https://passport.yandex.ru/auth')
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#passp-field-login')))
    driver.find_element_by_css_selector('#passp-field-login').send_keys(email_login)
    driver.find_element_by_css_selector('[type="submit"]').click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#passp-field-passwd')))
    driver.find_element_by_css_selector('#passp-field-passwd').send_keys(email_pass)
    driver.find_element_by_css_selector('[type="submit"]').click()
    time.sleep(2)

    if 'challenge' in driver.current_url:
        driver.find_element_by_css_selector('#passp-field-phone').send_keys(email_phone_number)
        driver.find_element_by_css_selector('[type="submit"]').click()

    return email_login

no_space_count = 0

with open('.' + os.path.join(os.sep, 'text_files', 'emails.yml'), 'r', encoding='utf-8-sig') as emails_file:
    emails_list = yaml.load(emails_file, Loader=yaml.FullLoader)

logger.info(f'Аккаунтов в файле: {len(emails_list)}')

for i in range(len(emails_list)):
    email_login, email_pass, email_phone, emails_list = email_appointment(emails_list)

    driver = webdriver.Chrome(executable_path='/home/valera/PycharmProjects/wordstat_hack/chromedriver')
    authorization_in_yandex(email_login, email_pass, email_phone)

    driver.get('https://disk.yandex.ru/')

    driver.get('https://mail.yandex.ru/?enable_mail_pro=1#inbox')
    driver.get('https://mail.yandex.ru/?enable_mail_pro=1#inbox')


    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//div[@class="MailProOnboardingStep-Actions"]/button[@type="button"]')))
        driver.find_element_by_xpath('//div[@class="MailProOnboardingStep-Actions"]/button[@type="button"]').click()

    except TimeoutException:
        logger.critical('Не было уведомления')
        pass

    time.sleep(1)


    driver.get('https://disk.yandex.ru/')
    time.sleep(3)

    disk_space_elem = driver.find_element_by_xpath('//div[@class="info-space__footer"]/div[@class="info-space__text"]').text
    logger.debug(f'Размер дискового пространства: {disk_space_elem}')


    disk_space = re.findall('\d+', disk_space_elem)[0]
    if int(disk_space) < 15:
        logger.critical('Простраства меньше, чем должно быть')
        no_space_count += 1

    else:
        logger.debug('Необходимое количество пространства получено')


    driver.delete_all_cookies()
    driver.quit()

logger.info(f'Неактивированных аккаунтов: {no_space_count}')