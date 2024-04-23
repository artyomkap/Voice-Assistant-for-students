import requests
from bs4 import BeautifulSoup
import lxml
import datetime
import re
from http.cookies import SimpleCookie
import config


def increment_variable_every_monday(start_date, variable):
    current_date = datetime.datetime.now()

    start_of_current_week = start_date - datetime.timedelta(days=start_date.weekday())

    if current_date.weekday() == 0 and current_date.date() > start_date.date():
        variable += 1

    return variable


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


def authorization():
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

        target_url = 'https://services.ntu.ac.uk/Timetabling/Timetabling/Student/WeeklyTimetable'
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


def get_timetable_this_week():
    session_id, requestToken, wa, saml_token, wctx = authorization()  # get authorization cookies
    link = 'https://services.ntu.ac.uk/Timetabling/Timetabling/Student/WeeklyTimetable'

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
    } # important data from authorization

    session = requests.Session()
    r = session.post(link, headers=headers, data=data, cookies=cookies) # post request itself
    soup = BeautifulSoup(r.text, 'lxml')
    table = soup.find("table", class_='timetable alternating')
    no_events_text = "There are no events to display for this week"
    if table is None:
        print("TABLE NOT FOUND!!!\n\n\n\n")
    elif table.find('td', class_='highlight') and table.find('td', class_='highlight').text.strip() == no_events_text:
        return "No lessons on this week"
    else:
        timetable_list = []
        table_rows = table.find_all('tr', class_='item')
        for row in table_rows:  # processing all information about schedule
            cols = row.find_all('td')
            if len(cols) > 0:
                day = cols[0].span.text.strip()
                day_of_week = re.match(r'^\w+', day).group()
                time_from = cols[1].text.strip()
                lecturer = cols[5].text.strip()
                lesson_type = cols[6].text.strip()

                module_name = ""
                if cols[7].a:
                    module_text = cols[7].a.text.strip()
                    module_match = re.search(
                        r'(Artificial Intelligence|Service-Centric & Cloud Comp|Comp Final Year Group Meeting)',
                        module_text)
                    if module_match:
                        module_name = module_match.group()
                    else:
                        module_name = "Module not found"
                else:
                    module_name = "Module not found"
                if 'creates an email to the lecturer' in lecturer:
                    lecturer = lecturer.replace('creates an email to the lecturer', '').strip()
                if lesson_type is None:
                    lesson_type = ''
                if module_name != "Module not found":
                    time_txt = time_to_text(time_from)
                    timetable_list.append(
                        f"{module_name} {lesson_type} with {lecturer} on {day_of_week} at {time_txt}\n")

        return timetable_list


