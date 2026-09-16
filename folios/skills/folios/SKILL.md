---
name: folios
description: 构建或迭代 Folios —— 西语优先、墨西哥–美国双市场的智能证据工作区 SaaS。用于：创建/优化 Folios 营销页面、Playbooks 目录与详情页、互动 folio demo、持久化等候名单、双语 UX、可下载资源、客户证据区。提到 Folios 产品、Folios 网站、Playbooks、folios.ai 相关工作即触发。
---

# Folios 双语 SaaS 构建工作流

把 Folios 需求变成打磨过的 **Spanish-first** SaaS 体验，面向在墨西哥与美国之间协作的团队。

## 产品契约

把 **Folios** 当作一个智能证据工作区（intelligent proof workspace）：产品收集工作素材、连接意图、产出结构化可分享的 folio。视觉体系用 **Editorial Workbench**：档案纸面底色（archive-paper）、常绿产品结构、Proof Lime 验证标记、克制的朱红批注、不对称的编辑式构图。

- 默认 **Spanish (Mexico)**；**English (US)** 作为用户显式控制的第二语言。
- **绝不发布伪造的客户评价、证言、评分或业务结果**。在没有客户认可的源材料前，展示空的证据框架。

## 设计标准：Awwwards 获奖级

每个交付的页面都要按 **Awwwards-winning** 的设计水准执行，不做"够用"的模板站：

1. **字体排印（Typography）**：一套有性格的字体配对（展示级 display 字体 + 高可读性正文字体），用字号对比和字重层级建立视觉节奏；西语重音字符（á é í ó ú ñ ¿ ¡）必须完整渲染。
2. **动态与交互（Motion）**：有意义的微交互——滚动叙事（scroll storytelling）、视差分层、hover 反馈、页面转场；动画用 opacity / transform 驱动，保持 60fps，尊重 `prefers-reduced-motion`。
3. **编辑式构图**：不对称网格、留白即设计元素、folio 标签页与档案编号等品牌构件贯穿全站；hero 之外也要有视觉惊喜。
4. **性能与工程**：图片优化、字体子集化、无渲染阻塞资源；动效不能牺牲 LCP/CLS。视觉复杂度必须建立在流畅体验之上。
5. **细节打磨**：定制光标/选择色、骨架屏、加载状态、404 页都按同一套视觉语言设计。交付前逐页截图核对桌面与移动端。

## 交付流程

### 1. 规划产品页面

识别需要哪些页面：营销叙事、等候名单、互动 demo、Playbooks 目录、Playbook 详情页、可下载资源、客户证据区。把每一项请求的改动先写进项目 `todo.md` 再动手。

| 页面 | 目的 | 默认内容规则 |
|---|---|---|
| Hero | 跨 MX–US 协作陈述价值主张 | 西语优先、证据驱动的文案 |
| Waitlist | 收集合法邮箱 | 通过公开的后端校验接口持久化 |
| Demo | 让访客模拟 folio 创建流程 | 三个阶段：collect、connect、publish |
| Playbooks | 让工作流可发现 | 组织为编辑档案式，绝不做连续通用卡片网格 |
| 详情页 | 讲清一个优先工作流 | 富文本指南、输入、输出、可下载起步资源 |
| Evidence | 用真实成果建立信任 | 需要来源、时间窗口、客户认可 |

### 2. 双语行为

- 所有面向用户的文案用本地化对象表示，`es` / `en` 各一份值，从 `es-MX` 起步。
- 语言偏好用 `localStorage` 持久化，键为 `folios-locale`；只在初始渲染之后读取，或在带浏览器守卫的 lazy state initializer 里读。
- 语言切换只做透明度 + 小幅垂直位移动画；保持焦点、避免布局突变；更新根节点 `lang` 属性。

### 3. 安全实现等候名单

- 用公开 tRPC procedure + 带唯一归一化邮箱约束的数据库表；客户端与服务端契约都校验邮箱。
- 只存邮箱、locale、来源、时间戳，除非用户明确要求更多字段。
- 成功时展示就地确认状态（短 transform/opacity 动画）；重复邮箱按友好的等价成功处理，不向提交者之外的人泄露是否已注册。
- 为邮箱归一化与非法邮箱拒绝补 Vitest 测试。

### 4. Playbooks 档案化组织

按章节分组，而非不间断的重复卡片网格。默认章节：

| 章节 | 示例 |
|---|---|
| Business | 市场规模、QBR、投资人 deck、deal tracker |
| Creative | AI 视频、视觉方向、故事生成器 |
| Sales & marketing | 市场调研、广告文案、销售漏斗 |
| Education | 翻译、写作、演示工具 |
| Personal productivity | 对比、规划器、计算器 |
| Other | 摘要、代码生成、机会管理 |

在章节索引之上放少量视觉突出的 **Archive Picks**：用 folio 标签页、档案编号、proof 圆点，以及 *collect*、*inspect*、*document*、*prove*、*publish* 这类检视语言。

### 5. 优先 Playbook 详情页

默认优先级：市场调研、投资人 pitch deck、AI 视频、PDF 翻译、YouTube 红人查找器（除非用户另给顺序）。每个详情页必须含：

1. 解释"要完成什么工作"的编辑式 hero；
2. 富文本指南：简短 brief、输入、流程、交付物、交接标准；
3. 基于 `templates/playbook-resource.md` 的可下载 markdown 起步资源；
4. 一个直接动作：在 Folios demo 里预选该 Playbook 或启动相关工作区。

可下载材料保持诚实：可以是起步 brief、清单或模板，但除非后端已接通，否则不得暗示能产出外部真实结果。

### 6. 客户证据处理

只接受可验证证据，且必须具备：数值、指标定义、度量周期、来源 URL 或来源文档、认可状态。证言需要：精确的获批引文、客户/公司署名、角色、授权状态、来源引用。

信息不全时渲染透明的"证据待补"状态，不用合成数字或文案。**不创建假评价、虚构客户名、无来源的效果宣称。**

### 7. 验证与交付

跑 `pnpm check` 和 `pnpm test`；核对桌面与移动端截图；每个检查点前过一遍 `todo.md`；交付前保存 checkpoint。

## 质量门（交付前逐项过）

| 检查 | 通过条件 |
|---|---|
| 视觉体系 | Archive-paper、常绿、Proof Lime、folio 标签页、人文批注在 hero 之后仍然可见 |
| 双语 UX | 西语默认；英语显式、可持久化、动画不造成突兀重排 |
| 等候名单 | 客户端/服务端校验、唯一存储、友好的重复状态、成功反馈 |
| Playbooks | 目录读起来是策展档案（章节 + 精选），不是库存目录 |
| 证据 | 所有公开指标与引文有来源且已获批，或明确留空 |
| 验证 | TypeScript、Vitest、桌面、移动端审查全部通过 |
