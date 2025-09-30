
library(readr)
library(readxl)
library(dplyr)

SURVEY_FILE <- "data/surveys_v5.xlsx"

get_dri_survey_info <- function(survey_name = NA) {
  
  # read the sheet names of the Excel file
  survey_names <- excel_sheets(SURVEY_FILE)
  
  if (!is.na(survey_name)) {
    survey_names <- survey_names[survey_names == survey_name]
  } else {
    # remove invalid and "template" 
    survey_names <- sort(survey_names[!grepl("^~", survey_names) & survey_names != "template"])
  }
  
  surveys <- list()
  
  # Iterate over each sheet in the workbook
  for (sn in survey_names) {
    
    # Read the current sheet into a data frame
    df <- read_excel(SURVEY_FILE, sheet = sn)
    
    # Check if required columns exist
    required_columns <- c("considerations", "policies", "scale_max", "q-method")
    missing_cols <- setdiff(required_columns, colnames(df))
    if (length(missing_cols) > 0) {
      cat(
        "Sheet",
        sn,
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
    
    # get considerations
    c_df <- df %>% 
      mutate(sid = paste0("C", considerations_order),
             statement = considerations) %>%
      select(sid, statement) %>%
      filter(!is.na(statement))
    
    # get considerations
    p_df <- df %>% 
      mutate(sid = paste0("P", policies_order),
             statement = policies) %>%
      select(sid, statement) %>%
      filter(!is.na(statement))
    
    surveys[[length(surveys) + 1]] <- list(
      survey_name = sn,
      considerations = c_df,
      policies = p_df,
      scale_max = scale_max,
      q_method = q_method
    )
    
  }

  surveys
  
}


# surveys <- get_dri_survey_info(survey_name = "ccps")
# 
# for (survey_info in surveys) {
#   print(survey_info$considerations)
# }


