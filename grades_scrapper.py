from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time

driver = webdriver.Chrome()
main_site = "https://my.sdu.edu.kz/"

driver.get(main_site)
print("Current URL:", driver.current_url) 

wait = WebDriverWait(driver, 15)

# Username
username_input = wait.until(
    EC.presence_of_element_located((By.ID, "username"))
)
username_input.send_keys("your id")

# Password
password_input = wait.until(
    EC.presence_of_element_located((By.ID, "password"))
)
password_input.send_keys("your pass")

# Login button
login_button = wait.until(
    EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @name='LogIn']"))
)
login_button.click()

# Wait for Transcript link
transcript_link = wait.until(
    EC.presence_of_element_located((By.XPATH, "//a[@href='?mod=transkript']"))
)

print("Login successful")
print("Current URL after login:", driver.current_url)

# Click on Transcript
print("Navigating to Transcript...")
transcript_link.click()

# Wait for page to load
wait.until(EC.presence_of_element_located((By.XPATH, "//table")))
print("Transcript page loaded")

soup = BeautifulSoup(driver.page_source, 'html.parser')

# Extract student info
faculty = soup.find('td', text='faculty:').find_next('td').text.strip()
specialty = soup.find('td', text='specialty:').find_next('td').text.strip()
language = soup.find('td', text='language:').find_next('td').text.strip()

# Initialize lists to store data
courses_data = []
current_semester = None

# Process all rows
rows = soup.find_all('tr')
for row in rows:
    # Check if this is a semester header
    semester_header = row.find('td', {'style': 'font-weight:bold; color:#333; padding-top:10px; padding-bottom:2px; font-size:12px'})
    if semester_header:
        current_semester = semester_header.text.strip()
        continue
    
    # Check if this is a course row
    cols = row.find_all('td')
    if len(cols) == 8 and not any('course code' in col.text.lower() for col in cols):
        course_code = cols[0].text.strip()
        # Skip if it's not a valid course code (e.g., footer rows)
        if not course_code or 'Total' in course_code:
            continue
            
        course_data = {
            'Semester': current_semester,
            'Course Code': course_code,
            'Course Title': cols[1].text.strip(),
            'Credit': cols[2].text.strip(),
            'ECTS': cols[3].text.strip(),
            'Grade': cols[4].text.strip(),
            'Letter Grade': cols[5].text.strip(),
            'Point': cols[6].text.strip(),
            'Traditional': cols[7].text.strip()
        }
        courses_data.append(course_data)

# Create DataFrame
df = pd.DataFrame(courses_data)

# Add student info as metadata
metadata_df = pd.DataFrame([{
    'Faculty': faculty,
    'Specialty': specialty,
    'Language': language
}])

# Save to CSV files
df.to_csv('transcript_courses.csv', index=False, encoding='utf-8')
metadata_df.to_csv('transcript_metadata.csv', index=False, encoding='utf-8')

print("\nTranscript data has been saved to:")
print("1. transcript_courses.csv - Contains all course information")
print("2. transcript_metadata.csv - Contains student program information")

time.sleep(5)
driver.quit()
