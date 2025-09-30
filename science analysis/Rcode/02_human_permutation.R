library(readr)
library(dplyr)
library(knitr)

# input data files
HUMAN_DATA_FILE <- "../data/human_data.csv"

# output data files
FIGURES_DIR <- "../figures"
HUMAN_PERM_FILE <- "../data/human_perm_data.csv"
HUMAN_PERM_RES_FILE <- "../data/human_perm_test_results.csv"


N_PERMUTATIONS <- 10000 # number of permutations for human tests

source("dri_functions.R") # load dri functions

set.seed(123) # for replicability



res <- list()
perms <- list()
j <- 0

human_data <- read_csv(HUMAN_DATA_FILE, show_col_types = FALSE)
cases <- sort(unique(human_data$case))

for (case_name in cases) {
  
  # for progress checking
  j <- j + 1
  cat(paste0("[", j, "/", length(cases), "] ", "Starting: ", case_name, " - "))
  
  # get case data
  data_case <- human_data %>% filter(case == case_name)
  
  # get pre and post observed delta
  obs_pre_dri <- get_dri(data_case %>% filter(stage_id == 1))
  obs_post_dri <- get_dri(data_case %>% filter(stage_id == 2))
  
  # calculate delta
  obs_delta <- obs_post_dri - obs_pre_dri
  
  # initialize results
  df <- tibble(case = case_name,
               delta = obs_delta,
               source = "observed",)
  
  # get columns to shuffle
  shuffle_cols <- grep("^stage_id$", names(data_case), value = TRUE)
  
  # initialize shuffled data with original data
  shuffled_data <- data_case
  
  
  dri_shuffle <- list()
  time_start <- Sys.time()
  
  # permutation loop
  for (i in 1:N_PERMUTATIONS) {
    shuffled_data[shuffle_cols] <- shuffled_data[sample(1:nrow(shuffled_data)), shuffle_cols]
    
    pre_dri <- get_dri(shuffled_data %>% filter(stage_id == 1))
    post_dri <- get_dri(shuffled_data %>% filter(stage_id == 2))
    
    # GET DRI "PRE"
    dri_shuffle[[i]] <- tibble(
      case = case_name,
      delta = post_dri - pre_dri,
      source = "permutation",
      permutation = i,
    )
    
  }
  
  time_end <- Sys.time()
  
  elapsed_time <- as.numeric(difftime(time_end, time_start, units = "secs"))
  
  cat(paste0("elapsed time: ", round(elapsed_time, 2), "s\n"))
  
  dri_shuffle <- bind_rows(dri_shuffle)
  
  df <- bind_rows(df, dri_shuffle)
  
  perms[[length(perms) + 1]] <- df
  
  p <- nrow(dri_shuffle %>% filter(delta >= obs_delta)) / nrow(dri_shuffle)
  
  res[[length(res) + 1]] <- tibble(
    case = case_name,
    N = nrow(data_case),
    observed_delta = obs_delta,
    mean_perm_delta = mean(dri_shuffle$delta, na.rm = TRUE),
    p = p,
    elapsed_time_s = elapsed_time,
  )
  
}

res <- bind_rows(res)
perms <- bind_rows(perms)

# write output
write_csv(perms, HUMAN_PERM_FILE)
write_csv(res, HUMAN_PERM_RES_FILE)


# save plot
perms %>%
  gghistogram(
    x = "delta",
    facet.by = "case",
    fill = "source",
    add = "mean",
    rug = TRUE,
    title = "Human-Only Permutation Test",
    subtitle = "Pre/Post-Deliberation Delta DRI",
    ylab = "Permutation Count",
    xlab = "Pre - Post Deliberation DRI Delta",
    caption = paste(N_PERMUTATIONS, "permutations"),
  ) -> plot

plot

ggsave(paste(FIGURES_DIR, "human_perm.png", sep = "/"),
       plot,
       width = 10,
       height = 6)
 