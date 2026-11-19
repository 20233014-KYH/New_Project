window.INVENTORY = {
 "_note": "디자인 비교용 공통 데이터. 토큰=첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비). 별 수·업데이트=GitHub 2026-10-26. 설명=GitHub 저장소 설명(영어 원문). 판정=김용현 1차 검수(PR #4).",
 "categories": [
  {
   "id": 1,
   "name": "기획·작업 방식",
   "desc": "Claude가 일하는 순서와 계획을 정해 줘요",
   "when": "Claude가 매번 제멋대로 일해서 순서와 규칙을 잡고 싶을 때"
  },
  {
   "id": 2,
   "name": "토큰·컨텍스트",
   "desc": "토큰을 아끼고 맥락을 이어 줘요",
   "when": "토큰이 너무 빨리 줄거나, 대화가 길어져 앞 내용을 잊을 때"
  },
  {
   "id": 3,
   "name": "코드 이해·검색",
   "desc": "코드와 기술 문서를 찾고 이해하게 도와줘요",
   "when": "큰 프로젝트에서 코드나 라이브러리 문서를 잘 찾게 하고 싶을 때"
  },
  {
   "id": 4,
   "name": "디자인·프론트엔드",
   "desc": "화면을 만들고 다듬어 줘요",
   "when": "화면을 만들거나 디자인 품질을 높이고 싶을 때"
  },
  {
   "id": 5,
   "name": "백엔드·인프라",
   "desc": "서버·DB·클라우드 작업을 도와줘요",
   "when": "DB나 서버, 클라우드 작업을 Claude에게 시키고 싶을 때"
  },
  {
   "id": 6,
   "name": "QA·테스트",
   "desc": "테스트·리뷰·보안을 점검해 줘요",
   "when": "테스트와 코드 리뷰, 보안 점검을 빠뜨리지 않고 싶을 때"
  }
 ],
 "tools": [
  {
   "id": "superpowers",
   "name": "superpowers",
   "repo": "obra/superpowers",
   "category": 1,
   "desc_en": "An agentic skills framework & software development methodology that works.",
   "version": "v7.0.0",
   "license": "MIT",
   "stars": 304883,
   "pushed_at": "2026-10-23",
   "tokens": 1562,
   "scope": {
    "skills": 15,
    "agents": 0,
    "commands": 15,
    "mcp": 0,
    "hooks_total": 1,
    "hook_events": {
     "SessionStart": 1
    }
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "ecc",
   "name": "ECC",
   "repo": "affaan-m/ECC",
   "category": 1,
   "desc_en": "The agent harness performance optimization system. Skills, instincts, memory, security, and research-first development for Claude Code, Codex, Opencode, Cursor and beyond.",
   "version": "v2.2.3",
   "license": "MIT",
   "stars": 288551,
   "pushed_at": "2026-10-20",
   "tokens": 9169,
   "scope": {
    "skills": 313,
    "agents": 71,
    "commands": 397,
    "mcp": 32,
    "hooks_total": 27,
    "hook_events": {
     "PreToolUse": 10,
     "UserPromptSubmit": 1,
     "PreCompact": 1,
     "SessionStart": 2,
     "PostToolUse": 2,
     "PostToolUseFailure": 2,
     "Stop": 8,
     "SessionEnd": 1
    }
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "gstack",
   "name": "gstack",
   "repo": "garrytan/gstack",
   "category": 1,
   "desc_en": "Use Garry Tan's exact Claude Code setup: 23 opinionated tools that serve as CEO, Designer, Eng Manager, Release Manager, Doc Engineer, and QA",
   "version": null,
   "license": "MIT",
   "stars": 137644,
   "pushed_at": "2026-10-25",
   "tokens": 1135,
   "scope": {
    "skills": 57,
    "agents": 0,
    "commands": 56,
    "mcp": 0,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "gsd-core",
   "name": "gsd-core",
   "repo": "open-gsd/gsd-core",
   "category": 1,
   "desc_en": "Git. Ship. Done - Core",
   "version": "v1.17.0",
   "license": "MIT",
   "stars": 10847,
   "pushed_at": "2026-10-25",
   "tokens": 4933,
   "scope": {
    "skills": 72,
    "agents": 35,
    "commands": 144,
    "mcp": 0,
    "hooks_total": 14,
    "hook_events": {
     "SessionStart": 2,
     "PreToolUse": 6,
     "PostToolUse": 2,
     "SubagentStop": 1,
     "Stop": 1,
     "PreCompact": 1,
     "FileChanged": 1
    }
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "planning-with-files",
   "name": "planning-with-files",
   "repo": "OthmanAdi/planning-with-files",
   "category": 1,
   "desc_en": "Persistent file-based planning for AI coding agents and long-running tasks. Crash-proof markdown plans, session recovery after /clear and compaction, per-turn re-injection against context rot, deterministic completion gate. Manus-style. Install from npm, the Claude Code plugin marketplace, or npx skills. Codex, Cursor, OpenCode, 60+ agents.",
   "version": "v3.24.3",
   "license": "MIT",
   "stars": 27635,
   "pushed_at": "2026-10-24",
   "tokens": 564,
   "scope": {
    "skills": 6,
    "agents": 0,
    "commands": 14,
    "mcp": 0,
    "hooks_total": 6,
    "hook_events": {
     "SessionStart": 1,
     "UserPromptSubmit": 1,
     "PreToolUse": 1,
     "PostToolUse": 1,
     "PreCompact": 1,
     "Stop": 1
    }
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "pm-skills",
   "name": "pm-skills",
   "repo": "phuryn/pm-skills",
   "category": 1,
   "desc_en": "PM Skills Marketplace: 100+ agentic skills, commands, and plugins — from discovery to strategy, execution, launch, and growth.",
   "version": "v2.2.0",
   "license": "MIT",
   "stars": 27363,
   "pushed_at": "2026-10-16",
   "tokens": 1280,
   "scope": {
    "skills": 69,
    "agents": 0,
    "commands": 103,
    "mcp": 0,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "caveman",
   "name": "caveman",
   "repo": "JuliusBrussee/caveman",
   "category": 2,
   "desc_en": "🪨 why use many token when few token do trick. Viral skill + proxy for coding agents that cuts 65% of tokens by talking like a caveman.",
   "version": "v4.0.1",
   "license": "Apache-2.0",
   "stars": 114956,
   "pushed_at": "2026-10-25",
   "tokens": 2643,
   "scope": {
    "skills": 22,
    "agents": 3,
    "commands": 23,
    "mcp": 0,
    "hooks_total": 4,
    "hook_events": {
     "SessionStart": 1,
     "SubagentStart": 1,
     "UserPromptSubmit": 1,
     "SessionEnd": 1
    }
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "rtk",
   "name": "rtk",
   "repo": "rtk-ai/rtk",
   "category": 2,
   "desc_en": "CLI proxy that reduces LLM token consumption by 60-90% on common dev commands. Single Rust binary, zero dependencies",
   "version": "v1.0.1",
   "license": "Apache-2.0",
   "stars": 84512,
   "pushed_at": "2026-10-25",
   "tokens": 17,
   "scope": {
    "skills": 0,
    "agents": 0,
    "commands": 0,
    "mcp": 0,
    "hooks_total": 1,
    "hook_events": {
     "PreToolUse": 1
    }
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "headroom",
   "name": "headroom",
   "repo": "headroomlabs-ai/headroom",
   "category": 2,
   "desc_en": "Compress tool outputs, logs, files, and RAG chunks before they reach the LLM. 20% fewer tokens for coding agents, 60-95% fewer tokens for JSON, same answers. Library, proxy, MCP server.",
   "version": "v0.41.0",
   "license": "Apache-2.0",
   "stars": 77791,
   "pushed_at": "2026-10-24",
   "tokens": 24,
   "scope": {
    "skills": 0,
    "agents": 0,
    "commands": 0,
    "mcp": 0,
    "hooks_total": 2,
    "hook_events": {
     "SessionStart": 1,
     "PreToolUse": 1
    }
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "claude-mem",
   "name": "claude-mem",
   "repo": "thedotmack/claude-mem",
   "category": 2,
   "desc_en": "Persistent Context Across Sessions for Every Agent –  Captures everything your agent does during sessions, compresses it with AI, and injects relevant context back into future sessions. Works with Claude Code, OpenClaw, Codex, Gemini, Hermes, Copilot, OpenCode + More",
   "version": "v14.0.1",
   "license": "Apache-2.0",
   "stars": 103016,
   "pushed_at": "2026-10-25",
   "tokens": 1075,
   "scope": {
    "skills": 30,
    "agents": 0,
    "commands": 30,
    "mcp": 0,
    "hooks_total": 17,
    "hook_events": {
     "Setup": 1,
     "SessionStart": 4,
     "UserPromptSubmit": 2,
     "PostToolUse": 2,
     "PostToolUseFailure": 1,
     "PreToolUse": 2,
     "Stop": 2,
     "SessionEnd": 2,
     "SubagentStop": 1
    }
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "claude-hud",
   "name": "claude-hud",
   "repo": "jarrodwatts/claude-hud",
   "category": 2,
   "desc_en": "A Claude Code plugin that shows what's happening - context usage, active tools, running agents, and todo progress",
   "version": "v0.11.3",
   "license": "MIT",
   "stars": 28861,
   "pushed_at": "2026-10-24",
   "tokens": 78,
   "scope": {
    "skills": 0,
    "agents": 0,
    "commands": 2,
    "mcp": 0,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "ccusage",
   "name": "ccusage",
   "repo": "ccusage/ccusage",
   "category": 2,
   "desc_en": "npx ccusage",
   "version": "v20.0.35",
   "license": "NOASSERTION",
   "stars": 19175,
   "pushed_at": "2026-10-25",
   "tokens": null,
   "scope": null,
   "token_note": "명령줄 도구. 세션에 읽히는 것 없음(README 기준)"
  },
  {
   "id": "graphify",
   "name": "graphify",
   "repo": "Graphify-Labs/graphify",
   "category": 3,
   "desc_en": "Turn any codebase, with its docs, SQL schemas, configs, and PDFs, into a queryable knowledge graph. A /graphify skill for Claude Code, Cursor, Codex, and Gemini CLI: local deterministic AST parsing, every edge explained, no vector store.",
   "version": "v0.9.92",
   "license": "Apache-2.0",
   "stars": 134869,
   "pushed_at": "2026-10-23",
   "tokens": 572,
   "scope": {
    "skills": 1,
    "agents": 0,
    "commands": 1,
    "mcp": 0,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "codegraph",
   "name": "codegraph",
   "repo": "colbymchenry/codegraph",
   "category": 3,
   "desc_en": "Pre-indexed code knowledge graph, auto syncs on code changes, for Claude Code, Codex, Gemini, Cursor, OpenCode, AntiGravity, Kiro, CoPilot, and Hermes Agent — fewer tokens, fewer tool calls, 100% local",
   "version": "v1.6.2",
   "license": "MIT",
   "stars": 75284,
   "pushed_at": "2026-10-24",
   "tokens": 839,
   "scope": {
    "skills": 0,
    "agents": 0,
    "commands": 0,
    "mcp": 1,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "claude-context",
   "name": "claude-context",
   "repo": "zilliztech/claude-context",
   "category": 3,
   "desc_en": "Code search MCP for Claude Code. Make entire codebase the context for any coding agent.",
   "version": null,
   "license": "MIT",
   "stars": 12646,
   "pushed_at": "2026-07-14",
   "tokens": 71,
   "scope": {
    "skills": 0,
    "agents": 0,
    "commands": 0,
    "mcp": 4,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "context7",
   "name": "context7",
   "repo": "upstash/context7",
   "category": 3,
   "desc_en": "Context7 Platform -- Up-to-date docs for AI agents",
   "version": "ctx7@0.8.0",
   "license": "MIT",
   "stars": 63648,
   "pushed_at": "2026-10-23",
   "tokens": 14,
   "scope": {
    "skills": 0,
    "agents": 0,
    "commands": 0,
    "mcp": 0,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "serena",
   "name": "serena",
   "repo": "oraios/serena",
   "category": 3,
   "desc_en": "A powerful MCP toolkit for coding, providing semantic retrieval and editing capabilities  - the IDE for your agent",
   "version": "v2.0.0",
   "license": "NOASSERTION",
   "stars": 30700,
   "pushed_at": "2026-10-20",
   "tokens": 149,
   "scope": {
    "skills": 0,
    "agents": 0,
    "commands": 0,
    "mcp": 3,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "understand-anything",
   "name": "Understand-Anything",
   "repo": "Egonex-AI/Understand-Anything",
   "category": 3,
   "desc_en": "Graphs that teach > graphs that impress. Turn any code into an interactive knowledge graph you can explore, search, and ask questions about. Works with Claude Code, Codex, Cursor, Copilot, Gemini CLI, and more.",
   "version": "v2.9.0",
   "license": "MIT",
   "stars": 88191,
   "pushed_at": "2026-10-22",
   "tokens": 893,
   "scope": {
    "skills": 9,
    "agents": 10,
    "commands": 9,
    "mcp": 0,
    "hooks_total": 2,
    "hook_events": {
     "PostToolUse": 1,
     "SessionStart": 1
    }
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "ui-ux-pro-max-skill",
   "name": "ui-ux-pro-max-skill",
   "repo": "nextlevelbuilder/ui-ux-pro-max-skill",
   "category": 4,
   "desc_en": "An AI skill that provides design intelligence for building professional UI/UX across multiple platforms.",
   "version": "v2.15.0",
   "license": "MIT",
   "stars": 140233,
   "pushed_at": "2026-10-23",
   "tokens": 751,
   "scope": {
    "skills": 7,
    "agents": 0,
    "commands": 7,
    "mcp": 0,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "taste-skill",
   "name": "taste-skill",
   "repo": "Leonxlnx/taste-skill",
   "category": 4,
   "desc_en": "Agent skills that give coding agents taste: art direction, reference images and a browser check instead of generic AI pages",
   "version": "v2.0.0",
   "license": "MIT",
   "stars": 102303,
   "pushed_at": "2026-10-25",
   "tokens": 957,
   "scope": {
    "skills": 14,
    "agents": 0,
    "commands": 14,
    "mcp": 0,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "impeccable",
   "name": "impeccable",
   "repo": "pbakaus/impeccable",
   "category": 4,
   "desc_en": "The design language that makes your AI harness better at design.",
   "version": "cli-v4.6.0",
   "license": "Apache-2.0",
   "stars": 87231,
   "pushed_at": "2026-10-25",
   "tokens": 463,
   "scope": {
    "skills": 1,
    "agents": 4,
    "commands": 1,
    "mcp": 0,
    "hooks_total": 2,
    "hook_events": {
     "PostToolUse": 1,
     "Stop": 1
    }
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "figma-context-mcp",
   "name": "Figma-Context-MCP",
   "repo": "GLips/Figma-Context-MCP",
   "category": 4,
   "desc_en": "MCP server to provide Figma layout information to AI coding agents like Cursor",
   "version": "v0.13.2",
   "license": "MIT",
   "stars": 16069,
   "pushed_at": "2026-10-24",
   "tokens": 58,
   "scope": {
    "skills": 0,
    "agents": 0,
    "commands": 0,
    "mcp": 2,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "cursor-talk-to-figma-mcp",
   "name": "cursor-talk-to-figma-mcp",
   "repo": "grab/cursor-talk-to-figma-mcp",
   "category": 4,
   "desc_en": "TalkToFigma: MCP integration between AI Agent (Cursor, Claude Code, Codex) and Figma, allowing Agentic AI to communicate with Figma for reading designs and modifying them programmatically.",
   "version": null,
   "license": "MIT",
   "stars": 7069,
   "pushed_at": "2026-07-26",
   "tokens": 651,
   "scope": {
    "skills": 0,
    "agents": 0,
    "commands": 6,
    "mcp": 40,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "shadcn-ui-mcp-server",
   "name": "shadcn-ui-mcp-server",
   "repo": "Jpisnice/shadcn-ui-mcp-server",
   "category": 4,
   "desc_en": "A mcp server to allow LLMS gain context about shadcn ui component structure,usage and installation,compaitable with react,svelte 5,vue & React Native",
   "version": "v3.0.0",
   "license": "MIT",
   "stars": 3070,
   "pushed_at": "2026-10-03",
   "tokens": 186,
   "scope": {
    "skills": 0,
    "agents": 0,
    "commands": 5,
    "mcp": 10,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "dbhub",
   "name": "dbhub",
   "repo": "bytebase/dbhub",
   "category": 5,
   "desc_en": "Token conscious database MCP server for Postgres, MySQL, SQL Server, Oracle, MariaDB, SQLite.",
   "version": "v1.5.0",
   "license": "MIT",
   "stars": 3717,
   "pushed_at": "2026-10-21",
   "tokens": 87,
   "scope": {
    "skills": 2,
    "agents": 0,
    "commands": 2,
    "mcp": 0,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "mcp-toolbox",
   "name": "mcp-toolbox",
   "repo": "googleapis/mcp-toolbox",
   "category": 5,
   "desc_en": "MCP Toolbox for Databases is an open source MCP server for databases.",
   "version": "v1.14.0",
   "license": "Apache-2.0",
   "stars": 16721,
   "pushed_at": "2026-10-23",
   "tokens": null,
   "scope": null,
   "token_note": "Windows 실행 파일 294MB + 실제 DB 필요 → 실측 안 함"
  },
  {
   "id": "supabase-mcp",
   "name": "mcp",
   "repo": "supabase/mcp",
   "category": 5,
   "desc_en": "Connect Supabase to your AI assistants",
   "version": "mcp-server-supabase-v0.14.0",
   "license": "Apache-2.0",
   "stars": 2969,
   "pushed_at": "2026-10-25",
   "tokens": 571,
   "scope": {
    "skills": 0,
    "agents": 0,
    "commands": 0,
    "mcp": 19,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "kubernetes-mcp-server",
   "name": "kubernetes-mcp-server",
   "repo": "containers/kubernetes-mcp-server",
   "category": 5,
   "desc_en": "Model Context Protocol (MCP) server for Kubernetes and OpenShift",
   "version": "v0.0.67",
   "license": "Apache-2.0",
   "stars": 2180,
   "pushed_at": "2026-10-23",
   "tokens": 23,
   "scope": {
    "skills": 0,
    "agents": 0,
    "commands": 0,
    "mcp": 0,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "mcp-server-kubernetes",
   "name": "mcp-server-kubernetes",
   "repo": "Flux159/mcp-server-kubernetes",
   "category": 5,
   "desc_en": "MCP Server for kubernetes management commands",
   "version": "v4.1.9",
   "license": "MIT",
   "stars": 1607,
   "pushed_at": "2026-10-21",
   "tokens": 278,
   "scope": {
    "skills": 0,
    "agents": 0,
    "commands": 1,
    "mcp": 23,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "terraform-mcp-server",
   "name": "terraform-mcp-server",
   "repo": "hashicorp/terraform-mcp-server",
   "category": 5,
   "desc_en": "The Terraform MCP Server provides seamless integration with Terraform ecosystem, enabling advanced automation and interaction capabilities for Infrastructure as Code (IaC) development.",
   "version": "v1.3.0",
   "license": "MPL-2.0",
   "stars": 1553,
   "pushed_at": "2026-10-23",
   "tokens": 672,
   "scope": {
    "skills": 0,
    "agents": 0,
    "commands": 0,
    "mcp": 9,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "playwright-mcp",
   "name": "playwright-mcp",
   "repo": "microsoft/playwright-mcp",
   "category": 6,
   "desc_en": "Playwright MCP server",
   "version": "v0.0.83",
   "license": "Apache-2.0",
   "stars": 38612,
   "pushed_at": "2026-10-22",
   "tokens": 273,
   "scope": {
    "skills": 0,
    "agents": 0,
    "commands": 0,
    "mcp": 25,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "chrome-devtools-mcp",
   "name": "chrome-devtools-mcp",
   "repo": "ChromeDevTools/chrome-devtools-mcp",
   "category": 6,
   "desc_en": "Chrome DevTools for coding agents",
   "version": "chrome-devtools-mcp-v1.11.0",
   "license": "Apache-2.0",
   "stars": 54113,
   "pushed_at": "2026-10-25",
   "tokens": 939,
   "scope": {
    "skills": 7,
    "agents": 0,
    "commands": 7,
    "mcp": 32,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "open-code-review",
   "name": "open-code-review",
   "repo": "alibaba/open-code-review",
   "category": 6,
   "desc_en": "Secure, fast, efficient, battle-tested at Alibaba's scale. Hybrid architecture code review tool: deterministic pipelines + LLM Agent, precise line-level comments, built-in multi-language ruleset (NPE, thread-safety, XSS, SQL injection), OpenAI & Anthropic compatible.",
   "version": "v1.13.1",
   "license": "Apache-2.0",
   "stars": 48251,
   "pushed_at": "2026-10-22",
   "tokens": 84,
   "scope": {
    "skills": 0,
    "agents": 0,
    "commands": 2,
    "mcp": 0,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "tdd-guard",
   "name": "tdd-guard",
   "repo": "nizos/tdd-guard",
   "category": 6,
   "desc_en": "Automated TDD enforcement for Claude Code",
   "version": "v1.7.0",
   "license": "MIT",
   "stars": 2367,
   "pushed_at": "2026-10-12",
   "tokens": 14,
   "scope": {
    "skills": 1,
    "agents": 0,
    "commands": 1,
    "mcp": 0,
    "hooks_total": 3,
    "hook_events": {
     "PreToolUse": 1,
     "UserPromptSubmit": 1,
     "SessionStart": 1
    }
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "trailofbits-skills",
   "name": "skills",
   "repo": "trailofbits/skills",
   "category": 6,
   "desc_en": "Trail of Bits skills for security research, vulnerability detection, and audit workflows",
   "version": null,
   "license": "CC-BY-SA-4.0",
   "stars": 7795,
   "pushed_at": "2026-10-24",
   "tokens": 3466,
   "scope": {
    "skills": 84,
    "agents": 30,
    "commands": 91,
    "mcp": 0,
    "hooks_total": 8,
    "hook_events": {
     "SessionStart": 3,
     "PreToolUse": 2,
     "SessionEnd": 1,
     "Stop": 1,
     "SubagentStop": 1
    }
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  },
  {
   "id": "claude-code-security-review",
   "name": "claude-code-security-review",
   "repo": "anthropics/claude-code-security-review",
   "category": 6,
   "desc_en": "An AI-powered security review GitHub Action using Claude to analyze code changes for security vulnerabilities.",
   "version": null,
   "license": "MIT",
   "stars": 6539,
   "pushed_at": "2026-02-11",
   "tokens": 45,
   "scope": {
    "skills": 0,
    "agents": 0,
    "commands": 0,
    "mcp": 0,
    "hooks_total": 0,
    "hook_events": {}
   },
   "token_note": "첫 응답 기준 실측(2026-10-18, Claude Code 2.1.191, 도구 없음 대비)"
  }
 ],
 "pairs": [
  {
   "a": "superpowers",
   "b": "ecc",
   "relation": "overlap",
   "relation_ko": "겹침",
   "review_state": "tested"
  },
  {
   "a": "superpowers",
   "b": "gstack",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "superpowers",
   "b": "gsd-core",
   "relation": "overlap",
   "relation_ko": "겹침",
   "review_state": "human_review"
  },
  {
   "a": "superpowers",
   "b": "planning-with-files",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "superpowers",
   "b": "pm-skills",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "ecc",
   "b": "gstack",
   "relation": "overlap",
   "relation_ko": "겹침",
   "review_state": "human_review"
  },
  {
   "a": "ecc",
   "b": "gsd-core",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "ecc",
   "b": "planning-with-files",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "ecc",
   "b": "pm-skills",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "gstack",
   "b": "gsd-core",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "gstack",
   "b": "planning-with-files",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "gstack",
   "b": "pm-skills",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "gsd-core",
   "b": "planning-with-files",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "gsd-core",
   "b": "pm-skills",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "planning-with-files",
   "b": "pm-skills",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "caveman",
   "b": "rtk",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "tested"
  },
  {
   "a": "caveman",
   "b": "headroom",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "caveman",
   "b": "claude-mem",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "caveman",
   "b": "claude-hud",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "tested"
  },
  {
   "a": "caveman",
   "b": "ccusage",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "rtk",
   "b": "headroom",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "rtk",
   "b": "claude-mem",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "rtk",
   "b": "claude-hud",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "rtk",
   "b": "ccusage",
   "relation": "complement",
   "relation_ko": "보완",
   "review_state": "human_review"
  },
  {
   "a": "headroom",
   "b": "claude-mem",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "headroom",
   "b": "claude-hud",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "headroom",
   "b": "ccusage",
   "relation": "complement",
   "relation_ko": "보완",
   "review_state": "human_review"
  },
  {
   "a": "claude-mem",
   "b": "claude-hud",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "claude-mem",
   "b": "ccusage",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "claude-hud",
   "b": "ccusage",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "graphify",
   "b": "codegraph",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "graphify",
   "b": "claude-context",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "graphify",
   "b": "context7",
   "relation": "complement",
   "relation_ko": "보완",
   "review_state": "human_review"
  },
  {
   "a": "graphify",
   "b": "serena",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "graphify",
   "b": "understand-anything",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "codegraph",
   "b": "claude-context",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "codegraph",
   "b": "context7",
   "relation": "complement",
   "relation_ko": "보완",
   "review_state": "human_review"
  },
  {
   "a": "codegraph",
   "b": "serena",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "codegraph",
   "b": "understand-anything",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "claude-context",
   "b": "context7",
   "relation": "complement",
   "relation_ko": "보완",
   "review_state": "human_review"
  },
  {
   "a": "claude-context",
   "b": "serena",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "claude-context",
   "b": "understand-anything",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "context7",
   "b": "serena",
   "relation": "complement",
   "relation_ko": "보완",
   "review_state": "human_review"
  },
  {
   "a": "context7",
   "b": "understand-anything",
   "relation": "complement",
   "relation_ko": "보완",
   "review_state": "human_review"
  },
  {
   "a": "serena",
   "b": "understand-anything",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "ui-ux-pro-max-skill",
   "b": "taste-skill",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "ui-ux-pro-max-skill",
   "b": "impeccable",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "ui-ux-pro-max-skill",
   "b": "figma-context-mcp",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "ui-ux-pro-max-skill",
   "b": "cursor-talk-to-figma-mcp",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "ui-ux-pro-max-skill",
   "b": "shadcn-ui-mcp-server",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "taste-skill",
   "b": "impeccable",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "taste-skill",
   "b": "figma-context-mcp",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "taste-skill",
   "b": "cursor-talk-to-figma-mcp",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "taste-skill",
   "b": "shadcn-ui-mcp-server",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "impeccable",
   "b": "figma-context-mcp",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "impeccable",
   "b": "cursor-talk-to-figma-mcp",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "impeccable",
   "b": "shadcn-ui-mcp-server",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "figma-context-mcp",
   "b": "cursor-talk-to-figma-mcp",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "figma-context-mcp",
   "b": "shadcn-ui-mcp-server",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "cursor-talk-to-figma-mcp",
   "b": "shadcn-ui-mcp-server",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "dbhub",
   "b": "mcp-toolbox",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "dbhub",
   "b": "supabase-mcp",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "dbhub",
   "b": "kubernetes-mcp-server",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "dbhub",
   "b": "mcp-server-kubernetes",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "dbhub",
   "b": "terraform-mcp-server",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "mcp-toolbox",
   "b": "supabase-mcp",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "mcp-toolbox",
   "b": "kubernetes-mcp-server",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "mcp-toolbox",
   "b": "mcp-server-kubernetes",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "mcp-toolbox",
   "b": "terraform-mcp-server",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "supabase-mcp",
   "b": "kubernetes-mcp-server",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "supabase-mcp",
   "b": "mcp-server-kubernetes",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "supabase-mcp",
   "b": "terraform-mcp-server",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "kubernetes-mcp-server",
   "b": "mcp-server-kubernetes",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "kubernetes-mcp-server",
   "b": "terraform-mcp-server",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "mcp-server-kubernetes",
   "b": "terraform-mcp-server",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "playwright-mcp",
   "b": "chrome-devtools-mcp",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "playwright-mcp",
   "b": "open-code-review",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "playwright-mcp",
   "b": "tdd-guard",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "playwright-mcp",
   "b": "trailofbits-skills",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "playwright-mcp",
   "b": "claude-code-security-review",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "chrome-devtools-mcp",
   "b": "open-code-review",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "chrome-devtools-mcp",
   "b": "tdd-guard",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "chrome-devtools-mcp",
   "b": "trailofbits-skills",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "chrome-devtools-mcp",
   "b": "claude-code-security-review",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "open-code-review",
   "b": "tdd-guard",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "open-code-review",
   "b": "trailofbits-skills",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "open-code-review",
   "b": "claude-code-security-review",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  },
  {
   "a": "tdd-guard",
   "b": "trailofbits-skills",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "tdd-guard",
   "b": "claude-code-security-review",
   "relation": "none",
   "relation_ko": "관계 없음",
   "review_state": "human_review"
  },
  {
   "a": "trailofbits-skills",
   "b": "claude-code-security-review",
   "relation": "situational",
   "relation_ko": "상황따라",
   "review_state": "human_review"
  }
 ],
 "highlight": {
  "a": "superpowers",
  "b": "ecc",
  "text": "같은 과제 27번: 결과는 모두 성공, 둘 다 켜면 토큰 약 1.9배·시간 약 1.5배. ECC의 겹치는 스킬은 한 번도 안 쓰임.",
  "date": "2026-10-17"
 }
};
// 직접 시험에서 나온 사실(judgment/experiments/2026-10-18-statusline-caveman-rtk). 기준 = superpowers + karpathy-skills + impeccable 조합, 과제 3개 x 3번, sonnet.
window.INVENTORY.tested = [
 {"tool":"caveman","effect":"출력 토큰 -38%, 시간 -27%, 입력 -14% (기준 조합 대비, 조건마다 9번 모두 성공)","caution":"버그를 고칠 때 superpowers 디버깅 절차를 3번 중 3번 건너뛰었어요","caution_work":"bugfix","date":"2026-10-18"},
 {"tool":"rtk","effect":"바꾼 명령의 출력은 -69%였지만, 작은 과제 전체로는 -4%로 차이가 거의 없었어요","caution":"Windows에서 Claude가 PowerShell로 명령을 실행하면 작동하지 않아요","caution_shell":"powershell","date":"2026-10-18"}
];
