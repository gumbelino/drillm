
library(boot)



# Define the colModes function
colModes <- function(data) {
  # Function to calculate the mode of a single vector
  getMode <- function(x) {
    # Get unique values and their counts
    ux <- unique(x)
    freq <- tabulate(match(x, ux))
    
    # Find the maximum frequency
    max_freq <- max(freq)
    
    # Return all modes (in case of ties)
    modes <- ux[freq == max_freq]
    return(modes)
  }
  
  # Apply getMode to each column in the dataframe
  mode_list <- lapply(data, getMode)
  
  # Convert list to a data frame for easier viewing
  mode_df <- do.call(cbind, mode_list)
  
  return(mode_df)
}


aggregate_llm_policies_mode <- function(policies) {
  if (ncol(policies) == 0) {
    return(tibble())
  }
  
  
  b <- boot(policies, mean, 1000)
  
  
  
    mode_policies <- policies %>%
    summarise(across(everything(), calculate_mode))
  
  return(mode_policies)
}

df <- tibble(
  P1 = c(1,1,2),
  P2 = c(2,2,1),
  P3 = c(3,3,1),
  P4 = c(4,2,1)
)

df


# Calculate modes for each column
modes <- colModes(df)
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

