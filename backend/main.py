import uuid
from datetime import date
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import bcrypt

import models
import ai_agent
from database import engine, get_db, Base

Base.metadata.create_all(bind=engine)

SESSIONS: dict[str, int] = {}  # token -> user_id  (simple in-memory session store)

app = FastAPI(title="NutriMate AI — Health & Nutrition Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not authorization or authorization not in SESSIONS:
        raise HTTPException(401, "Not authenticated")
    user = db.get(models.User, SESSIONS[authorization])
    if not user:
        raise HTTPException(401, "Invalid session")
    return user


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class RegisterIn(BaseModel):
    username: str
    password: str


class LoginIn(BaseModel):
    username: str
    password: str


class ProfileIn(BaseModel):
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    activity_level: str = "moderate"
    goal: str = "maintain"


class ChatIn(BaseModel):
    message: str
    history: list = []


class MealIn(BaseModel):
    food_name: str
    calories: float
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    meal_type: str = "snack"


class WaterIn(BaseModel):
    amount_ml: float


class WeightIn(BaseModel):
    weight_kg: float


# ---------------------------------------------------------------------------
# Helper: BMI / BMR / TDEE / macro calculator
# ---------------------------------------------------------------------------
def calc_metrics(p: ProfileIn) -> dict:
    bmi = round(p.weight_kg / ((p.height_cm / 100) ** 2), 1)

    if p.gender.lower().startswith("m"):
        bmr = 10 * p.weight_kg + 6.25 * p.height_cm - 5 * p.age + 5
    else:
        bmr = 10 * p.weight_kg + 6.25 * p.height_cm - 5 * p.age - 161

    activity_factors = {
        "sedentary": 1.2, "light": 1.375, "moderate": 1.55,
        "active": 1.725, "very_active": 1.9,
    }
    tdee = bmr * activity_factors.get(p.activity_level, 1.55)

    goal_adjustment = {"lose": -500, "maintain": 0, "gain": 500}
    target_calories = tdee + goal_adjustment.get(p.goal, 0)

    protein_g = round((target_calories * 0.30) / 4)
    carbs_g = round((target_calories * 0.40) / 4)
    fat_g = round((target_calories * 0.30) / 9)

    if bmi < 18.5:
        bmi_category = "Underweight"
    elif bmi < 25:
        bmi_category = "Normal"
    elif bmi < 30:
        bmi_category = "Overweight"
    else:
        bmi_category = "Obese"

    return {
        "bmi": bmi, "bmi_category": bmi_category,
        "bmr": round(bmr), "tdee": round(tdee),
        "target_calories": round(target_calories),
        "target_protein_g": protein_g, "target_carbs_g": carbs_g, "target_fat_g": fat_g,
    }


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@app.post("/api/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.query(models.User).filter_by(username=data.username).first():
        raise HTTPException(400, "Username already taken")
    hashed = bcrypt.hashpw(data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = models.User(username=data.username, password_hash=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = str(uuid.uuid4())
    SESSIONS[token] = user.id
    return {"token": token, "username": user.username}


@app.post("/api/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(username=data.username).first()
    if not user or not bcrypt.checkpw(data.password.encode("utf-8"), user.password_hash.encode("utf-8")):
        raise HTTPException(401, "Invalid username or password")
    token = str(uuid.uuid4())
    SESSIONS[token] = user.id
    return {"token": token, "username": user.username}


@app.post("/api/logout")
def logout(authorization: Optional[str] = Header(None)):
    SESSIONS.pop(authorization, None)
    return {"status": "logged out"}


# ---------------------------------------------------------------------------
# Profile & calculators
# ---------------------------------------------------------------------------
@app.post("/api/profile")
def save_profile(data: ProfileIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(models.Profile).filter_by(user_id=user.id).first()
    if not profile:
        profile = models.Profile(user_id=user.id)
        db.add(profile)
    for k, v in data.model_dump().items():
        setattr(profile, k, v)
    db.commit()
    return calc_metrics(data)


@app.get("/api/profile")
def get_profile(user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(models.Profile).filter_by(user_id=user.id).first()
    if not profile:
        raise HTTPException(404, "No profile yet")
    p_in = ProfileIn(
        age=profile.age, gender=profile.gender, height_cm=profile.height_cm,
        weight_kg=profile.weight_kg, activity_level=profile.activity_level, goal=profile.goal,
    )
    base = {c.name: getattr(profile, c.name) for c in profile.__table__.columns if c.name != "id"}
    return {**base, **calc_metrics(p_in)}


# ---------------------------------------------------------------------------
# AI agent — chat (with real tool-driven actions) + meal plan + tip
# ---------------------------------------------------------------------------
@app.post("/api/chat")
def chat(data: ChatIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    reply, updated_history = ai_agent.chat_with_agent(db, user.id, data.message, data.history)
    return {"reply": reply, "history": updated_history}


@app.get("/api/mealplan")
def mealplan(user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(models.Profile).filter_by(user_id=user.id).first()
    if not profile:
        raise HTTPException(400, "Please set up your profile first")
    profile_dict = {c.name: getattr(profile, c.name) for c in profile.__table__.columns if c.name != "id"}
    return {"plan": ai_agent.generate_meal_plan(profile_dict)}


@app.get("/api/tip")
def tip():
    return {"tip": ai_agent.daily_tip()}


# ---------------------------------------------------------------------------
# Meal / water / weight logging (manual, non-AI paths)
# ---------------------------------------------------------------------------
@app.post("/api/meals")
def add_meal(data: MealIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    entry = models.MealLog(user_id=user.id, **data.model_dump())
    db.add(entry)
    db.commit()
    return {"status": "ok"}


@app.get("/api/meals")
def list_meals(user=Depends(get_current_user), db: Session = Depends(get_db)):
    meals = (
        db.query(models.MealLog)
        .filter_by(user_id=user.id)
        .order_by(models.MealLog.logged_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": m.id, "food_name": m.food_name, "calories": m.calories,
            "protein_g": m.protein_g, "carbs_g": m.carbs_g, "fat_g": m.fat_g,
            "meal_type": m.meal_type, "logged_at": m.logged_at.isoformat(),
        }
        for m in meals
    ]


@app.post("/api/water")
def add_water(data: WaterIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    entry = models.WaterLog(user_id=user.id, amount_ml=data.amount_ml)
    db.add(entry)
    db.commit()
    return {"status": "ok"}


@app.get("/api/water/today")
def water_today(user=Depends(get_current_user), db: Session = Depends(get_db)):
    logs = db.query(models.WaterLog).filter_by(user_id=user.id).all()
    total = sum(w.amount_ml for w in logs if w.logged_at.date() == date.today())
    return {"total_ml": total}


@app.post("/api/weight")
def add_weight(data: WeightIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    entry = models.WeightLog(user_id=user.id, weight_kg=data.weight_kg)
    db.add(entry)
    db.commit()
    return {"status": "ok"}


@app.get("/api/weight/history")
def weight_history(user=Depends(get_current_user), db: Session = Depends(get_db)):
    logs = (
        db.query(models.WeightLog).filter_by(user_id=user.id).order_by(models.WeightLog.logged_at).all()
    )
    return [{"weight_kg": w.weight_kg, "logged_at": w.logged_at.isoformat()} for w in logs]


@app.get("/api/summary/today")
def summary_today(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return ai_agent._execute_tool(db, user.id, "get_daily_summary", {})


@app.get("/")
def root():
    return {"message": "NutriMate AI backend is running. See /docs for API reference."}
