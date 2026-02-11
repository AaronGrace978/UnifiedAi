"""
Export Engine
Enhanced export capabilities for knowledge graphs and reports.

Supports PNG, PDF, SVG, and various document formats.
"""

import base64
import io
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Try to import visualization and PDF libraries
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.platypus.flowables import HRFlowable
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


@dataclass
class ExportResult:
    """Result of an export operation"""
    format: str
    filename: str
    data_base64: Optional[str]
    mime_type: str
    size_bytes: int
    success: bool
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


class ExportEngine:
    """
    Export engine for UnifiedAi.
    
    Provides export capabilities for:
    - Knowledge graphs as PNG/SVG
    - Research proposals as PDF
    - Insights as formatted documents
    - Session reports
    """
    
    def __init__(self):
        self.default_dpi = 150
        self.graph_colors = {
            "insight": "#9B59B6",      # Purple
            "domain": "#3498DB",        # Blue
            "connection": "#2ECC71",    # Green
            "background": "#1a1a2e",    # Dark
            "text": "#FFFFFF"           # White
        }
    
    def export_graph_png(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        title: str = "Knowledge Graph",
        width: int = 1200,
        height: int = 800
    ) -> ExportResult:
        """
        Export knowledge graph as PNG image.
        
        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries  
            title: Graph title
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            ExportResult with base64 encoded PNG
        """
        if not MATPLOTLIB_AVAILABLE:
            return ExportResult(
                format="png",
                filename=f"graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                data_base64=None,
                mime_type="image/png",
                size_bytes=0,
                success=False,
                error="matplotlib not available"
            )
        
        try:
            # Create figure
            fig, ax = plt.subplots(1, 1, figsize=(width/100, height/100), dpi=100)
            ax.set_facecolor(self.graph_colors["background"])
            fig.patch.set_facecolor(self.graph_colors["background"])
            
            # Simple force-directed layout simulation
            import math
            import random
            
            # Initialize positions
            positions = {}
            for i, node in enumerate(nodes):
                angle = 2 * math.pi * i / len(nodes)
                radius = 0.35
                positions[node.get("id", str(i))] = {
                    "x": 0.5 + radius * math.cos(angle),
                    "y": 0.5 + radius * math.sin(angle)
                }
            
            # Draw edges
            for edge in edges:
                source_id = edge.get("source")
                target_id = edge.get("target")
                if source_id in positions and target_id in positions:
                    source_pos = positions[source_id]
                    target_pos = positions[target_id]
                    
                    strength = edge.get("strength", 0.5)
                    alpha = 0.3 + strength * 0.5
                    
                    ax.plot(
                        [source_pos["x"], target_pos["x"]],
                        [source_pos["y"], target_pos["y"]],
                        color=self.graph_colors["connection"],
                        alpha=alpha,
                        linewidth=1 + strength * 2
                    )
            
            # Draw nodes
            for node in nodes:
                node_id = node.get("id", "")
                pos = positions.get(node_id, {"x": 0.5, "y": 0.5})
                node_type = node.get("type", "insight")
                
                color = self.graph_colors.get(node_type, self.graph_colors["insight"])
                size = 300 if node_type == "domain" else 200
                
                ax.scatter(
                    pos["x"], pos["y"],
                    c=color,
                    s=size,
                    alpha=0.8,
                    edgecolors="white",
                    linewidths=1
                )
                
                # Add label (truncated)
                label = node.get("label", node_id)[:20]
                ax.annotate(
                    label,
                    (pos["x"], pos["y"]),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha='center',
                    fontsize=8,
                    color=self.graph_colors["text"]
                )
            
            # Add title
            ax.set_title(title, fontsize=14, color=self.graph_colors["text"], pad=20)
            
            # Remove axes
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            # Add legend
            insight_patch = mpatches.Patch(color=self.graph_colors["insight"], label='Insights')
            domain_patch = mpatches.Patch(color=self.graph_colors["domain"], label='Domains')
            ax.legend(handles=[insight_patch, domain_patch], loc='upper left', 
                     facecolor=self.graph_colors["background"], labelcolor=self.graph_colors["text"])
            
            # Save to buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=self.default_dpi, 
                       facecolor=self.graph_colors["background"],
                       bbox_inches='tight', pad_inches=0.1)
            plt.close(fig)
            
            buffer.seek(0)
            image_data = buffer.getvalue()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            return ExportResult(
                format="png",
                filename=f"graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                data_base64=image_base64,
                mime_type="image/png",
                size_bytes=len(image_data),
                success=True
            )
        
        except Exception as e:
            return ExportResult(
                format="png",
                filename="error.png",
                data_base64=None,
                mime_type="image/png",
                size_bytes=0,
                success=False,
                error=str(e)
            )
    
    def export_proposal_pdf(
        self,
        proposal: Dict[str, Any]
    ) -> ExportResult:
        """
        Export research proposal as PDF.
        
        Args:
            proposal: Research proposal dictionary
            
        Returns:
            ExportResult with base64 encoded PDF
        """
        if not REPORTLAB_AVAILABLE:
            return ExportResult(
                format="pdf",
                filename="proposal.pdf",
                data_base64=None,
                mime_type="application/pdf",
                size_bytes=0,
                success=False,
                error="reportlab not available"
            )
        
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, 
                                   rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=72)
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=20
            )
            body_style = styles['Normal']
            
            story = []
            
            # Title
            story.append(Paragraph(proposal.get("title", "Research Proposal"), title_style))
            story.append(Spacer(1, 12))
            
            # Metadata
            meta_data = [
                ["Proposal ID:", proposal.get("id", "N/A")],
                ["Status:", proposal.get("status", "draft")],
                ["Created:", proposal.get("created_at", "N/A")[:10] if proposal.get("created_at") else "N/A"],
                ["Novelty Score:", f"{proposal.get('novelty_score', 0):.2f}"],
                ["Testability:", f"{proposal.get('testability_score', 0):.2f}"]
            ]
            meta_table = Table(meta_data, colWidths=[100, 300])
            meta_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(meta_table)
            story.append(Spacer(1, 20))
            
            # Horizontal line
            story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
            story.append(Spacer(1, 20))
            
            # Abstract
            story.append(Paragraph("Abstract", heading_style))
            story.append(Paragraph(proposal.get("abstract", "No abstract provided."), body_style))
            
            # Hypothesis
            story.append(Paragraph("Hypothesis", heading_style))
            story.append(Paragraph(f"<b>Primary:</b> {proposal.get('hypothesis', 'N/A')}", body_style))
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"<b>Null:</b> {proposal.get('null_hypothesis', 'N/A')}", body_style))
            
            # Research Questions
            story.append(Paragraph("Research Questions", heading_style))
            for i, q in enumerate(proposal.get("research_questions", []), 1):
                story.append(Paragraph(f"{i}. {q}", body_style))
                story.append(Spacer(1, 4))
            
            # Objectives
            story.append(Paragraph("Objectives", heading_style))
            for i, obj in enumerate(proposal.get("objectives", []), 1):
                story.append(Paragraph(f"{i}. {obj}", body_style))
                story.append(Spacer(1, 4))
            
            # Methodology
            story.append(Paragraph("Methodology", heading_style))
            methodology = proposal.get("methodology", {})
            story.append(Paragraph(f"<b>Approach:</b> {methodology.get('approach', 'N/A')}", body_style))
            story.append(Spacer(1, 6))
            
            methods = methodology.get("methods", [])
            if methods:
                story.append(Paragraph("<b>Methods:</b>", body_style))
                for method in methods:
                    story.append(Paragraph(f"  • {method}", body_style))
            
            # Expected Outcomes
            story.append(Paragraph("Expected Outcomes", heading_style))
            for outcome in proposal.get("expected_outcomes", []):
                story.append(Paragraph(f"• {outcome}", body_style))
                story.append(Spacer(1, 4))
            
            # Timeline Summary
            story.append(Paragraph("Timeline", heading_style))
            story.append(Paragraph(
                f"<b>Estimated Duration:</b> {proposal.get('estimated_duration_weeks', 0)} weeks", 
                body_style
            ))
            story.append(Paragraph(
                f"<b>Estimated Budget:</b> ${proposal.get('estimated_budget', 0):,.2f}", 
                body_style
            ))
            
            # Build PDF
            doc.build(story)
            
            buffer.seek(0)
            pdf_data = buffer.getvalue()
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            return ExportResult(
                format="pdf",
                filename=f"{proposal.get('id', 'proposal')}.pdf",
                data_base64=pdf_base64,
                mime_type="application/pdf",
                size_bytes=len(pdf_data),
                success=True
            )
        
        except Exception as e:
            return ExportResult(
                format="pdf",
                filename="error.pdf",
                data_base64=None,
                mime_type="application/pdf",
                size_bytes=0,
                success=False,
                error=str(e)
            )
    
    def export_insights_json(
        self,
        insights: List[Dict[str, Any]],
        include_metadata: bool = True
    ) -> ExportResult:
        """Export insights as formatted JSON"""
        try:
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "count": len(insights),
                "insights": insights if include_metadata else [
                    {"id": i.get("id"), "content": i.get("content")} 
                    for i in insights
                ]
            }
            
            json_str = json.dumps(export_data, indent=2, default=str)
            json_bytes = json_str.encode('utf-8')
            json_base64 = base64.b64encode(json_bytes).decode('utf-8')
            
            return ExportResult(
                format="json",
                filename=f"insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                data_base64=json_base64,
                mime_type="application/json",
                size_bytes=len(json_bytes),
                success=True
            )
        
        except Exception as e:
            return ExportResult(
                format="json",
                filename="error.json",
                data_base64=None,
                mime_type="application/json",
                size_bytes=0,
                success=False,
                error=str(e)
            )
    
    def export_session_report(
        self,
        session_data: Dict[str, Any]
    ) -> ExportResult:
        """
        Export a thinking session as a formatted report.
        
        Args:
            session_data: Session data including question, thoughts, and answer
            
        Returns:
            ExportResult with HTML report
        """
        try:
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>UnifiedAi Session Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
            background: #1a1a2e;
            color: #e0e0e0;
        }}
        h1 {{ color: #9b59b6; border-bottom: 2px solid #9b59b6; padding-bottom: 10px; }}
        h2 {{ color: #3498db; margin-top: 30px; }}
        .meta {{ color: #888; font-size: 0.9em; margin-bottom: 20px; }}
        .question {{ 
            background: #2a2a4e; 
            padding: 20px; 
            border-radius: 8px;
            border-left: 4px solid #9b59b6;
        }}
        .thought {{
            background: #2a2a4e;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .thought-type {{
            color: #3498db;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.8em;
        }}
        .answer {{
            background: #1e3a2e;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #2ecc71;
        }}
        .confidence {{
            display: inline-block;
            padding: 4px 12px;
            background: #9b59b6;
            border-radius: 20px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>🧠 UnifiedAi Session Report</h1>
    <div class="meta">
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
        Model: {session_data.get('model', 'Unknown')} |
        Iterations: {session_data.get('iterations', 0)}
    </div>
    
    <h2>Question</h2>
    <div class="question">
        {session_data.get('question', 'No question recorded')}
    </div>
    
    <h2>Thinking Process</h2>
"""
            
            for thought in session_data.get('thoughts', []):
                html += f"""
    <div class="thought">
        <span class="thought-type">{thought.get('type', 'thought')}</span>
        <p>{thought.get('content', '')}</p>
    </div>
"""
            
            html += f"""
    <h2>Final Answer</h2>
    <div class="answer">
        <span class="confidence">Confidence: {session_data.get('confidence', 0)*100:.0f}%</span>
        <p style="margin-top: 15px;">{session_data.get('final_answer', 'No answer recorded')}</p>
    </div>
    
    <div class="meta" style="margin-top: 40px; text-align: center;">
        Thinking Time: {session_data.get('thinking_time', 0):.2f} seconds
    </div>
</body>
</html>
"""
            
            html_bytes = html.encode('utf-8')
            html_base64 = base64.b64encode(html_bytes).decode('utf-8')
            
            return ExportResult(
                format="html",
                filename=f"session_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                data_base64=html_base64,
                mime_type="text/html",
                size_bytes=len(html_bytes),
                success=True
            )
        
        except Exception as e:
            return ExportResult(
                format="html",
                filename="error.html",
                data_base64=None,
                mime_type="text/html",
                size_bytes=0,
                success=False,
                error=str(e)
            )
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get available export capabilities"""
        return {
            "png": MATPLOTLIB_AVAILABLE,
            "pdf": REPORTLAB_AVAILABLE,
            "json": True,
            "html": True,
            "svg": MATPLOTLIB_AVAILABLE,
            "image_processing": PIL_AVAILABLE
        }


# Global instance
export_engine = ExportEngine()

