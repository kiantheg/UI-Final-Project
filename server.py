# Sophie Cheng
# Part 2: Architecting data for the quiz portion

QUIZ_QUESTIONS = [
    {
        "id": 1,
        "type": "ingredient",
        "goal": "CRISPY & FLAT COOKIE",
        "prompt": "Help me make some cookies.",
        "hint": "Think about butter and flour. Which sugar has lower moisture?",
        "correct_answer": {
            "butter": "high",
            "flour": "low",
            "sugar": "white"
        },
        "feedback_title": "CRISPY FLAT COOKIE",
        "feedback_text": "Correct! Remember: High butter increases spreading. White sugar creates a crisp texture. Low flour keeps the cookie thin and flat."
    },
    {
        "id": 2,
        "type": "ingredient",
        "goal": "CHEWY & THICK COOKIE",
        "prompt": "Help me make some cookies.",
        "hint": "Use ingredients that reduce spreading and add moisture.",
        "correct_answer": {
            "butter": "low",
            "flour": "high",
            "sugar": "brown"
        },
        "feedback_title": "CHEWY & THICK COOKIE",
        "feedback_text": "Correct! Remember: Brown sugar adds moisture and chewiness. More flour gives the cookie structure. Less butter reduces spreading."
    },
    {
        "id": 3,
        "type": "multiple_choice",
        "prompt": "Oh no! My cookies came out too soft :(, but I wanted them crispier. What should I change?",
        "choices": [
            "Use brown sugar",
            "Use white sugar",
            "Increase flour",
            "Reduce butter"
        ],
        "correct_answer": "Use white sugar",
        "feedback_title": "Correct!",
        "feedback_text": "Yay you saved my cookies!"
    },
    {
        "id": 4,
        "type": "multiple_choice",
        "prompt": "Oh no! My cookies spread too much and came out flat. I wanted them thick and chewy. What should I change?",
        "choices": [
            "Add more flour and use brown sugar",
            "Increase butter and use white sugar",
            "Reduce flour and increase butter",
            "Use white sugar and reduce flour"
        ],
        "correct_answer": "Add more flour and use brown sugar",
        "feedback_title": "Correct!",
        "feedback_text": "I am so grateful for you, have a cookie please :)"
    }
]

QUIZ_END_PAGE = {
    "title": "COMPLETE",
    "message": "HAVE A COOKIE & A GOOD DAY!",
    "button_text": "RESTART"
}

def get_quiz_question(question_id):
    for question in QUIZ_QUESTIONS:
        if question["id"] == question_id:
            return question
    return None


from flask import Flask, render_template

app = Flask(__name__)


# -------------------
# HOME ROUTE
# -------------------
@app.route("/")
def home():
    return render_template("home.html")


# -------------------
# LEARNING ROUTE
# -------------------
@app.route("/learn/<int:step>")
def learn_step(step):
    return render_template("learning.html", step=step)


# -------------------
# SIMULATOR ROUTE
# -------------------
@app.route("/simulator")
def simulator():
    return render_template("simulator.html")


# -------------------
# QUIZ ROUTE
# -------------------
@app.route("/quiz/<int:step>")
def quiz_step(step):
    return render_template("placeholder.html", step=step)


# -------------------
# RESULTS ROUTE
# -------------------
@app.route("/results")
def results():
    return render_template("results.html")


# -------------------
# RUN APP
# -------------------
if __name__ == "__main__":
    app.run(debug=True)