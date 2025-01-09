import json
import subprocess
from InquirerPy import prompt

def filter_folders(structure, selection):
    if isinstance(structure, list):
        filtered = []
        for item in structure:
            filtered_item = filter_folders(item, selection)
            if filtered_item:
                filtered.append(filtered_item)
        return filtered
    elif isinstance(structure, dict):
        if structure["type"] == "directory" and structure["name"] in selection:
            return {
                "type": structure["type"],
                "name": structure["name"],
                "contents": filter_folders(structure.get("contents", []), selection)
            }
        elif structure["type"] == "directory":
            # Check children even if current directory is not selected
            contents = filter_folders(structure.get("contents", []), selection)
            if contents:
                return {
                    "type": structure["type"],
                    "name": structure["name"],
                    "contents": contents
                }
    return None

def display_structure(structure, indent=0):
    """Display the folder structure hierarchically."""
    for item in structure:
        print("  " * indent + item["name"])
        if item["type"] == "directory" and "contents" in item:
            display_structure(item["contents"], indent + 1)

def collect_folders(structure, path=""):
    """Flatten folder paths for menu display."""
    choices = []
    for item in structure:
        current_path = f"{path}/{item['name']}".strip("/")
        choices.append({"name": current_path, "value": current_path})
        if item["type"] == "directory" and "contents" in item:
            choices += collect_folders(item["contents"], current_path)
    return choices

# Example JSON structure
project_structure = subprocess.run(["tree", "-d", "-J", "--noreport", "../src/main/java"], capture_output=True).stdout.decode('utf-8')
project_structure = json.loads(project_structure)

# Display the structure
print("Project Structure:")
display_structure(project_structure)

choices = collect_folders(project_structure)

# Use InquirerPy to display a checkbox menu
questions = [
    {
        "type": "checkbox",
        "message": "Select folders:",
        "name": "selected_folders",
        "choices": [{"name": choice["name"], "value": choice["value"]} for choice in choices],
    }
]

answers = prompt(questions)

selected_folders = answers["selected_folders"]
selected_folders = [item[3:] for item in selected_folders]

# Process selected folders
print("\Writing to demo/tested_paths.json:")


fp = open('../tested_paths.json', 'w')
output = {
    "selected": selected_folders
}
fp.write(json.dumps(output))
fp.close()