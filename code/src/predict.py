#Authors: Anantha Raghuraman and Asish Ghoshal
#Date: Nov, 2013
#Filename: predict.py
#Description: Use graphical modelling to predict the relevance of a particular search result, for that user and query terms
#Model: ti is ith query term. Assume that t1, t2 etc are independent. Choose Pr(R,D,T) as max of Pr(R,D,ti) for all i, where 
# R is relevance, can be 0, 1 or 2 and D is Dwell time. 
#

'''
 D <--- T
  \    /
   \  /
     R
Pr(R|D,T) = max t \in Q, Pr(R|D,t)Pr(D|t)Pr(t)
'''

#!/usr/bin/python

import sys
from collections import OrderedDict

RESULT_COUNT = 10
OUTPUT_FORMAT = {
  "experiment": ["SessionID", "URLID", "Actual", "Predicted"], #Headers
  "actual": ["SessionID", "URLID"]}  # Experiment is used for experimenting, actual is used for submission

# Attribute indices
IDX_USER_ID = 0
IDX_SESSION_ID = 1
IDX_SERP_ID	=2
IDX_QUERY_ID =3
IDX_QUERY_TIME_PASSED = 4
IDX_QUERY_TERMS = 5
IDX_URLS = 6
IDX_DOMAINS = 7
IDX_CLICK_TIME_PASSED = 8
IDX_DWELL_TIME = 9


def printUsageAndExit():
  print "Usage: %s <training file> <test file> <output format: experiment/actual>"%(sys.argv[0])
  sys.exit(1)

def predict(trainFile, testFile, outputFile, outputFormat):
  trainFd = open(trainFile, 'rU')
  testFd = open(testFile, 'rU')
  outputFd = open(outputFile, 'w')
  sessionCount = 0
  currentUser = -1
  probabilities = None
  longTermTrain = None

  #Write the header first
  outputFd.write("%s\n"%(",".join(OUTPUT_FORMAT[outputFormat])))

  while True:
    data = readData(trainFd, testFd)

    #Added for logging
    sessionCount += 1
    if sessionCount % 10000 == 0:
      print "%d test sessions processed."%sessionCount

    if not data:
      break

    userId = data["test"][0][IDX_USER_ID]
    #In the first iteration we'll get both long term and short term data.
    #In subsequent calls if the user hasn't changed we may only get short term data but no long term data
    #So we need to store the long term data for the current user. The long term data doesn't change across
    #sessions.
    if currentUser != userId:
      longTermTrain = data["longTermTrain"]
      probabilities = None # Recompute probabilities since this is a new user
      currentUser = userId
    elif data["shortTermTrain"]:
      probabilities = None # Recompute probabilities since we have some new short term data
      data["longTermTrain"] = longTermTrain


    if not probabilities:
      probabilities = computeProbabilities(data["shortTermTrain"], data["longTermTrain"])

    (orderedResults, urlMap) = rankResults(data["test"], probabilities)
    sessionId = data["test"][0][IDX_SESSION_ID]
    index = 0
    for url in orderedResults:
      if outputFormat == "actual":
        outputFd.write("%s,%s\n"%(sessionId, url))

      elif outputFormat == "experiment":
        dwellTime = data["test"][index][IDX_DWELL_TIME]
        actualRelevance = computeRelevance(dwellTime)
        predictedRelevance = urlMap[url]
        outputFd.write("%s,%s,%d,%d\n"%(sessionId, url, actualRelevance, predictedRelevance))
        index += 1
        
      else:
        raise Exception("Invalid output format: %s"%outputFormat)

  trainFd.close()
  testFd.close()
  outputFd.close()

def computeRelevance(dwellTime):
  ''' Computes the relevance. Relevance is 2 if dwellTime >= 400, 1 if dwellTime 
      is between 50 and 399. Otherwise relevance is 0 '''
  dwellTime = max(map(int, dwellTime.split(",")))
  if dwellTime == 0: # Since this is the most frequent case. Short circuit the check to make the check faster.
    return 0
  if dwellTime >= 400:
    return 2
  elif dwellTime >= 50:
    return 1
  return 0

