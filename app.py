import json
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, session, url_for


BASE_DIR = Path(__file__).resolve().parent
CONTENT_FILE = BASE_DIR / "data" / "course_content.json"
SIMULATOR_FILE = BASE_DIR / "data" / "simulator_content.json"
QUIZ_FILE = BASE_DIR / "data" / "quiz_content.json"
STATE_FILE = BASE_DIR / "instance" / "user_state.json"

app = Flask(__name__)
app.secret_key = "cookeria-simulator-dev"


def load_json_file(file_path):
    with file_path.open(encoding="utf-8") as json_file:
        return json.load(json_file)


def load_content():
    """Load the shared course content so routes stay data-driven."""
    return load_json_file(CONTENT_FILE)


def load_simulator_content():
    """Load simulator definitions and recipe rules from structured data."""
    return load_json_file(SIMULATOR_FILE)

def load_quiz_content():
    """Load quiz questions and end-page content from structured data."""
    return load_json_file(QUIZ_FILE)


def timestamp():
    """Create a readable timestamp for simple backend activity logs."""
    return datetime.now().isoformat(timespec="seconds")


def default_state():
    """Single-user progress storage for this project phase."""
    return {
        "started": False,
        "started_at": None,
        "last_updated": None,
        "learning_steps_visited": [],
        "learning_selections": [],
        "simulator_visits": 0,
        "simulator_runs": [],
        "quiz_answers": [],
        "actions": [],
    }


def save_state(state):
    STATE_FILE.parent.mkdir(exist_ok=True)
    state["last_updated"] = timestamp()
    with STATE_FILE.open("w", encoding="utf-8") as state_file:
        json.dump(state, state_file, indent=2)


def load_state():
    if not STATE_FILE.exists():
        save_state(default_state())

    with STATE_FILE.open(encoding="utf-8") as state_file:
        state = json.load(state_file)

    state_updated = False
    for key, value in default_state().items():
        if key not in state:
            state[key] = value
            state_updated = True

    if state_updated:
        save_state(state)

    return state


def append_action(state, action_type, **details):
    action = {"type": action_type, "timestamp": timestamp()}
    action.update(details)
    state["actions"].append(action)


def reset_progress():
    state = default_state()
    state["started"] = True
    state["started_at"] = timestamp()
    append_action(state, "start_clicked")
    save_state(state)
    session.pop("simulator_discoveries", None)


def record_learning_step(step):
    content = load_content()
    step_data = get_learning_step(content["learning_steps"], step)
    state = load_state()

    if not state["started"]:
        state["started"] = True
        state["started_at"] = timestamp()
        append_action(state, "auto_started_from_learning", step=step)

    if step not in state["learning_steps_visited"]:
        state["learning_steps_visited"].append(step)

    append_action(
        state,
        "learning_step_visited",
        step=step,
        title=step_data["title"],
    )
    save_state(state)


def record_quiz_visit(step):
    state = load_state()
    append_action(state, "quiz_step_visited", step=step)
    save_state(state)

def check_quiz_answer(question, form_data):
    if question["type"] == "ingredient":
        butter = form_data.get("butter")
        flour = form_data.get("flour")
        sugar = form_data.get("sugar")

        return (
            butter == question["correct_answer"]["butter"]
            and flour == question["correct_answer"]["flour"]
            and sugar == question["correct_answer"]["sugar"]
        ), {
            "butter": butter,
            "flour": flour,
            "sugar": sugar,
        }

    if question["type"] == "multiple_choice":
        answer = form_data.get("answer")
        return answer == question["correct_answer"], {
            "answer": answer,
        }

    return False, {}


def record_quiz_answer(step, question, user_response, is_correct):
    state = load_state()
    state["quiz_answers"] = [entry for entry in state["quiz_answers"] if entry["step"] != step]

    state["quiz_answers"].append(
        {
            "step": step,
            "question_type": question["type"],
            "response": user_response,
            "correct": is_correct,
            "timestamp": timestamp(),
        }
    )

    append_action(
        state,
        "quiz_answer_submitted",
        step=step,
        correct=is_correct,
    )
    save_state(state)


def reset_quiz_progress():
    state = load_state()
    state["quiz_answers"] = []
    append_action(state, "quiz_restarted")
    save_state(state)


def clear_saved_results():
    save_state(default_state())


def record_simulator_entry():
    state = load_state()
    state["simulator_visits"] += 1
    append_action(state, "simulator_entered", visit_number=state["simulator_visits"])
    save_state(state)


def record_simulator_run(selections, result):
    state = load_state()
    state["simulator_runs"].append(
        {
            "timestamp": timestamp(),
            "ingredients": selections,
            "cookie_type": result["cookie_type"],
            "recipe_id": result.get("recipe_id"),
        }
    )
    append_action(
        state,
        "simulator_baked",
        ingredients=selections,
        cookie_type=result["cookie_type"],
    )
    save_state(state)


