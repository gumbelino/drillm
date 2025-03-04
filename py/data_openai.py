import csv
from datetime import datetime, timezone
from openai import OpenAI
import pandas as pd
import surveys
import os
from utils import parse_numbers_from_string
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

    print(f"Getting data from {PROVIDER}")

    # build initial message
    messages = [
        {"role": "user", "content": c_prompt},
    ]

    print("> Getting consideration ratings...")

    # send first messageS
    res = client.chat.completions.create(
        model=model,
        messages=messages,
        # reasoning_effort="low", #NOTE only for o1 models
        # seed=1, #NOTE possible to add a seed. should we do it??
    )

    # get initial message cost
    cost = res.usage.total_tokens

    c_response = res.choices[0].message.content

    # append response to messages
    messages.append(
        {"role": "assistant", "content": c_response},
    )

    # append policies prompt
    messages.append(
        {"role": "user", "content": p_prompt},
    )

    print("> Getting policies rankings...")

    # get p prompt response
    res = client.chat.completions.create(
        model=model,
        messages=messages,
    )

    p_response = res.choices[0].message.content

    # print("c_response", c_response.text)
    # print("p_response", p_response.text)

    # calculate cost
    cost += res.usage.total_tokens

    # parse ranks from response
    c_ranks = parse_numbers_from_string(c_response)
    p_ranks = parse_numbers_from_string(p_response)

    # set columns
    meta = [datetime.now(timezone.utc), res.model, PROVIDER, cost]

    return p_ranks, c_ranks, meta
