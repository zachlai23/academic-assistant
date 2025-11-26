import requests
import json
from collections import defaultdict
import time

base_url = "https://anteaterapi.com/v2/rest/"

def get_department_courses(department_name):
    url = f"{base_url}courses?department={department_name}"

    response = requests.get(url)

    if response.status_code == 200:
        department_data = response.json()
        return department_data
    else:
        print(f"Failed to retrieve data {response.status_code}")

def get_grade_data(department, course):
    dept_encoded = department.replace("&", "%26").replace(" ", "%20")
    url = f"{base_url}grades/aggregateByCourse?department={dept_encoded}&courseNumber={course['courseNumber']}"

    response = requests.get(url)

    if response.status_code == 200:
        grade_data = response.json()

        if not grade_data.get('data') or len(grade_data['data']) == 0:
            print(f"No grade data for {department} {course['courseNumber']}")
            return "unknown"

        avg_gpa = grade_data['data'][0]['averageGPA']

        if avg_gpa is None:
            return "unknown"

        if avg_gpa >= 3.5:
            difficulty = "easy"
        elif avg_gpa >= 3.0:
            difficulty = "medium"
        else:
            difficulty = "hard"
        return difficulty
    else:
        print(f"Failed to retrieve data {response.status_code}")

# Extract data from api output to courses.json format
def transform_course(api_course, department):
    course_dict = {}
    course_dict["code"] = api_course['id']
    course_dict["course_number"] = api_course['courseNumeric']
    course_dict["name"] = api_course['title']
    course_dict["prerequisites"] = [d['id'] for d in api_course['prerequisites']]
    course_dict["prereq_tree"] = api_course['prerequisiteTree']
    course_dict["credits"] = api_course['minUnits']
    course_dict["description"] = api_course['description']
    course_dict["offered_quarters"] = api_course['terms']

    course_dict["difficulty"] = get_grade_data(department, api_course)

    return course_dict


if __name__ == "__main__":
    # Populate courses.json
    departments = ["COMPSCI", "I%26C%20SCI", "IN4MATX"]
    department_actual_names = ["COMPSCI", "I&CSCI", "IN4MATX"]

    all_courses = defaultdict(list)

    for i, department in enumerate(departments):
        print(f"Fetching courses for {department}...")
        dep_data = get_department_courses(department)

        if dep_data:
            for course in dep_data["data"]:
                transformed = transform_course(course, department)
                all_courses[department_actual_names[i]].append(transformed)

                time.sleep(0.1)
            print(f"Added {len(dep_data['data'])} courses from {department}")
        else:
            print(f"Failed to fetch data for {department}")

    courses_dict = {"courses": all_courses}

    with open("../data/courses.json", "w") as f:
        json.dump(courses_dict, f, indent=4)

    print(f"\nTotal courses saved: {len(all_courses)}")



