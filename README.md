Re-order the top ten search results for a query based on user web history
=========================================================================

Author: Anantha Raghuraman and Asish Ghoshal
--------------------------------------------

# Goal of the Project

i) Parse a large dataset (obtained from Yandex logs) that has user web search history (hashed) data for 30 days.

ii) Identify key fields and build a machine learning model to predict relevance of search results for a given user and query terms.

iii) Divide training data into training and test and find out the best model by cross validation.


# Problem and Dataset

i) The problem was taken from Kaggle.com and the dataset was provided as part of the problem.

ii) Training data consisted of 30 day user search history for more than 12 million users.

iii) Training data was composed of various fields like "User ID", "Session ID", "Query Terms", "Ordered URL results", "Ordered Domain results", "Event: Click / Query Entry / Close", "Dwell time (Time spent after clicking, if applicable)"

iv) The main challenging feature of the dataset is that all the data fields are completele hashed and so we have no information about the meaning of search queries and results.


Design and Files
-----------------
There are 4 main files

i) extract_training_data.py
	This parses the training data into all the fields and computes dwell time. Then, is uses the dwell time to compute relevance.

ii) generate_test_data.py
	Randomly divide trainign data into training and test data based. A percentage field decides the probability with which we would get test data. 

iii) parse_test_data.py
	Parses Test data into relevant fields. The test data here corresponds to the test data provided to us by kaggle.com

iv) predict.py
	Uses the model to compute the probability of relevance being a particular value (0 (irrelevant), 1(moderately relevant) or 2 (high)) for a given user, query and history


Running information
--------------------
i) extract_training_data.py takes one argument, the name of the file that contains training data. Running the python file writes output to a file
	after parsing the relevant fields and adding dwell time.

ii) generate_test_data.py takes 4 inputs, the name of the file that contains parsed training data, the name of the output file that should contain 
	the new training data, the name of the output file that should contain the new test data and the percentage (prob (test data)). Running this file 
	generates two output files with randomly segregated training and test data for selecting best model parameters.

iii) parse_test_data.py takes one argument, the name of the file that contains training data. Running the python file writes output to a file
	after parsing the relevant fields and adding dwell time. This is very similar to parsing the training data, but this file input has an extra field
	called datatype which could be "TRAIN" or "TEST"

iv) predict.py uses the model to calculate the conditional probability that relevance would be a particular value (0 (irrelevant), 1(moderately relevant) or 2 (		high)) given that user is a particular user and the query terms are as they are. It uses the training data to generate conditional probabilities in a naive 		bayes like fashion, where each search term is considered to be independent of each other. Then, the maximum out of all conditional probabilities is chosen. 		Finally, the relevance with highest probability is assigned. Then, the search results are reordered according to relevance.

	It takes in 4 arguments:

	a) File containing parsed training data
	b) File containing parsed test data
	c) Output file
	d) Output format (could be actual (gives actual relevance) or experimental (gives predicted and actual relevance))

