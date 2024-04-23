import requests
from bs4 import BeautifulSoup
import lxml
import datetime
import re
import config
from num2words import num2words


def time_to_text(time_str):
    num_to_text = {
        '0': 'zero',
        '1': 'one',
        '2': 'two',
        '3': 'three',
        '4': 'four',
        '5': 'five',
        '6': 'six',
        '7': 'seven',
        '8': 'eight',
        '9': 'nine',
        '10': 'ten',
        '11': 'eleven',
        '12': 'twelve',
        '13': 'thirteen',
        '14': 'fourteen',
        '15': 'fifteen',
        '16': 'sixteen',
        '17': 'seventeen',
        '18': 'eighteen',
        '19': 'nineteen',
        '20': 'twenty',
        '30': 'thirty',
        '40': 'forty',
        '50': 'fifty'
    }

    hours, minutes = time_str.split(':')

    hours_text = num_to_text.get(hours, '')

    if int(minutes) < 20:
        minutes_text = num_to_text.get(minutes, '')
    else:
        minutes_text = num_to_text.get(minutes[0] + '0', '')
        if minutes[1] != '0':
            minutes_text += ' ' + num_to_text.get(minutes[1], '')

    time_text = hours_text + ' hours ' if hours_text else ''
    time_text += minutes_text + ' minutes' if minutes_text else ''

    return time_text





def exam_authorization():
    link = 'https://fs.ntu.ac.uk/adfs/ls/?wtrealm=https%3A%2F%2Fservices.ntu.ac.uk%2FTimetabling%2FTimetabling%2F&wctx=WsFedOwinState%3DJ65M_-HnO-Pajp9sV0ddQoXduUrs-503AcNNxnnjIAH4Q0XU4lgmxlmSMIUhlLofPHI38DuUwtpaVZK2Wwn4xoLYIUpsz-O_GlcQIc3ZRSZFx36Wh5YXfztKUs5hzv8wMCDJqh2Q7AJT5M6hWF6HOdY8p8EmMRieBA_L8udkvE8nHkrWKFQIex0W69gug43Q&wa=wsignin1.0&client-request-id=2b61b22e-fe2c-48be-3845-0080010000b4'
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36',
    }

    data = {
        'UserName': config.USER_EMAIL_FOR_AUTHORIZATION,
        'Password': config.USER_PASSWORD_FOR_AUTHORIZATION,
        'AuthMethod': 'FormsAuthentication'
    }  # student's account details
    session = requests.Session()
    response = session.post(link, headers=headers, data=data)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        saml_token = soup.find('input', {'name': 'wresult'}).get('value')
        wctx = soup.find('input', {'name': 'wctx'}).get('value')
        wa = soup.find('input', {'name': 'wa'}).get('value')

        target_url = 'https://services.ntu.ac.uk/Timetabling/Timetabling/Student/ExamTimetable'
        data = {
            'wa': wa,
            'wresult': saml_token,
            'wctx': wctx,

        }
        response = session.post(target_url, data=data, headers=headers, allow_redirects=True)
        if response.status_code == 200:
            cookies = response.cookies

            session_id = cookies.get('ASP.NET_SessionId')
            requestToken = cookies.get('__RequestVerificationToken_L1RpbWV0YWJsaW5nL1RpbWV0YWJsaW5n0')

            return session_id, requestToken, wa, saml_token, wctx

        else:
            print("Failed to access the target page.")
    else:
        print("Authentication failed.")


def get_exam_timetable():
    session_id, requestToken, wa, saml_token, wctx = exam_authorization()  # get authorization cookies
    link = 'https://services.ntu.ac.uk/Timetabling/Timetabling/Student/ExamTimetable'

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }  # headers for browser emulation

    cookies = {
        'Cookie': 'ASP.NET_SessionId=' + session_id + '; __RequestVerificationToken_L1RpbWV0YWJsaW5nL1RpbWV0YWJsaW5n0=' + requestToken + ';'
    }  # cookies from authorization

    data = {
        'wa': wa,
        'wresult': saml_token,
        'wctx': wctx,
    }  # important data from authorization

    session = requests.Session()
    r = session.post(link, headers=headers, data=data, cookies=cookies)
    r2 = session.get(link, headers=headers)
    soup = BeautifulSoup(r2.text, 'lxml')
    table = soup.find("table", class_='timetable')
    if table is None:
        print("TABLE NOT FOUND!!!\n\n\n\n")
    rows = soup.find_all('tr', class_='examItem')
    exam_list = []
    for row in rows:
        cells = row.find_all('td')
        date_with_day = cells[0].get_text(strip=True)
        date = date_with_day.split('-')[1].strip()
        day = int(date.split('/')[0])
        month = date.split('/')[1]
        month_name = datetime.datetime.strptime(month, '%m').strftime('%B')
        formatted_date = f"{num2words(day, ordinal=True).capitalize()} of {month_name}"
        subject = cells[1].get_text(strip=True)
        time = cells[3].get_text(strip=True)
        time_start_txt = time_to_text(time)
        time_end = cells[4].get_text(strip=True)
        time_end_txt = time_to_text(time_end)
        exam_list.append(
            f'Exam for {subject} on {formatted_date}, exam starting at: {time_start_txt} and finishes at {time_end_txt}')
    return exam_list


