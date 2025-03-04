from datetime import datetime, timezone
import cohere
import os

from utils import parse_numbers_from_string

PROVIDER = "cohere"

co = cohere.ClientV2(api_key=os.environ["COHERE_API_KEY"])


def get_llm_data(p_prompt, c_prompt, model="command-r-plus-08-2024"):

    print(f"Getting data from {PROVIDER}")

    # build initial message
    messages = [
        {
            "role": "user",
            "content": c_prompt,
        },
    ]

    print("> Getting consideration ratings...")

    # get response for first message
    res = co.chat(model=model, messages=messages)

    cost = res.usage.tokens.input_tokens + res.usage.tokens.output_tokens

    c_response = res.message.content[0].text

    # append response to messages
    messages.append(
        {
            "role": "assistant",
            "content": c_response,
        }
    )

    # append policies prompt
    messages.append(
        {
            "role": "user",
            "content": p_prompt,
        }
    )

    print("> Getting policies rankings...")

    # get response for second message
    res = co.chat(model=model, messages=messages)

    p_response = res.message.content[0].text

    # print("c_response", c_response)
    # print("p_response", p_response.text)

    # parse ranks from response
    c_ranks = parse_numbers_from_string(c_response)
    p_ranks = parse_numbers_from_string(p_response)

    # calculate cost
    cost += res.usage.tokens.input_tokens + res.usage.tokens.output_tokens

    # set columns
    meta = [datetime.now(timezone.utc), model, PROVIDER, int(cost)]

    return p_ranks, c_ranks, meta
