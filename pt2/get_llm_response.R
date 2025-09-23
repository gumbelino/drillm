# R function to send requests to the OpenRouter.ai API

# DESCRIPTION:
# This file contains functions to interact with the OpenRouter.ai API.
# 'ask_openrouter' sends a request to a model and returns the response,
# conversation history, and a cost breakdown. 'calculate_openrouter_cost'
# provides a way to estimate costs based on token counts.

# DEPENDENCIES:
# This function requires the 'httr' and 'jsonlite' packages.
# You can install them by running:
# install.packages("httr")
# install.packages("jsonlite")

# API KEY SETUP:
# For security, it is highly recommended to store your OpenRouter API key
# as an environment variable rather than hardcoding it in your script.
# You can set it in your R session like this:
# Sys.setenv(OPENROUTER_API_KEY = "your_api_key_here")
# Alternatively, you can add it to your .Renviron file for persistence
# across sessions.


# --- Internal Caching for Model Prices ---
.openrouter_cache <- new.env(parent = emptyenv())

#' Fetches and caches model pricing information from OpenRouter.
#'
#' @param model_id The ID of the model (e.g., "google/gemini-flash-1.5").
#' @return A list with 'prompt' and 'completion' token costs per million tokens.
#' @keywords internal
get_model_pricing <- function(model_id) {
  # Check if model data is already cached
  if (is.null(.openrouter_cache$models)) {
    message("Fetching model pricing information from OpenRouter...")
    response <- httr::GET("https://openrouter.ai/api/v1/models")
    if (httr::status_code(response) == 200) {
      .openrouter_cache$models <- httr::content(response, "parsed")$data
    } else {
      stop("Failed to fetch model pricing information.")
    }
  }
  
  # Find the specific model in the cached data
  model_info <- Filter(function(m) m$id == model_id, .openrouter_cache$models)
  
  if (length(model_info) == 0) {
    warning(paste("Could not find pricing information for model:", model_id))
    return(list(prompt = 0, completion = 0))
  }
  
  pricing <- model_info[[1]]$pricing
  
  # Prices are per million tokens, so we divide by 1,000,000
  return(list(
    prompt = as.numeric(pricing$prompt) / 1e6,
    completion = as.numeric(pricing$completion) / 1e6
  ))
}

#' Calculate the cost of an OpenRouter API request based on token usage.
#'
#' @param prompt_tokens An integer, the number of tokens in the prompt.
#' @param completion_tokens An integer, the number of tokens in the completion.
#' @param model_id A string specifying the model ID (e.g., "google/gemini-flash-1.5").
#' @return A list containing 'prompt_cost', 'completion_cost', and 'total_cost' in USD.
#' @export
calculate_cost <- function(prompt_tokens, completion_tokens, model_id) {
  pricing <- get_model_pricing(model_id)
  
  prompt_cost <- prompt_tokens * pricing$prompt
  completion_cost <- completion_tokens * pricing$completion
  total_cost <- prompt_cost + completion_cost
  
  return(list(
    prompt_cost = prompt_cost,
    completion_cost = completion_cost,
    total_cost = total_cost
  ))
}


