
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
    # message("Fetching model pricing information from OpenRouter...")
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
    warning("Could not find pricing information for model: ", model_id)
    return(list(prompt = 0, completion = 0))
  }
  
  pricing <- model_info[[1]]$pricing
  
  return(list(
    prompt = as.numeric(pricing$prompt),
    completion = as.numeric(pricing$completion)
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

is_valid_response <- function(considerations, policies, survey_info) {
  
  # Extract relevant data from survey_info
  c_ranks <- considerations %>% select(matches("^C\\d+$") & where(~!all(is.na(.))))
  p_ranks <- policies %>% select(matches("^P\\d+$") & where(~!all(is.na(.))))
  scale_max <- survey_info$scale_max
  q_method <- survey_info$q_method
  
  # TODO: return object instead (i.e., include reason)
  validity <- tibble(
    is_valid = TRUE,
    invalid_reason = NA_character_
  )
  
  # Check if data is valid (length mismatch)
  if (ncol(c_ranks) != nrow(survey_info$considerations)) {
    message(paste("ERROR: Considerations length mismatch (", ncol(c_ranks), "/", nrow(survey_info$considerations), ")."))
    validity$is_valid = FALSE; validity$invalid_reason = "c_length_mismatch"
    return(validity)
  }
  
  if (ncol(p_ranks) != nrow(survey_info$policies)) {
    message(paste("ERROR: Policies length mismatch (", ncol(p_ranks), "/", nrow(survey_info$policies), ")."))
    validity$is_valid = FALSE; validity$invalid_reason = "p_length_mismatch"
    return(validity)
  }
  
  # Check if c_ranks contains invalid values
  if (any(c_ranks > scale_max | c_ranks < 1)) {
    message("ERROR: Consideration ranks contain invalid values.")
    validity$is_valid = FALSE; validity$invalid_reason = "c_invalid_values"
    return(validity)
  }
  
  # Check if p_ranks contains invalid values
  if (any(p_ranks > ncol(p_ranks) | p_ranks < 1)) {
    message("ERROR: Policy ranks contain invalid values.")
    validity$is_valid = FALSE; validity$invalid_reason = "p_invalid_values"
    return(validity)
  }
  
  # Check for duplicate values in p_ranks
  if (ncol(p_ranks) != length(unique(unlist(p_ranks)))) {
    message("ERROR: Policy ranks contains duplicate values.")
    validity$is_valid = FALSE; validity$invalid_reason = "p_duplicate_ranks"
    return(validity)
  }
  
  # Check for quasi-normality (assuming a quasi_normality_check function exists in R)
  if (q_method && !quasi_normality_check(c_ranks)) {
    message("ERROR: Considerations do not follow a Fixed Quasi-Normal Distribution.")
    validity$is_valid = FALSE; validity$invalid_reason = "c_not_q_method"
    return(validity)
  }
  
  # Check if all considerations are the same value
  if (length(unique(unlist(c_ranks))) == 1) {
    message("ERROR: All considerations have the same rating.")
    validity$is_valid = FALSE; validity$invalid_reason = "c_all_equal"
    return(validity)
  }
  
  return(validity)
}


# Assuming a placeholder for the quasi_normality_check function
#' Checks if ratings approximate a Fixed Quasi-Normal Distribution.
#'
#' @param ratings A numeric vector of ratings.
#' @return TRUE if the data exhibits characteristics suggestive of
#'   a Quasi-Normal Distribution, FALSE otherwise.
#'
#' FIXME: make check more robust
quasi_normality_check <- function(ratings) {
  
  mean_val <- mean(ratings)
  median_val <- median(ratings)
  iqr_val <- IQR(ratings)
  
  # Define rough criteria (adjust as needed)
  is_quasi_normal <- abs(mean_val - median_val) < 10 && iqr_val < 30
  
  return(is_quasi_normal)
}


