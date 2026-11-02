"""
Script writer using LLM API to generate video prompts
"""
import os
from typing import List, Optional
from .utils import setup_logger, Config
from .queue_manager import Job

logger = setup_logger(__name__)


class ScriptWriter:
    """Generates video scene prompts using LLM."""
    
    def __init__(self, config: Config):
        """
        Initialize script writer.
        
        Args:
            config: Configuration instance
        """
        self.config = config
        self.provider = config.get('script_writer.llm_provider', 'openai')
        self.model = config.get('script_writer.model', 'gpt-4o')
        self.max_scenes = config.get('script_writer.max_scenes', 10)
        self.scene_duration = config.get('script_writer.scene_duration', 5)
        
        self._init_client()
    
    def _init_client(self):
        """Initialize all available LLM clients with fallback support."""
        self.clients = {}
        self.provider_order = []
        
        # DeepSeek (cheapest, OpenAI-compatible)
        if os.getenv('DEEPSEEK_API_KEY'):
            try:
                import openai
                self.clients['deepseek'] = openai.OpenAI(
                    api_key=os.getenv('DEEPSEEK_API_KEY'),
                    base_url="https://api.deepseek.com"
                )
                self.provider_order.append('deepseek')
                logger.info("DeepSeek client initialized")
            except ImportError:
                logger.warning("DeepSeek configured but openai package not installed")
        
        # Gemini (Google, free tier available)
        if os.getenv('GEMINI_API_KEY'):
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
                self.clients['gemini'] = genai
                self.provider_order.append('gemini')
                logger.info("Gemini client initialized")
            except ImportError:
                logger.warning("Gemini configured but google-generativeai package not installed")
        
        # OpenAI (reliable, moderate cost)
        if os.getenv('OPENAI_API_KEY'):
            try:
                import openai
                self.clients['openai'] = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                self.provider_order.append('openai')
                logger.info("OpenAI client initialized")
            except ImportError:
                logger.warning("OpenAI configured but openai package not installed")
        
        # Anthropic (premium)
        if os.getenv('ANTHROPIC_API_KEY'):
            try:
                import anthropic
                self.clients['anthropic'] = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
                self.provider_order.append('anthropic')
                logger.info("Anthropic client initialized")
            except ImportError:
                logger.warning("Anthropic configured but anthropic package not installed")
        
        if not self.clients:
            raise ValueError(
                "No LLM providers configured. Set at least one API key:\n"
                "DEEPSEEK_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY"
            )
        
        logger.info(f"LLM providers available: {', '.join(self.provider_order)}")
        
        # Set primary client for backward compatibility
        self.client = list(self.clients.values())[0]
    
    def generate_prompts(
        self,
        topic: str,
        num_scenes: Optional[int] = None,
        aspect_ratio: str = "16:9",
        style: Optional[str] = None
    ) -> List[Job]:
        """
        Generate video scene prompts for a topic.
        
        Args:
            topic: Topic or title for the video
            num_scenes: Number of scenes to generate (default from config)
            aspect_ratio: Aspect ratio for videos
            style: Optional style guidance (e.g., "cinematic", "documentary")
            
        Returns:
            List of Job objects with prompts
        """
        if num_scenes is None:
            num_scenes = self.max_scenes
        
        logger.info(f"Generating {num_scenes} scene prompts for: {topic}")
        
        # Build system prompt
        system_prompt = self._build_system_prompt(style)
        
        # Build user prompt
        user_prompt = self._build_user_prompt(topic, num_scenes, aspect_ratio)
        
        # Call LLM
        response = self._call_llm(system_prompt, user_prompt)
        
        # Parse response into jobs
        jobs = self._parse_response_to_jobs(response, aspect_ratio)
        
        logger.info(f"Generated {len(jobs)} scene prompts")
        return jobs
    
    def _build_system_prompt(self, style: Optional[str]) -> str:
        """Build the system prompt for the LLM."""
        prompt = """You are a video prompt generator for an AI video generation tool (Google Veo).
Your task is to create detailed, visual scene descriptions that will produce high-quality videos.

Guidelines:
- Each prompt should be 1-3 sentences describing a specific visual scene
- Focus on visual details: lighting, camera angles, motion, atmosphere
- Be specific but concise
- Avoid abstract concepts; focus on concrete visuals
- Each scene should work as a standalone video clip
"""
        
        if style:
            prompt += f"\nStyle guidance: {style}"
        
        return prompt
    
    def _build_user_prompt(
        self,
        topic: str,
        num_scenes: int,
        aspect_ratio: str
    ) -> str:
        """Build the user prompt."""
        prompt = f"""Generate {num_scenes} video scene prompts for a video about: {topic}

Each scene should be approximately {self.scene_duration} seconds.
Aspect ratio: {aspect_ratio}

Format your response as a numbered list:
1. [Scene ID] - [Prompt]
2. [Scene ID] - [Prompt]
...

Example:
1. scene_01 - A majestic mountain range at sunrise, golden light illuminating snow-capped peaks, slow pan from left to right
2. scene_02 - Close-up of morning dew on a leaf, shallow depth of field, soft morning light

Now generate {num_scenes} scenes:"""
        
        return prompt
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        Call LLM API with automatic fallback to alternative providers.
        
        Args:
            system_prompt: System instructions
            user_prompt: User request
            
        Returns:
            LLM response text
        """
        errors = []
        
        for provider in self.provider_order:
            if provider not in self.clients:
                continue
            
            try:
                logger.info(f"Trying LLM provider: {provider}")
                
                if provider == 'deepseek':
                    response = self.clients['deepseek'].chat.completions.create(
                        model='deepseek-chat',
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=2000
                    )
                    logger.info(f"✓ {provider} succeeded")
                    return response.choices[0].message.content
                
                elif provider == 'gemini':
                    genai = self.clients['gemini']
                    model = genai.GenerativeModel('gemini-pro')
                    prompt = f"{system_prompt}\n\n{user_prompt}"
                    response = model.generate_content(prompt)
                    logger.info(f"✓ {provider} succeeded")
                    return response.text
                
                elif provider == 'openai':
                    response = self.clients['openai'].chat.completions.create(
                        model=self.model if self.model != 'gpt-4o' else 'gpt-4o',
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=2000
                    )
                    logger.info(f"✓ {provider} succeeded")
                    return response.choices[0].message.content
                
                elif provider == 'anthropic':
                    message = self.clients['anthropic'].messages.create(
                        model=self.model if 'claude' in self.model else 'claude-3-5-sonnet-20241022',
                        max_tokens=2000,
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7
                    )
                    logger.info(f"✓ {provider} succeeded")
                    return message.content[0].text
            
            except Exception as e:
                error_msg = f"{provider}: {str(e)[:200]}"
                logger.warning(f"✗ {error_msg}")
                errors.append(error_msg)
                continue
        
        # All providers failed
        raise Exception(
            f"All LLM providers failed:\n" + "\n".join(f"  - {err}" for err in errors)
        )
    
    def _parse_response_to_jobs(
        self,
        response: str,
        aspect_ratio: str
    ) -> List[Job]:
        """
        Parse LLM response into Job objects.
        
        Args:
            response: LLM response text
            aspect_ratio: Aspect ratio for jobs
            
        Returns:
            List of Jobs
        """
        jobs = []
        
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Try to parse numbered format: "1. scene_01 - prompt text"
            if line[0].isdigit():
                # Remove number prefix
                line = line.split('.', 1)[-1].strip()
                
                # Try to split scene_id and prompt
                if ' - ' in line:
                    scene_id, prompt = line.split(' - ', 1)
                    scene_id = scene_id.strip()
                    prompt = prompt.strip()
                else:
                    # No scene_id, generate one
                    scene_num = len(jobs) + 1
                    scene_id = f"scene_{scene_num:02d}"
                    prompt = line
                
                job = Job(
                    scene_id=scene_id,
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    duration=self.scene_duration
                )
                jobs.append(job)
        
        return jobs
    
    def refine_prompt(self, original_prompt: str, feedback: str) -> str:
        """
        Refine a prompt based on feedback.
        
        Args:
            original_prompt: Original scene prompt
            feedback: User feedback or guidance
            
        Returns:
            Refined prompt
        """
        system_prompt = "You are a video prompt refiner. Improve prompts based on feedback."
        
        user_prompt = f"""Original prompt: {original_prompt}

Feedback: {feedback}

Provide an improved version of the prompt incorporating this feedback:"""
        
        return self._call_llm(system_prompt, user_prompt).strip()
