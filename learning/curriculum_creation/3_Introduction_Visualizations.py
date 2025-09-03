"""Curriculum visualization script for creating PNG charts and Mermaid diagrams.

This script processes curriculum files to:
1. Generate overall PNG charts showing curriculum metrics and analysis
2. Create domain-specific PNG visualizations for each curriculum:
   - Section breakdown and learning progression charts
   - Content complexity analysis with multiple metrics
   - Learning objectives distribution and density analysis
   - Technical content analysis with complexity scoring
3. Create Mermaid diagrams illustrating curriculum structure and flow
4. Analyze content complexity and learning pathways
5. Save all visualizations in structured data directories

Creates both static PNG images and interactive Mermaid diagrams with comprehensive
domain-specific analysis for each curriculum entity.
"""

import argparse
import os
from pathlib import Path
from typing import Dict, List, Tuple
import json
import re

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from src.common.logging_utils import setup_logging as common_setup_logging
from src.common.paths import data_visualizations_dir, data_written_curriculums_dir
from src.common.io import read_text, write_text


def extract_curriculum_metadata(curriculum_content: str) -> Dict[str, any]:
    """Extract metadata and metrics from curriculum content.
    
    Args:
        curriculum_content: Full curriculum text content
        
    Returns:
        Dictionary containing extracted metadata and metrics
    """
    # Extract basic metrics
    word_count = len(curriculum_content.split())
    paragraph_count = len(re.split(r'\n\s*\n', curriculum_content))
    
    # Extract sections using markdown headers
    sections = re.findall(r'^#+\s+(.+)$', curriculum_content, re.MULTILINE)
    section_count = len(sections)
    
    # Extract learning objectives (look for bullet points after "objectives" or "outcomes")
    objectives_pattern = r'(?i)(?:learning\s+)?(?:objectives|outcomes|goals)[\s\S]*?(?=\n#+|\n\n|\Z)'
    objectives_matches = re.findall(objectives_pattern, curriculum_content)
    objectives_count = 0
    for match in objectives_matches:
        objectives_count += len(re.findall(r'^\s*[-*+]\s+', match, re.MULTILINE))
    
    # Extract code blocks
    code_blocks = re.findall(r'```[\s\S]*?```', curriculum_content)
    code_block_count = len(code_blocks)
    
    # Extract mathematical content (LaTeX-style)
    math_expressions = re.findall(r'\$[^$]+\$|\\\([^)]+\\\)|\\\[[^\]]+\\\]', curriculum_content)
    math_count = len(math_expressions)
    
    return {
        'word_count': word_count,
        'paragraph_count': paragraph_count,
        'section_count': section_count,
        'sections': sections,
        'objectives_count': objectives_count,
        'code_block_count': code_block_count,
        'math_expressions_count': math_count,
        'words_per_section': word_count / max(section_count, 1),
        'words_per_paragraph': word_count / max(paragraph_count, 1),
    }


def create_curriculum_metrics_chart(curricula_data: List[Dict], output_path: Path) -> None:
    """Create PNG charts showing curriculum metrics.
    
    Args:
        curricula_data: List of curriculum metadata dictionaries
        output_path: Path to save the PNG chart
        
    Raises:
        ValueError: If curricula_data is empty or invalid
        RuntimeError: If matplotlib/plotting fails
    """
    if not curricula_data:
        raise ValueError("No curriculum data provided for chart creation")
    
    # Validate required fields
    required_fields = ['entity_name', 'word_count', 'section_count', 'objectives_count', 'code_block_count', 'math_expressions_count', 'words_per_section']
    for i, data in enumerate(curricula_data):
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Curriculum data {i} missing required field: {field}")
    
    try:
        # Convert to DataFrame for easier plotting
        df = pd.DataFrame(curricula_data)
        
        # Set up the plotting style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Create a figure with multiple subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Active Inference Curriculum Analysis', fontsize=16, fontweight='bold')
        
        # Chart 1: Word count by entity
        axes[0, 0].bar(df['entity_name'], df['word_count'])
        axes[0, 0].set_title('Word Count by Entity')
        axes[0, 0].set_xlabel('Entity')
        axes[0, 0].set_ylabel('Word Count')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Chart 2: Section count vs objectives count
        axes[0, 1].scatter(df['section_count'], df['objectives_count'], s=100, alpha=0.7)
        axes[0, 1].set_title('Sections vs Learning Objectives')
        axes[0, 1].set_xlabel('Number of Sections')
        axes[0, 1].set_ylabel('Number of Learning Objectives')
        
        # Chart 3: Code blocks and math expressions
        x = range(len(df))
        width = 0.35
        axes[1, 0].bar([i - width/2 for i in x], df['code_block_count'], width, label='Code Blocks')
        axes[1, 0].bar([i + width/2 for i in x], df['math_expressions_count'], width, label='Math Expressions')
        axes[1, 0].set_title('Technical Content by Entity')
        axes[1, 0].set_xlabel('Entity')
        axes[1, 0].set_ylabel('Count')
        axes[1, 0].set_xticks(x)
        axes[1, 0].set_xticklabels(df['entity_name'], rotation=45)
        axes[1, 0].legend()
        
        # Chart 4: Words per section distribution
        axes[1, 1].hist(df['words_per_section'], bins=min(10, len(df)), edgecolor='black', alpha=0.7)
        axes[1, 1].set_title('Distribution of Words per Section')
        axes[1, 1].set_xlabel('Words per Section')
        axes[1, 1].set_ylabel('Frequency')
        
        plt.tight_layout()
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
    except Exception as e:
        # Clean up any open plots
        plt.close('all')
        raise RuntimeError(f"Failed to create curriculum metrics chart: {str(e)}") from e


