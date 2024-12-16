import os
import sys
import logging
import argparse
import traceback
from typing import List, Tuple, Dict
import numpy as np
import spacy
from pathlib import Path
import re

# Set matplotlib backend to non-GUI
import matplotlib
matplotlib.use('Agg')  # Must be before importing pyplot
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA, LatentDirichletAllocation
from sklearn.manifold import TSNE
import networkx as nx
from collections import Counter
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def collect_curriculum_files(base_dir: str) -> List[Tuple[str, str]]:
    """
    Collect all complete curriculum files from Written_Curriculums directory.
    
    Returns:
        List of tuples (entity_name, curriculum_file_path)
    """
    curriculum_files = []
    
    try:
        # Setup directory
        curriculum_dir = Path(base_dir) / 'Written_Curriculums'
        curriculum_dir.mkdir(parents=True, exist_ok=True)
        
        # Recursively collect all complete curriculum files
        for curr_file in curriculum_dir.rglob("complete_curriculum_*.md"):
            entity_name = curr_file.parent.name
            curriculum_files.append((entity_name, str(curr_file)))
        
        logger.info(f"Found {len(curriculum_files)} complete curriculum files")
        return curriculum_files
    
    except Exception as e:
        logger.error(f"Error collecting curriculum files: {e}")
        return []

def preprocess_text(text: str, nlp) -> str:
    """Preprocess text for analysis."""
    doc = nlp(text)
    tokens = [token.lemma_.lower() for token in doc 
             if not token.is_stop and not token.is_punct 
             and token.text.strip()]
    return " ".join(tokens)

