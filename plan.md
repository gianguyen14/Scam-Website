# ScamGuard AI — Project Implementation Plan

## 1. Mục tiêu dự án

ScamGuard AI là một **Browser Extension phát hiện website lừa đảo/phishing theo thời gian thực**, tập trung trước tiên vào Chrome/Chromium với Manifest V3.

Mục tiêu của hệ thống:

- Tự động kiểm tra website khi người dùng truy cập.
- Phân tích URL, domain, DOM, form đăng nhập, OTP, nội dung và dấu hiệu giả mạo thương hiệu.
- Kết hợp nhiều nguồn tín hiệu thay vì phụ thuộc hoàn toàn vào một mô hình AI.
- Trả về `risk score 0–100` cùng lý do giải thích rõ ràng.
- Cảnh báo hoặc chặn mềm khi website có nguy cơ cao.
- Không thu thập mật khẩu, OTP, cookie, session token hoặc dữ liệu nhạy cảm người dùng nhập.
- Hệ thống vẫn hoạt động ở mức cơ bản khi backend hoặc một module AI gặp lỗi.

Dự án được thiết kế cho **team 2 người**, ưu tiên khả năng hoàn thành sản phẩm end-to-end trước, sau đó mới nâng dần độ mạnh của AI.

---

## 2. Nguyên tắc triển khai

### 2.1. Extension-first

Sản phẩm chính là Browser Extension, không phải web app nhập URL thủ công.

Luồng chính:

```text
User mở website
      ↓
Browser Extension
      ↓
Local URL + DOM precheck
      ↓
Known safe?
 ├─ YES → cho phép truy cập
 └─ NO / UNKNOWN
        ↓
     Backend API
        ↓
┌──────────────────────────────┐
│ URL detector                 │
│ Domain / Reputation          │
│ DOM / Form detector          │
│ Content detector             │
│ Brand impersonation detector │
│ Vision detector (optional)   │
└───────────────┬──────────────┘
                ↓
            Risk Engine
                ↓
        Risk Score 0–100
                ↓
0–29       30–69       70–100
SAFE     SUSPICIOUS   DANGEROUS
                         ↓
                   Warning Page
```

### 2.2. Vertical slice trước, AI nâng cao sau

Không chia project theo kiểu:

```text
Người A làm AI vài tuần
Người B làm extension vài tuần
Cuối cùng mới ghép
```

Thay vào đó, ngay từ tuần đầu phải có pipeline chạy hoàn chỉnh:

```text
Extension → API → detector → risk score → popup
```

Ban đầu detector có thể đơn giản hoặc hard-code, sau đó thay từng phần bằng module thật.

### 2.3. Main branch luôn phải chạy được

Sau mỗi phase:

- extension build được;
- backend start được;
- API contract không bị phá;
- demo end-to-end được;
- nếu module mới lỗi thì hệ thống vẫn dùng fallback cũ.

---

## 3. Phạm vi phiên bản v1.0

### Bắt buộc

- Chrome/Chromium Extension Manifest V3.
- Tự động nhận URL đang truy cập.
- URL phishing/scam detector.
- DOM scanner.
- Phát hiện login/password/OTP/credit-card-like field.
- Phân tích form action và iframe.
- Domain/reputation module.
- Brand-domain mismatch detector.
- Risk score 0–100.
- Explainable reasons.
- Popup hiển thị trạng thái.
- Warning page.
- Cache local/server.
- Report false-positive.
- FastAPI backend.
- Docker deployment.
- Unit test + integration test + extension E2E test.

### Không bắt buộc cho v1.0

- Firefox/Safari.
- Full crawler Internet.
- LLM lớn.
- OCR toàn bộ webpage.
- JavaScript malware sandbox đầy đủ.
- Network behavior emulation.
- Malware binary scanning.
- Hàng trăm thương hiệu ngay từ đầu.

Các mục này để dành cho v1.1/v2.

---

## 4. Cấu trúc repository dự kiến

