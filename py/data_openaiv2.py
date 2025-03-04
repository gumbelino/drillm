import csv
from openai import OpenAI
import pandas as pd
import surveys
import uuid
import utils
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def completion_with_backoff(**kwargs):
    return client.completions.create(**kwargs)


# define openai client to access API
client = OpenAI(
    organization="org-5vaJcJj36BER6kXQMdkKKpZP",
    project="proj_k8Gv8E3GjDirposW9zEqvdfq",
)

PROVIDER = "openai"

# deprecated: API_KEYS live in local file
# API_KEYS_FILE_PATH = "private/api_keys.csv"


# more about roles: https://platform.openai.com/docs/guides/text-generation#messages-and-roles
def get_llm_data(p_prompt, c_prompt, model="gpt-4o-mini"):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": c_prompt},
            {"role": "user", "content": p_prompt},
        ],
        # reasoning_effort="low", #NOTE only for o1 models
        # seed=1, #NOTE possible to add a seed. should we do it??
    )

    result = {}
    result["created_at"] = (
        pd.to_datetime(completion.created, unit="s")
        .tz_localize("UTC")
        .tz_convert("Europe/Zurich")
        .strftime("%Y-%m-%d %H:%M:%S %Z")
    )
    result["model"] = completion.model
    result["cost"] = completion.usage.total_tokens
    result["response"] = completion.choices[0].message.content

    return result


def read_api_keys_from_csv(file_path):
    api_keys = {}
    with open(file_path, mode="r") as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            provider, api_key = row
            api_keys[provider] = api_key
    return api_keys


# get mini publics data
mps_surveys = surveys.get_mps_data()

# iterate over each mini public
for mp in mps_surveys:

    # get policies and consideration statements
    policies, considerations = surveys.get_policies_and_considerations(mps_surveys[mp])

    # create policy and consideration files if they don't exist
    p_df, c_df = utils.get_or_create_output(mp, policies, considerations)

    # create policy and consideration prompts
    p_prompt, c_prompt = utils.get_prompts(policies, considerations)

    for i in range(1):

        # try to make API call
        result = get_llm_responses(p_prompt, c_prompt)

        print(result)
        break

        # parse ranks from response
        ranks = utils.parse_numbers_from_string(response)
        print(f"Policies [{len(policies)}/{len(ranks)}] [{i}]: {ranks}")

        # set columns
        meta = [created_at, response_model, PROVIDER, cost]

        # append ranks to policy dataframe
        p_df_temp.loc[len(p_df_temp)] = meta + ranks

        # try to make API call
        created_at, response_model, cost, response = get_llm_response(prompt_c, model)

        # parse ranks from response
        ranks = utils.parse_numbers_from_string(response)
        print(f"Considerations [{len(considerations)}/{len(ranks)}] [{i}]: {ranks}")

        # set columns
        meta = [created_at, response_model, PROVIDER, cost]

        # append ranks to policy dataframe
        try:
            c_df_temp.loc[len(c_df_temp)] = meta + ranks
        except Exception as e:
            print(f"Error appending to dataframe: {e}")
            continue

    # only do 1 minipublic for now
    break
