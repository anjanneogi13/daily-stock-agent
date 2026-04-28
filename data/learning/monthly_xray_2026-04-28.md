# Monthly X-Ray - 2026-04-28

_Gemini failed: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 0, model: gemini-2.0-flash\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, model: gemini-2.0-flash\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, model: gemini-2.0-flash\nPlease retry in 4.195133691s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_input_token_count', 'quotaId': 'GenerateContentInputTokensPerModelPerMinute-FreeTier', 'quotaDimensions': {'model': 'gemini-2.0-flash', 'location': 'global'}}, {'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.0-flash'}}, {'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.0-flash'}}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '4s'}]}}_

```json
{
  "period": {
    "start": "2026-03-29",
    "end": "2026-04-28",
    "picks": 10,
    "evaluated": 0
  },
  "weekly_summary": [
    {
      "week_starting": "2026-04-27",
      "picks": 10,
      "evaluated": 0,
      "tp": 0,
      "sl": 0,
      "win_rate_pct": 0,
      "avg_r": 0,
      "avg_return_pct": 0,
      "total_r": 0.0
    }
  ],
  "trend": [],
  "code_changes": [
    {
      "date": "2026-04-28",
      "msg": "Add premarket sanity check with risk-tagged Telegram + email"
    }
  ],
  "by_score": {},
  "by_regime": {},
  "best": [],
  "worst": [],
  "observation_types": {
    "sector_warning": 2,
    "weak_pick": 6,
    "sl_too_tight": 1,
    "premarket_correct": 6,
    "sl_well_placed": 2
  }
}
```