def create_curriculum_flow_mermaid(sections: List[str], entity_name: str) -> str:
    """Create a Mermaid diagram showing curriculum flow.
    
    Args:
        sections: List of section names
        entity_name: Name of the entity/audience
        
    Returns:
        Mermaid diagram as a string
    """
    # Create a flowchart showing the learning progression
    mermaid_content = f"""flowchart TD
    A["🎯 {entity_name}<br/>Active Inference Curriculum"] --> B["📚 Foundation"]
    
"""
    
    # Add each section as a node
    prev_node = 'B'
    for i, section in enumerate(sections):
        node_id = f'S{i+1}'
        # Clean section name for display
        clean_section = section.replace('"', "'").strip()
        if len(clean_section) > 30:
            clean_section = clean_section[:27] + "..."
        
        mermaid_content += f'    {prev_node} --> {node_id}["{clean_section}"]\n'
        prev_node = node_id
    
    # Add completion node
    mermaid_content += f'    {prev_node} --> Z["🏆 Mastery Achieved"]'
    
    return mermaid_content


def create_curriculum_structure_mermaid(curricula_data: List[Dict]) -> str:
    """Create a Mermaid diagram showing overall curriculum structure.
    
    Args:
        curricula_data: List of curriculum metadata dictionaries
        
    Returns:
        Mermaid diagram as a string
    """
    mermaid_content = """graph TB
    subgraph "🧠 Active Inference Curricula"
        AI["Active Inference<br/>Core Concepts"]
"""
    
    for i, curriculum in enumerate(curricula_data):
        entity = curriculum['entity_name']
        sections = curriculum.get('sections', [])
        
        # Add entity node
        entity_node = f'E{i+1}'
        mermaid_content += f'        AI --> {entity_node}["{entity}\\n({len(sections)} sections)"]\n'
        
        # Add key sections as sub-nodes
        for j, section in enumerate(sections[:3]):  # Show first 3 sections
            section_node = f'E{i+1}S{j+1}'
            clean_section = section.replace('"', "'")[:20]
            mermaid_content += f'        {entity_node} --> {section_node}["{clean_section}..."]\n'
    
    mermaid_content += "    end"
    return mermaid_content


