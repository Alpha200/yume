"""
Integration test for Home Assistant public transport departures

This test requires a real Home Assistant instance with a configured transport entity.
Set the following environment variables:
- HA_URL: URL of your Home Assistant instance (e.g., http://localhost:8123)
- HA_TOKEN: Long-lived access token from Home Assistant
- TEST_TRANSPORT_ENTITY: Entity ID to test (e.g., sensor.train_station_u47)

Run with: python -m pytest tests/test_home_assistant_transport.py -v
"""

import asyncio
import os
import pytest
from services.home_assistant import get_public_transport_departures, PublicTransportDeparture


@pytest.fixture
def transport_entity():
    """Get the transport entity ID from environment variable"""
    entity_id = os.getenv("TEST_TRANSPORT_ENTITY")
    if not entity_id:
        pytest.skip("TEST_TRANSPORT_ENTITY environment variable not set")
    return entity_id


@pytest.fixture
def check_ha_config():
    """Check if Home Assistant is configured"""
    ha_url = os.getenv("HA_URL")
    ha_token = os.getenv("HA_TOKEN")
    
    if not ha_url or not ha_token:
        pytest.skip("HA_URL and HA_TOKEN environment variables must be set")


@pytest.mark.asyncio
async def test_get_public_transport_departures(transport_entity, check_ha_config):
    """Test fetching public transport departures from a real entity"""
    
    # Fetch departures
    departures = await get_public_transport_departures(transport_entity)
    
    # Basic assertions
    assert isinstance(departures, list), "Should return a list"
    
    if len(departures) > 0:
        print(f"\n✅ Found {len(departures)} departures:")
        
        for i, dep in enumerate(departures, 1):
            # Check type
            assert isinstance(dep, PublicTransportDeparture), f"Departure {i} should be PublicTransportDeparture instance"
            
            # Check required fields
            assert dep.planned_time is not None, f"Departure {i} should have planned_time"
            
            # Print departure info
            print(f"  {i}. {dep}")
            print(f"     - Planned: {dep.planned_time}")
            print(f"     - Estimated: {dep.estimated_time}")
            print(f"     - Delay: {dep.delay_minutes} min" if dep.delay_minutes is not None else "     - Delay: Unknown")
            
            # Check delay calculation if estimated time exists
            if dep.estimated_time is not None:
                calculated_delay = int((dep.estimated_time - dep.planned_time).total_seconds() / 60)
                assert dep.delay_minutes == calculated_delay, f"Departure {i} delay calculation mismatch"
    else:
        print("\n⚠️  No departures found - entity might have no upcoming departures")


@pytest.mark.asyncio
async def test_get_public_transport_departures_invalid_entity(check_ha_config):
    """Test error handling with invalid entity"""
    
    with pytest.raises(Exception) as exc_info:
        await get_public_transport_departures("sensor.nonexistent_entity_12345")
    
    assert "Failed to fetch transit entity" in str(exc_info.value) or "404" in str(exc_info.value)


if __name__ == "__main__":
    """Run tests directly with python"""
    print("Running Home Assistant Public Transport Integration Tests\n")
    print("=" * 70)
    
    # Check environment
    ha_url = os.getenv("HA_URL")
    ha_token = os.getenv("HA_TOKEN")
    entity_id = os.getenv("TEST_TRANSPORT_ENTITY")
    
    if not ha_url or not ha_token:
        print("❌ ERROR: HA_URL and HA_TOKEN must be set")
        print("\nExample:")
        print('  export HA_URL="http://localhost:8123"')
        print('  export HA_TOKEN="your_long_lived_access_token"')
        print('  export TEST_TRANSPORT_ENTITY="sensor.train_station_u47"')
        exit(1)
    
    if not entity_id:
        print("❌ ERROR: TEST_TRANSPORT_ENTITY must be set")
        print("\nExample:")
        print('  export TEST_TRANSPORT_ENTITY="sensor.train_station_u47"')
        exit(1)
    
    print(f"Home Assistant URL: {ha_url}")
    print(f"Testing entity: {entity_id}")
    print("=" * 70)
    print()
    
    # Run the test
    async def run_test():
        try:
            departures = await get_public_transport_departures(entity_id)
            
            print(f"\n✅ Successfully fetched {len(departures)} departures\n")
            
            if len(departures) > 0:
                print("Departures:")
                for i, dep in enumerate(departures, 1):
                    print(f"  {i}. {dep}")
                    print(f"     Planned time: {dep.planned_time}")
                    print(f"     Estimated time: {dep.estimated_time}")
                    print(f"     Delay: {dep.delay_minutes} minutes" if dep.delay_minutes is not None else "     Delay: Unknown")
                    print()
            else:
                print("⚠️  No upcoming departures found")
            
            print("\n✅ Test passed!")
            
        except Exception as e:
            print(f"\n❌ Test failed with error:")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            exit(1)
    
    asyncio.run(run_test())
