import re
from openai import OpenAI

from utils import (
    CONSIDERATIONS,
    POLICIES,
    PROMPT_R,
    REASONS,
    get_utc_time,
    log_request,
    parse_numbers_from_response,
    parse_reasoning_from_response,
    get_provider,
)

# define openai client to access API
client = OpenAI(
    organization="org-5vaJcJj36BER6kXQMdkKKpZP",
    project="proj_k8Gv8E3GjDirposW9zEqvdfq",
)

# default reasoning effort
R_EFFORT = "medium"


def send_message(model, messages, temperature):

    # check if model contains "o{digit}" such as o1-mini, o1
    # NOTE: temperature parameter is not used
    if re.search(r"o\d", model):
        return client.chat.completions.create(model=model, messages=messages)

    return client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )


def generate_data(
    mp,
    p_prompt,
    c_prompt,
    cuid,
    model="gpt-4o",
    temperature=0,
    reason=False,
):

    # get current time
    date = get_utc_time()

    # get provider
    provider = get_provider(model)

    # build initial message
    messages = [
        {"role": "user", "content": c_prompt},
    ]

    # send first message
    res = send_message(
        model,
        messages,
        temperature,
    )

    c_response = res.choices[0].message.content

    # get cost
    input_tokens = res.usage.prompt_tokens
    output_tokens = res.usage.completion_tokens

    # log request history to file
    log_request(
        cuid,
        date,
        provider,
        model,
        temperature,
        mp,
        CONSIDERATIONS,
        c_prompt,
        c_response,
        res.usage.prompt_tokens,
        res.usage.completion_tokens,
        res.model,
    )

    # append response to messages
    messages.append(
        {"role": "assistant", "content": c_response},
    )

    # append policies prompt
    messages.append(
        {"role": "user", "content": p_prompt},
    )

    # get p prompt response
    res = send_message(
        model,
        messages,
        temperature,
    )

    p_response = res.choices[0].message.content

    # get cost
    input_tokens += res.usage.prompt_tokens
    output_tokens += res.usage.completion_tokens

    # log request history to file
    log_request(
        cuid,
        date,
        provider,
        model,
        temperature,
        mp,
        POLICIES,
        p_prompt,
        p_response,
        res.usage.prompt_tokens,
        res.usage.completion_tokens,
        res.model,
    )

    if reason:

        # append response to messages
        messages.append(
            {"role": "assistant", "content": p_response},
        )

        # append reasoning prompt
        messages.append(
            {"role": "user", "content": PROMPT_R},
        )

        res = send_message(
            model,
            messages,
            temperature,
        )

        r_response = res.choices[0].message.content

        reason_text = parse_reasoning_from_response(r_response)

        # get cost
        input_tokens += res.usage.prompt_tokens
        output_tokens += res.usage.completion_tokens

        # log request history to file
        log_request(
            cuid,
            date,
            provider,
            model,
            temperature,
            mp,
            REASONS,
            PROMPT_R,
            r_response,
            res.usage.prompt_tokens,
            res.usage.completion_tokens,
            res.model,
        )

    else:
        reason_text = "Reasoning was not requested."

    # parse ranks from response
    c_ranks = parse_numbers_from_response(c_response)
    p_ranks = parse_numbers_from_response(p_response)

    # set meta columns
    meta = [date, provider, model, temperature, input_tokens, output_tokens]

    return p_ranks, c_ranks, reason_text, meta
