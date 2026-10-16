if page == "Subject Prediction":

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

        transformed_input = preprocessor.transform(prediction_input)

        predicted_marks = model.predict(transformed_input)[0]

        predicted_marks = max(
            0,
            min(100, predicted_marks)
        )

        return predicted_marks

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


    for i, row in all_subjects_data.iterrows():

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
            predicted_subjects["subject_code"] == row["subject_code"],
            "predicted_marks"
        ] = predicted_marks

        predicted_subjects.loc[
            predicted_subjects["subject_code"] == row["subject_code"],
            "quiz1"
        ] = row["quiz1"]

        predicted_subjects.loc[
            predicted_subjects["subject_code"] == row["subject_code"],
            "quiz2"
        ] = row["quiz2"]

        predicted_subjects.loc[
            predicted_subjects["subject_code"] == row["subject_code"],
            "midsem"
        ] = row["midsem"]

        predicted_subjects.loc[
            predicted_subjects["subject_code"] == row["subject_code"],
            "assignment"
        ] = row["assignment"]

        predicted_subjects.loc[
            predicted_subjects["subject_code"] == row["subject_code"],
            "classes_attended"
        ] = row["classes_attended"]

        predicted_subjects.loc[
            predicted_subjects["subject_code"] == row["subject_code"],
            "classes_held"
        ] = row["classes_held"]

        predicted_subjects.loc[
            predicted_subjects["subject_code"] == row["subject_code"],
            "attendance_percentage"
        ] = row["attendance_percentage"]

    predicted_subjects["estimated_grade"] = None

    for i, row in predicted_subjects.iterrows():

        subject_code = row["subject_code"]
        predicted_marks = row["predicted_marks"]

        grade_history_query = """
        SELECT
            a.grade,
            AVG(a.marks_obtained) AS avg_marks
        FROM academic_records a
        JOIN curriculum c
            ON a.subject_id = c.subject_id
        WHERE a.subject_code = %s
        AND c.branch = %s
        AND c.semester = %s
        AND a.grade NOT IN ('FF', 'FA')
        GROUP BY a.grade
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

        if not grade_history.empty:

            grade_history["distance"] = (
                grade_history["avg_marks"] - predicted_marks
            ).abs()

            estimated_grade = grade_history.loc[
                grade_history["distance"].idxmin(),
                "grade"
            ]

            predicted_subjects.loc[
                i,
                "estimated_grade"
            ] = estimated_grade

    def generate_subject_feedback(row):

        feedback = []

        predicted_marks = row["predicted_marks"]

        if pd.isna(predicted_marks):
            return "Prediction unavailable for this subject."

        if predicted_marks >= 85:
            feedback.append("Strong predicted performance in this subject.")
        elif predicted_marks >= 70:
            feedback.append("Decent predicted performance, with room for improvement.")
        elif predicted_marks >= 55:
            feedback.append("Average predicted performance. Improvement is recommended.")
        else:
            feedback.append("Low predicted performance. This subject needs attention.")

        if pd.notna(row["attendance_percentage"]) and row["attendance_percentage"] < 75:
            feedback.append("Attendance is below the required 75%.")

        if pd.notna(row["quiz1"]) and row["quiz1"] < 10:
            feedback.append("Quiz 1 performance could be improved.")

        if pd.notna(row["quiz2"]) and row["quiz2"] < 10:
            feedback.append("Quiz 2 performance could be improved.")

        if pd.notna(row["midsem"]) and row["midsem"] < 20:
            feedback.append("Mid-semester performance could be improved.")

        if pd.notna(row["assignment"]) and row["assignment"] < 5:
            feedback.append("Assignment performance could be improved.")

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

    predicted_subjects["backlog_risk"] = predicted_subjects["estimated_grade"].apply(
        lambda grade: "High" if grade in ["FF", "FA"] else "Low"
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
                int(3 * held - 4 * attended)
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
                "attendance_percentage",
                "attendance_status",
                "attendance_action",
                "predicted_marks",
                "estimated_grade",
                "predicted_grade_point",
                "backlog_risk",
                "feedback"
            ]
        ],
        use_container_width=True
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
        st.dataframe(prediction_input, use_container_width=True)

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

        error_margin = 1.96 * residual_std

        lower_bound = max(0, predicted_marks - error_margin)
        upper_bound = min(100, predicted_marks + error_margin)

        predicted_marks = max(0, min(100, predicted_marks))

        st.subheader("Predicted Marks")

        st.metric(
            "Estimated Marks",
            f"{predicted_marks:.2f} / 100"
        )

        st.write(
            f"Expected Range: **{lower_bound:.2f} – {upper_bound:.2f}**"
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

        for _, row in grade_history_df.iterrows():
            if (
                row["max_marks"] >= lower_bound
                and row["min_marks"] <= upper_bound
            ):
                possible_grades.append(row["grade"])

        if possible_grades:
            possible_grades = list(dict.fromkeys(possible_grades))
        else:
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

        st.caption(
            "Reliability indicator based on model validation performance "
            "and historical data availability. It is not the probability "
            "that the prediction is correct."
        )
        

        coefficients = model.coef_

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
            use_container_width=True
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
            line_width=4,
            line_color="white",
            annotation_text=f"Predicted: {predicted_marks:.1f}",
            annotation_position="top"
        )

        fig.add_vline(
            x=lower_bound,
            line_width=2,
            line_color="white",
            line_dash="dash",
            annotation_text=f"Min: {lower_bound:.1f}",
            annotation_position="bottom"
        )

        fig.add_vline(
            x=upper_bound,
            line_width=2,
            line_color="white",
            line_dash="dash",
            annotation_text=f"Max: {upper_bound:.1f}",
            annotation_position="bottom"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

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
            use_container_width=True
        )

    


        st.subheader("Historical Subject Performance")
        st.dataframe(
            historical_subject_data,
            use_container_width=True
        )