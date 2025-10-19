import pdfplumber
import re
from pprint import pprint
import json

# returns text from degreeworks pdf
def extract_degreeworks_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Extract department/codes from line
# return list with codes extracted from line
def course_codes(line, data):
    all_courses = []
    department = ""
    dep_and_code = ""
    strs = line.split(' ')

    for s in strs:
        if len(s) > 0 and s[0].isalpha() and s[0].isupper():
            department = s
        elif s == "or":
            continue
        else:
            # If range of courses extracted from text(ex: 121:130)
            # only add courses that actually exist in that range
            if ':' in s:
                ranges = s.split(':')

                for course in data["courses"]:
                    if department in course['code']:
                        match = re.search(r'(\d+)([A-Za-z]*)', course['code'])
                        numeric = int(match.group(1))
                        full_code = match.group(0)

                        if numeric >= int(ranges[0]) and numeric <= int(ranges[1]):
                            all_courses.append(department + full_code)
            else:
                s = s.replace('@', 'A')
                dep_and_code = department + s
                all_courses.append(dep_and_code)

    return all_courses


# Extract course codes from lines
def clean_lines(lines, data):
    courses_map = {}

    for line in lines:
        num_courses = re.search(r'(\d+)\s+Class', line)   # Extract how many classes are needed from folowing list
        num_needed = int(num_courses.group(1)) if num_courses else 0

        if num_needed != 0:
            courses_map[num_needed]= []

            # Extract rest of string after 'in' - department + numbers
            department = re.search(r'\s+in\s+(.+)$', line)
            if not department:
                continue

            # Update line - only department, 'or', and course codes
            line = department.group(1)

            course_list = course_codes(line, data)
            courses_map[num_needed].append(course_list)

    return courses_map


# Extract lines with 'still needed'(courses user needs to take to fulfill grad requirements)
# Takes in full text, returns list of lines that contain 'still needed'
def parse_still_needed_lines(text):
    still_needed = []

    lines = text.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i]
        
        if 'Still needed:' in line:
            full_text = line
            i += 1
            
            # Capture continuation lines
            while i < len(lines):
                next_line = lines[i].strip()
                
                # Stop if empty or new section
                if not next_line or 'Still needed:' in next_line:
                    break
                
                # if line has 'or', still part of current line
                if next_line.startswith('or ') or ' or ' in next_line:
                    full_text += ' ' + next_line
                    i += 1
                else:
                    break
            
            still_needed.append(full_text)
        else:
            i += 1
    return still_needed

if __name__ == "__main__":
    with open('../data/courses.json', 'r') as f:
        course_data = json.load(f)

    text = extract_degreeworks_text("/Users/zacharylai/Desktop/zach_degreeworks.pdf")
    still_needed_lines = parse_still_needed_lines(text)
    codes_final = clean_lines(still_needed_lines, course_data)
    pprint(codes_final)