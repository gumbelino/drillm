import cohere
import os

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

client = cohere.ClientV2(os.environ.get("COHERE_API_KEY"))


def generate_data(
    mp,
    p_prompt,
    c_prompt,
    cuid,
    system_prompt=None,
    model="command-r7b-12-2024",
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
    res = client.chat(model=model, messages=messages, temperature=temperature)

    c_response = res.message.content[0].text

    # get cost
    input_tokens = res.usage.tokens.input_tokens
    output_tokens = res.usage.tokens.output_tokens

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
        res.usage.tokens.input_tokens,
        res.usage.tokens.output_tokens,
        model,
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
    res = client.chat(model=model, messages=messages, temperature=temperature)

    p_response = res.message.content[0].text

    # get cost
    input_tokens += res.usage.tokens.input_tokens
    output_tokens += res.usage.tokens.output_tokens

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
        res.usage.tokens.input_tokens,
        res.usage.tokens.output_tokens,
        model,
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

        res = client.chat(model=model, messages=messages, temperature=temperature)
        r_response = res.message.content[0].text

        reason_text = parse_reasoning_from_response(r_response)

        # get cost
        input_tokens += res.usage.tokens.input_tokens
        output_tokens += res.usage.tokens.output_tokens

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
            res.usage.tokens.input_tokens,
            res.usage.tokens.output_tokens,
            model,
        )

    else:
        reason_text = "Reasoning was not requested."

    # parse ranks from response
    c_ranks = parse_numbers_from_response(c_response)
    p_ranks = parse_numbers_from_response(p_response)

    # set meta columns
    meta = [date, provider, model, temperature, input_tokens, output_tokens]

    return p_ranks, c_ranks, reason_text, meta
