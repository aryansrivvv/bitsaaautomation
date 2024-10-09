from config import *
from driver_setup import *
from sheets_setup import * 
import openai
openai.api_key = OPENAI_API_KEY


def check_linkedin_login_status (driver):
    try : 
        login_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="global-nav"]')))
        return True 
    except : 
        return False 

def linkedin_login(driver):
    try:
        print("Attempting to log in to Linkedin")
        driver.get('https://www.linkedin.com/login')
        try : 
            email_xpath = "//input[@id ='username']"
            password_xpath = "//input[@id ='password']"
            email_field = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, email_xpath)))
            password_field = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, password_xpath)))
            email_field.clear()
            random_sleep()
            email_field.send_keys(LINKEDIN_EMAIL)
            password_field.clear()
            password_field.send_keys(LINKEDIN_PASSWORD)
            random_sleep()
        except Exception as e : 
            print("Error findling email and password field")
        login_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.btn__primary--large')))
        random_sleep()
        login_button.click()
        print("Login button clicked")
    except Exception as e:
        print(f"Error during login: {e}")
        raise

def wait_and_get_element(driver , xpath, wait_time=rand_time):
    try:
        element = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        print(f"Element found: {xpath}")
        return element
    except Exception as e:
        print(f"Error finding element {xpath}: {e}")
        return None
    
def wait_and_get_elements(driver , xpath, wait_time=rand_time):
    try:
        elements = WebDriverWait(driver, wait_time).until(
            EC.presence_of_all_elements_located((By.XPATH, xpath))
        )
        print(f"Elements found: {xpath}, count: {len(elements)}")
        return elements
    except Exception as e:
        print(f"Error finding elements {xpath}: {e}")

def clean_text(text):
    text = re.sub(r'#\S+\s*', '', text)
    text = re.sub(r'\bhashtag\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def click_view_job_button(driver ):
    try:
        xpath = '//*[@id="fie-impression-container"]/div[3]/div[1]/button[1]/span[2]'
        view_job_button = wait_and_get_element(driver , xpath , 20 )
        if view_job_button:
            view_job_button.click()
            print("'View Job' button clicked")
            return True
        else:
            print("'View Job' button not found")
            return False
    except ElementClickInterceptedException:
        print("Click was intercepted, trying again...")
        return False
    except Exception as e:
        print(f"Error clicking 'View Job' button: {e}")
        return False

def process_with_openai(info, more_info):
    prompt = f"""
    Given the following data from a LinkedIn job post, extract and format the following information:
    - Person to contact
    - Email (if available)
    - Phone number (if available)
    - Job title
    - Job location
    - Company name
    - Key job requirements
    - Any other relevant details for a job application

    Data:
    Info: {info}
    More Info: {more_info}

    Please format the output as a structured JSON object.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts and structures job posting information. Process the data and give output in a clean and formatted manner (free of quotes and brackets) so its easy to read and look clean"},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message['content']

def format_openai_response(response):
    try:
        response = re.sub(r'[{}"]+', '', response)
        response = re.sub(r'\s*:\s*', ': ', response)
        response = re.sub(r',\s*', '\n', response)
        formatted_response = response.strip()
        return formatted_response
    except Exception as e:
        print(f"Error formatting OpenAI response: {e}")
        return response


def contains_linkedin(url):
    return 'linkedin' in url.lower()

def main():
    try : 
        driver = initialise_driver()
        print("Starting LinkedIn scraper script")
        # check login status
        driver.get('https://www.linkedin.com/login') 
        random_long_sleep()
        if(check_linkedin_login_status(driver)):
            print("Already Logged in")
        else : 
            linkedin_login(driver)
        random_long_sleep()
        urls_and_statuses = get_urls_and_statuses_from_sheet(sheets)
        if not urls_and_statuses:
            print("No URLs found in the spreadsheet. Exiting.")
            return
        print(f"Found {len(urls_and_statuses)} URLs to process")
        for row_index, (url, status) in enumerate(urls_and_statuses, start=2):  # start=2 because row 1 is header
            if status.lower() == "done":
                print(f"Skipping already processed URL: {url}")
                continue
            if (url == "Not Provided"):
                print(f"No link found in row {row_index}")
                update_status(row_index, "Link not found", sheets)
                continue
            if (contains_linkedin(url)==False):
                print(f"Not a linkedin link")
                continue
            try : 
                print(f"Processing URL: {url}")
                driver.get(url)
                print(f"Navigated to URL: {url}")
                random_sleep()
                name_element = wait_and_get_element(driver , "//span[contains(@class, 'update-components-actor__name')]", rand_time)
                name = name_element.text.strip() if name_element else "Name not found"
                job_title_element = wait_and_get_element(driver , "//span[contains(@class, 'update-components-actor__description')]" , rand_time )
                job_title = job_title_element.text.strip() if job_title_element else "Job title not found"
                name = ' '.join(dict.fromkeys(name.split()))
                job_title = ' '.join(dict.fromkeys(job_title.split()))
                profile_link_element = wait_and_get_element(driver , "//a[contains(@class, 'update-components-actor__meta-link')]" , rand_time)
                profile_link = profile_link_element.get_attribute('href') if profile_link_element else "Profile link not found"
                info_element = wait_and_get_element(driver, "//div[contains(@class, 'update-components-text')]" , rand_time )
                info = clean_text(info_element.text) if info_element else "Info not found"
                if click_view_job_button(driver ):
                    job_details_element = wait_and_get_element(driver , "//div[contains(@class, 'job-details')]/child::h1" , rand_time )
                    job_details = job_details_element.text if job_details_element else "Job details not found"
                    additional_info_elements = wait_and_get_elements(driver , "//div[contains(@class, 'primary-description')]/div/span[@class]" , rand_time )
                    additional_info = [element.text for element in additional_info_elements]
                    skills_required_element = wait_and_get_element(driver , "//div[@id='how-you-match-card-container']/section[2]/div/div/div/div/a" , rand_time )
                    skills_required = skills_required_element.text if skills_required_element else "Skills required not found"
                    more_info = f"{job_details}, " + ", ".join(additional_info) + f", {skills_required}"
                else:
                    more_info = "Failed to click 'View job' button"
                print(f'More Info: {more_info}')
                scraped_data = {
                    'name': name,
                    'job_title': job_title,
                    'profile_link': profile_link,
                    'info': info,
                    'more_info': more_info,
                    'openai': format_openai_response(process_with_openai(info, more_info)),
                    'original_url': url
                }
                print("Data processed through OpenAI")
                save_to_google_sheets(scraped_data)
                print("Data saved to Google Sheets successfully.")
                update_status(row_index, "Done", sheets)
                driver.quit()
            except Exception as e:
                print(f"An error occurred while processing URL {url}: {e}")
                driver.quit()
    except Exception as e: 
        print(f"An error occurred: {e}")
        driver.quit()
    finally:
        print("Linkedin Scraper Completed!")
        driver.quit()
