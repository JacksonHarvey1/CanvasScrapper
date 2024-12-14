

import requests
import os

# Replace these with your details
API_TOKEN = "13250~fwz6KZX78QZ7ufcHRw8fex4kDEaP3RZR3v8VBQYmHYLMWZhHJuKKCE9ANeTZNRkT"
BASE_URL = "https://canvas.instructure.com/api/v1"
DOWNLOAD_FOLDER = "canvas_files"

# Setup headers for API requests
headers = {
    "Authorization": f"Bearer {API_TOKEN}"
}

def fetch_courses():
    """Fetch all courses available to the user."""
    response = requests.get(f"{BASE_URL}/courses", headers=headers)
    try:
        response.raise_for_status()
        data = response.json()
        print("Courses JSON Response:", data)  # Debug: Print the response
        return data
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.text}")
        return []
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return []


def fetch_files(course_id):
    """Fetch files for a specific course."""
    response = requests.get(f"{BASE_URL}/courses/{course_id}/files", headers=headers)
    if response.status_code == 403:
        print(f"403 Forbidden for course ID: {course_id}. Check permissions.")
    response.raise_for_status()
    return response.json()


def download_file(file_url, file_name):
    """Download a file from Canvas."""
    response = requests.get(file_url, headers=headers, stream=True)
    response.raise_for_status()
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_FOLDER, file_name)
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Downloaded: {file_name}")

def main():
    courses = fetch_courses()
    for course in courses:
        course_name = course.get('name', 'Unnamed Course')
        print(f"Processing course: {course_name}")

        # Skip restricted courses
        if course.get('access_restricted_by_date', False):
            print(f"Skipping restricted course: {course_name}")
            continue

        # Skip courses without an 'id'
        if 'id' not in course:
            print(f"Skipping course without ID: {course}")
            continue

        # Fetch and download files if applicable
        try:
            files = fetch_files(course["id"])
            for file in files:
                download_file(file["url"], file["display_name"])
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching files for course {course_name}: {e}")



if __name__ == "__main__":
    main()
