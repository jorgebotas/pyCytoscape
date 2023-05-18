import pandas as pd
import py4cytoscape as p4c
from typing import Self, Union


class CystoscapeLayout:
    def __init__( 
			self: Self,
            name: str,
        ) -> None:
        self.name = name
        return


class CytoscapeStyle:
    DEFAULTS = {
        "NODE_SHAPE": "ellipse",
        "NODE_FILL_COLOR": "#FFFFFF",
        "NODE_WIDTH": 110,
        "NODE_HEIGHT": 70,
        "NODE_BORDER_WIDTH": 2,
        "NODE_LABEL_FONT_SIZE": 30,
        "NODE_LOCK_DIMENSIONS": False,
        "EDGE_TRANSPARENCY": 100,
        "EDGE_WIDTH": 1,
    }
    MAPPINGS = [
        {
            "mappingType": "passthrough",
            "mappingColumn": "id",
            "mappingColumnType": "String",
            "visualProperty": "NODE_LABEL"
        },
    ]
    NODE_SHAPES = p4c.get_node_shapes()
    PALETTE = {"d": ""}
    def __init__(
			self: Self, 
            name: str,
            nodes: pd.DataFrame,
            defaults: dict = None, 
            mappings: dict = None,
            base_url: str = p4c.DEFAULT_BASE_URL,
        ) -> None:

        self.name = name
        self.nodes = nodes
        self.base_url = base_url
        self._defaults = defaults or self.DEFAULTS
        self._mappings = mappings or self.MAPPINGS
        p4c.create_visual_style(
                self.name,
                defaults=self._defaults, 
                mappings=self._mappings)
        p4c.lock_node_dimensions(False, style_name=self.name,
                                 base_url=self.base_url)
        p4c.sync_node_custom_graphics_size(False, style_name=self.name,
                                           base_url=self.base_url)

    def _get_mapping_type(
			self: Self, 
            column: str
        ) -> str:
        if self.nodes[column].dtype in ("int64", "float64"):
            mtype = "c"
        else:
            mtype = "d"
        return mtype

    def _check_mapping_type(
			self: Self, mtype: str) -> str:
        if mtype not in ("c", "d", "p"):
            print("""Mapping type should be one of the following:
            - 'c': continuous
            - 'd': discrete
            - 'p': passthrough
            Setting to default 'p'.""")
            return "p"
        return mtype

    def _check_node_shapes(
			self: Self, 
            shapes: list
        ) -> None:
        for shape in shapes:
            if shape not in self.NODE_SHAPES:
                print(f'Node shape: {shape}, not recognised. ' + \
                    f'Please use one ofthe following supported node shapes:'+\
                    ", ".join(self.NODE_SHAPES))

    def node_shape(
			self: Self,
            column: str, 
            mapping: dict,
        ) -> None:
        """
        Map node property to shape.
        :mapping: dictionary containing mapping. Variable should be discrete
        """
        values, shapes = list(mapping.keys()), list(mapping.values())
        self._check_node_shapes(shapes)
        p4c.set_node_shape_mapping(
                style_name=self.name,
                table_column=column, 
                table_column_values=values,
                shapes=shapes)

    def node_color(
			self: Self,
            column: str, 
            mtype: str = None,
            mapping: dict = None,
        ) -> dict:
        """
        Map node property to shape.
        :mapping: dictionary containing mapping. 
                  If not provided, automatic mapping.
        :mtype: mapping type ('c': continuous; 'd': discrete; 'p': passthrough).
                Derived from nodes' pd.DataFrame column if not provided.
        """

        if mtype:
            mtype = self._check_mapping_type(mtype)
        else:
            mtype = self._get_mapping_type(column)

        if mapping:
            values, colors = list(mapping.keys()), list(mapping.values())
        else:
            cmap = p4c.gen_node_color_map(
                    style_name=self.name, 
                    table_column=column,
                    mapping_type=mtype)
            values = cmap["table_column_values"]
            colors = cmap["colors"]


        p4c.set_node_color_mapping(
                style_name=self.name, 
                table_column=column,
                table_column_values=values, 
                colors=colors,
                mapping_type=mtype)

        return dict(zip(values, colors))

    def node_piechart(
            self: Self,
            columns: list,
            slot: int = 1,
            hole_size: float = 0.7,
            size: float = None,
            colors: list = None,
        ) -> None:

        p4c.set_node_custom_ring_chart(columns=columns,
                                       slot=slot,
                                       hole_size=hole_size,
                                       #colors=colors,
                                       style_name=self.name)
        if size is None:
            size = self.DEFAULTS["NODE_WIDTH"] / hole_size + 10
        
        style = {
            "visualProperty": f"NODE_CUSTOMGRAPHICS_SIZE_{slot}",
            "value": size
        }
        p4c.set_visual_property_default(style, style_name=self.name, 
                                        base_url=self.base_url)

    def edge_shape(
			self: Self, column: str) -> dict:
        """
        Map edge source and target shape. 
        Check CytoscapeStyle.EDGE_SHAPE_MAPPING for defaults
        """
        values = list(self.EDGE_SHAPE_MAPPING.keys())
        shapes = self.EDGE_SHAPE_MAPPING.values()
        source_shapes = [ shape[0] for shape in shapes ]
        target_shapes = [ shape[1] for shape in shapes ]
        p4c.set_edge_source_arrow_shape_mapping(
                style_name=self.name,
                table_column=column,
                table_column_values=values,
                shapes=source_shapes)
        p4c.set_edge_target_arrow_shape_mapping(
                style_name=self.name,
                table_column=column,
                table_column_values=values,
                shapes=target_shapes)


