import networkx as nx
import numpy as np
import math
from copy import deepcopy
from math import sin, cos, sqrt, atan2, asin, radians

## Global Scope variables 
gt_unknown = {} # Stores the ground truth values for users that did not share location
gt_unknown_orig = {}

# Data for Inferences
inferred_data = {} # Stores the known data and the inferences 
network = nx.Graph() # Stores the social network
unknown_users = [] # Stores the indices of the users that were initially unknown
unknown_users_rd2 = [] # Indices that are not inferred after first round

# Stats about the social network
num_total_users = 0
num_unknown_users = 0
num_known_users = 0
num_unknown_friendless = 0
num_unknown_friends = 0

percent_known = 0.0
percent_unknown = 0.0
percent_cant_guess = 0.0

# Copies of dictionaries/lists to let algorithms run independently 
gt_unknown_orig = {}
inferred_data_orig = {} 
unknown_users_orig = []
## End Global Scope variables

# User object
class User(object):
    def __init__(self, index, latitude, longitude, sharedLoc):
        self.index = index
        self.latitude = latitude
        self.longitude = longitude
        self.sharedLoc = sharedLoc

    def __getattr__(self, name):
        if(name == "index"):
            return self.index
        if(name == "latitude"):
            return self.latitude
        if(name == "longitude"):
            return self.longitude
        if(name == "sharedLoc"):
            return self.sharedLoc  

    def shared_loc(self):
        if(self.sharedLoc == 1):
            return True
        else: 
            return False

# Dataset Parser
def readDataset():
    # Parse user/node data from homes.txt
    with open('dataset/homes.txt', 'r') as homes:
        for line in homes:
            home_data = line.split(",")
            temp_index = home_data[0].strip()
            temp_lat = float(home_data[1].strip())
            temp_long = float(home_data[2].strip())
            temp_shared = int(home_data[3].strip())

            u = User(temp_index, temp_lat, temp_long, temp_shared)
            network.add_node(temp_index)

            # Populate the users that must be inferred
            if(temp_shared == 0):
                gt_unknown[temp_index] = u
                inferred_data[temp_index] = User(temp_index, 0, 0, 0)
                unknown_users.append(temp_index)
            else:
                inferred_data[temp_index] = u

    # Parse friendship/edge data from friends.txt
    with open('dataset/friends.txt', 'r') as friends:
        for line in friends:
            friendship = line.split(",")
            network.add_edge(friendship[0].strip(), friendship[1].strip())


# Populates the global variables with statistical info about dataset
def getDataDemographics():
    global num_total_users, num_unknown_users, num_known_users, num_unknown_friendless, num_unknown_friends, percent_known, percent_unknown, percent_cant_guess
    num_total_users = len(inferred_data)
    num_unknown_users = len(gt_unknown)
    num_known_users = num_total_users - num_unknown_users

    for i in unknown_users:
        if(len(list(network.neighbors(i))) == 0):
            num_unknown_friendless += 1

    num_unknown_friends = num_unknown_users - num_unknown_friendless
    percent_known = float(num_known_users)/float(num_total_users)
    percent_unknown = float(num_unknown_users)/float(num_total_users)
    percent_cant_guess = float(num_unknown_friendless)/float(num_total_users)


# Simple inference algorithm, as a basic location inference
def simpleInferenceAlgorithm():
    for i in unknown_users:
        neighbors = list(network.neighbors(i))
        loc_list = []
        for n in neighbors:
            n_i = str(n)
            if(inferred_data[n_i].shared_loc()):
                loc = (inferred_data[n_i].latitude, inferred_data[n_i].longitude)
                loc_list.append(loc)
        location_guess = ()
        if(len(loc_list) == 0):
            location_guess = (0.0, 0.0)
        else:
            location_guess = findCenter(loc_list)

        inferred_data[str(i)].latitude = location_guess[0]
        inferred_data[str(i)].longitude = location_guess[1]


# Outlier elimination in simple inference algorithm
def outlierInferenceAlgorithm():
    for i in unknown_users:
        neighbors = list(network.neighbors(i))
        loc_list = []
        for n in neighbors:
            n_i = str(n)
            if(inferred_data[n_i].shared_loc()):
                loc = (inferred_data[n_i].latitude, inferred_data[n_i].longitude)
                loc_list.append(loc)
        location_guess = ()
        if(len(loc_list) == 0):
            location_guess = (0.0, 0.0)
        elif(len(loc_list) > 2): # If 3+ neighbors, outlier elimination
            loc_list = eliminateOutliers(loc_list, 2.0) 
            location_guess = findCenter(loc_list)
        else: 
            location_guess = findCenter(loc_list)

        inferred_data[str(i)].latitude = location_guess[0]
        inferred_data[str(i)].longitude = location_guess[1]


