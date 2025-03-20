from datetime import timezone, datetime
import os
import pandas as pd
import random
import sys
import numpy as np

TOTAL_ITERATIONS = 100
LLM_INFO = "private/llms_v2.csv"
OUTPUT_DIR = "llm_data"
PROGRESS_FILE = "progress.csv"
META_DATA = [
    "cuid",
    "created_at",
    "provider",
    "model",
    "temperature",
    "input_tokens",
    "output_tokens",
]

POLICIES = "policies"
CONSIDERATIONS = "considerations"
REASONS = "reasons"

# https://ai.google.dev/gemini-api/docs/prompting-intro

# generic considerations prompt
PROMPT_C = """## Instructions:
- Rate each of the {0} [Considerations] below from 1 to {1}, where 1 is strongly \
disagree and {1} is strongly agree.{2}
- In your response, return an ordered list of {0} ratings as integers, one rating \
per line following the format in the [Example output].
- Your response must have exactly {0} lines in total.
- Do NOT include any additional text in your response.

## [Example output]:
1. 1
2. 4
3. 6
4. 3

## [Considerations]:
"""

PROMPT_C_V2 = """## Instructions:
- Rate each consideration below from 1 to {0}, where 1 is strongly disagree and {0} is strongly agree.
- In your response, return a single rating in your responses as an integer.
- Do NOT include any additional information or formatting, such as bullets or periods.
"""

SYSTEM_PROMPT_C = """You will be presented with {0} considerations. Rate each consideration from 1 to {1}, where 1 is strongly disagree and {1} is strongly agree. Do not include any additional formatting, such as bullets or periods."""

# generic policy preferences prompt
PROMPT_P = """## Instructions:
- Based on your previous ratings, rank the {0} [Policies] listed below from 1 to {0}, \
where 1 represents the option you support the most and {0} the option you support the least.
- In your response, return an ordered list of {0} ranks as integers, one rank per line \
following the format in the [Example output].
- Your response must have exactly {0} lines in total.
- Do NOT include any additional text in your response.

## [Example output]:
1. 4
2. 1
3. 3
4. 2

## [Policies]:
"""

PROMPT_R = """## Instructions:
- In a single line, explain your ratings above within 100 characters or less.
- Do not include any additional formatting, such as bullets or special characters.
- Do not include more than one space in a row.
"""

# Rate the considerations using a ranked based sort choice sorting process.
Q_METHOD_INSTRUCTION = """
- Using the Q Methodology, rate the statements following a Fixed Quasi-Normal Distribution between 1 and {0}."""


def get_model_info(model):
    df = pd.read_csv(LLM_INFO)
    model_data = df[df["model"] == model].to_dict(orient="records")
    if model_data:
        return model_data[0]
    else:
        raise ValueError(f"Model {model} not found in {LLM_INFO}")


def get_provider(model):
    model_info = get_model_info(model)
    return model_info["provider"]


def update_progress(progress_df, provider, model, survey):
    progress_file_path = os.path.join(OUTPUT_DIR, PROGRESS_FILE)

    if not os.path.exists(progress_file_path):
        print("Progress file does not exist.")
        return

    df = progress_df

    # Find the row that matches the provider, model, and survey
    mask = (
        (df["provider"] == provider) & (df["model"] == model) & (df["survey"] == survey)
    )
    if not mask.any():
        print(
            f"No matching entry found in progress file for {provider}/{model}/{survey}. Appending a new row."
        )

        new_row = {
            "provider": provider,
            "model": model,
            "survey": survey,
            "completions": 1,
            "completions left": TOTAL_ITERATIONS - 1,
            "done": False,
            "last updated": get_utc_time(),
        }

        df.loc[len(df)] = new_row

    else:
        # Increment the completions and update the completions left
        df.loc[mask, "completions"] += 1
        df.loc[mask, "completions left"] -= 1
        df.loc[mask, "done"] = df.loc[mask, "completions left"] == 0
        df.loc[mask, "last updated"] = get_utc_time()

    # Save the updated dataframe back to the CSV file
    df.to_csv(progress_file_path, index=False)


def append_data_to_file(survey, model, new_df, data_type):

    # get model provider
    provider = get_provider(model)

    # crete {OUTPUTDIR}/{provider}/{model} string
    output_path = os.path.join(OUTPUT_DIR, provider, model, survey)

    output_file_name = f"{data_type}.csv"
    output_file_path = os.path.join(output_path, output_file_name)

    # append data to file
    new_df.to_csv(output_file_path, mode="a", header=False, index=False)


