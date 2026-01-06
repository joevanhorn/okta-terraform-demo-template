"""
OpenAI provider for AI-assisted Terraform generation.
"""

from typing import Dict
from .base import AIProvider


class OpenAIProvider(AIProvider):
    """OpenAI API provider (GPT-4, GPT-3.5, etc.)."""

    def get_default_model(self) -> str:
        """Get default OpenAI model."""
        return "gpt-4o"

    def generate_terraform(self, prompt: str, context: Dict[str, str]) -> str:
        """
        Generate Terraform code using OpenAI.

        Args:
            prompt: User's prompt
            context: Context dictionary

        Returns:
            Generated Terraform code

        Raises:
            ImportError: If openai is not installed
            Exception: If generation fails
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is required for OpenAI provider.\n"
                "Install with: pip install openai"
            )

        # Initialize OpenAI client
        client = OpenAI(api_key=self.api_key)

        # Build full prompt with context
        full_prompt = self._build_full_prompt(prompt, context)

        # System message with instructions
        system_message = """You are an expert Terraform developer specializing in Okta infrastructure.

Generate clean, production-ready Terraform code following these rules:
1. Use exact patterns from the provided examples
2. Always escape template strings with $$ (e.g., "$${source.login}")
3. Set status = "ACTIVE" for all resources
4. Include descriptive comments
5. Follow HCL formatting conventions
6. Use proper resource naming (snake_case)
7. Include depends_on where appropriate
8. Generate only valid Terraform HCL code

Output only the Terraform code, no explanations unless specifically requested."""

        try:
            # Generate content
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.2,  # Lower temperature for more deterministic code generation
            )

            # Extract generated code
            generated_code = response.choices[0].message.content

            # Remove markdown code fences if present
            if "```hcl" in generated_code:
                generated_code = generated_code.split("```hcl")[1].split("```")[0].strip()
            elif "```terraform" in generated_code:
                generated_code = generated_code.split("```terraform")[1].split("```")[0].strip()
            elif "```" in generated_code:
                parts = generated_code.split("```")
                if len(parts) >= 3:
                    generated_code = parts[1].strip()

            # Track token usage
            if hasattr(response, 'usage'):
                self.token_usage["input"] += response.usage.prompt_tokens
                self.token_usage["output"] += response.usage.completion_tokens
                self.token_usage["total"] = response.usage.total_tokens

            # Validate generated code
            if not self.validate_terraform_code(generated_code):
                raise ValueError(
                    "Generated code failed validation. "
                    "Please check the output and try again with more specific instructions."
                )

            return generated_code

        except Exception as e:
            raise Exception(f"OpenAI generation failed: {str(e)}")
