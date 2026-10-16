if page == "Individual Subject Prediction":

    st.title("Individual Subject Prediction")

    if role == "admin":
        student_ids = students_df["student_id"].tolist()

        if not student_ids:
            st.warning("No students are available.")
            st.stop()

        selected_student = st.selectbox(
            "Select Student",
            student_ids,
            key="individual_prediction_student"
        )
    else:
        # Students can only predict for their own account.
        selected_student = st.session_state["user"]["student_id"]

    student_info_df = students_df[
        students_df["student_id"] == selected_student
    ]

    if student_info_df.empty:
        st.error("Student information could not be found.")
        st.stop()

    student_info = student_info_df.iloc[0]
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

    if current_semester_df.empty:
        st.warning("No academic records were found for this student.")
        st.stop()

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

    if subjects_df.empty:
        st.warning("No subjects were found for this student's current semester.")
        st.stop()

    subject_options = subjects_df["subject_code"].tolist()
    selected_subject = st.selectbox(
        "Select Subject",
        subject_options,
        format_func=lambda code: (
            f"{code} — "
            f"{subjects_df.loc[subjects_df['subject_code'] == code, 'subject_name'].iloc[0]}"
        ),
        key=f"individual_prediction_subject_{selected_student}"
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

    if subject_data.empty:
        default_data = {}
        st.info(
            "No saved assessment inputs were found. Enter the current marks "
            "below to generate a prediction."
        )
    else:
        default_data = subject_data.iloc[0].to_dict()

    def get_default(column, fallback=0.0):
        value = default_data.get(column, fallback)
        return fallback if pd.isna(value) else float(value)

    # Widget keys include student and subject so values from one prediction
    # cannot accidentally carry over to another student's subject.
    with st.form(f"individual_subject_form_{selected_student}_{selected_subject}"):
        st.subheader("Enter or Review Assessment Inputs")

        quiz1 = st.number_input(
            "Quiz 1 Marks", min_value=0.0, max_value=100.0,
            value=get_default("quiz1"),
            key=f"quiz1_{selected_student}_{selected_subject}"
        )
        quiz2 = st.number_input(
            "Quiz 2 Marks", min_value=0.0, max_value=100.0,
            value=get_default("quiz2"),
            key=f"quiz2_{selected_student}_{selected_subject}"
        )
        midsem = st.number_input(
            "Midsem Marks", min_value=0.0, max_value=100.0,
            value=get_default("midsem"),
            key=f"midsem_{selected_student}_{selected_subject}"
        )
        assignment = st.number_input(
            "Assignment Marks", min_value=0.0, max_value=100.0,
            value=get_default("assignment"),
            key=f"assignment_{selected_student}_{selected_subject}"
        )
        attendance = st.number_input(
            "Attendance (%)", min_value=0.0, max_value=100.0,
            value=get_default("attendance_percentage"),
            key=f"attendance_{selected_student}_{selected_subject}"
        )

        predict_clicked = st.form_submit_button(
            "Predict Subject Marks",
            type="primary"
        )

    prev_sga = get_default("prev_sga")
    prev_sem_percentage = get_default("prev_sem_percentage")
    prev_total_backlogs = int(get_default("prev_total_backlogs"))

    prediction_input = pd.DataFrame([{
        "subject_code": selected_subject,
        "quiz1": quiz1,
        "quiz2": quiz2,
        "midsem": midsem,
        "assignment": assignment,
        "attendance_percentage": attendance,
        "prev_sga": prev_sga,
        "prev_sem_percentage": prev_sem_percentage,
        "prev_total_backlogs": prev_total_backlogs,
        "branch": student_branch,
        "semester": student_semester
    }])

    prediction_signature = (
        role, selected_student, selected_subject, student_year,
        student_semester, float(quiz1), float(quiz2), float(midsem),
        float(assignment), float(attendance), float(prev_sga),
        float(prev_sem_percentage), int(prev_total_backlogs)
    )

    cached_prediction = st.session_state.get("individual_subject_prediction")

    if predict_clicked:
        transformed_input = preprocessor.transform(prediction_input)
        predicted_marks = predict_subject(
            selected_subject,
            quiz1,
            quiz2,
            midsem,
            assignment,
            attendance,
            prev_sga,
            prev_sem_percentage,
            prev_total_backlogs
        )
        predicted_marks = float(np.asarray(predicted_marks).reshape(-1)[0])
        predicted_marks = max(0.0, min(100.0, predicted_marks))
        prediction_lower = max(0.0, predicted_marks - prediction_error)
        prediction_upper = min(100.0, predicted_marks + prediction_error)

        st.session_state["individual_subject_prediction"] = {
            "signature": prediction_signature,
            "prediction_input": prediction_input.copy(),
            "transformed_input": transformed_input,
            "predicted_marks": predicted_marks,
            "prediction_lower": prediction_lower,
            "prediction_upper": prediction_upper
        }
        cached_prediction = st.session_state["individual_subject_prediction"]

    if (
        not cached_prediction
        or cached_prediction.get("signature") != prediction_signature
    ):
        st.info(
            "Enter or review the assessment inputs, then click "
            "**Predict Subject Marks** to see the prediction and analysis."
        )
        st.stop()

    prediction_input = cached_prediction["prediction_input"].copy()
    transformed_input = cached_prediction["transformed_input"]
    predicted_marks = cached_prediction["predicted_marks"]
    prediction_lower = cached_prediction["prediction_lower"]
    prediction_upper = cached_prediction["prediction_upper"]

    if show_prediction_input:

        st.subheader("Prediction Input")

        st.dataframe(

            prediction_input,

            width="stretch",

            hide_index=True

        )

    # ---------------------------------------------------------

    # PREDICTION CONFIDENCE

    # ---------------------------------------------------------

    if show_prediction_confidence:

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

    # ---------------------------------------------------------

    # HISTORICAL GRADE DATA

    # ---------------------------------------------------------

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

        matching_grades_df = grade_history_df[

            (grade_history_df["max_marks"] >= prediction_lower)

            & (grade_history_df["min_marks"] <= prediction_upper)

        ].copy()

        if not matching_grades_df.empty:

            matching_grades_df["distance_to_prediction"] = (

                matching_grades_df["avg_marks"] - predicted_marks

            ).abs()

            matching_grades_df = matching_grades_df.sort_values(

                "distance_to_prediction"

            ).head(3)

            total_count = matching_grades_df["student_count"].sum()

            if total_count > 0:

                possible_grades = [

                    f'{row["grade"]} '

                    f'({row["student_count"] / total_count:.1%})'

                    for _, row in matching_grades_df.iterrows()

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

        historical_subject_data["grade"].notna()

        & (historical_subject_data["grade"].str.upper() != "FA")

    ].copy()

    historical_count = (

        int(grade_history_df["student_count"].sum())

        if not grade_history_df.empty

        else 0

    )

    # ---------------------------------------------------------

    # ESTIMATED GRADE AND RELIABILITY

    # ---------------------------------------------------------

    mae = float(model_metrics.get("mae", 0))

    mean_marks = float(model_metrics.get("mean_marks", 0))

    if mean_marks > 0:

        model_reliability = max(

            0.0,

            min(100.0, (1 - mae / mean_marks) * 100)

        )

    else:

        model_reliability = 0.0

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

        0.7 * model_reliability

        + 0.3 * history_reliability

    )

    prediction_reliability = max(

        0.0,

        min(100.0, prediction_reliability)

    )

    if show_estimated_grade:

        st.subheader("Estimated Grade")

        st.metric(

            "Grade Based on Historical Performance",

            estimated_grade

        )

        st.write(

            f"**Possible Historical Grades:** {' - '.join(possible_grades)}"

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

    # ---------------------------------------------------------

    # SAVE PREDICTION

    # ---------------------------------------------------------

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

    # ---------------------------------------------------------

    # FACTOR CONTRIBUTIONS

    # ---------------------------------------------------------

    if show_factor_explanation:

        st.subheader("Factors Influencing Prediction")

        estimator = model.named_steps["model"]

        if not hasattr(estimator, "coef_"):

            st.info(

                "Factor contribution charts are available for models "

                "that expose coefficients. The current model does not."

            )

        else:

            model_coefficients = np.asarray(

                estimator.coef_

            ).reshape(-1)

            feature_names = preprocessor.get_feature_names_out()

            if hasattr(transformed_input, "toarray"):

                transformed_values = transformed_input.toarray().reshape(-1)

            else:

                transformed_values = np.asarray(

                    transformed_input

                ).reshape(-1)

            if (

                len(feature_names) != len(model_coefficients)

                or len(transformed_values) != len(model_coefficients)

            ):

                st.warning(

                    "Feature contributions cannot be displayed because "

                    "the feature names, transformed input, and coefficients "

                    "do not have matching dimensions."

                )

            else:

                contributions = transformed_values * model_coefficients

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

                        label = f"Subject: {selected_subject}"

                    elif feature.startswith("cat__branch_"):

                        label = f"Branch: {selected_branch_name}"

                    elif feature in feature_labels:

                        label = feature_labels[feature]

                    else:

                        label = (

                            feature

                            .replace("num__", "")

                            .replace("cat__", "")

                        )

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

                top_explanations = (

                    explanation_df.head(10)

                    .sort_values("contribution")

                )

                fig = px.bar(

                    top_explanations,

                    x="contribution",

                    y="feature",

                    orientation="h",

                    title="Factors Influencing Predicted Marks",

                    labels={

                        "contribution": "Linear Contribution",

                        "feature": "Factor"

                    }

                )

                fig.add_vline(x=0, line_width=1)

                st.plotly_chart(

                    fig,

                    width="stretch",

                    key="individual_factor_contributions"

                )

                st.caption(

                    "Positive contributions push the linear model output upward; "

                    "negative contributions push it downward. Numeric contributions "

                    "use transformed feature values and coefficients. The model "

                    "intercept is not included in this chart."

                )

                st.subheader("Individual Factor Explanations")

                factor_descriptions = {

                    "Quiz 1": (

                        "The first quiz score. Its contribution shows the "

                        "direction and size of this input's linear term."

                    ),

                    "Quiz 2": (

                        "The second quiz score. Its contribution reflects "

                        "the learned relationship between this score and marks."

                    ),

                    "Midsem": (

                        "The mid-semester examination score. Its contribution "

                        "shows how its transformed value affects the model output."

                    ),

                    "Assignment": (

                        "The assignment score. Its contribution reflects the "

                        "relationship learned from assignment marks during training."

                    ),

                    "Attendance": (

                        "The attendance percentage supplied to the model. "

                        "Its contribution reflects the learned relationship "

                        "between attendance and marks."

                    ),

                    "Previous SGA": (

                        "The student's previous SGA, representing earlier "

                        "academic performance used as a prediction input."

                    ),

                    "Previous Semester Percentage": (

                        "The previous semester's percentage, representing "

                        "earlier academic performance."

                    ),

                    "Previous Backlogs": (

                        "The number of previous backlogs. Its contribution "

                        "reflects the relationship learned between backlog "

                        "history and marks."

                    ),

                    "Semester": (

                        "The current semester number. Its contribution reflects "

                        "the relationship learned from semester-related patterns."

                    ),

                    f"Subject: {selected_subject}": (

                        "The selected subject's encoded category. Its contribution "

                        "represents the learned subject-specific term, if present "

                        "in the model."

                    ),

                    f"Branch: {selected_branch_name}": (

                        "The student's encoded branch category. Its contribution "

                        "represents the learned branch-specific term, if present "

                        "in the model."

                    )

                }

                for _, row in explanation_df.iterrows():

                    factor = row["feature"]

                    contribution = row["contribution"]

                    description = factor_descriptions.get(

                        factor,

                        "This feature was supplied to the model during prediction. "

                        "Its contribution reflects the relationship learned during "

                        "training."

                    )

                    if contribution > 0:

                        direction = "pushes the prediction upward"

                    elif contribution < 0:

                        direction = "pushes the prediction downward"

                    else:

                        direction = "has no direct contribution for this input"

                    with st.expander(f"{factor}: {contribution:+.2f}"):

                        st.write(description)

                        st.write(

                            f"For this student, this factor {direction} "

                            f"by approximately {abs(contribution):.2f} "

                            "contribution units."

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

                    if positive_factors.empty:

                        st.info(

                            "No positive factor contributions for this input."

                        )

                    else:

                        for _, row in positive_factors.head(3).iterrows():

                            st.write(

                                f"🟢 **{row['feature']}**: "

                                f"+{row['contribution']:.2f}"

                            )

                with col2:

                    st.write("### Strongest Negative Factors")

                    if negative_factors.empty:

                        st.info(

                            "No negative factor contributions for this input."

                        )

                    else:

                        for _, row in negative_factors.head(3).iterrows():

                            st.write(

                                f"🔴 **{row['feature']}**: "

                                f"{row['contribution']:.2f}"

                            )

    # ---------------------------------------------------------

    # HISTORICAL PERFORMANCE

    # ---------------------------------------------------------

    if show_historical_metrics:

        st.subheader("Historical Performance")

        historical_df = historical_subject_data.copy()

        if historical_df.empty:

            st.info(

                "No historical performance data is available for this subject."

            )

        else:

            historical_df["marks_obtained"] = pd.to_numeric(

                historical_df["marks_obtained"],

                errors="coerce"

            )

            historical_df = historical_df.dropna(

                subset=["marks_obtained"]

            )

            if historical_df.empty:

                st.info(

                    "No valid historical marks are available for comparison."

                )

            else:

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

                        if pd.notna(grade_min_marks)

                        else "N/A"

                    )

                with col2:

                    st.metric(

                        f"{estimated_grade} Historical Maximum",

                        f"{grade_max_marks:.0f}"

                        if pd.notna(grade_max_marks)

                        else "N/A"

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

                    labels={"marks_obtained": "Marks"}

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

                    annotation_text=f"Lower: {prediction_lower:.1f}",

                    annotation_position="bottom"

                )

                fig.add_vline(

                    x=prediction_upper,

                    line_width=3,

                    line_color="#FF6B6B",

                    line_dash="dot",

                    annotation_text=f"Upper: {prediction_upper:.1f}",

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

                fig.update_xaxes(

                    range=[max(0, x_min - 2), min(100, x_max + 2)]

                )

                st.plotly_chart(

                    fig,

                    width="stretch",

                    key="historical_marks_distribution"

                )

                grade_distribution = (

                    historical_df["grade"]

                    .dropna()

                    .value_counts()

                    .reindex(

                        ["AA", "AB", "BB", "BC", "CC", "CD", "DD", "FF", "FA"],

                        fill_value=0

                    )

                    .rename_axis("grade")

                    .reset_index(name="student_count")

                )

                if not grade_distribution.empty:

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

                            "grade": [

                                "AA", "AB", "BB", "BC", "CC",

                                "CD", "DD", "FF", "FA"

                            ]

                        }

                    )

                    fig.update_layout(showlegend=False)

                    st.plotly_chart(

                        fig,

                        width="stretch",

                        key="historical_grade_distribution"

                    )

    # ---------------------------------------------------------

    # SUBJECT-WISE GRADE CUTOFFS

    # ---------------------------------------------------------

    matching_grades = []

    if show_grade_cutoffs or show_grade_ranges:

        subject_cutoffs_df = pd.read_sql(

            """

            SELECT

                grade,

                MIN(marks_obtained) AS minimum_marks,

                MAX(marks_obtained) AS maximum_marks

            FROM academic_records

            WHERE subject_code = %s

              AND grade <> 'FA'

            GROUP BY grade, grade_point

            ORDER BY grade_point DESC

            """,

            con,

            params=(selected_subject,)

        )

        if not subject_cutoffs_df.empty:

            subject_cutoffs_df["minimum_marks"] = pd.to_numeric(

                subject_cutoffs_df["minimum_marks"],

                errors="coerce"

            )

            subject_cutoffs_df["maximum_marks"] = pd.to_numeric(

                subject_cutoffs_df["maximum_marks"],

                errors="coerce"

            )

            subject_cutoffs_df = subject_cutoffs_df.dropna(

                subset=["minimum_marks", "maximum_marks"]

            )

        if show_grade_cutoffs:

            st.subheader("Subject-wise Grade Cutoffs")

            if subject_cutoffs_df.empty:

                st.info(

                    "No historical grade cutoffs are available for this subject."

                )

            else:

                st.dataframe(

                    subject_cutoffs_df.rename(columns={

                        "grade": "Grade",

                        "minimum_marks": "Minimum Historical Marks",

                        "maximum_marks": "Maximum Historical Marks"

                    }),

                    width="stretch",

                    hide_index=True

                )

    # ---------------------------------------------------------

    # PREDICTED MARKS VS HISTORICAL GRADE RANGES

    # ---------------------------------------------------------

    if show_grade_ranges:

        st.subheader("Predicted Marks vs Historical Grade Ranges")

        if subject_cutoffs_df.empty:

            st.info(

                "No historical grade ranges are available for comparison."

            )

        else:

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

                contains_prediction = (

                    minimum <= predicted_marks <= maximum

                )

                if contains_prediction:

                    matching_grades.append(grade)

                fig_comparison.add_trace(

                    go.Bar(

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

                    )

                )

            fig_comparison.add_hline(

                y=predicted_marks,

                line_color="red",

                line_width=2,

                line_dash="dash",

                annotation_text=f"Predicted marks: {predicted_marks:.2f}",

                annotation_position="top left"

            )

            fig_comparison.update_layout(

                title=(

                    "Predicted Marks vs Historical Grade Ranges — "

                    f"{selected_subject}"

                ),

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

                    f"the historical range for grade(s): "

                    f"{', '.join(matching_grades)}."

                )

            else:

                st.warning(

                    f"Predicted marks of {predicted_marks:.2f} fall outside "

                    "all observed historical grade ranges."

                )

    # ---------------------------------------------------------

    # PREDICTION SUMMARY

    # ---------------------------------------------------------

    if show_prediction_summary:

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

            historical_match = (

                ", ".join(matching_grades)

                if matching_grades

                else "Outside observed ranges"

            )

            st.metric(

                "Historical Range Match",

                historical_match

            )

    # ---------------------------------------------------------

    # PREDICTION UNCERTAINTY

    # ---------------------------------------------------------

    if show_uncertainty:

        st.subheader("Prediction Uncertainty")

        residual_std_value = float(residual_std)

        prediction_lower_uncertainty = max(

            0.0,

            predicted_marks - 1.96 * residual_std_value

        )

        prediction_upper_uncertainty = min(

            100.0,

            predicted_marks + 1.96 * residual_std_value

        )

        st.metric(

            "Approximate Prediction Range",

            f"{prediction_lower_uncertainty:.2f} – "

            f"{prediction_upper_uncertainty:.2f}"

        )

        st.caption(

            "This is an approximate range based on the model's residual "

            "standard deviation, assuming roughly normal and stable prediction "

            "errors. It is not a guaranteed interval."

        )

    # ---------------------------------------------------------

    # MODEL VALIDATION SUMMARY

    # ---------------------------------------------------------

    if show_model_validation:

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
