import pandas as pd


def validate_data(input_file, output_file):

    # Load the data into a DataFrame
    df = pd.read_csv(input_file)

    # Define the columns to check for U columns
    c_columns = [f"U{i:02d}" for i in range(1, 51)]

    # Define the columns to check
    # c_columns = [f"F{i}" for i in range(1, 51)]
    p_columns = [f"Pref{i}" for i in range(1, 11)]

    LMIN = "Likert min"
    LMAX = "Likert max"
    NC = "number of considerations"
    NP = "N_preference"

    # Convert values in c_columns and p_columns to int if value is integer and whole
    for col in c_columns + p_columns:
        df[col] = df[col].apply(
            lambda x: int(x) if pd.notna(x) and float(x).is_integer() else x
        )

    # Function to check if a row is valid
    def is_valid_row(row):

        # Get column values
        cons = row[c_columns].dropna()
        prefs = row[p_columns].dropna()

        study = row["Study"]

        # Load the study-survey mapping
        survey_map = pd.read_csv("data/studies_survey_map.csv")

        # Get the matching survey for the current study
        try:
            survey = survey_map[survey_map["Study"] == study]["Survey"].values[0]
        except:
            return False, ["no matching survey data"]

        # Load the guideline survey data
        guideline_survey = pd.read_excel("data/guideline_survey.xlsx")

        # Get the matching row for the current survey
        guideline_row = guideline_survey[guideline_survey["Study"] == survey]

        # Extract the values for LMIN, LMAX, NC, and NP
        try:
            lmin = guideline_row[LMIN].values[0]
            lmax = guideline_row[LMAX].values[0]
            nc = guideline_row[NC].values[0]
            np = guideline_row[NP].values[0]
        except:
            print(study)
            return False, [f"{study} has incomplete data"]

        is_valid = True
        reasons = []

        # Check for fractional values in considerations
        if any(not float(x).is_integer() for x in cons):
            is_valid = False
            reasons += ["fractional values in considerations"]

        # Check for fractional values in preferences
        if any(not float(x).is_integer() for x in prefs):
            is_valid = False
            reasons += ["fractional values in preferences"]

        # check considerations
        if len(cons) != nc:
            is_valid = False
            reasons += [f"incomplete considerations rating ({len(cons)} out of {nc})"]

        if any(cons < lmin) or any(cons > lmax):
            cmin = int(min(cons))
            cmax = int(max(cons))
            is_valid = False
            reasons += [
                f"invalid consideration value [{lmin}, {lmax}] - [{cmin}, {cmax}]"
            ]

        # check preferences
        if len(prefs) != np:
            is_valid = False
            reasons += [f"incomplete preferences ranking ({len(prefs)} out of {np})"]

        if len(prefs) != len(set(prefs)):
            is_valid = False
            reasons += ["duplicate preferences"]

        if any(val > len(prefs) or val < 1 for val in prefs):
            is_valid = False
            reasons += [f"invalid preference value [1, {len(prefs)}]"]

        return is_valid, reasons

    # Iterate over rows and count invalid rows
    invalid_row_count = 0
    for index, row in df.iterrows():
        is_valid, reasons = is_valid_row(row)
        reason_str = "; ".join(reasons)
        df.at[index, "InvalidReason"] = reason_str

        if not is_valid:
            print(
                f"Invalid row at index {index}: {row[p_columns].values}: {reason_str}"
            )
            invalid_row_count += 1

    print(f"Number of invalid rows: {invalid_row_count}")

    # Save the valid rows to a new CSV file
    df.to_csv(output_file, index=False)


# Usage
# validate_data("data/Data1_Raw_Input_SIMON.csv", "data/clean_data.csv")
validate_data("data/total dataset_clean.csv", "data/clean_clean_data.csv")

# def validate_data(input_file, output_file):
#     # Load the data into a DataFrame
#     df = pd.read_csv(input_file)

#     # Define the columns to check
#     pref_columns = [f"Pref{i}" for i in range(1, 11)]

#     # Function to check if a row is valid
#     def is_valid_row(row):
#         values = row[pref_columns].dropna().astype(int)
#         return len(values) == len(set(values)) and all(
#             1 <= val <= len(values) for val in values
#         )

#     # Filter the valid rows
#     valid_rows = df[df.apply(is_valid_row, axis=1)]

#     # Save the valid rows to a new CSV file
#     valid_rows.to_csv(output_file, index=False)


# # Usage
# validate_data("data/Data1_Raw_Input_SIMON.csv", "data/clean_data.csv")
