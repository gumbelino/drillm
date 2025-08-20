import os
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
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1",
)


def is_reasoning(model):
    if re.search(r"-r=", model):
        return True
    return False


def send_message(model, messages, temperature):

    if is_reasoning(model):

        # get model and reasoning effort
        model, reasoning_effort = model.split("-r=")

        return client.chat.completions.create(
            model=model,
            reasoning_effort=reasoning_effort,
            messages=messages,
            temperature=temperature,
        )

    return client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )


def get_response(model, res):
    if is_reasoning(model):
        reasoning_content = res.choices[0].message.reasoning_content
        response_content = res.choices[0].message.content

        # format response like deepseek
        return f"<think>{reasoning_content}</think>{response_content}"

    return res.choices[0].message.content


def get_request_cost(model, res):

    input_tokens = res.usage.prompt_tokens
    output_tokens = res.usage.completion_tokens

    # add reasoning tokens to input
    if is_reasoning(model):
        input_tokens += res.usage.completion_tokens_details.reasoning_tokens

    return input_tokens, output_tokens


def generate_data(
    mp,
    p_prompt,
    c_prompt,
    cuid,
    system_prompt=None,
    model="grok-2-1212",
    temperature=0,
    reason=False,
):

    # get current time
    date = get_utc_time()

    # get provider
    provider = get_provider(model)

    # build initial message
    if system_prompt is None:
        messages = [
            {"role": "user", "content": c_prompt},
        ]
    else:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": c_prompt},
        ]

    # send first message
    res = send_message(
        model,
        messages,
        temperature,
    )

    c_response = get_response(model, res)

    # get cost
    input_tokens, output_tokens = get_request_cost(model, res)

    # log request history to file
    log_request(
        cuid,
        date,
        provider,
        model,
        temperature,
        system_prompt,
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

    p_response = get_response(model, res)

    # get cost
    r_input_tokens, r_output_tokens = get_request_cost(model, res)
    input_tokens += r_input_tokens
    output_tokens += r_output_tokens

    # log request history to file
    log_request(
        cuid,
        date,
        provider,
        model,
        temperature,
        system_prompt,
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

        r_response = get_response(model, res)

        reason_text = parse_reasoning_from_response(r_response)

        # get cost
        r_input_tokens, r_output_tokens = get_request_cost(model, res)
        input_tokens += r_input_tokens
        output_tokens += r_output_tokens

        # log request history to file
        log_request(
            cuid,
            date,
            provider,
            model,
            temperature,
            system_prompt,
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
