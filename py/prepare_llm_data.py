import pandas as pd
import os


def get_models(file_path="private/llms_v2.csv"):
    # Read the CSV file
    df = pd.read_csv(file_path)

    # Initialize the has_data column
    df["has_data"] = False

    # Check if the path exists for each provider and model
    for index, row in df.iterrows():
        provider = row["provider"]
        model = row["model"]
        path = f"llm_data/{provider}/{model}"
        if os.path.exists(path):
            df.at[index, "has_data"] = True

    return df[["provider", "model", "has_data"]]


def get_models_with_data(file_path="private/llms_v2.csv"):
    df = get_models(file_path)
    df = df[df["has_data"] == True]
    return list(df[["provider", "model"]].itertuples(index=False, name=None))


def get_survey_names(file_path="data/surveys_v2.xlsx"):
    # Load the Excel file
    excel_file = pd.ExcelFile(file_path)

    # Return the sheet names
    return excel_file.sheet_names


def get_data_file_name(provider, model, survey, file_type):
    return f"llm_data/{provider}/{model}/{survey}_{file_type}.csv"


surveys = get_survey_names()
providers_models = get_models_with_data()
file_types = ["considerations", "policies", "reasons"]


for survey in surveys:
    for provider, model in providers_models:
        for file_type in file_types:
            file_name = get_data_file_name(provider, model, survey, file_type)
            if os.path.exists(file_name):

                df = pd.read_csv(file_name)

                if file_type == "considerations":
                    # Generate new column names
                    new_columns = {f"C{i}": f"C{i}" for i in range(1, 51)}

                    # Replace column names starting at index 6
                    df.columns.values[6 : 6 + len(new_columns)] = list(
                        new_columns.values()
                    )

                    # Fill out values with NAs if necessary
                    df = df.reindex(
                        columns=list(df.columns[:6]) + list(new_columns.values()),
                        fill_value=pd.NA,
                    )

                    print(df)
