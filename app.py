from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Хранилище категорий
categories = [
    {"title": "Беседки", "image": "placeholder.png"},
    {"title": "Участки", "image": "placeholder.png"},
    {"title": "Бани", "image": "placeholder.png"},
    {"title": "Дома", "image": "placeholder.png"},
    {"title": "Изделия", "image": "placeholder.png"}
]

@app.route("/")
def index():
    return render_template("index.html", categories=categories)

@app.route("/add_category", methods=["POST"])
def add_category():
    data = request.json
    title = data.get("title")
    image = data.get("image")
    if title and image:
        categories.append({"title": title, "image": image})
        return jsonify({"success": True, "categories": categories})
    return jsonify({"success": False, "message": "Название и изображение обязательны."})

if __name__ == "__main__":
    app.run(debug=True)
