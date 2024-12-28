import streamlit as st
import google.generativeai as genai
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from io import BytesIO
import os
import logging
import pandas as pd
import datetime


logging.basicConfig(level=logging.INFO)


os.environ['GOOGLE_API_KEY'] = 'AIzaSyDRsftfex1wmCRXE6_X-CWe7dz0cI3qYb8'  # using Gemini API
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])


if "data" not in st.session_state:
    st.session_state["data"] = {
        "Date": [],
        "Steps": [],
        "Sleep (hours)": [],
        "Calories Burned": []
    }

def query_health_coach(goal, metrics):
    prompt = f"""Based on the goal: {goal} and the following fitness metrics: {metrics}, generate:
    1. A customized workout plan.
    2. A personalized dietary plan.
    3. Additional fitness tips or motivational messages.

    Format:
    - Day 1: ...
    Workout Plan:
    - Day 2: ...
    ...

    Dietary Plan:
    - Breakfast: ...
    - Lunch: ...
    - Dinner: ...
    ...

    Tips:
    1. Tip 1
    2. Tip 2
    ...
    """

    model = genai.GenerativeModel('gemini-pro')
    try:
        response = model.generate_content(prompt)
        if response and response.parts:
            return response.text
        else:
            logging.error("No response parts found.")
            return "Sorry, there was an error generating the response."
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return "Sorry, there was an error generating the response."

def create_pdf(report):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 50

    c.setFont("Helvetica-Bold", 20)
    c.setFillColorRGB(0.2, 0.4, 0.6)
    c.drawString(margin, height - margin, "Health & Fitness Report")

    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0, 0, 0)
    y = height - margin - 30
    max_width = width - 2 * margin

    def draw_wrapped_text(c, text, x, y, max_width, font_name="Helvetica", font_size=12):
        lines = simpleSplit(text, font_name, font_size, max_width)
        for line in lines:
            if y < margin:
                c.showPage()
                c.setFont(font_name, font_size)
                y = height - margin
            c.drawString(x, y, line)
            y -= font_size + 2
        return y

    for line in report.split('\n'):
        if line.strip():
            if line.startswith('Workout Plan:') or line.startswith('Dietary Plan:') or line.startswith('Tips:'):
                c.setFont("Helvetica-Bold", 16)
                c.setFillColorRGB(0.4, 0.6, 0.8)
                y = draw_wrapped_text(c, line, margin, y, max_width, "Helvetica-Bold", 16)
                c.setFont("Helvetica", 12)
                c.setFillColorRGB(0, 0, 0)
            else:
                y = draw_wrapped_text(c, line, margin + 20, y, max_width - 20)

    c.save()
    buffer.seek(0)
    return buffer

st.set_page_config(page_title="Health & Fitness Bot", layout="wide")
st.title("Health & Fitness Personal Coach")

st.sidebar.header("Dashboard")
dashboard_tab, planning_tab = st.tabs(["User Performance Dashboard", "Generate Plans"])

with dashboard_tab:
    st.subheader("Performance Metrics")

    with st.form("add_data_form"):
        date = st.date_input("Select Date", value=datetime.date.today())
        steps = st.number_input("Steps Count", min_value=0, step=1)
        sleep = st.number_input("Sleep Hours", min_value=0.0, step=0.1)
        calories = st.number_input("Calories Burned", min_value=0, step=1)
        submitted = st.form_submit_button("Add or Update Data")

        if submitted:
            if date in st.session_state["data"]["Date"]:
               
                index = st.session_state["data"]["Date"].index(date)
                st.session_state["data"]["Steps"][index] = steps
                st.session_state["data"]["Sleep (hours)"][index] = sleep
                st.session_state["data"]["Calories Burned"][index] = calories
                st.success(f"Data for {date} updated successfully!")
            else:
               
                st.session_state["data"]["Date"].append(date)
                st.session_state["data"]["Steps"].append(steps)
                st.session_state["data"]["Sleep (hours)"].append(sleep)
                st.session_state["data"]["Calories Burned"].append(calories)
                st.success(f"Data for {date} added successfully!")

 
    if st.session_state["data"]["Date"]:
        df = pd.DataFrame(st.session_state["data"])

        
        st.subheader("Step Count Over Time")
        st.line_chart(df.set_index("Date")["Steps"], use_container_width=True)

        st.subheader("Sleep Pattern Over Time")
        st.line_chart(df.set_index("Date")["Sleep (hours)"], use_container_width=True)

        st.subheader("Calories Burned Over Time")
        st.bar_chart(df.set_index("Date")["Calories Burned"], use_container_width=True)

        st.write("Detailed Performance Table:")
        st.dataframe(df)
    else:
        st.write("No data available. Please add your performance metrics.")


with planning_tab:
    st.subheader("Generate Your Plan")

   
    goal = st.text_area("Enter your health and fitness goal:", "")
    metrics = st.text_area("Provide your current fitness metrics (e.g., steps, calories, sleep hours):", "")

    if st.button("Generate Plan and Recommendations"):
        if goal and metrics:
            with st.spinner("Generating your personalized plan..."):
                
                report = query_health_coach(goal, metrics)

           
                st.subheader("Your Personalized Plan")
                st.write(report)

              
                pdf = create_pdf(report)
                st.download_button(
                    label="Download Report as PDF",
                    data=pdf,
                    file_name="health_fitness_report.pdf",
                    mime="application/pdf"
                )
        else:
            st.warning("Please enter both your goal and fitness metrics.")

st.sidebar.markdown("""
## How to use:
1. Add or update your daily performance metrics using the form in the dashboard.
2. Visualize your progress with graphs.
3. Generate personalized health and fitness plans using the **Generate Plans** tab.
""")

st.markdown("---")
st.write("we uses Gemini AI to provide personalized health and fitness plans and recommendations. Stay healthy and motivated!")
