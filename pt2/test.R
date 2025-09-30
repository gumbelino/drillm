
# source("pt2/get_dri_llm_response.R")

library(devtools)
install_github("gumbelino/deliberr", force = TRUE)
library(deliberr)

ls("package:deliberr")

# copy model id from openrouter.ai
model_id <- "google/gemini-2.0-flash-001"
survey_name <- "ccps"
role_uid <- "csk"

library(dplyr)

api_key <- Sys.getenv("OPENROUTER_API_KEY")
# Sys.setenv(OPENROUTER_API_KEY = "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")

survey_info <- get_dri_survey_info("ccps")

.shuffle_statements <- function(survey_info) {
  survey_info$considerations <- survey_info$considerations %>%
    mutate(order = sample(order))
  survey_info$policies <- survey_info$policies %>%
    mutate(order = sample(order))
  survey_info
}

shuffled_info <- .shuffle_statements(survey_info)


## TODO: deal with invalid responses; pnums; error messages
llm_data <- get_dri_llm_response(model_id, survey_name, role_uid, n = 10)

llm_data$pnum <- rownames(llm_data)

ic <- get_dri_ic(llm_data)

plot_dri_ic(ic, dri = get_dri(ic))

