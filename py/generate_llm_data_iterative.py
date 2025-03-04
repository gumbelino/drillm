import os
import sys
from surveys import get_mps_data, get_policies_and_considerations
from utils import (
    get_or_create_output,
    get_prompts,
    append_data_to_file,
    POLICIES,
    CONSIDERATIONS,
    REASONS,
)

import data_google
import data_openai
import data_cohere
import data_mistral
import data_ollama
import data_ollamav2


import time
import pandas as pd


def get_available_llms():
    df = pd.read_csv("private/llms.csv")
    available_llms = df[df["available"] == True]
    return available_llms


# get mini publics data
mps_surveys = get_mps_data()

REASON = False
mismatches = 0
error = 0
iterations = 2
llm_provider = data_ollama
model = "llama3.2"


start_time = time.time()

print(get_available_llms())

# iterate over each mini public
for mp in mps_surveys:

    # get policies and consideration statements
    try:
        policies, considerations, likert, q_method = get_policies_and_considerations(
            mps_surveys[mp]
        )
    except Exception as e:
        print(f"ERROR: {mp} not formatted correctly: {e}")
        break

    # create policy and consideration files if they don't exist
    p_df, c_df, r_df = get_or_create_output(mp, policies, considerations)

    # create policy and consideration prompts
    p_prompt, c_prompt = get_prompts(policies, considerations, likert, q_method)

    # print prompts
    # print(c_prompt)
    # print(p_prompt)

    for i in range(iterations):

        print(f"\nStarting iteration {i+1} for {mp} mini-public.")

        # try to make API call
        # try:
        p_ranks, c_ranks, reason, meta = llm_provider.generate_data(
            p_prompt, considerations, model=model, reason=REASON
        )
        # except Exception as e:
        #     print(f"ERROR: Error getting LLM data: {e}")
        #     # exc_type, exc_obj, exc_tb = sys.exc_info()
        #     # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        #     # print(exc_type, fname, exc_tb.tb_lineno)
        #     error += 1
        #     continue

        # print(c_ranks)

        # check if data is valid -- this is a common issue
        if len(c_ranks) != len(considerations):
            print(
                f"ERROR: Considerations length mismatch ({len(c_ranks)}/{len(considerations)}). Continue."
            )
            mismatches += 1
            continue

        # check if data is valid -- this is a common issue
        if len(p_ranks) != len(policies):
            print(
                f"ERROR: Policies length mismatch ({len(p_ranks)}/{len(policies)}). Continue."
            )
            mismatches += 1
            continue

        # create output dataframes
        p_df.loc[0] = meta + p_ranks
        c_df.loc[0] = meta + c_ranks
        r_df.loc[0] = meta + [reason]

        # append data to files
        print(f"SUCCESS: Appending data to files.")
        append_data_to_file(mp, p_df, POLICIES)
        append_data_to_file(mp, c_df, CONSIDERATIONS)
        append_data_to_file(mp, r_df, REASONS)

        time.sleep(2)

    # only do 1 minipublic for now
    break

end_time = time.time()
fail = error + mismatches

print(f"\n===============================")
print(f"Data generation complete.")
print(f"Iterations: {iterations}")
print(f"Length mismatches: {mismatches}")
print(f"Errors: {error}")
print(f"Time per request: {int((end_time - start_time) / iterations)}s")
print(f"SUCCESS: {iterations - fail} | FAIL: {fail}")
print(f"===============================\n")
