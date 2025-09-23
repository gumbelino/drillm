
library(tidyr)

df <- read_excel(SURVEY_FILE, sheet = "ccps")

c_df <- df %>% 
  mutate(sid = paste0("C", considerations_order),
         statement = considerations) %>%
  select(sid, statement) %>%
  filter(!is.na(statement))

p_df <- df %>% 
  mutate(sid = paste0("P", policies_order),
         statement = policies) %>%
  select(sid, statement) %>%
  filter(!is.na(statement))


