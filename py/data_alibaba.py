import os
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
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)


def send_message(model, messages, temperature, qwq):

    if qwq:
        res = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True,
            stream_options={"include_usage": True},
        )
    else:
        res = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
    return res


def parse_response(res, qwq):

    reasoning_content = ""  # Define complete thinking process
    answer_content = ""  # Define complete response
    is_answering = (
        False  # Determine if thinking process has ended and response has begun
    )

    if qwq:
        # print("\n" + "=" * 20 + "Reasoning Process" + "=" * 20 + "\n")
        for chunk in res:
            # If chunk.choices is empty, print usage
            if not chunk.choices:
                usage = chunk.usage
            else:
                delta = chunk.choices[0].delta
                # Print thinking process
                # print(hasattr(delta, "reasoning_content"))
                # print(delta)
                # print(delta.reasoning_content != None)
                if (
                    hasattr(delta, "reasoning_content")
                    and delta.reasoning_content != None
                ):
                    # print(delta.reasoning_content, end="", flush=True)
                    reasoning_content += delta.reasoning_content
                else:
                    # Start response
                    if delta.content != "" and is_answering is False:
                        # print("\n" + "=" * 20 + "Complete Response" + "=" * 20 + "\n")
                        is_answering = True
                    # Print response process
                    # print(delta.content, end="", flush=True)
                    answer_content += delta.content

        # format reasoning like deepseek
        reasoning_content = f"<think>{reasoning_content}</think>"

        return usage, f"{reasoning_content}\n{answer_content}"

    else:
        return res.usage, res.choices[0].message.content


def generate_data(
    mp,
    p_prompt,
    c_prompt,
    cuid,
    model="qwen-plus",
    temperature=0,
    reason=False,
):

    # get current time
    date = get_utc_time()

    # get provider
    provider = get_provider(model)

    # QwQ model only supports streaming output calls
    if model == "qwq-plus":
        qwq = True
    else:
        qwq = False

    # build initial message
    messages = [
        {"role": "user", "content": c_prompt},
    ]

    # send first message
    res = send_message(model, messages, temperature, qwq)

    usage, c_response = parse_response(res, qwq)

    # get cost
    input_tokens = usage.prompt_tokens
    output_tokens = usage.completion_tokens

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
        usage.prompt_tokens,
        usage.completion_tokens,
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
    res = send_message(model, messages, temperature, qwq)

    usage, p_response = parse_response(res, qwq)

    # get cost
    input_tokens += usage.prompt_tokens
    output_tokens += usage.completion_tokens

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
        usage.prompt_tokens,
        usage.completion_tokens,
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

        res = send_message(model, messages, temperature, qwq)

        usage, r_response = parse_response(res, qwq)

        reason_text = parse_reasoning_from_response(r_response)

        # get cost
        input_tokens += usage.prompt_tokens
        output_tokens += usage.completion_tokens

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
            usage.prompt_tokens,
            usage.completion_tokens,
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
