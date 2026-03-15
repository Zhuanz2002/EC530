from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# In-memory database
users = {}
next_user_id = 1


# Models
class UserCreate(BaseModel):
    username: str


class NoteCreate(BaseModel):
    text: str


# Create user
@app.post("/users")
def create_user(user: UserCreate):
    global next_user_id

    # check duplicate username
    for u in users.values():
        if u["username"] == user.username:
            raise HTTPException(status_code=409, detail="Username already exists")

    new_user = {
        "id": next_user_id,
        "username": user.username,
        "notes": []
    }

    users[next_user_id] = new_user
    next_user_id += 1

    return new_user


# Get user by id
@app.get("/users/{user_id}")
def get_user(user_id: int):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")

    return users[user_id]


# Add note
@app.post("/users/{user_id}/notes")
def add_note(user_id: int, note: NoteCreate):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")

    users[user_id]["notes"].append(note.text)

    return {"message": "Note added", "notes": users[user_id]["notes"]}


# Read notes
@app.get("/users/{user_id}/notes")
def get_notes(user_id: int):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")

    return {"notes": users[user_id]["notes"]}