---
name: jsnovel-skill
description: 技术叙事小说创作技能包。执行Part大纲、人物、目录、章节的专业创作，基于技术准确性铁律和叙事多样性系统生成高质量技术小说内容。
---

# 技术叙事小说创作 Skill

[技能说明]
    专业的技术叙事小说创作技能包，覆盖故事构思、人物塑造、章节规划、正文写作全流程。根据不同创作阶段，读取对应的创作资源并生成符合技术叙事规范的小说内容。

[文件结构]
    .claude/skills/jsnovel-skill/
    ├── SKILL.md                        # 本文件（技能包核心配置）
    ├── TECHNICAL_ACCURACY.md           # 技术准确性铁律
    ├── TYPOGRAPHY_RULES.md             # 排版规则（9条铁律）
    ├── NARRATIVE_DIVERSITY.md          # 叙事多样性系统
    ├── templates/                      # 文档结构模板（通用）
    │   ├── part-outline-template.md    # Part大纲文档格式模板
    │   ├── character-template.md       # 人物小传格式模板
    │   ├── chapter-index-template.md   # 章节目录格式模板
    │   └── chapter-template.md         # 章节正文格式模板
    └── parts/                          # Part级别定制（10个Part）
        ├── part-01-genesis/            # Part 1: 世界诞生 (HTML)
        │   ├── part-config.md          # Part配置（叙事方式、世界观、长线故事）
        │   ├── narrative-method.md     # Part专属叙事方法
        │   ├── technical-scope.md      # 技术范围（HTML知识点列表）
        │   └── examples/
        │       └── chapter-example.md  # Part风格示例章节
        ├── part-02-appearance/         # Part 2: 表象与幻术 (CSS)
        │   └── ...
        ├── part-03-causality/          # Part 3: 因果律初现 (JS基础)
        │   └── ...
        ├── part-04-object-memory/      # Part 4: 对象与记忆
        │   └── ...
        ├── part-05-function-abyss/     # Part 5: 函数深渊
        │   └── ...
        ├── part-06-prototype/          # Part 6: 血统与继承
        │   └── ...
        ├── part-07-async/              # Part 7: 时间与异步
        │   └── ...
        ├── part-08-module/             # Part 8: 模块与杂项
        │   └── ...
        ├── part-09-dom/                # Part 9: 浏览器世界
        │   └── ...
        └── part-10-network/            # Part 10: 数据网络与组件
            └── ...

[核心能力]
    - **创作阶段理解**：识别当前处于Part大纲、人物、目录还是章节创作阶段
    - **资源整合**：读取模板、方法论、风格、示例等多维度资源
    - **专业创作**：基于资源和上下文创作符合技术叙事规范的小说内容
    - **风格把控**：确保创作内容符合技术准确性和叙事多样性要求
    - **模板遵循**：严格按照模板格式生成文档结构
    - **上下文理解**：理解已有文档内容，确保创作连贯性
    - **Part识别**：根据章节编号自动识别所属Part
    - **技术验证**：确保所有代码可运行，输出与描述一致

