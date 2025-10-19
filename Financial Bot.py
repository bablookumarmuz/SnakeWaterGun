from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory storage for expenses and budget
expenses = []
budget = 0.0

# Route to set a budget
@app.route('/set_budget', methods=['POST'])
def set_budget():
    global budget
    data = request.json
    budget = data.get('budget', 0.0)
    return jsonify({"message": "Budget set successfully!", "budget": budget})

# Route to add an expense
@app.route('/add_expense', methods=['POST'])
def add_expense():
    data = request.json
    expenses.append(data)
    return jsonify({"message": "Expense added!", "data": data})

# Route to view all expenses
@app.route('/view_expenses', methods=['GET'])
def view_expenses():
    return jsonify({"expenses": expenses})

# Route to check budget status
@app.route('/check_budget', methods=['GET'])
def check_budget():
    total_spent = sum(item['amount'] for item in expenses)
    if total_spent > budget:
        return jsonify({"status": "over", "message": f"You've exceeded your budget by {total_spent - budget:.2f}."})
    else:
        return jsonify({"status": "under", "message": f"You're within budget. You have {budget - total_spent:.2f} left."})

# Route to get financial tips
@app.route('/financial_tips', methods=['GET'])
def financial_tips():
    tips = [
        "Automate your savings to ensure consistent contributions.",
        "Cut back on non-essential subscriptions.",
        "Build an emergency fund covering 6 months' expenses.",
        "Invest in low-cost index funds for steady growth.",
        "Pay off high-interest debt as a priority.",
    ]
    return jsonify({"tips": tips})

# Route to suggest investments
@app.route('/suggest_investments', methods=['POST'])
def suggest_investments():
    data = request.json
    risk_level = data.get('risk_level', 'medium').lower()

    if risk_level == "low":
        investments = ["Government Bonds", "Fixed Deposits"]
    elif risk_level == "medium":
        investments = ["Index Funds", "Balanced Mutual Funds"]
    elif risk_level == "high":
        investments = ["Stocks", "Cryptocurrency"]
    else:
        investments = ["Please specify a valid risk tolerance: low, medium, or high."]

    return jsonify({"risk_level": risk_level, "investments": investments})

if __name__ == '__main__':
    app.run(debug=True)
