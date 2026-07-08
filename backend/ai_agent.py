import os
import json
from datetime import date

from anthropic import Anthropic
from dotenv import load_dotenv
from sqlalchemy.orm import Session

import models

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"

# ---------------------------------------------------------------------------
# TOOL DEFINITIONS — this is what makes NutriMate an "action agent" and not
# just a chatbot. The model decides when to call these based on conversation.
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name": "log_meal",
        "description": "Log a food or meal the user says they ate/are eating, with your best "
                        "nutrition estimate, into their food diary.",
        "input_schema": {
            "type": "object",
            "properties": {
                "food_name": {"type": "string", "description": "Short name of the food/meal"},
                "calories": {"type": "number"},
                "protein_g": {"type": "number"},
                "carbs_g": {"type": "number"},
                "fat_g": {"type": "number"},
                "meal_type": {"type": "string", "enum": ["breakfast", "lunch", "dinner", "snack"]},
            },
            "required": ["food_name", "calories", "meal_type"],
        },
    },
    {
        "name": "log_water",
        "description": "Log a quantity of water the user drank, in millilitres.",
        "input_schema": {
            "type": "object",
            "properties": {"amount_ml": {"type": "number"}},
            "required": ["amount_ml"],
        },
    },
    {
        "name": "log_weight",
        "description": "Log the user's current body weight in kilograms.",
        "input_schema": {
            "type": "object",
            "properties": {"weight_kg": {"type": "number"}},
            "required": ["weight_kg"],
        },
    },
    {
        "name": "get_daily_summary",
        "description": "Fetch the user's totals for today (calories, macros, water, meals "
                        "logged) so you can give grounded, accurate feedback.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

SYSTEM_PROMPT = """You are NutriMate AI — an expert, warm, encouraging health & nutrition
research and action agent. You don't just chat, you take real actions in the user's diary:

- If the user mentions eating or drinking something, estimate its nutrition sensibly and
  call log_meal (or log_water for plain water).
- If the user mentions their current weight, call log_weight.
- Before giving progress feedback, call get_daily_summary to ground your answer in real data.
- Give safe, evidence-based general nutrition/fitness guidance. For medical symptoms or
  diagnoses, gently recommend seeing a doctor — never diagnose.
- Keep replies concise, practical, and encouraging. Use at most one or two emojis.
"""


def _execute_tool(db: Session, user_id: int, name: str, tool_input: dict) -> dict:
    if name == "log_meal":
        entry = models.MealLog(
            user_id=user_id,
            food_name=tool_input.get("food_name", "food"),
            calories=tool_input.get("calories", 0),
            protein_g=tool_input.get("protein_g", 0),
            carbs_g=tool_input.get("carbs_g", 0),
            fat_g=tool_input.get("fat_g", 0),
            meal_type=tool_input.get("meal_type", "snack"),
        )
        db.add(entry)
        db.commit()
        return {"status": "logged", "food_name": entry.food_name, "calories": entry.calories}

    if name == "log_water":
        entry = models.WaterLog(user_id=user_id, amount_ml=tool_input["amount_ml"])
        db.add(entry)
        db.commit()
        return {"status": "logged", "amount_ml": entry.amount_ml}

    if name == "log_weight":
        entry = models.WeightLog(user_id=user_id, weight_kg=tool_input["weight_kg"])
        db.add(entry)
        db.commit()
        return {"status": "logged", "weight_kg": entry.weight_kg}

    if name == "get_daily_summary":
        today = date.today()
        meals = db.query(models.MealLog).filter(models.MealLog.user_id == user_id).all()
        todays_meals = [m for m in meals if m.logged_at.date() == today]
        waters = db.query(models.WaterLog).filter(models.WaterLog.user_id == user_id).all()
        todays_water = sum(w.amount_ml for w in waters if w.logged_at.date() == today)
        return {
            "total_calories": sum(m.calories for m in todays_meals),
            "total_protein_g": sum(m.protein_g for m in todays_meals),
            "total_carbs_g": sum(m.carbs_g for m in todays_meals),
            "total_fat_g": sum(m.fat_g for m in todays_meals),
            "water_ml": todays_water,
            "meals_logged": len(todays_meals),
        }

    return {"error": "unknown tool"}


def chat_with_agent(db: Session, user_id: int, message: str, history: list):
    """Runs the agentic tool-use loop and returns (reply_text, updated_history)."""
    messages = list(history) + [{"role": "user", "content": message}]

    for _ in range(5):  # safety cap on tool-use round trips
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = _execute_tool(db, user_id, block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        text = "".join(b.text for b in response.content if b.type == "text")
        messages.append({"role": "assistant", "content": text})
        return text, messages

    return "I had trouble completing that action — could you rephrase?", messages


def generate_meal_plan(profile: dict) -> str:
    prompt = f"""Create a personalized ONE-DAY meal plan for this person:
{json.dumps(profile, default=str)}

Return clean, concise Markdown with these sections: Breakfast, Lunch, Dinner, 2 Snacks.
For each item give approx calories and macros (P/C/F in grams). End with a "Daily Totals" line.
Keep it realistic, culturally flexible, and achievable — no fad diets."""
    response = client.messages.create(
        model=MODEL, max_tokens=1200, messages=[{"role": "user", "content": prompt}]
    )
    return "".join(b.text for b in response.content if b.type == "text")


def daily_tip() -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=150,
        messages=[{
            "role": "user",
            "content": "Give one short, specific, evidence-based nutrition or fitness tip "
                       "for today. Just the tip itself, 1-2 sentences, no preamble.",
        }],
    )
    return "".join(b.text for b in response.content if b.type == "text")
