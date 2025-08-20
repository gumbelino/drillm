import pandas as pd
from utils import PROMPT_S


def get_system_prompts():
    return pd.read_csv("prompts/prompts.csv")


def get_prompt_uids():
    prompts_df = get_system_prompts()
    return prompts_df["uid"].tolist()


def build_system_prompt(uid):

    # check for "all" keyword
    if uid == "all":
        return None

    prompts_df = get_system_prompts()

    # get row with uid
    row = prompts_df[prompts_df["uid"] == uid]

    # check if row is empty
    if row.empty:
        raise ValueError(f"Prompt with uid {uid} not found in prompts.csv")

    # get role and description
    role = row["role"].values[0]
    description = row["description"].values[0]
    article = row["article"].values[0]

    # build system prompt
    system_prompt = PROMPT_S.format(article, role, description)

    return system_prompt
