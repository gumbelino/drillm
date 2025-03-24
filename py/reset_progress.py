from utils import (
    get_models,
    get_utc_time,
    OUTPUT_DIR,
    PROGRESS_FILE,
    POLICIES,
    TOTAL_ITERATIONS,
)
from surveys import get_survey_names
import os
import pandas as pd

# get surveys data
surveys = get_survey_names()
surveys.remove("template")
models = get_models()

progress_file_path = os.path.join(OUTPUT_DIR, PROGRESS_FILE)
progress_df = pd.DataFrame()

# create output directory if it doesn't exist
progress_dir = os.path.dirname(progress_file_path)
if not os.path.exists(progress_dir):
    os.makedirs(progress_dir)


for _, model_info in models.sort_values("model").iterrows():

    provider = model_info.provider
    model = model_info.model

    for survey in surveys:

        # check only policies file, assume all are the same length
        policy_file = f"{POLICIES}.csv"
        file_path = os.path.join(OUTPUT_DIR, provider, model, survey, policy_file)

        if os.path.exists(file_path):
            s_df = pd.read_csv(file_path)
            num_rows = len(s_df)
        else:
            num_rows = 0

        progress_data = {
            "provider": provider,
            "model": model,
            "survey": survey,
            "completions": num_rows,
            "completions left": TOTAL_ITERATIONS - num_rows,
            "done": True if num_rows == TOTAL_ITERATIONS else False,
            "last updated": get_utc_time(),
        }

        if progress_df.empty:
            progress_df = pd.DataFrame([progress_data])
        else:
            progress_df.loc[len(progress_df)] = progress_data

progress_df.to_csv(progress_file_path, index=False)

progress_df = progress_df[progress_df["completions"] > 0]
progress_df = progress_df.sort_values("completions")

summary = (
    progress_df.groupby(["provider", "model"])["completions"]
    .sum()
    .sort_values(ascending=False)
)

print(summary)