# Use past inferences algorithm, builds on framework of past inferences
def usePastInferencesAlgorithm(firstAlgType):
    if(firstAlgType == 'simple'):
        simpleInferenceAlgorithm()
        getInferenceAccuracy()
    elif(firstAlgType == 'outlier'):
        outlierInferenceAlgorithm()
        getInferenceAccuracy()
    elif(firstAlgType == 'mutual'):
        mutualFriendsAlgorithm()
        getInferenceAccuracy()        

    for i in unknown_users_rd2:
        neighbors = list(network.neighbors(i))
        loc_list = []
        for n in neighbors:
            n_i = str(n)
            if((inferred_data[n_i].shared_loc()) or (inferred_data[n_i].latitude != 0 and inferred_data[n_i].longitude != 0)):
                loc = (inferred_data[n_i].latitude, inferred_data[n_i].longitude)
                loc_list.append(loc)
        location_guess = ()
        if(len(loc_list) == 0):
            location_guess = (0.0, 0.0)
        else:
            location_guess = findCenter(loc_list)

        inferred_data[str(i)].latitude = location_guess[0]
        inferred_data[str(i)].longitude = location_guess[1]


# Use mutual friends algorithm, like simple inference but with friends of friends too
def mutualFriendsAlgorithm():
    for i in unknown_users:
        neighbors = list(network.neighbors(i))
        loc_list = []
        if(len(neighbors) != 0):
            percent_shared = percentFriendsShared(neighbors)
        
        if(percent_shared < 0.05):
            for n in neighbors:
                n_i = str(n)
                if(inferred_data[n_i].shared_loc()):
                    loc = (inferred_data[n_i].latitude, inferred_data[n_i].longitude)
                    loc_list.append(loc)
                else:
                    mutual_friends = list(network.neighbors(n))   
                    mutual_friends.remove(i)
                    for m in mutual_friends:
                        m_i = str(m)
                        if(inferred_data[m_i].shared_loc()):
                            loc = (inferred_data[m_i].latitude, inferred_data[m_i].longitude)
                            loc_list.append(loc)
        else:
            for n in neighbors:
                n_i = str(n)
                if(inferred_data[n_i].shared_loc()):
                    loc = (inferred_data[n_i].latitude, inferred_data[n_i].longitude)
                    loc_list.append(loc)
        
        location_guess = ()
        if(len(loc_list) == 0):
            location_guess = (0.0, 0.0)
        else:
            location_guess = findCenter(loc_list)

        inferred_data[str(i)].latitude = location_guess[0]
        inferred_data[str(i)].longitude = location_guess[1]


# Uses the mutual friends algorithm with an added call to the outlier elimination helper
def outlierMutualAlgorithm():
    for i in unknown_users:
        neighbors = list(network.neighbors(i))
        loc_list = []
        if(len(neighbors) != 0):
            percent_shared = percentFriendsShared(neighbors)
        
        if(percent_shared < 0.05):
            for n in neighbors:
                n_i = str(n)
                if(inferred_data[n_i].shared_loc()):
                    loc = (inferred_data[n_i].latitude, inferred_data[n_i].longitude)
                    loc_list.append(loc)
                else:
                    mutual_friends = list(network.neighbors(n))   
                    mutual_friends.remove(i)
                    for m in mutual_friends:
                        m_i = str(m)
                        if(inferred_data[m_i].shared_loc()):
                            loc = (inferred_data[m_i].latitude, inferred_data[m_i].longitude)
                            loc_list.append(loc)
        else:
            for n in neighbors:
                n_i = str(n)
                if(inferred_data[n_i].shared_loc()):
                    loc = (inferred_data[n_i].latitude, inferred_data[n_i].longitude)
                    loc_list.append(loc)
        
        if(len(loc_list) == 0):
            location_guess = (0.0, 0.0)
        elif(len(loc_list) > 2): # If 3+ neighbors, outlier elimination
            loc_list = eliminateOutliers(loc_list, 2.0) 
            location_guess = findCenter(loc_list)
        else: 
            location_guess = findCenter(loc_list)

        inferred_data[str(i)].latitude = location_guess[0]
        inferred_data[str(i)].longitude = location_guess[1]


# Returns percent accuracy of inferences with metric within 25km 
def getInferenceAccuracy():
    num_predicted = 0

    for i in unknown_users:
        if(within25km(i)):
            num_predicted += 1
        else:
            unknown_users_rd2.append(i)

    accuracy = (float(num_known_users) + float(num_predicted))/float(num_total_users)
    return accuracy
  

