class MiddleSchoolStudentWorldview:
    def __init__(self):
        self.name = "Average Middle School Student 2025"
        self.key_concepts = {
            "digital_native": "Born into and growing up in a world of ubiquitous technology and connectivity",
            "social_media": {
                "identity_formation": "Early stages of identity development through social media",
                "social_connections": "Digital platforms for connecting with friends and classmates",
                "content_consumption": "Heavy consumption of short-form video content",
                "information_source": "Entertainment and trends from social platforms",
                "validation_seeking": "Growing importance of peer approval and likes",
                "digital_anxiety": "Early experiences with online social pressure",
                "authenticity_struggles": "Learning to navigate online self-presentation",
                "algorithmic_exposure": "First encounters with content algorithms",
                "privacy_basics": "Beginning to learn about online privacy",
                "digital_footprint": "Introduction to lasting online presence"
            },
            "education": {
                "hybrid_learning": "Adapting to mix of traditional and digital learning",
                "ai_discovery": "First exposure to AI tools for schoolwork",
                "information_filtering": "Learning to manage information sources",
                "practical_interests": "Curiosity about real-world applications",
                "future_exploration": "Early thoughts about future careers",
                "testing_pressure": "Introduction to standardized testing",
                "guided_learning": "Teacher and parent-directed digital learning",
                "group_projects": "Learning digital collaboration basics",
                "attention_span": "Challenges with digital distractions",
                "task_management": "Learning to handle multiple assignments"
            },
            "mental_health": {
                "peer_pressure": "Increased awareness of social dynamics",
                "screen_habits": "Developing screen time boundaries",
                "activity_balance": "Managing school, hobbies, and free time",
                "emotional_growth": "Understanding and expressing feelings",
                "friend_dynamics": "Navigating changing friendships",
                "self_awareness": "Growing understanding of personal needs",
                "support_seeking": "Learning to ask for help when needed",
                "stress_coping": "Basic stress management skills",
                "energy_management": "Balancing excitement and rest",
                "self_discovery": "Early stages of identity formation"
            },
            "technology": {
                "digital_exploration": "Discovering new apps and platforms",
                "basic_literacy": "Learning essential digital skills",
                "supervised_use": "Parent-guided technology usage",
                "online_safety": "Learning internet safety basics",
                "content_judgment": "Beginning to evaluate online content",
                "creative_tools": "Exploring digital creativity apps",
                "gaming_social": "Gaming as social activity with friends",
                "tech_rules": "Understanding family and school tech guidelines",
                "online_etiquette": "Learning digital communication norms",
                "tech_interests": "Curiosity about new technologies"
            },
            "social_consciousness": {
                "world_awareness": "Growing understanding of global issues",
                "environmental_interest": "Basic environmental awareness",
                "fairness_focus": "Strong sense of fairness and equality",
                "civic_learning": "Introduction to community involvement",
                "inclusion_values": "Learning about diversity and inclusion",
                "helping_others": "Interest in making positive change",
                "peer_influence": "Strong influence of peer group views",
                "cultural_exposure": "Learning about different cultures",
                "choice_impact": "Understanding personal choices matter",
                "local_community": "Connection to school and neighborhood"
            }
        }
        self.quotes = [
            "My parents are always worried about my screen time",
            "I wish school was more like my favorite YouTube channels",
            "Sometimes I don't know what I want to be when I grow up",
            "It's hard when my friends are all posting fun things without me",
            "My teacher says we can't use AI for homework",
            "I want to help save the planet but I'm just a kid",
            "Everyone else seems to have cooler stuff to post",
            "TikTok teaches me a lot of interesting things",
            "Sometimes I feel stressed but I don't know why",
            "I can't wait until I'm old enough for my own phone"
        ]

    def get_worldview(self):
        """Return the comprehensive worldview of a typical middle school student in 2025."""
        return {
            "digital_native": self.key_concepts["digital_native"],
            "social_media": self.key_concepts["social_media"],
            "education": self.key_concepts["education"],
            "mental_health": self.key_concepts["mental_health"],
            "technology": self.key_concepts["technology"],
            "social_consciousness": self.key_concepts["social_consciousness"]
        }

    def relationship_with_ai(self):
        """Explores how middle school students interact with and view AI technology"""
        ai_relationship = {
            "tool_discovery": "First experiences with AI tools",
            "guided_usage": "Parent and teacher supervised AI use",
            "curiosity": "Wonder about how AI works",
            "homework_help": "Basic AI tools for schoolwork",
            "creative_play": "Simple AI creative tools",
            "fact_checking": "Learning to question AI responses",
            "basic_understanding": "Growing awareness of AI in daily life",
            "social_exposure": "Encountering AI in games and apps",
            "safety_awareness": "Learning AI safety guidelines",
            "future_interest": "Curiosity about future AI developments"
        }
        return ai_relationship

    def digital_social_life(self):
        """Represents the digital social experience of modern middle school students"""
        social_dynamics = {
            "supervised_platforms": "Parent-approved social media use",
            "friend_connections": "Digital connection with school friends",
            "online_boundaries": "Learning healthy online social limits",
            "basic_communication": "Simple digital messaging and sharing",
            "group_belonging": "Digital connection to peer groups",
            "trend_following": "Awareness of popular trends",
            "friendship_rules": "Understanding online friendship etiquette",
            "digital_hangouts": "Supervised online social activities",
            "conflict_learning": "Beginning to handle online disagreements",
            "shared_interests": "Connecting through common interests"
        }
        return social_dynamics