def get_or_create_single_output(survey, model, columns, data_type):

    # get model provider
    provider = get_provider(model)

    # create {OUTPUTDIR}/{provider}/{model} string
    output_path = os.path.join(OUTPUT_DIR, provider, model, survey)

    # create output directory if it doesn't exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # create output file
    output_file_name = f"{data_type}.csv"
    output_file_path = os.path.join(output_path, output_file_name)

    # prefix columns based on data_type
    if data_type == POLICIES:
        columns = [f"P{i+1}. {col}" for i, col in enumerate(columns)]
    elif data_type == CONSIDERATIONS:
        columns = [f"C{i+1}. {col}" for i, col in enumerate(columns)]

    # create file if it doesn't exist
    if not os.path.exists(output_file_path):
        print(f"Creating output file: {output_file_path}")
        pd.DataFrame([], columns=META_DATA + columns).to_csv(
            output_file_path, index=False
        )

    # return existing data
    return pd.read_csv(output_file_path, nrows=0)


def get_or_create_output(survey, model, policies, considerations):

    # get empty dataframes
    p_df = get_or_create_single_output(survey, model, policies, POLICIES)
    c_df = get_or_create_single_output(survey, model, considerations, CONSIDERATIONS)
    r_df = get_or_create_single_output(survey, model, ["reason"], REASONS)

    return p_df, c_df, r_df


def format_statements(items):
    return "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])


def parse_numbers_from_string(number_string: str):

    # in case of deepseek-r1, remove the think tag
    number_string = number_string.split("</think>")[-1].strip()

    try:
        num_list = [int(num) for num in number_string.split()]
    except ValueError:

        # Extract numbers from the string

        num_list = []
    return num_list