```text
Scam-Website/
│
├── extension/
│   ├── manifest.json
│   ├── src/
│   │   ├── background/
│   │   │   └── service-worker.ts
│   │   ├── content/
│   │   │   ├── scanner.ts
│   │   │   ├── forms.ts
│   │   │   └── page-features.ts
│   │   ├── popup/
│   │   │   ├── App.tsx
│   │   │   └── components/
│   │   ├── warning/
│   │   │   └── Warning.tsx
│   │   └── shared/
│   │       ├── api.ts
│   │       ├── types.ts
│   │       └── storage.ts
│   ├── tests/
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── models/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── ml/
│   ├── datasets/
│   ├── features/
│   ├── training/
│   ├── evaluation/
│   └── export/
│
├── data/
│   └── brand_registry/
│
├── test-sites/
│   ├── normal/
│   ├── fake-bank/
│   ├── fake-google/
│   ├── fake-facebook/
│   ├── otp-scam/
│   ├── investment-scam/
│   └── crypto-scam/
│
├── deploy/
│   ├── docker-compose.yml
│   └── .env.example
│
├── docs/
│   ├── architecture.md
│   ├── api-contract.md
│   └── threat-model.md
│
├── .github/
│   └── workflows/
│
├── plan.md
└── README.md
```

---

## 5. API Contract

API contract cần được thống nhất sớm và hạn chế thay đổi breaking change.

### Request

```json
{
  "schema_version": 1,
  "url": "https://example.com/login",
  "page": {
    "title": "Account Login",
    "has_password": true,
    "has_otp": false,
    "has_credit_card": false,
    "has_login_form": true,
    "external_form_action": true,
    "iframe_count": 1,
    "link_count": 18
  }
}
```

### Response

```json
{
  "schema_version": 1,
  "risk_score": 87,
  "level": "dangerous",
  "confidence": 0.93,
  "detected_brand": "Example Bank",
  "reasons": [
    {
      "code": "BRAND_DOMAIN_MISMATCH",
      "score": 30
    },
    {
      "code": "CREDENTIAL_FORM",
      "score": 20
    }
  ],
  "modules": {
    "url": 0.88,
    "domain": 0.79,
    "content": 0.91,
    "vision": null
  }
}
```

Module chưa chạy hoặc lỗi phải trả `null`, không làm toàn bộ request thất bại.

---

## 6. Phase 0 — Skeleton end-to-end

### Thời gian

Ngày 1–2.

### Người 1

- Tạo FastAPI skeleton.
- Tạo endpoint `/health`.
- Tạo endpoint `/api/v1/scan`.
- Response tạm thời hard-code.

### Người 2

- Tạo Chrome Extension Manifest V3.
- Service worker.
- Popup cơ bản.
- Lấy current tab URL.
- Gọi backend API.

### Luồng phải chạy

```text
Chrome
 ↓
Extension
 ↓
Current URL
 ↓
POST /api/v1/scan
 ↓
FastAPI
 ↓
risk = 10
 ↓
Popup
 ↓
SAFE 10/100
```

### Gate 0

Chỉ đi tiếp khi:

- [ ] Extension build thành công.
- [ ] Load unpacked extension được.
- [ ] Extension đọc được URL tab hiện tại.
- [ ] Gọi được backend.
- [ ] Backend trả JSON đúng schema.
- [ ] Popup hiển thị risk score.
- [ ] Đổi tab không crash.
- [ ] Refresh browser vẫn hoạt động.

Nếu Gate 0 chưa qua thì chưa train model AI.

---

## 7. Phase 1 — URL Detector

### Thời gian

Ngày 3–7.

### Mục tiêu

Xây detector đầu tiên có thể chạy thật trên CPU và cho latency thấp.

### Pipeline

```text
URL
 ↓
Normalize
 ↓
Feature Extraction
 ↓
LightGBM / XGBoost
 ↓
Scam probability 0–1
```

### Feature ban đầu

