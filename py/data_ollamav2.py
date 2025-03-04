from datetime import datetime, timezone
from ollama import chat
from ollama import ChatResponse

from data_llm import DataGenerator
from utils import (
    PROMPT_C_V2,
    PROMPT_R,
    SYSTEM_PROMPT_C,
    log_request,
    parse_numbers_from_response,
    parse_reasoning_from_response,
)

PROVIDER = "ollama"

PROVIDERS = {"llama3.2": "meta", "gemma2": "google", "deepseek-r1": "deepseek"}


# class Ollama(DataGenerator):
#     pass


def generate_data(p_prompt, considerations, model="llama3.2", reason=False):

    # get current time
    date = datetime.now(timezone.utc)

    # get provider
    provider = PROVIDERS[model] if model in PROVIDERS else PROVIDER

    print(f"> generating data from {provider}: {model}")

    # build initial message
    messages = [
        {"role": "assistant", "content": PROMPT_C_V2.format("10")},
    ]

    print("> consideration ratings...")

    # send first message
    res: ChatResponse = chat(model=model, messages=messages)

    c_response = res.message.content

    # log request history to file
    log_request(date, provider, model, PROMPT_C_V2, c_response)

    c_ranks = []

    i = 0
    for c in considerations:

        i += 1

        # append response to messages
        messages.append(
            {"role": "assistant", "content": c_response},
        )

        # append policies prompt
        messages.append(
            {"role": "user", "content": c},
        )

        # send first message
        res: ChatResponse = chat(model=model, messages=messages)

        c_response = res.message.content

        if c_response.isdigit():
            rank = int(c_response)
        else:
            print(c_response)
            rank = 0

        c_ranks.append(rank)

        print(f"{i}: [{rank}] {c}")

        # log request history to file
        log_request(date, provider, model, PROMPT_C_V2, c_response)

    print("> policies rankings...")

    # append response to messages
    messages.append(
        {"role": "assistant", "content": c_response},
    )

    # append policies prompt
    messages.append(
        {"role": "user", "content": p_prompt},
    )

    # get p prompt response
    res: ChatResponse = chat(model=model, messages=messages)

    p_response = res.message.content

    # log request history to file
    log_request(date, provider, model, p_prompt, p_response)

    if reason:

        # append response to messages
        messages.append(
            {"role": "assistant", "content": p_response},
        )

        # append reasoning prompt
        messages.append(
            {"role": "user", "content": PROMPT_R},
        )

        print("> reasoning...")
        res: ChatResponse = chat(model=model, messages=messages)

        r_response = res.message.content

        reason_text = parse_reasoning_from_response(r_response)

        # log request history to file
        log_request(date, provider, model, PROMPT_R, r_response)

    else:
        reason_text = "Reasoning was not requested."

    # parse ranks from response
    # c_ranks = parse_numbers_from_response(c_response)
    p_ranks = parse_numbers_from_response(p_response)

    # local models, no cost
    cost = 0

    # set columns
    meta = [date, res.model, provider, cost]

    return p_ranks, c_ranks, reason_text, meta
