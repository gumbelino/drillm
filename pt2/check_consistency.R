library(readr)
library(dplyr)
library(psych)
library(knitr)
library(rstatix)

# input data files
LLM_DATA_FILE <- "pt2/data/llm_data_clean.csv"

# output data files
CONSISTENCY_RESULTS_FILE <- "pt2/data/consistency_results.csv"

if (file.exists(CONSISTENCY_RESULTS_FILE)) {
  stop(paste("File", CONSISTENCY_RESULTS_FILE, "already exists.",
             "Please delete file to regenerate it."))
}

# load llm data
llm_data <- read_csv(LLM_DATA_FILE, show_col_types = FALSE)

# Initialize an empty list to store the alpha results
consistency_results <- list()

models_with_data <- llm_data %>%
  distinct(provider, model) 

# Iterate over each unique provider/model combination
for (row in 1:nrow(models_with_data)) {
  provider <- models_with_data[row, ]$provider
  model <- models_with_data[row, ]$model
  
  # filter the data for the current provider/model
  provider_model_data <- llm_data %>%
    filter(model == !!model)
  
  # iterate over each survey
  for (survey_name in unique(provider_model_data$survey)) {
    
    # iterate over each prompt
    for (prompt_uid in unique(provider_model_data$prompt_uid)) {
      
      # filter the data for the current survey/prompt
      survey_prompt_data <- provider_model_data %>%
        filter(survey == !!survey_name, prompt_uid == !!prompt_uid)
      
      # Calculate Cronbach's Alpha for considerations
      considerations_data <- survey_prompt_data %>%
        select(matches("^C\\d+$") & where(~!all(is.na(.))))
      
      if (nrow(considerations_data) > 1) {
        
        # Check if policies are all equal (no variance)
        # this can happen when there are few iterations
        c_all_equal <- all(apply(considerations_data, 1, function(row)
          all(row == considerations_data[1, ], na.rm = TRUE)), na.rm = TRUE)
        
        # TODO: FIXME! 
        # NOTE: assign alpha = 1, which should NOT exist!
        # if (c_all_equal) {
        #   alpha_considerations <- 1
        # } else {
        alpha_considerations <- psych::alpha(
          considerations_data,
          check.keys = TRUE,
          warnings = FALSE,
        )$total$raw_alpha
        # }
      } else {
        alpha_considerations <- NA
      }
      
      # Calculate Cronbach's Alpha for policies
      policies_data <- survey_prompt_data %>%
        select(matches("^P\\d+$") & where(~!all(is.na(.))))
      
      if (nrow(policies_data) > 1) {
        
        # Check if policies are all equal (no variance)
        # this can happen when there are few iterations
        p_all_equal <- all(apply(policies_data, 1, function(row)
          all(row == policies_data[1, ], na.rm = TRUE)), na.rm = TRUE)
        
        # NOTE: assign alpha = 1, which should NOT exist!
        if (p_all_equal) {
          alpha_policies <- 1
        }
        
        # normal case, calculate alpha
        else {
        alpha_policies <- psych::alpha(
          policies_data,
          check.keys = TRUE,
          warnings = FALSE,
        )$total$raw_alpha
        }
      } else {
        alpha_policies <- NA
      }
      
      if (nrow(policies_data) > 1 && nrow(considerations_data) > 1) {
        all_data <- cbind(considerations_data, policies_data)
        alpha_all <- psych::alpha(
          all_data,
          check.keys = TRUE,
          warnings = FALSE,
        )$total$raw_alpha
      } else {
        alpha_all <- NA
      }
      
      
      # Store the results in the list
      consistency_results[[length(consistency_results) + 1]] <- tibble(
        provider = provider,
        model = model,
        survey = survey_name,
        prompt_uid,
        N = nrow(considerations_data),
        alpha_considerations = alpha_considerations,
        alpha_policies = alpha_policies,
        alpha_all = alpha_all
      )
      
    }
  }
}

# Combine all results into a single data frame
consistency_results <- bind_rows(consistency_results)

rm(models_with_data)
rm(considerations_data)
rm(survey_data)
rm(policies_data)
rm(provider_model_data)

# write summary to file
write_csv(consistency_results, CONSISTENCY_RESULTS_FILE)
