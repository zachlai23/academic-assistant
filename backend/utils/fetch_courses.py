import requests
import json

base_url = "https://anteaterapi.com/v2/rest/"

def get_department_courses(department_name):
    url = f"{base_url}courses?department={department_name}"

    response = requests.get(url)

    if response.status_code == 200:
        department_data = response.json()
        return department_data
    else:
        print(f"Failed to retrieve data {response.status_code}")

# Extract data from api output to courses.json format
def transform_course(api_course):
    course_dict = {}
    course_dict["code"] = api_course['id']
    course_dict["course_number"] = api_course['courseNumeric']
    course_dict["name"] = api_course['title']
    course_dict["prerequisites"] = [d['id'] for d in api_course['prerequisites']]
    course_dict["prereq_tree"] = api_course['prerequisiteTree']
    course_dict["credits"] = api_course['minUnits']
    course_dict["description"] = api_course['description']
    course_dict["offered_quarters"] = api_course['terms']

    return course_dict


if __name__ == "__main__":
    departments = ["COMPSCI", "I%26C%20SCI", "IN4MATX"]  # Add your departments here

    all_courses = []

    for department in departments:
        print(f"Fetching courses for {department}...")
        dep_data = get_department_courses(department)

        if dep_data:
            for course in dep_data["data"]:
                transformed = transform_course(course)
                all_courses.append(transformed)
            print(f"Added {len(dep_data['data'])} courses from {department}")
        else:
            print(f"Failed to fetch data for {department}")

    courses_dict = {"courses": all_courses}

    with open("../data/courses.json", "w") as f:
        json.dump(courses_dict, f, indent=4)

    print(f"\nTotal courses saved: {len(all_courses)}")