class Cytoscape:
    def __init__(
			self: Self,
            name: str,
            nodes: pd.DataFrame,
            edges: pd.DataFrame,
            collection: str = None,
            base_url: str = p4c.DEFAULT_BASE_URL,
        ) -> None:
        """
        name: Name of the network (also used as style name).
        nodes: node information. Names of nodes must match names of nodes in
               edge data. 
        edges: contains information on interaction between nodes. Required.
        """
        self.name = name
        self.nodes = nodes
        self.edges = edges

        self.collection = collection or self.name
        p4c.create_network_from_data_frames(
                nodes=self.nodes,
                edges=self.edges, 
                title=self.name,
                collection=self.collection)
        self.base_url = base_url
        self.suid = p4c.networks.get_network_suid(None, base_url=self.base_url) 
        style_name = f'{self.name} style'
        self.style = CytoscapeStyle(style_name, self.nodes, 
                                    base_url=self.base_url)
        p4c.set_visual_style(style_name)


    def save_session(
			self: Self, 
            outfile: str, 
            overwrite: bool = True):
        if outfile[-4:] != ".cys":
            outfile += ".cys"
        p4c.save_session(outfile, overwrite_file=overwrite)
        return outfile

    def save_image(
			self: Self, 
            outfile: str, 
            format: str = "svg",
            overwrite: bool = True) -> str:
        """
        Write session to file (outfile). Returns file name
        """
        extension = f'.{format.lower()}'
        if outfile[-len(extension):] != extension:
            outfile += extension

        p4c.export_image(outfile, type=format.upper(), overwrite_file=overwrite)
        return outfile


    def set_layout(
            self: Self,
            layout: CystoscapeLayout,
        ) -> None:
        """
        Apply Cytoscape Layout to network
        """
        return

    def group_attribute_layout(
            self: Self,
            node_attribute: str,
            spacingx: int = 150, 
            spacingy: int = 150, 
            maxwidth: int = 2000, 
            minrad: int = 100, 
            radmult: float = 50
        ) -> None:
        """
        Apply Group Attribute Layout to network given
        """
        p4c.set_layout_properties("attributes-layout", {
            "spacingx": spacingx,
            "spacingy": spacingy,
            "maxwidth": maxwidth,
            "minrad": minrad,
            "radmult": radmult,
            })
        layout_name = "attributes-layout"
        command = f'layout {layout_name} network="SUID:{self.suid}"'
        command = f'{command} nodeAttribute="{node_attribute}"'
        p4c.commands.commands_post(command, base_url=self.base_url)

    def annotate_clusters(
            self: Self,
            node_attribute: str,
            font_family: str = "Avenir",
            font_size: int = 40,
            spacingx: int = 150, 
            spacingy: int = 150, 
            maxwidth: int = 2000, 
            minrad: int = 100, 
            radmult: float = 50
        ) -> None:
        """
        Annotate clusters (numbers)

        Calls Cystocape.group_attribute_layout. See documentation
        """
        self.group_attribute_layout(node_attribute,
                                    spacingx=spacingx,
                                    spacingy=spacingy,
                                    maxwidth=maxwidth,
                                    minrad=minrad,
                                    radmult=radmult)
        nodes = self.nodes
        for cluster in nodes[node_attribute].unique():
            cluster_nodes = nodes[nodes[node_attribute] == cluster].index
            cluster_node_pos = p4c.get_node_position(list(cluster_nodes))

            # Circular annotation
            width = height = 70

            # X coordinate
            x_max = cluster_node_pos.x.max()
            x_min = cluster_node_pos.x.min()
            x = x_max - abs(x_max - x_min + width) / 2
            # Prettify triangles and pentagons
            if len(cluster_nodes) in (3, 5):
                x -= width / len(cluster_nodes)

            # Y coordinate
            y_max = cluster_node_pos.y.max()
            y_min = cluster_node_pos.y.min()
            y = y_max - (y_max - y_min + height) / 2
            # Prettify singletons
            if len(cluster_nodes) == 1:
                y += height + 30

            p4c.add_annotation_bounded_text(text=int(cluster), 
                                            width=width,
                                            height=height,
                                            x_pos=x,
                                            y_pos=y,
                                            type="ELLIPSE",
                                            fill_color="#FFFFFF",
                                            font_family=font_family,
                                            font_size=font_size,
                                            z_order=1)