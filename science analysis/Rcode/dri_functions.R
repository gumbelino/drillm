calculate_dri <- function(data, v1, v2) {
  d <- abs((data[[v1]] - data[[v2]]) / sqrt(2))
  lambda <- 1 - (sqrt(2) / 2)
  
  # Scalar penalty based on strength of signal (|r| and |q|)
  penalty <- ifelse(pmax(abs(data[[v1]]), abs(data[[v2]])) <= 0.2, pmax(abs(data[[v1]]), abs(data[[v2]])) / 0.2, 1)
  
  consistency <- (1 - d) * penalty
  avg_consistency <- mean(consistency)
  
  dri <- 2 * ((avg_consistency - lambda) / (1 - lambda)) - 1
  
  return(dri)
}

get_dri <- function(data) {
  if (nrow(data) < 1) {
    return(NA)
  }
  
  pnums <- data$pnum
  
  Q <- data %>% select(C1:C50)
  R <- data %>% select(P1:P10)
  
  # remove all NA columns (in case there are less than 50
  Q <- Q[, colSums(is.na(Q)) != nrow(Q)]
  R <- R[, colSums(is.na(R)) != nrow(R)]
  
  # transpose data
  Q <- t(Q) %>% as.data.frame()
  R <- t(R) %>% as.data.frame()
  
  # name columns with participant numbers
  colnames(Q) <- pnums
  colnames(R) <- pnums
  
  # obtain a list of correlations without duplicates
  # cor() returns a correlation matrix between Var1 and Var2
  # Var1 and Var2 are the variables being correlated
  # Freq is the correlation
  QWrite <- subset(as.data.frame(as.table(cor(Q, method = "spearman"))),
                   match(Var1, names(Q)) > match(Var2, names(Q)))
  
  RWrite <- subset(as.data.frame(as.table(cor(R, method = "spearman"))),
                   match(Var1, names(R)) > match(Var2, names(R)))
  
  # initialize the output in the first iteration
  IC <- data.frame("P_P" = paste0(QWrite$Var1, '-', QWrite$Var2))
  IC$P1 <- as.numeric(as.character(QWrite$Var1))
  IC$P2 <- as.numeric(as.character(QWrite$Var2))
  
  # prepare QWrite
  QWrite <- as.data.frame(QWrite$Freq)
  names(QWrite) <- "Q2"
  
  # prepare RWrite for merge
  RWrite <- as.data.frame(RWrite$Freq)
  names(RWrite) <- "R2"
  
  # merge
  IC <- cbind(IC, QWrite, RWrite)
  
  ## IC Points calculations ##
  IC$IC_POST <- 1 - abs((IC$R2 - IC$Q2) / sqrt(2))
  
  ## Group DRI level V3 ##
  DRI_POST_V3 <- calculate_dri(IC, 'R2', 'Q2')
  
  return(DRI_POST_V3)
  
}

get_ind_dri <- function(data) {
  if (nrow(data) < 1) {
    return(NA)
  }
  
  pnums <- data$pnum
  
  Q <- data %>% select(C1:C50)
  R <- data %>% select(P1:P10)
  
  # remove all NA columns (in case there are less than 50
  Q <- Q[, colSums(is.na(Q)) != nrow(Q)]
  R <- R[, colSums(is.na(R)) != nrow(R)]
  
  # transpose data
  Q <- t(Q) %>% as.data.frame()
  R <- t(R) %>% as.data.frame()
  
  # name columns with participant numbers
  colnames(Q) <- pnums
  colnames(R) <- pnums
  
  # obtain a list of correlations without duplicates
  # cor() returns a correlation matrix between Var1 and Var2
  # Var1 and Var2 are the variables being correlated
  # Freq is the correlation
  QWrite <- subset(as.data.frame(as.table(cor(Q, method = "spearman"))),
                   match(Var1, names(Q)) > match(Var2, names(Q)))
  
  RWrite <- subset(as.data.frame(as.table(cor(R, method = "spearman"))),
                   match(Var1, names(R)) > match(Var2, names(R)))
  
  # initialize the output in the first iteration
  IC <- data.frame("P_P" = paste0(QWrite$Var1, '-', QWrite$Var2))
  IC$P1 <- as.numeric(as.character(QWrite$Var1))
  IC$P2 <- as.numeric(as.character(QWrite$Var2))
  
  # prepare QWrite
  QWrite <- as.data.frame(QWrite$Freq)
  names(QWrite) <- "Q2"
  
  # prepare RWrite for merge
  RWrite <- as.data.frame(RWrite$Freq)
  names(RWrite) <- "R2"
  
  # merge
  IC <- cbind(IC, QWrite, RWrite)
  
  ## IC Points calculations ##
  IC$IC_POST <- 1 - abs((IC$R2 - IC$Q2) / sqrt(2))
  
  Plist <- unique(c(IC$P1, IC$P2))
  
  Plist <- Plist[order(Plist)]
  
  DRIInd <- data.frame('pnum' = Plist)
  
  #Add individual-level metrics
  for (i in 1:length(Plist)) {
    # calculate updated DRI V3
    DRIInd$DRIPostV3[i] <- calculate_dri(
      data = IC  %>% filter(P1 == Plist[i] | P2 == Plist[i]),
      v1 = 'R2',
      v2 = 'Q2'
    )
    
  }
  
  return(DRIInd)
  
}

get_llm_dri <- function(data) {
  ind_dri <- get_ind_dri(data)
  llm_ind_dri <- ind_dri %>% filter(pnum == 0)
  
  return(llm_ind_dri[1, 2])
  
}


add_llm_participant <- function(llm_survey_data, data) {
  # get llm data
  llm_participant <- llm_survey_data[it, ]
  
  # check if it exists
  if (nrow(llm_participant) == 0) {
    warning(paste(
      "No participant found for",
      paste(provider, model, survey, sep = "/")
    ))
  }
  
  # create 2 participants, PRE and POST
  llm_participants <- bind_rows(llm_participant, llm_participant)
  llm_participants$pnum <- 0 # PNum = 0 is LLM
  llm_participants$stage_id <- c(1, 2)
  
  data_with_llm <- bind_rows(data, llm_participants)
  
  return(data_with_llm)
  
}
