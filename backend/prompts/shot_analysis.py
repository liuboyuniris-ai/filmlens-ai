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
        narrative_pos = "影片开场"
    elif progress > 0.9:
        narrative_pos = "影片结尾"
    else:
        narrative_pos = f"影片中段（第 {int(progress * 100)}% 处）"

    preceding_part = f"\n前序镜头节奏（供剪辑分析参考）：\n{preceding_shots_desc}" if preceding_shots_desc else ""

    return f"""══════════════════════════════════════════
影片身份
══════════════════════════════════════════
影片：《{film_title}》（{production_year}）
导演：{director}
国家/地区：{country}

══════════════════════════════════════════
当前镜头位置
══════════════════════════════════════════
镜头编号：第 {shot_id} 个，共 {total_shots} 个
时间码：{timecode} / {total_duration}
叙事位置：{narrative_pos}{preceding_part}

══════════════════════════════════════════
影片社会历史背景（供语境分析参考）
══════════════════════════════════════════
{film_summary}

══════════════════════════════════════════
分析任务开始
══════════════════════════════════════════
关于 editing 字段的填写规则（基于你看到的多张滑动窗口图判断）：
- cut_type_in：你从第一张图切到第二张图（当前帧）时用的是什么剪辑方式？
- cut_type_out：你从第二张图切到第三张图时用的是什么剪辑方式？
- prev_shot_relation：第一张图和第二张图在叙事上是什么关系？
- next_shot_relation：第二张图和第三张图在叙事上是什么关系？
- 如果没有第一张图（开场镜头），cut_type_in 填 film_opening
- 如果没有第三张图（结尾镜头），cut_type_out 填 film_closing
"""

SHOT_ANALYSIS_PROMPT = """你刚刚读取了上方的影片背景信息。请结合那些具体背景分析这张关键帧，理论分析必须解释为什么该理论适用于这个镜头的这个具体视觉选择，不能只描述理论本身。

核心分析原则：语境桥接 (Contextual Bridging)
你必须将看到的“视觉事实”（景别、构图、光影）与影片《[FILM_TITLE]》以及导演 [DIRECTOR] 的整体作者性风格联系起来。如果该镜头体现了 [DIRECTOR] 典型的美学偏好，请在分析中明确指出。

你是一位接受过大卫·波德维尔（David Bordwell）、克里斯汀·汤普森（Kristin Thompson）、
安德烈·巴赞（André Bazin）和劳拉·穆尔维（Laura Mulvey）学术传统训练的专业电影分析师。

请分析这张电影关键帧，严格按照以下 JSON 格式返回，不要添加任何解释或 Markdown 标记。

{
  "shot_scale": "从以下选一：大特写|特写|中近景|中景|中远景|远景|大远景|未知",
  "camera_movement": "从以下选一：固定|摇镜|俯仰|推拉|变焦|手持|升降|跟拍|未知",
  "camera_angle": "从以下选一：平视|仰角|俯角|鸟瞰|虫眼|未知",
  "depth_of_field": "从以下选一：浅景深|中等景深|深景深|未知",
  "lighting_scheme": "从以下选一：高调|低调|自然光|混合|未知",
  "color_temperature": "从以下选一：暖调|中性|冷调|混合|未知",
  "dominant_colors": ["最多3个，用颜色名称描述，如：深红、赭石、近黑"],
  "primary_technique": "这个镜头最核心的一个电影技法，15字以内",
  "theoretical_connections": [
    {
      "theory_name_cn": "理论中文名，如：穆尔维凝视理论",
      "theory_name_en": "Visual Pleasure and Narrative Cinema",
      "theorist_en": "Laura Mulvey",
      "theorist_cn": "劳拉·穆尔维",
      "year": 1975,
      "description": "结合本镜头的具体视觉元素，解释为什么该理论在《[FILM_TITLE]》的这一刻被激活。必须分析导演 [DIRECTOR] 的具体视觉选择如何回应了该理论。",
      "search_keywords_en": ["mulvey", "gaze", "visual pleasure", " narrative cinema"],
      "search_keywords_cn": ["穆尔维", "凝视理论", "女性主义电影"]
    }
  ],
  "narrative_function": "这个镜头在《[FILM_TITLE]》当前节点（[NARRATIVE_POS]）的具体叙事功能，2句话。",
  "contextual_analysis": "你作为AI对该镜头的深度分析：将具体的视觉选择（构图、色彩、运动等）与影片《[FILM_TITLE]》的历史语境、导演风格或叙事意图直接挂钩。这是必填项，不含括号引用。",
  "editing": {
    "cut_type_in": "从以下选一：切出|淡入|叠化|划像|未知",
    "cut_type_out": "从以下选一：切入|淡出|叠化|划像|未知",
    "rhythm_feel": "该镜头的剪辑节奏感，如：沉稳、跳跃、急促",
    "prev_shot_relation": "与前一镜头的逻辑关系，如：匹配剪辑、轴线切换、对比",
    "next_shot_relation": "与后一镜头的预期关系",
    "editing_function": "该剪辑点在叙事或情感上的功能",
    "specific_techniques": ["使用的具体剪辑技法，如：交叉剪辑、跳切"],
    "search_keywords_en": ["editing", "montage", "cut"],
    "search_keywords_cn": ["剪辑", "蒙太奇", "切向"]
  }
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
theoretical_connections 填写规则（最重要）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

这个字段允许为空数组 []。请严格按照以下标准判断：

【应该填入理论】
- 该镜头有明确的、非常规的视觉处理（特殊景别选择、异常摄影机运动、
  刻意的构图失衡、强烈的光线对比等），且某个具体理论能解释这种选择的意义
- 理论与镜头的关联可以用帧内可见的视觉元素直接论证

【必须返回空数组 []】
- 功能性过场镜头：主要目的是交代地点、时间、人物位置关系
- 平淡的对话镜头：正反打或肩拍，无特殊视觉处理
- 技法普通的镜头：没有值得分析的风格特征
- 你能想到的理论与该镜头的关联是牵强的、需要大量推论才能成立的

错误示范（禁止）：
  × 每个镜头都套上巴赞的"长镜头理论"或"写实主义"
  × 只要有人物就引用穆尔维的凝视理论
  × 因为"这是艺术片"就默认需要引用理论
  × 将通用的叙事技巧（正反打、过肩镜头）强行与特定理论绑定

- 禁止添加任何类似“（参见...）”或“根据...理论”的学术括号引用。这里只呈现你的原发性分析。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
其他要求
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 如果从视觉上无法判断某个字段，使用"未知"而非猜测
- search_keywords 用英文和中文分别填写，将用于学术数据库检索
- 只返回合法 JSON，不要 Markdown 代码块，不要任何解释文字
"""

def get_shot_analysis_prompt(locale: str = "zh-CN") -> str:
    return SHOT_ANALYSIS_PROMPT
