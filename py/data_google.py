from datetime import datetime, timezone
from google import genai
from google.genai import types
import os

from utils import (
    CONSIDERATIONS,
    POLICIES,
    PROMPT_R,
    REASONS,
    log_request,
    parse_numbers_from_response,
    parse_reasoning_from_response,
    get_provider,
)

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def generate_data(
    mp,
    p_prompt,
    c_prompt,
    cuid,
    system_prompt=None,
    model="gemini-1.5-flash",
    temperature=0,
    reason=False,
):

    # get current time
    date = datetime.now(timezone.utc)

    # get provider
    provider = get_provider(model)

    # start chat
    # set temperature and system prompt in runtime
    if system_prompt is None:
        chat = client.chats.create(
            model=model, config=types.GenerateContentConfig(temperature=temperature)
        )
    else:
        chat = client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                temperature=temperature, system_instruction=system_prompt
            ),
        )

    # send first message
    res = chat.send_message(c_prompt)
    c_response = res.text
    # print(res.usage_metadata)

    # get cost
    input_tokens = res.usage_metadata.prompt_token_count
    output_tokens = res.usage_metadata.candidates_token_count

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
        res.usage_metadata.prompt_token_count,
        res.usage_metadata.candidates_token_count,
        res.model_version,
    )

    # get p prompt response
    res = chat.send_message(p_prompt)
    p_response = res.text
    # print(res.usage_metadata)

    # get cost
    input_tokens += res.usage_metadata.prompt_token_count
    output_tokens += res.usage_metadata.candidates_token_count

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
        res.usage_metadata.prompt_token_count,
        res.usage_metadata.candidates_token_count,
        res.model_version,
    )

    if reason:

        res = chat.send_message(PROMPT_R)
        r_response = res.text
        # print(res.usage_metadata)

        # get cost
        input_tokens += res.usage_metadata.prompt_token_count
        output_tokens += res.usage_metadata.candidates_token_count

        reason_text = parse_reasoning_from_response(r_response)

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
            res.usage_metadata.prompt_token_count,
            res.usage_metadata.candidates_token_count,
            res.model_version,
        )

    else:
        reason_text = "Reasoning was not requested."

    # parse ranks from response
    c_ranks = parse_numbers_from_response(c_response)
    p_ranks = parse_numbers_from_response(p_response)

    # set meta columns
    meta = [date, provider, model, temperature, input_tokens, output_tokens]

    return p_ranks, c_ranks, reason_text, meta
