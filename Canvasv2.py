from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import os
import time

# Replace with your Canvas URL and credentials
CANVAS_URL = "https://ycp.instructure.com/"
USERNAME = "jharvey8@ycp.edu"
PASSWORD = "Stuff!234567890"

# Initialize the WebDriver
driver = webdriver.Chrome()

try:
    # Step 1: Log in to Canvas
    driver.get(CANVAS_URL)

    # Wait for the email input field
    email_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "i0116"))
    )
    email_input.send_keys(USERNAME)

    next_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "idSIButton9"))
    )
    next_button.click()

    # Wait for the password input field
    password_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "passwd"))
    )
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.RETURN)

    # Handle additional prompts if necessary
    sign_in_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "idSIButton9"))
    )
    sign_in_button.click()

    confirm_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "idSIButton9"))
    )
    confirm_button.click()

    # Step 2: Navigate to a course (using the class from your screenshot)
    time.sleep(5)  # Ensure login completes
    course_links = driver.find_elements(By.CLASS_NAME, "ic-DashboardCard__action")  # Adjusted selector

    if course_links:
        course_links[0].click()  # Click the first course
    else:
        print("No courses found!")
        driver.quit()
        exit()

    # Step 3: Go to the Files section of the course
    time.sleep(5)  # Allow course page to load
    files_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Files"))
    )
    files_button.click()

    # Step 4: Wait for files to load
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.ic-Table__cell-content"))
    )

    # Step 5: Download files
    file_links = driver.find_elements(By.CSS_SELECTOR, "a.ic-Table__cell-content")
    download_dir = "Canvas_Files"
    os.makedirs(download_dir, exist_ok=True)

    for link in file_links:
        file_url = link.get_attribute("href")
        file_name = link.text.strip()
        if file_url:
            print(f"Downloading: {file_name} from {file_url}")
            response = requests.get(file_url, stream=True)
            with open(os.path.join(download_dir, file_name), "wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)

    print(f"All files downloaded to {os.path.abspath(download_dir)}")

except Exception as e:
    print(f"An error occurred: {e}")
    print("Page source for debugging:\n", driver.page_source)

finally:
    driver.quit()