def get_quiz_progress(quiz_questions, state):
    answered_steps = sorted(
        {
            entry["step"]
            for entry in state.get("quiz_answers", [])
            if get_quiz_question(quiz_questions, entry.get("step")) is not None
        }
    )
    total_questions = len(quiz_questions)
    completed = len(answered_steps) >= total_questions
    next_step = None

    for question in quiz_questions:
        if question["id"] not in answered_steps:
            next_step = question["id"]
            break

    return {
        "answered_steps": answered_steps,
        "completed": completed,
        "next_step": next_step,
    }


def get_quiz_response_for_step(state, step):
    for entry in state.get("quiz_answers", []):
        if entry.get("step") == step:
            return entry
    return None


def summarize_level_usage(state):
    counts = {"low": 0, "medium": 0, "high": 0}

    for run in state.get("simulator_runs", []):
        for level in run.get("ingredients", {}).values():
            if level in counts:
                counts[level] += 1

    most_used_level = max(counts, key=counts.get)
    if counts[most_used_level] == 0:
        return {"label": "Most-used ingredient level", "value": "No simulator attempts yet"}

    return {
        "label": "Most-used ingredient level",
        "value": f"{most_used_level.title()} ({counts[most_used_level]} selections)",
    }


def get_discovered_simulator_recipes(state):
    discovered = []

    for run in state.get("simulator_runs", []):
        recipe_id = run.get("recipe_id")
        if recipe_id and recipe_id not in discovered:
            discovered.append(recipe_id)

    return discovered


def get_session_discovered_simulator_recipes():
    discovered = session.get("simulator_discoveries", [])
    if not isinstance(discovered, list):
        discovered = []
    return discovered


def record_session_simulator_discovery(recipe_id):
    if not recipe_id:
        return

    discovered = get_session_discovered_simulator_recipes()
    if recipe_id not in discovered:
        discovered.append(recipe_id)
        session["simulator_discoveries"] = discovered
        session.modified = True


def can_session_continue_to_quiz(simulator_data):
    discovered_recipe_ids = get_session_discovered_simulator_recipes()
    required_recipe_ids = [recipe["id"] for recipe in simulator_data["recipes"]]
    return len(set(discovered_recipe_ids)) >= 2

def get_learning_step(learning_steps, step_number):
    for step in learning_steps:
        if step["step"] == step_number:
            return step
    return None

def get_quiz_question(quiz_questions, step_number):
    for question in quiz_questions:
        if question["id"] == step_number:
            return question
    return None


def build_default_selections(simulator_data):
    selections = {}
    for ingredient in simulator_data["ingredients"]:
        selections[ingredient["key"]] = ingredient.get("default_level", "medium")
    return selections


def normalize_level(level, simulator_data):
    if not isinstance(level, str):
        return "medium"

    cleaned_level = level.strip().lower().replace("_", "-")

    normalization = simulator_data.get("normalization", {})

    normalized = normalization.get(cleaned_level, cleaned_level)

    if normalized not in simulator_data["levels"]:
        return "medium"

    return normalized


def parse_simulator_selections(form_data, simulator_data):
    selections = {}
    invalid_fields = []
    allowed_levels = set(simulator_data["levels"])

    for ingredient in simulator_data["ingredients"]:
        key = ingredient["key"]

        raw_value = form_data.get(key)

        if raw_value is None:
            raw_value = ingredient.get("default_level", "medium")

        normalized_level = normalize_level(raw_value, simulator_data)

        if normalized_level not in allowed_levels:
            normalized_level = "medium"

        selections[key] = normalized_level

    return selections, invalid_fields

def recipe_matches(selections, recipe, simulator_data):
    for ingredient_key, expected_level in recipe["requirements"].items():

        # normalize ONLY selections once (safe)
        actual = normalize_level(selections.get(ingredient_key), simulator_data)

        # normalize expected once
        expected = normalize_level(expected_level, simulator_data)

        if actual != expected:
            return False

    return True


def evaluate_simulator_result(selections, simulator_data):
    for recipe in simulator_data["recipes"]:
        if recipe_matches(selections, recipe, simulator_data):
            return {
                "cookie_type": recipe["cookie_type"],
                "explanation": recipe["explanation"],
                "recipe_id": recipe["id"],
            }

    fallback_result = simulator_data["fallback_result"]
    return {
        "cookie_type": fallback_result["cookie_type"],
        "explanation": fallback_result["explanation"],
        "recipe_id": None,
    }


@app.route("/", methods=["GET", "POST"])
def home():
    content = load_content()

    if request.method == "POST":
        reset_progress()
        return redirect(url_for("learn_step", step=1))

    return render_template("home.html", home=content["home"])