def log_request(
    cuid,
    date,
    provider,
    model,
    temperature,
    survey,
    type,
    prompt,
    response,
    input_tokens=0,
    output_tokens=0,
    model_version=None,
):
    log_file_path = os.path.join(OUTPUT_DIR, provider, model, "request_log.csv")
    log_data = {
        "cuid": cuid,
        "date": date,
        "provider": provider,
        "model": model_version if model_version else model,
        "temperature": temperature,
        "survey": survey,
        "type": type,
        "prompt": prompt,
        "response": response,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
    log_df = pd.DataFrame([log_data])

    if os.path.isfile(log_file_path):
        log_df.to_csv(log_file_path, mode="a", header=False, index=False)
    else:
        log_df.to_csv(log_file_path, mode="w", header=True, index=False)


def log_execution(
    provider,
    model,
    temperature,
    iterations,
    num_requests,
    num_completions,
    elapsed_time,
    num_errors,
    num_invalid,
    success_rate,
    time_per_completion,
    cost_input,
    cost_output,
    surveys_exec,
    surveys_success,
):
    log_file_path = os.path.join(OUTPUT_DIR, "exec_log.csv")
    log_data = {
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "num surveys": len(surveys_exec),
        "num iterations": iterations,
        "num completions": num_completions,
        "num requests": num_requests,
        "input cost ($)": round(cost_input, 2),
        "output cost ($)": round(cost_output, 2),
        "total cost ($)": round(cost_input + cost_output, 2),
        "num errors": num_errors,
        "num fail completions": num_invalid,
        "num success completions": sum([surveys_success[s] for s in surveys_success]),
        "success rate (%)": round(success_rate, 2),
        "total elapsed time (min)": round(elapsed_time / 60, 2),
        "time per completion (s)": round(time_per_completion, 2),
    }

    log_df = pd.DataFrame([log_data])

    # append survey data to data frame, make it a percentage
    for s in surveys_success:
        column_name = s + " success rate (%)"
        if s in surveys_exec:
            row_value = int(surveys_success[s] * 100 / iterations)
        else:
            row_value = ""
        log_df[column_name] = row_value

    if os.path.isfile(log_file_path):
        log_df.to_csv(log_file_path, mode="a", header=False, index=False)
    else:
        log_df.to_csv(log_file_path, mode="w", header=True, index=False)


def parse_numbers_from_response(response: str):

    # print(response)

    # in case of deepseek-r1, remove the think tag
    response = response.split("</think>")[-1].strip()

    # remove spaces and split response line by line
    lines = response.replace(" ", "").split("\n")

    num_list = []

    # remove characters before a period in each string in lines
    lines = [line.split(".")[-1] for line in lines]

    # print(lines)

    # filter lines that contain integers
    num_list = [int(line) for line in lines if line.isdigit()]

    # print(num_list)

    return num_list


def shuffle_p_and_c(policies, considerations):

    policy_indexes = list(range(len(policies)))
    consideration_indexes = list(range(len(considerations)))

    random.shuffle(policy_indexes)
    random.shuffle(consideration_indexes)

    shuffled_policies = [policies[i] for i in policy_indexes]
    shuffled_considerations = [considerations[i] for i in consideration_indexes]

    return (
        shuffled_policies,
        shuffled_considerations,
        policy_indexes,
        consideration_indexes,
    )


def parse_reasoning_from_response(response: str):

    reason_text = response.strip()
    reason_text = " ".join(reason_text.split())
    reason_text = reason_text.split("</think>")[-1].strip()

    return reason_text


def get_prompts(policies, considerations, likert, q_method):

    q_instr = Q_METHOD_INSTRUCTION.format(likert) if q_method else ""

    prompt_p = (PROMPT_P.format(len(policies))) + format_statements(policies)
    prompt_c = (
        PROMPT_C.format(len(considerations), likert, q_instr)
    ) + format_statements(considerations)
    return prompt_p, prompt_c


# FIXME: need to update this function to read all files from all
def get_or_create_progress_tracker(survey_names):

    # create progress tracker file
    progress_file_path = os.path.join(OUTPUT_DIR, PROGRESS_FILE)

    # return progress if it exists
    if os.path.exists(progress_file_path):
        return pd.read_csv(progress_file_path)

    # create output directory if it doesn't exist
    progress_dir = os.path.dirname(progress_file_path)
    if not os.path.exists(progress_dir):
        os.makedirs(progress_dir)

    sys.stdout.write("Updating data generation progress...")
    sys.stdout.flush()
    df = pd.read_csv(LLM_INFO)
    for _, row in df.iterrows():
        provider = row["provider"]
        model = row["model"]
        for survey in survey_names:
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
            progress_df = pd.DataFrame([progress_data])

            if os.path.isfile(progress_file_path):
                progress_df.to_csv(
                    progress_file_path, mode="a", header=False, index=False
                )
            else:
                progress_df.to_csv(
                    progress_file_path, mode="w", header=True, index=False
                )
    sys.stdout.write(" DONE.\n")
    sys.stdout.flush()

    return pd.read_csv(progress_file_path)


def get_utc_time():
    return datetime.now(timezone.utc)


def print_progress():
    progress_file_path = os.path.join(OUTPUT_DIR, PROGRESS_FILE)

    if not os.path.exists(progress_file_path):
        print("Summary file does not exist.")
        return

    df = pd.read_csv(progress_file_path)

    partial = df[df["completions"] > 0].drop_duplicates(subset=["model", "mini-public"])

    not_done = df[df["done"] == False].drop_duplicates(subset=["model", "mini-public"])

    if not_done.empty:
        print("All providers and models are done.")
    else:
        print("Providers and models not done:")
        for i, row in not_done.iterrows():
            print(
                f"\t{int((i/3)+1)}. {row['provider']}/{row['model']} - {row["mini-public"]}"
            )

    if not partial.empty:
        print("\nPartially done:")
        for i, row in partial.iterrows():
            print(
                f"\t{int((i/3)+1)}. {row['provider']}/{row['model']} - {row["mini-public"]}"
            )


def check_params(progress_df, provider, model, surveys_exec, iterations):
    selection = progress_df[
        (progress_df["provider"] == provider)
        & (progress_df["model"] == model)
        & (progress_df["survey"].isin(surveys_exec))
        & (progress_df["completions left"] < iterations)
    ]

    if selection.any(axis=None):
        print(
            f"WARNING: iterations value ({iterations}) is too high for this selection of provider/model ({provider}/{model}) and surveys {surveys_exec}:"
        )

        print(selection)
        print(
            f"Lower the value of iterations or see {OUTPUT_DIR}/{PROGRESS_FILE} for alternative models or surveys."
        )
        exit(-1)


def is_valid_response(c_ranks, p_ranks, considerations, policies, likert, q_method):
    # check if data is valid -- this is a common issue
    if len(c_ranks) != len(considerations):
        print(
            f"ERROR: Considerations length mismatch ({len(c_ranks)}/{len(considerations)})."
        )
        return False

    # check if data is valid -- this is a common issue
    if len(p_ranks) != len(policies):
        print(f"ERROR: Policies length mismatch ({len(p_ranks)}/{len(policies)}).")
        return False

    # check if c_ranks contains values greater than likert
    if any(rank > likert or rank < 1 for rank in c_ranks):
        print(f"ERROR: Consideration ranks contain invalid values.")
        return False

    # check if p_ranks contains values greater than the length of p_ranks
    if any(rank > len(p_ranks) or rank < 1 for rank in p_ranks):
        print(f"ERROR: Policy ranks contain invalid values.")
        return False

    # check if p_ranks has duplicate values
    if len(p_ranks) != len(set(p_ranks)):
        print(f"ERROR: Policy ranks contains duplicate values.")
        return False

    # check for normality
    if q_method and not quasi_normality_check(c_ranks):
        print(f"ERROR: Considerations do not follow a Fixed Quasi-Normal Distribution.")
        return False

    return True


def quasi_normality_check(ratings):
    """
    Checks if ratings approximate a Fixed Quasi-Normal Distribution.

    Args:
      ratings: A list or array of numerical ratings.

    Returns:
      True if the data exhibits characteristics suggestive of
      a Quasi-Normal Distribution, False otherwise.
    """

    mean = np.mean(ratings)
    median = np.median(ratings)
    percentile_25 = np.percentile(ratings, 25)
    percentile_75 = np.percentile(ratings, 75)
    iqr = percentile_75 - percentile_25

    # Define rough criteria (adjust as needed)
    is_quasi_normal = abs(mean - median) < 10 and iqr < 30

    return is_quasi_normal
