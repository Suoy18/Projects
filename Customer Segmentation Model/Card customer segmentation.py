# -*- coding: utf-8 -*-
"""
Created on Mon Aug  3 17:46:29 2020

@author: suoying
"""

'''Data Import'''
import pandas as pd
client = pd.read_csv('client12.csv')
mcc = pd.read_csv('mcc.csv', encoding = "unicode_escape" )
trx = pd.read_csv('trx12.csv', encoding = "unicode_escape")

trx.info(' ')
trx.describe()
trx.DATE = pd.to_datetime(trx.DATE)
trx.TYPE = trx.TYPE.astype(str)

client.info(' ')
client.describe()
client.CITY = client.CITY.astype(str)
client.STATE = client.STATE.astype(str)
client.GENDER = client.GENDER.astype(str)
client.MARITAL = client.MARITAL.astype(str)
client.HHIncome = client.HHIncome.astype(str)

mcc.info(' ')
mcc.describe()
mcc.MCC = mcc.MCC.astype(int)
mcc.CLASS = mcc.CLASS.astype(str)

acct = trx.groupby(trx['ACCT']).agg({'DATE':['count','max'], 'TRAMT':'sum',})
acct.columns = ['Frequency','LDT','Monetary']
END = pd.to_datetime('2019-11-01')
acct['Recency'] = (END - acct.LDT).dt.days
acct = acct.drop(columns=['LDT'])
ctrx = pd.merge(acct, client, left_on = acct.index, right_on = client.CLIENT_ID)
ctrx = ctrx.drop(columns=['key_0'])

# RFM Analysis
import seaborn as sns
from matplotlib import pyplot as plt
sns.distplot(ctrx['Recency'])
plt.show()
sns.distplot(ctrx['Frequency'])
plt.show()
sns.distplot(ctrx['Monetary'])
plt.show()

ctrx_RFM = ctrx[['Frequency', 'Monetary', 'Recency']]
ctrx_RFM.describe()
r_labels = range(2, 0, -1)
r_quartiles = pd.qcut(ctrx_RFM['Recency'], 2, labels = r_labels, duplicates = 'drop')
ctrx_RFM = ctrx_RFM.assign(R = r_quartiles.values)
f_labels = range(1,6)
m_labels = range(1,6)
f_quartiles = pd.qcut(ctrx_RFM['Frequency'], 5, labels = f_labels)
m_quartiles = pd.qcut(ctrx_RFM['Monetary'], 5, labels = m_labels)
ctrx_RFM = ctrx_RFM.assign(F = f_quartiles.values)
ctrx_RFM = ctrx_RFM.assign(M = m_quartiles.values)
def join_rfm(x): return str(x['R']) + str(x['F']) + str(x['M'])
ctrx_RFM['RFM_Segment'] = ctrx_RFM.apply(join_rfm, axis=1)
ctrx_RFM['RFM_Score'] = ctrx_RFM[['R','F','M']].sum(axis=1)
RFM = pd.DataFrame(ctrx_RFM.groupby('RFM_Score').agg({
'Recency': ['mean', 'median'],
'Frequency': ['mean', 'median'],
'Monetary': ['mean','median', 'count']}).round(1))
RFM
sns.distplot(ctrx_RFM['RFM_Score'])
plt.show()
import numpy as np
n = ctrx_RFM.shape[0]
def segment_me(x):
    if x >= 11:
        return 'Heavy'
    elif x >= 8:
        return 'Frequent'
    elif x >= 5:
        return 'Common'
    else:
        return 'Rare'
ctrx_RFM['General_RFM_Segment'] = ctrx_RFM.RFM_Score.apply(segment_me)
General_RFM_Segment = ctrx_RFM.groupby('General_RFM_Segment').agg({
'Recency': 'mean',
'Frequency': 'mean',
'Monetary': ['mean', 'count']}).round(1)
General_RFM_Segment.columns = ['R mean','F mean','M mean', 'Count']
General_RFM_Segment['Percentage'] = General_RFM_Segment.Count/n
#Treemap for RFM segment 
import squarify
p1 = plt.figure(figsize=(10, 6))
squarify.plot(sizes=General_RFM_Segment.Count, 
              label=General_RFM_Segment.index + '\n'+ General_RFM_Segment.Percentage.map(str), alpha=0.6) 