def create_domain_section_breakdown_chart(curriculum_data: Dict, output_path: Path) -> None:
    """Create a PNG chart showing section breakdown for a specific domain.
    
    Args:
        curriculum_data: Curriculum metadata dictionary for a single domain
        output_path: Path to save the PNG chart
        
    Raises:
        ValueError: If curriculum_data is invalid
        RuntimeError: If matplotlib/plotting fails
    """
    if not curriculum_data or 'sections' not in curriculum_data:
        raise ValueError("Invalid curriculum data for section breakdown chart")
    
    sections = curriculum_data.get('sections', [])
    entity_name = curriculum_data.get('entity_name', 'Unknown Entity')
    
    if not sections:
        print(f"Warning: No sections found for {entity_name}")
        return
    
    try:
        plt.style.use('default')
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        fig.suptitle(f'{entity_name} - Active Inference Curriculum Structure', fontsize=16, fontweight='bold')
        
        # Chart 1: Section count and distribution
        section_lengths = [len(section) for section in sections]
        ax1.bar(range(len(sections)), section_lengths, color='steelblue', alpha=0.7)
        ax1.set_title('Section Title Lengths')
        ax1.set_xlabel('Section Index')
        ax1.set_ylabel('Title Length (characters)')
        ax1.grid(True, alpha=0.3)
        
        # Chart 2: Section progression overview
        section_numbers = list(range(1, len(sections) + 1))
        cumulative_complexity = [i * (curriculum_data.get('words_per_section', 100)) for i in section_numbers]
        
        ax2.plot(section_numbers, cumulative_complexity, marker='o', linewidth=2, markersize=8, color='darkgreen')
        ax2.set_title('Cumulative Learning Complexity')
        ax2.set_xlabel('Section Number')
        ax2.set_ylabel('Cumulative Content Volume')
        ax2.grid(True, alpha=0.3)
        ax2.fill_between(section_numbers, cumulative_complexity, alpha=0.3, color='lightgreen')
        
        plt.tight_layout()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
    except Exception as e:
        plt.close('all')
        raise RuntimeError(f"Failed to create section breakdown chart for {entity_name}: {str(e)}") from e


def create_domain_complexity_chart(curriculum_data: Dict, output_path: Path) -> None:
    """Create a PNG chart showing content complexity analysis for a specific domain.
    
    Args:
        curriculum_data: Curriculum metadata dictionary for a single domain
        output_path: Path to save the PNG chart
        
    Raises:
        ValueError: If curriculum_data is invalid
        RuntimeError: If matplotlib/plotting fails
    """
    if not curriculum_data:
        raise ValueError("Invalid curriculum data for complexity chart")
    
    entity_name = curriculum_data.get('entity_name', 'Unknown Entity')
    
    try:
        plt.style.use('default')
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'{entity_name} - Content Complexity Analysis', fontsize=16, fontweight='bold')
        
        # Chart 1: Content metrics pie chart
        metrics = {
            'Code Blocks': curriculum_data.get('code_block_count', 0),
            'Math Expressions': curriculum_data.get('math_expressions_count', 0),
            'Learning Objectives': curriculum_data.get('objectives_count', 0),
            'Sections': curriculum_data.get('section_count', 0)
        }
        
        # Filter out zero values for pie chart
        non_zero_metrics = {k: v for k, v in metrics.items() if v > 0}
        if non_zero_metrics:
            ax1.pie(non_zero_metrics.values(), labels=non_zero_metrics.keys(), autopct='%1.1f%%', startangle=90)
            ax1.set_title('Content Type Distribution')
        else:
            ax1.text(0.5, 0.5, 'No technical content\nfound', ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title('Content Type Distribution')
        
        # Chart 2: Word distribution analysis
        word_count = curriculum_data.get('word_count', 0)
        words_per_section = curriculum_data.get('words_per_section', 0)
        words_per_paragraph = curriculum_data.get('words_per_paragraph', 0)
        
        categories = ['Total Words', 'Words/Section', 'Words/Paragraph']
        values = [word_count, words_per_section, words_per_paragraph]
        colors = ['lightcoral', 'lightskyblue', 'lightgreen']
        
        bars = ax2.bar(categories, values, color=colors, alpha=0.7)
        ax2.set_title('Word Distribution Metrics')
        ax2.set_ylabel('Count')
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01, 
                    f'{int(value)}', ha='center', va='bottom')
        
        # Chart 3: Technical content complexity
        tech_categories = ['Code Blocks', 'Math Expressions']
        tech_values = [curriculum_data.get('code_block_count', 0), curriculum_data.get('math_expressions_count', 0)]
        
        ax3.barh(tech_categories, tech_values, color=['orange', 'purple'], alpha=0.7)
        ax3.set_title('Technical Content Complexity')
        ax3.set_xlabel('Count')
        
        # Chart 4: Learning structure metrics
        structure_categories = ['Sections', 'Paragraphs', 'Objectives']
        structure_values = [
            curriculum_data.get('section_count', 0),
            curriculum_data.get('paragraph_count', 0),
            curriculum_data.get('objectives_count', 0)
        ]
        
        ax4.bar(structure_categories, structure_values, color=['gold', 'silver', 'bronze'], alpha=0.7)
        ax4.set_title('Learning Structure Metrics')
        ax4.set_ylabel('Count')
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
    except Exception as e:
        plt.close('all')
        raise RuntimeError(f"Failed to create complexity chart for {entity_name}: {str(e)}") from e


