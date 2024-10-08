from config import *
from driver_setup import *
from sheets_setup import * 
import anthropic
client = anthropic.Anthropic(api_key=API_KEY)


def check_login_status(driver):
    try:
        search_bar_xpath = '//button[contains(@aria-label , "Search or start new chat")]'
        search_bar = WebDriverWait(driver,90).until(
            EC.presence_of_element_located((By.XPATH,search_bar_xpath))
        )
        return True
    except Exception as e:
        return False

def whatsapp_login(driver):
    x_path_link_with_phone = "//span[text()='Link with phone number']"
    element = WebDriverWait(driver, 30 ).until(EC.element_to_be_clickable((By.XPATH,x_path_link_with_phone )))
    element.click()
    random_sleep()
    current_country = "//img[@crossorigin = 'anonymous']/parent::div"
    details = WebDriverWait(driver,30).until(EC.element_to_be_clickable((By.XPATH, current_country)))
    print(f"The current country is :{details.text}")
    x_path_set_country = "//span[@data-icon ='caret-down']"
    try:
        random_sleep()
        element = WebDriverWait(driver, 30 ).until(EC.element_to_be_clickable((By.XPATH,x_path_set_country )))
        print("Selecting : " + COUNTRY_CODE)
        element.click()
        random_sleep()
    except Exception as e:
        print("Country not found or")
        print(e)
    random_sleep()
    input_field = WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
    )
    input_field.clear()
    random_sleep()
    input_field.send_keys(COUNTRY_CODE)
    x_path_country_code =  "//button[contains(@aria-label,'Selected country')]"
    country_button = WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.XPATH,x_path_country_code))
    )
    random_sleep()
    country_button.click()
    print("Country Changed to "+ COUNTRY_CODE)
    random_sleep()
    x_path_input_phone = "//input[@aria-label ='Type your phone number.']"
    input_field = WebDriverWait(driver, 30).until(
    EC.presence_of_element_located((By.XPATH, x_path_input_phone))
    )
    random_sleep()
    phone_number = PHONE_NUMBER 
    input_field.send_keys(phone_number)
    print("Phone number entered")
    x_path_next_button = "//div[text()='Next']"
    element = WebDriverWait(driver, 30 ).until(
    EC.element_to_be_clickable((By.XPATH,x_path_next_button ))
    )
    random_sleep()
    element.click()
    x_path_of_code = "//div[@aria-details='link-device-phone-number-code-screen-instructions']"
    try:
        element = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH,x_path_of_code ))
        )
        link_code = element.get_attribute('data-link-code')
        print(f"The link code is: {link_code}")
        time.sleep(67.4)
    except Exception as e : 
        print(f"Some error occured")

def check_stat_login_to_whatsapp(driver):
    try :
        while(True):
            driver.get("https://web.whatsapp.com/")
            random_sleep()
            print("Checking login status")
            x = check_login_status(driver)
            if (x == False):
                print("Logging in")
                random_sleep()
                whatsapp_login(driver)
                random_sleep()
                if(check_login_status(driver)== False):
                    print("Retrying")
                else : 
                    print("Logged in Successfully!")
                    break
            else : 
                print("Logged in Successfully!")
                break 
    except Exception as e : 
        pass 

def split_date_time_name(a):
    pattern = r'\[(.*?), (.*?)\] (.*?):'
    match = re.match(pattern, a)
    return match.group(1), match.group(2), match.group(3) if match else (None, None, None)

def extract_messages(driver, group_name):
    x_path_of_all_text_messages = '//div[@role = "row"]//div[contains(@class , "copyable-text")]'
    try:
        message_elements = WebDriverWait(driver, 100).until(EC.presence_of_all_elements_located((By.XPATH, x_path_of_all_text_messages)))
    except :
        print("error occured here for the particular element")
        pass
    print(f"Found the group: {group_name} with {len(message_elements)} text messages")
    data = []
    for message_element in message_elements:
        text_data = message_element.get_attribute("data-pre-plain-text")
        try :
            text_message_xpath = './/span[@dir = "ltr"]'
            text_message_element = message_element.find_element(By.XPATH, text_message_xpath)
        except :
            print("error occured here for the particular element")
            pass 
        date_time_name = split_date_time_name(text_data)
        append_data = [group_name, date_time_name[1], "' "+date_time_name[2], date_time_name[0] ,text_message_element.text ]
        data.append(append_data)
    return data

def extract_job_info(message):
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": f"""Determine if the following message is a job opportunity or referral. If it is either, extract the requested information. If it's not a job opportunity, provide any contact details, links, emails present in the message.

Message: {message}

Provide the information in the following format, don't provide any extra text:
Job/referral opportunity:(reply with yes or no only)
Brief Description(if any): 
Phone numbers provided(if any):
emails provided(if any):
links/URL Provided(if any):

For any information not provided in the message, use "Not Provided"."""
            }
        ]
    )
    return response.content[0].text if isinstance(response.content, list) else response.content

def split_processed_job_details(job_info):
    split_1 = job_info.split('\n')
    return [i.split(': ')[1] for i in split_1]

def extract(driver , sheets):
    try:
        group_names = read_group_names_from_sheets(sheets)
        print("The groups to scrape :")
        print(group_names)
    except Exception as e:
        print(f"Error reading group names")
        return
    try:
        for group_name in group_names:
            try:
                x_path = f'//span[@dir = "auto" and @title ="{group_name}"]'
                chathead_element = WebDriverWait(driver,10).until(
                    EC.element_to_be_clickable((By.XPATH, x_path))
                )
                print(group_name + ": Extracting messages...")
                chathead_element.click()
                time.sleep(45)
                try : 
                    extracted_messages =extract_messages(driver , group_name )
                    send_data_to_sheets(extracted_messages, sheets, id = SPREADSHEET2_ID)
                    print(f"Extraction complete for group {group_name} Results saved in Sheets.")
                except Exception as e : 
                    print("error in group extraction")
                    print(e)
            except TimeoutException as e :
                print(f"Could not find or click on group: {group_name}")
            except Exception as e:
                print(f"Error processing group {group_name}")
    except Exception as e:
        print(f"An unexpected error occurred")
    finally:
        print("Extraction complete !")

def process(message):
    job_info = extract_job_info(message)
    return split_processed_job_details(job_info)

def extract_and_process(sheets):
    try : 
        group_data = read_data_from_sheets(sheets)
        print(f"found {len(group_data)} messages to extract and process")
        for data in group_data :
            try:
                final_data = process(data[4])
                if final_data[0].lower() == "yes":
                    append_data = [data[0] ,data[1] , data[2] , data[3] , final_data[1], f"' {final_data[2]}", final_data[3], final_data[4] ]
                    send_data = [append_data]
                    send_data_to_sheets(send_data , sheets , SPREADSHEET_ID)
            except Exception as e: 
                print(f'Processing failed for {data}')
        print("Data processed and added successfully.")
    except Exception as e : 
        print("No data Available or " + e )
        return 

def main():
    try : 
        driver = initialise_driver()
        check_stat_login_to_whatsapp(driver)
        extract(driver,sheets)
        driver.quit()
        extract_and_process(sheets)
        print("Clearing Sheet")
        clear_sheet_except_header(sheets, SPREADSHEET2_ID)
        print("Scraping complete , will close soon")
    except Exception as e : 
        pass
    pass 

