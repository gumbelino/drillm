from utils import (
    get_models,
    get_provider_info,
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
surveys.remove("template")  ## removes survey "template" from progress
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
    api = model_info.api

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
            "api": api,
            "survey": survey,
            "completions": num_rows,
            "completions left": TOTAL_ITERATIONS - num_rows,
            "done": True if num_rows >= TOTAL_ITERATIONS else False,
            "last updated": get_utc_time(),
        }

        if progress_df.empty:
            progress_df = pd.DataFrame([progress_data])
        else:
            progress_df.loc[len(progress_df)] = progress_data

progress_df.to_csv(progress_file_path, index=False)

summary = (
    progress_df.groupby(["provider", "api", "model"])["completions"]
    .agg(["max", "min"])
    .sort_values(by=["provider"])
    .reset_index()
)

num_models = len(summary)
has_data = len(summary[summary["max"] > 0])
is_done = len(summary[summary["min"] >= 30])
no_data_providers = ", ".join(
    [p for p in sorted(set(summary[summary["max"] == 0].api))]
)
print("=" * 80)
print(f"Number of models: {num_models}")
print(
    f"Number of models with some data (>0 iterations for any survey): {has_data} ({round(has_data*100/num_models)}%)"
)
print(
    f"Number of models done (>=30 iterations per survey): {is_done} ({round(is_done*100/num_models)}%)"
)
print(f"APIs with models without data: {no_data_providers}")

# print model summaries
for provider in sorted(set(models.provider)):

    print(f"\n====== SUMMARY for {provider} ======")
    provider_info = get_provider_info(provider)

    summary = (
        progress_df[progress_df["provider"] == provider]
        .join(provider_info.set_index("model"), rsuffix="_r", on="model")
        .groupby(["model", "api_r", "total_estimate"])["completions"]
        .agg(["max", "min"])
        .sort_values(by=["total_estimate", "max"])
        .reset_index()
    )
    print(summary)
print("=" * 80)