- URL length.
- Hostname length.
- Path length.
- Number of dots.
- Number of subdomains.
- Number of digits.
- Digit ratio.
- Special-character ratio.
- Entropy.
- IP-address-as-host.
- Punycode.
- Suspicious TLD.
- HTTPS.
- Explicit port.
- URL shortener.
- `login` keyword.
- `verify` keyword.
- `secure` keyword.
- `account` keyword.
- `wallet` keyword.
- `bank` keyword.
- Brand token in subdomain/path.

### Dataset rule

Train/test phải split theo domain.

Sai:

```text
train: bad.com/login1
test : bad.com/login2
```

Đúng:

```text
train: bad1.com, bad2.xyz
test : bad3.top
```

Mục tiêu là tránh domain leakage.

### API

```http
POST /api/v1/scan/url
```

### Gate 1

Phải chạy được:

```text
Extension → URL → API → ML → score → popup
```

Kết quả sau phase này là `v0.1`.

---

## 8. Phase 2 — DOM Scanner

### Thời gian

Tuần 2.

### Mục tiêu

Content script phân tích cấu trúc trang mà không đọc dữ liệu nhạy cảm người dùng nhập.

### Feature cần lấy

- `has_password`
- `has_otp`
- `has_email`
- `has_phone`
- `has_credit_card`
- `has_login_form`
- `external_form_action`
- `iframe_count`
- hidden iframe.
- download link.
- suspicious button label.
- page title.
- visible text summary.
- number of forms.
- number of external links.

### Privacy rule

Không bao giờ lấy:

```javascript
input.value
```

đối với password, OTP, card number hoặc dữ liệu form nhạy cảm.

Chỉ lấy metadata:

```json
{
  "has_password": true,
  "has_otp": true
}
```

### Gate 2

Test bằng local test sites:

```text
test-sites/
├── normal/
├── fake-bank/
├── fake-login/
├── otp-test/
└── external-form/
```

Extension phải nhận đúng loại field và form.

---

## 9. Phase 3 — Risk Engine v1

### Mục tiêu

Kết hợp URL AI + DOM rules + domain rules thành một risk score duy nhất.

Ban đầu có thể dùng weighted rules.

Ví dụ:

```text
URL AI                 34
Brand mismatch         25
Password field         15
OTP field              10
External form          10
Suspicious TLD          6
                       ──
                      100
```

Sau đó clamp về 0–100.

### Level

```text
0–29   = safe
30–69  = suspicious
70–100 = dangerous
```

### Gate 3

| Test site | Expected |
|---|---|
| Normal blog | Safe |
| Normal login page | Safe/Low |
| Weird URL | Suspicious |
| Fake bank + password | Dangerous |
| Fake bank + OTP | Dangerous |

Sau phase này hệ thống phải đủ khả năng demo độc lập dù các module AI nâng cao chưa tồn tại.

---

## 10. Phase 4 — Warning System

### Mục tiêu

Khi risk vượt threshold, chuyển người dùng sang trang cảnh báo của extension.

### Warning page

Phải hiển thị:

- Risk score.
- Risk level.
- Top reasons.
- Detected brand nếu có.
- Nút quay lại.
- Nút tiếp tục truy cập.
- Nút report false positive.

Ví dụ:

```text
⚠ WEBSITE CÓ NGUY CƠ LỪA ĐẢO

Risk: 91/100

• Website yêu cầu mật khẩu
• Domain đáng ngờ
• Có dấu hiệu giả thương hiệu

[Quay lại]
[Tiếp tục truy cập]
[Report false positive]
```

Không khóa user hoàn toàn khỏi website.

---

## 11. Phase 5 — Domain / Reputation

### Thời gian

Tuần 3.

### Module

```text
backend/app/services/domain_service.py
```

### Input

```text
example.xyz
```

### Output

```json
{
  "known_malicious": false,
  "known_safe": false,
  "domain_age_days": 5,
  "tld_risk": 0.72,
  "dns_valid": true,
  "tls_valid": true
}
```

### Feature

