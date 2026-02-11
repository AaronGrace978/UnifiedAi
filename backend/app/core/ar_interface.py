"""
AR/Holographic Interface
WebXR integration for spatial computing.

Provides the foundation for AR/VR visualization
of knowledge graphs and AI interactions.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import math


@dataclass
class SpatialNode:
    """A node with 3D position for AR visualization"""
    id: str
    type: str
    label: str
    position: Dict[str, float]  # x, y, z
    scale: float = 1.0
    color: str = "#9B59B6"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpatialEdge:
    """An edge between spatial nodes"""
    source: str
    target: str
    strength: float = 1.0
    color: str = "#3498DB"
    style: str = "solid"  # solid, dashed, dotted


@dataclass
class SpatialScene:
    """A complete 3D scene for AR rendering"""
    id: str
    nodes: List[SpatialNode] = field(default_factory=list)
    edges: List[SpatialEdge] = field(default_factory=list)
    camera_position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 1.6, "z": 3})
    environment: str = "void"  # void, grid, skybox
    lighting: str = "ambient"  # ambient, directional, point
    created_at: datetime = field(default_factory=datetime.now)


class ARInterface:
    """
    AR/Holographic interface for UnifiedAi.
    
    Provides:
    - 3D scene generation from knowledge graphs
    - WebXR configuration
    - Spatial layout algorithms
    - Interactive holographic UI components
    """
    
    def __init__(self):
        self.scenes: Dict[str, SpatialScene] = {}
        self.scene_counter = 0
        
        # Layout parameters
        self.sphere_radius = 3.0
        self.cluster_spread = 2.0
        self.height_layers = 3
    
    def create_spatial_scene(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        layout: str = "sphere"
    ) -> SpatialScene:
        """
        Create a 3D scene from graph data.
        
        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries
            layout: Layout algorithm (sphere, layers, force)
            
        Returns:
            SpatialScene ready for AR rendering
        """
        self.scene_counter += 1
        scene_id = f"scene_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.scene_counter}"
        
        # Position nodes based on layout
        if layout == "sphere":
            positioned_nodes = self._sphere_layout(nodes)
        elif layout == "layers":
            positioned_nodes = self._layer_layout(nodes)
        else:
            positioned_nodes = self._force_layout(nodes, edges)
        
        # Create spatial edges
        spatial_edges = [
            SpatialEdge(
                source=e.get("source", ""),
                target=e.get("target", ""),
                strength=e.get("strength", 1.0),
                color=self._edge_color(e.get("type", "default")),
                style="solid"
            )
            for e in edges
        ]
        
        scene = SpatialScene(
            id=scene_id,
            nodes=positioned_nodes,
            edges=spatial_edges
        )
        
        self.scenes[scene_id] = scene
        return scene
    
    def _sphere_layout(self, nodes: List[Dict]) -> List[SpatialNode]:
        """Arrange nodes on a sphere surface"""
        n = len(nodes)
        if n == 0:
            return []
        
        spatial_nodes = []
        
        # Fibonacci sphere distribution for even spacing
        golden_ratio = (1 + math.sqrt(5)) / 2
        
        for i, node in enumerate(nodes):
            # Fibonacci sphere point
            theta = 2 * math.pi * i / golden_ratio
            phi = math.acos(1 - 2 * (i + 0.5) / n)
            
            x = self.sphere_radius * math.sin(phi) * math.cos(theta)
            y = self.sphere_radius * math.sin(phi) * math.sin(theta) + 1.6  # Eye height
            z = self.sphere_radius * math.cos(phi)
            
            spatial_nodes.append(SpatialNode(
                id=node.get("id", f"node_{i}"),
                type=node.get("type", "insight"),
                label=node.get("label", "")[:30],
                position={"x": x, "y": y, "z": z},
                scale=1.0 if node.get("type") == "insight" else 1.5,
                color=self._node_color(node.get("type", "insight")),
                metadata=node
            ))
        
        return spatial_nodes
    
    def _layer_layout(self, nodes: List[Dict]) -> List[SpatialNode]:
        """Arrange nodes in horizontal layers by type"""
        # Group by type
        type_groups = {}
        for node in nodes:
            node_type = node.get("type", "other")
            if node_type not in type_groups:
                type_groups[node_type] = []
            type_groups[node_type].append(node)
        
        spatial_nodes = []
        layer_height = 1.2
        current_layer = 0
        
        for node_type, group in type_groups.items():
            n = len(group)
            y = 1.0 + current_layer * layer_height
            
            for i, node in enumerate(group):
                # Arrange in a circle at this height
                angle = 2 * math.pi * i / n if n > 0 else 0
                x = self.cluster_spread * math.cos(angle)
                z = self.cluster_spread * math.sin(angle)
                
                spatial_nodes.append(SpatialNode(
                    id=node.get("id", f"node_{len(spatial_nodes)}"),
                    type=node_type,
                    label=node.get("label", "")[:30],
                    position={"x": x, "y": y, "z": z},
                    scale=1.0,
                    color=self._node_color(node_type),
                    metadata=node
                ))
            
            current_layer += 1
        
        return spatial_nodes
    
    def _force_layout(self, nodes: List[Dict], edges: List[Dict]) -> List[SpatialNode]:
        """Simple force-directed layout in 3D"""
        import random
        
        # Initialize random positions
        positions = {
            node.get("id", f"node_{i}"): {
                "x": random.uniform(-2, 2),
                "y": random.uniform(0.5, 2.5),
                "z": random.uniform(-2, 2)
            }
            for i, node in enumerate(nodes)
        }
        
        # Build adjacency for forces
        adjacency = {}
        for edge in edges:
            s, t = edge.get("source"), edge.get("target")
            if s not in adjacency:
                adjacency[s] = []
            if t not in adjacency:
                adjacency[t] = []
            adjacency[s].append(t)
            adjacency[t].append(s)
        
        # Simple force simulation (few iterations)
        for _ in range(50):
            forces = {nid: {"x": 0, "y": 0, "z": 0} for nid in positions}
            
            # Repulsion between all pairs
            node_ids = list(positions.keys())
            for i, n1 in enumerate(node_ids):
                for n2 in node_ids[i+1:]:
                    p1, p2 = positions[n1], positions[n2]
                    dx = p1["x"] - p2["x"]
                    dy = p1["y"] - p2["y"]
                    dz = p1["z"] - p2["z"]
                    dist = math.sqrt(dx*dx + dy*dy + dz*dz) + 0.01
                    
                    force = 0.5 / (dist * dist)
                    forces[n1]["x"] += dx * force
                    forces[n1]["y"] += dy * force
                    forces[n1]["z"] += dz * force
                    forces[n2]["x"] -= dx * force
                    forces[n2]["y"] -= dy * force
                    forces[n2]["z"] -= dz * force
            
            # Attraction along edges
            for edge in edges:
                s, t = edge.get("source"), edge.get("target")
                if s in positions and t in positions:
                    p1, p2 = positions[s], positions[t]
                    dx = p2["x"] - p1["x"]
                    dy = p2["y"] - p1["y"]
                    dz = p2["z"] - p1["z"]
                    dist = math.sqrt(dx*dx + dy*dy + dz*dz) + 0.01
                    
                    force = 0.1 * dist
                    forces[s]["x"] += dx * force
                    forces[s]["y"] += dy * force
                    forces[s]["z"] += dz * force
                    forces[t]["x"] -= dx * force
                    forces[t]["y"] -= dy * force
                    forces[t]["z"] -= dz * force
            
            # Apply forces
            for nid in positions:
                positions[nid]["x"] += forces[nid]["x"] * 0.1
                positions[nid]["y"] = max(0.5, positions[nid]["y"] + forces[nid]["y"] * 0.1)
                positions[nid]["z"] += forces[nid]["z"] * 0.1
        
        # Create spatial nodes
        spatial_nodes = []
        for node in nodes:
            nid = node.get("id", f"node_{len(spatial_nodes)}")
            pos = positions.get(nid, {"x": 0, "y": 1.6, "z": 0})
            
            spatial_nodes.append(SpatialNode(
                id=nid,
                type=node.get("type", "insight"),
                label=node.get("label", "")[:30],
                position=pos,
                scale=1.0,
                color=self._node_color(node.get("type", "insight")),
                metadata=node
            ))
        
        return spatial_nodes
    
    def _node_color(self, node_type: str) -> str:
        """Get color for node type"""
        colors = {
            "insight": "#9B59B6",
            "domain": "#3498DB",
            "topic": "#E74C3C",
            "connection": "#2ECC71",
            "question": "#F1C40F",
            "answer": "#1ABC9C"
        }
        return colors.get(node_type, "#95A5A6")
    
    def _edge_color(self, edge_type: str) -> str:
        """Get color for edge type"""
        colors = {
            "similar": "#3498DB",
            "builds_on": "#2ECC71",
            "contradicts": "#E74C3C",
            "extends": "#9B59B6",
            "belongs_to": "#F1C40F"
        }
        return colors.get(edge_type, "#7F8C8D")
    
    def get_webxr_config(self) -> Dict[str, Any]:
        """Get WebXR configuration for the frontend"""
        return {
            "requiredFeatures": ["local-floor", "hit-test"],
            "optionalFeatures": ["hand-tracking", "dom-overlay"],
            "renderer": {
                "antialias": True,
                "alpha": True,
                "powerPreference": "high-performance"
            },
            "interaction": {
                "pointer": True,
                "gaze": True,
                "hand": True
            },
            "defaults": {
                "nodeSize": 0.15,
                "edgeWidth": 0.01,
                "labelScale": 0.1,
                "ambient_light": 0.6,
                "directional_light": 0.8
            }
        }
    
    def get_aframe_components(self) -> str:
        """Get A-Frame component definitions for the frontend"""
        return """
