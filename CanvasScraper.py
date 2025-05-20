import os
import time
import requests
import hashlib
import argparse
import getpass
import logging
import traceback
import datetime
import math
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from urllib.parse import urlparse, unquote

# Set up logging
log_filename = f"canvas_scraper_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CanvasScraper")

class CanvasScraper:
    def __init__(self, canvas_url, username, password, download_dir="Canvas_Downloads", skip_existing=True, headless=False, delay=2):
        """
        Initialize the Canvas Scraper
        
        Args:
            canvas_url (str): The URL of your Canvas instance
            username (str): Your Canvas username/email
            password (str): Your Canvas password
            download_dir (str): Directory to save downloaded files
            skip_existing (bool): Skip downloading files that already exist
            headless (bool): Run Chrome in headless mode (no visible browser)
            delay (int): Delay in seconds between actions for visibility
        """
        self.canvas_url = canvas_url.rstrip('/')  # Remove trailing slash if present
        self.username = username
        self.password = password
        self.base_download_dir = download_dir
        self.skip_existing = skip_existing
        self.headless = headless
        self.delay = delay
        self.driver = None
        self.session = requests.Session()
        self.auth_provider = self._detect_auth_provider()
        logger.info(f"Initializing Canvas Scraper for {canvas_url}")
        logger.info(f"Authentication provider detected: {self.auth_provider}")
        
    def _detect_auth_provider(self):
        """Try to detect the authentication provider based on the Canvas URL"""
        if "ycp.instructure.com" in self.canvas_url:
            return "microsoft"  # York College of Pennsylvania uses Microsoft authentication
        elif "canvas.instructure.com" in self.canvas_url:
            return "canvas"  # Default Canvas authentication
        else:
            return "unknown"  # Will try to detect during login
            
    def login(self):
        """Log in to Canvas using Selenium"""
        logger.info("Initializing Chrome browser...")
        try:
            # Use webdriver_manager to automatically download the correct ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            # Configure Chrome options
            chrome_options = webdriver.ChromeOptions()
            if self.headless:
                logger.info("Running in headless mode...")
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
        
            # Initialize the Chrome driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            if not self.headless:
                self.driver.maximize_window()
        
            logger.info(f"Navigating to {self.canvas_url}...")
            self.driver.get(self.canvas_url)
            time.sleep(self.delay)  # Add delay for visibility
            
            # Take a screenshot of the login page
            self._take_screenshot("login_page")
            
            # Detect login method if unknown
            if self.auth_provider == "unknown":
                self.auth_provider = self._detect_login_method()
                
            logger.info(f"Detected authentication provider: {self.auth_provider}")
            
            # Handle login based on the authentication provider
            if self.auth_provider == "microsoft":
                self._login_microsoft()
            elif self.auth_provider == "google":
                self._login_google()
            elif self.auth_provider == "canvas":
                self._login_canvas_native()
            else:
                logger.info("Unknown authentication provider. Attempting generic login...")
                self._login_generic()
            
            # Wait for the dashboard to load to confirm successful login
            logger.info("Waiting for dashboard to load...")
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ic-Dashboard-header"))
            )
            logger.info("Successfully logged in to Canvas!")
            
            # Take a screenshot of the dashboard
            self._take_screenshot("dashboard")
            
            # Transfer cookies from Selenium to Requests session
            for cookie in self.driver.get_cookies():
                self.session.cookies.set(cookie['name'], cookie['value'])
                
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Take a screenshot of the error page
            self._take_screenshot("login_error")
            
            # Log the page source for debugging
            if self.driver:
                logger.debug(f"Page source at error: {self.driver.page_source}")
                
            logger.info("If you're having trouble logging in, try manually logging in to Canvas in a browser first.")
            return False
            
    def _detect_login_method(self):
        """Detect the login method based on the login page elements"""
        try:
            # Check for Microsoft login
            if self.driver.find_elements(By.ID, "i0116") or self.driver.find_elements(By.ID, "idSIButton9"):
                return "microsoft"
                
            # Check for Google login
            if self.driver.find_elements(By.ID, "identifierId") or self.driver.find_elements(By.CLASS_NAME, "google-login-button"):
                return "google"
                
            # Check for Canvas native login
            if self.driver.find_elements(By.ID, "pseudonym_session_unique_id") or self.driver.find_elements(By.ID, "pseudonym_session_password"):
                return "canvas"
                
            return "unknown"
        except:
            return "unknown"
            
    def _take_screenshot(self, name):
        """Take a screenshot for debugging purposes"""
        if self.driver:
            try:
                screenshot_dir = "screenshots"
                os.makedirs(screenshot_dir, exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{screenshot_dir}/{name}_{timestamp}.png"
                self.driver.save_screenshot(filename)
                logger.info(f"Screenshot saved to {filename}")
            except Exception as e:
                logger.error(f"Failed to take screenshot: {str(e)}")
    
    def _login_microsoft(self):
        """Login using Microsoft authentication"""
        logger.info("Logging in with Microsoft authentication...")
        
        try:
            # Wait for the email input field
            logger.info("Waiting for email input field...")
            email_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "i0116"))
            )
            logger.info("Entering email...")
            email_input.clear()
            email_input.send_keys(self.username)
            time.sleep(self.delay)  # Add delay for visibility
            
            logger.info("Clicking next button...")
            next_button = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.ID, "idSIButton9"))
            )
            next_button.click()
            time.sleep(self.delay)  # Add delay for visibility
            
            # Take a screenshot after entering email
            self._take_screenshot("after_email")
            
            # Wait for the password input field
            logger.info("Waiting for password input field...")
            password_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.NAME, "passwd"))
            )
            logger.info("Entering password...")
            password_input.clear()
            password_input.send_keys(self.password)
            time.sleep(self.delay)  # Add delay for visibility
            password_input.send_keys(Keys.RETURN)
            time.sleep(self.delay)  # Add delay for visibility
            
            # Take a screenshot after entering password
            self._take_screenshot("after_password")
            
            # Handle "Stay signed in?" prompt - Always click "Yes"
            try:
                logger.info("Looking for 'Stay signed in' prompt...")
                # Take a screenshot before clicking stay signed in
                self._take_screenshot("before_stay_signed_in")
                
                sign_in_button = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.ID, "idSIButton9"))
                )
                logger.info("Clicking 'Yes' on 'Stay signed in' prompt...")
                sign_in_button.click()
                time.sleep(self.delay)  # Add delay for visibility
            except TimeoutException:
                logger.info("No 'Stay signed in' prompt detected, continuing...")
            
            # Handle additional confirmation if needed
            try:
                logger.info("Looking for additional confirmation prompt...")
                # Take a screenshot before additional confirmation
                self._take_screenshot("before_additional_confirmation")
                
                confirm_button = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.ID, "idSIButton9"))
                )
                logger.info("Clicking confirmation button...")
                confirm_button.click()
                time.sleep(self.delay)  # Add delay for visibility
            except TimeoutException:
                logger.info("No additional confirmation prompt detected, continuing...")
                
        except Exception as e:
            logger.error(f"Microsoft login failed: {str(e)}")
            logger.error(traceback.format_exc())
            self._take_screenshot("microsoft_login_error")
            raise
            
    def _login_google(self):
        """Login using Google authentication"""
        logger.info("Logging in with Google authentication...")
        
        try:
            # Wait for the email input field
            logger.info("Waiting for email input field...")
            email_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "identifierId"))
            )
            logger.info("Entering email...")
            email_input.clear()
            email_input.send_keys(self.username)
            time.sleep(self.delay)  # Add delay for visibility
            
            # Take a screenshot after entering email
            self._take_screenshot("google_after_email")
            
            # Click next button or press Enter
            try:
                next_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#identifierNext button"))
                )
                logger.info("Clicking next button...")
                next_button.click()
            except:
                logger.info("No next button found, pressing Enter...")
                email_input.send_keys(Keys.RETURN)
                
            time.sleep(self.delay)  # Add delay for visibility
            
            # Wait for the password input field
            logger.info("Waiting for password input field...")
            password_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            logger.info("Entering password...")
            password_input.clear()
            password_input.send_keys(self.password)
            time.sleep(self.delay)  # Add delay for visibility
            
            # Take a screenshot after entering password
            self._take_screenshot("google_after_password")
            
            # Click next button or press Enter
            try:
                password_next_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#passwordNext button"))
                )
                logger.info("Clicking password next button...")
                password_next_button.click()
            except:
                logger.info("No password next button found, pressing Enter...")
                password_input.send_keys(Keys.RETURN)
                
            time.sleep(self.delay)  # Add delay for visibility
            
            # Check for additional verification or prompts
            try:
                logger.info("Checking for additional verification steps...")
                # Take a screenshot of any additional verification
                self._take_screenshot("google_verification")
                
                # Look for common verification elements
                verification_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    "input[type='tel'], button:contains('Verify'), button:contains('Next'), button:contains('Continue')")
                
                if verification_elements:
                    logger.info("Additional verification step detected. Manual intervention may be required.")
                    # Give extra time for manual intervention if needed
                    time.sleep(10)
            except:
                logger.info("No additional verification steps detected.")
                
        except Exception as e:
            logger.error(f"Google login failed: {str(e)}")
            logger.error(traceback.format_exc())
            self._take_screenshot("google_login_error")
            raise
        
    def _login_canvas_native(self):
        """Login using Canvas native authentication"""
        logger.info("Logging in with Canvas native authentication...")
        
        try:
            # Wait for the email input field
            logger.info("Waiting for email input field...")
            email_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "pseudonym_session_unique_id"))
            )
            logger.info("Entering email...")
            email_input.clear()
            email_input.send_keys(self.username)
            time.sleep(self.delay)  # Add delay for visibility
            
            # Enter password
            logger.info("Entering password...")
            password_input = self.driver.find_element(By.ID, "pseudonym_session_password")
            password_input.clear()
            password_input.send_keys(self.password)
            time.sleep(self.delay)  # Add delay for visibility
            
            # Take a screenshot before clicking login
            self._take_screenshot("before_canvas_login")
            
            # Click login button
            logger.info("Clicking login button...")
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            time.sleep(self.delay)  # Add delay for visibility
            
            # Take a screenshot after login attempt
            self._take_screenshot("after_canvas_login")
            
            # Check for "Stay signed in" or similar prompts
            try:
                logger.info("Looking for post-login confirmation prompts...")
                # Look for common confirmation buttons
                confirm_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                    "button:contains('Yes'), button:contains('Continue'), button:contains('Accept'), button:contains('Allow')")
                
                if confirm_buttons:
                    logger.info(f"Found {len(confirm_buttons)} confirmation buttons, clicking the first one...")
                    confirm_buttons[0].click()
                    time.sleep(self.delay)  # Add delay for visibility
            except Exception as e:
                logger.info(f"No post-login confirmation prompts found or error: {str(e)}")
                
        except Exception as e:
            logger.error(f"Canvas native login failed: {str(e)}")
            logger.error(traceback.format_exc())
            self._take_screenshot("canvas_login_error")
            raise
        
    def _login_generic(self):
        """Attempt a generic login by looking for common username/password fields"""
        logger.info("Attempting generic login...")
        
        try:
            # Take a screenshot before generic login
            self._take_screenshot("before_generic_login")
            
            # Look for username/email field
            logger.info("Looking for username/email field...")
            username_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[type='email'], input[type='text'], input[name='username'], input[name='email']")
            if username_fields:
                logger.info("Found username field, entering username...")
                username_fields[0].clear()
                username_fields[0].send_keys(self.username)
                time.sleep(self.delay)  # Add delay for visibility
                
                # Try to find a "Next" button first
                next_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button:contains('Next'), input[value='Next']")
                if next_buttons:
                    logger.info("Found Next button, clicking...")
                    next_buttons[0].click()
                else:
                    logger.info("No Next button found, pressing Enter...")
                    username_fields[0].send_keys(Keys.RETURN)
                    
                time.sleep(self.delay)  # Add delay for visibility
            
            # Take a screenshot after username
            self._take_screenshot("generic_after_username")
            
            # Look for password field
            logger.info("Looking for password field...")
            password_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
            if password_fields:
                logger.info("Found password field, entering password...")
                password_fields[0].clear()
                password_fields[0].send_keys(self.password)
                time.sleep(self.delay)  # Add delay for visibility
                
                # Take a screenshot after password
                self._take_screenshot("generic_after_password")
                
                # Try to find a submit button first
                submit_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                    "button[type='submit'], input[type='submit'], button:contains('Log in'), button:contains('Sign in'), button:contains('Continue')")
                if submit_buttons:
                    logger.info("Found submit button, clicking...")
                    submit_buttons[0].click()
                else:
                    logger.info("No submit button found, pressing Enter...")
                    password_fields[0].send_keys(Keys.RETURN)
                    
                time.sleep(self.delay)  # Add delay for visibility
                
            # Take a screenshot after login attempt
            self._take_screenshot("generic_after_login")
            
            # Check for "Stay signed in" or similar prompts
            try:
                logger.info("Looking for post-login confirmation prompts...")
                # Look for common confirmation buttons
                confirm_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                    "button:contains('Yes'), button:contains('Continue'), button:contains('Accept'), button:contains('Allow')")
                
                if confirm_buttons:
                    logger.info(f"Found {len(confirm_buttons)} confirmation buttons, clicking the first one...")
                    confirm_buttons[0].click()
                    time.sleep(self.delay)  # Add delay for visibility
            except Exception as e:
                logger.info(f"No post-login confirmation prompts found or error: {str(e)}")
                
        except Exception as e:
            logger.error(f"Generic login failed: {str(e)}")
            logger.error(traceback.format_exc())
            self._take_screenshot("generic_login_error")
    
    def get_courses(self):
        """Get all available courses"""
        logger.info("Fetching available courses...")
        try:
            # Navigate to the courses page
            self.driver.get(f"{self.canvas_url}/courses")
            time.sleep(self.delay)  # Add delay for visibility
            
            # Take a screenshot of the courses page
            self._take_screenshot("courses_page")
            
            # First try to find courses in the dashboard card view
            courses = self._get_courses_from_dashboard()
            
            # If no courses found in dashboard view, try the "All Courses" table view
            if not courses:
                logger.info("No courses found in dashboard view, trying 'All Courses' table view...")
                courses = self._get_courses_from_all_courses_table()
            
            if courses:
                logger.info(f"Found {len(courses)} courses")
                return courses
            else:
                # If still no courses found, try one more approach - the course list view
                logger.info("No courses found in table view, trying course list view...")
                return self._get_courses_from_list_view()
            
        except Exception as e:
            logger.error(f"Error fetching courses: {str(e)}")
            logger.error(traceback.format_exc())
            self._take_screenshot("courses_error")
            return []
            
    def _get_courses_from_dashboard(self):
        """Get courses from the dashboard card view"""
        try:
            # Check if dashboard cards are present
            if not self.driver.find_elements(By.CLASS_NAME, "ic-DashboardCard"):
                logger.info("No dashboard cards found")
                return []
                
            # Wait for course cards to load
            logger.info("Waiting for dashboard course cards to load...")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ic-DashboardCard"))
            )
            
            # Get all course cards
            course_cards = self.driver.find_elements(By.CLASS_NAME, "ic-DashboardCard")
            logger.info(f"Found {len(course_cards)} dashboard course cards")
            
            courses = []
            for card in course_cards:
                try:
                    title_element = card.find_element(By.CLASS_NAME, "ic-DashboardCard__header-title")
                    course_name = title_element.text.strip()
                    
                    # Get the course URL from the card
                    link_element = card.find_element(By.CSS_SELECTOR, "a.ic-DashboardCard__link")
                    course_url = link_element.get_attribute("href")
                    
                    # Extract course ID from URL
                    course_id = course_url.split("/courses/")[1].split("/")[0]
                    
                    courses.append({
                        "id": course_id,
                        "name": course_name,
                        "url": course_url
                    })
                    
                    logger.info(f"Found dashboard course: {course_name} (ID: {course_id})")
                except Exception as e:
                    logger.error(f"Error processing dashboard course card: {str(e)}")
                    logger.debug(traceback.format_exc())
            
            return courses
            
        except Exception as e:
            logger.error(f"Error fetching dashboard courses: {str(e)}")
            logger.debug(traceback.format_exc())
            return []
            
    def _get_courses_from_all_courses_table(self):
        """Get courses from the 'All Courses' table view"""
        try:
            # Check if we're on the All Courses page, if not navigate to it
            if "all_courses" not in self.driver.current_url:
                # Look for "All Courses" button or link
                all_courses_links = self.driver.find_elements(By.XPATH, 
                    "//a[contains(text(), 'All Courses') or contains(@title, 'All Courses')]")
                
                if all_courses_links:
                    logger.info("Clicking 'All Courses' link...")
                    all_courses_links[0].click()
                    time.sleep(self.delay)
                else:
                    # Try navigating directly to the all courses URL
                    logger.info("Navigating to All Courses page...")
                    self.driver.get(f"{self.canvas_url}/courses/all_courses")
                    time.sleep(self.delay)
            
            # Take a screenshot of the All Courses page
            self._take_screenshot("all_courses_page")
            
            # Wait for the course table to load
            logger.info("Waiting for course table to load...")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.course-list, table.ic-Table"))
            )
            
            # Find all course rows in the table
            course_rows = self.driver.find_elements(By.CSS_SELECTOR, "table.course-list tr, table.ic-Table tr")
            logger.info(f"Found {len(course_rows)} rows in course table")
            
            courses = []
            # Skip the header row
            for row in course_rows[1:]:
                try:
                    # Find the course name and link
                    course_link = row.find_element(By.CSS_SELECTOR, "a[href*='/courses/']")
                    course_name = course_link.text.strip()
                    course_url = course_link.get_attribute("href")
                    
                    # Extract course ID from URL
                    if "/courses/" in course_url:
                        course_id = course_url.split("/courses/")[1].split("/")[0]
                        
                        courses.append({
                            "id": course_id,
                            "name": course_name,
                            "url": course_url
                        })
                        
                        logger.info(f"Found table course: {course_name} (ID: {course_id})")
                except Exception as e:
                    logger.error(f"Error processing course row: {str(e)}")
                    logger.debug(traceback.format_exc())
            
            return courses
            
        except Exception as e:
            logger.error(f"Error fetching courses from table: {str(e)}")
            logger.debug(traceback.format_exc())
            self._take_screenshot("table_courses_error")
            return []
            
    def _get_courses_from_list_view(self):
        """Get courses from the course list view"""
        try:
            # Check if we need to navigate to the courses page
            if not self.driver.current_url.endswith("/courses"):
                logger.info("Navigating to courses page...")
                self.driver.get(f"{self.canvas_url}/courses")
                time.sleep(self.delay)
            
            # Take a screenshot of the courses page
            self._take_screenshot("courses_list_page")
            
            # Look for course links in any format
            logger.info("Looking for course links...")
            course_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/courses/']")
            logger.info(f"Found {len(course_links)} potential course links")
            
            courses = []
            for link in course_links:
                try:
                    course_url = link.get_attribute("href")
                    
                    # Skip links that don't point directly to a course
                    if "/courses/all" in course_url or "/courses/favorites" in course_url or "/courses/search" in course_url:
                        continue
                        
                    # Extract course ID from URL
                    if "/courses/" in course_url:
                        parts = course_url.split("/courses/")[1].split("/")
                        if len(parts) > 0 and parts[0].isdigit():
                            course_id = parts[0]
                            course_name = link.text.strip()
                            
                            # Skip empty or navigation links
                            if not course_name or course_name.lower() in ["all courses", "dashboard", "courses"]:
                                continue
                                
                            # Check if this course is already in our list
                            if not any(c["id"] == course_id for c in courses):
                                courses.append({
                                    "id": course_id,
                                    "name": course_name,
                                    "url": course_url
                                })
                                
                                logger.info(f"Found list course: {course_name} (ID: {course_id})")
                except Exception as e:
                    logger.error(f"Error processing course link: {str(e)}")
                    logger.debug(traceback.format_exc())
            
            return courses
            
        except Exception as e:
            logger.error(f"Error fetching courses from list: {str(e)}")
            logger.debug(traceback.format_exc())
            self._take_screenshot("list_courses_error")
            return []
    
    def process_course(self, course):
        """Process a single course and download all its files"""
        course_id = course["id"]
        course_name = course["name"]
        
        # Create a sanitized directory name for the course
        safe_course_name = self._sanitize_filename(course_name)
        course_dir = os.path.join(self.base_download_dir, safe_course_name)
        os.makedirs(course_dir, exist_ok=True)
        
        logger.info(f"\nProcessing course: {course_name}")
        
        # First, try to find files on the course homepage and in modules
        homepage_files_found = self._process_course_homepage(course_id, course_name, course_dir)
        
        # Then, try to find files in the modules section
        modules_files_found = self._process_course_modules(course_id, course_name, course_dir)
        
        # Finally, try the dedicated Files section as a fallback
        files_section_found = self._process_course_files_section(course_id, course_name, course_dir)
        
        if not (homepage_files_found or modules_files_found or files_section_found):
            logger.warning(f"No files found for course: {course_name}")
            
    def _process_course_homepage(self, course_id, course_name, course_dir):
        """Process the course homepage for downloadable files"""
        logger.info(f"Checking course homepage for files: {course_name}")
        
        # Navigate to the course homepage
        homepage_url = f"{self.canvas_url}/courses/{course_id}"
        logger.info(f"Navigating to course homepage: {homepage_url}")
        self.driver.get(homepage_url)
        time.sleep(self.delay)  # Add delay for visibility
        
        # Take a screenshot of the course homepage
        safe_course_name = self._sanitize_filename(course_name)
        self._take_screenshot(f"homepage_{safe_course_name}")
        
        # First, check for direct downloadable links on the homepage
        direct_files_found = self._process_direct_links(course_dir, "Homepage_Direct")
        
        # Then, click on each link on the homepage and look for downloadable files
        indirect_files_found = self._process_clickable_links(course_dir, "Homepage", homepage_url)
        
        return direct_files_found or indirect_files_found
        
    def _process_direct_links(self, course_dir, subfolder_name):
        """Process direct downloadable links on the current page"""
        logger.info(f"Looking for direct downloadable links on the current page")
        
        # Look for file links on the page
        file_links = self._find_downloadable_links()
        
        if file_links:
            logger.info(f"Found {len(file_links)} direct downloadable links")
            
            # Create a subfolder
            subfolder_dir = os.path.join(course_dir, subfolder_name)
            os.makedirs(subfolder_dir, exist_ok=True)
            
            # Download each file
            files_downloaded = False
            for link in file_links:
                try:
                    file_url = link.get_attribute("href")
                    file_name = link.text.strip()
                    
                    # If the link text is empty, try to get the filename from the URL
                    if not file_name:
                        file_name = os.path.basename(urlparse(file_url).path)
                        # Remove any query parameters
                        file_name = file_name.split("?")[0]
                        # URL decode the filename
                        file_name = unquote(file_name)
                    
                    # Sanitize the filename
                    safe_file_name = self._sanitize_filename(file_name)
                    if not safe_file_name.endswith(('.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.zip')):
                        safe_file_name += '.pdf'  # Default extension if none is detected
                        
                    # Download the file
                    if self._download_file(file_url, os.path.join(subfolder_dir, safe_file_name)):
                        files_downloaded = True
                except Exception as e:
                    logger.error(f"Error downloading direct file: {str(e)}")
                    logger.debug(traceback.format_exc())
            
            return files_downloaded
        else:
            logger.info("No direct downloadable links found")
            return False
            
    def _process_clickable_links(self, course_dir, subfolder_name, return_url):
        """Process clickable links on the current page and look for downloadable files on the resulting pages"""
        logger.info(f"Looking for clickable links on the current page")
        
        # Get all links on the page
        all_links = self.driver.find_elements(By.TAG_NAME, "a")
        
        # Filter out navigation links and empty links
        content_links = []
        for link in all_links:
            try:
                href = link.get_attribute("href")
                text = link.text.strip()
                
                # Skip empty links, navigation links, and links we can't interact with
                if not href or not text:
                    continue
                    
                # Skip common navigation links
                if text.lower() in ["home", "announcements", "grades", "people", "files", "syllabus", "modules", "settings", "dashboard"]:
                    continue
                    
                # Skip links to external sites
                if href and self.canvas_url in href:
                    content_links.append((href, text))
            except:
                pass
                
        logger.info(f"Found {len(content_links)} content links to process")
        
        if not content_links:
            logger.info("No content links found to process")
            return False
            
        # Create a subfolder for this page's content
        subfolder_dir = os.path.join(course_dir, subfolder_name)
        os.makedirs(subfolder_dir, exist_ok=True)
        
        files_downloaded = False
        
        # Process each link
        for i, (link_url, link_text) in enumerate(content_links):
            try:
                logger.info(f"Processing link {i+1}/{len(content_links)}: {link_text}")
                
                # Navigate to the link
                self.driver.get(link_url)
                time.sleep(self.delay * 2)  # Add extra delay for page to load
                
                # Take a screenshot
                safe_name = self._sanitize_filename(link_text)
                self._take_screenshot(f"link_{safe_name}")
                
                # Create a subfolder for this link
                link_dir = os.path.join(subfolder_dir, safe_name)
                os.makedirs(link_dir, exist_ok=True)
                
                # Look for download links on this page
                download_links = self._find_enhanced_download_links()
                
                if download_links:
                    logger.info(f"Found {len(download_links)} download links on page: {link_text}")
                    
                    # Download each file
                    for dl_link in download_links:
                        try:
                            file_url = dl_link.get_attribute("href")
                            file_name = dl_link.text.strip()
                            
                            # If the link text is empty, try to get the filename from the URL or use the parent link text
                            if not file_name:
                                file_name = os.path.basename(urlparse(file_url).path)
                                # Remove any query parameters
                                file_name = file_name.split("?")[0]
                                # URL decode the filename
                                file_name = unquote(file_name)
                                
                            # If still no filename, use the parent link text
                            if not file_name or file_name == "":
                                file_name = link_text
                            
                            # Sanitize the filename
                            safe_file_name = self._sanitize_filename(file_name)
                            if not safe_file_name.endswith(('.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.zip')):
                                safe_file_name += '.pdf'  # Default extension if none is detected
                                
                            # Download the file
                            if self._download_file(file_url, os.path.join(link_dir, safe_file_name)):
                                files_downloaded = True
                        except Exception as e:
                            logger.error(f"Error downloading file from link page: {str(e)}")
                            logger.debug(traceback.format_exc())
                else:
                    # If no download links found, check for Canvas-specific download buttons
                    try:
                        # Look for Canvas download buttons
                        download_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                            "a.icon-download, a.file_download_btn, a[download], a.download_submissions_link")
                        
                        if download_buttons:
                            logger.info(f"Found {len(download_buttons)} Canvas download buttons")
                            
                            for button in download_buttons:
                                try:
                                    download_url = button.get_attribute("href")
                                    if not download_url:
                                        continue
                                        
                                    # Try to get a filename
                                    file_name = button.get_attribute("download") or button.get_attribute("title") or link_text
                                    
                                    # Sanitize the filename
                                    safe_file_name = self._sanitize_filename(file_name)
                                    if not safe_file_name.endswith(('.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.zip')):
                                        safe_file_name += '.pdf'  # Default extension if none is detected
                                        
                                    # Download the file
                                    if self._download_file(download_url, os.path.join(link_dir, safe_file_name)):
                                        files_downloaded = True
                                except Exception as e:
                                    logger.error(f"Error downloading from Canvas button: {str(e)}")
                                    logger.debug(traceback.format_exc())
                        else:
                            # If still no download buttons, try clicking on any file links in the content
                            file_links = self.driver.find_elements(By.CSS_SELECTOR, 
                                "a.instructure_file_link, a.inline_disabled, a[id^='file_']")
                            
                            if file_links:
                                logger.info(f"Found {len(file_links)} file links in content")
                                
                                for file_link in file_links:
                                    try:
                                        # Get the link URL and text
                                        file_url = file_link.get_attribute("href")
                                        file_name = file_link.text.strip() or link_text
                                        
                                        # Sanitize the filename
                                        safe_file_name = self._sanitize_filename(file_name)
                                        if not safe_file_name.endswith(('.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.zip')):
                                            safe_file_name += '.pdf'  # Default extension if none is detected
                                            
                                        # Download the file
                                        if self._download_file(file_url, os.path.join(link_dir, safe_file_name)):
                                            files_downloaded = True
                                    except Exception as e:
                                        logger.error(f"Error downloading from file link: {str(e)}")
                                        logger.debug(traceback.format_exc())
                    except Exception as e:
                        logger.error(f"Error checking for Canvas-specific elements: {str(e)}")
                        logger.debug(traceback.format_exc())
                
            except Exception as e:
                logger.error(f"Error processing link {link_text}: {str(e)}")
                logger.debug(traceback.format_exc())
                
            # Navigate back to the original page
            self.driver.get(return_url)
            time.sleep(self.delay)  # Add delay for visibility
        
        return files_downloaded
        
    def _find_enhanced_download_links(self):
        """Find all downloadable links on the current page with enhanced detection"""
        # Start with basic downloadable links
        downloadable_links = self._find_downloadable_links()
        
        # Also look for Canvas-specific download links
        try:
            canvas_download_links = self.driver.find_elements(By.CSS_SELECTOR, 
                "a.file_download_btn, a.icon-download, a[download], a.instructure_file_link")
            
            for link in canvas_download_links:
                try:
                    href = link.get_attribute("href")
                    if href and href not in [dl.get_attribute("href") for dl in downloadable_links]:
                        downloadable_links.append(link)
                except:
                    pass
        except:
            pass
            
        # Look for links with specific text that suggests they are downloads
        try:
            text_download_links = self.driver.find_elements(By.XPATH, 
                "//a[contains(text(), 'Download') or contains(text(), 'download') or contains(text(), '.pdf') or contains(text(), '.doc')]")
            
            for link in text_download_links:
                try:
                    href = link.get_attribute("href")
                    if href and href not in [dl.get_attribute("href") for dl in downloadable_links]:
                        downloadable_links.append(link)
                except:
                    pass
        except:
            pass
                
        return downloadable_links
            
    def _process_course_modules(self, course_id, course_name, course_dir):
        """Process the course modules for downloadable files"""
        logger.info(f"Checking course modules for files: {course_name}")
        
        # Navigate to the modules page
        modules_url = f"{self.canvas_url}/courses/{course_id}/modules"
        logger.info(f"Navigating to modules page: {modules_url}")
        self.driver.get(modules_url)
        time.sleep(self.delay)  # Add delay for visibility
        
        # Take a screenshot of the modules page
        safe_course_name = self._sanitize_filename(course_name)
        self._take_screenshot(f"modules_{safe_course_name}")
        
        # Check if there are any modules
        modules = self.driver.find_elements(By.CSS_SELECTOR, ".context_module")
        if not modules:
            logger.info("No modules found for this course")
            return False
            
        logger.info(f"Found {len(modules)} modules")
        
        files_found = False
        
        # Process each module
        for i, module in enumerate(modules):
            try:
                # Get the module name
                module_name_elem = module.find_element(By.CSS_SELECTOR, ".name")
                module_name = module_name_elem.text.strip()
                safe_module_name = self._sanitize_filename(module_name)
                
                logger.info(f"Processing module: {module_name}")
                
                # Create a directory for this module
                module_dir = os.path.join(course_dir, safe_module_name)
                os.makedirs(module_dir, exist_ok=True)
                
                # Try to expand the module if it's collapsed
                try:
                    # Check if the module is collapsed
                    if "collapsed" in module.get_attribute("class"):
                        # Find and click the expand button
                        expand_button = module.find_element(By.CSS_SELECTOR, ".expand_module_link")
                        logger.info(f"Expanding module: {module_name}")
                        expand_button.click()
                        time.sleep(self.delay)  # Wait for expansion
                except Exception as e:
                    logger.info(f"Module may already be expanded or couldn't expand: {str(e)}")
                
                # Find all items in the module
                module_items = module.find_elements(By.CSS_SELECTOR, ".context_module_item")
                logger.info(f"Found {len(module_items)} items in module: {module_name}")
                
                # Process each item in the module
                for item in module_items:
                    try:
                        # Check if this is a file item
                        item_classes = item.get_attribute("class")
                        item_name_elem = item.find_element(By.CSS_SELECTOR, ".item_name")
                        item_name = item_name_elem.text.strip()
                        
                        # Find links in this item
                        links = item.find_elements(By.TAG_NAME, "a")
                        
                        for link in links:
                            try:
                                link_url = link.get_attribute("href")
                                
                                # Skip if not a file link
                                if not link_url or not self._is_downloadable_link(link_url):
                                    continue
                                    
                                # Get the file name
                                file_name = item_name
                                if not file_name:
                                    file_name = link.text.strip()
                                if not file_name:
                                    file_name = os.path.basename(urlparse(link_url).path)
                                    file_name = file_name.split("?")[0]  # Remove query parameters
                                    file_name = unquote(file_name)  # URL decode
                                
                                # Sanitize the filename
                                safe_file_name = self._sanitize_filename(file_name)
                                if not safe_file_name.endswith(('.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.zip')):
                                    safe_file_name += '.pdf'  # Default extension if none is detected
                                
                                # Download the file
                                if self._download_file(link_url, os.path.join(module_dir, safe_file_name)):
                                    files_found = True
                            except Exception as e:
                                logger.error(f"Error processing link in module item: {str(e)}")
                                logger.debug(traceback.format_exc())
                    except Exception as e:
                        logger.error(f"Error processing module item: {str(e)}")
                        logger.debug(traceback.format_exc())
            except Exception as e:
                logger.error(f"Error processing module {i+1}: {str(e)}")
                logger.debug(traceback.format_exc())
                
        return files_found
        
    def _process_course_files_section(self, course_id, course_name, course_dir):
        """Process the dedicated Files section of the course"""
        logger.info(f"Checking Files section for course: {course_name}")
        
        # Navigate to the Files section of the course
        files_url = f"{self.canvas_url}/courses/{course_id}/files"
        logger.info(f"Navigating to Files section: {files_url}")
        self.driver.get(files_url)
        time.sleep(self.delay)  # Add delay for visibility
        
        # Take a screenshot of the files page
        safe_course_name = self._sanitize_filename(course_name)
        self._take_screenshot(f"files_page_{safe_course_name}")
        
        # Wait for the files page to load
        try:
            logger.info("Waiting for files to load...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ef-item-row"))
            )
            
            # Create a "Files" subfolder
            files_dir = os.path.join(course_dir, "Files")
            os.makedirs(files_dir, exist_ok=True)
            
            # Process the current folder and its files
            self._process_folder(files_dir, files_url)
            return True
            
        except TimeoutException:
            logger.warning(f"No files found in Files section or section not accessible for course: {course_name}")
            self._take_screenshot(f"no_files_{safe_course_name}")
            return False
            
    def _find_downloadable_links(self):
        """Find all downloadable links on the current page"""
        # Look for links that might be files
        all_links = self.driver.find_elements(By.TAG_NAME, "a")
        
        # Filter for downloadable links
        downloadable_links = []
        for link in all_links:
            try:
                href = link.get_attribute("href")
                if href and self._is_downloadable_link(href):
                    downloadable_links.append(link)
            except:
                pass
                
        return downloadable_links
        
    def _is_downloadable_link(self, url):
        """Check if a URL is likely to be a downloadable file"""
        if not url:
            return False
            
        # Check for Canvas file download patterns
        if "/files/" in url and ("/download" in url or "?download=1" in url or "?download_frd=1" in url):
            return True
            
        # Check for common file extensions
        file_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.zip', 
                          '.jpg', '.jpeg', '.png', '.gif', '.mp3', '.mp4', '.mov', '.avi']
        
        for ext in file_extensions:
            if url.lower().endswith(ext) or f"{ext}?" in url.lower():
                return True
                
        return False
    
    def _process_folder(self, current_dir, folder_url):
        """Process a folder and its contents recursively"""
        folder_name = os.path.basename(current_dir)
        logger.info(f"Processing folder: {folder_name}")
        self.driver.get(folder_url)
        time.sleep(self.delay)  # Add delay for visibility
        
        # Take a screenshot of the folder
        self._take_screenshot(f"folder_{self._sanitize_filename(folder_name)}")
        
        # Wait for the folder contents to load
        try:
            logger.info("Waiting for folder contents to load...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ef-directory"))
            )
        except TimeoutException:
            logger.warning(f"No items found in folder '{folder_name}' or folder is empty")
            return
        
        # Get all items in the current folder
        time.sleep(self.delay)  # Give a moment for all items to load
        items = self.driver.find_elements(By.CLASS_NAME, "ef-item-row")
        logger.info(f"Found {len(items)} items in folder '{folder_name}'")
        
        # First, process all subfolders
        subfolder_count = 0
        for item in items:
            try:
                # Check if the item is a folder
                item_classes = item.get_attribute("class")
                if "ef-item-folder" in item_classes:
                    subfolder_count += 1
                    folder_name_element = item.find_element(By.CLASS_NAME, "ef-name-col__text")
                    folder_name = folder_name_element.text.strip()
                    safe_folder_name = self._sanitize_filename(folder_name)
                    
                    # Create subfolder
                    subfolder_path = os.path.join(current_dir, safe_folder_name)
                    os.makedirs(subfolder_path, exist_ok=True)
                    logger.info(f"Created subfolder: {safe_folder_name}")
                    
                    # Click on the folder to navigate into it
                    logger.info(f"Navigating into subfolder: {folder_name}")
                    folder_name_element.click()
                    time.sleep(self.delay)  # Add delay for visibility
                    
                    # Get the current URL (which is now the subfolder URL)
                    subfolder_url = self.driver.current_url
                    
                    # Process the subfolder recursively
                    self._process_folder(subfolder_path, subfolder_url)
                    
                    # Navigate back to the parent folder
                    logger.info(f"Navigating back to parent folder")
                    self.driver.get(folder_url)
                    time.sleep(self.delay)  # Add delay for visibility
                    
                    # Wait for the folder contents to load again
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "ef-directory"))
                    )
                    
                    # Refresh the items list
                    time.sleep(self.delay)
                    items = self.driver.find_elements(By.CLASS_NAME, "ef-item-row")
            except Exception as e:
                logger.error(f"Error processing subfolder: {str(e)}")
                logger.debug(traceback.format_exc())
                self._take_screenshot(f"subfolder_error_{self._sanitize_filename(folder_name)}")
        
        logger.info(f"Processed {subfolder_count} subfolders in '{folder_name}'")
        
        # Then, process all files
        file_count = 0
        for item in items:
            try:
                # Check if the item is a file (not a folder)
                item_classes = item.get_attribute("class")
                if "ef-item-folder" not in item_classes:
                    file_count += 1
                    file_name_element = item.find_element(By.CLASS_NAME, "ef-name-col__text")
                    file_name = file_name_element.text.strip()
                    safe_file_name = self._sanitize_filename(file_name)
                    
                    # Get the file URL
                    file_link = item.find_element(By.CSS_SELECTOR, "a.ef-name-col__link")
                    file_url = file_link.get_attribute("href")
                    
                    # Download the file
                    self._download_file(file_url, os.path.join(current_dir, safe_file_name))
            except Exception as e:
                logger.error(f"Error processing file: {str(e)}")
                logger.debug(traceback.format_exc())
                
        logger.info(f"Processed {file_count} files in '{folder_name}'")
    
    def _download_file(self, file_url, file_path):
        """Download a file from Canvas"""
        file_name = os.path.basename(file_path)
        try:
            # Check if file already exists and skip if needed
            if self.skip_existing and os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                if file_size > 0:  # Only skip if the file has content
                    logger.info(f"Skipping existing file: {file_name}")
                    return True
            
            # Click on the file to get to the file preview page
            logger.info(f"Navigating to file: {file_name}")
            self.driver.get(file_url)
            time.sleep(self.delay)  # Add delay for visibility
            
            # Take a screenshot of the file preview page
            self._take_screenshot(f"file_preview_{self._sanitize_filename(file_name)}")
            
            # Wait for the download button to appear
            try:
                logger.info("Looking for download button...")
                download_button = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.icon-download"))
                )
                logger.info("Found primary download button")
            except TimeoutException:
                # Try alternative download button selectors
                try:
                    logger.info("Primary download button not found, trying alternatives...")
                    download_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".file_download_btn, .file-download-btn, a[download]"))
                    )
                    logger.info("Found alternative download button")
                except TimeoutException:
                    # If we can't find a download button, try to get the file directly
                    logger.warning(f"No download button found for {file_name}. Trying direct download...")
                    self._take_screenshot(f"no_download_button_{self._sanitize_filename(file_name)}")
                    response = self.session.get(file_url, stream=True)
                    if response.status_code == 200:
                        self._save_file_with_progress(response, file_path)
                        return True
                    else:
                        logger.error(f"Failed to download file: {file_name}")
                        return False
            
            # Get the actual download URL
            download_url = download_button.get_attribute("href")
            logger.info(f"Got download URL for {file_name}")
            
            # Download the file using requests
            logger.info(f"Downloading: {file_name}")
            response = self.session.get(download_url, stream=True)
            response.raise_for_status()
            
            # Save the file with progress bar
            self._save_file_with_progress(response, file_path)
            return True
            
        except Exception as e:
            logger.error(f"Error downloading file {file_name}: {str(e)}")
            logger.debug(traceback.format_exc())
            self._take_screenshot(f"download_error_{self._sanitize_filename(file_name)}")
            
            # Create an empty placeholder file to indicate we tried to download it
            try:
                with open(file_path, "wb") as f:
                    pass
                logger.info(f"Created empty placeholder for failed download: {file_name}")
            except Exception as write_error:
                logger.error(f"Failed to create placeholder file: {str(write_error)}")
            return False
            
    def _save_file_with_progress(self, response, file_path):
        """Save a file with a progress bar"""
        file_name = os.path.basename(file_path)
        
        # Get the file size if available
        file_size = int(response.headers.get('content-length', 0))
        
        # Create a progress bar
        progress = tqdm(total=file_size, unit='B', unit_scale=True, desc=file_name)
        
        # Save the file
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    progress.update(len(chunk))
        
        progress.close()
        logger.info(f"Downloaded: {file_name} ({self._format_size(file_size)})")
        
    def _format_size(self, size_bytes):
        """Format file size in a human-readable format"""
        if size_bytes == 0:
            return "0B"
        size_names = ("B", "KB", "MB", "GB", "TB")
        i = int(math.log(size_bytes, 1024)) if size_bytes > 0 else 0
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    def _sanitize_filename(self, filename):
        """Sanitize a filename to be safe for all operating systems"""
        # Replace invalid characters with underscores
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Trim leading/trailing spaces and periods
        filename = filename.strip('. ')
        
        # Ensure the filename is not empty
        if not filename:
            filename = "unnamed"
            
        return filename
    
    def run(self):
        """Run the full scraping process"""
        try:
            # Create the base download directory
            os.makedirs(self.base_download_dir, exist_ok=True)
            logger.info(f"Created download directory: {os.path.abspath(self.base_download_dir)}")
            
            # Login to Canvas
            if not self.login():
                logger.error("Login failed. Exiting.")
                return False
            
            # Get all available courses
            courses = self.get_courses()
            if not courses:
                logger.error("No courses found. Exiting.")
                return False
            
            logger.info(f"Found {len(courses)} courses to process")
            
            # Process each course
            for i, course in enumerate(courses, 1):
                logger.info(f"Processing course {i} of {len(courses)}: {course['name']}")
                self.process_course(course)
            
            logger.info(f"\nAll files have been downloaded to: {os.path.abspath(self.base_download_dir)}")
            return True
            
        except Exception as e:
            logger.error(f"An error occurred during the scraping process: {str(e)}")
            logger.error(traceback.format_exc())
            return False
            
        finally:
            # Close the browser
            if self.driver:
                logger.info("Closing browser...")
                self.driver.quit()
                logger.info("Browser closed.")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Canvas File Scraper - Download all your Canvas course files")
    
    parser.add_argument("--url", "-u", help="Canvas URL (e.g., https://ycp.instructure.com)")
    parser.add_argument("--username", "-e", help="Canvas username/email")
    parser.add_argument("--password", "-p", help="Canvas password (not recommended, use interactive prompt instead)")
    parser.add_argument("--dir", "-d", default="Canvas_Downloads", help="Download directory (default: Canvas_Downloads)")
    parser.add_argument("--no-skip", action="store_true", help="Don't skip existing files (re-download all)")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode (no visible browser)")
    parser.add_argument("--delay", type=int, default=2, help="Delay in seconds between actions for visibility (default: 2)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    return parser.parse_args()

def main():
    """Main function to run the Canvas Scraper"""
    print("=" * 60)
    print("Canvas File Scraper - Download all your Canvas course files")
    print("=" * 60)
    
    # Parse command line arguments
    args = parse_args()
    
    # Set up logging level
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Get Canvas URL
    canvas_url = args.url
    if not canvas_url:
        canvas_url = input("Enter your Canvas URL (e.g., https://ycp.instructure.com): ")
    
    # Get username
    username = args.username
    if not username:
        username = input("Enter your Canvas username/email: ")
    
    # Get password
    password = args.password
    if not password:
        password = getpass.getpass("Enter your Canvas password: ")
    
    # Get download directory
    download_dir = args.dir
    if not download_dir:
        download_dir = input("Enter download directory (default: Canvas_Downloads): ") or "Canvas_Downloads"
    
    # Get skip existing files option
    skip_existing = not args.no_skip
    if not args.url:  # Only ask if not provided via command line
        skip_existing = input("Skip existing files? (Y/n): ").lower() != 'n'
    
    # Create and run the scraper
    scraper = CanvasScraper(canvas_url, username, password, download_dir, skip_existing, args.headless, args.delay)
    
    logger.info("\nStarting Canvas scraper...")
    logger.info("This will open a Chrome browser window and log in to Canvas.")
    logger.info("Please do not close the browser window during the process.")
    logger.info("=" * 60)
    logger.info(f"Log file is being saved to: {os.path.abspath(log_filename)}")
    logger.info(f"Screenshots will be saved to: {os.path.abspath('screenshots')}")
    
    try:
        success = scraper.run()
        
        if success:
            logger.info("\n" + "=" * 60)
            logger.info(f"Canvas scraper completed successfully!")
            logger.info(f"All files have been downloaded to: {os.path.abspath(download_dir)}")
            logger.info("=" * 60)
        else:
            logger.info("\n" + "=" * 60)
            logger.info("Canvas scraper encountered errors.")
            logger.info("Some files may have been downloaded.")
            logger.info(f"Check the log file for details: {os.path.abspath(log_filename)}")
            logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc())
        logger.info("\n" + "=" * 60)
        logger.info("Canvas scraper encountered a critical error.")
        logger.info(f"Check the log file for details: {os.path.abspath(log_filename)}")
        logger.info("=" * 60)

if __name__ == "__main__":
    main()
