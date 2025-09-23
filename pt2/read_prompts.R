

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
calculate_cost <- function(usage, model_id) {
  
  prompt_tokens <- usage$prompt_tokens
  completion_tokens <- usage$completion_tokens
  
  pricing <- get_model_pricing(model_id)
  
  prompt_cost <- prompt_tokens * pricing$prompt
  completion_cost <- completion_tokens * pricing$completion
  total_cost <- prompt_cost + completion_cost
  
  return(total_cost)
}



library(readr)
library(uuid)

make_dri_prompts <- function(survey_info, system_prompt_uid = NA_character_) {
  
  ## get prompt templates
  prompts <- read_csv("pt2/data/dri_prompts.csv", show_col_types = FALSE)
  prompt_c_template <- prompts[prompts$type == "considerations",]$prompt
  prompt_p_template <- prompts[prompts$type == "policies",]$prompt
  prompt_r <- prompts[prompts$type == "reason",]$prompt
  prompt_q <- prompts[prompts$type == "q_method",]$prompt
  prompt_s_template <- prompts[prompts$type == "system",]$prompt
  
  ## extract survey info
  scale_max <- survey_info$scale_max
  q_method <- if (survey_info$q_method) prompt_q else ""
  
  c_df <- survey_info$considerations
  p_df <- survey_info$policies
  
  n_c <- nrow(c_df)
  n_p <- nrow(p_df)
  
  ## get statements 
  c_statements <- paste(paste0(rownames(c_df), ". ", c_df$statement), collapse = "\n")
  p_statements <- paste(paste0(rownames(p_df), ". ", p_df$statement), collapse = "\n")
  
  ## make prompts
  prompt_c <- 
    paste0(sprintf(prompt_c_template, n_c, scale_max, scale_max, q_method, n_c, n_c), 
           c_statements)
  
  prompt_p <- 
    paste0(sprintf(prompt_p_template, n_p, n_p, n_p, n_p, n_p), 
           p_statements)
  
  ## make system prompt
  if (is.na(system_prompt_uid)) {
    prompt_s <- "You are a helpful assistant."
  } else {
    # get system prompts
    system_prompts <- read_csv("pt2/data/system_prompts.csv", show_col_types = FALSE)
    s_article <- system_prompts[system_prompts$uid == system_prompt_uid,]$article
    s_role <- system_prompts[system_prompts$uid == system_prompt_uid,]$role
    s_description <- system_prompts[system_prompts$uid == system_prompt_uid,]$description
  
    # build prompt
    prompt_s <- sprintf(prompt_s_template, s_article, s_role, s_description)
  }
  
  return(list(
    system = prompt_s,
    considerations = prompt_c,
    policies = prompt_p,
    reason = prompt_r
  ))
  
}

## MAKE METADATA
model_id <- "anthropic/claude-sonnet-4"

split_parts <- strsplit(model_id, "/")[[1]]

Sys.setenv(TZ='UTC')

meta <- tibble(
  uuid = UUIDgenerate(),
  created_at_utc = Sys.time(),
  provider = split_parts[1],
  model = split_parts[2],
  survey = "ccps",
  role_uid = "csk",
)

### GET SURVEY INFO
survey_infos <- get_dri_survey_info(survey_name = meta$survey)

survey_info <- survey_infos[[1]]

### MAKE PROMPT
prompts <- make_dri_prompts(survey_info, meta$role_uid)


### GET LLM RESPONSES
cost_usd <- 0

res <- get_llm_response(prompts$considerations, system_prompt = prompts$system)
response_c <- res$response
cost_usd <- cost_usd + calculate_cost(res$usage, model_id)
log <- log_request(meta, "considerations", prompts$considerations, res)

res <- get_llm_response(prompts$policies, context = res$context)
response_p <- res$response
cost_usd <- cost_usd + calculate_cost(res$usage, model_id)
log <- bind_rows(log, log_request(meta, "policies", prompts$policies, res))

res <- get_llm_response(prompts$reason, context = res$context)
response_r <- res$response
cost_usd <- cost_usd + calculate_cost(res$usage, model_id)
log <- bind_rows(log, log_request(meta, "reason", prompts$reason, res))

## PARSE RESPONSES
considerations <- parse_llm_response(response_c, 50, "C")
policies <- parse_llm_response(response_p, 10, "P")
reason <- parse_llm_response(response_r, 1, "R")

end_time <- Sys.time()
time_s <- as.numeric(difftime(end_time, meta$created_at_utc, units = "secs"))

llm_data_row <- tibble(
  meta,
  time_s,
  cost_usd,
  considerations,
  policies,
  reason
)

## write log
# write_csv(llm_data_row, "pt2/data/llm_data_row.csv")

## append log to file
write_csv(log, "pt2/data/request_log.csv", append = TRUE)

parse_llm_response <- function(response, max_cols=c(50, 10, 1), col_prefix=c("C", "P", "R")) {
  
  # check for reasoning case
  if (col_prefix == "R") {
    return(tibble(
      R = gsub("[\r\n]+$", "", response) ## remove trailing newlines
    ))
  }
  
  lines <- unlist(strsplit(trimws(response), "\n"))
  data_matrix <- do.call(rbind, strsplit(lines, "\\. "))
  
  df <- data.frame(
    sid = paste0(col_prefix, as.numeric(data_matrix[, 1])),
    value = as.numeric(data_matrix[, 2])
  )
  
  df <- pivot_wider(df, names_from = "sid", values_from = "value")
  
  num_cols <- ncol(df)
  
  if (is.na(max_cols) || num_cols >= max_cols) {
    return(df)
  }
  
  # Calculate the number of columns to add
  cols_to_add <- max_cols - num_cols
  
  # Create a new data frame with the columns to be added
  new_cols <- data.frame(matrix(NA, nrow = nrow(df), ncol = cols_to_add))
  
  # Generate names for the new columns
  names(new_cols) <- paste0(col_prefix, (num_cols + 1):max_cols)
  
  # Combine the original data frame with the new columns
  # The use of `cbind` ensures the new columns are appended
  combined_df <- cbind(df, new_cols)
  
  return(combined_df)
}

log_request <- function(meta, type, prompt, res) {

  tibble(
    meta,
    type,
    prompt_tokens = res$usage$prompt_tokens,
    completion_tokens = res$usage$completion_tokens,
    prompt,
    response = res$response,
  )
  
}


