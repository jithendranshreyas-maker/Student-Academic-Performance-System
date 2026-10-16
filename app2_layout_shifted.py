import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import joblib
import numpy as np

subject_data_query = """
SELECT
    a.quiz1,
    a.quiz2,
    a.midsem,
    a.assignment,
    a.attendance_percentage,
    sr.sga AS prev_sga,
    sr.semester_percentage AS prev_sem_percentage,
    sr.total_backlogs AS prev_total_backlogs
FROM academic_records a
LEFT JOIN semester_results sr
    ON sr.student_id = a.student_id
    AND (
        sr.academic_year < a.academic_year
        OR (
            sr.academic_year = a.academic_year
            AND sr.semester < a.semester
        )
    )
WHERE a.student_id = %s
AND a.subject_code = %s
AND a.academic_year = %s
AND a.semester = %s
ORDER BY sr.academic_year DESC, sr.semester DESC
LIMIT 1
"""

def predict_subject(
    subject_code,
    quiz1,
    quiz2,
    midsem,
    assignment,
    attendance_percentage,
    prev_sga,
    prev_sem_percentage,
    prev_total_backlogs
):
    prediction_input = pd.DataFrame([{
        "subject_code": subject_code,
        "quiz1": quiz1,
        "quiz2": quiz2,
        "midsem": midsem,
        "assignment": assignment,
        "attendance_percentage": attendance_percentage,
        "prev_sga": prev_sga,
        "prev_sem_percentage": prev_sem_percentage,
        "prev_total_backlogs": prev_total_backlogs,
        "branch": student_branch,
        "semester": student_semester
    }])

    predicted_marks = model.predict(prediction_input)[0]
    predicted_marks = max(0, min(100, predicted_marks))

    print("Model features:")
    print(getattr(model, "n_features_in_", "Not available"))

    print("\nPreprocessor input features:")
    print(getattr(preprocessor, "feature_names_in_", "Not available"))

    return predicted_marks


st.set_page_config(
    page_title="Student Academic Performance System",
    page_icon="🎓",
    layout="wide"
)

st.write("Welcome to the Student Academic Performance System.")

model = joblib.load("linear_regression_pipeline.pkl")
preprocessor = joblib.load("preprocessor_linear.pkl")
residual_std=joblib.load("residual_std.pkl")
model_metrics = joblib.load("model_metrics.pkl")
prediction_error=joblib.load("prediction_error.pkl")
error_by_range = pd.read_csv("error_by_mark_range.csv",index_col=0)

st.markdown(
    """
    <style>

    header[data-testid="stHeader"] {
    display:none;
    }

    .top-nav {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 65px;
        background-color: #0e1117;
        z-index: 9999;
        display: flex;
        align-items: center;
        padding-left: 290px; /* Keep the title clear of the fixed left sidebar */
    }

    .top-nav-title {
        font-size: 22px;
        font-weight: bold;
        margin-right: 40px;
    }

    .main .block-container {
        padding-top: 90px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="top-nav">
        <div class="top-nav-title">
            🎓 Student Academic Performance & Risk Analytics
        </div>
    </div>
    """,
    unsafe_allow_html=True
)



if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

pages = [
    "Dashboard",
    "Student Performance",
    "Overall Academic Prediction",
    "Individual Subject Prediction",
    "Historical Comparison",
    "Student Risk Analysis",
    "Backlog Tracker",
    "Prediction Validation"
]