plt.axis('off') 
plt.show() 

#Hierarchical clustering, too much storage and time, drop out
#import scipy
#from scipy.cluster.hierarchy import linkage, fcluster
#from scipy.cluster.vq import whiten
#from scipy.cluster.hierarchy import dendrogram
#scaled_RFM = whiten(ctrx_RFM)
#Z = scipy.cluster.hierarchy.linkage(scaled_RFM, method='ward', metric='euclidean')
#dn = dendrogram(Z)
#plt.show()

# Kmeans clustering
import sklearn
from sklearn.preprocessing import StandardScaler
ctrx_RFM_2 = ctrx[['Frequency', 'Monetary', 'Recency']]
scaler = StandardScaler()
scaler.fit(ctrx_RFM_2)
ctrx_RFM_scaled = scaler.transform(ctrx_RFM_2)

from sklearn.cluster import KMeans
# Elbow criterion method
# Fit KMeans and calculate SSE for each *k*
sse = {}
for k in range(2, 11):
    kmeans = KMeans(n_clusters=k, random_state=1)
    kmeans.fit(ctrx_RFM_scaled)
    sse[k] = kmeans.inertia_ # sum of squared distances to closest cluster cente
# Plot SSE for each *k*
plt.title('The Elbow Method')
plt.xlabel('k'); plt.ylabel('SSE')
sns.pointplot(x=list(sse.keys()), y=list(sse.values()))
plt.show()

kmeans = KMeans(n_clusters=4, random_state=1)
kmeans.fit(ctrx_RFM_scaled)
cluster_labels = kmeans.labels_
k2 = kmeans.inertia_
ctrx_RFM_k2 = ctrx_RFM.assign(Cluster_RFM = cluster_labels)
Cluster_RFM = ctrx_RFM_k2.groupby(['Cluster_RFM']).agg({
'Recency': 'mean',
'Frequency': 'mean',
'Monetary': ['mean', 'count'],}).round(1)
Cluster_RFM.columns = ['R mean','F mean','M mean', 'Count']
Cluster_RFM['Percentage'] = Cluster_RFM.Count/n
Cluster_RFM.index = ['Frequent','Rare','Heavy', 'Common']

p2 = plt.figure(figsize=(10, 6))
squarify.plot(sizes=Cluster_RFM.Count, 
              label=Cluster_RFM.index + '\n' + Cluster_RFM.Percentage.map(str), alpha=0.6) 
plt.axis('off') 
plt.show() 

def cluster_rfm_name(x):
    if x == 0:
        return 'Frequent'
    elif x == 1:
        return 'Rare'
    elif x == 2:
        return 'Heavy'
    else:
        return 'Common'
ctrx_RFM_k2['RFM_Cluster_1'] = ctrx_RFM_k2.Cluster_RFM.apply(cluster_rfm_name)
ctrx_RFM_k2 = ctrx_RFM_k2.drop(columns=['Cluster_RFM'])

ctrx_RFM_normalized = pd.DataFrame(ctrx_RFM_scaled, index=ctrx_RFM_2.index,
columns=ctrx_RFM_2.columns)
ctrx_RFM_normalized['Cluster'] = ctrx_RFM_k2['RFM_Cluster_1']
ctrx_RFM_normalized['Client_ID'] = ctrx['CLIENT_ID']
ctrx_RFM_melt = pd.melt(ctrx_RFM_normalized.reset_index(),
id_vars=['Client_ID', 'Cluster'],
value_vars=['Recency', 'Frequency', 'Monetary'],
var_name='Attribute',
value_name='Value')
plt.title('Snake plot of standardized variables')
sns.lineplot(x="Attribute", y="Value", hue='Cluster', data=ctrx_RFM_melt)

