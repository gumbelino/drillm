
library(readxl)
library(tidyverse)


process_excel_file <- function(file_path) {
  # Load all sheets from the Excel file
  sheet_names <- excel_sheets(file_path)
  
  rand <- list()
  
  # Iterate over each sheet in the workbook
  for (sheet_name in sheet_names) {
    #cat("Processing sheet:", sheet_name, "\n")
    
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
    #cat("Sheet:", sheet_name, "\n")
    #cat("Number of considerations:", n_c, "\n")
    #cat("Number of policies:", n_p, "\n")
    #cat("Integer value from 'scale_max' column:", scale_max, "\n")
    #cat("Logical value from 'q-method' column:", q_method, "\n")
    
    
    ### Make random survey
    # Generate data for C1:C50 with Likert scale values [1, scale_max] randomly assigned
    if (q_method) {
      
      # get normally distributed data
      c_df <- data.frame(t(round(rnorm(n = n_c, mean = scale_max / 2, sd = scale_max / 4))))
      
      # replace values below lower and above upper bound
      c_df[c_df < 1] <- 1
      c_df[c_df > scale_max] <- scale_max
      
    } else {
      c_df <- data.frame(t(replicate(n_c, sample(1:scale_max, 1, replace = TRUE))))
    }
    
    # fill and rename columns
    c_df[1, (n_c + 1):50] <- NA
    colnames(c_df) <- paste0("C", 1:50)
    
    # Generate data for P1:P10 with random unique ranks 1 to n_p for each row
    p_df <- data.frame(t(apply(matrix(0, nrow = 1, ncol = n_p), 1, function(x)
      sample(1:n_p))))
    p_df[1, (n_p + 1):10] <- NA
    colnames(p_df) <- paste0("P", 1:10)
    
    # Validate data
    c_valid <- !(any(c_df < 1, na.rm = TRUE) || any(c_df > scale_max, na.rm = TRUE))
    p_valid <- !(any(duplicated(p_df[!is.na(p_df)])) ||
      any(p_df < 1, na.rm = TRUE) ||
      any(p_df > n_p, na.rm = TRUE))
  
    #cat("Valid considerations:", c_valid, "\n")
    #cat("Valid policies:", p_valid, "\n")
    
    if (c_valid || !p_valid) {
      warn(paste("Random generation produced invalid data for", survey_name))
    }
    
    # Combine the two datasets into one data frame
    dataset <- as.data.frame(cbind(c_df, p_df))
    dataset <- dataset %>%
      mutate(survey = sheet_name) %>%
      relocate(survey, .before = 1)
    
    rand[[length(rand) + 1]] <- dataset
    
    #cat(rep("-", 40), "\n")
    
    
  }
  
  rand <- bind_rows(rand)
  return(rand)
  
}

# Example usage
rand_data <- process_excel_file(SURVEY_FILE)
