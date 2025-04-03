
# helper function to calculate mode of data, same as stat_function
calc_mode <- function(data) {
  as.numeric(names(sort(table(data), decreasing = TRUE)[1]))
}

# function to bootstrap mode
bootstrap_mode <- function(data, n_bootstrap = 1000) {
  # return NA if data contains any NA
  if (any(is.na(data))) {
    return(NA)
  }
  
  # define the statistic function for bootstrapping to find mode
  stat_function <- function(data, indices) {
    as.numeric(names(sort(table(data[indices]), decreasing = TRUE)[1]))
  }
  
  # perform bootstrap
  results <- boot(data = data,
                  statistic = stat_function,
                  R = n_bootstrap)
  
  # calculate bootstrapped mode
  b_mode <- calc_mode(results$t)
  
  # return the bootstrapped modes
  return(b_mode)
}

aggregate_llm_considerations <- function(considerations) {
  # ensure there are at least 2 rows to aggregate
  if (nrow(considerations) < 2) {
    return(considerations)
  }
  
  # Calculate the mode for each column
  mode_considerations <- considerations %>%
    summarise(across(everything(), bootstrap_mode))
  
  return(mode_considerations)
  
}

aggregate_llm_policies <- function(policies) {
  # ensure there are at least 2 rows to aggregate
  if (nrow(policies) < 2) {
    return(policies)
  }
  
  # Remove columns with NAs
  valid_policies <- policies[, colSums(is.na(policies)) != nrow(policies)]
  
  # Convert the policies to a ranked matrix
  ranked_matrix <- as.matrix(valid_policies)
  
  # Define the number of winners to all - 1 policies
  # stv complains if winners == all policies
  num_winners <- ncol(valid_policies) - 1
  
  # Run the Single Transferable Vote algorithm
  results <- stv(ranked_matrix, num_winners, quiet = TRUE)
  
  # add last policy to ranked result
  last_policy <- setdiff(colnames(valid_policies), results$elected)
  ranked_policies <- c(results$elected, last_policy)
  
  policy_order <- colnames(valid_policies)
  
  order <- match(policy_order, ranked_policies)
  
  # calculate the number of missing values needed to reach length 10
  missing_columns <- ncol(policies) - length(order)
  
  # fill in the missing values with NA
  order <- c(order, rep(NA, missing_columns))
  
  # create a new data frame with aggregated results
  policy_ranks <- data.frame(t(order))
  colnames(policy_ranks) <- colnames(policies)
  
  return(policy_ranks)
}

aggregate_llm_data <- function(data) {
  
  # initialize an empty list to store the alpha results
  aggregation_results <- list()
  
  # iterate over each unique provider/model/survey combination
  for (row in 1:nrow(llm_surveys)) {
    provider <- llm_surveys[row, ]$provider
    model <- llm_surveys[row, ]$model
    survey <- llm_surveys[row, ]$survey
    N <- llm_surveys[row, ]$N
    
    # filter the data for the current survey
    survey_data <- data %>%
      filter(model == !!model, survey == !!survey)
    
    # get only first x iterations, where x = MAX_ITERATIONS
    arrange(created_at) %>%
      head(MAX_ITERATIONS)
    
    # aggregate considerations C1:C50
    considerations_data <- survey_data %>% select(C1:C50)
    aggregated_considerations <- aggregate_llm_considerations(considerations_data)
    
    # aggregate policies P1:P10
    policies_data <- survey_data %>% select(P1:P10)
    aggregated_policies <- aggregate_llm_policies(policies_data)
    
    # store the results in the list
    aggregation_result <- tibble(
      provider = provider,
      model = model,
      survey = survey,
      N = N,
      date = Sys.time(),
      aggregated_considerations,
      aggregated_policies,
    )
    
    aggregation_results[[length(aggregation_results) + 1]] <- aggregation_result
    
  }
  
  
  # Combine all results into a single data frame
  aggregation_results <- bind_rows(aggregation_results)
  
  return(aggregation_results)
  
}

time_start <- Sys.time()
llm_data_aggregated <- aggregate_llm_data(llm_data)
time_end <- Sys.time()
elapsed_time <- difftime(time_end, time_start, units = "auto")

print(paste("Aggregation of", nrow(llm_data), "LLM responses across", length(unique(llm_data$survey)) ,"surveys completed in", round(as.numeric(elapsed_time),2), units(elapsed_time)))

print(head(llm_data_aggregated))

# write aggregated data to file
write_csv(llm_data_aggregated, paste(OUTPUT_DIR, "llm_data_aggregated.csv", sep = "/"))

round(as.numeric(elapsed_time),2)


