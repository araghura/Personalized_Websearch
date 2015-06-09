#Authors: Anantha Raghuraman and Asish Ghoshal
#Date: Nov, 2013
#Filename: generate_test_data.py
#Description:
#Splits training data into training and test by randomly sampling data to test our model. 
#A field called percentage gives the probability with which a random data point would be labelled as "TEST"

#!/usr/bin/python

import sys
import random

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
  print "Usage: %s <train file> <output train file name> <output test file name> <percentage>"%sys.argv[0]
  sys.exit(1)

def generateTestData(trainFile, outputTrainFile, outputTestFile, percentage):
  seed = trainFile+outputTrainFile+outputTestFile+str(percentage)

  trainFd = open(trainFile, 'rU')
  outputTrainFd = open(outputTrainFile, 'w')
  outputTestFd = open(outputTestFile, 'w')

  while True:
    session = getNextSession(trainFd)
    if not session:
      break;

    rand = random.random()
    if rand <= percentage:
      # Write the session to test file.
      writeSession(session, outputTestFd, "test")
    else:
      # Write the session to train file.
      writeSession(session, outputTrainFd, "train")
      

  trainFd.close()
  outputTrainFd.close()
  outputTestFd.close()
    
def getNextSession(trainFd):
  session = []
  currentPos = trainFd.tell()
  line = trainFd.readline()
  if not line:
    return None

  line = line.strip()
  line = line.split()
  trainFd.seek(currentPos) #Rewind
  sessionId = line[IDX_SESSION_ID]
  
  while True:
    currentPos = trainFd.tell()
    line = trainFd.readline()
    if not line:
      break; 
    line = line.strip()
    line = line.split()
    currSessionId = line[IDX_SESSION_ID]
    if currSessionId != sessionId:
      trainFd.seek(currentPos)
      break;

    session.append(line)

  return session

def writeSession(session, outputFd, dataType):
  if dataType == "test":
    for row in session[0:-10]:
      row.insert(4, "TRAIN")
      outputFd.write("%s\n"%"\t".join(row))

    for row in session[-10:]:
      row.insert(4, "TEST")
      outputFd.write("%s\n"%"\t".join(row))
  elif dataType == "train":
    for row in session:
      outputFd.write("%s\n"%"\t".join(row))
  else:
    raise Exception("Invalid type specified: %s"%dataType)

def main():
  if len(sys.argv) != 5 :
    printUsageAndExit()

  trainFile = sys.argv[1]
  outputTrainFile = sys.argv[2]
  outputTestFile = sys.argv[3]
  percentage = float(sys.argv[4])

  generateTestData(trainFile, outputTrainFile, outputTestFile, percentage)

if __name__ == '__main__':
  sys.exit(main())