- Domain age.
- Registration age.
- DNS validity.
- MX presence.
- Name server.
- TLS validity.
- Certificate age.
- TLD.
- ASN/IP reputation nếu có.
- Threat-intelligence result.

Nếu external service timeout thì trả partial result, không HTTP 500 toàn scan.

---

## 12. Phase 6 — Brand Impersonation Detector

### Thời gian

Tuần 3–4.

### Brand Registry

```text
data/brand_registry/
```

Ví dụ:

```json
{
  "brand": "Vietcombank",
  "official_domains": [
    "vietcombank.com.vn"
  ],
  "keywords": [
    "Vietcombank",
    "VCB"
  ]
}
```

### Logic

```text
Page detected brand = Vietcombank
          +
Current domain = vietcombank-login.xyz
          +
Official domain = vietcombank.com.vn
          ↓
Brand-domain mismatch = true
          ↓
Risk tăng mạnh
```

### Scope v1

Chỉ cần 10–30 thương hiệu phổ biến trước, sau đó mở rộng.

---

## 13. Phase 7 — Content AI

### Thời gian

Tuần 4.

### Input

Không gửi toàn HTML thô nếu không cần thiết.

Ưu tiên:

- visible text;
- title;
- form labels;
- button labels;
- heading;
- detected brand text;
- selected metadata.

### Classes / signals

- credential request;
- urgency;
- account suspension threat;
- financial request;
- fake prize;
- investment scam;
- crypto scam;
- fake support;
- impersonation.

### Output

```json
{
  "credential_request": 0.92,
  "urgency": 0.73,
  "financial_scam": 0.08
}
```

Content AI không tự quyết định SAFE/SCAM; Risk Engine là lớp quyết định cuối.

---

## 14. Phase 8 — Vision Detector

### Thời gian

Tuần 5.

Vision là second-stage detector, không chạy trên tất cả website.

### Trigger đề xuất

Chỉ capture khi:

```text
URL suspicious
OR
password field + unknown domain
OR
brand detected
OR
risk hiện tại nằm vùng 40–75
```

### Pipeline

```text
Screenshot
   ↓
Vision model
   ↓
Logo / UI / OCR / brand clues
   ↓
Detected brand
   ↓
Compare official domain
   ↓
Risk adjustment
```

Ví dụ:

```text
Risk trước Vision = 61
        ↓
Screenshot giống Microsoft Login
        ↓
Current domain != microsoft.com
        ↓
Risk sau Vision = 93
```

Vision failure không được làm scan thất bại.

---

## 15. Extension Architecture

### Background service worker

Phụ trách:

- navigation events;
- API calls;
- cache lookup;
- risk state;
- notification;
- warning navigation;
- retry/fallback.

### Content script

Phụ trách:

- DOM scanning;
- form metadata;
- page feature extraction;
- sensitive field detection;
- visible text extraction;
- không đọc user-entered secrets.

### Popup

Hiển thị:

```text
example.com

SAFE / SUSPICIOUS / DANGEROUS
Risk: 8/100

URL       3/100
Domain    4/100
Content  12/100
Vision     N/A
```

### Storage

Không phụ thuộc vào biến global trong service worker.

Dùng tùy trường hợp:

```text
chrome.storage.session
chrome.storage.local
```

State ví dụ:

```json
{
  "tab_15": {
    "url": "https://abc.xyz",
    "risk": 84,
    "timestamp": 1789400000
  }
}
```

---

## 16. Blocking Strategy

Manifest V3 không nên thiết kế dựa trên việc giữ request chờ AI vài giây.

### Known malicious

Dùng local/blocking rules phù hợp với Manifest V3 để xử lý nhanh.

```text
Known malicious domain
        ↓
Immediate block / warning
```

### Unknown domain

```text
Navigation
   ↓
Local precheck
   ↓
Backend analysis
   ↓
Warning nếu cần
```

Không thiết kế:

```text
Network request
   ↓
wait AI 3–5s
   ↓
block
```

---

## 17. Cache Strategy