def create_domain_learning_objectives_chart(curriculum_data: Dict, output_path: Path) -> None:
    """Create a PNG chart focusing on learning objectives for a specific domain.
    
    Args:
        curriculum_data: Curriculum metadata dictionary for a single domain
        output_path: Path to save the PNG chart
        
    Raises:
        ValueError: If curriculum_data is invalid
        RuntimeError: If matplotlib/plotting fails
    """
    if not curriculum_data:
        raise ValueError("Invalid curriculum data for learning objectives chart")
    
    entity_name = curriculum_data.get('entity_name', 'Unknown Entity')
    
    try:
        plt.style.use('default')
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        fig.suptitle(f'{entity_name} - Learning Objectives Analysis', fontsize=16, fontweight='bold')
        
        # Chart 1: Objectives vs Sections ratio
        objectives_count = curriculum_data.get('objectives_count', 0)
        section_count = curriculum_data.get('section_count', 1)
        objectives_per_section = objectives_count / section_count
        
        categories = ['Learning Objectives', 'Sections', 'Objectives per Section']
        values = [objectives_count, section_count, objectives_per_section]
        colors = ['forestgreen', 'royalblue', 'darkorange']
        
        bars = ax1.bar(categories, values, color=colors, alpha=0.7)
        ax1.set_title('Learning Structure Overview')
        ax1.set_ylabel('Count / Ratio')
        
        # Add value labels
        for bar, value in zip(bars, values):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01,
                    f'{value:.1f}', ha='center', va='bottom')
        
        # Chart 2: Content density analysis
        word_count = curriculum_data.get('word_count', 0)
        words_per_objective = word_count / max(objectives_count, 1)
        words_per_section = curriculum_data.get('words_per_section', 0)
        
        density_data = {
            'Words per Objective': words_per_objective,
            'Words per Section': words_per_section,
            'Total Word Count': word_count / 100  # Scale down for visualization
        }
        
        x_pos = range(len(density_data))
        ax2.bar(x_pos, density_data.values(), color=['teal', 'coral', 'mediumpurple'], alpha=0.7)
        ax2.set_title('Content Density Metrics')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(density_data.keys(), rotation=45, ha='right')
        ax2.set_ylabel('Words (Total/100)')
        
        # Add grid for better readability
        ax1.grid(True, alpha=0.3)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
    except Exception as e:
        plt.close('all')
        raise RuntimeError(f"Failed to create learning objectives chart for {entity_name}: {str(e)}") from e


