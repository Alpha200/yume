# Home Assistant Integration Test

This test verifies the public transport departures integration with Home Assistant.

## Setup

1. Install test dependencies:
```bash
pip install pytest pytest-asyncio
```

2. Set environment variables:
```bash
export HA_URL="http://localhost:8123"
export HA_TOKEN="your_long_lived_access_token"
export TEST_TRANSPORT_ENTITY="sensor.train_station_u47"
```

### Getting a Home Assistant Token

1. Go to your Home Assistant instance
2. Click on your profile (bottom left)
3. Scroll down to "Long-Lived Access Tokens"
4. Click "Create Token"
5. Give it a name (e.g., "Yume Test")
6. Copy the token

## Running Tests

### With pytest:
```bash
python -m pytest tests/test_home_assistant_transport.py -v
```

### Direct execution:
```bash
python tests/test_home_assistant_transport.py
```

## What it tests

- ✅ Fetches departure data from a real Home Assistant entity
- ✅ Validates the data structure (PublicTransportDeparture objects)
- ✅ Checks planned times, estimated times, and delay calculations
- ✅ Tests error handling with invalid entities
- ✅ Displays detailed departure information for debugging

## Expected Output

```
Running Home Assistant Public Transport Integration Tests

======================================================================
Home Assistant URL: http://localhost:8123
Testing entity: sensor.train_station_u47
======================================================================

✅ Successfully fetched 5 departures

Departures:
  1. 14:30 (delayed by 3 min)
     Planned time: 2025-12-07 14:30:00+01:00
     Estimated time: 2025-12-07 14:33:00+01:00
     Delay: 3 minutes

  2. 15:00 (on time)
     Planned time: 2025-12-07 15:00:00+01:00
     Estimated time: 2025-12-07 15:00:00+01:00
     Delay: 0 minutes

✅ Test passed!
```
