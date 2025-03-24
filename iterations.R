

it <- 8
inc <- 5

mf <- llm_surveys %>% filter(N >= it*inc)
res <- list()

for (row in 1:nrow(mf)) {
  
  provider <- mf[row,]$provider
  model <- mf[row,]$model
  survey <- mf[row,]$survey
  
  df <- llm_data %>%
    filter(provider == !!provider, model == !!model, survey == !!survey) %>%
    arrange(created_at)
  
  for (i in 1:it) {
    
    print(paste(provider,model,survey,i, sep = "/"))
    
    # get incremental data
    inc_df <- head(df, i*inc)
    
    # c and p data
    c_df <- inc_df %>% select(C1:C50)
    p_df <- inc_df %>% select(P1:P10)
    
    # calculate alphas
    alpha_c <- alpha(c_df, check.keys = TRUE, warnings = FALSE)$total$raw_alpha
    alpha_p <- alpha(p_df, check.keys = TRUE, warnings = FALSE)$total$raw_alpha
    
    # aggregate data
    agg_c <- aggregate_llm_considerations(c_df)
    agg_p <- aggregate_llm_policies(p_df)
    
    # get for differences
    if (i == 1) {
      c_diff <- NA
      p_diff <- NA
      num_c_diff <- NA
      num_p_diff <- NA
    } else {
      
      # get previous row data
      prev_i <- ((row - 1) * it) + i - 1
      prev_row <- res[[prev_i]]
      
      # check if comparing the right values
      if (prev_row$i != i - 1 || prev_row$survey != survey) {
        warn("SOMETHING IS WRONG!")
        break
      }
      
      c_diff <- alpha_c - prev_row$alpha_c
      p_diff <- alpha_p - prev_row$alpha_p
      num_c_diff <- sum(agg_c != prev_row %>% select(C1:C50), na.rm = TRUE)
      num_p_diff <- sum(agg_p != prev_row %>% select(P1:P10), na.rm = TRUE)
    }

    # save result
    res[[length(res) + 1]] <- tibble(
      mf[row,1:3],
      i = i,
      N = nrow(inc_df),
      alpha_c = alpha_c,
      alpha_p = alpha_p,
      c_diff = c_diff,
      p_diff = p_diff,
      num_c_diff = num_c_diff,
      num_p_diff = num_p_diff,
      agg_c,
      agg_p,
    )
    
  }
  
}

res <- bind_rows(res)

res <- res %>%
  mutate(label = paste(model, survey, sep="/"))

# Assuming your data frame is named df
plot <- ggplot(res, aes(x = N)) +
  # Add points and smooth line for num_c_diff in red
  geom_point(aes(y = num_c_diff, color = "num_c_diff")) +
  geom_smooth(aes(y = num_c_diff, color = "num_c_diff"), method = "loess", se = FALSE) +
  
  # Add points and smooth line for num_p_diff in blue
  geom_point(aes(y = num_p_diff, color = "num_p_diff")) +
  geom_smooth(aes(y = num_p_diff, color = "num_p_diff"), method = "loess", se = FALSE) +
  
  # Facet by model to create separate plots per category
  facet_wrap(~ label) +
  
  # Add labels and theme for better visualization
  labs(title = "Comparison of aggregated LLM data across models/surveys",
       x = "Number of iterations",
       y = "Number of differences (from previous 10 iterations)") +
  theme_minimal() +
  theme(
    plot.background = element_rect(fill = "white"))

ggsave(paste(OUTPUT_DIR, "iterations_num_diff.png", sep = "/"), plot, width = 10, height = 6)


# Assuming your data frame is named df
plot <- ggplot(res, aes(x = N)) +
  # Add points and smooth line for alpha_c in red
  geom_point(aes(y = alpha_c, color = "alpha_c")) +
  geom_smooth(aes(y = alpha_c, color = "alpha_c"), method = "loess", se = FALSE) +
  
  # Add points and smooth line for alpha_p in blue
  geom_point(aes(y = alpha_p, color = "alpha_p")) +
  geom_smooth(aes(y = alpha_p, color = "alpha_p"), method = "loess", se = FALSE) +
  
  # Facet by model to create separate plots per category
  facet_wrap(~ label) +
  
  # Add labels and theme for better visualization
  labs(title = "Comparison of Cronbach's alpha (considerations & policies) across models/surveys",
       x = "Number of iterations",
       y = "Cronbach's alpha") +
  theme_minimal() +
  theme(
    plot.background = element_rect(fill = "white"))

ggsave(paste(OUTPUT_DIR, "iterations_alpha.png", sep = "/"), plot, width = 10, height = 6)

