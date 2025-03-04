from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uvicorn


class Student(BaseModel):
    id: int = Field(..., description="Unique identifier for the student")
    name: str = Field(..., min_length=2, max_length=50, description="Student's full name")
    email: str = Field(EmailStr, description="Student's email address")
    tests_taken: List[int] = []


class Test(BaseModel):
    id: int = Field(..., description="Unique identifier for the test")
    name: str = Field(..., min_length=2, max_length=100, description="Name of the test")
    max_score: int = Field(..., description="Maximum possible score")


class TestResult(BaseModel):
    student_id: int = Field(..., description="ID of the student taking the test")
    test_id: int = Field(..., description="ID of the test taken")
    score: int = Field(..., description="Score obtained in the test")


class ResponseMessage(BaseModel):
    message: str


app = FastAPI()

students: Dict[int, Student] = {}
tests: Dict[int, Test] = {}
test_results: List[TestResult] = []


@app.post("/students/", response_model=Student, tags=["Students"])
async def create_student(student: Student):
    if student.id in students:
        raise HTTPException(status_code=400, detail=f"Student with ID {student.id} already exists")
    students[student.id] = student
    return student


@app.get("/students/{student_id}", response_model=Student, tags=["Students"])
async def get_student(student_id: int = Path(..., description="ID of the student to retrieve")):
    if student_id not in students:
        raise HTTPException(status_code=404, detail=f"Student with ID {student_id} not found")
    return students[student_id]


@app.get("/students/", response_model=List[Student], tags=["Students"])
async def get_all_students():
    return list(students.values())


@app.post("/tests/", response_model=Test, tags=["Tests"])
async def create_test(test: Test):
    if test.id in tests:
        raise HTTPException(status_code=400, detail=f"Test with ID {test.id} already exists")
    tests[test.id] = test
    return test


@app.get("/tests/{test_id}", response_model=Test, tags=["Tests"])
async def get_test(test_id: int = Path(..., description="ID of the test to retrieve")):
    if test_id not in tests:
        raise HTTPException(status_code=404, detail=f"Test with ID {test_id} not found")
    return tests[test_id]


@app.get("/tests/", response_model=List[Test], tags=["Tests"])
async def get_all_tests():
    return list(tests.values())


@app.post("/results/", response_model=TestResult, tags=["Results"])
async def submit_test_result(result: TestResult):
    if result.student_id not in students:
        raise HTTPException(status_code=404, detail=f"Student with ID {result.student_id} not found")

    if result.test_id not in tests:
        raise HTTPException(status_code=404, detail=f"Test with ID {result.test_id} not found")


    test = tests[result.test_id]
    if result.score < 0 or result.score > test.max_score:
        raise HTTPException(
            status_code=400,
            detail=f"Score must be between 0 and {test.max_score}"
        )


    if result.test_id not in students[result.student_id].tests_taken:
        students[result.student_id].tests_taken.append(result.test_id)

    test_results.append(result)
    return result


@app.get("/results/student/{student_id}", response_model=List[TestResult], tags=["Results"])
async def get_student_results(student_id: int = Path(..., description="ID of the student")):
    if student_id not in students:
        raise HTTPException(status_code=404, detail=f"Student with ID {student_id} not found")

    return [result for result in test_results if result.student_id == student_id]


@app.get("/results/test/{test_id}", response_model=List[TestResult], tags=["Results"])
async def get_test_results(test_id: int = Path(..., description="ID of the test")):
    if test_id not in tests:
        raise HTTPException(status_code=404, detail=f"Test with ID {test_id} not found")

    return [result for result in test_results if result.test_id == test_id]


@app.get("/results/test/{test_id}/average", response_model=Dict[str, Any], tags=["Analytics"])
async def get_test_average(test_id: int = Path(..., description="ID of the test")):
    if test_id not in tests:
        raise HTTPException(status_code=404, detail=f"Test with ID {test_id} not found")

    test_scores = [result.score for result in test_results if result.test_id == test_id]

    if not test_scores:
        return {"test_id": test_id, "average_score": 0, "test_name": tests[test_id].name, "participants": 0}

    average = sum(test_scores) / len(test_scores)

    return {
        "test_id": test_id,
        "test_name": tests[test_id].name,
        "average_score": round(average, 2),
        "participants": len(test_scores)
    }


@app.get("/results/test/{test_id}/highest", response_model=Dict[str, Any], tags=["Analytics"])
async def get_test_highest(test_id: int = Path(..., description="ID of the test")):
    if test_id not in tests:
        raise HTTPException(status_code=404, detail=f"Test with ID {test_id} not found")

    test_results_filtered = [result for result in test_results if result.test_id == test_id]

    if not test_results_filtered:
        return {"test_id": test_id, "highest_score": 0, "test_name": tests[test_id].name, "student_id": None}

    highest_result = max(test_results_filtered, key=lambda x: x.score)

    return {
        "test_id": test_id,
        "test_name": tests[test_id].name,
        "highest_score": highest_result.score,
        "student_id": highest_result.student_id,
        "student_name": students[highest_result.student_id].name
    }


@app.delete("/students/{student_id}", response_model=ResponseMessage, tags=["Students"])
async def delete_student(student_id: int = Path(..., description="ID of the student to delete")):
    if student_id not in students:
        raise HTTPException(status_code=404, detail=f"Student with ID {student_id} not found")


    del students[student_id]

    global test_results
    test_results = [result for result in test_results if result.student_id != student_id]

    return ResponseMessage(message=f"Student with ID {student_id} has been deleted")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)