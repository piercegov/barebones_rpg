AI Integration
==============

Integrate Large Language Models (LLMs) for dynamic content generation.

Coming Soon
-----------

This guide will demonstrate:

- LLM-generated dialog
- Dynamic quest generation
- AI-driven NPCs
- Procedural story generation
- Context-aware responses

Example Preview
---------------

.. code-block:: python

   from barebones_rpg.dialog import DialogNode

   class LLMDialogNode(DialogNode):
       """Dialog node that generates responses with an LLM."""
       
       def __init__(self, llm_client, prompt_template, **kwargs):
           super().__init__(**kwargs)
           self.llm_client = llm_client
           self.prompt_template = prompt_template
       
       def enter(self, context):
           """Generate dialog text when entering this node."""
           # Build prompt with context
           prompt = self.prompt_template.format(
               player_name=context.get("player").name,
               player_level=context.get("player").level,
               location=context.get("location").name
           )
           
           # Generate response
           self.text = self.llm_client.generate(prompt)
           
           return super().enter(context)

Check back soon for the full guide with working examples!

