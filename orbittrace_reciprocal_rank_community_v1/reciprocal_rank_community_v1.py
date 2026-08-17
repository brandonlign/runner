#!/usr/bin/env python3
from __future__ import annotations
import hashlib, math
from typing import Any
import networkx as nx
import numpy as np
from sklearn.neighbors import NearestNeighbors

H_SOL=2.0*math.sin(math.radians(5.0)/2.0)
H_RAD=2.0*math.sin(math.radians(4.0)/2.0)
H_LOGV=math.log(1.1)
RESOLUTION=1.0
LOUVAIN_THRESHOLD=1.0e-7
SEED=20260816
MIN_SUPPORT=4

def require(ok,msg):
    if not ok: raise RuntimeError(msg)

def embedding(rows:list[dict[str,Any]])->np.ndarray:
    sol=np.radians(np.asarray([float(r["sol"]) for r in rows],dtype=np.float64))
    lon=np.radians(np.asarray([float(r["sun_lon"]) for r in rows],dtype=np.float64))
    lat=np.radians(np.asarray([float(r["ecl_lat"]) for r in rows],dtype=np.float64))
    vg=np.asarray([float(r["vg"]) for r in rows],dtype=np.float64)
    require(np.all(vg>0) and np.all(np.isfinite(vg)),"invalid speed")
    cl=np.cos(lat)
    return np.column_stack([np.cos(sol)/H_SOL,np.sin(sol)/H_SOL,cl*np.cos(lon)/H_RAD,cl*np.sin(lon)/H_RAD,np.sin(lat)/H_RAD,np.log(vg)/H_LOGV])

def fit_ranked(rows:list[dict[str,Any]]):
    ids=[str(r["id"]) for r in rows]; n=len(ids); require(n==len(set(ids)) and n>4,"bad ids")
    X=embedding(rows)
    k=int(math.ceil(math.log2(n)))
    require(2<=k<n,"bad k")
    nbr=NearestNeighbors(n_neighbors=k+1,metric="euclidean",algorithm="auto",n_jobs=1).fit(X)
    distances,indices=nbr.kneighbors(X,return_distance=True)
    ranked_neighbors=[]
    for i in range(n):
        pairs=[(float(d),int(j)) for d,j in zip(distances[i],indices[i]) if int(j)!=i]
        pairs.sort(key=lambda z:(z[0],z[1]))
        require(len(pairs)>=k,"insufficient neighbors")
        ranked_neighbors.append([j for _,j in pairs[:k]])
    rank_maps=[{j:r for r,j in enumerate(row,start=1)} for row in ranked_neighbors]
    G=nx.Graph(); G.add_nodes_from(range(n))
    for i,row in enumerate(ranked_neighbors):
        for r,j in enumerate(row,start=1):
            if j<=i: continue
            s=rank_maps[j].get(i)
            if s is None: continue
            G.add_edge(i,j,weight=float(1.0/math.sqrt(r*s)))
    require(G.number_of_edges()>n,"reciprocal graph too sparse")
    comms=nx.community.louvain_communities(G,weight="weight",resolution=RESOLUTION,threshold=LOUVAIN_THRESHOLD,seed=SEED)
    require(len(comms)>1,"partition collapsed")
    m=float(G.size(weight="weight")); require(m>0,"zero graph weight")
    raw=[]
    for nodes in comms:
        nodes=sorted(int(i) for i in nodes)
        if len(nodes)<MIN_SUPPORT: continue
        sub=G.subgraph(nodes)
        internal=float(sub.size(weight="weight"))
        volume=float(sum(dict(G.degree(nodes,weight="weight")).values()))
        q=float(internal/m-(volume/(2*m))**2)
        eids=[ids[i] for i in nodes]
        tie=hashlib.sha256(("\n".join(sorted(eids))+"\n").encode()).hexdigest()
        raw.append(dict(event_ids=eids,member_count=len(eids),modularity_contribution=q,internal_weight=internal,volume=volume,tie_hash=tie))
    raw.sort(key=lambda x:(-x["modularity_contribution"],x["tie_hash"]))
    out=[]
    for rank,x in enumerate(raw,start=1):
        out.append({"family_id":f"rrc-{x['tie_hash'][:16]}","rank":rank,**x})
    return out, {"n_events":n,"k":k,"mutual_edge_count":G.number_of_edges(),"community_count":len(comms),"reportable_community_count":len(out),"weighted_modularity":float(nx.community.modularity(G,comms,weight="weight",resolution=RESOLUTION))}