<!-- UnifiedAi A-Frame Components -->
<script>
AFRAME.registerComponent('unified-node', {
    schema: {
        type: {type: 'string', default: 'insight'},
        label: {type: 'string', default: ''},
        color: {type: 'color', default: '#9B59B6'}
    },
    init: function() {
        const el = this.el;
        const data = this.data;
        
        // Create sphere for node
        el.setAttribute('geometry', {primitive: 'sphere', radius: 0.15});
        el.setAttribute('material', {color: data.color, metalness: 0.3, roughness: 0.7});
        
        // Add label
        if (data.label) {
            const label = document.createElement('a-text');
            label.setAttribute('value', data.label);
            label.setAttribute('position', '0 0.25 0');
            label.setAttribute('align', 'center');
            label.setAttribute('scale', '0.3 0.3 0.3');
            label.setAttribute('color', '#FFFFFF');
            el.appendChild(label);
        }
        
        // Add glow effect
        el.setAttribute('animation__glow', {
            property: 'material.emissive',
            from: '#000000',
            to: data.color,
            dur: 2000,
            loop: true,
            dir: 'alternate'
        });
    }
});

AFRAME.registerComponent('unified-edge', {
    schema: {
        from: {type: 'vec3'},
        to: {type: 'vec3'},
        color: {type: 'color', default: '#3498DB'}
    },
    init: function() {
        const data = this.data;
        const el = this.el;
        
        // Calculate line
        const dx = data.to.x - data.from.x;
        const dy = data.to.y - data.from.y;
        const dz = data.to.z - data.from.z;
        const length = Math.sqrt(dx*dx + dy*dy + dz*dz);
        
        // Position at midpoint
        el.setAttribute('position', {
            x: (data.from.x + data.to.x) / 2,
            y: (data.from.y + data.to.y) / 2,
            z: (data.from.z + data.to.z) / 2
        });
        
        // Create cylinder for edge
        el.setAttribute('geometry', {
            primitive: 'cylinder',
            radius: 0.01,
            height: length
        });
        el.setAttribute('material', {
            color: data.color,
            opacity: 0.7
        });
        
        // Rotate to point toward target
        el.setAttribute('look-at', {
            x: data.to.x,
            y: data.to.y,
            z: data.to.z
        });
    }
});