@app.route("/learn/<int:step>")
def learn_step(step):
    content = load_content()
    learning_steps = content["learning_steps"]

    if step >= 3 and step <= 6:
        return redirect(url_for("learn_step", step=2))
    
    step_data = get_learning_step(learning_steps, step)

    if step_data is None:
        abort(404)

    record_learning_step(step)

    step_numbers = [item["step"] for item in learning_steps]
    current_index = step_numbers.index(step)
    previous_step = step_numbers[current_index - 1] if current_index > 0 else None
    next_step = step_numbers[current_index + 1] if current_index < len(step_numbers) - 1 else None
    
    if step == 2:
        next_step = 7

    if step == 7:
        previous_step = 2

    next_url = (
        url_for("learn_step", step=next_step)
        if next_step
        else url_for("simulator")
    )
    next_button_label = (
        step_data.get("next_button_label", "Continue")
        if next_step
        else step_data.get("next_button_label", "Continue to Simulator")
    )
    ingredient_lessons = [item for item in learning_steps if item["step"] >= 3 and item["step"] <= 6]

    return render_template(
        "learning.html",
        step_data=step_data,
        ingredient_lessons=ingredient_lessons,
        total_steps=len(learning_steps),
        previous_step=previous_step,
        next_step=next_step,
        next_button_label=next_button_label,
        next_url=next_url,
    )


@app.route("/simulator", methods=["GET", "POST"])
def simulator():
    simulator_data = load_simulator_content()
    selections = build_default_selections(simulator_data)
    result = None
    error_message = None

    if request.method == "GET":
        if "simulator_discoveries" not in session:
            session["simulator_discoveries"] = []
        record_simulator_entry()
    else:
        action = request.form.get("simulator_action", "bake")
        
        if action == "reset":
            selections = build_default_selections(simulator_data)
            result = None

        else:
            selections, invalid_fields = parse_simulator_selections(request.form, simulator_data)
            if invalid_fields:
                error_message = "Please choose a valid level for: {}.".format(
                    ", ".join(invalid_fields)
                )
            else:
                result = evaluate_simulator_result(selections, simulator_data)
                record_simulator_run(selections, result)
                if result and result.get("recipe_id"):
                    record_session_simulator_discovery(result["recipe_id"])

    return render_template(
        "simulator.html",
        simulator=simulator_data,
        selections=selections,
        result=result,
        error_message=error_message,
    )


@app.route("/quiz/<int:step>", methods=["GET", "POST"])
def quiz_step(step):
    quiz_content = load_quiz_content()
    quiz_questions = quiz_content["quiz_questions"]
    question = get_quiz_question(quiz_questions, step)
    question_ids = [item["id"] for item in quiz_questions]
    simulator_data = load_simulator_content()

    if not can_session_continue_to_quiz(simulator_data):
        return redirect(url_for("simulator"))

    state = load_state()
    progress = get_quiz_progress(quiz_questions, state)
    review_mode = progress["completed"]
    saved_response = get_quiz_response_for_step(state, step)

    if question is None:
        return redirect(url_for("results"))

    if not review_mode and step != progress["next_step"]:
        return redirect(url_for("quiz_step", step=progress["next_step"]))

    if request.method == "GET":
        record_quiz_visit(step)
        current_index = question_ids.index(step)
        previous_review_step = question_ids[current_index - 1] if current_index > 0 else None
        next_review_step = (
            question_ids[current_index + 1] if current_index < len(question_ids) - 1 else None
        )
        return render_template(
            "quiz_test.html",
            question=question,
            review_mode=review_mode,
            saved_response=saved_response["response"] if saved_response else {},
            saved_correct=saved_response["correct"] if saved_response else None,
            review_index=step,
            total_questions=len(quiz_questions),
            previous_review_step=previous_review_step,
            next_review_step=next_review_step,
        )

    if review_mode:
        return redirect(url_for("quiz_step", step=step))

    is_correct, user_response = check_quiz_answer(question, request.form)
    record_quiz_answer(step, question, user_response, is_correct)

    next_step = step + 1
    is_last = step == len(quiz_questions)

    return render_template(
        "feedback_test.html",
        question=question,
        is_correct=is_correct,
        user_response=user_response,
        next_step=next_step,
        is_last=is_last,
    )


@app.route("/quiz/restart", methods=["POST"])
def restart_quiz():
    clear_saved_results()
    reset_quiz_progress()
    return redirect(url_for("quiz_step", step=1))


@app.route("/results/clear", methods=["POST"])
def clear_results():
    clear_saved_results()
    return redirect(url_for("home"))


@app.route("/results")
def results():
    content = load_content()
    quiz_content = load_quiz_content()
    state = load_state()

    total_questions = len(quiz_content["quiz_questions"])
    correct_answers = sum(1 for answer in state["quiz_answers"] if answer["correct"])
    quiz_percent = round((correct_answers / total_questions) * 100) if total_questions else 0
    usage_stat = summarize_level_usage(state)

    return render_template(
        "results.html",
        page=content["results_page"],
        state=state,
        quiz_end_page=quiz_content["quiz_end_page"],
        quiz_score=correct_answers,
        quiz_percent=quiz_percent,
        total_questions=total_questions,
        quiz_questions=quiz_content["quiz_questions"],
        usage_stat=usage_stat,
    )


if __name__ == "__main__":
    app.run(debug=True)
