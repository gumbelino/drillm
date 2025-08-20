library(readr)
PROMPTS_FILE <- "prompts/prompts.csv"

source("pt2/get_llm_data.R", echo = FALSE)

llm_data <- read_csv("pt2/data/llm_data_clean.csv", show_col_types = FALSE)

progress <- llm_data %>%
  group_by(model, survey, prompt_uid) %>%
  summarise(N = n())

prompts <- read_csv(PROMPTS_FILE, show_col_types = FALSE)
survey_names <- unique(cases$survey)

# only include "included" models
models <- models %>% filter(included)

for (uid in unique(prompts$uid)) {
  
  for (survey in survey_names) {
    
    for (model in models$model) {
      
      # if model/survey/uid doesn't exist,
      n <- progress %>% filter(prompt_uid == uid, survey == !!survey, model == !!model) %>% nrow()
      if (n == 0) {
        new_row <- tibble(
          model,
          survey,
          prompt_uid = uid,
          N = 0
        )
        progress <- bind_rows(progress, new_row)
      }
      
    }
    
  }
  
}

write_csv(progress, "pt2/data/progress.csv")