# Relative importance of segment attributes
# The further a ratio is from 0, the more important that attribute is for a segment
# relative to the total population.
cluster_avg = ctrx_RFM_k2.groupby(['RFM_Cluster_1']).mean()
cluster_avg = cluster_avg.drop(columns=['RFM_Score'])
population_avg = ctrx_RFM_2.mean()
relative_imp = (cluster_avg / population_avg - 1).round(2)
plt.figure(figsize=(10, 4))
plt.title('Relative importance of attributes')
ax = sns.heatmap(data=relative_imp, annot=True, fmt='.2f', cmap='RdYlGn')
ax.set_ylim([4, 0])
plt.show()

# Transaction among Industry


# CART Decision Tree
# Import DecisionTreeClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
ctrx_dt = ctrx.drop(columns=['CLIENT_ID', 'CITY', 'STATE', 'MARITAL'])
# Transform string variable 
from sklearn.preprocessing import OneHotEncoder
Gender = ctrx_dt.GENDER.unique()
for j in range(len(Gender)):
    ctrx_dt.GENDER = ctrx_dt.GENDER.apply(lambda x:j if x==Gender[j] else x)
    # 0-F, 1-M, 2-U, 3-B
#One-hot coding for gender
tempgender = ctrx_dt[['GENDER']]
enc = OneHotEncoder()
enc.fit(tempgender)
tempgender = enc.transform(tempgender).toarray()
tempdata = pd.DataFrame(tempgender,columns=['GENDER']*len(tempgender[0]))
tempdata.columns = ['F', 'M', 'U', 'B']
ctrx_dt = pd.concat([ctrx_dt, tempdata], axis=1)
ctrx_dt = ctrx_dt.drop(columns=['GENDER'])
#coding for HHIncome
ctrx_dt.HHIncome = ctrx_dt.HHIncome.map({'A':1, 'B':2, 'C':3, 'D':4, 'E':5,
                                         'F':6, 'G':7, 'H':8,'I':9, 'J':10,
                                         'K':11, 'L':12, 'U':0}).astype(int)

# Label from clustering k2
# ctrx_dt['Target'] = ctrx_RFM_k2.RFM_Cluster_1
import pydotplus
from IPython.display import Image
from sklearn import tree
# Train decisiont tree model
clf=tree.DecisionTreeClassifier(max_depth = 4, min_samples_leaf = 500)
clf=clf.fit(ctrx_dt,ctrx_RFM_k2.RFM_Cluster_1)
print("train score:", clf.score(ctrx_dt, ctrx_RFM_k2.RFM_Cluster_1))
fig, ax = plt.subplots(figsize=(16, 16))
tree.plot_tree(clf, fontsize=10)






'''Major Update for new analysis and new models'''
##Update Industry and RF+10M Model
mcc_sum = pd.DataFrame(trx.groupby('MCC').agg({
'ACCT': 'count',
'TRAMT': 'sum'}).round(0))
mcc_top = mcc_sum.sort_values("TRAMT", axis=0, ascending=False)[0:10]
mcc_top = pd.merge(mcc_top, mcc, how='left', on = 'MCC')
trx_mcc_top = trx[trx['MCC'].isin(mcc_top.MCC)]
trx_mcc_top = trx_mcc_top[trx_mcc_top['ACCT'].isin(ctrx.CLIENT_ID)]
acct_mcc = pd.DataFrame(trx_mcc_top.groupby(['ACCT','MCC']).agg({'TRAMT':'sum'}))
acct_mcc.reset_index(inplace=True)
acct_mcc_pivot = acct_mcc.pivot(index='ACCT', columns='MCC', values='TRAMT')
acct_mcc_pivot[np.isnan(acct_mcc_pivot)] = 0
acct_mcc_pivot.reset_index(inplace=True)
acct_full = pd.merge(ctrx, acct_mcc_pivot, how='inner', left_on = 'CLIENT_ID', right_on = 'ACCT')
acct_full = acct_full.drop(columns=['ACCT'])
order = ['CLIENT_ID', 'Recency', 'Frequency', 'Monetary', 
         5411,5812,5542,5814,5541,4814,6300,5200,4899,4900,
         'STATE','CITY','AGE','GENDER','MARITAL','HHIncome']
acct_full = acct_full[order]
m = acct_full.CLIENT_ID.nunique()

