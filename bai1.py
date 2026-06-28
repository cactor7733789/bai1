from fastapi import FastAPI
app = FastAPI()
students = ["An","Bình","Dương"]
@app.get("/students") 
def get_students():
    return {
        "status": "success",
        "message": "Danh sách sinh viên hệ thống",
        "data": students  
    }