[执行流程]
    第一步：理解创作需求
        识别当前创作阶段：
        - 如果在讨论Part大纲或part-outline.md不存在 → Part大纲创作阶段
        - 如果在讨论人物或刚执行/character → 人物创作阶段
        - 如果在讨论章节规划或刚执行/catalog → 目录创作阶段
        - 如果在创作章节正文或刚执行/write → 章节创作阶段

        识别所属Part（基于章节编号）：
        - 第1-15章 → Part 1 (世界诞生-HTML)
        - 第16-30章 → Part 2 (表象与幻术-CSS)
        - 第31-46章 → Part 3 (因果律初现-JS基础)
        - 第47-66章 → Part 4 (对象与记忆-Object)
        - 第67-78章 → Part 5 (函数深渊-Function)
        - 第79-92章 → Part 6 (血统与继承-Prototype)
        - 第93-102章 → Part 7 (时间与异步-Async)
        - 第103-112章 → Part 8 (模块与杂项-Module)
        - 第113-140章 → Part 9 (浏览器世界-DOM)
        - 第141-168章 → Part 10 (数据网络与组件-Network)

    第二步：读取创作资源
        **Part大纲创作阶段**：
            1. 读取 templates/part-outline-template.md（文档格式模板）
            2. 读取 parts/part-XX/part-config.md（Part配置：世界观、叙事分布、节奏轮换）
            3. 读取 parts/part-XX/narrative-method.md（叙事方法论）
            4. 读取 parts/part-XX/technical-scope.md（技术范围：章节主题清单）
            5. 读取 TECHNICAL_ACCURACY.md（技术准确性铁律）
            6. 读取 TYPOGRAPHY_RULES.md（排版规则）
            7. 读取 NARRATIVE_DIVERSITY.md（叙事多样性系统）
            8. 从对话历史获取用户提供的Part核心信息（如有）

        **人物创作阶段**：
            1. 读取 XX-Part目录/part-outline.md（了解故事背景和设定）
            2. 读取 templates/character-template.md（文档格式模板）
            3. 读取 parts/part-XX/part-config.md（Part世界观设定）
            4. 读取 parts/part-XX/narrative-method.md（角色设计指导部分）
            5. 读取 NARRATIVE_DIVERSITY.md（人物设计方法）

        **目录创作阶段**：
            1. 读取 XX-Part目录/part-outline.md 和 character.md（了解故事和人物）
            2. 读取 templates/chapter-index-template.md（文档格式模板）
            3. 读取 parts/part-XX/part-config.md（Part叙事风格分布）
            4. 读取 parts/part-XX/narrative-method.md（章节规划方法）
            5. 读取 parts/part-XX/technical-scope.md（详细技术点列表）
            6. 读取 NARRATIVE_DIVERSITY.md（叙事方式分配指导）

        **章节创作阶段**：
            1. 读取 XX-Part目录/part-outline.md、character.md、chapter-index.md（全部上下文）
            2. 读取 templates/chapter-template.md（文档格式模板）
            3. 读取 parts/part-XX/part-config.md（Part世界观和风格）
            4. 读取 parts/part-XX/narrative-method.md（叙事方法和技术揭示手法）
            5. 读取 parts/part-XX/technical-scope.md（该章节的技术点）
            6. 读取 parts/part-XX/examples/chapter-example.md（Part风格示例）
            7. 读取 TECHNICAL_ACCURACY.md（技术准确性铁律，最重要）
            8. 读取 TYPOGRAPHY_RULES.md（排版规则9条，最重要）
            9. 读取 NARRATIVE_DIVERSITY.md（叙事多样性要求）
            10. 读取 XX-Part目录/chapter-*.md（该章之前的所有章节，用于上下文积累）
            11. 从chapter-index.md获取当前章节的规划内容

    第三步：执行专业创作
        **Part大纲创作**：
            基于用户提供的信息和读取的资源：
            - 严格按照 templates/part-outline-template.md 的格式结构
            - 遵循 parts/part-XX/narrative-method.md 的叙事方法论
            - 应用 parts/part-XX/part-config.md 的世界观和叙事风格
            - 参考 parts/part-XX/technical-scope.md 规划章节主题
            - 生成包含以下内容的完整Part大纲：
                • Part信息（编号、技术领域、章节范围、核心主题）
                • 长线故事主题
                • 核心技术脉络
                • 章节规划概要
                • 人物角色构想
                • 世界规则

        **人物创作**：
            基于part-outline.md的故事设定和读取的资源：
            - 严格按照 templates/character-template.md 的格式结构
            - 遵循 parts/part-XX/narrative-method.md 中的角色设计指导
            - 应用 parts/part-XX/part-config.md 的世界观设定
            - 参考 NARRATIVE_DIVERSITY.md 的人物设计方法
            - 生成包含以下内容的人物小传：
                • 主要角色（3-5个，详细描述）
                • 角色关系网
                • 角色在长线故事中的作用
            - 确保人物与故事冲突匹配，人物关系合理

        **目录创作**：
            基于part-outline.md和character.md的设定和读取的资源：
            - 严格按照 templates/chapter-index-template.md 的格式结构
            - 遵循 parts/part-XX/part-config.md 的叙事方式分配
            - 应用 parts/part-XX/technical-scope.md 的技术点列表
            - 参考 NARRATIVE_DIVERSITY.md 确保叙事多样性
            - 为每章分配：技术主题、叙事方式、文章形式、场景设定、字数范围
            - 确保起承转合布局合理，节奏控制得当

        **章节创作**：
            基于全部上下文文档和读取的资源：
            - 严格按照 templates/chapter-template.md 的格式结构
            - 严格遵循 TECHNICAL_ACCURACY.md 的技术准确性铁律（最重要）
            - 严格遵循 TYPOGRAPHY_RULES.md 的排版规则9条（最重要）
            - 应用 parts/part-XX/narrative-method.md 的叙事方法和技术揭示手法
            - 参考 parts/part-XX/examples/chapter-example.md 的示例风格
            - 基于 chapter-index.md 中该章节的规划进行创作
            - 参考前序章节的知识总结部分，实现上下文积累
            - 生成2000-3500字的章节正文（75%故事+25%技术解释）
            - 确保人物行为一致，剧情推进连贯
            - 验证所有代码可运行，输出与描述一致

    第四步：返回创作成果
        **Part大纲创作阶段**：
            返回符合templates/part-outline-template.md格式的完整Part大纲内容

        **人物创作阶段**：
            返回符合templates/character-template.md格式的完整人物小传

        **目录创作阶段**：
            返回符合templates/chapter-index-template.md格式的完整章节目录

        **章节创作阶段**：
            返回符合templates/chapter-template.md格式的完整章节正文

