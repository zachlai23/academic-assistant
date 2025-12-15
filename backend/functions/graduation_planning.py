import uuid
from collections import defaultdict
from typing import List, Dict, Any
from functions.course_functions import plan_next_quarter

graduation_sessions = {}

# Graduation planning continually calls quarter plan function while keeping track of classes added/remaining requirements
# saves state for graduation planning
class GraduationSession:

    def __init__(self, original_completed, original_grad_reqs, graduation_quarter, quarters_to_plan):
        self.original_completed = original_completed.copy()
        self.original_grad_reqs = {k: v.copy() for k, v in original_grad_reqs.items()}
        self.graduation_quarter = graduation_quarter
        self.planned_quarters = []
        self.current_completed = original_completed.copy()
        self.current_grad_reqs = {k: v.copy() for k, v in original_grad_reqs.items()}
        self.next_quarter = "Winter 2026"
        self.quarters_to_plan = quarters_to_plan


    # update class instance completed/grad reqs after a quarter is planned
    def add_quarter(self, quarter_name, courses):
        self.planned_quarters.append({
            "quarter": quarter_name,
            "courses": courses
        })
        
        # update completed courses
        for course in courses:
            self.current_completed.append(course["code"])
        
        # update grad requirements
        self.current_grad_reqs = update_requirements(self.current_grad_reqs, courses)

    # Returns complete graduation plan summary
    def get_summary(self):
        total_courses = sum(len(q["courses"]) for q in self.planned_quarters)
        total_units = sum(sum(c.get("credits", 4) for c in q["courses"]) for q in self.planned_quarters)
        
        return {
            "graduation_quarter": self.graduation_quarter,
            "quarters_planned": len(self.planned_quarters),
            "total_courses": total_courses,
            "total_units": total_units,
            "plan": self.planned_quarters,
            "requirements_remaining": len(self.current_grad_reqs) > 0
        }

# Takes in quarter name, returns next quarter
def get_next_quarter(curr_quarter):
    parts = curr_quarter.split()
    season, year = parts[0], int(parts[1])

    if season == "Fall":
        return f"Winter {year + 1}"
    elif season == "Winter":
        return f"Spring {year}"
    elif season == "Spring":
        return f"Fall {year}"
    return None

# returns updated grad_reqs after planning courses for graduation
def update_requirements(grad_reqs, planned_courses):
    updated_reqs = {}
    planned_codes = [course["code"] for course in planned_courses]
    
    # each item in form num required:list of course objects
    for num_required, courses in grad_reqs.items():
        # remove planned courses
        remaining = [c for c in courses if c["code"] not in planned_codes]
        
        # update num required
        num_satisfied = len([c for c in courses if c["code"] in planned_codes])
        new_required = int(num_required) - num_satisfied
        
        # keep requirement in dict if still needed
        if new_required > 0 and remaining:
            updated_reqs[str(new_required)] = remaining
    
    return updated_reqs
 
# Initialize grad planning session - create session id + class instance
# Returns dict with session id and planning info
async def start_graduation_planning(graduation_quarter, completed_courses, grad_reqs):
    session_id = str(uuid.uuid4())[:8]

    curr_quarter = "Winter 2026"
    quarters_until = 0
    quarters_to_plan = []

    while curr_quarter != graduation_quarter:
        quarters_until += 1
        quarters_to_plan.append(curr_quarter)
        curr_quarter = get_next_quarter(curr_quarter)

    quarters_to_plan.append(graduation_quarter)
    quarters_until += 1
        
    if quarters_until <= 0:
        return {"error": f"Graduation quarter is invalid or in the past"}
    
    # Create session
    session = GraduationSession(completed_courses, grad_reqs, graduation_quarter, quarters_to_plan)
    graduation_sessions[session_id] = session
        
    return {
        "session_id": session_id,
        "graduation_quarter": graduation_quarter,
        "quarters_to_plan": quarters_to_plan,
        "quarters_remaining": quarters_until,
        "next_quarter": quarters_to_plan[0] if quarters_to_plan else None,
        "message": f"Started planning for {graduation_quarter}. Plan {quarters_until} quarters. Start with {quarters_to_plan[0]}."
    }

