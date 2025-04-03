from together import Together

client = Together()

response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=[
        {"role": "user", "content": "What are some fun things to do in New York?"}
    ],
)


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

T_MODELS = {
    "llama3:70b": "meta-llama/Llama-3-70b-chat-hf",
    "gemma2:27b": "google/gemma-2-27b-it",
    "llama3.1:405B-turbo": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
    "llama3.3:70b": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    "llama2:13b": "meta-llama/Llama-2-13b-chat-hf",
    "llama2:70b": "meta-llama/Llama-2-70b-hf",
}


def send_message(model, messages, temperature):

    # check if model contains "o{digit}" such as o1-mini, o1
    # NOTE: temperature parameter is not used
    try:
        together_model = T_MODELS[model]
    except KeyError as e:
        raise ValueError(
            f"Model {model} is not supported. Supported models are: {', '.join(T_MODELS.keys())}"
        ) from e

    return client.chat.completions.create(
        model=together_model,
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
