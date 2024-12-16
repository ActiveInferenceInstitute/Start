class HighSchoolStudentWorldview:
    def __init__(self):
        self.name = "Average High School Student 2025"
        self.key_concepts = {
            "digital_native": "Born into and growing up in a world of ubiquitous technology and connectivity",
            "social_media": {
                "identity_formation": "Social media plays a key role in identity development and expression",
                "social_connections": "Digital platforms are primary means of maintaining friendships",
                "content_creation": "Active participation in creating and sharing digital content",
                "information_source": "Primary source for news, trends, and cultural knowledge",
                "validation_seeking": "Likes and engagement as forms of social validation",
                "digital_anxiety": "Stress from constant connectivity and social comparison",
                "authenticity_struggles": "Balancing authentic self vs curated online presence",
                "algorithmic_awareness": "Growing understanding of how algorithms shape online experience",
                "privacy_concerns": "Navigating privacy in an increasingly public digital world",
                "digital_footprint": "Awareness of long-term implications of online presence"
            },
            "education": {
                "hybrid_learning": "Mix of traditional and digital learning environments",
                "ai_integration": "Growing use of AI tools for homework and learning",
                "information_overload": "Challenge of filtering and processing abundant information",
                "practical_skills": "Interest in real-world applicable knowledge",
                "career_uncertainty": "Anxiety about future job market and career paths",
                "standardized_testing": "Pressure from traditional academic metrics",
                "self_directed_learning": "Using online resources for independent study",
                "collaborative_tools": "Familiarity with digital collaboration platforms",
                "instant_gratification": "Expectation of immediate access to information",
                "multitasking": "Constant switching between different tasks and platforms"
            },
            "mental_health": {
                "anxiety": "High levels of academic and social pressure",
                "screen_time": "Impact of extensive digital device usage",
                "work_life_balance": "Struggle to balance school, activities, and rest",
                "future_concerns": "Worry about climate change, economy, and society",
                "social_comparison": "Stress from constant peer comparison",
                "self_care": "Growing awareness of mental health importance",
                "therapy_stigma": "Decreasing stigma around seeking mental health help",
                "mindfulness": "Interest in stress management techniques",
                "burnout": "Exhaustion from constant productivity pressure",
                "identity_exploration": "Process of discovering and defining self"
            },
            "technology": {
                "ai_coexistence": "Growing up alongside AI tools and assistants",
                "digital_literacy": "Native understanding of technology usage",
                "tech_dependence": "Heavy reliance on digital tools and devices",
                "privacy_awareness": "Understanding of digital privacy implications",
                "content_filtering": "Ability to evaluate online information sources",
                "digital_creativity": "Using technology for creative expression",
                "gaming_culture": "Video games as social and recreational activity",
                "tech_ethics": "Developing views on responsible technology use",
                "digital_citizenship": "Navigation of online social norms",
                "future_tech": "Interest in emerging technologies"
            },
            "social_consciousness": {
                "global_awareness": "Connected to worldwide events and issues",
                "climate_concern": "Worry about environmental sustainability",
                "social_justice": "Interest in equity and fairness issues",
                "political_engagement": "Growing awareness of political processes",
                "diversity_appreciation": "Value placed on inclusivity and representation",
                "activism": "Digital and real-world social participation",
                "generational_identity": "Sense of shared generational experience",
                "cultural_fluency": "Exposure to diverse perspectives online",
                "consumer_awareness": "Consciousness of consumption impacts",
                "community_involvement": "Balance of online and local community"
            }
        }
        self.quotes = [
            "I can't imagine life without my phone",
            "School feels outdated sometimes compared to how we actually learn things",
            "I'm worried about what jobs will even exist when I graduate",
            "It's exhausting trying to keep up with everything online",
            "AI tools make homework easier but I wonder if that's cheating",
            "I care about the environment but feel helpless to change things",
            "Social media is like a highlight reel of everyone's best moments",
            "I learn more from YouTube than I do in some classes",
            "Mental health is important but it's hard to find balance",
            "Technology is just part of who we are now"
        ]

    def get_worldview(self):
        """Return the comprehensive worldview of a typical high school student in 2025."""
        return {
            "digital_native": self.key_concepts["digital_native"],
            "social_media": self.key_concepts["social_media"],
            "education": self.key_concepts["education"],
            "mental_health": self.key_concepts["mental_health"],
            "technology": self.key_concepts["technology"],
            "social_consciousness": self.key_concepts["social_consciousness"]
        }

    def relationship_with_ai(self):
        """Explores how high school students interact with and view AI technology"""
        ai_relationship = {
            "tool_usage": "Regular use of AI for academic and creative tasks",
            "ethical_considerations": "Developing understanding of AI ethics",
            "future_impact": "Concern about AI's impact on future careers",
            "learning_aid": "AI as supplementary learning resource",
            "creativity_enhancement": "AI as tool for creative projects",
            "information_verification": "Growing need to verify AI-generated content",
            "digital_literacy": "Understanding AI capabilities and limitations",
            "social_interaction": "Navigation of AI in social platforms",
            "privacy_concerns": "Awareness of AI data collection",
            "career_preparation": "Interest in AI-relevant skills"
        }
        return ai_relationship

    def digital_social_life(self):
        """Represents the digital social experience of modern high school students"""
        social_dynamics = {
            "platform_usage": "Multiple social media platforms for different purposes",
            "online_identity": "Curated digital presence across platforms",
            "real_virtual_balance": "Navigation between online and offline social life",
            "communication_styles": "Mix of text, visual, and video communication",
            "community_building": "Digital community participation and creation",
            "trend_awareness": "Rapid adoption and abandonment of trends",
            "social_capital": "Digital influence and social standing",
            "friendship_maintenance": "Digital tools for maintaining relationships",
            "conflict_resolution": "Managing disagreements in digital spaces",
            "cultural_participation": "Engagement with digital cultural phenomena"
        }
        return social_dynamics
