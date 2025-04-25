import argparse
import math
from utils import (
    get_current_time,
    get_model_info,
    get_models,
    get_provider_info,
    get_utc_time,
    OUTPUT_DIR,
    PROGRESS_FILE,
    POLICIES,
)
from surveys import get_survey_names
import os
import pandas as pd

# get surveys data
surveys = get_survey_names(no_template=True)
models = get_models(include_all=True)


def reset_progress(quiet=False, temperature=0):

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

        min_iterations = model_info.min_iterations

        for survey in surveys:

            # check only policies file, assume all are the same length
            policy_file = f"{POLICIES}.csv"
            file_path = os.path.join(OUTPUT_DIR, provider, model, survey, policy_file)

            if os.path.exists(file_path):
                s_df = pd.read_csv(file_path)

                # make sure to check for temp == 0
                s_df = s_df[s_df["temperature"] == temperature]

                num_rows = len(s_df)
                last_updated = s_df["created_at"].max()
            else:
                num_rows = 0
                last_updated = get_utc_time()

            progress_data = {
                "provider": provider,
                "model": model,
                "api": api,
                "survey": survey,
                "completions": num_rows,
                "min_iterations": min_iterations,
                "completions_left": min_iterations - num_rows,
                "done": True if num_rows >= min_iterations else False,
                "last_updated": last_updated,
            }

            if progress_df.empty:
                progress_df = pd.DataFrame([progress_data])
            else:
                progress_df.loc[len(progress_df)] = progress_data

    progress_df.to_csv(progress_file_path, index=False)

    if quiet:
        return progress_df

    summary = (
        progress_df.groupby(["provider", "api", "model", "done"])["completions"]
        .agg(["max", "min"])
        .sort_values(by=["provider"])
        .reset_index()
    )

    num_models = len(summary)
    has_data = len(summary[summary["max"] > 0])
    is_done = len(summary[summary["done"] == True])
    no_data_providers = ", ".join(
        [p for p in sorted(set(summary[summary["max"] == 0].api))]
    )
    print("=" * 80)
    print(f"Number of models: {num_models}")
    print(
        f"Number of models with some data (>0 iterations for any survey): {has_data} ({round(has_data*100/num_models)}%)"
    )
    print(
        f"Number of models done (>=min_iterations per survey): {is_done} ({round(is_done*100/num_models)}%)"
    )
    print(f"APIs with models without data: {no_data_providers}")

    # print model summaries
    for provider in sorted(set(models.provider)):

        print(f"\n====== SUMMARY for {provider} ======")
        provider_info = get_provider_info(provider)

        summary = (
            progress_df[progress_df["provider"] == provider]
            .join(provider_info.set_index("model"), rsuffix="_r", on="model")
            .groupby(["model", "api_r", "total_estimate", "min_iterations"])[
                "completions"
            ]
            .agg(["max", "min", "sum"])
            .sort_values(by=["min", "total_estimate"])
            .reset_index()
        )

        summary["left"] = summary["min_iterations"] - summary["min"]
        summary["left"] = ["DONE" if x <= 0 else f"{x}" for x in summary["left"]]

        summary["prog"] = (
            summary["sum"] * 100 / (summary["min_iterations"] * len(surveys))
        )

        summary["prog"] = [
            "-" if x["left"] == "DONE" else f"{int(x["prog"])}%"
            for _, x in summary.iterrows()
        ]

        summary["cost_left"] = [
            (
                "-"
                if x["left"] == "DONE"
                else f"{round((x["total_estimate"] / x["min_iterations"]) * int(x["left"]), 2)} USD"
            )
            for _, x in summary.iterrows()
        ]

        summary["total_estimate"] = [
            f"{round(x, 2)} USD" for x in summary["total_estimate"]
        ]

        summary["python_cmd"] = [
            "-" if x["left"] == "DONE" else f"{x["model"]} {x["left"]}"
            for _, x in summary.iterrows()
        ]

        # exclude done models
        summary = summary[summary["left"] != "DONE"]

        if summary.empty:
            print(f"DONE!")
            continue

        print(summary)
    print("=" * 80)


def print_model_summary(model, progress_df):

    model_info = get_model_info(model)

    print(f"\n====== SUMMARY for {model_info["provider"]}/{model} ======")

    summary = (
        progress_df[progress_df["model"] == model]
        .sort_values(by=["completions"])
        .reset_index()
    )

    summary["left"] = [f"{x}" if x > 0 else "DONE" for x in summary["completions_left"]]

    total_estimate = model_info["total_estimate"]
    left = sum([int(x) if x.isdigit() else 0 for x in summary.left])
    ratio = left / model_info["min_iterations"]

    print(f"API: {model_info["api"]}")
    print(
        f"Estimate total cost left: {total_estimate*ratio:.2} USD out of {total_estimate} USD"
    )

    print(f"Comment: {model_info["comment"]}\n")

    summary["python_cmd"] = [
        "-" if x["left"] == "DONE" else f"{model} {x["left"]} --survey {x["survey"]}"
        for _, x in summary.iterrows()
    ]

    print(summary[["survey", "completions", "left", "python_cmd"]])


def main():
    parser = argparse.ArgumentParser(
        description="A script that generates data based on command-line arguments."
    )

    # Define expected command-line arguments
    parser.add_argument(
        "--model",
        type=str,
        required=False,
        default=None,
        help="model name",
    )
    parser.add_argument(
        "--temp", type=float, required=False, default=0, help="temperature"
    )

    # Parse the arguments
    args = parser.parse_args()

    if args.model:
        progress_df = reset_progress(quiet=True, temperature=args.temp)
        print_model_summary(args.model, progress_df)

    else:
        reset_progress(temperature=args.temp)


if __name__ == "__main__":
    main()
