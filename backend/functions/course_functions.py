import json 
import asyncio
import os

async def recommend_courses(completed_courses=None, major="Computer Science", num_recommendations=3):
    course_recs = []
    with open('data/courses.json', 'r') as file:
        data = json.load(file)

        if completed_courses == None:
            completed_courses = []

        for course in data['courses']:
            if course['code'] not in completed_courses and all(prereq in completed_courses for prereq in course['prerequisites']):
                if len(course_recs) < num_recommendations:
                    course_recs.append([course['code'], course['name'], course['description']])
        return course_recs