#' Send a request to a model on OpenRouter.ai
#'
#' This function sends a system prompt and a user prompt to a specified
#' language model through the OpenRouter.ai API and returns the text response.
#' It can also manage conversation history.
#'
#' @param user_prompt A string containing the prompt or question for the model.
#' @param model A string specifying the model to use (e.g., "google/gemini-flash-1.5").
#'        You can find model names on the OpenRouter.ai website.
#' @param system_prompt A string defining the role or behavior of the model. This is
#'        only used for the first message in a conversation (when 'context' is NULL).
#' @param context A list representing the conversation history. If provided, the
#'        'system_prompt' is ignored, as the context is assumed to contain the full
#'        history. Defaults to NULL for a new conversation.
#' @param temperature A numeric value between 0 and 2 that controls the randomness
#'        of the model's output. Higher values mean more creative responses.
#' @param context_length An integer specifying the maximum number of tokens
#'        (words and punctuation) in the response. This is also known as `max_tokens`.
#' @param reasoning A logical toggle (TRUE/FALSE). When set to TRUE, it hints to
#'        the model that it should "think" or use reasoning steps. The exact
#'        behavior is model-dependent. It works by setting `tool_choice` to `"auto"`.
#' @param api_key A string containing your OpenRouter.ai API key. It is strongly
#'        recommended to use the default, which retrieves the key from an
#'        environment variable named `OPENROUTER_API_KEY`.
#'
#' @return A list containing three elements: 'response', 'context', and 'cost'. 
#'         'cost' is itself a list containing 'prompt_cost', 'completion_cost', 
#'         and 'total_cost' in USD.
#' @export
#'
#' @examples
#' \dontrun{
#' # Make sure to set your API key first
#' # Sys.setenv(OPENROUTER_API_KEY = "your_api_key_here")
#'
#' # First turn of the conversation
#' first_turn <- ask_openrouter(
#'   user_prompt = "What are the three main benefits of using R for data analysis?",
#'   model = "google/gemini-flash-1.5",
#'   system_prompt = "You are a helpful assistant who provides concise answers."
#' )
#' cat("--- Initial Response ---\n")
#' cat(first_turn$response)
#' cat(paste0("\n--- Total Cost: $", format(first_turn$cost$total_cost, scientific = FALSE), " ---\n"))
#'
#' # Follow-up question using the context from the first turn
#' second_turn <- ask_openrouter(
#'   user_prompt = "Can you elaborate on the second benefit you mentioned?",
#'   model = "google/gemini-flash-1.5",
#'   context = first_turn$context
#' )
#' cat("\n\n--- Follow-up Response ---\n")
#' cat(second_turn$response)
#' cat(paste0("\n--- Total Cost: $", format(second_turn$cost$total_cost, scientific = FALSE), " ---\n"))
#' }
get_llm_response <- function(user_prompt,
                           model = "google/gemini-flash-1.5",
                           system_prompt = "You are a helpful assistant.",
                           context = NULL,
                           temperature = 0,
                           # max_tokens = 2048,
                           enable_reasoning = FALSE,
                           reasoning_effort = "low",
                           api_key = Sys.getenv("OPENROUTER_API_KEY")) {
  
  # # Check for required packages
  # if (!requireNamespace("httr", quietly = TRUE)) {
  #   stop("The 'httr' package is required. Please install it with install.packages('httr').")
  # }
  # if (!requireNamespace("jsonlite", quietly = TRUE)) {
  #   stop("The 'jsonlite' package is required. Please install it with install.packages('jsonlite').")
  # }
  # 
  # Validate API key
  if (api_key == "") {
    stop("API key is not found. Please set the OPENROUTER_API_KEY environment variable or pass it directly to the function.")
  }
  
  # API endpoint
  url <- "https://openrouter.ai/api/v1/chat/completions"
  
  # Headers
  headers <- c(
    "Authorization" = paste("Bearer", api_key),
    "Content-Type" = "application/json"
  )
  
  # Construct the message list
  messages <- list()
  if (is.null(context)) {
    # Start a new conversation with the system prompt if no context is provided
    messages <- list(
      list(role = "system", content = system_prompt),
      list(role = "user", content = user_prompt)
    )
  } else {
    # Continue an existing conversation by appending the new user prompt
    messages <- c(context, list(list(role = "user", content = user_prompt)))
  }
  
  # Set up reasoning parameters
  reasoning <- c(
    "enabled" = enable_reasoning,
    "effort" = reasoning_effort
  )
  
  # Construct the body of the request
  body <- list(
    model = model,
    messages = messages,
    temperature = temperature
    # max_tokens = max_tokens,
    # reasoning = reasoning
  )
  
  # Add reasoning parameter if requested
  # if (reasoning) {
  #   body$tool_choice <- "auto"
  # }
  # 
  # Make the POST request
  response <- httr::POST(
    url = url,
    httr::add_headers(.headers = headers),
    body = jsonlite::toJSON(body, auto_unbox = TRUE),
    encode = "json"
  )
  
  # Check for errors in the response
  if (httr::status_code(response) != 200) {
    error_content <- httr::content(response, "text", encoding = "UTF-8")
    stop(
      sprintf(
        "API request failed with status %d\nError message: %s",
        httr::status_code(response),
        error_content
      )
    )
  }
  
  # Parse the response content
  parsed_content <- httr::content(response, "parsed")
  
  # Get usage costs (in tokens)
  usage <- parsed_content$usage
  
  # Extract the text from the response
  text_response <- parsed_content$choices[[1]]$message$content
  
  # Create the assistant's message to be added to the context
  assistant_message <- parsed_content$choices[[1]]$message
  
  # Update the context for the next turn
  updated_context <- c(messages, list(assistant_message))
  
  # Return a list containing the response, updated context, and cost details
  return(list(
    response = text_response,
    context = updated_context,
    usage = usage
  ))
}

# --- Example Usage ---
# 1. Set your API key (replace "your_api_key_here" with your actual key)
# Sys.setenv(OPENROUTER_API_KEY = "your_api_key_here")
#
# 2. Call the function for the first time

first_turn <- get_llm_response(
  user_prompt = "Explain the concept of neural networks in three simple points.",
  model = "deepseek/deepseek-r1",
  enable_reasoning = TRUE,
)

cat("--- First Response ---\n")
cat(first_turn$response)
cat(paste0("\n--- Total Usage: ", format(first_turn$usage$total_tokens, scientific = FALSE, nsmall = 8), " tokens ---\n"))

# 3. Use the context for a follow-up question
if (!is.null(first_turn)) {
  
  second_turn <- get_llm_response(
    user_prompt = "Now, can you elaborate on the second point?",
    model = "deepseek/deepseek-r1",
    context = first_turn$context # Pass the context from the first call
  )
  
  cat("\n\n--- Follow-up Response ---\n")
  cat(second_turn$response)
  cat(paste0("\n--- Total Usage: ", format(second_turn$usage$total_tokens, scientific = FALSE, nsmall = 8), " tokens ---\n"))

  }
  