### Local cache

Ví dụ:

```json
{
  "google.com": {
    "risk": 2,
    "expires_at": 1789400000
  }
}
```

### TTL gợi ý

- Known safe: dài hơn.
- Suspicious: ngắn hơn.
- Malicious: ngắn/trung bình tùy threat feed.
- Domain metadata: cache server.
- Vision result: cache theo URL/page hash nếu cần.

### Flow

```text
URL
 ↓
Local cache?
 ├─ YES → result
 └─ NO
      ↓
 Backend cache?
 ├─ YES → result
 └─ NO → detectors
```

---

## 18. Fail-safe / Degraded Mode

Hệ thống bắt buộc có graceful degradation.

| Module lỗi | Hành vi fallback |
|---|---|
| Backend down | Local URL/DOM scanner vẫn chạy |
| URL AI down | Rule engine chạy |
| Domain API down | Domain feature = unavailable |
| Content AI down | URL + DOM + domain vẫn chạy |
| Vision timeout | Bỏ Vision |
| Redis down | Bỏ cache server |
| DB down | Scan vẫn chạy, không persistence |
| Screenshot denied | Bỏ Vision |
| Service worker restart | Restore state từ storage |
| Internet mất | Local detection |

Không được để:

```text
Vision failed
   ↓
Entire scan failed
```

Phải là:

```text
Vision = unavailable
URL    = available
DOM    = available
Domain = available

→ partial risk result
```

---

## 19. Privacy và Security

Extension có quyền xem trang web nên privacy phải là requirement từ đầu.

### Không thu thập

- Password value.
- OTP value.
- Credit card number.
- CVV.
- Cookie.
- Authorization header.
- Session token.
- Form input nhạy cảm.

### Chỉ thu metadata

```json
{
  "has_password": true,
  "has_otp": true,
  "has_credit_card": false
}
```

### Backend

- Validate URL input.
- Reject unsupported schemes.
- Rate limit.
- Request size limit.
- Timeout cho external providers.
- Không log sensitive payload.
- API key/secrets chỉ trong environment variables.

---

## 20. Phân công team 2 người

### Người 1 — AI / Detection

Sở hữu chính:

```text
ml/
backend/app/services/url_detector.py
backend/app/services/content_detector.py
backend/app/services/brand_detector.py
backend/app/services/risk_engine.py
```

Nhiệm vụ:

- Dataset.
- URL features.
- URL model.
- Domain feature experiments.
- Brand detector.
- Content model.
- Vision model nếu kịp.
- Evaluation.
- Threshold tuning.
- Fusion/risk engine.

### Người 2 — Extension / Platform

Sở hữu chính:

```text
extension/
backend/app/api/
deploy/
.github/workflows/
```

Nhiệm vụ:

- Manifest V3.
- Background worker.
- Content scripts.
- Popup.
- Warning page.
- API integration.
- Cache/storage.
- Docker.
- CI/CD.
- Integration/E2E tests.

### Phần dùng chung cần review cả hai

- API schema.
- Risk schema.
- Docker Compose.
- Integration tests.
- Release checklist.

---

## 21. CI/CD

Thiết lập GitHub Actions từ tuần 1.

### Extension pipeline

```text
npm install
  ↓
lint
  ↓
typecheck
  ↓
build
  ↓
unit tests
```

### Backend pipeline

```text
install dependencies
  ↓
ruff / lint
  ↓
pytest
  ↓
API contract tests
```

### Integration pipeline

```text
Start backend
   ↓
POST sample scan
   ↓
Validate response schema
   ↓
Run smoke tests
```

Chỉ merge khi CI green.

---

## 22. Testing Strategy

Test theo 4 lớp:

```text
Unit Test
   ↓
Integration Test
   ↓
Extension E2E
   ↓
Real-world Benchmark
```

### Synthetic test sites

```text
test-sites/
├── normal/
├── fake-bank/
├── fake-google/
├── fake-facebook/
├── otp-scam/
├── investment-scam/
├── crypto-scam/
└── suspicious-download/
```

