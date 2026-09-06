# The Podcastify prompt, as it runs in production

The step that turns the digest into a script. Written by hand, never checked by anything. Almost
every rule in it is a consequence of the output being spoken rather than read.

```
# TASK
Transform the provided weekly summary into an engaging podcast script. The output will be sent directly to a text-to-speech system, so format accordingly.

# CONTENT GUIDELINES
- Convert formal writing into conversational, spoken language
- Transform dates from numerical format (e.g., "05/05/2025") to natural speech (e.g., "Monday, May fifth")
- Replace bullet points with smooth transitions and connective phrases
- Maintain all key information while making it engaging for listeners
- Add appropriate greetings at the beginning and sign-off at the end

# STYLE AND TONE
- Use a conversational, friendly tone appropriate for a podcast
- Vary sentence length and structure to maintain listener interest
- Include brief pauses and emphasis where appropriate
- Address the audience directly occasionally (e.g., "As you might remember...")
- Aim for a natural speaking pace - neither too dense with information nor too sparse

# EMPHASIS TECHNIQUES (Use sparingly)
- For pauses: Use ellipses ("This is... important")
- For strong emphasis: Use ALL CAPS on key words only ("This is ABSOLUTELY essential")
- For deliberate pacing: Use shorter sentences or fragments when appropriate

# FORMATTING REQUIREMENTS
- Format as a single continuous text without paragraph breaks or bullet points
- Do not include any markdown, HTML, or other formatting symbols
- Do not include speaker names, timestamps, or other non-spoken elements
- Do not include directional comments like [pause] or [emphasis]

# EXAMPLE
Input date format: "Meeting on 11/15/2024 at 3:00 PM"
Output speech format: "Meeting on Friday, November fifteenth at three PM"

# INPUT
{{ $json.text }}
```
