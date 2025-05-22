import os
import re
import anthropic

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

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)

# should be enough for data generation
MAX_TOKENS = 1024


def is_reasoning(model):
    if re.search(r"-think=", model):
        return True
    return False


REASONING_BUDGET = {"low": 1024, "high": 16000}

# from https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking
# The budget_tokens parameter determines the maximum number of
# tokens Claude is allowed to use for its internal reasoning process.
# Larger budgets can improve response quality by enabling more thorough
# analysis for complex problems, although Claude may not use the entire
# budget allocated, especially at ranges above 32K.

# Adjusted to 16K because: ERROR: Streaming is strongly recommended for
# operations that may take longer than 10 minutes.
# See https://github.com/anthropics/anthropic-sdk-python#long-requests for more details


def send_message(model, messages, temperature):

    if is_reasoning(model):

        # get model and reasoning effort
        model, reasoning_effort = model.split("-think=")

        return client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS
            + REASONING_BUDGET[
                reasoning_effort
            ],  # set to MAX_TOKENS + REASONING_BUDGET to allow for response + reasoning
            thinking={
                "type": "enabled",
                "budget_tokens": REASONING_BUDGET[reasoning_effort],
            },
            # temperature=temperature, # no temperature parameter for reasoning
            messages=messages,
        )

    return client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        temperature=temperature,
        messages=messages,
    )


def get_response(model, res):
    if is_reasoning(model):

        for content_block in res.content:
            if content_block.type == "thinking":
                reasoning_content = content_block.thinking
            elif content_block.type == "text":
                response_content = content_block.text

        # format response like deepseek
        return f"<think>{reasoning_content}</think>{response_content}"

    return res.content[0].text


## API: https://docs.anthropic.com/en/api/messages
def generate_data(
    mp,
    p_prompt,
    c_prompt,
    cuid,
    model="claude-3-haiku-20240307",
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

    c_response = get_response(model, res)

    # get cost
    input_tokens = res.usage.input_tokens
    output_tokens = res.usage.output_tokens

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
        res.usage.input_tokens,
        res.usage.output_tokens,
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
    input_tokens += res.usage.input_tokens
    output_tokens += res.usage.output_tokens

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
        res.usage.input_tokens,
        res.usage.output_tokens,
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
        input_tokens += res.usage.input_tokens
        output_tokens += res.usage.output_tokens

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
            res.usage.input_tokens,
            res.usage.output_tokens,
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