Các trang này chỉ mô phỏng hành vi/phần tử UI, không chứa malware thật.

### Metrics AI

Không chỉ dùng Accuracy.

Theo dõi:

- Precision.
- Recall.
- F1.
- PR-AUC.
- ROC-AUC.
- False Positive Rate.
- False Negative Rate.
- Recall at low FPR.

Đặc biệt phải giảm false positive vì extension chặn nhầm website bình thường sẽ gây mất niềm tin người dùng.

---

## 23. Roadmap 6 tuần

| Tuần | Version | Mục tiêu |
|---|---|---|
| 1 | v0.1 | Extension + FastAPI + URL detector |
| 2 | v0.2 | DOM scanner + Risk Engine + Warning page |
| 3 | v0.3 | Domain/reputation + cache |
| 4 | v0.4 | Brand impersonation + Content AI |
| 5 | v0.5 | Vision + feedback + optimization |
| 6 | v1.0 | Benchmark + hardening + packaging |

Tiến trình:

```text
DAY 2
Extension ↔ API
        ↓
WEEK 1
URL phishing detector
        ↓
WEEK 2
URL + DOM protection
        ↓
WEEK 3
URL + DOM + Domain
        ↓
WEEK 4
+ Brand + Content AI
        ↓
WEEK 5
+ Vision
        ↓
WEEK 6
Production candidate v1.0
```

---

## 24. Release Gates

### Gate A — Foundation

- Extension cài được.
- Backend chạy được.
- API communication ổn định.
- Popup hiển thị kết quả.

### Gate B — Core Detection

- URL model chạy thật.
- DOM scanner hoạt động.
- Risk engine có explainable reasons.
- Không thu sensitive input.

### Gate C — Protection

- Warning page.
- Cache.
- Domain module.
- Degraded mode.

### Gate D — AI Enhancement

- Brand impersonation.
- Content classifier.
- Threshold tuning.

### Gate E — v1.0

- Vision nếu đủ ổn định.
- CI green.
- E2E test pass.
- Benchmark report.
- Docker deployment.
- Extension package build.
- Documentation đầy đủ.

Vision không được phép block release v1.0 nếu các core module đã đạt yêu cầu.

---

## 25. Definition of Done cho v1.0

v1.0 được coi là hoàn thành khi:

- [ ] User cài extension trên Chrome/Chromium được.
- [ ] Extension tự động phát hiện navigation.
- [ ] URL detector trả score ổn định.
- [ ] DOM scanner nhận được form/login/OTP metadata.
- [ ] Brand-domain mismatch hoạt động.
- [ ] Risk engine trả `safe/suspicious/dangerous`.
- [ ] Có lý do giải thích.
- [ ] Dangerous website có warning page.
- [ ] User có thể back hoặc continue manually.
- [ ] Không gửi password/OTP/card data.
- [ ] Backend có Dockerfile/docker-compose.
- [ ] Backend failure không làm extension crash.
- [ ] Test suite chạy tự động.
- [ ] Có benchmark cơ bản.
- [ ] README hướng dẫn cài và chạy.

---

## 26. Mục tiêu sản phẩm cuối

Phiên bản v1.0 tối thiểu sẽ có:

```text
Browser Extension
      +
URL ML Detector
      +
DOM Analysis
      +
Domain Intelligence
      +
Brand Protection
      +
Explainable Risk Engine
      +
Warning System
      +
Fail-safe Architecture
```

Các module Content AI và Vision giúp tăng chất lượng nhưng không được trở thành single point of failure.

Nguyên tắc quan trọng nhất của dự án:

> Sau mỗi phase, repository phải luôn có một phiên bản có thể build, cài vào trình duyệt và demo end-to-end được.

Mục tiêu là ưu tiên một sản phẩm hoàn chỉnh, có thể kiểm thử và triển khai thật, thay vì có nhiều model mạnh nhưng không tích hợp được thành hệ thống chạy ổn định.
