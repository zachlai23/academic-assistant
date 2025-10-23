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
# return list with course objects that match the codes
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

                # Loop through all courses and keep numbers if an actual course matches
                # More efficient way? Will have lots more courses when expand to all majors
                for course in data["courses"]:
                    if department in course['code']:
                        match = re.search(r'(\d+)([A-Za-z]*)', course['code'])
                        numeric = int(match.group(1))
                        full_code = match.group(0)

                        if numeric >= int(ranges[0]) and numeric <= int(ranges[1]):
                            all_courses.append(course)
            else:
                s = s.replace('@', 'A')
                dep_and_code = department + s
                # Find matching course object
                for course in data["courses"]:
                    if course['code'] == dep_and_code:
                        all_courses.append(course)
                        break

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

def extract_courses_needed(filepath):
    with open('data/courses.json', 'r') as f:
        course_data = json.load(f)

    text = extract_degreeworks_text(filepath)
    still_needed_lines = parse_still_needed_lines(text)
    codes_final = clean_lines(still_needed_lines, course_data)
    return codes_final

# Takes in degreeworks pdf, returns list of course objects of courses user has completed
def extract_courses_completed(filepath):
    text = extract_degreeworks_text(filepath)
    completed = []

    # Detect completed courses if line has grade + term
    grade_pattern = r'\b([A-D][+-]?|F|IP|T)\b'# Regex for grade
    term_pattern = r'(FALL|WINTER|SPRING|SS)'

    lines = text.split('\n')
    for line in lines:
        has_grade = re.search(grade_pattern, line)
        has_term = re.search(term_pattern, line)
        
        if has_grade and has_term:
            # If line starts with (T) its transfer course that doesnt satisfy uci requirement - skip
            if line.strip().startswith('(T)'):
                continue
            
            # Find course codes in the line
            course_pattern = r'([A-Za-z&]+)\s+(\d+[A-Za-z]?)'
            matches = re.findall(course_pattern, line)
            
            for match in matches:
                dept = match[0].upper().replace(' ', '')
                num = match[1].upper().replace(' ', '')
                
                code_with_space = f"{match[0]} {match[1]}"
                # If (T) later in line, skip course, add uci equiv
                if f"(T){code_with_space}" in line:
                    continue
                
                # validate + add
                if dept.replace('&', '').isalpha() and num[0].isdigit() and len(dept) > 1:
                    code = dept + num
                    if code not in completed:
                        completed.append(code)

    # pprint(completed)
    return completed


if __name__ == "__main__":
    # codes = extract_courses_needed("/Users/zacharylai/Desktop/zach_degreeworks.pdf")
    extract_courses_completed("/Users/zacharylai/Desktop/zach_degreeworks.pdf")
    # pprint(codes)