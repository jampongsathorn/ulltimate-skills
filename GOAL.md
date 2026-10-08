# GOAL: Build Web Automation Framework (tokvideo-inspired)

**Status:** ACTIVE  
**Created:** 2026-10-08  
**Owner:** jampongsathorn  

---

## 🎯 Primary Objective

Build a **reusable web automation framework** by reverse-engineering the `tokvideo` repository pattern:
- Multi-step web scraping (Playwright)
- API-driven data aggregation (requests)
- Headless browser automation with session management
- Third-party service integration
- Error handling & retry logic

**NOT a port of tokvideo** — a **pattern library** for similar multi-stage automation tasks.

---

## 📊 Reference Architecture (tokvideo)

### Stage 1: Auth & Setup
- TikTok login via Playwright (`_tiktok.py:__login()`)
- Session persistence to JSON
- Cookie/CSRF token management

### Stage 2: Data Collection
- Shopee Affiliate API queries (`_shopee.py:get_product_offers()`)
- Product filtering by metrics (commission, rating, stock)
- CSV merge with deduplication

### Stage 3: Linked Search
- Multi-threaded keyword search (TikTok videos)
- URL extraction via XPath/CSS selectors
- Cached deduplication

### Stage 4: Download & Transform
- Third-party service integration (ssstik.io)
- Content generation (caption from template + data)
- File management (mkdir, push via adb)

### Stage 5: Push & Automate
- Appium-driven mobile app control
- XPath-based element selection
- Sequential action flow with wait strategies

---

## ✅ Success Criteria

- [ ] **Core Framework**
  - [ ] Auth module (session + cookie persistence)
  - [ ] Multi-stage pipeline orchestrator
  - [ ] Error handling & retry decorator
  - [ ] Logging + event checkpoint system

- [ ] **Reference Implementation** (TikTok→Shopee pattern)
  - [ ] Playwright integration
  - [ ] API client wrapper
  - [ ] CSV/JSON data layer
  - [ ] Third-party downloader adapter

- [ ] **Testing & Documentation**
  - [ ] Mocked unit tests (no browser/API calls)
  - [ ] Integration test pattern
  - [ ] ADR for architecture decisions
  - [ ] Runbook for local setup

- [ ] **Production-Ready Features**
  - [ ] Graceful degradation (missing session)
  - [ ] Rate-limit handling
  - [ ] CAPTCHA detection trigger
  - [ ] Stateful resume from checkpoint

---

## 🔴 Blockers & Risks

1. **Third-party API fragility** (ssstik.io, TikTok endpoint changes)
   - Mitigation: Abstraction layer + fallback strategy
   - Owner: TBD
   - ETA: Phase 2

2. **Appium/ADB dependency** (Android/mobile-specific)
   - Mitigation: Make mobile stage optional; unit test separately
   - Owner: TBD
   - ETA: Phase 1.5 (optional)

3. **XPath brittleness** (UI changes break selectors)
   - Mitigation: Selector versioning + CI test on real devices
   - Owner: TBD
   - ETA: Phase 2

---

## 📐 Phases

### Phase 1: Framework Skeleton (1 week)
- [ ] Base classes: `Authenticator`, `Pipeline`, `Stage`
- [ ] Example: Simple TikTok auth + session save
- [ ] Checkpoint logging
- [ ] Basic retry logic

### Phase 2: Reference Implementation (1.5 weeks)
- [ ] Full tokvideo pattern in new codebase
- [ ] CSV data layer
- [ ] Playwright + API orchestration
- [ ] Mocked tests

### Phase 3: Polish & Deploy (1 week)
- [ ] Documentation + runbook
- [ ] CI/CD skeleton
- [ ] Optional Appium integration guide
- [ ] Public release

---

## 📁 Deliverables

```
ulltimate-skills/
├── automation/
│   ├── __init__.py
│   ├── core/
│   │   ├── authenticator.py       # Session + cookie handling
│   │   ├── pipeline.py            # Multi-stage orchestrator
│   │   ├── checkpoint.py          # Event logging + resume
│   │   └── retry.py               # Decorator + strategy
│   ├── adapters/
│   │   ├── playwright_adapter.py  # Browser automation
│   │   ├── requests_adapter.py    # HTTP API wrapper
│   │   └── downloader_adapter.py  # Third-party services
│   └── examples/
│       └── tiktok_to_shopee.py    # Full reference flow
├── tests/
│   ├── mocks/
│   ├── test_auth.py
│   ├── test_pipeline.py
│   └── test_checkpoint.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ADR_001_session_persistence.md
│   └── RUNBOOK.md
└── requirements.txt
```

---

## 🔗 References

- **Source:** https://github.com/etomun/tokvideo
- **Pattern:** Web scraping → API aggregation → Download → Transform → Push
- **Stack:** Playwright, requests, pandas, argparse, adb (optional)
- **License Compliance:** TBD (reverse-engineer public code)

---

## 📞 Next Steps

1. **Confirm scope** with team
2. **Lock Phase 1 deliverables** (framework skeleton)
3. **Setup repo structure** + requirements.txt
4. **Assign owners** for each phase
