"""
Anthropic Claude provider for AI-assisted Terraform generation.
"""

from typing import Dict
from .base import AIProvider


class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider."""

    def get_default_model(self) -> str:
        """Get default Claude model."""
        return "claude-sonnet-4-20250514"

    def generate_terraform(self, prompt: str, context: Dict[str, str]) -> str:
        """
        Generate Terraform code using Anthropic Claude.

        Args:
            prompt: User's prompt
            context: Context dictionary

        Returns:
            Generated Terraform code

        Raises:
            ImportError: If anthropic is not installed
            Exception: If generation fails
        """
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError(
                "anthropic package is required for Anthropic provider.\n"
                "Install with: pip install anthropic"
            )

        # Initialize Anthropic client
        client = Anthropic(api_key=self.api_key)

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
            response = client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_message,
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.2,
            )

            # Extract generated code
            generated_code = response.content[0].text

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
                self.token_usage["input"] += response.usage.input_tokens
                self.token_usage["output"] += response.usage.output_tokens
                self.token_usage["total"] = self.token_usage["input"] + self.token_usage["output"]

            # Validate generated code
            if not self.validate_terraform_code(generated_code):
                raise ValueError(
                    "Generated code failed validation. "
                    "Please check the output and try again with more specific instructions."
                )

            return generated_code

        except Exception as e:
            raise Exception(f"Anthropic generation failed: {str(e)}")