def get_timetable_next_week():
    session_id, requestToken, wa, saml_token, wctx = authorization()
    link = 'https://services.ntu.ac.uk/Timetabling/Timetabling/Student/WeeklyTimetable'

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }

    cookies = {
        'Cookie': 'ASP.NET_SessionId=' + session_id + '; __RequestVerificationToken_L1RpbWV0YWJsaW5nL1RpbWV0YWJsaW5n0=' + requestToken + ';'
    }

    # cookies = {
    #     'Cookie': 'ASP.NET_SessionId=' + session_id + '; __RequestVerificationToken_L1RpbWV0YWJsaW5nL1RpbWV0YWJsaW5n0=' + requestToken + '; __utmc=41656352; __utmz=41656352.1711483282.1.1.utmcsr=fs.ntu.ac.uk|utmccn=(referral)|utmcmd=referral|utmcct=/; __utma=41656352.479835140.1711483282.1711483282.1711485265.2; __utmt=1; .AspNet.Cookies=uMtbVmKPv1bcAs-VmXN9wfGX77IL4q11muSQS5P64CGbsIP43IDCq_Gcmdga-6jMrLlC69mg-hTLc2l5wEphHVOuTyWgkSxr2VKBca_4PawhPfyhv4Y3E31nwIbzIuJ1u3fxuVUFyQpXu-2yv4RJCYczIF_UCZsftfgMHA52d4MikGP9UfSfs3LwschdEtf1qxmFvO61X5IyYnBFiN7S0ExHQev8k4V8MtxiOGdhFCI6JxjHcuZ82DV2C0lMiIm642XCMBrnxeWMg61aXQaeAgWxCFAL4v-ga_PAcSqHXu9ypwhgLPjDDDpUA80W0LAoewncFdy81pgLx3lSneyfES1XvgJitr2qKMy06-6EruzqiQPPTvEtF1xYvQChEKKEgDCsLuld75kLV-23KdHO0Rb7KpSAgp3aTKAJ7NpE9aMo_DbuZR-g__yIYdYzD6Dj67wMGyOyBpkg532pyMsWz_s3budYRdkWIKlyABdbAssA20152285ogg-VKp9YU0-3C9SnQ15SBIvT4TF1cccspfjfdXCOSqQvPfR58P7O2P1Fkbp6L_unPFeH6crRaS4-mMtanK6hCxNSsAUSXpa2-pGZWVEViJ2nEmbmqNPlccd0w6nmVMBsyYUQ7tw7x7cL1OiTBvZTOF713wtDz7kz90c9c14EQaIGqvRRrgC6I1INRBIgoNAvWegGV8TrvwRugspNpIYu8fGlKjTvePK4UV15I5cuV9gayQcvJoj6HohPYHZUwV79yRQLlUsorKQFUa_do8uRVJIgQMVrmpXS9MIJtPJNzAKVQCqvx5PE9tq4fL443FwnAhvhrcskLoMr55rKlMe5RUjpgDsmRwQMyUQykT0od630mmnX9ikPBDxn54Mg5LVskd_mKHLnX0rTgruL5x4tsDOT_I4-2jTiawfxdpASDBTAtJ02C4o9G0JVwIfOfOAhOOS4hgnIDfBbmLBY4WaJajYggYgMdV39IJY-AinLqc6IgrfpP3U1g8XaZTSDwHLfAX8j6n9L6ruu1ESaYCGyXgGLYAEI6JYKS3hg2KAn7NMhkQhNLYgLHoYOfCcyTWKy31uCHHLUjTNmL6ZwbuuIOiWxg65IfOmf10EK64C70OMLAkcXhmkuM97Qs9gZ0cPLlm6xK0oW_tmFbMX6bTYQV8DHWy_hP0Ejg23CsWy92yegOXv0C6P_pwqkqUNlLEsnQwbQB0NSSew3q6zgig5JBAtRhlqxkXzu_JLxiR82HQ6tfj1GkpHTqrcuaZm31Go2T2BRVtr1rZzkWb6ip0lCdPyhXbjuZpg7pcr02bflTXNxKNOHaSLAGMD987jkCcsga9hvYeAUIe1vTOcXcDJhEYuhXj6y9YTbMIxcLltcgfRcfdfOqjZkmH4tOuW3OJeF7P5bvDT787Ww47zp4jZ8S0l796RNEkFZKaQwLr8373zzUf8X5X814zunSz5a2nwAWXcFQmvy1N86LE14YHEE6TT8bxUzvWXvcGGIwJWB9r-98AO7va_Ycei6wVdcWqWt1nYMYuYcBJu9CUsTkG5azlTYblZ_HBrxsvAn1DSQscvrfI5qoK58j-YQ3RWivkLJREQlMXOe47EX6DEWQVfvxz04-yWJdGjoYTg_ocAkju-sMRjprqR8pfO09xc-dpcuwnRdkcEpDvK2lbF8ncNSsS7JLaFvOugHD2yyrCCzTVq0m7yUiG5lSj4IFpRp-0P9-4eFUUsgFBiTFQV16uyUQyhZ6VZj0o4VWbVI5zNoxFKjFKNrT08gBgFgLQhPYJofwjArHBw4nhysHQAarDwlOf9DMqsjj3bcsvfXy92D-305aVjN09DzXnLqWMAShrLYHOd9DioDQikM7rONSBg3k49rI7i9lmA8_zn7fgp5nnudbyb70oiZ1frdfzlqK5iLcBhthZNDlx6dTKibjVQpXO_k8Vg7b6NGy0-A3hN03VM3gzghjiWmSFuqTI8Xla-BSWhWJ9N8ttq3arPd7CEkkkJxJ9TnJa-FV4qkEDtuP8cz_43Yd5O3KNQxUEbrK6QlyGaLa7ZkdpSD8ZHHrahBTCHzizlRnosdzvwiU1zr1SyVs8KffXMRp_aDyys19hfe6y1QHB9TIYuQpW9jGlMjLlsiAz_1Gr_EFBAXY20GK0JzhOiHq2jxdywCjtI6Y2WGM9bGE3nmNyHOPrTu3nOi4mZRakaJ6KpvMHGCdG_wCnJp4841dfk8ArO6Cx-RHBz8Uawqu6QEh58X9hl0hhYwSYKchecNANRgf4mLoSeBlfKQWtmTRGNNtYZJ5tI93J1CtiC9_OypBT4PE_vQqhISdHoR7R-cuad3UWbDMVesTSIt8MUwGukq5r1nMjQIJNDyWvRX7QOCVpzSLx_oQIgTpt4qxlijB7slONrqspTr6Oh0GY8YzmSC5Y0jBE5SZBMmOI9h-MmW8VZiyeNfN-AeJ-WJwyeJoWPu6xgva8cY8jjL9SHbq1Rb-ciUszN-WVsX3e5V1098e0i4IMaQbdrbHWkAZbzfl84Z4FDzdSK45T89dS3MhhcXIk1p-CqP4se4gijZwDjq48ciovvDTwDKM71MgZNyQVNgGPYesd1K1ZHWCR27WqRcezGv3dr0TkVYwllPB66U5Yt0bGb-G3EI_TBxpq-r10_MOuQpNBzPm59ABLg81MaA-1oLygyF5A4Xi9B3NjzvqhhbZ0DR6jLZ6zGDmY_yfAgMobHAosR9i3wFf0w4UhPObONYvtmQAtWvlb9h781_Jz62jW-Pg2fn79khQc9aSxwGj_6Ow_GzowDaaul4p8fIB39NfjeXeoeIohRQSsHn6syFMmp5gvGk68GdSrcjDKRjvwZ1fYonJiQgLawyUr-zLQhi5sRR6ys--XXjG9oCXG6zEl-vUTS7Uuuc0R82pjmjdygFnFGZyFi3E0th9twTg-mjlCcq2RGPAJHPLtH-8z1JY6F0gscX8w0c1nP-0ho75lZDSt_LWeZwT9GdI6TfpTFT2E89JDkqDubWFzEvOueRU3cE5fKYD8_zYxFiFrLlEkFaLmK3Wyvt_AmzFR3ZvJIOVpWaoflj4sOWoSgFqqocShovv1YVpalhxdqwERv_0BSVFkn9asXyxSuLeCiNLoV33HswdzVUgxZOHXBJ2tf; __utmb=41656352.5.10.1711485265'
    # }

    start_date = datetime.datetime(2024, 3, 25)
    variable = 37
    variable_2 = 38
    variable = increment_variable_every_monday(start_date, variable)
    variable_2 = increment_variable_every_monday(start_date, variable_2)

    data = {
        'wa': wa,
        'wresult': saml_token,
        'wctx': wctx,
        '__RequestVerificationToken': requestToken,
        'WeekNumber': variable_2,
        'RenderedWeekNumber': variable,
        'Command': 'Update timetable'
    }

    data2 = {
        '__RequestVerificationToken': requestToken,
        'WeekNumber': variable_2,
        'RenderedWeekNumber': variable,
        'Command': 'Update timetable'
    }

    session = requests.Session()
    req = session.post(link, headers=headers, data=data, cookies=cookies)
    r = session.post(link, headers=headers, data=data2)
    soup = BeautifulSoup(r.text, 'lxml')
    table = soup.find("table", class_='timetable alternating')
    no_events_text = "There are no events to display for this week"
    if table is None:
        print("TABLE NOT FOUND!!!\n\n\n\n")
    elif table.find('td', class_='highlight') and table.find('td', class_='highlight').text.strip() == no_events_text:
        return 'No timetable for this week'
    else:
        timetable_list = []

        table_rows = table.find_all('tr', class_='item')
        for row in table_rows:
            cols = row.find_all('td')
            if len(cols) > 0:
                day = cols[0].span.text.strip()
                day_of_week = re.match(r'^\w+', day).group()
                time_from = cols[1].text.strip()
                lecturer = cols[5].text.strip()
                lesson_type = cols[6].text.strip()

                module_name = ""
                if cols[7].a:
                    module_text = cols[7].a.text.strip()
                    module_match = re.search(
                        r'(Artificial Intelligence|Service-Centric & Cloud Comp|Comp Final Year Group Meeting)',
                        module_text)
                    if module_match:
                        module_name = module_match.group()
                    else:
                        module_name = "Module not found"
                else:
                    module_name = "Module not found"
                if 'creates an email to the lecturer' in lecturer:
                    lecturer = lecturer.replace('creates an email to the lecturer', '').strip()
                if lesson_type is None:
                    lesson_type = ''
                if module_name != "Module not found":
                    time_txt = time_to_text(time_from)
                    timetable_list.append(
                        f"{module_name} {lesson_type} with {lecturer} on {day_of_week} at {time_txt}\n")

        return timetable_list