def rankResults(testData, probabilities):
  orderedResults = OrderedDict()
  (topics, domainTopics, relevanceDomainTopics) = probabilities 
  for data in testData:
    relevance = [0, 0, 0] # Relevance = 0, 1, 2
    terms = data[IDX_QUERY_TERMS]
    terms = terms.split(",")
    domain = data[IDX_DOMAINS]
 
    for term in terms:
      if term not in topics:
        continue
      if (domain, term) not in domainTopics:
        continue
      rel = computeRelevanceProbability(relevanceDomainTopics.get((0, domain, term), 0),
                                        domainTopics[(domain, term)],
                                        topics[term])
      relevance[0] = max(rel, relevance[0])
      
      rel = computeRelevanceProbability(relevanceDomainTopics.get((1, domain, term), 0),
                                        domainTopics[(domain, term)],
                                        topics[term])
      relevance[1] = max(rel, relevance[1])

      rel = computeRelevanceProbability(relevanceDomainTopics.get((2, domain, term), 0),
                                        domainTopics[(domain, term)],
                                        topics[term])
      relevance[2] = max(rel, relevance[2])

    maxRelevance = max(relevance)
    rank = 0
    if maxRelevance != 0:
      for index in range(0, len(relevance)):
        if maxRelevance == relevance[index]:
          rank = index

    orderedResults[data[IDX_URLS]] = rank
    
  return (sorted(orderedResults.keys(), key=lambda x: orderedResults[x], reverse=True), orderedResults)

def computeRelevanceProbability(relevanceDomainTopic, domainTopic, topic):
  probability = float(relevanceDomainTopic) / (float(domainTopic))
  return probability

def computeProbabilities(shortTermTrain, longTermTrain):
  ''' Compute the conditional probability tables. Currently the short term training data is treated the same
      way as long term data. The probabilities are approximated by counts 
      since the probabilities are proportional to the count.'''
  topics = {} # For Pr(T)
  domainTopics = {} # For Pr(D, T)
  relevanceDomainTopics = {} # For Pr(R, D, T)
  
  for data in (shortTermTrain + longTermTrain):
    terms = data[IDX_QUERY_TERMS]
    terms = terms.split(",")
    domain = data[IDX_DOMAINS]
    relevance = computeRelevance(data[IDX_DWELL_TIME])
    for term in terms:
      count = topics.get(term, 0)
      topics[term] = count +1
      count = domainTopics.get((domain,term), 0)
      domainTopics[(domain, term)] = count +1
      count = relevanceDomainTopics.get((relevance, domain, term), 0)
      relevanceDomainTopics[(relevance, domain, term)] = count +1
  

  return (topics, domainTopics, relevanceDomainTopics)

def readData(trainFd, testFd):
  '''
    Reads short term traing, long term training and test data for each user. 
    Everytime the function is called data for a new user is read.
  '''
  data = {}
  shortTermTrain = []
  longTermTrain = []
  test = []

  testCurrentPos = testFd.tell() # Where we are currently in the test file.
  trainCurrentPos = trainFd.tell() # Where we are currently in the train file.

  testLine = testFd.readline()
  if not testLine:
    return None

  testLine = testLine.strip()
  testLine = testLine.split()
  recordType = testLine.pop(4) # 4 Corresponds to the type column in the test data
  testUserId = int(testLine[IDX_USER_ID])
  testSessionId = testLine[IDX_SESSION_ID]
  testFd.seek(testCurrentPos) # GO back to the previous line

  while True: #Using the for each loop doesn't work with seek/tell. So read line by line.
    line = testFd.readline()
    if not line:
      break

    line = line.strip()
    line = line.split()
    recordType = line.pop(4) # 4 Corresponds to the type column in the test data
    sessionId = line[IDX_SESSION_ID]

    if sessionId != testSessionId:
      #We have read a line from the next Session. Move back the cursor to the previous line and break.
      testFd.seek(testCurrentPos)
      break;
    
    if recordType == "TEST":
      # This is the test data which we need to predict.
      test.append(line)
    elif recordType == "TRAIN":
      # This is the short term training data
      shortTermTrain.append(line)
    testCurrentPos = testFd.tell()

  #Get training data for userId from training file.
  while True:
    line = trainFd.readline()
    if not line:
      break
    line = line.strip()
    line = line.split()
    userId = int(line[IDX_USER_ID])
    if userId > testUserId:
      # We have read data for the next user. Go back to the previous line and break.
      trainFd.seek(trainCurrentPos)
      break
    elif userId == testUserId:
      longTermTrain.append(line)
    trainCurrentPos = trainFd.tell()
   
  data["test"] = test
  data["shortTermTrain"] = shortTermTrain
  data["longTermTrain"] = longTermTrain
  return data

def main():
  if len(sys.argv) != 4:
    printUsageAndExit()

  trainFile = sys.argv[1]
  testFile = sys.argv[2]
  outputFormat = sys.argv[3]
  if outputFormat not in OUTPUT_FORMAT:
    raise Exception("Invalid output Format %s. Has to be either %s"%(",".join(OUTPUT_FORMAT.keys())))

  outputFile = "%s.predict"%testFile

  predict(trainFile, testFile, outputFile, outputFormat)
  

if __name__ == '__main__':
  sys.exit(main())

