from datetime import datetime, timezone
from ollama import chat
from ollama import ChatResponse

from utils import (
    CONSIDERATIONS,
    POLICIES,
    PROVIDERS,
    PROMPT_R,
    REASONS,
    log_request,
    parse_numbers_from_response,
    parse_reasoning_from_response,
)

PROVIDER = "ollama"


def generate_data(mp, p_prompt, c_prompt, cuid, model="llama3.2", reason=False):

    # get current time
    date = datetime.now(timezone.utc)

    # get provider
    provider = PROVIDERS[model] if model in PROVIDERS else PROVIDER

    # build initial message
    messages = [
        {"role": "user", "content": c_prompt},
    ]

    # send first messageS
    res: ChatResponse = chat(model=model, messages=messages)

    c_response = res.message.content

    # log request history to file
    log_request(cuid, date, provider, model, mp, CONSIDERATIONS, c_prompt, c_response)

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
    log_request(cuid, date, provider, model, mp, POLICIES, p_prompt, p_response)

    if reason:

        # append response to messages
        messages.append(
            {"role": "assistant", "content": p_response},
        )

        # append reasoning prompt
        messages.append(
            {"role": "user", "content": PROMPT_R},
        )

        res: ChatResponse = chat(model=model, messages=messages)

        r_response = res.message.content

        reason_text = parse_reasoning_from_response(r_response)

        # log request history to file
        log_request(cuid, date, provider, model, mp, REASONS, PROMPT_R, r_response)

    else:
        reason_text = "Reasoning was not requested."

    # parse ranks from response
    c_ranks = parse_numbers_from_response(c_response)
    p_ranks = parse_numbers_from_response(p_response)

    # local models, no cost
    input_tokens = 0
    output_tokens = 0

    # set meta columns
    meta = [date, provider, res.model, input_tokens, output_tokens]

    return p_ranks, c_ranks, reason_text, meta