[创作原则]
    - **模板遵循原则**：
        • 创作的所有文档必须严格遵循templates/中定义的格式
        • 不能遗漏模板中的必要标题和段落
        • 不能改变模板定义的层级结构
        • 可以根据实际需要调整内容的详略

    - **技术准确性原则**（最高优先级）：
        • 所有代码必须可运行，所有输出必须与实际一致
        • 所有技术规则必须符合ECMAScript/HTML/CSS/浏览器规范
        • 绝不为故事性牺牲技术准确性
        • 严格遵循TECHNICAL_ACCURACY.md中的三级校验流程

    - **排版规则原则**（强制约束）：
        • 严格遵守TYPOGRAPHY_RULES.md中的9条排版规则
        • 中英文/数字间距、标点符号后空格、标点符号选择
        • 引号使用、数字与单位空格、专有名词大小写
        • 破折号使用、代码块前后空行、省略号使用

    - **叙事多样性原则**：
        • 所有创作必须保持叙事多样性，避免重复感
        • 严格遵循NARRATIVE_DIVERSITY.md中定义的叙事系统
        • Part内保持叙事方式、文章形式、时间场景的多样性
        • 参考叙事多样性检查清单确保质量

    - **风格一致性原则**：
        • 所有创作必须保持Part内风格统一
        • 严格遵循parts/part-XX/part-config.md中定义的世界观和叙事风格
        • 确保Part大纲、人物、章节的风格协调

    - **上下文连贯性原则**：
        • character创作必须基于part-outline
        • chapter-index创作必须基于part-outline + character
        • chapter创作必须基于part-outline + character + chapter-index + 前序章节
        • 确保前后内容不矛盾，逻辑连贯
        • 实现Part内上下文积累（后章可引用前章知识点）

    - **质量标准原则**：
        • Part大纲：核心主题清晰，技术脉络完整，章节规划合理
        • 人物：性格鲜明，与故事匹配，关系网清晰
        • 目录：叙事多样性分配合理，技术点覆盖完整，布局合理
        • 章节：2000-3500字，技术准确，排版规范，叙事精彩

[注意事项]
    - 确保每个阶段的必需资源都已读取完整
    - 不仅读取文档内容，还要深入理解其含义
    - TECHNICAL_ACCURACY.md中的技术准确性要求是最高优先级，必须严格遵守
    - TYPOGRAPHY_RULES.md中的排版规则是强约束，必须100%遵守
    - templates/中的格式是必须遵循的，任何偏离都可能导致问题
    - 每个Part的章节数不同（10-28章），需根据part-config.md确定
    - 创作内容必须完整、连贯、符合技术叙事特点
    - Part内上下文积累机制：读取前序章节的知识总结，在新章节中可引用
    - 始终使用中文创作
    - 所有代码示例必须在浏览器中验证通过