def analyze_curriculum_content(curriculum_files: List[Tuple[str, str]], 
                             output_dir: str,
                             nlp) -> None:
    """Analyze curriculum content and generate visualizations."""
    
    # Prepare data structures
    curriculums = []
    entity_labels = []
    
    # Collect documents
    for entity_name, curr_file in curriculum_files:
        try:
            with open(curr_file, 'r', encoding='utf-8') as f:
                content = f.read()
                curriculums.append(content)
                entity_labels.append(entity_name)
        except Exception as e:
            logger.error(f"Error reading curriculum file {curr_file}: {e}")
            continue
    
    if not curriculums:
        logger.error("No valid curriculum content found")
        return
    
    # Create visualization directories
    vis_dir = Path(output_dir)
    for subdir in ['content_analysis', 'learning_paths', 'concept_maps', 'metrics']:
        (vis_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    try:
        # Preprocess texts
        logger.info("Preprocessing curriculum texts...")
        processed_curriculums = [preprocess_text(doc, nlp) for doc in curriculums]
        
        # Create TF-IDF vectors
        logger.info("Creating TF-IDF vectors...")
        vectorizer = TfidfVectorizer(
            max_features=1000,
            min_df=2,
            max_df=0.95,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        # Fit and transform
        curriculum_tfidf = vectorizer.fit_transform(processed_curriculums)
        
        # Generate visualizations
        logger.info("Generating content analysis...")
        plot_content_analysis(curriculum_tfidf, entity_labels, 
                            vectorizer, vis_dir / 'content_analysis')
        
        logger.info("Generating learning paths...")
        plot_learning_paths(curriculums, entity_labels, 
                          vis_dir / 'learning_paths')
        
        logger.info("Generating concept maps...")
        plot_concept_maps(processed_curriculums, entity_labels,
                         vis_dir / 'concept_maps')
        
        logger.info("Generating curriculum metrics...")
        generate_curriculum_metrics(curriculums, entity_labels,
                                 vis_dir / 'metrics')
        
    except Exception as e:
        logger.error(f"Error in curriculum analysis: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")

def generate_curriculum_metrics(curriculum_docs: List[str], 
                              entity_labels: List[str],
                              output_dir: str) -> None:
    """Generate curriculum metrics and visualizations."""
    try:
        metrics = []
        for i, curriculum in enumerate(curriculum_docs):
            # Calculate metrics
            words = len(curriculum.split())
            sections = len(re.findall(r'^#+\s+(.+)$', curriculum, re.MULTILINE))
            paragraphs = len(re.split(r'\n\s*\n', curriculum))
            
            metrics.append({
                'Entity': entity_labels[i],
                'Total Words': words,
                'Sections': sections,
                'Paragraphs': paragraphs,
                'Words per Section': words / max(sections, 1),
                'Words per Paragraph': words / max(paragraphs, 1)
            })
        
        # Create metrics DataFrame
        df = pd.DataFrame(metrics)
        
        # Save metrics to CSV
        df.to_csv(output_dir / 'curriculum_metrics.csv', index=False)
        
        # Plot distributions
        plt.figure(figsize=(15, 10))
        
        # Plot word count distribution
        plt.subplot(2, 2, 1)
        plt.bar(entity_labels, df['Total Words'], color='skyblue')
        plt.title('Word Count Distribution')
        plt.xticks(rotation=45, ha='right')
        plt.ylabel('Words')
        
        # Plot sections distribution
        plt.subplot(2, 2, 2)
        plt.bar(entity_labels, df['Sections'], color='lightgreen')
        plt.title('Section Count Distribution')
        plt.xticks(rotation=45, ha='right')
        plt.ylabel('Sections')
        
        # Plot words per section
        plt.subplot(2, 2, 3)
        plt.bar(entity_labels, df['Words per Section'], color='lightcoral')
        plt.title('Words per Section Distribution')
        plt.xticks(rotation=45, ha='right')
        plt.ylabel('Words/Section')
        
        # Plot words per paragraph
        plt.subplot(2, 2, 4)
        plt.bar(entity_labels, df['Words per Paragraph'], color='plum')
        plt.title('Words per Paragraph Distribution')
        plt.xticks(rotation=45, ha='right')
        plt.ylabel('Words/Paragraph')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'metrics_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Generate summary statistics
        summary_stats = df.describe()
        summary_stats.to_csv(output_dir / 'summary_statistics.csv')
        
        logger.info(f"Curriculum metrics saved to {output_dir}")
        
    except Exception as e:
        logger.error(f"Error generating curriculum metrics: {e}")

def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        import matplotlib
        import seaborn
        import wordcloud
        import sklearn
        import networkx
        import pandas
        import spacy
        
        # Try loading spaCy model
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error("spaCy model 'en_core_web_sm' not found. Installing...")
            os.system("python -m spacy download en_core_web_sm")
        
        logger.info("All dependencies checked successfully")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {str(e)}")
        logger.error("Please install required packages using: pip install matplotlib seaborn wordcloud scikit-learn networkx pandas spacy")
        return False

def plot_safely(func):
    """Decorator to handle plotting errors and cleanup."""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            plt.close('all')  # Cleanup
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            plt.close('all')  # Cleanup even on error
            return None
    return wrapper

@plot_safely
def plot_content_analysis(curriculum_tfidf, entity_labels, vectorizer, output_dir):
    """Generate enhanced content analysis visualizations."""
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 1. Enhanced Topic Distribution with Hierarchical Clustering
        n_topics = min(8, len(entity_labels))  # Adjust number of topics based on data size
        lda = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=42,
            max_iter=100,
            learning_method='batch'
        )
        topics = lda.fit_transform(curriculum_tfidf)
        
        # Get top words for each topic
        n_top_words = 10
        feature_names = vectorizer.get_feature_names_out()
        topic_summaries = []
        for topic_idx, topic in enumerate(lda.components_):
            top_words = [feature_names[i] for i in topic.argsort()[:-n_top_words-1:-1]]
            topic_summaries.append(f"Topic {topic_idx+1}\n" + "\n".join(top_words))
        
        # Plot topic distribution heatmap
        plt.figure(figsize=(20, 12))
        g = sns.clustermap(topics, 
                          xticklabels=[f'Topic {i+1}' for i in range(n_topics)],
                          yticklabels=entity_labels,
                          cmap='YlOrRd',
                          figsize=(20, 12),
                          dendrogram_ratio=0.2,
                          cbar_pos=(0.02, 0.8, 0.03, 0.2))
        plt.setp(g.ax_heatmap.get_xticklabels(), rotation=45, ha='right')
        plt.setp(g.ax_heatmap.get_yticklabels(), rotation=0)
        g.fig.suptitle('Hierarchical Clustering of Curriculum Topics', fontsize=16, y=1.02)
        plt.savefig(output_dir / 'topic_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save topic summaries
        with open(output_dir / 'topic_summaries.txt', 'w') as f:
            f.write('\n\n'.join(topic_summaries))
        
        # 2. Enhanced Key Concepts WordCloud with Frequency Analysis
        text = " ".join(vectorizer.get_feature_names_out())
        wordcloud = WordCloud(width=1600, height=800, 
                            background_color='white',
                            max_words=200,
                            collocations=True,
                            colormap='viridis').generate(text)
        
        plt.figure(figsize=(20, 10))
        plt.subplot(1, 2, 1)
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('Key Concepts Word Cloud', fontsize=16)
        
        # Add frequency distribution
        word_freq = Counter(text.split())
        top_words = dict(sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20])
        
        plt.subplot(1, 2, 2)
        plt.barh(list(top_words.keys()), list(top_words.values()), color='skyblue')
        plt.title('Top 20 Concepts Frequency', fontsize=16)
        plt.xlabel('Frequency')
        plt.tight_layout()
        plt.savefig(output_dir / 'key_concepts.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Enhanced Similarity Analysis
        similarity_matrix = (curriculum_tfidf * curriculum_tfidf.T).toarray()
        
        # Hierarchical clustering of similarity matrix
        plt.figure(figsize=(15, 15))
        g = sns.clustermap(similarity_matrix,
                          xticklabels=entity_labels,
                          yticklabels=entity_labels,
                          cmap='YlOrRd',
                          annot=True,
                          fmt='.2f',
                          figsize=(15, 15),
                          dendrogram_ratio=0.2,
                          cbar_pos=(0.02, 0.8, 0.03, 0.2))
        plt.setp(g.ax_heatmap.get_xticklabels(), rotation=45, ha='right')
        plt.setp(g.ax_heatmap.get_yticklabels(), rotation=0)
        g.fig.suptitle('Hierarchical Clustering of Curriculum Similarities', fontsize=16, y=1.02)
        plt.savefig(output_dir / 'similarity_matrix.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 4. Enhanced Content Distribution Analysis
        # PCA
        pca = PCA(n_components=2)
        curriculum_pca = pca.fit_transform(curriculum_tfidf.toarray())
        explained_var_ratio = pca.explained_variance_ratio_
        
        # t-SNE for comparison
        tsne = TSNE(n_components=2, random_state=42, perplexity=min(len(entity_labels)-1, 30))
        curriculum_tsne = tsne.fit_transform(curriculum_tfidf.toarray())
        
        plt.figure(figsize=(20, 10))
        
        # PCA plot
        plt.subplot(1, 2, 1)
        scatter = plt.scatter(curriculum_pca[:, 0], curriculum_pca[:, 1], 
                            c=range(len(entity_labels)), cmap='viridis', s=200)
        for i, label in enumerate(entity_labels):
            plt.annotate(label, (curriculum_pca[i, 0], curriculum_pca[i, 1]),
                        xytext=(5, 5), textcoords='offset points', fontsize=10)
        plt.title(f'PCA Distribution\nExplained Variance: {sum(explained_var_ratio):.2%}', 
                 fontsize=14)
        plt.colorbar(scatter, label='Curriculum Index')
        
        # t-SNE plot
        plt.subplot(1, 2, 2)
        scatter = plt.scatter(curriculum_tsne[:, 0], curriculum_tsne[:, 1],
                            c=range(len(entity_labels)), cmap='viridis', s=200)
        for i, label in enumerate(entity_labels):
            plt.annotate(label, (curriculum_tsne[i, 0], curriculum_tsne[i, 1]),
                        xytext=(5, 5), textcoords='offset points', fontsize=10)
        plt.title('t-SNE Distribution', fontsize=14)
        plt.colorbar(scatter, label='Curriculum Index')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'content_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 5. Topic Evolution Analysis
        plt.figure(figsize=(15, 10))
        topic_evolution = pd.DataFrame(topics, columns=[f'Topic {i+1}' for i in range(n_topics)])
        topic_evolution.index = entity_labels
        
        # Plot topic evolution
        for i in range(n_topics):
            plt.plot(topic_evolution.index, topic_evolution[f'Topic {i+1}'],
                    marker='o', label=f'Topic {i+1}')
        
        plt.title('Topic Evolution Across Curriculums', fontsize=14)
        plt.xticks(rotation=45, ha='right')
        plt.ylabel('Topic Strength')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_dir / 'topic_evolution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Enhanced content analysis visualizations saved to {output_dir}")
        
    except Exception as e:
        logger.error(f"Error in content analysis plotting: {e}")
        raise

@plot_safely
def plot_learning_paths(curriculums, entity_labels, output_dir):
    """Generate enhanced learning path visualizations."""
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        for curr, entity in zip(curriculums, entity_labels):
            sections = re.findall(r'^#+\s+(.+)$', curr, re.MULTILINE)
            
            if not sections:
                logger.warning(f"No sections found for {entity}")
                continue
            
            # Create directed graph
            G = nx.DiGraph()
            for i in range(len(sections)-1):
                G.add_edge(sections[i], sections[i+1])
            
            # Calculate node metrics
            centrality = nx.betweenness_centrality(G)
            in_degree = dict(G.in_degree())
            
            # Create enhanced visualization
            plt.figure(figsize=(20, 15))
            pos = nx.spring_layout(G, k=2, iterations=50)
            
            # Draw edges with varying width based on centrality
            edge_weights = [centrality[v] for u, v in G.edges()]
            nx.draw_networkx_edges(G, pos, edge_color='gray',
                                 width=[w*5 for w in edge_weights],
                                 alpha=0.6,
                                 arrows=True,
                                 arrowsize=20)
            
            # Draw nodes with varying size based on in-degree
            node_sizes = [1000 + v*500 for v in in_degree.values()]
            node_colors = list(centrality.values())
            nodes = nx.draw_networkx_nodes(G, pos,
                                         node_size=node_sizes,
                                         node_color=node_colors,
                                         cmap=plt.cm.viridis)
            
            # Add labels with better formatting
            labels = nx.draw_networkx_labels(G, pos,
                                           font_size=8,
                                           font_weight='bold',
                                           bbox=dict(facecolor='white',
                                                   edgecolor='none',
                                                   alpha=0.7))
            
            plt.colorbar(nodes, label='Betweenness Centrality')
            plt.title(f'Learning Path: {entity}\nNode size: In-degree, Color: Centrality',
                     fontsize=16, pad=20)
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(output_dir / f'{entity}_learning_path.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # Save metrics
            metrics = {
                'section': sections,
                'centrality': [centrality[s] for s in sections],
                'in_degree': [in_degree[s] for s in sections]
            }
            pd.DataFrame(metrics).to_csv(output_dir / f'{entity}_path_metrics.csv', index=False)
        
        logger.info(f"Enhanced learning path visualizations saved to {output_dir}")
            
    except Exception as e:
        logger.error(f"Error in learning path plotting: {e}")
        raise

@plot_safely
def plot_concept_maps(processed_curriculums, entity_labels, output_dir):
    """Generate enhanced concept map visualizations."""
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        for curr, entity in zip(processed_curriculums, entity_labels):
            words = curr.split()
            if len(words) < 2:
                logger.warning(f"Insufficient content for concept map: {entity}")
                continue
            
            # Create edges with sliding window
            window_size = 3
            edges = []
            for i in range(len(words) - window_size + 1):
                window = words[i:i + window_size]
                for j in range(len(window)):
                    for k in range(j + 1, len(window)):
                        edges.append((window[j], window[k]))
            
            G = nx.Graph()
            edge_counts = Counter(edges)
            
            # Filter to keep only significant connections
            threshold = np.percentile(list(edge_counts.values()), 75)  # Keep top 25%
            significant_edges = {edge: count for edge, count in edge_counts.items() 
                              if count > threshold}
            
            if not significant_edges:
                logger.warning(f"No significant connections found for {entity}")
                continue
            
            # Create graph
            for edge, weight in significant_edges.items():
                G.add_edge(edge[0], edge[1], weight=weight)
            
            # Calculate node metrics
            centrality = nx.eigenvector_centrality(G, max_iter=1000)
            communities = list(nx.community.greedy_modularity_communities(G))
            
            # Assign community colors
            node_colors = []
            for node in G.nodes():
                for i, community in enumerate(communities):
                    if node in community:
                        node_colors.append(plt.cm.tab20(i % 20))
                        break
            
            # Create enhanced visualization
            plt.figure(figsize=(24, 18))
            pos = nx.spring_layout(G, k=2, iterations=100)
            
            # Draw edges with varying width
            edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
            max_weight = max(edge_weights)
            edge_widths = [w/max_weight * 5 for w in edge_weights]
            
            nx.draw_networkx_edges(G, pos,
                                 width=edge_widths,
                                 edge_color='gray',
                                 alpha=0.3)
            
            # Draw nodes with varying size based on centrality
            node_sizes = [v * 5000 for v in centrality.values()]
            nodes = nx.draw_networkx_nodes(G, pos,
                                         node_size=node_sizes,
                                         node_color=node_colors,
                                         alpha=0.7)
            
            # Add labels with better formatting
            labels = nx.draw_networkx_labels(G, pos,
                                           font_size=8,
                                           font_weight='bold',
                                           bbox=dict(facecolor='white',
                                                   edgecolor='none',
                                                   alpha=0.7))
            
            plt.title(f'Concept Map: {entity}\nNode size: Eigenvector Centrality, Colors: Communities',
                     fontsize=16, pad=20)
            plt.axis('off')
            
            # Add legend for communities
            legend_elements = [plt.Line2D([0], [0], marker='o', color='w',
                                        markerfacecolor=plt.cm.tab20(i % 20),
                                        label=f'Community {i+1}',
                                        markersize=10)
                             for i in range(len(communities))]
            plt.legend(handles=legend_elements,
                      loc='center left',
                      bbox_to_anchor=(1, 0.5))
            
            plt.tight_layout()
            plt.savefig(output_dir / f'{entity}_concept_map.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # Save metrics
            metrics = {
                'word': list(centrality.keys()),
                'centrality': list(centrality.values()),
                'community': [''] * len(centrality)
            }
            for i, community in enumerate(communities):
                for word in community:
                    idx = metrics['word'].index(word)
                    metrics['community'][idx] = f'Community {i+1}'
            
            pd.DataFrame(metrics).to_csv(output_dir / f'{entity}_concept_metrics.csv', index=False)
        
        logger.info(f"Enhanced concept map visualizations saved to {output_dir}")
            
    except Exception as e:
        logger.error(f"Error in concept map plotting: {e}")
        raise

def main(input_folder: str, output_folder: str) -> None:
    """Main function to orchestrate curriculum visualization."""
    logger.info(f"Starting curriculum visualization for: {input_folder}")
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Missing required dependencies. Please install them and try again.")
        return
    
    try:
        # Load spaCy model
        nlp = spacy.load("en_core_web_sm")
        
        # Collect curriculum files
        curriculum_files = collect_curriculum_files(input_folder)
        if not curriculum_files:
            logger.error("No curriculum files found")
            return
        
        # Create output directory
        os.makedirs(output_folder, exist_ok=True)
        
        # Perform analysis
        analyze_curriculum_content(curriculum_files, output_folder, nlp)
        
        logger.info(f"Visualization complete. Results saved in: {output_folder}")
        
    except Exception as e:
        logger.error(f"Fatal error in visualization: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze and visualize curriculum content.")
    parser.add_argument("--input", default="Inputs_and_Outputs",
                       help="Path to the input directory containing research and curriculum files")
    parser.add_argument("--output", default="Curriculum_Visualizations",
                       help="Path to save visualization outputs")
    args = parser.parse_args()
    
    # Get absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, '..', args.input)
    output_dir = os.path.join(script_dir, '..', args.output)
    
    main(input_dir, output_dir)
