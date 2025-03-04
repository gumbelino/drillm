import os
import sys
from surveys import get_mps_data, get_policies_and_considerations
from utils import (
    check_params,
    get_model_info,
    get_or_create_output,
    get_prompts,
    append_data_to_file,
    POLICIES,
    CONSIDERATIONS,
    REASONS,
    get_provider,
    is_valid_response,
    log_execution,
    get_or_create_progress_tracker,
    print_progress,
    shuffle_p_and_c,
    update_progress,
)

import data_google
import data_openai
import data_cohere
import data_mistral
import data_ollama

import time
import pandas as pd
import random
import uuid


def get_available_llms():
    df = pd.read_csv("private/llms.csv")
    available_llms = df[df["available"] == True]
    return available_llms


# get mini publics data
mps_surveys = get_mps_data()

progress_df = get_or_create_progress_tracker(mps_surveys)

# execution constants
REASON = True

# execution numbers
num_invalid = 0  # LLM errors
num_errors = 0  # critical errors
num_success = 0  # successful runs
num_requests = 0  # LLM requests
num_iterations = 0  # record number of iterations completed

input_tokens = 0
output_tokens = 0

# track execution data on each mini-public
mps_success = {mp: 0 for mp in mps_surveys}

# execurtion params
iterations = 10
llm_provider = data_ollama
model = "llama3.2"

model_info = get_model_info(model)
provider = get_provider(model)

# testing params
subset_mps = ["3.ACP"]  # ["0.Template", "3.ACP", "6.Biobanking"]
subset_only = True

# set reproduceable seed
random.seed(1)

# record start time
start_time = time.time()

# llms = get_available_llms()
# providers = llms["provider"].drop_duplicates().tolist()

mps_exec = subset_mps if subset_only else [mp for mp in mps_surveys]

# fail if iteration count will go over completions left for current params
check_params(progress_df, provider, model, mps_exec, iterations)

print(f"\nGenerating data for: {mps_exec}")
print(f"LLM provider: {provider}")
print(f"Model: {model}")

# iterate over each mini public
for mp in mps_exec:

    print(f"\nMini-public: {mp}")

    # get policies and consideration statements
    try:
        policies, considerations, likert, q_method = get_policies_and_considerations(
            mps_surveys[mp]
        )
    except Exception as e:
        print(f"ERROR: {mp} not formatted correctly: {e}")
        break

    # create policy and consideration files if they don't exist
    p_df, c_df, r_df = get_or_create_output(mp, model, policies, considerations)

    # get X completions from the LLM API, where X is _iterations_
    for i in range(iterations):

        print(f"- iteration {i+1} of {iterations}... ", end="", flush=True)

        # generate a unique id for the completion
        completion_uid = str(uuid.uuid4())

        # shuffle policies and considerations
        rand_p, rand_c, p_indexes, c_indexes = shuffle_p_and_c(policies, considerations)

        # create policy and consideration prompts
        p_prompt, c_prompt = get_prompts(rand_p, rand_c, likert, q_method)

        # make API call
        p_ranks, c_ranks, reason, meta = llm_provider.generate_data(
            mp, p_prompt, c_prompt, completion_uid, model=model, reason=REASON
        )

        # record number of requests
        num_requests += 3 if REASON else 2

        if not is_valid_response(
            c_ranks, p_ranks, considerations, policies, likert, q_method
        ):
            num_invalid += 1
            continue

        # sort ranks based on original order
        p_ranks = [x for _, x in sorted(zip(p_indexes, p_ranks))]
        c_ranks = [x for _, x in sorted(zip(c_indexes, c_ranks))]

        # create output dataframes
        p_df.loc[0] = [completion_uid] + meta + p_ranks
        c_df.loc[0] = [completion_uid] + meta + c_ranks
        r_df.loc[0] = [completion_uid] + meta + [reason]

        # read costs
        input_tokens += meta[3]
        output_tokens += meta[4]

        # append data to files
        print(f"SUCCESS.")
        append_data_to_file(mp, model, p_df, POLICIES)
        append_data_to_file(mp, model, c_df, CONSIDERATIONS)
        append_data_to_file(mp, model, r_df, REASONS)

        # save progress to file
        # note: progress_df passed by reference, so values here are updated too
        update_progress(progress_df, provider, model, mp)

        num_success += 1
        mps_success[mp] += 1

        time.sleep(2)


end_time = time.time()

elapsed_time = end_time - start_time
num_completions = num_success + num_invalid
time_per_completion = elapsed_time / num_completions
success_rate = int(num_success * 100 / num_completions)
cost_input = (input_tokens / 1000000) * model_info["price_1M_input"]
cost_output = (output_tokens / 1000000) * model_info["price_1M_output"]

print(f"\n=============== S U M M A R Y ===============")
print(f"Execution complete for {provider}/{model}")
print(f"Mini-publics (MP): {len(mps_exec)}")
print(f"Iterations per MP: {iterations}")
print(f"Total LLM completions: {num_completions}")
print(f"Total LLM requests: {num_requests}")

print(f"Cost input: US${cost_input:.2f}")
print(f"Cost output: US${cost_output:.2f}")
print(f"Total cost: US${cost_input + cost_output:.2f}")

print(f"Invalid LLM completions: {num_invalid}")
print(f"Success rate: {success_rate}%")
et_summary = elapsed_time if elapsed_time < 60 else elapsed_time / 60
et_summary_unit = "s" if elapsed_time < 60 else "min"
print(f"Elapsed time: {et_summary:.2f}{et_summary_unit}")
print(f"Average time per completion: {time_per_completion:.2f}s")
print(f"=============================================\n")

log_execution(
    provider,
    model,
    iterations,
    num_requests,
    num_completions,
    elapsed_time,
    num_invalid,
    success_rate,
    time_per_completion,
    cost_input,
    cost_output,
    mps_exec,
    mps_success,
)
