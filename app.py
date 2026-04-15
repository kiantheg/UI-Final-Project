import json
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for


BASE_DIR = Path(__file__).resolve().parent
CONTENT_FILE = BASE_DIR / "data" / "course_content.json"
STATE_FILE = BASE_DIR / "instance" / "user_state.json"

app = Flask(__name__)


def load_content():
    """Load the shared course content so routes stay data-driven."""
    with CONTENT_FILE.open(encoding="utf-8") as content_file:
        return json.load(content_file)


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
        return json.load(state_file)


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


def get_learning_step(learning_steps, step_number):
    for step in learning_steps:
        if step["step"] == step_number:
            return step
    return None


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
    step_data = get_learning_step(learning_steps, step)

    if step_data is None:
        abort(404)

    record_learning_step(step)

    step_numbers = [item["step"] for item in learning_steps]
    current_index = step_numbers.index(step)
    previous_step = step_numbers[current_index - 1] if current_index > 0 else None
    next_step = step_numbers[current_index + 1] if current_index < len(step_numbers) - 1 else None

    return render_template(
        "learning.html",
        step_data=step_data,
        total_steps=len(learning_steps),
        previous_step=previous_step,
        next_step=next_step,
        next_button_label=step_data.get("next_button_label", "Continue"),
    )


@app.route("/quiz/<int:step>")
def quiz_step(step):
    content = load_content()
    record_quiz_visit(step)
    return render_template(
        "placeholder.html",
        page_title=content["quiz_placeholder"]["title"],
        message=content["quiz_placeholder"]["message"],
        back_url=url_for("learn_step", step=len(content["learning_steps"])),
        next_url=url_for("results"),
        next_label="View Results Placeholder",
    )


@app.route("/results")
def results():
    content = load_content()
    state = load_state()
    return render_template(
        "results.html",
        page=content["results_page"],
        state=state,
    )


if __name__ == "__main__":
    app.run(debug=True)