# Call quarter plan function with the updated completed courses/grad reqs
async def add_quarter_to_plan(session_id, quarter_name, selected_courses):
    if session_id not in graduation_sessions:
        return {"error": "Session not found"}
    
    session = graduation_sessions[session_id]
    
    # Error/duplicate validation
    already_planned = [
        c["code"] for q in session.planned_quarters for c in q["courses"]
    ]

    for course in selected_courses:
        if course["code"] in already_planned:
            return {"error": f"{course['code']} already planned"}
    
    session.add_quarter(quarter_name, selected_courses)
    
    # bool for if grad requirements satisfied
    requirements_met = len(session.current_grad_reqs) == 0
    
    if quarter_name == session.graduation_quarter:
        session.next_quarter = None
    else:
        session.next_quarter = get_next_quarter(quarter_name)
    
    return {
        "quarter_added": quarter_name,
        "courses_added": len(selected_courses),
        "courses": [{"code": c["code"], "name": c["name"]} for c in selected_courses],
        "total_units": sum(c.get("credits", 4) for c in selected_courses),
        "requirements_remaining": not requirements_met,
        "next_quarter": session.next_quarter,
        "message": f"Added {len(selected_courses)} courses for {quarter_name}."
    }

# Select courses based on requirement groups
async def get_graduation_plan_for_quarter(session_id, quarter_name):
    if session_id not in graduation_sessions:
        return {"error": "Session not found"}
    
    session = graduation_sessions[session_id]
    
    courses_needed = 3  # Fix later to ask user how many courses per quarter
    
    # Returns all possible courses user can take
    all_available = await plan_next_quarter(
        completed_courses=session.current_completed,
        grad_reqs=session.current_grad_reqs,
        preferred_num_courses=courses_needed,
        single_q_planning=False
    )
    
    if "error" in all_available:
        return all_available
    
    selected_courses = smart_course_selection(
        all_available["available_courses"],
        session.current_grad_reqs,
        courses_needed
    )
    
    return {
        "selected_courses": selected_courses,
        "num_selected": len(selected_courses),
        "message": f"Auto-selected {len(selected_courses)} courses for {quarter_name}"
    }

# Select courses based on requirement groups, prioritize courses from groups with smaller requirement numbers
def smart_course_selection(available_courses, grad_reqs, num_courses):
    selected = []
    
    # group courses by requirement, need to fix the key ids so lists arent merged with same keys
    courses_by_requirement = {}
    for course in available_courses:
        req = course.get("satisfies_requirement")
        if req not in courses_by_requirement:
            courses_by_requirement[req] = []
        courses_by_requirement[req].append(course)
    
    # sort requirement groups
    requirement_priority = sorted(
        courses_by_requirement.keys(),
        key=lambda req: len(courses_by_requirement[req])
    )
    
    # select at least one course from each requirement group considering cumber of courses per quarter
    for req in requirement_priority:
        if len(selected) >= num_courses:
            break
        # get courses from this requirement that aren't selected yet
        req_courses = [
            c for c in courses_by_requirement[req] 
            if c["code"] not in [s["code"] for s in selected]
        ]
        if req_courses:
            selected.append(req_courses[0])
    
    # If courses left to be planned fill remaining slots with priority courses
    while len(selected) < num_courses:
        remaining = [
            c for c in available_courses 
            if c["code"] not in [s["code"] for s in selected]
        ]
        if not remaining:
            break
        for req in requirement_priority:
            req_courses = [
                c for c in remaining 
                if c.get("satisfies_requirement") == req
            ]
            if req_courses:
                selected.append(req_courses[0])
                break
        else:
            selected.append(remaining[0])
    
    return selected

# get final summary of grad plan
async def finish_graduation_plan(session_id):
    if session_id not in graduation_sessions:
        return {"error": "Session not found"}
    
    session = graduation_sessions[session_id]
    summary = session.get_summary()
    
    del graduation_sessions[session_id]
    
    return summary