def create_domain_technical_content_chart(curriculum_data: Dict, output_path: Path) -> None:
    """Create a PNG chart focusing on technical content for a specific domain.
    
    Args:
        curriculum_data: Curriculum metadata dictionary for a single domain
        output_path: Path to save the PNG chart
        
    Raises:
        ValueError: If curriculum_data is invalid
        RuntimeError: If matplotlib/plotting fails
    """
    if not curriculum_data:
        raise ValueError("Invalid curriculum data for technical content chart")
    
    entity_name = curriculum_data.get('entity_name', 'Unknown Entity')
    
    try:
        plt.style.use('default')
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'{entity_name} - Technical Content Analysis', fontsize=16, fontweight='bold')
        
        # Chart 1: Technical content overview
        tech_metrics = {
            'Code Blocks': curriculum_data.get('code_block_count', 0),
            'Math Expressions': curriculum_data.get('math_expressions_count', 0)
        }
        
        if sum(tech_metrics.values()) > 0:
            ax1.pie(tech_metrics.values(), labels=tech_metrics.keys(), autopct='%1.1f%%', 
                   colors=['lightblue', 'lightcoral'], startangle=90)
            ax1.set_title('Technical Content Distribution')
        else:
            ax1.text(0.5, 0.5, 'No technical content\nidentified', ha='center', va='center', 
                    transform=ax1.transAxes, fontsize=12, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
            ax1.set_title('Technical Content Distribution')
        
        # Chart 2: Content complexity score
        complexity_score = (
            curriculum_data.get('code_block_count', 0) * 3 +  # Code blocks are complex
            curriculum_data.get('math_expressions_count', 0) * 2 +  # Math expressions are moderately complex
            curriculum_data.get('objectives_count', 0) * 1  # Objectives indicate structure
        )
        
        total_content = curriculum_data.get('section_count', 1)
        normalized_complexity = complexity_score / total_content
        
        # Create a gauge-like visualization
        categories = ['Basic', 'Intermediate', 'Advanced', 'Expert']
        thresholds = [5, 15, 30, float('inf')]
        colors = ['green', 'yellow', 'orange', 'red']
        
        level = 0
        for i, threshold in enumerate(thresholds):
            if normalized_complexity <= threshold:
                level = i
                break
        
        ax2.bar(categories, [10, 10, 10, 10], color=['lightgray']*4, alpha=0.3)
        ax2.bar(categories[level], 10, color=colors[level], alpha=0.8)
        ax2.set_title(f'Complexity Level: {categories[level]}')
        ax2.set_ylabel('Level Indicator')
        ax2.set_ylim(0, 12)
        
        # Chart 3: Technical density per section
        tech_density = (curriculum_data.get('code_block_count', 0) + 
                       curriculum_data.get('math_expressions_count', 0)) / max(curriculum_data.get('section_count', 1), 1)
        
        density_categories = ['Technical Elements', 'Per Section Density']
        density_values = [curriculum_data.get('code_block_count', 0) + curriculum_data.get('math_expressions_count', 0), 
                         tech_density]
        
        ax3.bar(density_categories, density_values, color=['steelblue', 'darkgreen'], alpha=0.7)
        ax3.set_title('Technical Content Density')
        ax3.set_ylabel('Count / Density')
        
        # Chart 4: Learning curve estimation
        sections = list(range(1, curriculum_data.get('section_count', 1) + 1))
        estimated_difficulty = [i * normalized_complexity * 0.1 + 1 for i in sections]
        
        if len(sections) > 1:
            ax4.plot(sections, estimated_difficulty, marker='o', linewidth=2, markersize=6, color='darkred')
            ax4.fill_between(sections, estimated_difficulty, alpha=0.3, color='pink')
            ax4.set_title('Estimated Learning Curve')
            ax4.set_xlabel('Section Number')
            ax4.set_ylabel('Relative Difficulty')
            ax4.grid(True, alpha=0.3)
        else:
            ax4.text(0.5, 0.5, 'Insufficient data\nfor learning curve', ha='center', va='center', 
                    transform=ax4.transAxes, fontsize=12)
            ax4.set_title('Estimated Learning Curve')
        
        plt.tight_layout()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
    except Exception as e:
        plt.close('all')
        raise RuntimeError(f"Failed to create technical content chart for {entity_name}: {str(e)}") from e


def collect_curriculum_data(curriculum_dir: Path) -> List[Dict]:
    """Collect data from all curriculum files.
    
    Args:
        curriculum_dir: Directory containing curriculum files
        
    Returns:
        List of curriculum data dictionaries
        
    Raises:
        FileNotFoundError: If curriculum directory doesn't exist
    """
    if not curriculum_dir.exists():
        raise FileNotFoundError(f"Curriculum directory not found: {curriculum_dir}")
    
    curricula_data = []
    processed_count = 0
    error_count = 0
    
    # Find all complete curriculum files
    curriculum_files = list(curriculum_dir.rglob("complete_curriculum_*.md"))
    if not curriculum_files:
        print(f"Warning: No complete_curriculum_*.md files found in {curriculum_dir}")
        return curricula_data
    
    print(f"Found {len(curriculum_files)} curriculum files to process")
    
    for curriculum_file in curriculum_files:
        entity_name = curriculum_file.parent.name
        
        try:
            # Check file size
            file_size = curriculum_file.stat().st_size
            if file_size == 0:
                print(f"Warning: Empty curriculum file: {curriculum_file}")
                error_count += 1
                continue
            
            content = read_text(curriculum_file)
            if not content.strip():
                print(f"Warning: Curriculum file has no content: {curriculum_file}")
                error_count += 1
                continue
            
            metadata = extract_curriculum_metadata(content)
            metadata['entity_name'] = entity_name
            metadata['file_path'] = str(curriculum_file)
            curricula_data.append(metadata)
            processed_count += 1
            print(f"Processed curriculum for entity: {entity_name}")
            
        except Exception as e:
            error_count += 1
            print(f"Error processing {curriculum_file}: {e}")
            continue
    
    print(f"Curriculum data collection complete: {processed_count} processed, {error_count} errors")
    return curricula_data


def main(input_folder: str = None, output_folder: str = None) -> None:
    """Main function to generate curriculum visualizations.
    
    Args:
        input_folder: Path to curriculum files (defaults to data/written_curriculums)
        output_folder: Path to save visualizations (defaults to data/visualizations)
    """
    logger = common_setup_logging()
    logger.info("Starting curriculum visualization generation")
    
    # Setup paths
    input_dir = Path(input_folder) if input_folder else data_written_curriculums_dir()
    output_dir = Path(output_folder) if output_folder else data_visualizations_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Processing curricula from: {input_dir}")
    logger.info(f"Saving visualizations to: {output_dir}")
    
    try:
        # Collect curriculum data
        curricula_data = collect_curriculum_data(input_dir)
        
        if not curricula_data:
            logger.warning("No curriculum files found to visualize")
            return
        
        logger.info(f"Found {len(curricula_data)} curricula to visualize")
        
        # Create PNG metrics chart
        metrics_chart_path = output_dir / "curriculum_metrics.png"
        create_curriculum_metrics_chart(curricula_data, metrics_chart_path)
        logger.info(f"Created metrics chart: {metrics_chart_path}")
        
        # Create overall structure Mermaid diagram
        structure_diagram = create_curriculum_structure_mermaid(curricula_data)
        structure_path = output_dir / "curriculum_structure.mmd"
        write_text(structure_path, structure_diagram)
        logger.info(f"Created structure diagram: {structure_path}")
        
        # Create individual flow diagrams and domain-specific PNG charts for each curriculum
        for curriculum in curricula_data:
            entity_name = curriculum['entity_name']
            sections = curriculum.get('sections', [])
            
            if sections:
                # Create Mermaid flow diagram
                flow_diagram = create_curriculum_flow_mermaid(sections, entity_name)
                flow_path = output_dir / f"{entity_name}_flow.mmd"
                write_text(flow_path, flow_diagram)
                logger.info(f"Created flow diagram for {entity_name}: {flow_path}")
                
            # Create domain-specific PNG visualizations
            try:
                # Section breakdown chart
                section_chart_path = output_dir / f"{entity_name}_section_breakdown.png"
                create_domain_section_breakdown_chart(curriculum, section_chart_path)
                logger.info(f"Created section breakdown chart for {entity_name}: {section_chart_path}")
                
                # Content complexity chart
                complexity_chart_path = output_dir / f"{entity_name}_complexity_analysis.png"
                create_domain_complexity_chart(curriculum, complexity_chart_path)
                logger.info(f"Created complexity analysis chart for {entity_name}: {complexity_chart_path}")
                
                # Learning objectives chart
                objectives_chart_path = output_dir / f"{entity_name}_learning_objectives.png"
                create_domain_learning_objectives_chart(curriculum, objectives_chart_path)
                logger.info(f"Created learning objectives chart for {entity_name}: {objectives_chart_path}")
                
                # Technical content chart
                technical_chart_path = output_dir / f"{entity_name}_technical_content.png"
                create_domain_technical_content_chart(curriculum, technical_chart_path)
                logger.info(f"Created technical content chart for {entity_name}: {technical_chart_path}")
                
            except Exception as e:
                logger.warning(f"Failed to create some visualizations for {entity_name}: {e}")
                continue
        
        # Save detailed metrics as JSON
        metrics_path = output_dir / "curriculum_metrics.json"
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(curricula_data, f, indent=2, default=str)
        logger.info(f"Saved detailed metrics: {metrics_path}")
        
        logger.info("Visualization generation completed successfully")
        
    except Exception as e:
        logger.error(f"Error generating visualizations: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate PNG charts and Mermaid diagrams for curriculum visualization.")
    parser.add_argument("--input", 
                       help="Path to directory containing curriculum files (default: data/written_curriculums)")
    parser.add_argument("--output", 
                       help="Path to save visualization outputs (default: data/visualizations)")
    args = parser.parse_args()
    
    main(args.input, args.output)


