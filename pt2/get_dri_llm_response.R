
library(uuid)

# load all functions
source("pt2/read_prompts.R")
source("get_dri_survey_info.R")
source("pt2/get_llm_response.R")

SURVEY_FILE <- "data/surveys_v5.xlsx"
survey_names <- excel_sheets(SURVEY_FILE) 
survey_names <- sort(survey_names[!grepl("^~", survey_names) & survey_names != "template"])

get_dri_llm_response <- function(model_id, survey_name, role_uid = NA_character_) {
  
  # set time to UTC for consistent logging
  Sys.setenv(TZ='UTC')
  
  if (!survey_name %in% survey_names) {
    stop("Invalid survey name: ", 
            survey_name, 
            "\nValid names include:\n",
            paste(paste0(1:length(survey_names), ". ", sort(survey_names)), collapse = "\n"))
  }
  
  split_parts <- strsplit(model_id, "/")[[1]]
  
  # create meta data to be attached to request logs
  meta <- tibble(
    uuid = UUIDgenerate(),
    created_at_utc = Sys.time(),
    provider = split_parts[1],
    model = split_parts[2],
    survey = survey_name,
    role_uid = role_uid,
  )
  
  ### GET SURVEY INFO
  survey_infos <- get_dri_survey_info(survey_name = meta$survey)
  
  survey_info <- survey_infos[[1]]
  
  ### MAKE PROMPT
  prompts <- make_dri_prompts(survey_info, meta$role_uid)
  
  
  ### GET LLM RESPONSES
  est_cost_usd <- 0
  
  res <- get_llm_response(prompts$considerations, model_id = model_id, system_prompt = prompts$system)
  response_c <- res$response
  est_cost_usd <- est_cost_usd + calculate_cost(res$usage, model_id)
  log <- log_request(meta, "considerations", prompts$considerations, res)
  
  res <- get_llm_response(prompts$policies, model_id = model_id, context = res$context)
  response_p <- res$response
  est_cost_usd <- est_cost_usd + calculate_cost(res$usage, model_id)
  log <- bind_rows(log, log_request(meta, "policies", prompts$policies, res))
  
  res <- get_llm_response(prompts$reason, model_id = model_id, context = res$context)
  response_r <- res$response
  est_cost_usd <- est_cost_usd + calculate_cost(res$usage, model_id)
  log <- bind_rows(log, log_request(meta, "reason", prompts$reason, res))
  
  ## PARSE RESPONSES
  considerations <- parse_llm_response(response_c, 50, "C")
  policies <- parse_llm_response(response_p, 10, "P")
  reason <- parse_llm_response(response_r, 1, "R")
  
  validity <- is_valid_response(considerations, policies, survey_info)
  
  end_time <- Sys.time()
  time_s <- as.numeric(difftime(end_time, meta$created_at_utc, units = "secs"))
  
  llm_data_row <- tibble(
    meta,
    time_s,
    est_cost_usd,
    validity,
    considerations,
    policies,
    reason
  )
  
  ## write log
  # write_csv(llm_data_row, "pt2/data/llm_data_row.csv")
  
  ## append log to 
  if (file.exists("pt2/data/request_log.csv")) 
    write_csv(log, "pt2/data/request_log.csv", append = TRUE)
  else
    write_csv(log, "pt2/data/request_log.csv")
  
  
  # log result
  status <- if (validity$is_valid) "SUCCESS: " else "ERROR! "
  message(status,"LLM response generated in ", round(time_s, 1), "s")
  
  return(llm_data_row)
  
}



