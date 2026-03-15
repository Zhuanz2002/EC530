# Exercise 2 – FastAPI User Notes API

## User Stories

- As a user, I can create an account with a username.
- As a user, I can retrieve my account by id.
- If username already exists → return 409.
- As a user, I can add text notes.
- As a user, I can read my text notes.

## API Endpoints

POST /users  
Create a new user.

GET /users/{user_id}  
Retrieve user by ID.

POST /users/{user_id}/notes  
Add a text note.

GET /users/{user_id}/notes  
Retrieve notes for a user.

## Run

```bash
pip install fastapi uvicorn
uvicorn main:app --reload