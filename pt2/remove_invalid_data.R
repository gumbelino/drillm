#' Remove Rows with Constant Non-NA Values
#'
#' This function checks each row of a data frame. For the columns C1 through C50,
#' it ignores any NA values and checks if all the remaining (non-NA) values
#' in that slice are identical. If they are, the entire row is removed.
#' Columns containing all NAs are ignored by this process and are not removed.
#'
#' @param df A data frame.
#' @return A data frame with the identified rows removed.
#' @examples
#' df_test <- data.frame(
#'   ID = 1:5,
#'   C1 = c(8, 8, NA, 1, 5),
#'   C2 = c(NA, NA, NA, 2, 5),
#'   C3 = c(8, 9, NA, 3, 5),
#'   C4 = c(8, 8, NA, 4, 5),
#'   C43 = rep(NA, 5) # This all-NA column is now kept
#' )
#' # Row 1 has non-NA values of (8, 8, 8) -> constant, will be removed.
#' # Row 5 has non-NA values of (5, 5, 5, 5) -> constant, will be removed.
#' remove_invalid_data(df_test)

remove_invalid_data <- function(df) {
  
  # 1. Define the columns to check
  cols_to_check <- paste0("C", 1:50)
  cols_in_df <- intersect(cols_to_check, names(df))
  
  # Stop if no target columns exist
  if (length(cols_in_df) == 0) {
    message("ℹ️ No target columns (C1-C50) found. No changes made.")
    return(df)
  }
  
  # 2. Identify rows with a single unique non-NA value across the target columns
  rows_are_constant_sans_na <- apply(df[, cols_in_df, drop = FALSE], 1, function(row) {
    # Isolate the non-NA values from the row slice
    non_na_values <- row[!is.na(row)]
    
    # A row is "constant" if there's exactly one unique non-NA value.
    # If a row has only NAs in these columns, `length(unique(non_na_values))` will be 0.
    # This ensures rows with only NAs are kept.
    return(length(unique(non_na_values)) == 1)
  })
  
  # 3. Remove the identified rows and provide feedback
  num_removed <- sum(rows_are_constant_sans_na)
  
  if (num_removed > 0) {
    message(paste("🗑️ Removed", num_removed, "rows where non-NA values were constant across columns", 
                  paste(cols_in_df, collapse=", ")))
    df_final <- df[!rows_are_constant_sans_na, ]
  } else {
    message("👍 No rows found with constant non-NA values across the specified columns.")
    df_final <- df
  }
  
  return(df_final)
}