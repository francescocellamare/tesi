import argparse
from bs4 import BeautifulSoup
import csv

# Function to extract percentage and values from coverage data
def extract_coverage(text):
    # Extract percentage
    percentage = int(text.split("%")[0].strip())

    # Extract numbers inside the parenthesis or legend (e.g., "134/140")
    values_text = text.split()[-1]  # Extract the last part, "134/140"
    covered, total = map(int, values_text.split("/"))  # Split by "/"

    return percentage, covered, total

def main():
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="Extract data from PIT HTML report and save it as a CSV.")
    parser.add_argument("html_file", help="Path to the PIT report HTML file.")
    parser.add_argument("output_csv", help="Path to the output CSV file.")
    args = parser.parse_args()

    # Parse the HTML file
    with open(args.html_file, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    # Extract overall project summary
    project_summary = soup.find("h3", string="Project Summary").find_next("table")
    project_row = project_summary.find("tbody").find("tr").find_all("td")
    number_of_classes = int(project_row[0].text.strip())
    line_coverage = extract_coverage(project_row[1].text)
    mutation_coverage = extract_coverage(project_row[2].text)
    test_strength = extract_coverage(project_row[3].text)

    # Store project summary
    data = [
        {
            "Name": "Project Summary",
            "Number of Classes": number_of_classes,
            "Line Coverage (%)": line_coverage[0],
            "Line Coverage (Covered)": line_coverage[1],
            "Line Coverage (Total)": line_coverage[2],
            "Mutation Coverage (%)": mutation_coverage[0],
            "Mutation Coverage (Covered)": mutation_coverage[1],
            "Mutation Coverage (Total)": mutation_coverage[2],
            "Test Strength (%)": test_strength[0],
            "Test Strength (Covered)": test_strength[1],
            "Test Strength (Total)": test_strength[2],
        }
    ]

    # Extract package-level data
    package_table = soup.find("h3", string="Breakdown by Package").find_next("table")
    package_rows = package_table.find("tbody").find_all("tr")

    for row in package_rows:
        cols = row.find_all("td")
        package_name = cols[0].text.strip()
        package_classes = int(cols[1].text.strip())
        package_line_coverage = extract_coverage(cols[2].text)
        package_mutation_coverage = extract_coverage(cols[3].text)
        package_test_strength = extract_coverage(cols[4].text)
        
        # Append to data
        data.append({
            "Name": package_name,
            "Number of Classes": package_classes,
            "Line Coverage (%)": package_line_coverage[0],
            "Line Coverage (Covered)": package_line_coverage[1],
            "Line Coverage (Total)": package_line_coverage[2],
            "Mutation Coverage (%)": package_mutation_coverage[0],
            "Mutation Coverage (Covered)": package_mutation_coverage[1],
            "Mutation Coverage (Total)": package_mutation_coverage[2],
            "Test Strength (%)": package_test_strength[0],
            "Test Strength (Covered)": package_test_strength[1],
            "Test Strength (Total)": package_test_strength[2],
        })

    # Write data to CSV
    with open(args.output_csv, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "Name",
            "Number of Classes",
            "Line Coverage (%)",
            "Line Coverage (Covered)",
            "Line Coverage (Total)",
            "Mutation Coverage (%)",
            "Mutation Coverage (Covered)",
            "Mutation Coverage (Total)",
            "Test Strength (%)",
            "Test Strength (Covered)",
            "Test Strength (Total)"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"Data successfully extracted and written to {args.output_csv}")

if __name__ == "__main__":
    main()
