#Authors: Anantha Raghuraman and Asish Ghoshal
#Date: Nov, 2013
#Filename: extract_training_data.py
#Description:
#a) Parses training data's fields from the CSV file to get all the attributes of the data points.
#b) Maps click data to query data for all sessions
#c) Computes Dwell time for each data point
#d) Write the entire data into a form that is more readable to a file


#!/usr/bin/python
import sys

QUERY_TYPE = 'Q'
CLICK_TYPE = 'C'
MAX_DWELL_TIME = sys.maxint

def printUsageAndExit():
  print "Usage: %s <filename>"%sys.argv[0]
  sys.exit(1)

def parseMetadata(tokens):
  (sessionId, userId) = (tokens[0], tokens[3])
  attributeMap = {"SESSION_ID":sessionId,
    "USER_ID":userId
    }
  return attributeMap

def parseQueryRecord(tokens):
  (sessionID, timePassed, serpID, queryID, listOfTerms) = (tokens[0], tokens[1],
    tokens[3], tokens[4], tokens[5])

  urlList = {}
  for line in tokens[6:]:
    line = line.strip()
    urlTokens = line.split(",")
    (url, domain) = (urlTokens[0], urlTokens[1])
    urlList[url] = (domain,)

  attributeMap = { "SESSION_ID": sessionID,
      "QUERY_TIME_PASSED": timePassed,
      "SERP_ID": serpID,
      "QUERY_ID": queryID,
      "QUERY_TERMS": listOfTerms,
      "URL_LIST": urlList,
    }
  return attributeMap


def parseClickRecord(tokens):
  (sessionID, timePassed, serpID, urlID) = (tokens[0], tokens[1], tokens[3], tokens[4])

  attributeMap = { "SESSION_ID": sessionID,
      "CLICK_TIME_PASSED": timePassed,
      "SERP_ID": serpID,
      "URL_ID": urlID
    }
  return attributeMap

def getQueryList(session):
  ''' This function maps click data to reults of queries and returns the query list for the session '''
  queryList = {}
  for query in session["queries"]:
    serpID = query["SERP_ID"]
    queryList[serpID] = query

  for click in session["clicks"]:
    serpID = click["SERP_ID"]
    urlID = click["URL_ID"]
    query = queryList[serpID]
    if len(query["URL_LIST"][urlID]) == 2:
      (domain, urlClick) = query["URL_LIST"][urlID]
      click["DWELL_TIME"] = urlClick["DWELL_TIME"] + click["DWELL_TIME"]
      query["URL_LIST"][urlID] = (domain, click)
    else:
      domain = query["URL_LIST"][urlID][0]
      query["URL_LIST"][urlID] = (domain, click)

  return queryList.values()

def writeSessionData(session, fid):
  if session == None or len(session["queries"]) == 0:
    #Nothing to write.
    return

  queries = getQueryList(session)
  userID = session["metadata"]["USER_ID"]
  for query in queries:
    #USER_ID, SESSION_ID, SERP_ID, QUERY_ID, QUERY_TIME_PASSED, QUERY_TERMS, URLS, DOMAINS, CLICK_TIME_PASSED, DWELL_TIME
    record = "%s\t%s\t%s\t%s\t%s\t%s"%(userID, 
      query["SESSION_ID"], query["SERP_ID"], query["QUERY_ID"], query["QUERY_TIME_PASSED"], query["QUERY_TERMS"])
    for (url, value) in query["URL_LIST"].iteritems():
      if len(value) == 2:
        (domain, click) = value
        dwellTime = ",".join(map(str, click["DWELL_TIME"]))
        record1 = "%s\t%s\t%s\t%s\t%s\n"%(record, url, domain, click["CLICK_TIME_PASSED"], dwellTime)
      else:
        domain = value[0]
        dwellTime = "0"  
        record1 = "%s\t%s\t%s\t%d\t%s\n"%(record, url, domain, 0, dwellTime)
      fid.write(record1)

def computeDwellTime(click, time):
  clickTime = int(click["CLICK_TIME_PASSED"])
  dwellTime = time - clickTime
  appendDwellTime(click, dwellTime)

def appendDwellTime(click, dwellTime):
  dwellTimes = click.get("DWELL_TIME", [])
  dwellTimes.append(dwellTime)
  click["DWELL_TIME"] = dwellTimes

def initializeSession(session):
  session.clear()
  session["queries"] = []
  session["clicks"] = []

def extractTrainingData(filename, tableName):
  fid = open(filename, 'rU')
  wfid = open(tableName, 'w')
  
  #Write the header
  wfid.write("USER_ID\tSESSION_ID\tSERP_ID\tQUERY_ID\tQUERY_TIME_PASSED\tQUERY_TERMS\tURLS\tDOMAINS\tCLICK_TIME_PASSED\tDWELL_TIME\n")

  currentSessionId = -1
  session = {}
  initializeSession(session)
  lastClick = None
  lastActivity = None

  for line in fid:
    line = line.strip()
    tokens = line.split("\t")
    sessionId = int(tokens[0])

    if sessionId == currentSessionId:
      # Check the type of record field to identify if its a query record or a click record.
      typeOfRecord = tokens[2]
      if typeOfRecord == QUERY_TYPE:
        queryAttr = parseQueryRecord(tokens)
        if lastClick:
          computeDwellTime(lastClick, int(queryAttr["QUERY_TIME_PASSED"]))
        session["queries"].append(queryAttr)
        lastActivity = QUERY_TYPE
        lastClick = None
      else:
        clickAttr = parseClickRecord(tokens)
        if lastClick:
          computeDwellTime(lastClick, int(clickAttr["CLICK_TIME_PASSED"]))
        session["clicks"].append(clickAttr)
        lastClick = clickAttr
        lastActivity = CLICK_TYPE
    else:
      # THis is a new session. So the record must be a metadata record
      # First write the existing session data to files.
      if lastActivity == CLICK_TYPE:
        appendDwellTime(lastClick, MAX_DWELL_TIME)
      writeSessionData(session, wfid)

      lastActivity = None
      lastClick = None
      
      if (sessionId >= 10000):
        break;

      initializeSession(session)

      metadataAttributes = parseMetadata(tokens)
      currentSessionId = int(metadataAttributes["SESSION_ID"])
      session["metadata"] = metadataAttributes

  if lastActivity == CLICK_TYPE:
    appendDwellTime(lastClick, MAX_DWELL_TIME)
  writeSessionData(session, wfid)

  fid.close()
  wfid.close()

def main():
  if len(sys.argv) != 2 :
    printUsageAndExit()

  filename = sys.argv[1]
  table = "%s.results"%filename
  extractTrainingData(filename, table)

if __name__ == '__main__':
  sys.exit(main())
