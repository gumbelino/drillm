
data <- tibble(
  C1 = c(1,2,3,4),
  C2 = c(1,2,3,4),
  C3 = c(1,2,3,4),
  P1 = c(1,2,3,4),
  P2 = c(1,2,3,4),
  P3 = c(1,2,3,4),
  PId = c(1,2,3,4),
)

# shuffle the dataframe by rows
pref_cols <- grep("^P\\d", names(data), value = TRUE)
shuffled_data <- data
shuffled_data[pref_cols] <- shuffled_data[sample(1:nrow(shuffled_data)), pref_cols]

