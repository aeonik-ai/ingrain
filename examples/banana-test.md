# The Banana Test

The Banana Test is a small demo for learned experience.

1. Tell the agent a weird project rule:

   ```text
   Remember: For this project, yellow CTA buttons are called bananas. Never ship bananas in enterprise demos.
   ```

2. Compile:

   ```bash
   ingrain compile
   ```

3. Start a fresh session and ask for a landing page review.

Expected behavior: the agent carries the correction forward without replaying the old transcript.
