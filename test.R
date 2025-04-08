# Create a sample data frame with one row of 50 random numbers between 1 and 7
set.seed(123) # For reproducibility
data <- tibble(C1 = sample(1:7, 50, replace = TRUE))

# Plot the histogram for the distribution of numbers in this row
ggplot(data, aes(x = C1)) +
  geom_histogram(bins = 7, fill = "blue", color = "black") +
  labs(title = "Distribution of Numbers from 1 to 7",
       x = "Number",
       y = "Frequency")