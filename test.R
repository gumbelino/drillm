
library(boot)

# Function to calculate mode of data, same as stat_function
calc_mode <- function(data) {
  as.numeric(names(sort(table(data), decreasing = TRUE)[1]))
}

bootstrap_mode <- function(data, n_bootstrap = 1000) {
  
  # Return NA if data contains any NA
  if (any(is.na(data))) {
    return(NA)
  }
  
  # Define the statistic function for bootstrapping to find mode
  stat_function <- function(data, indices) {
    as.numeric(names(sort(table(data[indices]), decreasing = TRUE)[1]))
  }
  
  # Perform bootstrap
  results <- boot(data = data, statistic = stat_function, R = n_bootstrap)
  
  # Calculate bootstrapped mode
  b_mode <- calc_mode(results$t)
  
  # Return the bootstrapped modes
  return(b_mode)
}

# Example usage:
# bootstrap_mode(c(1, 2, 3, 4, 5, 5))

# Example usage:
test <- c(1, 2, 3, 4, 5, 5)
calc_mode(test)
mode <- bootstrap_mode(test)
b_mode <- calc_mode(modes)


aggregate_llm_considerations <- function(considerations) {
  # Ensure there are columns to aggregate
  if (ncol(considerations) == 0) {
    return(tibble())
  }
  
  # Calculate the mode for each column
  mode_considerations <- considerations %>%
    summarise(across(everything(), bootstrap_mode))
  
  return(mode_considerations)
  
}

df <- tibble(
  C1 = c(1, 2, 3, 4, 5, 5),
  C2 = c(1, 1, 1, 4, 5, 5),
  C3 = c(1, 2, 2, 2, 5, 5),
  C4 = NA
)

df

aggregate_llm_considerations(df)



print(modes)


# Define a function to calculate column means
column_modes <- function(data, indices) {
  # Subset the data based on bootstrap sample indices
  d <- data[indices, ]
  
  # Calculate and return the mean of each column
  colModes(d)
}

# Perform bootstrapping with 1000 replications
set.seed(123)  # For reproducibility
boot_results <- boot(data = df, statistic = column_modes, R = 1000)

# View results
print(boot_results)

print(boot_results$)

