

library(readr)


make_dri_prompts <- function(survey_info, system_prompt = NA) {
  
  ## get prompt templates
  prompts <- read_csv("pt2/data/dri_prompts.csv")
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
  
  ## TODO
  prompt_s <- system_prompt
  
  return(list(
    prompt_s = prompt_s,
    prompt_c = prompt_c,
    prompt_p = prompt_p,
    prompt_r = prompt_r,
  ))
  
}

### GET SURVEY INFO

survey_infos <- get_dri_survey_info(survey_name = "ccps")

survey_info <- survey_info[[1]]

### MAKE PROMPT




cat(prompt)


### GET LLM RESPONSE

res <- get_llm_response(prompt)

input_string <- res$response

lines <- unlist(strsplit(trimws(input_string), "\n"))

data_matrix <- do.call(rbind, strsplit(lines, "\\. "))

df <- data.frame(
  sid = paste0("C", as.numeric(data_matrix[, 1])),
  value = as.numeric(data_matrix[, 2])
)

df_t <- pivot_wider(df, names_from = "sid", values_from = "value")

cs <- append_cols(df_t, 50)

res$usage$total_tokens









append_cols <- function(df, max_cols) {
  
  num_cols <- ncol(df)
  
  if (is.na(max_cols) || num_cols >= max_cols) {
    return(df)
  }
  
  # Calculate the number of columns to add
  cols_to_add <- max_cols - num_cols
  
  # Create a new data frame with the columns to be added
  new_cols <- data.frame(matrix(NA, nrow = nrow(df), ncol = cols_to_add))
  
  # Generate names for the new columns
  names(new_cols) <- paste0("C", (num_cols + 1):max_cols)
  
  # Combine the original data frame with the new columns
  # The use of `cbind` ensures the new columns are appended
  combined_df <- cbind(df, new_cols)
  
  return(combined_df)
}



