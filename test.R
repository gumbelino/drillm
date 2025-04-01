
library(readxl)
library(tidyverse)


process_excel_file <- function(file_path) {
  # Load all sheets from the Excel file
  sheet_names <- excel_sheets(file_path)
  
  # Iterate over each sheet in the workbook
  for (sheet_name in sheet_names) {
    cat("Processing sheet:", sheet_name, "\n")
    
    # Read the current sheet into a data frame
    df <- read_excel(file_path, sheet = sheet_name)
    
    # Check if required columns exist
    required_columns <- c("considerations", "scale_max", "q-method")
    missing_cols <- setdiff(required_columns, colnames(df))
    if (length(missing_cols) > 0) {
      cat(
        "Sheet",
        sheet_name,
        "is missing the following columns:",
        paste(missing_cols, collapse = ", "),
        "\n\n"
      )
      next
    }
    
    # Calculate the number of non-NA rows in "considerations" column
    n_c <- sum(!is.na(df$considerations))
    
    # Calculate the number of non-NA rows in "policies" column
    n_p <- sum(!is.na(df$policies))
    
    # Extract integer values from "scale_max" column, assuming they are already integers
    scale_max <- as.integer(na.omit(df$scale_max))
    
    # Extract logical (boolean) values from "q-method" column
    q_method <- as.logical(na.omit(df$`q-method`))
    
    # Print the results for each sheet
    cat("Sheet:", sheet_name, "\n")
    cat("Number of considerations:", n_c, "\n")
    cat("Number of policies:", n_p, "\n")
    cat("Integer value from 'scale_max' column:", scale_max, "\n")
    cat("Logical value from 'q-method' column:", q_method, "\n")
    cat(rep("-", 40), "\n")
    
    
    ### Make random survey
    # Generate data for C1:C50 with Likert scale values [1, scale_max] randomly assigned
    if (q_method) {
      c_df <- data.frame(t(round(rnorm(n = n_c, mean = scale_max / 2, sd = scale_max / 4))))
    } else {
      c_df <- data.frame(t(replicate(n_c, sample(1:scale_max, 1, replace = TRUE))))
    }
    
    # fill and rename columns
    c_df[1, (n_c + 1):50] <- NA
    colnames(c_df) <- paste0("C", 1:50)
    
    # Generate data for P1:P10 with random unique ranks 1 to 7 for each row
    p_df <- data.frame(t(apply(matrix(0, nrow = 1, ncol = n_p), 1, function(x)
      sample(1:n_p))))#if you increase RF options also need to increase number of ranks
    p_df[1, (n_p + 1):10] <- NA
    colnames(p_df) <- paste0("P", 1:10)
    
    # Combine the two datasets into one data frame
    dataset <- as.data.frame(cbind(c_df, p_df))
    dataset <- dataset %>%
      mutate(survey = sheet_name) %>%
      relocate(survey, .before = 1)
    
    cat(dataset)
    
  }
}

# Example usage
process_excel_file(SURVEY_FILE)

seed(123)



sample_values[sample_values < 0] <- NA
sample_values[is.na(sample_values)] <- sample(0:11, sum(is.na(sample_values)), replace = TRUE)
sample_values

sampled_values <- rnorm(n = 5, mean = (0 + 11) / 2, sd = (11 - 0) / 4)
sampled_values[sampled_values < 0] <- 0
sampled_values[sampled_values > 11] <- 11
sampled_values

floor(rnorm(5) + 5.5)

  
  