st.markdown("""
<style>
section[data-testid="stSidebar"] {
    display: block !important;
    min-width: 260px !important;
    width: 260px !important;
    transform: none !important;
}

button[data-testid="stSidebarCollapseButton"],
button[data-testid="stSidebarExpandButton"] {
    display: none !important;
}

div[data-testid="stHorizontalBlock"] {
    gap: 0.75rem;
}

.top-navigation {
    position: sticky;
    top: 0;
    z-index: 999;
    background: var(--background-color);
    padding: 0.5rem 0;
}

.fixed-left-panel {
    position: fixed;
    top: 150px;
    left: 2rem;
    bottom: 1rem;
    width: 240px;
    overflow-y: auto;
    padding: 0.75rem;
    background: var(--background-color);
    z-index: 100;
}

/* Keep the top navigation visible while scrolling */
div[data-testid="stVerticalBlock"]:has(> div.top-navigation) {
    position: sticky;
    top: 0;
    z-index: 999;
    background: var(--background-color);
}

/* Prevent the page content from becoming too narrow */
div[data-testid="stMainBlockContainer"] {
    max-width: 100%;
}

/* Keep the left panel's contents available while scrolling */
div[data-testid="stHorizontalBlock"]:has(
    div[data-testid="stColumn"]:first-child
) {
    align-items: flex-start;
}


.main-content-panel {
    margin-left: 270px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="top-navigation">', unsafe_allow_html=True)



nav_columns = st.columns(4)

for index, name in enumerate(pages):
    with nav_columns[index % 4]:
        if st.button(
            name,
            key=f"nav_{name}",
            use_container_width=True,
            type=(
                "primary"
                if st.session_state.page == name
                else "secondary"
            )
        ):
            st.session_state.page = name
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

page = st.session_state.page




with st.sidebar:

    if page == "Dashboard":
        st.markdown("#### Dashboard Sections")

        show_overview = st.checkbox("Overview", value=True)
        show_student_info = st.checkbox("Student Information", value=False)
        show_academic = st.checkbox("Academic Performance", value=True)
        show_semester = st.checkbox("Semester Performance", value=False)
        show_sga = st.checkbox("SGA Trend", value=True)
        show_attendance = st.checkbox("Attendance", value=False)

    elif page == "Student Performance":
        st.markdown("#### Performance Options")
        performance_view = st.radio(
            "View",
            ["Subject Marks", "Grade Points", "Attendance"]
        )

    elif page == "Overall Academic Prediction":
        st.markdown("#### Prediction Options")
        st.caption("Use the existing prediction inputs in the main area.")

    elif page == "Individual Subject Prediction":
        st.markdown("#### Subject Options")
        st.caption("Use the existing subject-selection controls.")

    elif page == "Historical Comparison":
        st.markdown("#### Comparison Options")
        st.caption("Choose the comparison options in the main area.")

    elif page == "Student Risk Analysis":
        st.markdown("#### Risk Options")
        st.caption("Use the existing risk-analysis filters.")

    elif page == "Backlog Tracker":
        st.markdown("#### Backlog Options")
        st.caption("Use the existing backlog filters.")

    elif page == "Prediction Validation":
        st.markdown("#### Validation Options")
        st.caption("Use the existing validation controls.")


con=mysql.connector.connect(host="127.0.0.1",port=3306,user="root",password="password",database="Project_2")
cursor=con.cursor()


query = """
SELECT
    student_id,
    name,
    branch,
    current_year,
    current_semester
FROM students
"""

students_df = pd.read_sql(query, con)



if page == "Dashboard":
    st.subheader("Student Dashboard")

    student_ids = students_df["student_id"].tolist()
    selected_student = st.selectbox("Select Student", student_ids)

    student_info = students_df[
        students_df["student_id"] == selected_student
    ]

    if show_overview:
        st.subheader("Overview")

        query = """
        SELECT
            a.subject_code,
            c.subject_name,
            a.marks_obtained,
            a.grade,
            a.grade_point,
            a.attendance_percentage,
            a.backlog
        FROM academic_records a
        JOIN curriculum c ON a.subject_id = c.subject_id
        WHERE a.student_id = %s
        """

        academic_df = pd.read_sql(
            query, con, params=(selected_student,)
        )

        avg_marks = academic_df["marks_obtained"].mean()
        avg_gp = academic_df["grade_point"].mean()
        total_subjects = len(academic_df)
        total_backlogs = academic_df["backlog"].sum()
        avg_attendance = academic_df["attendance_percentage"].mean()

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Average Marks", f"{avg_marks:.2f}")
        col2.metric("Average Grade Point", f"{avg_gp:.2f}")
        col3.metric("Subjects", total_subjects)
        col4.metric("Backlogs", total_backlogs)
        col5.metric("Average Attendance", f"{avg_attendance:.2f}%")

    else:
        query = """
        SELECT
            a.subject_code,
            c.subject_name,
            a.marks_obtained,
            a.grade,
            a.grade_point,
            a.attendance_percentage,
            a.backlog
        FROM academic_records a
        JOIN curriculum c ON a.subject_id = c.subject_id
        WHERE a.student_id = %s
        """

        academic_df = pd.read_sql(
            query, con, params=(selected_student,)
        )

    if show_student_info:
        st.subheader("Student Information")
        st.dataframe(student_info, width="stretch")

    if show_academic:
        st.subheader("Academic Performance")
        st.dataframe(academic_df, width="stretch")

    query = """
    SELECT
        academic_year,
        semester,
        sga,
        semester_percentage,
        total_backlogs,
        semester_status
    FROM semester_results
    WHERE student_id = %s
    ORDER BY academic_year, semester
    """

    semester_df = pd.read_sql(
        query, con, params=(selected_student,)
    )

    if show_semester:
        st.subheader("Semester Performance")
        st.dataframe(semester_df, width="stretch")

    if show_sga:
        st.subheader("SGA Trend")

        if not semester_df.empty:
            chart_df = semester_df.copy()
            chart_df["Semester_Label"] = (
                chart_df["academic_year"].astype(str)
                + " - Sem "
                + chart_df["semester"].astype(str)
            )

            fig = px.line(
                chart_df,
                x="Semester_Label",
                y="sga",
                markers=True,
                labels={
                    "Semester_Label": "Semester",
                    "sga": "SGA"
                }
            )

            fig.update_yaxes(range=[0, 10], dtick=1)
            st.plotly_chart(fig, width="stretch")

            latest_semester = semester_df.iloc[-1]
            latest_sga = latest_semester["sga"]

            previous_sga = (
                semester_df.iloc[-2]["sga"]
                if len(semester_df) > 1 else None
            )

            sga_change = (
                latest_sga - previous_sga
                if previous_sga is not None else None
            )

            col1, col2 = st.columns(2)
            col1.metric(
                "Latest SGA",
                f"{latest_sga:.2f}",
                f"{sga_change:+.2f}" if sga_change is not None else None
            )
            col2.metric(
                "Latest Semester",
                f"Semester {int(latest_semester['semester'])}"
            )
        else:
            st.info("No semester results are available for this student.")

    if show_attendance:
        st.subheader("Attendance")

        if not academic_df.empty:
            attendance = academic_df["attendance_percentage"].mean()
            attendance_status = (
                "Eligible" if attendance >= 75
                else "Attendance Shortage"
            )

            col1, col2 = st.columns(2)
            col1.metric("Average Attendance", f"{attendance:.2f}%")
            col2.metric("Status", attendance_status)
        else:
            st.info("No attendance records are available.")

    st.divider()
    st.subheader("Download Evaluation Report")

    report_csv = error_by_range.to_csv().encode("utf-8")

    st.download_button(
        label="Download Mark-Range Evaluation (CSV)",
        data=report_csv,
        file_name="error_by_mark_range.csv",
        mime="text/csv"
    )

    st.subheader("Prediction Error Across Mark Ranges")
    st.bar_chart(error_by_range["MAE"])

    st.caption(
        "Mean absolute prediction error by predicted-mark range. "
        "Lower values indicate smaller errors on average."
    )

    st.subheader("Model Evaluation Summary")

    col1, col2, col3 = st.columns(3)
    col1.metric("Mean Absolute Error", f"{model_metrics['mae']:.2f} marks")
    col2.metric("Root Mean Squared Error", f"{model_metrics['rmse']:.2f} marks")
    col3.metric("R² Score", f"{model_metrics['r2_score']:.4f}")

    st.caption(
        "Evaluation results are based on the generated synthetic dataset "
        "and may not represent performance on real student records."
    )



if page == "Student Performance":
    st.subheader("Student Performance")

    student_ids = students_df["student_id"].tolist()

    selected_student = st.selectbox(
        "Select Student",
        student_ids
    )

    query = """
    SELECT
        a.subject_code,
        c.subject_name,
        a.marks_obtained,
        a.grade,
        a.grade_point,
        a.attendance_percentage,
        a.backlog
    FROM academic_records a
    JOIN curriculum c
        ON a.subject_id = c.subject_id
    WHERE a.student_id = %s
    ORDER BY a.subject_code
    """

    performance_df = pd.read_sql(
        query,
        con,
        params=(selected_student,)
    )

    performance_df["attendance_status"] = performance_df[
        "attendance_percentage"
    ].apply(
        lambda x: "Safe" if x >= 75 else "Shortage"
    )


    performance_df["performance_category"] = performance_df[
        "marks_obtained"
    ].apply(
        lambda x:
            "Amazing" if x >= 85
            else "Decent" if x >= 70
            else "Average" if x >= 55
            else "Below Par" if x >= 40
            else "Very Bad"
    )

    styled_df = performance_df.style.map(
        lambda x:
            "background-color: #00b050; color: black; font-weight: bold;"
            if x == "Amazing"
            else "background-color: #70ad47; color: black; font-weight: bold;"
            if x == "Decent"
            else "background-color: #a9d18e; color: black; font-weight: bold;"
            if x == "Average"
            else "background-color: #ff9999; color: black; font-weight: bold;"
            if x == "Below Par"
            else "background-color: #ff0000; color: black; font-weight: bold;"
            if x == "Very Bad"
            else "",
        subset=["performance_category"]
    )

    styled_df = styled_df.map(
        lambda x:
            "background-color: #ff0000; color: black; font-weight: bold;"
            if isinstance(x, (int, float)) and x < 75
            else "",
        subset=["attendance_percentage"]
    )

    styled_df = styled_df.map(
        lambda x:
            "background-color: #ff0000; color: black; font-weight: bold;"
            if x == "Shortage"
            else "",
        subset=["attendance_status"]
    )
    

    st.dataframe(
        styled_df,
        width="stretch"
    )

    

    if not performance_df.empty:
        performance_df["display_grade_point"] = performance_df.apply(
            lambda row: 10
            if str(row["grade"]).strip().upper() in ["FF", "FA"]
            else row["grade_point"],
            axis=1
        )

        bar_colors = [
            "red"
            if str(grade).strip().upper() in ["FF", "FA"]
            else "#636EFA"
            for grade in performance_df["grade"]
        ]
        bar_colors = [
            "#FA6363" if str(grade).strip().upper() in ["FF", "FA"] else "#636EFA"
            for grade in performance_df["grade"]
        ]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=performance_df["subject_code"],
                y=performance_df["display_grade_point"],
                marker_color=bar_colors,
                customdata=performance_df[
                    ["subject_name", "grade", "grade_point"]
                ],
                hovertemplate=
                    "<b>%{x}</b><br>"
                    "Subject: %{customdata[0]}<br>"
                    "Grade: %{customdata[1]}<br>"
                    "Grade Point: %{customdata[2]}<extra></extra>"
            )
        )

        fig.update_yaxes(
            range=[0, 10],
            dtick=1,
            title="Grade Point"
        )

        fig.update_xaxes(
            title="Subject"
        )

        fig.update_layout(
            showlegend=False
        )

        st.subheader("Subject-wise Grade Point")
        st.plotly_chart(
            fig,
            width="stretch"
        )


        
        fig = px.bar(
            performance_df,
            x="subject_code",
            y="marks_obtained",
            hover_data=["subject_name", "grade", "grade_point"],
            labels={
                "subject_code": "Subject",
                "marks_obtained": "Marks"
            }
        )

        fig.update_yaxes(
            range=[0, 100],
            dtick=10
        )

        

        st.subheader("Subject-wise Marks")
        st.plotly_chart(
            fig,
            width="stretch"
        )

        if not performance_df.empty:
            grade_counts = (
                performance_df["grade"]
                .value_counts()
                .reset_index()
            )

            grade_counts.columns = ["grade", "count"]

            fig = px.pie(
                grade_counts,
                names="grade",
                values="count",
                title="Grade Distribution"
            )

            st.plotly_chart(
                fig,
                width="stretch"
            )
        backlog_count = performance_df["backlog"].sum()

        if backlog_count > 0:
            st.warning(
                f"This student currently had {int(backlog_count)} backlog(s)."
            )
        else:
            st.success("No backlogs recorded.")


        st.subheader("Semester Performance")

        query = """
        SELECT
            academic_year,
            semester,
            sga,
            semester_percentage,
            total_backlogs,
            semester_status
        FROM semester_results
        WHERE student_id = %s
        ORDER BY academic_year, semester
        """

        semester_performance_df = pd.read_sql(
            query,
            con,
            params=(selected_student,)
        )

        st.dataframe(
            semester_performance_df,
            width="stretch"
        )


if page == "Overall Academic Prediction":

    grade_points = {
        "AA": 10,
        "AB": 9,
        "BB": 8,
        "BC": 7,
        "CC": 6,
        "CD": 5,
        "DD": 4,
        "FF": 0,
        "FA": 0
    }

    st.subheader("Subject Marks Prediction")

    student_ids = students_df["student_id"].tolist()

    selected_student = st.selectbox(
        "Select Student",
        student_ids
    )
    
    student_info = students_df[
    students_df["student_id"] == selected_student
    ].iloc[0]

    student_branch = student_info["branch"]
    current_semester_query = """
    SELECT academic_year, semester
    FROM academic_records
    WHERE student_id = %s
    ORDER BY academic_year DESC, semester DESC
    LIMIT 1
    """

    current_semester_df = pd.read_sql(
        current_semester_query,
        con,
        params=(selected_student,)
    )

    student_semester = int(current_semester_df.iloc[0]["semester"])
    student_year = int(current_semester_df.iloc[0]["academic_year"])

    st.write(
    f"Branch: {student_branch} | "
    f"Year: {student_year} | "
    f"Semester: {student_semester}"
    )


    subjects_query = """
    SELECT
        subject_code,
        subject_name,
        credits
    FROM curriculum
    WHERE branch = %s
    AND academic_year = %s
    AND semester = %s
    ORDER BY subject_code
    """

    subjects_df = pd.read_sql(
        subjects_query,
        con,
        params=(
            student_branch,
            student_year,
            student_semester
        )
    )

    all_subjects_query = """
    SELECT
        a.subject_code,
        a.quiz1,
        a.quiz2,
        a.midsem,
        a.assignment,
        a.classes_attended,
        a.classes_held,
        a.attendance_percentage,
        sr.sga AS prev_sga,
        sr.semester_percentage AS prev_sem_percentage,
        sr.total_backlogs AS prev_total_backlogs
    FROM academic_records a
    LEFT JOIN semester_results sr
        ON sr.student_id = a.student_id
        AND (
            sr.academic_year < a.academic_year
            OR (
                sr.academic_year = a.academic_year
                AND sr.semester < a.semester
            )
        )
    WHERE a.student_id = %s
    AND a.academic_year = %s
    AND a.semester = %s
    AND NOT EXISTS (
        SELECT 1
        FROM semester_results sr2
        WHERE sr2.student_id = sr.student_id
        AND (
            sr2.academic_year > sr.academic_year
            OR (
                sr2.academic_year = sr.academic_year
                AND sr2.semester > sr.semester
            )
        )
        AND (
            sr2.academic_year < %s
            OR (
                sr2.academic_year = %s
                AND sr2.semester < %s
            )
        )
    )
    ORDER BY a.subject_code
    """

    all_subjects_data = pd.read_sql(
        all_subjects_query,
        con,
        params=(
            selected_student,
            student_year,
            student_semester,
            student_year,
            student_year,
            student_semester
        )
    )

    predicted_subjects = subjects_df.copy()

    predicted_subjects["predicted_marks"] = None
    predicted_subjects["quiz1"] = None
    predicted_subjects["quiz2"] = None
    predicted_subjects["midsem"] = None
    predicted_subjects["assignment"] = None
    predicted_subjects["classes_attended"] = None
    predicted_subjects["classes_held"] = None
    predicted_subjects["attendance_percentage"] = None
    predicted_subjects["estimated_grade"] = None
    
    
    for i, row in all_subjects_data.iterrows():

        subject_code = row["subject_code"]

        predicted_marks = predict_subject(
            row["subject_code"],
            row["quiz1"],
            row["quiz2"],
            row["midsem"],
            row["assignment"],
            row["attendance_percentage"],
            row["prev_sga"],
            row["prev_sem_percentage"],
            row["prev_total_backlogs"]
        )

        predicted_subjects.loc[
            predicted_subjects["subject_code"] == subject_code,
            "predicted_marks"
        ] = predicted_marks

        predicted_subjects.loc[
            predicted_subjects["subject_code"] == subject_code,
            "quiz1"
        ] = row["quiz1"]

        predicted_subjects.loc[
            predicted_subjects["subject_code"] == subject_code,
            "quiz2"
        ] = row["quiz2"]

        predicted_subjects.loc[
            predicted_subjects["subject_code"] == subject_code,
            "midsem"
        ] = row["midsem"]

        predicted_subjects.loc[
            predicted_subjects["subject_code"] == subject_code,
            "assignment"
        ] = row["assignment"]

        predicted_subjects.loc[
            predicted_subjects["subject_code"] == subject_code,
            "classes_attended"
        ] = row["classes_attended"]

        predicted_subjects.loc[
            predicted_subjects["subject_code"] == subject_code,
            "classes_held"
        ] = row["classes_held"]

        predicted_subjects.loc[
            predicted_subjects["subject_code"] == subject_code,
            "attendance_percentage"
        ] = row["attendance_percentage"]

        if (
            pd.notna(row["attendance_percentage"])
            and row["attendance_percentage"] < 75
        ):
            predicted_subjects.loc[
                predicted_subjects["subject_code"] == subject_code,
                "estimated_grade"
            ] = "FA"
            continue

        predicted_marks = float(predicted_marks)

        grade_history_query = """
        SELECT
            a.grade,
            MIN(a.marks_obtained) AS min_marks,
            MAX(a.marks_obtained) AS max_marks,
            AVG(a.marks_obtained) AS avg_marks
        FROM academic_records a
        JOIN curriculum c
            ON a.subject_id = c.subject_id
        WHERE a.subject_code = %s
        AND c.branch = %s
        AND c.semester = %s
        AND a.grade NOT IN ('FF', 'FA')
        GROUP BY a.grade
        ORDER BY avg_marks
        """

        grade_history = pd.read_sql(
            grade_history_query,
            con,
            params=(
                subject_code,
                student_branch,
                student_semester
            )
        )

        if grade_history.empty:

            estimated_grade = "N/A"


        else:

            matching_grade = grade_history[
                (grade_history["min_marks"] <= predicted_marks)
                & (grade_history["max_marks"] >= predicted_marks)
            ]

            if not matching_grade.empty:

                estimated_grade = matching_grade.iloc[0]["grade"]

            else:

                grade_history["distance"] = (
                    grade_history["avg_marks"] - predicted_marks
                ).abs()

                estimated_grade = grade_history.loc[
                    grade_history["distance"].idxmin(),
                    "grade"
                ]
        possible_grades = []

        predicted_subjects.loc[
            predicted_subjects["subject_code"] == subject_code,
            "estimated_grade"
        ] = estimated_grade

    historical_average_query = """
    SELECT
        a.subject_code,
        AVG(a.marks_obtained) AS historical_average
    FROM academic_records a
    JOIN curriculum c
        ON a.subject_id = c.subject_id
    WHERE c.branch = %s
    AND c.semester = %s
    AND a.grade NOT IN ('FF', 'FA')
    GROUP BY a.subject_code
    """

    historical_average_df = pd.read_sql(
        historical_average_query,
        con,
        params=(
            student_branch,
            student_semester
        )
    )

    predicted_subjects = predicted_subjects.merge(
        historical_average_df,
        on="subject_code",
        how="left"
    )

    predicted_subjects["performance_vs_history"] = (
        predicted_subjects["predicted_marks"]
        - predicted_subjects["historical_average"]
    )

    predicted_subjects["historical_comparison"] = (
        predicted_subjects["performance_vs_history"].apply(
            lambda x:
                "Above Historical Average"
                if x > 0
                else "Below Historical Average"
                if x < 0
                else "Same as Historical Average"
        )
    )

    predicted_subjects["historical_performance_gap"] = (
        predicted_subjects["performance_vs_history"].apply(
            lambda x:
                "Significantly Above"
                if x >= 10
                else "Above"
                if x >= 3
                else "Near Historical Average"
                if x > -3
                else "Below"
                if x > -10
                else "Significantly Below"
        )
    )

    def generate_subject_feedback(row):

        feedback = []

        predicted_marks = row["predicted_marks"]

        if pd.isna(predicted_marks):
            return "Prediction unavailable for this subject."

        if predicted_marks >= 85:
            feedback.append(
                "Strong predicted performance in this subject."
            )

        elif predicted_marks >= 70:
            feedback.append(
                "Decent predicted performance, with room for improvement."
            )

        elif predicted_marks >= 55:
            feedback.append(
                "Average predicted performance. Improvement is recommended."
            )

        else:
            feedback.append(
                "Low predicted performance. This subject needs attention."
            )

        if (
            pd.notna(row["attendance_percentage"])
            and row["attendance_percentage"] < 75
        ):
            feedback.append(
                "Attendance is below the required 75%."
            )

        if pd.notna(row["quiz1"]) and row["quiz1"] < 10:
            feedback.append(
                "Quiz 1 performance could be improved."
            )

        if pd.notna(row["quiz2"]) and row["quiz2"] < 10:
            feedback.append(
                "Quiz 2 performance could be improved."
            )

        if pd.notna(row["midsem"]) and row["midsem"] < 20:
            feedback.append(
                "Mid-semester performance could be improved."
            )

        if pd.notna(row["assignment"]) and row["assignment"] < 5:
            feedback.append(
                "Assignment performance could be improved."
            )

        return " ".join(feedback)


    predicted_subjects["feedback"] = predicted_subjects.apply(
        generate_subject_feedback,
        axis=1
    )


    predicted_subjects["predicted_grade_point"] = (
        predicted_subjects["estimated_grade"].map(grade_points)
    )

    predicted_subjects["weighted_grade_point"] = (
        predicted_subjects["predicted_grade_point"]
        * predicted_subjects["credits"]
    )

    total_credits = predicted_subjects["credits"].sum()

    predicted_sga = (
        predicted_subjects["weighted_grade_point"].sum()
        / total_credits
    )


    previous_cg_query = """
    SELECT
        sr.academic_year,
        sr.semester,
        sr.sga,
        SUM(c.credits) AS semester_credits
    FROM semester_results sr
    JOIN students s
        ON s.student_id = sr.student_id
    JOIN curriculum c
        ON c.branch = s.branch
        AND c.academic_year = sr.academic_year
        AND c.semester = sr.semester
    WHERE sr.student_id = %s
    AND (
        sr.academic_year < %s
        OR (
            sr.academic_year = %s
            AND sr.semester < %s
        )
    )
    GROUP BY
        sr.academic_year,
        sr.semester,
        sr.sga
    ORDER BY
        sr.academic_year,
        sr.semester
    """

    previous_cg_data = pd.read_sql(
        previous_cg_query,
        con,
        params=(
            selected_student,
            student_year,
            student_year,
            student_semester
        )
    )

    if not previous_cg_data.empty:

        previous_weighted_points = (
            previous_cg_data["sga"]
            * previous_cg_data["semester_credits"]
        ).sum()

        previous_total_credits = (
            previous_cg_data["semester_credits"].sum()
        )

        estimated_cg = (
            previous_weighted_points
            + predicted_sga * total_credits
        ) / (
            previous_total_credits + total_credits
        )

    else:
        estimated_cg = predicted_sga


    st.subheader("Semester Prediction")

    predicted_subjects["backlog_risk"] = predicted_subjects[
        "estimated_grade"
    ].apply(
        lambda grade:
            "High"
            if grade in ["FF", "FA"]
            else "Low"
    )

    predicted_backlog_count = (
        predicted_subjects["backlog_risk"] == "High"
    ).sum()

    if predicted_backlog_count > 0:
        backlog_risk = "High"
    elif predicted_subjects["predicted_marks"].lt(40).any():
        backlog_risk = "Moderate"
    else:
        backlog_risk = "Low"

    if predicted_sga >= 9:
        performance_category = "Amazing"
    elif predicted_sga >= 8:
        performance_category = "Decent"
    elif predicted_sga >= 7:
        performance_category = "Average"
    elif predicted_sga >= 6:
        performance_category = "Below Par"
    else:
        performance_category = "Very Bad"

    col1, col2, col3 ,col4= st.columns(4)

    with col1:
        st.metric(
            "Estimated SGA",
            f"{predicted_sga:.2f}"
        )

    with col2:
        st.metric(
            "Estimated CG",
            f"{estimated_cg:.2f}"
        )

    with col3:
        st.metric(
            "Backlog Risk",
            backlog_risk
        )

    with col4:
        st.metric(
            "Performance Category",
            performance_category
        )


    predicted_subjects["attendance_action"] = None
    predicted_subjects["attendance_status"] = None

    for i, row in predicted_subjects.iterrows():

        attendance = row["attendance_percentage"]
        attended = row["classes_attended"]
        held = row["classes_held"]

        if pd.isna(attendance) or pd.isna(attended) or pd.isna(held):
            predicted_subjects.loc[i, "attendance_status"] = "Unavailable"
            predicted_subjects.loc[i, "attendance_action"] = (
                "Attendance data unavailable."
            )

        elif attendance >= 75:
            predicted_subjects.loc[i, "attendance_status"] = "Safe"

            can_miss = max(
                0,
                int((attended / 0.75) - held)
            )

            if can_miss == 0:
                predicted_subjects.loc[i, "attendance_action"] = (
                    "Cannot miss another class while maintaining 75%."
                )
            else:
                predicted_subjects.loc[i, "attendance_action"] = (
                    f"Can miss approximately {can_miss} more classes."
                )

        else:
            predicted_subjects.loc[i, "attendance_status"] = "Shortage"

            required = max(
                0,
                int(np.ceil((0.75 * held - attended) / 0.25))
            )

            predicted_subjects.loc[i, "attendance_action"] = (
                f"Must attend the next {required} classes."
            )

    
    st.dataframe(
        predicted_subjects[
            [
                "subject_code",
                "subject_name",
                "credits",
                "predicted_marks",
                "estimated_grade",
                "backlog_risk",
                "feedback"
            ]
        ],
        width="stretch"
    )

    st.subheader("Attendance Tracker")

    st.dataframe(
        predicted_subjects[
            [
                "subject_code",
                "credits",
                "attendance_percentage",
                "attendance_status",
                "attendance_action",
            ]
        ],
        width="stretch"
    )

    st.subheader("Historical Performance Comparison")

    historical_comparison_df = predicted_subjects[
        [
            "subject_code",
            "subject_name",
            "predicted_marks",
            "historical_average",
            "performance_vs_history",
            "historical_comparison",
            "historical_performance_gap"
        ]
    ].copy()

    historical_comparison_df["performance_vs_history"] = pd.to_numeric(
        historical_comparison_df["performance_vs_history"],
        errors="coerce"
    )

    historical_comparison_df["predicted_marks"] = pd.to_numeric(
        historical_comparison_df["predicted_marks"],
        errors="coerce"
    )

    historical_comparison_df["historical_average"] = pd.to_numeric(
        historical_comparison_df["historical_average"],
        errors="coerce"
    )

    comparison_chart_df = historical_comparison_df[
        [
            "subject_name",
            "predicted_marks",
            "historical_average"
        ]
    ].copy()

    comparison_chart_df = comparison_chart_df.melt(
        id_vars="subject_name",
        value_vars=[
            "predicted_marks",
            "historical_average"
        ],
        var_name="Performance Type",
        value_name="Marks"
    )

    comparison_chart_df["Performance Type"] = (
        comparison_chart_df["Performance Type"].replace({
            "predicted_marks": "Predicted Marks",
            "historical_average": "Historical Average"
        })
    )

    fig = px.bar(
        comparison_chart_df,
        x="subject_name",
        y="Marks",
        color="Performance Type",
        barmode="group",
        title="Predicted Marks vs Historical Average"
    )

    fig.update_layout(
        xaxis_title="Subject",
        yaxis_title="Marks",
        yaxis_range=[0, 100]
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )

    performance_status_df = historical_comparison_df[
        [
            "subject_code",
            "subject_name",
            "predicted_marks",
            "historical_average",
            "performance_vs_history"
        ]
    ].copy()

    performance_status_df = performance_status_df.merge(
        predicted_subjects[
            [
                "subject_code",
                "attendance_percentage",
                "estimated_grade"
            ]
        ],
        on="subject_code",
        how="left"
    )

    performance_status_df["performance_status"] = (
        performance_status_df["performance_vs_history"].apply(
            lambda x:
                "Excellent"
                if x >= 10
                else "Above Average"
                if x >= 3
                else "Average"
                if x > -3
                else "Below Average"
                if x > -10
                else "Needs Improvement"
        )
    )

    performance_status_df = performance_status_df.sort_values(
        by="performance_vs_history"
    )

    st.dataframe(
        performance_status_df[
        [ 
            "subject_code",
            "subject_name",
            "predicted_marks",
            "historical_average",
            "performance_vs_history",
            "performance_status",
        ]
    ],
        width="stretch"
    )

    st.subheader("Subject-Specific Advice")

    def generate_subject_advice(row):

        if row["attendance_percentage"] < 75:
            return "Attendance shortage: improve attendance immediately and attend the required upcoming classes."

        if row["estimated_grade"] in ["FF", "FA"]:
            return "High risk: the predicted grade indicates a possible backlog. Prioritize this subject and seek academic support."

        if row["performance_vs_history"] <= -10:
            return "High priority: significantly below historical performance. Increase study time and focus on weak concepts."

        elif row["performance_vs_history"] <= -3:
            return "Needs improvement: performance is below the historical average. Review difficult topics and practice more questions."

        elif row["performance_vs_history"] < 3:
            return "Maintain consistency: performance is close to the historical average. Regular revision can help improve further."

        elif row["performance_vs_history"] < 10:
            return "Good performance: currently above the historical average. Continue the same preparation strategy."

        else:
            return "Excellent performance: significantly above the historical average. Maintain your current preparation level."
    
    performance_status_df["advice"] = (
        performance_status_df.apply(
            generate_subject_advice,
            axis=1
        )
    )

    st.dataframe(
        performance_status_df[
            [
                "subject_code",
                "performance_status",
                "advice"
            ]
        ],
        column_config={
            "advice": st.column_config.TextColumn(
                "Advice",
                width="large")
                ,
        "subject_code": st.column_config.TextColumn(
            "Subject",
            width="small"
        ),
        "performance_status": st.column_config.TextColumn(
            "Status",
            width="small"
        )
        },
        width="stretch"
    )


    st.subheader("Overall Academic Risk")

    high_risk_subjects = (
        predicted_subjects["backlog_risk"] == "High"
    ).sum()

    moderate_risk_subjects = (
        predicted_subjects["predicted_marks"] < 40
    ).sum()

    attendance_shortage_subjects = (
        predicted_subjects["attendance_percentage"] < 75
    ).sum()

    if high_risk_subjects > 0:
        overall_academic_risk = "High"
    elif attendance_shortage_subjects > 0 or moderate_risk_subjects > 0:
        overall_academic_risk = "Moderate"
    else:
        overall_academic_risk = "Low"

    col1, col2= st.columns(2)


    with col1:
        st.metric(
            "High-Risk Subjects",
            int(high_risk_subjects)
        )

    with col2:
        st.metric(
            "Attendance Shortages",
            int(attendance_shortage_subjects)
        )

    if overall_academic_risk == "High":

        risk_explanation = (
            f"High academic risk: {high_risk_subjects} subject(s) "
            "currently show a predicted backlog risk. "
            "Immediate attention is recommended."
        )

    elif overall_academic_risk == "Moderate":

        reasons = []

        if attendance_shortage_subjects > 0:
            reasons.append(
                f"{attendance_shortage_subjects} subject(s) have attendance below 75%"
            )

        if moderate_risk_subjects > 0:
            reasons.append(
                f"{moderate_risk_subjects} subject(s) have predicted marks below 40"
            )

        risk_explanation = (
            "Moderate academic risk: "
            + " and ".join(reasons)
            + "."
        )

    else:

        risk_explanation = (
            "Low academic risk: no predicted backlog risk, "
            "no predicted marks below 40, and no attendance shortage."
        )

    st.info(risk_explanation)


    if overall_academic_risk == "High":

        high_risk_df = predicted_subjects[
            predicted_subjects["backlog_risk"] == "High"
        ]

        high_risk_subjects_list = high_risk_df["subject_name"].tolist()

        st.error("Recommended Action")

        for subject in high_risk_subjects_list:
            st.write(
                f"🔴 **{subject}** — High backlog risk. "
                "Prioritize this subject immediately and seek additional academic support."
            )

    elif overall_academic_risk == "Moderate":

        moderate_subjects = predicted_subjects[
            (predicted_subjects["predicted_marks"] < 40)
            | (predicted_subjects["attendance_percentage"] < 75)
        ]

        st.warning("Recommended Action")

        for _, row in moderate_subjects.iterrows():

            reasons = []

            if row["predicted_marks"] < 40:
                reasons.append(
                    f"predicted marks are {row['predicted_marks']:.1f}"
                )

            if row["attendance_percentage"] < 75:
                reasons.append(
                    f"attendance is {row['attendance_percentage']:.1f}%"
                )

            st.write(
                f"🟠 **{row['subject_name']}** — "
                + " and ".join(reasons)
                + ". Focus on this subject and take corrective action."
            )

    else:

        below_average_subjects = predicted_subjects[
            predicted_subjects["historical_performance_gap"].isin(
                ["Below", "Significantly Below"]
            )
        ]

        if not below_average_subjects.empty:

            st.success("Recommended Action")

            for _, row in below_average_subjects.iterrows():

                st.write(
                    f"🟢 **{row['subject_name']}** — "
                    f"currently predicted at {row['predicted_marks']:.1f} marks, "
                    "which is below the historical average. "
                    "Consider additional revision and practice."
                )

        else:

            st.success(
                "Overall performance is healthy. "
                "Continue your current preparation strategy and maintain attendance above 75%."
            )

    st.subheader("Subject Action Priorities")

    subject_action_df = predicted_subjects[
        [
            "subject_code",
            "subject_name",
            "predicted_marks",
            "estimated_grade",
            "attendance_percentage",
            "backlog_risk",
            "historical_performance_gap"
        ]
    ].copy()

    def get_action_priority(row):

        if row["backlog_risk"] == "High":
            return "Critical"

        elif row["attendance_percentage"] < 75:
            return "High"

        elif row["predicted_marks"] < 40:
            return "High"

        elif row["historical_performance_gap"] in [
            "Below",
            "Significantly Below"
        ]:
            return "Medium"

        else:
            return "Low"

    subject_action_df["action_priority"] = (
        subject_action_df.apply(
            get_action_priority,
            axis=1
        )
    )

    priority_order = {
        "Critical": 0,
        "High": 1,
        "Medium": 2,
        "Low": 3
    }

    subject_action_df["priority_order"] = (
        subject_action_df["action_priority"].map(priority_order)
    )

    subject_action_df = subject_action_df.sort_values(
        by="priority_order"
    )

    st.dataframe(
        subject_action_df[
            [
                "subject_code",
                "subject_name",
                "predicted_marks",
                "estimated_grade",
                "attendance_percentage",
                "action_priority",
                "backlog_risk",
            ]
        ],
        width="stretch"
    )
if page == "Individual Subject Prediction":

    st.title("Individual Subject Prediction")

    student_ids = students_df["student_id"].tolist()

    selected_student = st.selectbox(
        "Select Student",
        student_ids,
        key="individual_prediction_student"
    )

    student_info = students_df[
        students_df["student_id"] == selected_student
    ].iloc[0]

    student_branch = student_info["branch"]

    current_semester_df = pd.read_sql(
        """
        SELECT academic_year, semester
        FROM academic_records
        WHERE student_id = %s
        ORDER BY academic_year DESC, semester DESC
        LIMIT 1
        """,
        con,
        params=(selected_student,)
    )

    student_semester = int(current_semester_df.iloc[0]["semester"])
    student_year = int(current_semester_df.iloc[0]["academic_year"])

    subjects_df = pd.read_sql(
        """
        SELECT subject_code, subject_name, credits
        FROM curriculum
        WHERE branch = %s
        AND academic_year = %s
        AND semester = %s
        ORDER BY subject_code
        """,
        con,
        params=(student_branch, student_year, student_semester)
    )

    st.write(
        f"Branch: {student_branch} | "
        f"Year: {student_year} | "
        f"Semester: {student_semester}"
    )

    selected_subject = st.selectbox(
        "Select Subject",
        subjects_df["subject_code"].tolist()
    )

    subject_data = pd.read_sql(
        subject_data_query,
        con,
        params=(
            selected_student,
            selected_subject,
            student_year,
            student_semester
        )
    )
        
    if not subject_data.empty:

        prediction_input = subject_data[
            [
                "quiz1",
                "quiz2",
                "midsem",
                "assignment",
                "attendance_percentage",
                "prev_sga",
                "prev_sem_percentage",
                "prev_total_backlogs"
            ]
        ].copy()

        prediction_input["subject_code"] = selected_subject
        prediction_input["branch"] = student_branch
        prediction_input["semester"] = student_semester
        prediction_input = prediction_input[
            [
                "subject_code",
                "quiz1",
                "quiz2",
                "midsem",
                "assignment",
                "attendance_percentage",
                "prev_sga",
                "prev_sem_percentage",
                "prev_total_backlogs",
                "branch",
                "semester",
            ]
        ]

        st.subheader("Prediction Input")
        st.dataframe(prediction_input, width="stretch")

        transformed_input = preprocessor.transform(prediction_input)

        predicted_marks = predict_subject(
            selected_subject,
            prediction_input["quiz1"].iloc[0],
            prediction_input["quiz2"].iloc[0],
            prediction_input["midsem"].iloc[0],
            prediction_input["assignment"].iloc[0],
            prediction_input["attendance_percentage"].iloc[0],
            prediction_input["prev_sga"].iloc[0],
            prediction_input["prev_sem_percentage"].iloc[0],
            prediction_input["prev_total_backlogs"].iloc[0]
        )


        prediction_lower = max(0, predicted_marks - prediction_error)
        prediction_upper = min(100, predicted_marks + prediction_error)

        predicted_marks = max(0, min(100, predicted_marks))

        st.subheader("Prediction Confidence")

        st.metric(
            label="Predicted Marks",
            value=f"{predicted_marks:.2f}/100"
        )

        st.write(
            f"Estimated prediction range: "
            f"{prediction_lower:.2f} – {prediction_upper:.2f}"
        )

        st.caption(
            "This range is estimated from training-set prediction errors. "
            "It is not a guarantee, and actual marks may fall outside it."
        )
        

        grade_history_query = """
        SELECT
            a.grade,
            COUNT(*) AS student_count,
            MIN(a.marks_obtained) AS min_marks,
            MAX(a.marks_obtained) AS max_marks,
            AVG(a.marks_obtained) AS avg_marks
        FROM academic_records a
        JOIN curriculum c
            ON a.subject_id = c.subject_id
        WHERE a.subject_code = %s
        AND c.branch = %s
        AND c.semester = %s
        AND a.grade NOT IN ('FF', 'FA')
        GROUP BY a.grade
        ORDER BY avg_marks DESC
        """ 

        grade_history_df = pd.read_sql(
            grade_history_query,
            con,
            params=(
                selected_subject,
                student_branch,
                student_semester
            )
        )

        if not grade_history_df.empty:
            grade_history_df["distance"] = (
                grade_history_df["avg_marks"] - predicted_marks
            ).abs()

            estimated_grade = grade_history_df.loc[
                grade_history_df["distance"].idxmin(),
                "grade"
            ]
        else:
            estimated_grade = "N/A"

        possible_grades = []

        if not grade_history_df.empty:
            matching_grades = grade_history_df[
                (grade_history_df["max_marks"] >= prediction_lower)
                & (grade_history_df["min_marks"] <= prediction_upper)
            ].copy()

            if not matching_grades.empty:
                matching_grades["distance_to_prediction"] = (
                    matching_grades["avg_marks"] - predicted_marks
                ).abs()

                matching_grades = matching_grades.sort_values(
                    "distance_to_prediction"
                ).head(3)

                total_count = matching_grades["student_count"].sum()

                if total_count > 0:
                    possible_grades = [
                        f'{row["grade"]} ({row["student_count"] / total_count:.1%})'
                        for _, row in matching_grades.iterrows()
                    ]

        if not possible_grades:
            possible_grades = ["N/A"]

        

        historical_subject_query = """
        SELECT
            a.marks_obtained,
            a.grade,
            a.grade_point
        FROM academic_records a
        JOIN curriculum c
            ON a.subject_id = c.subject_id
        WHERE a.subject_code = %s
        AND c.branch = %s
        AND c.semester = %s
        """

        historical_subject_data = pd.read_sql(
            historical_subject_query,
            con,
            params=(
                selected_subject,
                student_branch,
                student_semester
            )
        )

        historical_subject_data = historical_subject_data[
            historical_subject_data["grade"].str.upper() != "FA"
        ]

        st.subheader("Estimated Grade")
        st.metric(
            "Grade Based on Historical Performance",
            estimated_grade
        )

        st.write(
            f"**Possible Historical Grades:** {' - '.join(possible_grades)}"
        )

        historical_count = int(grade_history_df["student_count"].sum())

        # Base reliability from model MAE
        model_reliability = max(
            0,
            min(
                100,
                (1 - (model_metrics["mae"] / model_metrics["mean_marks"])) * 100
            )
        )
        if historical_count >= 100:
            history_reliability = 100
        elif historical_count >= 50:
            history_reliability = 90
        elif historical_count >= 20:
            history_reliability = 75
        else:
            history_reliability = 60

        history_missing = prediction_input[
            ["prev_sga", "prev_sem_percentage", "prev_total_backlogs"]
        ].isna().any(axis=1).iloc[0]

        if history_missing:
            history_reliability -= 15

        prediction_reliability = (
            0.7 * model_reliability +
            0.3 * history_reliability
        )

        prediction_reliability = max(
            0,
            min(100, prediction_reliability)
        )

        st.metric(
            "Prediction Reliability",
            f"{prediction_reliability:.1f}%"
        )


        if st.button("Save Prediction", key="save_subject_prediction"):
            subject_id_result = pd.read_sql(
                """
                SELECT subject_id
                FROM curriculum
                WHERE subject_code = %s
                  AND branch = %s
                  AND academic_year = %s
                  AND semester = %s
                LIMIT 1
                """,
                con,
                params=(
                    selected_subject,
                    student_branch,
                    student_year,
                    student_semester
                )
            )

            if subject_id_result.empty:
                st.error("Could not find the subject ID.")
            else:
                subject_id = int(
                    subject_id_result.iloc[0]["subject_id"]
                )

                cursor = con.cursor()
                cursor.execute(
                    """
                    INSERT INTO predictions (
                        student_id,
                        subject_id,
                        prediction_type,
                        predicted_marks,
                        predicted_grade,
                        lower_bound,
                        upper_bound,
                        prediction_confidence
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        selected_student,
                        subject_id,
                        "Individual Subject",
                        float(predicted_marks),
                        estimated_grade,
                        float(prediction_lower),
                        float(prediction_upper),
                        float(prediction_reliability)
                    )
                )
                con.commit()
                cursor.close()

                st.success("Prediction saved successfully!")

        st.caption(
            "Reliability indicator based on model validation performance "
            "and historical data availability. It is not the probability "
            "that the prediction is correct."
        )
        

        coefficients = model.named_steps["model"].coef_

        feature_names = preprocessor.get_feature_names_out()

        if hasattr(transformed_input, "toarray"):
            transformed_values = transformed_input.toarray()[0]
        else:
            transformed_values = transformed_input[0]

        contributions = transformed_values * coefficients

        explanation_df = pd.DataFrame({
            "feature": feature_names,
            "contribution": contributions
        })

        feature_labels = {
            "num__quiz1": "Quiz 1",
            "num__quiz2": "Quiz 2",
            "num__midsem": "Midsem",
            "num__assignment": "Assignment",
            "num__attendance_percentage": "Attendance",
            "num__prev_sga": "Previous SGA",
            "num__prev_sem_percentage": "Previous Semester Percentage",
            "num__prev_total_backlogs": "Previous Backlogs",
            "num__semester": "Semester"
        }

        branch_names = {
            "CS": "Computer Science",
            "IT": "Information Technology",
            "AI": "Artificial Intelligence",
            "Mech": "Mechanical Engineering",
            "Civil": "Civil Engineering",
            "Chem": "Chemical Engineering",
            "Metallurgy": "Metallurgical Engineering",
            "ECE": "Electronics & Communication",
            "EEE": "Electrical & Electronics",
            "CDS": "Computational Data Science"
        }

        selected_branch_name = branch_names.get(
            student_branch,
            student_branch
        )

        grouped_explanations = []

        for _, row in explanation_df.iterrows():

            feature = row["feature"]
            contribution = row["contribution"]

            if feature.startswith("cat__subject_code_"):
                label = selected_subject

            elif feature.startswith("cat__branch_"):
                label = selected_branch_name

            elif feature in feature_labels:
                label = feature_labels[feature]

            else:
                label = feature

            grouped_explanations.append({
                "feature": label,
                "contribution": contribution
            })

        explanation_df = pd.DataFrame(grouped_explanations)

        explanation_df = (
            explanation_df
            .groupby("feature", as_index=False)["contribution"]
            .sum()
        )

        explanation_df["absolute_contribution"] = (
            explanation_df["contribution"].abs()
        )

        explanation_df = explanation_df.sort_values(
            "absolute_contribution",
            ascending=False
        )

        top_explanations = explanation_df.head(10).copy()

        top_explanations = top_explanations.sort_values(
            "contribution"
        )

        fig = px.bar(
            top_explanations,
            x="contribution",
            y="feature",
            orientation="h",
            title="Factors Influencing Prediction",
            labels={
                "contribution": "Contribution to Prediction",
                "feature": "Feature"
            }
        )

        fig.add_vline(
            x=0,
            line_width=1
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )

        st.subheader("Model Inputs")
        
        input_display = subject_data[
            [
                "quiz1",
                "quiz2",
                "midsem",
                "assignment",
                "attendance_percentage",
                "prev_sga",
                "prev_sem_percentage",
                "prev_total_backlogs"
            ]
        ].T


        input_display.columns = ["Value"]

        st.dataframe(input_display)

        st.caption(
            "Positive values increase the predicted marks, while negative values "
            "decrease the predicted marks."
        )

        positive_factors = explanation_df[
            explanation_df["contribution"] > 0
        ].sort_values(
            "contribution",
            ascending=False
        )

        negative_factors = explanation_df[
            explanation_df["contribution"] < 0
        ].sort_values(
            "contribution"
        )

        col1, col2 = st.columns(2)

        with col1:
            st.write("### Strongest Positive Factors")

            for _, row in positive_factors.head(3).iterrows():
                st.write(
                    f"🟢 **{row['feature']}**: "
                    f"+{row['contribution']:.2f}"
                )

        with col2:
            st.write("### Strongest Negative Factors")

            for _, row in negative_factors.head(3).iterrows():
                st.write(
                    f"🔴 **{row['feature']}**: "
                    f"{row['contribution']:.2f}"
                )

        historical_df = historical_subject_data.copy()

        estimated_grade_row = grade_history_df[
            grade_history_df["grade"] == estimated_grade
        ]

        if not estimated_grade_row.empty:
            grade_min_marks = estimated_grade_row.iloc[0]["min_marks"]
            grade_max_marks = estimated_grade_row.iloc[0]["max_marks"]
            grade_student_count = estimated_grade_row.iloc[0]["student_count"]
        else:
            grade_min_marks = None
            grade_max_marks = None
            grade_student_count = 0

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                f"{estimated_grade} Historical Minimum",
                f"{grade_min_marks:.0f}"
                if grade_min_marks is not None else "N/A"
            )

        with col2:
            st.metric(
                f"{estimated_grade} Historical Maximum",
                f"{grade_max_marks:.0f}"
                if grade_max_marks is not None else "N/A"
            )

        with col3:
            st.metric(
                f"Students with {estimated_grade}",
                f"{int(grade_student_count)}"
            )

        historical_percentile = (
            historical_df["marks_obtained"] < predicted_marks
        ).mean() * 100

        st.metric(
            "Historical Percentile",
            f"{historical_percentile:.1f}%"
        )

        if historical_percentile >= 90:
            percentile_category = "Top 10%"
        elif historical_percentile >= 75:
            percentile_category = "Above Average"
        elif historical_percentile >= 50:
            percentile_category = "Average"
        elif historical_percentile >= 25:
            percentile_category = "Below Average"
        else:
            percentile_category = "Bottom 25%"

        st.write(
            f"**Historical Performance Category:** {percentile_category}"
        )

        fig = px.histogram(
            historical_df,
            x="marks_obtained",
            nbins=15,
            title="Historical Marks Distribution",
            labels={
                "marks_obtained": "Marks"
            }
        )

        fig.add_vline(
            x=predicted_marks,
            line_width=3,
            line_color="#00E5FF",
            line_dash="solid",
            annotation_text=f"Predicted: {predicted_marks:.1f}",
            annotation_position="top"
        )

        fig.add_vline(
            x=prediction_lower,
            line_width=3,
            line_color="#FFD166",
            line_dash="dot",
            annotation_text=f"Min Predicted: {prediction_lower:.1f}",
            annotation_position="bottom"
        )

        fig.add_vline(
            x=prediction_upper,
            line_width=3,
            line_color="#FF6B6B",
            line_dash="dot",
            annotation_text=f"Max Predicted: {prediction_upper:.1f}",
            annotation_position="bottom"
        )

        x_min = min(
            historical_df["marks_obtained"].min(),
            prediction_lower
        )
        x_max = max(
            historical_df["marks_obtained"].max(),
            prediction_upper
        )

        fig.update_xaxes(range=[x_min - 2, x_max + 2])

        st.plotly_chart(fig, width="stretch")

        grade_distribution = (
            historical_df["grade"]
            .value_counts()
            .reindex(
                ["AA", "AB", "BB", "BC", "CC", "CD", "DD","FF","FA"],
                fill_value=0
            )
            .reset_index()
        )

        grade_distribution.columns = ["grade", "student_count"]

        grade_distribution["highlight"] = (
            grade_distribution["grade"] == estimated_grade
        )

        fig = px.bar(
            grade_distribution,
            x="grade",
            y="student_count",
            title="Historical Grade Distribution",
            labels={
                "grade": "Grade",
                "student_count": "Number of Students"
            },
            color="highlight",
            color_discrete_map={
                True: "white",
                False: "#444444"
            },
            category_orders={
                "grade": ["AA", "AB", "BB", "BC", "CC", "CD", "DD","FF","FA"]
            }
        )

        fig.update_layout(
            showlegend=False
        )

        fig.add_annotation(
            x=estimated_grade,
            y=grade_distribution.loc[
                grade_distribution["grade"] == estimated_grade,
                "student_count"
            ].iloc[0],
            text=f"Estimated Grade: {estimated_grade}",
            showarrow=True,
            arrowhead=2
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )

    st.subheader("Subject-wise Grade Cutoffs")

    subject_cutoffs_df = pd.read_sql(
        """
        SELECT
            grade,
            MIN(marks_obtained) AS minimum_marks,
            MAX(marks_obtained) AS maximum_marks
        FROM academic_records
        WHERE subject_code = %s and grade <> "FA"
        GROUP BY grade, grade_point
        ORDER BY grade_point DESC
        """,
        con,
        params=(selected_subject,)
    )

    if not subject_cutoffs_df.empty:
        subject_cutoffs_df["minimum_marks"] = (
            subject_cutoffs_df["minimum_marks"].round(2)
        )

        subject_cutoffs_df["maximum_marks"] = (
            subject_cutoffs_df["maximum_marks"].round(2)
        )

        st.dataframe(
            subject_cutoffs_df.rename(columns={
                "grade": "Grade",
                "minimum_marks": "Minimum Historical Marks",
                "maximum_marks": "Maximum Historical Marks",
            }),
            width="stretch",
            hide_index=True
        )
    else:
        st.info("No historical grade data is available for this subject.")

        st.subheader("Historical Subject Performance")
        st.dataframe(
            historical_subject_data,
            width="stretch"
        )


    fig_comparison = go.Figure()

    grade_colors = {
        "AA": "#2ca02c",
        "AB": "#4da6ff",
        "BB": "#f1c40f",
        "BC": "#ff9933",
        "CC": "#ff6677",
        "CD": "#9966cc",
        "DD": "#999999",
        "FF": "#d62728",
        "FA": "#8c564b"
    }

    for _, row in subject_cutoffs_df.iterrows():
        grade = row["grade"]
        minimum = float(row["minimum_marks"])
        maximum = float(row["maximum_marks"])

        fig_comparison.add_trace(go.Bar(
            x=[grade],
            y=[maximum - minimum],
            base=[minimum],
            name=grade,
            marker_color=grade_colors.get(grade, "#aaaaaa"),
            showlegend=False,
            hovertemplate=(
                f"Grade: {grade}<br>"
                "Minimum: %{base}<br>"
                "Maximum: %{customdata}<extra></extra>"
            ),
            customdata=[maximum]
        ))

    fig_comparison.add_trace(go.Scatter(
        x=subject_cutoffs_df["grade"],
        y=[predicted_marks] * len(subject_cutoffs_df),
        mode="markers",
        name="Predicted Marks",
        marker=dict(
            color="red",
            size=12,
            symbol="circle",
            line=dict(color="white", width=1)
        ),
        hovertemplate="Predicted Marks: %{y:.2f}<extra></extra>"
    ))

    fig_comparison.update_layout(
        title=f"Prediction Compared with Historical Grade Ranges — {selected_subject}",
        xaxis_title="Grade",
        yaxis_title="Marks",
        yaxis=dict(range=[0, 100]),
        barmode="overlay",
        showlegend=True
    )

    st.subheader("Predicted Marks vs Historical Grade Ranges")

    fig_comparison = go.Figure()

    grade_colors = {
        "AA": "#2ca02c",
        "AB": "#4da6ff",
        "BB": "#f1c40f",
        "BC": "#ff9933",
        "CC": "#ff6677",
        "CD": "#9966cc",
        "DD": "#999999",
        "FF": "#d62728",
        "FA": "#8c564b"
    }

    matching_grades = []

    for _, row in subject_cutoffs_df.iterrows():
        grade = row["grade"]
        minimum = float(row["minimum_marks"])
        maximum = float(row["maximum_marks"])

        contains_prediction = minimum <= predicted_marks <= maximum

        if contains_prediction:
            matching_grades.append(grade)

        fig_comparison.add_trace(go.Bar(
            x=[grade],
            y=[maximum - minimum],
            base=[minimum],
            name=grade,
            marker_color=grade_colors.get(grade, "#aaaaaa"),
            opacity=1.0 if contains_prediction else 0.45,
            showlegend=False,
            customdata=[[minimum, maximum]],
            hovertemplate=(
                "Grade: %{x}<br>"
                "Minimum: %{customdata[0]:.2f}<br>"
                "Maximum: %{customdata[1]:.2f}"
                "<extra></extra>"
            )
        ))

    fig_comparison.add_hline(
        y=predicted_marks,
        line_color="red",
        line_width=2,
        line_dash="dash",
        annotation_text=f"Predicted marks: {predicted_marks:.2f}",
        annotation_position="top left"
    )

    fig_comparison.update_layout(
        title=f"Predicted Marks vs Historical Grade Ranges — {selected_subject}",
        xaxis_title="Grade",
        yaxis_title="Marks",
        yaxis=dict(range=[0, 100]),
        barmode="overlay"
    )

    st.plotly_chart(
        fig_comparison,
        width="stretch",
        key="predicted_marks_historical_grade_ranges"
    )

    if matching_grades:
        st.success(
            f"Predicted marks of {predicted_marks:.2f} fall within "
            f"the historical range for grade(s): {', '.join(matching_grades)}."
        )
    else:
        st.warning(
            f"Predicted marks of {predicted_marks:.2f} fall outside "
            "all observed historical grade ranges."
        )

    st.subheader("Prediction Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Predicted Marks",
            f"{predicted_marks:.2f}/100"
        )

    with col2:
        st.metric(
            "Estimated Grade",
            estimated_grade
        )

    with col3:
        if matching_grades:
            historical_match = ", ".join(matching_grades)
        else:
            historical_match = "Outside observed ranges"

        st.metric(
            "Historical Range Match",
            historical_match
        )

    st.subheader("Prediction Uncertainty")

    prediction_lower = max(0, predicted_marks - 1.96 * residual_std)
    prediction_upper = min(100, predicted_marks + 1.96 * residual_std)

    st.metric(
        "Approximate Prediction Range",
        f"{prediction_lower:.2f} – {prediction_upper:.2f}"
    )

    st.caption(
        "This is an approximate range based on the model's residual "
        "standard deviation, assuming roughly normal and stable prediction errors. "
        "It is not a guaranteed interval."
    )

    st.subheader("Model Validation Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("MAE", f"{model_metrics['mae']:.2f}")

    with col2:
        st.metric("RMSE", f"{model_metrics['rmse']:.2f}")

    with col3:
        st.metric("R² Score", f"{model_metrics['r2_score']:.4f}")

    with col4:
        st.metric("Mean Marks", f"{model_metrics['mean_marks']:.2f}")

    st.caption(
        "These metrics summarize model evaluation performance. "
        "They do not establish the confidence of an individual prediction."
    )

elif page == "Student Risk Analysis":
    st.subheader("Student Academic Risk Analysis")

    risk_query = """
    SELECT
        s.student_id,
        sr.academic_year,
        sr.semester,
        sr.sga,
        sr.semester_percentage,
        sr.total_backlogs,
        sr.semester_status
    FROM students s
    JOIN semester_results sr
        ON s.student_id = sr.student_id
    ORDER BY s.student_id, sr.academic_year, sr.semester
    """

    risk_df = pd.read_sql(risk_query, con)

    if risk_df.empty:
        st.warning("No semester records available for risk analysis.")

    else:
        risk_df["sga_change"] = (
            risk_df.groupby("student_id")["sga"].diff()
        )

        risk_df["risk_factors"] = (
            (risk_df["sga"] < 5) |
            (risk_df["sga_change"] <= -1) |
            (risk_df["total_backlogs"] >= 3) |
            (risk_df["semester_percentage"] < 50)
        )

        risk_df["Risk Indicators"] = risk_df["risk_factors"].apply(
            lambda value: "Needs Review" if value else "No Flagged Indicators"
        )

        st.subheader("Student Risk Summary")

        st.dataframe(
            risk_df[
                [
                    "student_id",
                    "academic_year",
                    "semester",
                    "sga",
                    "sga_change",
                    "semester_percentage",
                    "total_backlogs",
                    "Risk Indicators"
                ]
            ],
            width="stretch"
        )

        risk_summary = risk_df.groupby("student_id").agg(
            Semesters_Recorded=("semester", "count"),
            Flagged_Semesters=("risk_factors", "sum"),
            Latest_SGA=("sga", "last"),
            Latest_Backlogs=("total_backlogs", "last"),
            Latest_Percentage=("semester_percentage", "last")
        ).reset_index()

        risk_summary["Risk Level"] = risk_summary["Flagged_Semesters"].apply(
            lambda count: (
                "High Review Priority" if count >= 3
                else "Needs Review" if count >= 1
                else "No Flagged Indicators"
            )
        )

        risk_summary = risk_summary.sort_values(
            by=["Flagged_Semesters", "Latest_Backlogs"],
            ascending=[False, False]
        )

        backlog_history_df = pd.read_csv("backlog_history_demo_download.csv")

        backlog_counts = (
            backlog_history_df.assign(
                is_pending=backlog_history_df["clearance_status"].eq("Pending"),
                is_cleared=backlog_history_df["clearance_status"].eq("Cleared")
            )
            .groupby("student_id")
            .agg(
                Total_Recorded_Backlogs=("student_id", "size"),
                Cleared_Backlogs=("is_cleared", "sum"),
                Pending_Backlogs=("is_pending", "sum")
            )
            .reset_index()
        )

        risk_summary["student_id"] = risk_summary["student_id"].astype(str)
        backlog_counts["student_id"] = backlog_counts["student_id"].astype(str)

        risk_summary = risk_summary.merge(
            backlog_counts,
            on="student_id",
            how="left"
        )

        for col in [
            "Total_Recorded_Backlogs",
            "Cleared_Backlogs",
            "Pending_Backlogs"
        ]:
            risk_summary[col] = risk_summary[col].fillna(0).astype(int)


        risk_summary["Risk Level"] = risk_summary.apply(
            lambda row: (
                "High Review Priority"
                if row["Pending_Backlogs"] >= 3
                or row["Flagged_Semesters"] >= 3
                else "Needs Review"
                if row["Pending_Backlogs"] >= 1
                or row["Flagged_Semesters"] >= 1
                else "No Flagged Indicators"
            ),
            axis=1
        )

        st.subheader("Semester Risk Indicators")

        risk_levels = [
            "High Review Priority",
            "Needs Review",
            "No Flagged Indicators"
        ]

        selected_risk_levels = st.multiselect(
            "Filter by Risk Level",
            options=risk_levels,
            default=risk_levels
        )

        filtered_risk_summary = risk_summary[
            risk_summary["Risk Level"].isin(selected_risk_levels)
        ]

        student_search = st.text_input(
        "Search by Student ID"
        )

        if student_search:
            filtered_risk_summary = filtered_risk_summary[
                filtered_risk_summary["student_id"]
                .astype(str)
                .str.contains(student_search, case=False, na=False)
            ]

        st.dataframe(
            filtered_risk_summary,
            width="stretch"
        )

elif page == "Historical Comparison":
    st.subheader("Historical Academic Performance")

    student_ids = students_df["student_id"].tolist()

    selected_student = st.selectbox(
        "Select Student for Historical Comparison",
        student_ids,
        key="historical_student"
    )

    history_query = """
    SELECT
        academic_year,
        semester,
        sga,
        semester_percentage,
        total_backlogs,
        semester_status
    FROM semester_results
    WHERE student_id = %s
    ORDER BY academic_year, semester
    """

    history_df = pd.read_sql(
        history_query,
        con,
        params=(selected_student,)
    )

    if history_df.empty:
        st.warning("No historical semester records found for this student.")

    else:
        history_df["Semester Label"] = (
            history_df["academic_year"].astype(str)
            + " - Sem "
            + history_df["semester"].astype(str)
        )

        st.subheader("SGA Across Semesters")

        st.line_chart(
            history_df.set_index("Semester Label")["sga"]
        )

        st.subheader("Semester Percentage Across Semesters")

        st.line_chart(
            history_df.set_index("Semester Label")["semester_percentage"]
        )

        st.subheader("Backlog History")

        st.bar_chart(
            history_df.set_index("Semester Label")["total_backlogs"]
        )

        st.dataframe(
            history_df,
            width="stretch"
        )

elif page == "Backlog Tracker":
    st.subheader("Student Backlog Tracker")

    backlog_df = pd.read_csv("backlog_history_demo_download.csv")

    st.caption(
        "Demo data: some clearance statuses are synthetic examples, "
        "not verified academic results."
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Backlog Records", len(backlog_df))
    col2.metric(
        "Cleared (Demo)",
        (backlog_df["clearance_status"] == "Cleared").sum()
    )
    col3.metric(
        "Pending",
        (backlog_df["clearance_status"] == "Pending").sum()
    )

    student_filter = st.text_input("Filter by Student ID")

    if student_filter:
        backlog_df = backlog_df[
            backlog_df["student_id"].astype(str).str.contains(
                student_filter, na=False
            )
        ]

    st.dataframe(backlog_df, width="stretch")

    st.download_button(
        "Download Backlog Report",
        data=backlog_df.to_csv(index=False).encode("utf-8"),
        file_name="backlog_report.csv",
        mime="text/csv"
    )

if page == "Prediction Validation":
    st.subheader("Prediction Validation & Feedback")

    validation_query = """
    SELECT
        p.prediction_id,
        p.student_id,
        p.subject_id,
        c.subject_code,
        c.subject_name,
        p.prediction_type,
        p.predicted_marks,
        p.predicted_grade,
        p.created_at
    FROM predictions p
    LEFT JOIN curriculum c
        ON p.subject_id = c.subject_id
    WHERE p.predicted_marks IS NOT NULL
    ORDER BY p.created_at DESC
    """

    predictions_df = pd.read_sql(validation_query, con)

    validated_query = """
    SELECT prediction_id
    FROM prediction_feedback
    """

    validated_ids = set(
        pd.read_sql(
            "SELECT prediction_id FROM prediction_feedback",
            con
        )["prediction_id"].astype(int)
    )

    all_status_counts = predictions_df["prediction_id"].map(
        lambda prediction_id: (
            "Validated"
            if prediction_id in validated_ids
            else "Pending Validation"
        )
    ).value_counts()

    validated_df = pd.read_sql(validated_query, con)

    validated_ids = set(validated_df["prediction_id"].tolist())

    predictions_df["Validation Status"] = predictions_df["prediction_id"].apply(
        lambda prediction_id: (
            "Validated"
            if prediction_id in validated_ids
            else "Pending Validation"
        )
    )

    status_filter = st.multiselect(
        "Filter by Validation Status",
        options=["Pending Validation", "Validated"],
        default=["Pending Validation", "Validated"]
    )

    predictions_df = predictions_df[
        predictions_df["Validation Status"].isin(status_filter)
    ]

    status_counts = predictions_df["Validation Status"].value_counts()

    col1, col2 = st.columns(2)

    col1.metric(
        "Total Pending Validation",
        int(all_status_counts.get("Pending Validation", 0))
    )

    col2.metric(
        "Total Validated",
        int(all_status_counts.get("Validated", 0))
    )

    if predictions_df.empty:
        st.info("No predictions with predicted marks are available to validate yet.")

    else:
        st.dataframe(predictions_df, width="stretch")

        selected_prediction = st.selectbox(
            "Select Prediction ID",
            predictions_df["prediction_id"].tolist()
        )

        selected_row = predictions_df[
            predictions_df["prediction_id"] == selected_prediction
        ].iloc[0]

        prediction_id = int(selected_row["prediction_id"])

        st.write(f"Student ID: {selected_row['student_id']}")
        st.write(f"Predicted Marks: {selected_row['predicted_marks']}")
        st.write(f"Predicted Grade: {selected_row['predicted_grade']}")

        actual_marks = st.number_input(
            "Actual Final Marks",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.5,
            key=f"actual_marks_{prediction_id}"
        )

        grade_options = ["AA", "AB", "BB", "BC", "CC", "CD", "DD", "FF", "FA"]

        actual_grade = st.radio(
            "Actual Final Grade — select one",
            options=grade_options,
            index=None,
            key=f"actual_grade_{prediction_id}"
        )
        

        feedback_notes = st.text_area(
            "Feedback Notes",
            placeholder="Optional observations about the prediction",
            key=f"feedback_notes_{prediction_id}"
        )
        if st.button("Save Validation"):
            if actual_grade is None:
                st.warning("Please select the actual final grade.")
            else:
                absolute_error = abs(
                    float(selected_row["predicted_marks"]) - actual_marks
                )

                cursor.execute("""
                    INSERT INTO prediction_feedback
                    (
                        prediction_id,
                        actual_marks,
                        actual_grade,
                        absolute_error,
                        feedback_notes
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    prediction_id,
                    actual_marks,
                    actual_grade,
                    absolute_error,
                    feedback_notes
                ))

                con.commit()

                st.success(
                    f"Validation saved. Absolute error: {absolute_error:.2f} marks"
                )

                st.rerun()

        st.divider()
        st.subheader("Prediction Validation Results")

        results_query = """
            SELECT
                pf.prediction_id,
                p.student_id,
                c.subject_code,
                pf.actual_marks,
                p.predicted_marks,
                pf.absolute_error,
                pf.feedback_date AS validated_at,
                pf.actual_grade,
                p.predicted_grade
            FROM prediction_feedback pf
            JOIN predictions p
                ON pf.prediction_id = p.prediction_id
            LEFT JOIN curriculum c
                ON p.subject_id = c.subject_id
            ORDER BY pf.feedback_date DESC
        """

        results_df = pd.read_sql(results_query, con)

        if results_df.empty:
            st.info("No predictions have been validated yet.")

        else:

            grade_order = ["AA", "AB", "BB", "BC", "CC", "CD", "DD", "FF", "FA"]

            grade_to_rank = {
                grade: rank for rank, grade in enumerate(grade_order)
            }

            grade_comparison_df = results_df[
                results_df["actual_grade"].isin(grade_order)
                & results_df["predicted_grade"].isin(grade_order)
            ].copy()

            if not grade_comparison_df.empty:
                exact_matches = (
                    grade_comparison_df["actual_grade"]
                    == grade_comparison_df["predicted_grade"]
                ).sum()

                grade_accuracy = (
                    exact_matches / len(grade_comparison_df)
                ) * 100

                st.metric(
                    "Exact Grade Accuracy",
                    f"{grade_accuracy:.1f}%"
                )

                grade_comparison_df["actual_rank"] = (
                    grade_comparison_df["actual_grade"].map(grade_to_rank)
                )

                grade_comparison_df["predicted_rank"] = (
                    grade_comparison_df["predicted_grade"].map(grade_to_rank)
                )

                within_one_band = (
                    (
                        grade_comparison_df["actual_rank"]
                        - grade_comparison_df["predicted_rank"]
                    ).abs() <= 1
                ).mean() * 100

                st.metric(
                    "Accuracy Within One Grade Band",
                    f"{within_one_band:.1f}%"
                )
            else:
                st.info("No validated grade comparisons are available yet.")

            total_validations = len(results_df)
            mae = results_df["absolute_error"].mean()
            median_error = results_df["absolute_error"].median()
            within_5_marks = (
                results_df["absolute_error"] <= 5
            ).mean() * 100

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Validated Predictions", total_validations)
            col2.metric("Mean Absolute Error", f"{mae:.2f} marks")
            col3.metric("Median Absolute Error", f"{median_error:.2f} marks")
            col4.metric("Within 5 Marks", f"{within_5_marks:.1f}%")

            st.subheader("Actual vs Predicted Marks")

            chart_df = results_df[
                ["prediction_id", "actual_marks", "predicted_marks"]
            ].set_index("prediction_id")

            st.scatter_chart(
                chart_df,
                x="actual_marks",
                y="predicted_marks"
            )

            st.subheader("Validation Records")
            st.dataframe(results_df, width="stretch")

            st.download_button(
                "Download Validation Report",
                data=results_df.to_csv(index=False).encode("utf-8"),
                file_name="prediction_validation_report.csv",
                mime="text/csv"
            )