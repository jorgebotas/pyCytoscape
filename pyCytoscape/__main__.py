from argparse import ArgumentParser
import pandas as pd

from .cytoscape import Cytoscape



def parse_args():
    parser = ArgumentParser("pyCytoscape")
    parser.add_argument("--name", "-n", type=str, default="pyCytoscape")
    parser.add_argument("--edges", "-e", type=str, required=True)
    parser.add_argument("--clusters", "-c", type=str)
    parser.add_argument("--sources", "-s", type=str)
    return parser.parse_args()

def get_edges_and_nodes(edge_path):
    edges = pd.read_csv(edge_path, sep="\t")
    try:
        edges = edges[["#node1", "node2"]]
    except:
        edges = pd.read_csv(edge_path, sep=",")
    edges = edges[["#node1", "node2"]]
    edges.columns = ["source", "target"]
    nodes = pd.DataFrame(list(set(set(edges.source) | set(edges.target))))
    nodes.columns = ["id"]
    nodes.set_index("id", inplace=True, drop=False)
    return edges, nodes

def main():
    args = parse_args()
    edges, nodes = get_edges_and_nodes(args.edges)

    if args.clusters:
        clusters = pd.read_csv(args.clusters, sep="\t")\
            .set_index("protein name")
        nodes["cluster"] = clusters["cluster number"]
        nodes = nodes.dropna(subset=["cluster"])
        # cluster_colormap = clusters[["cluster number", "cluster color"]]\
        #     .drop_duplicates().set_index("cluster number")\
        #     .to_dict()["cluster color"]
    
    if args.sources:
        sources = pd.read_csv(args.sources, sep="\t")
        sources.set_index("gene", inplace=True)
        nodes = pd.concat([nodes, sources], axis=1).reindex(nodes.index)
    
   
    cys = Cytoscape(args.name, nodes, edges)
    cys.group_attribute_layout("cluster")
    #cys.annotate_clusters("cluster")
    cys.style.node_color("cluster", "d")
    cys.style.node_piechart(list(sources.columns))

    return

if __name__ == "__main__":
    main()
