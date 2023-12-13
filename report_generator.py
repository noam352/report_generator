from pypdf import PdfReader
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Spacer,
    Paragraph,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet
import pandas as pd
import os
import sys

def get_script_dir():
    # Get the directory of the current script
    if getattr(sys, "frozen", False):
        script_directory = os.path.dirname(sys.executable)
    else:
        script_directory = os.path.dirname(os.path.abspath(__file__))
    return script_directory


def get_file_names(script_directory):
    # Define the path to the 'inputs' folder
    inputs_folder = os.path.join(script_directory, "inputs")

    # Check if the 'inputs' folder exists
    if os.path.exists(inputs_folder) and os.path.isdir(inputs_folder):
        # Get the list of filenames in the 'inputs' folder
        filenames = os.listdir(inputs_folder)
        return filenames
    else:
        print("The 'inputs' folder does not exist.")


def split_at_first_non_capitalized_word(input_string):
    words = input_string.split()

    for i, word in enumerate(words):
        if not word.isupper() and len(word) > 1:
            # Split the string at the space before the first non-fully capitalized word
            first_half = " ".join(words[:i]).strip()
            second_half = " ".join(words[i:]).strip()
            return [first_half, second_half]

    # Return the original string if all words are fully capitalized
    return [input_string]


def get_goals(text):
    # Define the regex pattern
    pattern = re.compile(r"GOAL(.*?)MEANS", re.DOTALL)

    # Find all matches in the input string
    matches = pattern.findall(text)

    matches = [match.replace("\t", " ") for match in matches]

    matches = [match.replace("\n", " ") for match in matches]

    matches = [match.strip() for match in matches]

    goal_dict = {}
    for match in matches:
        key, value = split_at_first_non_capitalized_word(match)
        goal_dict[key.title()] = value
    return goal_dict


def get_name(text):
    pattern = re.compile(r"((?:.*\n){3})Date\s+of\s+birth:", re.MULTILINE)
    # Find matches
    matches = re.findall(pattern, text)
    return "".join(matches[0].split("\n")[:-2]).replace("\t", " ")


def generate_date_ranges(start_month, start_year, end_month, end_year):
    start_date = pd.to_datetime(f"{start_month}/01/{start_year}")
    end_date = pd.to_datetime(f"{end_month}/01/{end_year}")

    date_ranges = []

    current_date = start_date
    while current_date < end_date:
        # Find the next Monday
        monday = current_date + pd.DateOffset(days=(0 - current_date.dayofweek))

        # Find the next Friday
        friday = monday + pd.DateOffset(days=4)

        # Add the date range for the week (Monday to Friday)
        date_range = f"{monday.strftime('%A, %b %d')} - {friday.strftime('%A, %b %d')}"
        date_ranges.append(date_range)

        # Move to the next week
        current_date = friday + pd.DateOffset(days=3)

    return date_ranges


def create_pdf_schedule_with_title_and_dates(
    title, name, competency, goal, date_ranges
):
    # Create a Pandas DataFrame
    columns = ["Week of", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    data = []

    for date_range in date_ranges:
        row = [date_range]
        row.extend(["Y | N"] * 5)
        data.append(row)

    df = pd.DataFrame(data, columns=columns)

    # Convert the Pandas DataFrame to a list of lists
    data = [df.columns.tolist()] + df.values.tolist()

    # Create a table with the data
    table = Table(data)

    # Add style to the table
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]
    )

    table.setStyle(style)

    # Build the PDF content
    content = [
        Paragraph(f"<b>{title}</b>", getSampleStyleSheet()["Title"]),
        Spacer(1, 12),  # Add some space
        Paragraph(f"Name: {name}", getSampleStyleSheet()["Normal"]),
        Spacer(1, 12),  # Add some space
        # Competency section
        Paragraph("<b>Competency:</b>", getSampleStyleSheet()["Heading1"]),
        Spacer(1, 6),  # Add space after Competency heading
        Paragraph(competency, getSampleStyleSheet()["Normal"]),
        Spacer(1, 12),  # Add some space before the table
        # Goal section
        Paragraph("Goal:", getSampleStyleSheet()["Heading2"]),
        Spacer(1, 6),  # Add space after Goal heading
        Paragraph(goal, getSampleStyleSheet()["Normal"]),
        Spacer(1, 12),  # Add some space before the table
        table,
        PageBreak(),  # Add a page break after each table
    ]

    return content


def create_combined_pdf(output_filename, title, name, competencies_goals_dict):
    # Create a PDF document
    pdf = SimpleDocTemplate(output_filename, pagesize=letter)

    # Build the combined PDF content
    combined_content = []

    start_month = 2  # February
    start_year = 2024
    end_month = 6  # June
    end_year = 2024

    for competency, goal in competencies_goals_dict.items():
        date_ranges = generate_date_ranges(start_month, start_year, end_month, end_year)
        content = create_pdf_schedule_with_title_and_dates(
            title, name, competency, goal, date_ranges
        )
        combined_content.extend(content)

    pdf.build(combined_content)


def main():
    script_directory = get_script_dir()
    file_names = get_file_names(script_directory)
    title = "IEP Data Collection - Term 2"
    file_names = [f"{script_directory}/inputs/{file_name}" for file_name in file_names]

    for file_name in file_names:
        reader = PdfReader(file_name)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        student_name = get_name(text)
        output_filename = f"{script_directory}/outputs/Report_Term2_{student_name.replace(', ', '_').replace(' ', '_')}.pdf"
        competencies_goals_dict = get_goals(text)
        create_combined_pdf(
            output_filename, title, student_name, competencies_goals_dict
        )


if __name__ == "__main__":
    main()
