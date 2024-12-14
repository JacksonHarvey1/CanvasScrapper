import requests
from bs4 import BeautifulSoup

# Session with cookies
session = requests.Session()
session.cookies.update({"your_cookie_key": "your_cookie_value"})  # Add cookies after manual login

# Access courses page
CANVAS_URL = "https://ycp.instructure.com/"

response = session.get(f"{CANVAS_URL}/courses")
soup = BeautifulSoup(response.content, "html.parser")

# Find course links
courses = soup.select("a.course_link_selector")  # Adjust selector
for course in courses:
    course_name = course.text
    print(f"Processing course: {course_name}")
    course_url = course["href"]
    course_page = session.get(course_url)

    # Parse course files
    course_soup = BeautifulSoup(course_page.content, "html.parser")
    files = course_soup.select("a.file_link_selector")  # Adjust selector
    for file in files:
        file_url = file["href"]
        print(f"Downloading file: {file_url}")
        file_content = session.get(file_url).content
        with open(file.text, "wb") as f:
            f.write(file_content)
