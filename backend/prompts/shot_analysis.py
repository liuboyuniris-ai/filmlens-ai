def build_context_header(
    film_title: str,
    director: str,
    production_year: int,
    country: str,
    shot_id: int,
    total_shots: int,
    timecode: str,
    total_duration: str,
    film_summary: str,
    preceding_shots_desc: str = ""
) -> str:
    # Narrative position logic
    progress = (shot_id / total_shots) if total_shots > 0 else 0.5
    if progress < 0.1:
        narrative_pos = "Film Opening"
    elif progress > 0.9:
        narrative_pos = "Film Ending"
    else:
        narrative_pos = f"Middle Segment ({int(progress * 100)}%)"

    preceding_part = f"\nPreceding Shot Rhythm (for editing reference):\n{preceding_shots_desc}" if preceding_shots_desc else ""

    return f"""══════════════════════════════════════════
Film Identity
══════════════════════════════════════════
Film: "{film_title}" ({production_year})
Director: {director}
Country/Region: {country}

══════════════════════════════════════════
Current Shot Position
══════════════════════════════════════════
Shot ID: {shot_id} of {total_shots}
Timecode: {timecode} / {total_duration}
Narrative Position: {narrative_pos}{preceding_part}

══════════════════════════════════════════
Flim Social-Historical Context (for contextual analysis)
══════════════════════════════════════════
{film_summary}

══════════════════════════════════════════
Analysis Task Start
══════════════════════════════════════════
Rules for the 'editing' fields (judged based on the sliding window of images provided):
- cut_type_in: What editing technique was used when cutting from the 1st image to the 2nd image (current frame)?
- cut_type_out: What was used from the 2nd image to the 3rd image?
- prev_shot_relation: What is the narrative relationship between the 1st and 2nd images?
- next_shot_relation: What is it between the 2nd and 3rd images?
- If no 1st image (opening), use 'film_opening' for cut_type_in.
- If no 3rd image (closing), use 'film_closing' for cut_type_out.
"""

SHOT_ANALYSIS_PROMPT = """You have read the film's background info above. Please analyze this keyframe focusing on the specific context. Theoretical analysis must explain WHY the theory applies to this SPECIFIC visual choice in this shot; do not just describe the theory itself.

Core Principle: Contextual Bridging
You must link observed 'visual facts' (shot scale, composition, lighting) to the overall film "[FILM_TITLE]" and the auteur style of director [DIRECTOR]. If the shot reflects a typical aesthetic preference of [DIRECTOR], state it explicitly.

You are a professional film analyst trained in the academic traditions of David Bordwell, Kristin Thompson, André Bazin, and Laura Mulvey.

Analyze this film keyframe and return strictly in the following JSON format. Do not add any explanation or Markdown tags.

{
  "shot_scale": "Choose one: Extreme Close-up|Close-up|Medium Close-up|Medium Shot|Medium Long Shot|Long Shot|Extreme Long Shot|Unknown",
  "camera_movement": "Choose one: Static|Pan|Tilt|Dolly/Track|Zoom|Handheld|Crane|Follow|Unknown",
  "camera_angle": "Choose one: Eye-level|High Angle|Low Angle|Bird's Eye|Worm's Eye|Unknown",
  "depth_of_field": "Choose one: Shallow|Medium|Deep|Unknown",
  "lighting_scheme": "Choose one: High-key|Low-key|Natural Light|Mixed|Unknown",
  "color_temperature": "Choose one: Warm|Neutral|Cool|Mixed|Unknown",
  "dominant_colors": ["Max 3, described as color names, e.g., Deep Red, Ocher, Near Black"],
  "primary_technique": "The most core cinematic technique in this shot (max 15 words)",
  "theoretical_connections": [
    {
      "theory_name_cn": "Theory Name in Chinese, e.g. 穆尔维凝视理论",
      "theory_name_en": "Visual Pleasure and Narrative Cinema",
      "theorist_en": "Laura Mulvey",
      "theorist_cn": "劳拉·穆尔维",
      "year": 1975,
      "description": "Explaining why the theory is activated at this moment in '[FILM_TITLE]', linking specific visual elements. Must analyze how [DIRECTOR]'s specific visual choices respond to the theory.",
      "search_keywords_en": ["mulvey", "gaze", "visual pleasure", "narrative cinema"],
      "search_keywords_cn": ["穆尔维", "凝视理论", "女性主义电影"]
    }
  ],
  "narrative_function": "The specific narrative function of this shot at the stage '[NARRATIVE_POS]', max 2 sentences.",
  "contextual_analysis": "Your deep analysis as an AI: Linking visual choices (composition, color, motion, etc.) to the historical context, director's style, or narrative intent of '[FILM_TITLE]'. This is mandatory.",
  "editing": {
    "cut_type_in": "Choose one: Cut|Fade-in|Dissolve|Wipe|Unknown",
    "cut_type_out": "Choose one: Cut|Fade-out|Dissolve|Wipe|Unknown",
    "rhythm_feel": "Rhythm of the cut, e.g., Steady, Jump cuts, Urgent",
    "prev_shot_relation": "Logic between shots, e.g., Match cut, Axis switch, Contrast",
    "next_shot_relation": "Predicted relation with the next shot",
    "editing_function": "The narrative or emotional function of the cut point",
    "specific_techniques": ["Specific techniques used, e.g., Cross-cutting, Jump-cut"],
    "search_keywords_en": ["editing", "montage", "cut"],
    "search_keywords_cn": ["剪辑", "蒙太奇", "切向"]
  }
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rules for 'theoretical_connections' (Crucial)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This field can be an empty array []. Follow these standards:

[INCLUDE THEORY IF]
- The shot has clear, unconventional visual treatment (unusual scale, abnormal movement, deliberate composition imbalance, strong lighting contrast, etc.) and a specific theory explains it.
- The link between theory and shot can be directly argued with visible elements.

[MUST RETURN EMPTY ARRAY [] IF]
- Functional transitions: Establishing location, time, or character positions.
- Plain dialogue: Shot-reverse-shot or over-the-shoulder without special treatment.
- Ordinary techniques: No unique stylistic features.
- Links are tenuous or require too much inference.

COMMON ERRORS (PROHIBITED):
- Applying Bazin's 'Deep Focus' or 'Realism' to every shot.
- Citing Mulvey's Gaze Theory just because a character is present.
- Defaulting to theory just because it's an 'art film'.
- Forcing generic techniques (over-the-shoulder) into specific theories.

Analyze purely without academic parenthetical citations.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Other Requirements
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Use 'Unknown' for fields that cannot be visualy determined.
- Return only valid JSON without Markdown blocks or any and explanitory text.
- Analyze results in English by default.
"""

def get_shot_analysis_prompt(locale: str = "en-US") -> str:
    return SHOT_ANALYSIS_PROMPT
