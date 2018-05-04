# User Location Inferencing
@author: Miranda Kang (mskang2)

## How to Run Code

- Make sure Python is installed
- Run 'python inference.py'
- Wait.  It takes some time.
- The algorithm accuracy results will be printed to the terminal

## Introduction
 
### How I ended up with this data

I wanted to do a project on feature/user identification.  Originally, I wanted to do a user identification project by selecting a hashtag, and using the overlap of the hashtag's use in Twitter and Instagram to determine user account linkage.  However, due to the recent privacy controversy, Instagram's API for searching by hashtag has been severely deprecated.  Instead of returning a list of post metadata that uses the hashtag, it will only return the number of posts the hashtag has been used in. So I had to change gears.

Then, I was going to implement a location inferencing with the Yelp Academic Dataset.  However, there's 3 reasons why that turned out to be a bad idea:
1. The dataset is too large, and trying to parse just one of the files took much longer than anticipated.  Since I was going to use 4 of those files and I care about the well-being of my computer, I needed a smaller dataset.  
2. The Yelp dataset also lacked ground truth for the user location, so I'd be unable to test the accuracy of my algorithm.
3. The 'terms and conditions' of that dataset also includes a line about not violating the privacy of the users included in the dataset.  Oops.

Due to those limitations, and that it's surprisingly difficult to (legally) find datasets with ground truth on user attributes, I'm using a social network dataset from CS 463.  The data is an anonymized form of a real social network.  Unlike the Yelp Academic Dataset, this is a reasonable size to work with, includes ground truth, and will keep me out of legal trouble.

### Distinction of Implementation

This data was used for a Java-based location inferencing project, which was given to us with provided data structures and simple inference algorithm to implement.  While still drawing on the same base concepts of that project, I am making a distinct implementation from the CS 463 project:
- Use of Python instead of Java to ensure no code reuse
- Not strongly object oriented
- More advanced algorithm than the simple inference algorithm
- Comparative analysis of different optimizations
- Project features that we didn't have to write ourselves
- Writing the tests/evaluation by myself

### Project Statement

The social network dataset consists of homes.txt and friends.txt.  Homes.txt describes the social network users with each line containing:
- A user index
- Latitude
- Longitude
- If user shared location (0 for not shared, or 1 for shared)
Friends.txt contains 2 numbers per line, each indicating an edge in the social network between the users represented by each number.

Given this social network dataset, my goal is to compare algorithms that infer the locations of users who did not provide their locations.  The accuracy of my implementation will be measured by a metric of 25 km within the user's location, using a comparison of the ground truth values to the inferred users.

## The Algorithms

### Simple Inference Algorithm

For each of the users without a known location, average the locations of their friends to return the center location.  Use this location as the inferred location.

If the unknown user has no friends that shared locations, return 0's for latitude/longitude.

### Outlier Elimination

This optimization builds off the simple inference implementation.  For users that have more than 2 friends, the half (floored if not exact) of the neighbor location list that is furthest from the calculated initial center is eliminated.  While this does seem like a large portion of the shared locations, this produced the most accurate results.

This optimization is based on the idea users are more likely to have a majority of friends that are geographically close to them, and a smaller number of friends that are geographically distant.

### Use Past Inferences

This optimization starts off with one round of the Simple Inference Algorithm.  Afterwards, it runs through the algorithm for a second round, utilizing inferred locations from friends that did not have their locations shared during the initial round.  It is likely to boost location accuracy due to filling in information gaps.

This will ignore any of the user’s friends that do not have a location initialized.  It will also ignore any users that met the metric in the first round.

### Mutual Friends

The mutual friends optimization will closely follow the simple inference algorithm.  However, for users where less than 5% of their friends have shared locations, it will include friends of friends in the location list to find the center of.  

This optimization is based on the idea that 2nd degree connections are still likely to share a geographic area.

### Combined - Outlier Elimination and Use Past Inferences

This combined optimization will use the outlier elimination algorithm first, then call the use past inferences.

### Combined - Mutual Friends and Use Past Inferences

This combined optimization will use the mutual friends algorithm first, then call the use past inferences.

### Combined - Outlier Elimination and Mutual Friends

This combined optimization will use the mutual friends algorithm with a call to the outlier elimination helper.

### Combined - All Three Optimizations

This combined optimization will use the mutual friends algorithm with a call to the outlier elimination helper, then call the use past inferences.

## Statistical Analysis

### Notes
The accuracy of my inference the total percentage of users that shared locations willingly or were correctly inferred within the 25 km metric.

The baseline accuracy represents the percent accuracy of the dataset locations without inferencing, or the percentage of users that shared their location

The accuracy upper bound is the max accuracy of the dataset locations, which assumes that users without a shared location can be inferred if they have at least one friend.  This is the same as the percent of all users minus users without a location/friend.

### Base Numbers

- Number of Total Users:  107092
- Number of Known Users:  53469
- Number of Unknown Users:  53623
- Number of Graph Nodes (Users):  107092
- Number of Graph Edges (Friendships):  456830

- Baseline Accuracy:  0.49928099204422366
- Accuracy Upper Bound:  0.9647125835730026

### Algorithm Comparisons
- Simple Inference Accuracy:  0.6189071079072199
- Outlier Elimination Accuracy:  0.6459119261943003
- Use Past Inferences Accuracy:  0.6296642139468868
- Mutual Friends Accuracy:  0.6280674560191237
- Combined - Outlier/Past Inferences Accuracy:  0.6602080454188922
- Combined - Mutual Friends/Past Inferences Accuracy:  0.630616666044149
- Combined - Outlier/Mutual Friends Accuracy:  0.6599839390430657
- Combined - All Three Optimizations:  0.6626452022560042
