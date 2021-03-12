import os
import time
from time import strptime
import datetime
import smtplib, ssl # send email notification
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

### ensure chromedriver and chrome have comptaible versions and are installed in path ###

# chose day/mounatin you're trying to ski on given month and where to send message
ski_month = 'April'
day = 3
mountain = 'Vail'
# where to send text (options == [<phone>@txt.att.net, <phone>@vtext.com, <phone>@tmomail.net])
phone_receiver = '' 

# get current month
date_today = datetime.datetime.now()
current_month = date_today.strftime("%B")

# find num_clicks to get to correct calendar
ski_datetime_object = datetime.datetime.strptime(ski_month, "%B")
current_datetime_object = datetime.datetime.strptime(current_month, "%B")
ski_month_num = ski_datetime_object.month
current_month_num = current_datetime_object.month
num_clicks = ski_month_num - current_month_num

# epicpass url
url = 'https://www.epicpass.com/plan-your-trip/lift-access/reservations.aspx'

# chrome/driver paths
#chromedriver_path = '/home/ec2-user/ski_scraper/chromedriver_linux'
#chrome_path = '/home/ec2-user/ski_scraper/Chrome'

# chromedriver options
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-setuid-sandbox")
options.add_argument("--disable-infobars")
options.add_argument("--disable-dev-shm-usage")

# other options
#chrome_options.add_argument('user-data-dir={}'.format(chrome_path))
#chrome_options.add_argument("--kiosk")
#options.add_argument("window-size=1400,1500")
#options.add_argument("--disable-gpu")
#options.add_argument("start-maximized")
#options.add_argument("enable-automation")

# sneaky selenium
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

# initialize driver and go to url
driver = webdriver.Chrome(options=options)
try:
    driver.get(url)
except Exception as e:
    print(e)
time.sleep(2)

# epic user/pass
epic_username = os.getenv('EPIC_USER')
epic_password = os.getenv('EPIC_PASS')

# look for chrome cookies popup and click OK if needed
try:
    chrome_popup = driver.find_element_by_xpath('//*[@id="onetrust-accept-btn-handler"]')
    chrome_popup.click()
    time.sleep(2)
except:
    pass

# type in user/pass
try:
    user_login = driver.find_element_by_id('txtUserName_3')
    user_login.send_keys(epic_username)
    time.sleep(2)
    pass_login = driver.find_element_by_id('txtPassword_3')
    pass_login.send_keys(epic_password)
    time.sleep(2)
    user_saved = False
except:
    user_saved = True

try:
    pass_login = driver.find_element_by_id('txtPassword_1')
    pass_login.send_keys(epic_password)
    time.sleep(2)
except:
    if user_saved:
        pass_login = driver.find_element_by_id('txtPassword_1')
        pass_login.send_keys(epic_password)
        time.sleep(2)
    elif not user_saved:
        print('Logged in with no credentials saved')
    else:
        print('XPATH(s) needs updating')

# click login button
try:
    login_button = driver.find_element_by_xpath('/html/body/div[3]/div/div/div[2]/div/div/div[1]/form/div/div/div[5]/button') 
    login_button.click()
except Exception as e:
    print(e)

# wait for new page to populate and select mountain to check
try:
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="PassHolderReservationComponent_Resort_Selection"]')))
    select = Select(driver.find_element_by_xpath('//*[@id="PassHolderReservationComponent_Resort_Selection"]'))
    # select by visible text
    select.select_by_visible_text(mountain)
    time.sleep(2)
except Exception as e:
    print('Specified mountain is not an option for this dropdown')
    print(e)

# click on search for dates available
try:
    search_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div/div[2]/div[2]/div/div/div/div[3]/div/div/div[3]/button')))
    search_button.click()
    time.sleep(2)
except Exception as e:
    print('Search button XPATH incorrect')
    print(e)

# check if date is available
msg = ''
unavailable_msg = ''
if ski_month != current_month:
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="passHolderReservations__wrapper"]/div[3]/div[2]/div[1]/div[2]/div[2]/div/div[1]/button[2]')))
        next_button = driver.find_element_by_xpath('//*[@id="passHolderReservations__wrapper"]/div[3]/div[2]/div[1]/div[2]/div[2]/div/div[1]/button[2]')
    except Exception as e:
        print(e)
    if next_button.is_enabled():
        i = 0
        while i < num_clicks:
            try:
                i += 1
                WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, '//*[@id="passHolderReservations__wrapper"]/div[3]/div[2]/div[1]/div[2]/div[2]/div/div[1]/button[2]')))
                next_button.click()
            except:
                # season is over
                break
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div/div[2]/div[2]/div/div/div/div[3]/div[2]/div[1]/div[2]/div[2]/div/div[4]/button[{}]'.format(day))))
            calendar_button = driver.find_element_by_xpath('/html/body/div[3]/div/div[2]/div[2]/div/div/div/div[3]/div[2]/div[1]/div[2]/div[2]/div/div[4]/button[{}]'.format(day))
            if calendar_button.is_enabled():
                msg = "{} lift tickets are available for {} {}!\n{}\n".format(
                    mountain, ski_month, day, url.replace('https://', '').replace('.aspx', ''))
            else:
                unavailable_msg = ('{} {} is not available at {}...'.format(ski_month, day, mountain))
        except Exception as e:
            print(e)
    else:
        unavailable_msg = ('{} {} is not available at {}...'.format(ski_month, day, mountain))
else:
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div/div[2]/div[2]/div/div/div/div[3]/div[2]/div[1]/div[2]/div[2]/div/div[4]/button[{}]'.format(day))))
        calendar_button = driver.find_element_by_xpath('/html/body/div[3]/div/div[2]/div[2]/div/div/div/div[3]/div[2]/div[1]/div[2]/div[2]/div/div[4]/button[{}]'.format(day))
    except Exception as e:
        print(e)
    if calendar_button.is_enabled():
        msg = "{} lift tickets are available for {} {}!\n{}\n".format(
            mountain, ski_month, day, url.replace('https://', '').replace('.aspx', ''))
    else:
        unavailable_msg = ('{} {} is not available at {}...'.format(ski_month, day, mountain))

# cleanly exit
driver.quit()

#setup email for ski notification
port = 465
email_sender = os.getenv('TEXT_USER')
email_password = os.getenv('TEXT_PASS')
context = ssl.create_default_context()
server = smtplib.SMTP_SSL('smtp.gmail.com', port, context=context)

try:
    server.login(email_sender, email_password)
except:
    print('could not sign in to email')

# send text confirmation if date is available
if msg:
    try:
        server.sendmail(email_sender, phone_receiver, msg)
        print('Successfully sent text!')
        print(msg)
        server.quit()
    except Exception as e:
        print('Could not send text...')
        print(e)
else:
    print(unavailable_msg)