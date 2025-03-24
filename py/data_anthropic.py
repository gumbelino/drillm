import os
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
    res = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        temperature=temperature,
        messages=messages,
    )

    c_response = res.content[0].text

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
    res = client.messages.create(
        model=model, max_tokens=MAX_TOKENS, messages=messages, temperature=temperature
    )

    p_response = res.content[0].text

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

        res = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            messages=messages,
            temperature=temperature,
        )
        r_response = res.content[0].text

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
