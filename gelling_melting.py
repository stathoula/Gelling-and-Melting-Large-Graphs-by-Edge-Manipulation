import argparse
import numpy as np
import scipy as sc
import networkx as nx
import matplotlib.pyplot as plt
import itertools
from scipy import sparse

parser = argparse.ArgumentParser()
parser.add_argument("-g", "--gell", action="store_true" , help="gel graph")
parser.add_argument("-d", "--directed", action="store_true" , help="directed graph")
parser.add_argument("-s", "--separator" , help="seperator")
parser.add_argument("-f", "--figure" ,  action="store_true", help="Figure")
parser.add_argument("filename", help="name of input file")
parser.add_argument("num_edges", help="number of edges to delete", type=int)
args = parser.parse_args()
num_edges = args.num_edges

if not args.directed:
	if args.separator:
		s = args.separator
		G=nx.read_edgelist(args.filename, delimiter = s, nodetype = int)
	else:
		G=nx.read_edgelist(args.filename, nodetype = int)
else:
	if args.separator:
		s = args.separator
		G=nx.read_edgelist(args.filename, delimiter = s, nodetype = int, create_using=nx.DiGraph())
	else:
		G=nx.read_edgelist(args.filename, nodetype = int, create_using=nx.DiGraph())

nodes = [node for node in G.nodes()]
# We find the coordinate of each node
nodeToCoordinate = { node: count for count, node in enumerate(nodes) }

adj_matrix = nx.to_scipy_sparse_matrix(G, dtype=np.float64, format='csr')
#we calculate the max eigenvalue, left eigenvector right eigenvector
max_eigenvalue, right_eigenvector= sc.sparse.linalg.eigs(adj_matrix, k=1, M=None, sigma=None, which='LR', v0=None, ncv=None, maxiter=None, tol=0, return_eigenvectors=True, Minv=None, OPinv=None, OPpart=None)
#we calculate the transpose adjacency_matrix so as to find the left eigenvector
adj_matrix_T = sc.sparse.csr_matrix.transpose(adj_matrix)
max_eigenvalue, left_eigenvector= sc.sparse.linalg.eigs(adj_matrix_T, k=1, M=None, sigma=None, which='LR', v0=None, ncv=None, maxiter=None, tol=0, return_eigenvectors=True, Minv=None, OPinv=None, OPpart=None)
# We now check for negative values of the max left eigenvector

if np.min(left_eigenvector) < 0:
	left_eigenvector = - left_eigenvector
if np.min(right_eigenvector) < 0:
	right_eigenvector = - right_eigenvector

if not args.gell: #(K-edge Deletion)
	#we  calculate the score of every edge
	scores = {}
	for edge in G.edges():
		scores[(edge[0],edge[1])] = float(left_eigenvector[nodeToCoordinate[edge[0]]].real * right_eigenvector[nodeToCoordinate[edge[1]]].real)

	#PRINT SOLUTION###
	deletions = {} #A dictionary with the edges that we will add and their score in order to use it for args.figure
	for x  in sorted(scores.items(), key=lambda x: x[1], reverse = True)[:num_edges]:
		deletions[x[0]] = x[1]
		print(str(x))

else: #(K-edge Addition)
	if (args.directed):
		in_degrees = G.in_degree(G.nodes())
		max_inDegree = max(in_degrees.values())
		out_degrees = G.out_degree(G.nodes())
		max_outDegree = max(out_degrees.values())
	else:
		degrees = G.degree(G.nodes())
		max_degree = max(degrees.values())

	# We find the subset of k + din nodes with the highest left eigenscores ui
	# and the subset of k + dout nodes with the highest right eigenscores vi
	if args.directed:
		nodesI = np.argsort(-left_eigenvector.T, kind='quicksort')[:num_edges + max_inDegree].flatten()
		nodesJ = np.argsort(-right_eigenvector.T, kind='quicksort')[:num_edges + max_outDegree].flatten()
	else:
		nodesI = np.argsort(-left_eigenvector.T, kind='quicksort')[:num_edges + max_degree].flatten()
		nodesJ = np.argsort(-right_eigenvector.T, kind='quicksort')[:num_edges + max_degree].flatten()

	# We find the coordinate of each node
	coordinateToNode = { count: node for count, node in enumerate(nodes) }

	#We calculate the score of the edges i,j E(nodesI, nodesJ)
	scores = {}
	combinations = itertools.product(nodesI,nodesJ)
	for x in combinations:
		if x[0] != x[1] and adj_matrix[(x[0], x[1])] == 0 and (coordinateToNode[x[1]],coordinateToNode[x[0]]) not in scores.keys():
			scores[(coordinateToNode[x[0]],coordinateToNode[x[1]])] = float(left_eigenvector[x[0]].real * right_eigenvector[x[1]].real)

	#PRINT SOLUTION###
	additions = {} #A dictionary with the edges that we will add and their score in order to use it for args.figure
	for x  in sorted(scores.items(), key=lambda x: x[1], reverse = True)[:num_edges]:
		additions[x[0]] = x[1]
		print(str(x))
		
#Print a small graph before and after the k-edge addition/k-edge addition if --figured
if (args.figure):
	fig = plt.figure()
	fig.suptitle('BEFORE', fontsize=20)
	nx.draw_networkx(G)
	plt.show()
	if (args.gell):
		G.add_edges_from(additions.keys())
	else:
		G.remove_edges_from(deletions.keys())
	fig = plt.figure()
	fig.suptitle('AFTER', fontsize=20)
	nx.draw_networkx(G)
	plt.show()
