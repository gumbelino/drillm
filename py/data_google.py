from datetime import datetime, timezone
import google.generativeai as genai
import os

from utils import (
    log_request,
    parse_numbers_from_response,
    parse_numbers_from_string,
    PROMPT_R,
)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

PROVIDER = "google"


def generate_data(p_prompt, c_prompt, model="gemini-1.5-flash", reason=False):

    print(f"getting data from {PROVIDER}: {model}")

    date = datetime.now(timezone.utc)

    api = genai.GenerativeModel(model)
    chat = api.start_chat()

    print("> consideration ratings...")
    c_response = chat.send_message(c_prompt)

    # log request history to file
    log_request(date, PROVIDER, model, c_prompt, c_response.text)

    print("> policies rankings...")
    p_response = chat.send_message(p_prompt)

    # log request history to file
    log_request(date, PROVIDER, model, p_prompt, p_response.text)

    # parse ranks from response
    c_ranks = parse_numbers_from_response(c_response.text)
    p_ranks = parse_numbers_from_response(p_response.text)

    # calculate cost
    cost = (
        c_response.usage_metadata.total_token_count
        + p_response.usage_metadata.total_token_count
    )

    if reason:
        print("> reasoning...")
        r_response = chat.send_message(PROMPT_R)

        # Clean up the reasoning text
        reason_text = r_response.text.strip()
        reason_text = " ".join(reason_text.split())

        # log request history to file
        log_request(date, PROVIDER, model, PROMPT_R, reason_text)

        # update cost
        cost += r_response.usage_metadata.total_token_count
    else:
        reason_text = "Reasoning was not requested."

    # set columns
    meta = [date, model, PROVIDER, cost]

    return p_ranks, c_ranks, reason_text, meta
