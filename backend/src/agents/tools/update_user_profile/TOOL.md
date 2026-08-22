# Update User Profile Tool

## Description

Records durable personalization information identified by the Post-booking Agent from the current message, conversation history, and profile brief.

The tool enqueues the update to Redis and returns immediately. A worker merges the signals into the anonymous/trusted profile without invoking another LLM.

Call this tool only when there is a new signal, an existing signal needs correction, its confidence should be strengthened or weakened, or it should be retracted.

Do not call the tool merely to fill empty profile sections.

## Parameters

The tool accepts one required parameter, `signals`: an array containing at least one `SignalCandidate`.

`profile_id`, `conversation_id`, and `trace_id` are injected by the system; the agent must not provide them.

| Field         | Required | Allowed values                                     | Meaning                                                                                                                                                                                      |
| ------------- | -------: | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `category`    |      Yes | Allow-list below                                   | Information category                                                                                                                                                                         |
| `key`         |      Yes | Stable semantic key                                | Example: `daily_commute_distance`                                                                                                                                                            |
| `value`       |      Yes | string/number/bool/list/object                     | Value to store                                                                                                                                                                               |
| `description` |       No | Short string                                       | Human-readable text shown in the profile brief                                                                                                                                               |
| `certainty`   |       No | `known`, `likely`, `possible`                      | Default: `possible`                                                                                                                                                                          |
| `confidence`  |       No | number `0..1`                                      | Default: `0.5`                                                                                                                                                                               |
| `source_type` |       No | `explicit_user`, `implicit_user`, `trusted_domain` | Default: `implicit_user`                                                                                                                                                                     |
| `subject`     |       No | `self`, `third_party`                              | Default: `self`. Use `self` for the current speaker whether they are booker or driver. Use `third_party` only when that speaker clearly provides information about the other participant in the same booking; the backend resolves the target and marks it as lower-confidence information supplied on their behalf. |
| `operation`   |       No | `add`, `strengthen`, `weaken`, `revise`, `retract` | Default: `add`                                                                                                                                                                               |

## Category allow-list

* `fact`: Facts explicitly stated by the user or confirmed by context, such as number of children or current vehicle.
* `usage`: Vehicle usage, travel distance, recurring journeys, or family context.
* `experience`: Relevant driving or EV experience.
* `interest`: Topics of interest such as charging, ADAS, or family space.
* `concern`: Something the user is worried about or wants to validate.
* `test_drive_goal`: Something the user wants to evaluate during the test drive.
* `conversation_preference`: How the user prefers to receive support.
* `likely_intent`: A broader goal inferred from multiple signals.
* `custom_intent`: A durable intent that does not fit the categories above.

## Certainty and source rules

* Direct user statement: `known`, `explicit_user`, typically confidence `0.85–1.0`.
* Inference supported by multiple signals: `likely`, `implicit_user`, typically `0.6–0.84`.
* Hypothesis requiring confirmation: `possible`, `implicit_user`, typically below `0.6`.
* When the user corrects existing information, use `revise`; when they explicitly reject it, use `retract`.
* Never turn an inference into a known fact.
* `subject=self` is the normal choice whenever the current speaker describes their own needs, habits, experience, or concerns.
* `subject=third_party` means the current speaker is describing the other booking participant. It is never used merely because that other person is named in the booking.

## Do not store

Do not store OTPs, access tokens, email addresses, phone numbers, credentials, raw conversations, or transient booking state.

Do not store information merely because a profile section is empty.

## Example

```json
{
  "signals": [
    {
      "category": "usage",
      "key": "daily_commute_distance",
      "value": {
        "distance_km": 40,
        "frequency": "daily"
      },
      "description": "Commutes approximately 40 km per day.",
      "certainty": "known",
      "confidence": 0.95,
      "source_type": "explicit_user",
      "operation": "add"
    },
    {
      "category": "likely_intent",
      "key": "evaluate_charging_feasibility",
      "value": true,
      "description": "Likely evaluating the feasibility of EV charging.",
      "certainty": "likely",
      "confidence": 0.7,
      "source_type": "implicit_user",
      "operation": "add"
    }
  ]
}
```

## Result

* `queued`: Redis successfully received the job.
* `unavailable`: Redis did not receive the job; do not claim that the profile was updated.
* `skipped/profile_not_resolved`: The profile could not be resolved.
