from flask import Flask, render_template, request, redirect, send_from_directory
import os
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn3
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    sets = []
    labels = []

    i = 0
    while True:
        file_field = f"file_{i}"
        text_field = f"text_{i}"
        label_field = f"label_{i}"

        if file_field not in request.files and text_field not in request.form:
            break

        file = request.files.get(file_field)
        text = request.form.get(text_field).strip()
        label = request.form.get(label_field).strip() or f"Set {i+1}"

        data = set()

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)
            with open(path, "r") as f:
                data = set(line.strip() for line in f if line.strip())
        elif text:
            data = set(line.strip() for line in text.splitlines() if line.strip())
        else:
            i += 1
            continue  # skip empty entry

        if data:
            sets.append(data)
            labels.append(label)

        i += 1

    if len(sets) < 2:
        return render_template("index.html", message="Please provide at least 2 valid data entries.")

    # Excel Report - Universal
    all_values = sorted(set.union(*sets))
    value_to_labels = []

    for val in all_values:
        present_labels = [label for label, s in zip(labels, sets) if val in s]
        value_to_labels.append((val, ", ".join(present_labels)))

    df = pd.DataFrame(value_to_labels, columns=["Values", "Labels"])
    table_path = os.path.join(RESULT_FOLDER, "unique_and_common_values_analysis_report.xlsx")
    df.to_excel(table_path, index=False)

    venn_path = None
    if len(sets) <= 3:
        # Generate Venn Diagram
        plt.figure(figsize=(6,6))
        if len(sets) == 2:
            venn2(subsets=sets, set_labels=labels)
        elif len(sets) == 3:
            venn3(subsets=sets, set_labels=labels)

        venn_path = os.path.join(RESULT_FOLDER, "venn_diagram.png")
        plt.savefig(venn_path)
        plt.close()

    elif len(sets) > 3:
        venn_path = None  # skip Venn if more than 3 levels

    return render_template(
        "index.html",
        venn_path="/download/venn_diagram.png" if venn_path else None,
        download=True,
        message="Venn diagram not generated for more than 3 datasets." if len(sets) > 3 else ""
    )

@app.route("/download/<path:filename>")
def download(filename):
    return send_from_directory(RESULT_FOLDER, filename, as_attachment=False)

if __name__ == "__main__":
    app.run(debug=True)
