

policies_data

na.omit(policies_data)
all_equal <- all(apply(policies_data, 1,
          function(row) all(row == policies_data[1,], na.rm = TRUE)),
    na.rm = TRUE)