// Scene generator
window.UnifiedARScene = {
    generate: function(sceneData, containerEl) {
        const scene = document.createElement('a-scene');
        scene.setAttribute('embedded', '');
        scene.setAttribute('vr-mode-ui', 'enabled: true');
        
        // Add environment
        const sky = document.createElement('a-sky');
        sky.setAttribute('color', '#1a1a2e');
        scene.appendChild(sky);
        
        // Add lighting
        const ambient = document.createElement('a-light');
        ambient.setAttribute('type', 'ambient');
        ambient.setAttribute('intensity', '0.6');
        scene.appendChild(ambient);
        
        // Add nodes
        sceneData.nodes.forEach(node => {
            const el = document.createElement('a-entity');
            el.setAttribute('unified-node', {
                type: node.type,
                label: node.label,
                color: node.color
            });
            el.setAttribute('position', node.position);
            scene.appendChild(el);
        });
        
        // Add edges
        sceneData.edges.forEach(edge => {
            const sourceNode = sceneData.nodes.find(n => n.id === edge.source);
            const targetNode = sceneData.nodes.find(n => n.id === edge.target);
            if (sourceNode && targetNode) {
                const el = document.createElement('a-entity');
                el.setAttribute('unified-edge', {
                    from: sourceNode.position,
                    to: targetNode.position,
                    color: edge.color
                });
                scene.appendChild(el);
            }
        });
        
        // Add camera
        const camera = document.createElement('a-entity');
        camera.setAttribute('camera', '');
        camera.setAttribute('wasd-controls', '');
        camera.setAttribute('look-controls', '');
        camera.setAttribute('position', sceneData.camera_position || '0 1.6 3');
        scene.appendChild(camera);
        
        containerEl.appendChild(scene);
        return scene;
    }
};
</script>
"""
    
    def scene_to_dict(self, scene: SpatialScene) -> Dict[str, Any]:
        """Convert scene to dictionary for JSON serialization"""
        return {
            "id": scene.id,
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "label": n.label,
                    "position": n.position,
                    "scale": n.scale,
                    "color": n.color,
                    "metadata": n.metadata
                }
                for n in scene.nodes
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "strength": e.strength,
                    "color": e.color,
                    "style": e.style
                }
                for e in scene.edges
            ],
            "camera_position": scene.camera_position,
            "environment": scene.environment,
            "lighting": scene.lighting,
            "created_at": scene.created_at.isoformat()
        }
    
    def get_scene(self, scene_id: str) -> Optional[SpatialScene]:
        """Get a scene by ID"""
        return self.scenes.get(scene_id)
    
    def list_scenes(self) -> List[Dict[str, Any]]:
        """List all scenes"""
        return [
            {
                "id": s.id,
                "node_count": len(s.nodes),
                "edge_count": len(s.edges),
                "created_at": s.created_at.isoformat()
            }
            for s in self.scenes.values()
        ]


# Global instance
ar_interface = ARInterface()