##K-Means - RF+10M - 4 Clusters
import sklearn
from sklearn.preprocessing import StandardScaler
acct_full_1 = acct_full[['Recency','Frequency',5411,5812,5542,5814,5541,4814,6300,5200,4899,4900]]
scaler = StandardScaler()
scaler.fit(acct_full_1)
acct_full_1scaled = scaler.transform(acct_full_1)

from sklearn.cluster import KMeans
# Elbow criterion method
# Fit KMeans and calculate SSE for each *k*
sse = {}
for k in range(2, 11):
    kmeans = KMeans(n_clusters=k, random_state=1)
    kmeans.fit(acct_full_1scaled)
    sse[k] = kmeans.inertia_ # sum of squared distances to closest cluster cente
# Plot SSE for each *k*
plt.title('The Elbow Method')
plt.xlabel('k'); plt.ylabel('SSE')
sns.pointplot(x=list(sse.keys()), y=list(sse.values()))
plt.show()

kmeans = KMeans(n_clusters=4, random_state=1)
kmeans.fit(acct_full_1scaled)
cluster_labels_kmeans12 = kmeans.labels_
acct_full = acct_full.assign(kmeans12 = cluster_labels_kmeans12)
kmeans12_summary = acct_full.groupby(['kmeans12']).agg({
'Recency': 'median',
'Frequency': 'median',
'Monetary': ['median', 'count'],}).round(1)
kmeans12_summary.columns = ['R median','F median','M median', 'Count']
kmeans12_summary['Percentage'] = kmeans12_summary.Count/m

import squarify
plt.figure(figsize=(10, 6))
squarify.plot(sizes=kmeans12_summary.Count,
              label=kmeans12_summary.Percentage, alpha=0.6) 
plt.axis('off') 
plt.show() 

# Kmeans - RF+10M - 5 Clusters, one cluster is less than 1%
# kmeans = KMeans(n_clusters=5, random_state=1)
# kmeans.fit(acct_full_1scaled)
# cluster_labels_kmeans12 = kmeans.labels_
# acct_full = acct_full.assign(kmeans12 = cluster_labels_kmeans12)
# kmeans12_summary = acct_full.groupby(['kmeans12']).agg({
# 'Recency': 'median',
# 'Frequency': 'median',
# 'Monetary': ['median', 'count'],}).round(1)
# kmeans12_summary.columns = ['R median','F median','M median', 'Count']
# kmeans12_summary['Percentage'] = kmeans12_summary.Count/m

##K-Medians - RF+10M - 4 Clusters
from pyclustering.cluster.kmedians import kmedians
from pyclustering.cluster import cluster_visualizer
# Load list of points for cluster analysis.
from sklearn.decomposition import PCA
pca = PCA(n_components=2)
principalComponents = pca.fit_transform(acct_full_1scaled)
principalDf = pd.DataFrame(data = principalComponents
             , columns = ['pc1', 'pc2'])
plt.scatter(principalDf.pc1, principalDf.pc2)
# Create instance of K-Medians algorithm.
initial_medians = [[-2,0.1], [0,6], [5,5], [10,10]]
kmedians_instance = kmedians(principalComponents, initial_medians)
# Run cluster analysis and obtain results.
kmedians_instance.process()
clusters = kmedians_instance.get_clusters()
df1 = pd.DataFrame(clusters[0],columns=[0])
df1['group']=0
df2 = pd.DataFrame(clusters[1],columns=[0])
df2['group']=1
df3 = pd.DataFrame(clusters[2],columns=[0])
df3['group']=2
df4 = pd.DataFrame(clusters[3],columns=[0])
df4['group']=3
dfs = [df1, df2,df3,df4]
df = pd.concat(dfs)
acct_full=pd.merge(acct_full,df,how='left',left_on=acct_full.index,right_on=df[0])
acct_full = acct_full.drop(columns=['key_0',0])
acct_full=acct_full.rename(columns={'group': 'kmedians12'})
kmedians12_summary = acct_full.groupby(['kmedians12']).agg({
'Recency': 'median',
'Frequency': 'median',
'Monetary': ['median', 'count'],}).round(1)
kmedians12_summary.columns = ['R median','F median','M median', 'Count']
kmedians12_summary['Percentage'] = kmedians12_summary.Count/m
