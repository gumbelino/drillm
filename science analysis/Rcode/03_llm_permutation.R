library(readr)
library(dplyr)
library(knitr)

# input data files
HUMAN_DATA_FILE <- "../data/human_data.csv"
DELIB_CASES_FILE <- "../data/deliberative_cases.csv"
LLM_DATA_FILE <- "../data/llm_data_clean.csv"

# output data files
FIGURES_DIR <- "../figures"
OUTPUT_DIR <- "../data"
LLM_PERM_FILE <- "../data/llm_perm_data.csv"
LLM_PERM_RES_FILE <- "../data/llm_perm_test_results.csv"


N_PERMUTATIONS <- 1000 # number of permutations for llm tests
LLM_ITERATIONS <- 5
SIG_LEVEL <- 0.05

source("dri_functions.R") # load dri functions

set.seed(123) # for replicability


res_llms <- list()
perms <- list()
j <- 0
m <- 0 

# select subset of data to analyse: post-deliberation
human_data <- read_csv(HUMAN_DATA_FILE, show_col_types = FALSE)
data <- human_data %>% filter(stage_id == 2)

# load llm data
llm_data <- read_csv(LLM_DATA_FILE, show_col_types = FALSE)

# select deliberative cases
deliberative_cases <- read_csv(DELIB_CASES_FILE, show_col_types = FALSE)

cases <- sort(unique(deliberative_cases$case))

model_names <- sort(unique(llm_data$model))

for (case_name in cases) {
  
  # for progress checking
  j <- j + 1
  cat(paste0("[",j,"/",length(cases),"] ", "Starting: ", case_name, "\n"))
  
  # get case data
  data_case <- data %>% filter(case == case_name)
  
  survey_case <- unique(data_case$survey)
  
  m <- 0
  for (model in model_names) {
    
    m <- m + 1
    cat(paste0("- [",m,"/",length(model_names),"] ", "Model: ", model, "\n"))
    
    # add LLM participant
    llm_case_data <- llm_data %>%
      filter(model == !!model, survey == survey_case)
    
    for (it in 1:LLM_ITERATIONS) {
      
      cat(paste0("- - [",it,"] "))
      
      llm_participant <- llm_case_data[it, ]
      llm_participant$pnum <- 0
      
      data_case_with_llm <- bind_rows(data_case, llm_participant)
      
      # get observed DRI
      obs_dri <- get_llm_dri(data_case_with_llm)
      
      if (is.na(obs_dri)) {
        warning("Observed DRI is NA!!")
        llm_participant
      }
      
      # initiate results
      df <- tibble(
        model = model,
        it = it,
        case = case_name,
        dri = obs_dri,
        source = "observed"
      )
      
      # get preferences
      pref_cols <- grep("^P\\d", names(data_case_with_llm), value = TRUE)
      shuffled_data <- data_case_with_llm
      
      dri_shuffle <- list()
      time_start <- Sys.time()
      
      # permutation loop
      for (i in 1:N_PERMUTATIONS) {
        shuffled_data[pref_cols] <- shuffled_data[sample(1:nrow(shuffled_data)), pref_cols]
        
        dri_shuffle[[i]] <- tibble(
          model = model,
          it = it,
          case = case_name,
          dri = get_dri(shuffled_data),
          source = "permutation",
          permutation = i,
        )
        
      }
      
      time_end <- Sys.time()
      
      elapsed_time <- as.numeric(difftime(time_end, time_start, units = "secs"))
      
      cat(paste0("elapsed time: ", round(elapsed_time, 2), "s, observed DRI = ", round(obs_dri, 3), "\n"))
      
      
      dri_shuffle <- bind_rows(dri_shuffle)
      
      df <- bind_rows(df, dri_shuffle)
      
      perms[[length(perms)+1]] <- df
      
      p <- nrow(dri_shuffle %>% filter(dri >= obs_dri)) / nrow(dri_shuffle)
      
      res_llms[[length(res_llms) + 1]] <- tibble(
        model = model,
        it = it,
        case = case_name,
        N = nrow(data_case),
        observed_dri = obs_dri,
        mean_perm_dri = mean(dri_shuffle$dri, na.rm = TRUE),
        p = p,
        elapsed_time_s = elapsed_time,
      )
      
      
    }
    
  }
  
}

res_llms <- bind_rows(res_llms)
perms <- bind_rows(perms)

write_csv(res_llms, LLM_PERM_RES_FILE)
write_csv(perms, LLM_PERM_FILE)

# perms %>%
#   gghistogram(
#     x = "dri",
#     facet.by = c("model", "case"),
#     fill = "source",
#     add = "mean",
#     rug = TRUE,
#     title = "Permutation test",
#     subtitle = "Post-deliberation DRI",
#     caption = paste(ITERATIONS, "iterations"),
#   ) -> plot
# 
# plot
#   
# ggsave(
#   paste(OUTPUT_DIR, "plots", paste0("all-llm-perm.png"), sep = "/"),
#   plot,
#   width = 15,
#   height = 6
# )

# write summary
res_llms %>%
  filter(!is.na(observed_dri)) %>%
  group_by(model) %>%
  summarise(
    N = n(),
    sig.count = sum(p < SIG_LEVEL),
    sig.rate = sig.count / N,
  ) %>%
  arrange(-sig.rate) %>%
  write_csv(paste0(
    OUTPUT_DIR, "/",
    LLM_ITERATIONS,"-responses_",
    N_PERMUTATIONS, "-perms_",
    length(model_names),"-models_summary.csv"))


res_llms %>%
  group_by(model) %>%
  summarise(
    N = n(),
    sig.count = sum(p < SIG_LEVEL),
    sig.rate = sig.count / N,
  ) %>%
  arrange(-sig.rate)