# Uses Haversine formula to determine distance in km
def getDistancekm(lat1, lon1, lat2, lon2):
    dist_lon = lon2 - lon1 
    dist_lat = lat2 - lat1 

    a = sin(dist_lat/2)**2 + cos(lat1) * cos(lat2) * sin(dist_lon/2)**2
    c = 2 * asin(sqrt(a)) 
    R = 6371.0  # Earth radius (km)
    distance = c * R
    return distance


# Uses Haversine formula to determine if prediction w/i 25 km
def within25km(index):
    index = str(index)

    lat_pred = radians(float(gt_unknown[index].latitude))
    lon_pred = radians(float(gt_unknown[index].longitude))
    lat_true = radians(float(inferred_data[index].latitude))
    lon_true = radians(float(inferred_data[index].longitude))
    distance = getDistancekm(lat_pred, lon_pred, lat_true, lon_true)

    if(distance < 25.0):
        return True  # If prediction w/i 25 mile, true
    else: 
        return False # If prediction not w/i 25 miles, false


# Helper function to return center of locations from list
def findCenter(loc_list):
    num_neighbors = len(loc_list)
    lat_total = 0.0
    lon_total = 0.0
    
    for loc in loc_list:
        lat_total += loc[0]
        lon_total += loc[1]

    lat_guess = float(lat_total/num_neighbors)
    lon_guess = float(lon_total/num_neighbors)

    return((lat_guess, lon_guess))


# Helper function to get rid of location outliers
def eliminateOutliers(loc_list, divisor):
    center = findCenter(loc_list)
    distances = []

    for loc in loc_list:
        distances.append(getDistancekm(loc[0], loc[1], center[0], center[1]))

    dist_arr = np.array(distances)

    for i in range(math.floor(len(loc_list)/divisor)):
        max_i = np.argmax(dist_arr)
        dist_arr = np.delete(dist_arr, max_i)
        loc_list.pop(max_i)
    return loc_list

# Helper function to determine percent of friends that share location
def percentFriendsShared(friend_list):
    num_shared = 0
    num_total = len(friend_list)

    for f in friend_list:
        f_i = str(f)
        if(inferred_data[f_i].shared_loc()):
            num_shared += 1

    return float(num_shared/num_total)

# Function to restore the data structures to the original copies
def refreshDataStructs():
    global gt_unknown, inferred_data, unknown_users, gt_unknown_orig, inferred_data_orig, unknown_users_orig
    gt_unknown.clear()
    inferred_data.clear()
    unknown_users.clear()
    unknown_users_rd2.clear()

    gt_unknown = gt_unknown_orig.copy()
    inferred_data = inferred_data_orig.copy()
    unknown_users = unknown_users_orig.copy()


# Main function
readDataset()
getDataDemographics()

gt_unknown_orig = gt_unknown.copy()
inferred_data_orig = inferred_data.copy()
unknown_users_orig = unknown_users.copy()

simpleInferenceAlgorithm()
accuracy_simple = getInferenceAccuracy()
usePastInferencesAlgorithm('none')
accuracy_past = getInferenceAccuracy()

refreshDataStructs()
outlierInferenceAlgorithm()
accuracy_outlier = getInferenceAccuracy()
usePastInferencesAlgorithm('none')
accuracy_combo_outlier_past = getInferenceAccuracy()

refreshDataStructs()
mutualFriendsAlgorithm()
accuracy_mutualFriends = getInferenceAccuracy()
usePastInferencesAlgorithm('none')
accuracy_combo_mutual_past = getInferenceAccuracy()

refreshDataStructs()
outlierMutualAlgorithm()
accuracy_combo_outlier_mutual = getInferenceAccuracy()
usePastInferencesAlgorithm('none')
accuracy_combo_triple_threat = getInferenceAccuracy()

print("Number of Total Users: ", num_total_users)
print("Number of Known Users: ", num_known_users)
print("Number of Unknown Users: ", num_unknown_users)
print("Number of Graph Nodes (Users): ", network.number_of_nodes())
print("Number of Graph Edges (Friendships): ", network.number_of_edges())

print("Baseline Accuracy: ", percent_known)
print("Accuracy Upper Bound: ", (1.0 - percent_cant_guess))

print("Simple Inference Accuracy: ", accuracy_simple)
print("Outlier Elimination Accuracy: ", accuracy_outlier)
print("Use Past Inferences Accuracy: ", accuracy_past)
print("Mutual Friends Accuracy: ", accuracy_mutualFriends)
print("Combined - Outlier/Past Inferences Accuracy: ", accuracy_combo_outlier_past)
print("Combined - Mutual Friends/Past Inferences Accuracy: ", accuracy_combo_mutual_past)
print("Combined - Outlier/Mutual Friends Accuracy: ", accuracy_combo_outlier_mutual)
print("Combined - All Three Optimizations: ", accuracy_combo_triple_threat)